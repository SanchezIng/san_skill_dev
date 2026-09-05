#!/usr/bin/env python3
"""Lo que `/que-toca` necesita saber ANTES de elegir tarea, en una sola pasada.

POR QUE EXISTE (y por que no es un servidor MCP)
------------------------------------------------
Los pasos 2-3 del protocolo eran CINCO invocaciones a `gh`, y cada una deja su
salida en el contexto durante el resto de la sesion. La propuesta original para
arreglarlo era un servidor MCP de solo lectura. Esto es la version barata de la
misma idea: agregar aqui, en un script que viaja por el kit, se testea en CI y
no añade ningun proceso vivo a la maquina de nadie.

Se midio antes de decidir: la agregacion ahorra ~500 tokens por reclamo, no los
~10.000 que la propuesta estimaba. Un servidor no puede superar ese techo —los
datos son los datos— y encima pagaria su catalogo de herramientas en CADA
sesion, se use o no. Por eso el kit trae este script y no aquel servidor.

**Y su valor real no es el ahorro.** Es que TRES comprobaciones del candado
dejen de depender de que el agente se acuerde de hacerlas: el tope de las
listas, el titulo vivo y los issues invisibles. Las tres estan abajo, y las tres
tienen un caso que muerde en `test_estado.py`.

QUE PREGUNTA RESPONDE, TODO DE UNA VEZ
--------------------------------------
1. ¿Ya tengo tarea? (issues abiertos asignados a mi)
2. ¿Que hay Disponible y sin dueño?
3. ¿Hay issues abiertos FUERA del Project, o items DENTRO pero sin estado? — las
   dos formas de quedar invisible para todo el mundo: `gh issue create` no añade
   al Project, y `item-add` no pone el estado ni protesta si falta.
4. ¿Alguna lista viene cortada por el tope? Una lista truncada en silencio es
   peor que un error: da por libre lo que otro ya tiene.
5. ¿Lo Disponible es trabajo, o solo avisos? Un tablero lleno de decisiones y
   vigilancias no ofrece nada que reclamar, y eso no se ve hasta abrir una.

Uso:
    python3 scripts/estado.py
    python3 scripts/estado.py --json     # para encadenar, no para leer
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
RAIZ = _AQUI.parent

if str(_AQUI) not in sys.path:
    # `append`, no `insert(0, ...)`: al final la stdlib sigue ganando. Un
    # `scripts/json.py` que apareciera mañana no debe poder secuestrar el
    # `import json` de nadie.
    sys.path.append(str(_AQUI))

# UNA sola casilla que rellenar, y esta en `tablero.py`: el checklist de
# instalacion manda ponerlos alli (singular) y alli esta la guarda del
# placeholder sin rellenar. Una copia aqui significaba que quien arranca el kit y
# rellena solo uno lee el Project equivocado EN SILENCIO, que es el peor modo de
# fallo posible para un candado.
from tablero import OWNER, PROJECT_NUMBER  # noqa: E402

# Una TAREA reclamable se reconoce por el prefijo `T-nnn` del titulo: es la
# convencion que `/cerrar-sesion` exige para poder cruzar el issue con el
# backlog. Lo que no lo lleva es un aviso al equipo o una decision, y ninguna de
# las dos es trabajo que se reclame.
TAREA = re.compile(r"^\s*T-\d+")

# Alto A PROPOSITO: `gh` trae 30 por defecto y una lista truncada no avisa. Si
# alguna consulta devuelve exactamente el tope, se dice en voz alta.
TOPE = 500


def _gh(argumentos: list[str]) -> str:
    # `cwd=RAIZ` y no `--repo`: `gh issue list` deduce el repo del directorio
    # actual, asi que invocado desde fuera moria con "fatal: not a git
    # repository" en vez de decir que pasa. Fijarlo por cwd no añade una
    # constante mas que rellenar, y sirve tambien para `gh api`, que ni siquiera
    # acepta `--repo` (misma razon por la que `deriva_ramas.py` usa GH_REPO).
    proceso = subprocess.run(
        ["gh", *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=RAIZ,
    )
    if proceso.returncode != 0:
        salida = (proceso.stderr or proceso.stdout or "").strip()
        sys.exit("gh %s fallo:\n%s" % (" ".join(argumentos[:2]), salida))
    return proceso.stdout


def _items_del_project() -> list[dict]:
    crudo = _gh(
        [
            "project", "item-list", PROJECT_NUMBER,
            "--owner", OWNER,
            "--format", "json",
            "--limit", str(TOPE),
        ]
    )
    return json.loads(crudo).get("items", [])


def _issues_abiertos() -> list[dict]:
    crudo = _gh(
        [
            "issue", "list",
            "--state", "open",
            "--limit", str(TOPE),
            "--json", "number,title,assignees",
        ]
    )
    return json.loads(crudo)


def _login() -> str:
    return _gh(["api", "user", "--jq", ".login"]).strip()


def _titulo(item: dict) -> str:
    """El titulo VIVO, el del issue.

    El `.title` del item es una copia congelada al añadir la tarjeta y NO sigue
    los renombrados del issue. Medido en un proyecto real: 9 de 90 items
    desincronizados, y en el peor el item decia una tarea y el issue decia otra
    REAL distinta — elegir por ese numero es reclamar otra cosa.
    """
    contenido = item.get("content") or {}
    return contenido.get("title") or item.get("title") or ""


def reunir() -> dict:
    items = _items_del_project()
    issues = _issues_abiertos()
    yo = _login()

    numeros_en_project = {
        (i.get("content") or {}).get("number")
        for i in items
        if (i.get("content") or {}).get("number") is not None
    }

    mias = [
        {"numero": i["number"], "titulo": i["title"]}
        for i in issues
        if any(a.get("login") == yo for a in i.get("assignees") or [])
    ]

    disponibles = sorted(
        (
            {
                "numero": (i.get("content") or {}).get("number"),
                "titulo": _titulo(i),
                "assignees": i.get("assignees") or [],
            }
            for i in items
            if i.get("status") == "Disponible"
        ),
        key=lambda t: t["numero"] if t["numero"] is not None else 10**9,
    )
    # Un item DRAFT no tiene issue detras, asi que no se puede reclamar: no lleva
    # numero que asignar ni tarjeta que mover. Colarlo entre las candidatas lo
    # imprimia como `#None` y mandaba al dev a reclamar algo inexistente.
    borradores = [t for t in disponibles if t["numero"] is None]
    libres = [t for t in disponibles if not t["assignees"] and t["numero"] is not None]

    # El hueco entre las dos listas: un item que SI esta en el Project pero sin
    # estado no sale ni en `libres` (no es "Disponible") ni en `fuera_del_project`
    # (si esta en el Project). Es una tarea invisible, y es justo el fallo que la
    # skill documenta: `item-add` son tres pasos y los dos ultimos se olvidan
    # porque no protestan.
    sin_estado = sorted(
        (i.get("content") or {}).get("number")
        for i in items
        if not (i.get("status") or "").strip()
        and (i.get("content") or {}).get("number") is not None
    )

    fuera = sorted(
        i["number"] for i in issues if i["number"] not in numeros_en_project
    )

    avisos = []
    if len(items) >= TOPE:
        avisos.append(
            "el Project devolvio %d items = el tope: HAY MAS y no se ven" % len(items)
        )
    if len(issues) >= TOPE:
        avisos.append(
            "los issues abiertos devolvieron %d = el tope: HAY MAS" % len(issues)
        )
    con_dueno = [t for t in disponibles if t["assignees"]]
    if con_dueno:
        avisos.append(
            "%d Disponible(s) CON assignee (estado y dueño no cuadran): %s"
            % (len(con_dueno), ", ".join("#%s" % t["numero"] for t in con_dueno))
        )
    if sin_estado:
        avisos.append(
            "%d item(s) SIN estado en el Project (invisibles para todos): %s"
            % (len(sin_estado), ", ".join("#%s" % n for n in sin_estado))
        )
    if borradores:
        avisos.append(
            "%d borrador(es) Disponible sin issue detras: no se pueden reclamar"
            % len(borradores)
        )
    # El tablero puede estar lleno y aun asi no ofrecer trabajo: si TODO lo
    # Disponible son avisos y decisiones, el dev que venga a reclamar se lleva
    # una vigilancia en vez de una tarea. Se denuncia en vez de dejar que lo
    # descubra al abrirla, porque `libres` no distingue una cosa de la otra.
    if libres and not any(TAREA.match(t["titulo"] or "") for t in libres):
        avisos.append(
            "lo Disponible (%d) son avisos o decisiones: NINGUNA es una tarea "
            "`T-nnn`, no hay trabajo reclamable en el tablero" % len(libres)
        )

    return {
        "yo": yo,
        "items": len(items),
        "issues_abiertos": len(issues),
        "mias": mias,
        "libres": libres,
        "fuera_del_project": fuera,
        "sin_estado": sin_estado,
        "avisos": avisos,
    }


def imprimir(estado: dict) -> None:
    print(
        "Project %s · %d items · %d issues abiertos · dev: %s"
        % (PROJECT_NUMBER, estado["items"], estado["issues_abiertos"], estado["yo"])
    )

    if estado["mias"]:
        print("\nYA TIENES asignadas (WIP max 1-2 — retomar antes que reclamar):")
        for t in estado["mias"]:
            print("  #%s %s" % (t["numero"], t["titulo"]))
    else:
        print("\nNo tienes ningun issue abierto asignado.")

    print("\nDisponibles y sin dueño (%d):" % len(estado["libres"]))
    for t in estado["libres"]:
        print("  #%s %s" % (t["numero"], t["titulo"]))
    if not estado["libres"]:
        print("  (ninguna)")

    fuera = estado["fuera_del_project"]
    print(
        "\nIssues abiertos FUERA del Project (%d)%s"
        % (len(fuera), ": " + " ".join("#%s" % n for n in fuera) if fuera else "")
    )
    if fuera:
        print("  -> nadie puede reclamarlos hasta añadirlos (item-add + estado + label)")

    if estado["avisos"]:
        print("\nAVISOS:")
        for a in estado["avisos"]:
            print("  ! %s" % a)


def main(argv: list[str]) -> int:
    # En Windows desde Git Bash `sys.stdout` es cp1252, y basta con que UN item
    # del Project lleve un caracter que cp1252 no sepa imprimir (⚠️, 🟡...) para
    # que el script muera con UnicodeEncodeError JUSTO al listar las candidatas,
    # que es para lo que existe. `_gh` ya leia en utf-8; falta la otra mitad, la
    # escritura.
    #
    # `errors="replace"` y no `strict`: si mañana aparece algo que ni utf-8 puede
    # representar, el reclamo sale con un `?` en un titulo — nunca se cae. Un
    # candado que se cae por un emoji no es un candado.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass  # stdout sustituido (tests) o no reconfigurable: no es motivo para parar

    estado = reunir()
    if "--json" in argv:
        print(json.dumps(estado, ensure_ascii=False))
    else:
        imprimir(estado)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
