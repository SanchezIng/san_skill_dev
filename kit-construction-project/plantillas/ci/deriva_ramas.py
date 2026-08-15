#!/usr/bin/env python3
"""Aviso de deriva en ramas de vida larga.

Por que existe: el kit prescribe modulos reclamables trabajados EN PARALELO, y
eso produce estructuralmente ramas que divergen entre si. Es una consecuencia
del diseño, no un accidente — pero el kit creaba la condicion y no daba el
instrumento.

En el piloto, un PR salio de su base el dia 18 y se mergeo el 22: cuatro dias de
deriva, cuatro conflictos, y uno de ellos NO MECANICO — la rama afirmaba un
estado de tarea que ya era falso, y resolverlo con `--theirs` a ciegas habria
metido una regresion documental en `main` con el CI en verde. Fue el mayor
sumidero de tiempo de la sesion; el dia 19 habria sido trivial.

La opcion nativa de GitHub ("Require branches to be up to date before merging")
depende de la proteccion de rama, que en repos privados con plan Free NO existe.
De ahi que haga falta un workflow propio.

Regla de diseño que importa mas que el umbral: **UN AVISO POR PR, NO UNO POR
EJECUCION**. Un bot que comenta cada seis horas se filtra, y un aviso filtrado no
es un aviso. Aqui se comenta UNA vez y, en las siguientes pasadas, se EDITA ese
mismo comentario: la cifra queda al dia sin generar una sola notificacion nueva.
Si la rama se pone al dia, el comentario se actualiza para decirlo — un aviso que
se queda obsoleto tambien miente.

Esto NO rompe builds: es un aviso, corre en `schedule` y su unico efecto es
comentar. Lo que si hace es fallar ruidosamente si no puede hacer su trabajo,
para no dar la falsa impresion de que se esta vigilando algo que no se vigila.

Uso:
    python3 scripts/deriva_ramas.py             # comenta donde toque
    python3 scripts/deriva_ramas.py --simular   # dice que haria, sin tocar nada
Tests:
    python3 scripts/test_deriva_ramas.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# Commits por detras de su base a partir de los cuales se avisa. El numero
# correcto depende del ritmo del equipo: el bueno es el que produce avisos que la
# gente lee. Si nadie hace caso, esta bajo; si aparecen conflictos sin aviso
# previo, esta alto.
UMBRAL_COMMITS = 15

# Los borradores son trabajo declaradamente en curso. Avisarlos es ruido — pero
# la deriva les afecta igual, asi que ponlo a True si el equipo los usa como
# ramas largas de verdad.
AVISAR_EN_BORRADORES = False

# Tope del listado de PRs. Si se alcanza, se PARA: un aviso que solo cubre parte
# de los PRs abiertos da una tranquilidad que no corresponde.
LIMITE_PRS = 100

MARCA = "<!-- deriva-ramas: comentario gestionado por scripts/deriva_ramas.py -->"


class ErrorDeGuarda(Exception):
    """No se ha podido vigilar. NO es "no hay deriva"."""


def _gh(args: list[str], repo: str | None = None) -> str:
    """Ejecuta `gh`. El repo se fija con GH_REPO y no con `--repo`: `gh api` no
    acepta ese flag, y GH_REPO sirve para ambos (comprobado)."""
    cmd = ["gh", *args]
    entorno = None
    if repo:
        entorno = {**os.environ, "GH_REPO": repo}
    r = subprocess.run(cmd, capture_output=True, text=True, env=entorno)
    if r.returncode != 0:
        raise ErrorDeGuarda(
            f"`{' '.join(cmd)}` fallo:\n   {(r.stderr or '').strip()}\n"
            f"   Sin poder consultar los PRs no se puede afirmar que no hay deriva."
        )
    return r.stdout


def _json(salida: str, que: str):
    try:
        return json.loads(salida)
    except json.JSONDecodeError:
        raise ErrorDeGuarda(f"La respuesta de {que} no es JSON valido.") from None


def prs_abiertos(repo: str | None = None) -> list[dict]:
    datos = _json(_gh([
        "pr", "list", "--state", "open", "--limit", str(LIMITE_PRS),
        "--json", "number,title,url,baseRefName,headRefName,isDraft,createdAt,mergeable",
    ], repo), "gh pr list")
    if len(datos) >= LIMITE_PRS:
        raise ErrorDeGuarda(
            f"El listado trajo justo el tope ({LIMITE_PRS} PRs): asume que hay mas.\n"
            f"   Sube LIMITE_PRS en scripts/deriva_ramas.py y vuelve a ejecutar.\n"
            f"   Avisar solo de una parte da una tranquilidad que no corresponde."
        )
    return datos


def commits_por_detras(pr: dict, repo: str | None = None) -> int:
    """Cuantos commits de la base NO estan en la rama del PR."""
    base, head = pr["baseRefName"], pr["headRefName"]
    datos = _json(_gh([
        "api", f"repos/{{owner}}/{{repo}}/compare/{base}...{head}",
        "--jq", "{behind: .behind_by, ahead: .ahead_by}",
    ], repo), f"compare {base}...{head}")
    detras = datos.get("behind")
    if not isinstance(detras, int):
        raise ErrorDeGuarda(
            f"La comparacion {base}...{head} no devolvio 'behind_by'.\n"
            f"   No se inventa un 0: eso seria decir 'esta al dia' sin saberlo."
        )
    return detras


def _dias(creado: str) -> int:
    try:
        nacimiento = datetime.fromisoformat(creado.replace("Z", "+00:00"))
    except ValueError:
        return 0
    return max((datetime.now(timezone.utc) - nacimiento).days, 0)


def comentario(pr: dict, detras: int, dias: int) -> str:
    """El texto del aviso: el numero, el riesgo concreto y como salir.

    Va en español con acentos porque lo lee gente en un PR, no una consola.
    """
    base = pr["baseRefName"]
    cabecera = (f"**Esta rama va {detras} commits por detrás de `{base}`**"
                f"{f' y lleva {dias} días abierta' if dias else ''}.")
    if pr.get("mergeable") == "CONFLICTING":
        cabecera += " GitHub ya reporta **conflictos**."
    return "\n".join([
        MARCA,
        "",
        cabecera,
        "",
        f"El riesgo no es el número de conflictos, es su tipo. Uno de dos líneas se "
        f"resuelve en un minuto; el caro es el que **no es mecánico** — la rama afirma "
        f"algo (un estado, una decisión, un dato en un doc) que en `{base}` ya es "
        f"falso. Resolverlo a ciegas con `--theirs`/`--ours` mete una regresión **con "
        f"el CI en verde**, porque ningún test cubre eso.",
        "",
        f"**No hace falta ponerla al día para que te revisen.** La rama tiene que "
        f"estar al día para **mergear**, no antes: se revisa el diff contra su base. "
        f"Perseguir a `{base}` mientras esperas review es una carrera que no se gana "
        f"—cada actualización reinicia la verificación y, mientras, `{base}` vuelve a "
        f"moverse—, y encima invalida la review que ya te hicieron.",
        "",
        "Cuando vayas a mergear (o si quieres adelantarte porque ves conflicto gordo):",
        "",
        "```bash",
        f"git fetch origin && git rebase origin/{base}     # o: git merge origin/{base}",
        "```",
        "",
        "_Aviso automático. Este comentario se **actualiza**, no se repite: no vas a "
        "recibir otra notificación por esto._",
    ])


def comentario_resuelto(pr: dict, detras: int) -> str:
    base = pr["baseRefName"]
    estado = "al día" if detras == 0 else f"a solo {detras} commits"
    return "\n".join([
        MARCA,
        "",
        f"~~Aviso de deriva~~ — resuelto: la rama está **{estado}** de `{base}`.",
        "",
        "_Aviso automático, actualizado al ponerse la rama al día._",
    ])


def comentario_previo(numero: int, repo: str | None = None) -> dict | None:
    """El comentario que ya dejo esta guarda en el PR, si lo hay."""
    datos = _json(_gh([
        "api", f"repos/{{owner}}/{{repo}}/issues/{numero}/comments",
        "--paginate", "--jq", "[.[] | {id: .id, body: .body}]",
    ], repo), f"comentarios del PR #{numero}")
    for c in datos:
        if MARCA in (c.get("body") or ""):
            return c
    return None


def _publicar(numero: int, cuerpo: str, previo: dict | None, repo: str | None) -> str:
    """Crea o EDITA. Devuelve que se hizo, para el reporte."""
    if previo:
        if previo.get("body") == cuerpo:
            return "sin cambios"
        _gh(["api", f"repos/{{owner}}/{{repo}}/issues/comments/{previo['id']}",
             "--method", "PATCH", "-f", f"body={cuerpo}"], repo)
        return "actualizado"
    _gh(["api", f"repos/{{owner}}/{{repo}}/issues/{numero}/comments",
         "--method", "POST", "-f", f"body={cuerpo}"], repo)
    return "comentado"


def revisar(repo: str | None = None, simular: bool = False) -> list[str]:
    """Devuelve las lineas del reporte. No lanza salvo que no pueda vigilar."""
    reporte = []
    for pr in prs_abiertos(repo):
        numero = pr["number"]
        if pr.get("isDraft") and not AVISAR_EN_BORRADORES:
            continue
        detras = commits_por_detras(pr, repo)
        previo = comentario_previo(numero, repo)

        if detras >= UMBRAL_COMMITS:
            cuerpo = comentario(pr, detras, _dias(pr.get("createdAt", "")))
        elif previo:
            # Se puso al dia: el aviso viejo dejaria de ser cierto.
            cuerpo = comentario_resuelto(pr, detras)
        else:
            continue

        if simular:
            accion = "COMENTARIA" if not previo else "ACTUALIZARIA"
        else:
            accion = _publicar(numero, cuerpo, previo, repo)
        reporte.append(f"#{numero} ({detras} detras de {pr['baseRefName']}): {accion}")
    return reporte


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    simular = "--simular" in argv
    repo = None
    if "--repo" in argv:
        repo = argv[argv.index("--repo") + 1]

    try:
        reporte = revisar(repo, simular)
    except ErrorDeGuarda as e:
        print(f"FALLO {e}", file=sys.stderr)
        print("\nLa vigilancia de deriva NO se ha ejecutado. Que no haya avisos hoy\n"
              "no significa que las ramas esten al dia.", file=sys.stderr)
        return 1

    if not reporte:
        print(f"Sin deriva por encima del umbral ({UMBRAL_COMMITS} commits).")
        return 0
    print(f"Umbral: {UMBRAL_COMMITS} commits{' (SIMULACION)' if simular else ''}")
    for linea in reporte:
        print(f"  {linea}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
