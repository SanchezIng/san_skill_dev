#!/usr/bin/env python3
"""Guardas de deriva doc<->realidad.

1. Enlaces markdown relativos rotos: un doc que apunta a un archivo que ya no
   existe miente, y un doc que miente envenena a cualquier lector (humano o LLM)
   con confianza falsa.
2. Coherencia backlog<->issues (se salta sin token o sin `gh`). Se adapta al modo
   del proyecto, detectado por la presencia de `(#N)` en las cabeceras:

   - Sin espejado a GitHub (ninguna tarea trae `(#N)`): el backlog es la unica
     fuente de estado. No hay nada contra que cotejar -> la guarda se salta.
   - Con espejado: toda T-nnn debe declarar un issue y ese issue debe existir
     (caza tareas inventadas en el doc e issues borrados). Ademas, si el backlog
     conserva el campo `Estado:`, una tarea `Done` obliga a issue cerrado.

   Recomendacion al espejar: quitar `Estado:` del backlog y dejar el estado solo
   en el Project. Un estado duplicado en dos sitios se desfasa, y el que se
   desfasa es el del doc, porque ningun automatismo lo lee. Ver trabajo_en_equipo.md §6.

Uso: python3 scripts/docs_check.py   (desde la raiz del repo; exit 1 si hay fallos)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Ruta del backlog relativa a la raiz del repo (placeholder: se rellena al instalar).
RUTA_BACKLOG = "{{RUTA_BACKLOG}}"

# Solo archivos trackeados: lo no versionado (notas locales) no se audita.
ARBOLES = ["CLAUDE.md", "README.md", "ROADMAP.md", "docs", "progreso"]

ENLACE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^(```|~~~)")

# Formato del backlog que genera el kickstart (trabajo_en_equipo.md §6):
#   ### T-014 · [B] Endpoint POST /facturas (#14)   ← (#N) al espejar como issues
#   - Estado: Done                                  ← solo si NO se espeja a GitHub
CABECERA_TAREA = re.compile(r"### (T-\d+)\b(?:.*\(#(\d+)\))?")
ESTADO_DONE = re.compile(r"^[-*]?\s*Estado:\s*\**\s*Done\b", re.IGNORECASE)


def archivos_md() -> list[Path]:
    salida = subprocess.run(
        ["git", "ls-files", "--", *ARBOLES],
        cwd=RAIZ, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return [RAIZ / linea for linea in salida if linea.endswith(".md")]


def enlaces_rotos() -> list[str]:
    fallos = []
    for archivo in archivos_md():
        en_fence = False
        for num, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
            if FENCE.match(linea.strip()):
                en_fence = not en_fence
                continue
            if en_fence:
                continue
            for destino in ENLACE.findall(linea):
                if destino.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                ruta = destino.split("#", 1)[0]
                if not ruta:
                    continue
                # Vale relativo al archivo O relativo a la raiz del repo
                if (archivo.parent / ruta).exists() or (RAIZ / ruta).exists():
                    continue
                rel = archivo.relative_to(RAIZ)
                fallos.append(f"{rel}:{num}: enlace roto -> {destino}")
    return fallos


def backlog_incoherente() -> list[str]:
    if not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"):
        print("(sin GH_TOKEN: se salta la coherencia backlog<->issues)")
        return []
    try:
        crudo = subprocess.run(
            ["gh", "issue", "list", "--state", "all", "--limit", "300",
             "--json", "number,state"],
            cwd=RAIZ, capture_output=True, text=True, check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"(gh no disponible, se salta la coherencia backlog<->issues: {e})")
        return []

    estados = {i["number"]: i["state"] for i in json.loads(crudo)}
    contenido = (RAIZ / RUTA_BACKLOG).read_text(encoding="utf-8")

    tareas = []
    for seccion in re.split(r"\n(?=### )", contenido):
        lineas = seccion.splitlines()
        m = CABECERA_TAREA.match(lineas[0]) if lineas else None
        if m:
            hecha = any(ESTADO_DONE.match(l.strip()) for l in lineas[1:])
            tareas.append((m.group(1), m.group(2), hecha))

    # Modo del proyecto: si ninguna tarea declara issue, el backlog no esta
    # espejado a GitHub y es la unica fuente de estado -> nada que cotejar.
    if not any(numero for _, numero, _ in tareas):
        print("(backlog sin espejar a issues: se salta la coherencia backlog<->issues)")
        return []

    fallos = []
    for tarea, numero, hecha in tareas:
        if numero is None:
            fallos.append(
                f"{RUTA_BACKLOG}: {tarea} no declara su issue (#N en la cabecera)"
            )
        elif int(numero) not in estados:
            fallos.append(
                f"{RUTA_BACKLOG}: {tarea} apunta al issue #{numero}, que no existe en GitHub"
            )
        elif hecha and estados[int(numero)] == "OPEN":
            # Solo aplica si el backlog conserva `Estado:` (proyectos que no
            # migraron el estado al Project). Ver cabecera del modulo.
            fallos.append(
                f"{RUTA_BACKLOG}: {tarea} marcada Done pero el issue #{numero} sigue OPEN"
            )
    return fallos


def main() -> int:
    fallos = enlaces_rotos() + backlog_incoherente()
    for fallo in fallos:
        print(f"FALLO {fallo}")
    if fallos:
        print(f"\n{len(fallos)} problema(s) de coherencia en la documentacion.")
        return 1
    print("Documentacion coherente: enlaces OK, backlog<->issues OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
