#!/usr/bin/env python3
"""Guarda de integridad de `main` — para repos donde la proteccion de rama NO
esta disponible (privados en plan Free: la API responde 403 "Upgrade to GitHub
Pro or make this repository public").

No PUEDE impedir un push directo: nadie puede, sin proteccion de rama. Lo que
hace es **no dejar que pase inadvertido**: cada commit que llega a `main` sin
haber pasado por un PR revisado deja el CI en rojo, con nombre y apellido.

Detectar no es prevenir, y conviene no confundirlos:

    Proteccion de rama  ->  el push se RECHAZA        (mecanismo preventivo)
    Esta guarda         ->  el push entra y se DENUNCIA (mecanismo detectivo)

Si el proyecto puede permitirse GitHub Pro o ser publico, usa la proteccion de
rama y borra esta guarda. Esto es la red para cuando no se puede.

Uso: python3 scripts/proteccion_main.py <sha_antes> <sha_ahora>
     (lo invoca .github/workflows/proteccion-main.yml en cada push a main)
Tests: python3 scripts/test_proteccion_main.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# CONFIGURACION DE ESTE REPO (catalogo de skills, sin protocolo de equipo).
#
# Sin excepciones: aqui no hay tablero markdown que haga de candado, asi que
# nada justifica saltarse el PR.
PREFIJOS_PERMITIDOS: tuple[str, ...] = ()

# En falso MIENTRAS SE TRABAJE EN SOLITARIO. GitHub no deja aprobar tu propio
# PR, asi que exigir una aprobacion con un solo dev bloquea el 100% del trabajo
# y acabaria con la guarda desactivada — que es peor que tenerla en modo suave.
# Lo que si se exige es que todo pase por PR: diff revisable, CI ejecutado,
# historia limpia. Y ya no depende de acordarse: en cuanto el repo tenga un
# segundo colaborador humano, la guarda EXIGE ponerlo a True.
EXIGIR_REVISION = False

# Excepcion DECLARADA (decision del 2026-07-26). Este repo tiene un segundo
# colaborador con acceso, pero el trabajo aqui es en solitario y GitHub no deja
# aprobar el PR propio. Se acepta a sabiendas, con fecha: al vencer hay que
# decidir de verdad — o el segundo revisa (EXIGIR_REVISION = True), o su acceso
# sobra en este repo. Sin caducidad esto dejaria de ser una excepcion.
REVISION_RELAJADA: dict[str, str] | None = {
    "motivo": "Trabajo en solitario pese a haber un segundo colaborador con "
              "acceso; GitHub no deja aprobar el PR propio",
    "vence": "2026-10-24",
}
MAX_DIAS_EXCEPCION = 180

SHA_NULO = "0" * 40

# Prefijo de los hallazgos que son de CONFIGURACION de la guarda, no de commits
# que se saltaron el protocolo. Los remedios son distintos y el resumen final los
# separa: contarlos juntos haria que el reporte mintiera sobre lo que paso.
MARCA_CONFIG = "configuracion: "


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True,
                          text=True, check=True).stdout.strip()


def _api(ruta: str) -> list | dict | None:
    """GET a la API de GitHub. `None` = no se pudo consultar (404 de un commit
    que aun no esta publicado, falta de permisos, corte de red...).

    Punto unico de contacto con la red: los tests lo sustituyen para no depender
    de un repo real.
    """
    r = subprocess.run(["gh", "api", ruta], cwd=RAIZ, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout) if r.stdout.strip() else []


def commits_nuevos(antes: str, ahora: str) -> list[str]:
    if antes in ("", SHA_NULO):
        # Primer push de la rama: no hay rango anterior con el que comparar.
        return []
    return [c for c in _git("rev-list", f"{antes}..{ahora}").splitlines() if c]


def _asunto(sha: str) -> str:
    return _git("log", "-1", "--format=%s", sha)


def _es_merge(sha: str) -> bool:
    return len(_git("log", "-1", "--format=%P", sha).split()) > 1


def _humanos_con_acceso() -> list[str] | None:
    """Colaboradores humanos del repo. `None` = no se pudo consultar.

    Son los que PODRIAN aprobar un PR: la pregunta que decide si `EXIGIR_REVISION`
    en False sigue estando justificado. Los bots (dependabot y compañia) no
    cuentan — no revisan nada.
    """
    datos = _api("repos/{owner}/{repo}/collaborators?per_page=100")
    if datos is None:
        return None
    return sorted(
        c["login"] for c in datos
        if c.get("type") != "Bot" and not c.get("login", "").endswith("[bot]")
    )


def _excepcion_mal_declarada(exc: dict, hoy: date | None = None) -> str:
    """Cadena vacia si la excepcion es valida; el problema concreto si no.

    Una excepcion mal escrita no silencia nada: si lo hiciera, bastaria con poner
    cualquier cosa ahi para apagar la guarda, que es lo contrario de decidir a
    sabiendas.
    """
    hoy = hoy or date.today()
    if not exc.get("motivo"):
        return ("REVISION_RELAJADA no declara 'motivo'. Una excepcion sin razon "
                "escrita no se puede reevaluar: nadie sabra por que se acepto.")
    texto = exc.get("vence")
    if not texto:
        return ("REVISION_RELAJADA no declara 'vence'. Sin caducidad la excepcion "
                "se vuelve el estado normal, y el estado normal no se revisa.")
    try:
        vence = datetime.strptime(str(texto), "%Y-%m-%d").date()
    except ValueError:
        return f"REVISION_RELAJADA tiene 'vence' invalido ({texto}), formato AAAA-MM-DD."
    if vence < hoy:
        return (f"La excepcion de revision CADUCO el {texto}. Reevalua: o el "
                f"segundo colaborador revisa de verdad (EXIGIR_REVISION = True), "
                f"o su acceso sobra en este repo, o renuevas con motivo nuevo.")
    if vence > hoy + timedelta(days=MAX_DIAS_EXCEPCION):
        return (f"La excepcion vence el {texto}, a mas de {MAX_DIAS_EXCEPCION} dias "
                f"vista. Una excepcion tan larga deja de revisarse; acorta la fecha.")
    return ""


def revision_desactivada_con_equipo() -> list[str]:
    """La excusa de trabajar en solitario caduca cuando deja de ser cierto."""
    if EXIGIR_REVISION:
        return []
    humanos = _humanos_con_acceso()
    if humanos is None:
        # Aviso, no fallo: esto es una comprobacion de configuracion, no un
        # veredicto de seguridad. Poner el CI en rojo porque la API de
        # colaboradores no respondio seria una falsa alarma, y las falsas
        # alarmas es lo que ensena a ignorar el rojo.
        print("(AVISO: EXIGIR_REVISION=False y no se pudo comprobar si sigues "
              "en solitario. Si ya hay mas gente en el repo, subelo a True.)")
        return []
    if len(humanos) < 2:
        return []
    if REVISION_RELAJADA is not None:
        problema = _excepcion_mal_declarada(REVISION_RELAJADA)
        if problema:
            return [MARCA_CONFIG + problema]
        print(f"(AVISO: revision relajada a sabiendas hasta "
              f"{REVISION_RELAJADA.get('vence')} — {REVISION_RELAJADA.get('motivo')})")
        return []

    return [
        MARCA_CONFIG
        + f"EXIGIR_REVISION=False pero el repo ya tiene {len(humanos)} colaboradores "
        f"humanos ({', '.join(humanos)}).\n"
        f"        Esa excepcion existia solo para trabajar en solitario, porque "
        f"GitHub no deja aprobar el PR propio.\n"
        f"        Ya no es el caso: pon EXIGIR_REVISION = True en "
        f"scripts/proteccion_main.py.\n"
        f"        Mientras siga en False, esta guarda exige PR pero NO revision "
        f"— media barrera que aparenta ser entera."
    ]


def revisar(antes: str, ahora: str) -> list[str]:
    fallos: list[str] = revision_desactivada_con_equipo()
    for sha in commits_nuevos(antes, ahora):
        asunto = _asunto(sha)
        corto = sha[:8]

        if asunto.startswith(PREFIJOS_PERMITIDOS):
            continue
        if _es_merge(sha):
            # El merge del propio PR: lo que se juzga son sus commits.
            continue

        prs = _api(f"repos/{{owner}}/{{repo}}/commits/{sha}/pulls")
        if prs is None:
            # No se calla: un commit en main que no se puede verificar es un
            # agujero, y una guarda que se salta lo que no entiende no sirve.
            fallos.append(
                f"{corto} \"{asunto}\" no se pudo verificar contra GitHub "
                f"(commit sin publicar, permisos del token o API caida)"
            )
            continue
        if not prs:
            fallos.append(
                f"{corto} \"{asunto}\" llego a main sin PR (push directo)"
            )
            continue

        if not EXIGIR_REVISION:
            continue

        numero = prs[0].get("number")
        revisiones = _api(f"repos/{{owner}}/{{repo}}/pulls/{numero}/reviews")
        if revisiones is None:
            fallos.append(
                f"{corto} \"{asunto}\": no se pudieron leer las revisiones del PR #{numero}"
            )
            continue
        aprobaciones = [r for r in revisiones if r.get("state") == "APPROVED"]
        if not aprobaciones:
            fallos.append(
                f"{corto} \"{asunto}\" entro por el PR #{numero}, mergeado SIN "
                f"ninguna aprobacion"
            )
    return fallos


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("Uso: proteccion_main.py <sha_antes> <sha_ahora>")
        return 2
    fallos = revisar(argv[1], argv[2])
    for fallo in fallos:
        print(f"FALLO {fallo}")
    # Dos clases de hallazgo con remedios distintos: un commit que se salto el
    # protocolo se revisa o se revierte; una guarda mal configurada se
    # reconfigura. Contarlos juntos haria que el resumen mintiera sobre lo que
    # acaba de pasar, que es justo el falso exito que este kit persigue.
    de_config = [f for f in fallos if f.startswith(MARCA_CONFIG)]
    de_commits = [f for f in fallos if not f.startswith(MARCA_CONFIG)]

    if de_commits:
        print(f"\n{len(de_commits)} commit(s) entraron a main saltandose el protocolo.")
        print("Esta guarda no puede impedirlo (hace falta proteccion de rama, que")
        print("exige repo publico o GitHub Pro). Lo que hace es que no pase")
        print("inadvertido: revisa el cambio y, si procede, revierte o abre el PR.")
    if de_config:
        print(f"\n{len(de_config)} problema(s) de CONFIGURACION de la guarda.")
        print("Nadie se salto el protocolo: lo que pasa es que la guarda ya no")
        print("vigila lo que cree vigilar. Se arregla en scripts/proteccion_main.py.")
    if fallos:
        return 1
    print("main integra: todo llego por PR revisado.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
