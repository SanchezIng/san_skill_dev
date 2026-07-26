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
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Commits que SI pueden ir directo a main. En un proyecto sin GitHub Project el
# tablero es el candado de reclamo y tiene que publicarse al instante (ver
# trabajo_en_equipo.md §9). Si el proyecto usa Project, deja esto vacio: ahi el
# candado vive en GitHub y nada necesita saltarse el PR.
PREFIJOS_PERMITIDOS: tuple[str, ...] = ("chore(tablero):",)

# Exigir >=1 aprobacion humana en el PR de origen. La regla del kit es
# "respondes por lo que tu Claude Code genero": sin revision, no se mergea.
EXIGIR_REVISION = True

SHA_NULO = "0" * 40


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True,
                          text=True, check=True).stdout.strip()


def _api(ruta: str) -> list | dict:
    """GET a la API de GitHub. Punto unico de contacto con la red: los tests lo
    sustituyen para no depender de un repo real."""
    salida = subprocess.run(
        ["gh", "api", ruta], cwd=RAIZ, capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(salida) if salida.strip() else []


def commits_nuevos(antes: str, ahora: str) -> list[str]:
    if antes in ("", SHA_NULO):
        # Primer push de la rama: no hay rango anterior con el que comparar.
        return []
    return [c for c in _git("rev-list", f"{antes}..{ahora}").splitlines() if c]


def _asunto(sha: str) -> str:
    return _git("log", "-1", "--format=%s", sha)


def _es_merge(sha: str) -> bool:
    return len(_git("log", "-1", "--format=%P", sha).split()) > 1


def revisar(antes: str, ahora: str) -> list[str]:
    fallos: list[str] = []
    for sha in commits_nuevos(antes, ahora):
        asunto = _asunto(sha)
        corto = sha[:8]

        if asunto.startswith(PREFIJOS_PERMITIDOS):
            continue
        if _es_merge(sha):
            # El merge del propio PR: lo que se juzga son sus commits.
            continue

        prs = _api(f"repos/{{owner}}/{{repo}}/commits/{sha}/pulls")
        if not prs:
            fallos.append(
                f"{corto} \"{asunto}\" llego a main sin PR (push directo)"
            )
            continue

        if not EXIGIR_REVISION:
            continue

        numero = prs[0].get("number")
        revisiones = _api(f"repos/{{owner}}/{{repo}}/pulls/{numero}/reviews")
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
    if fallos:
        print(f"\n{len(fallos)} commit(s) entraron a main saltandose el protocolo.")
        print("Esta guarda no puede impedirlo (hace falta proteccion de rama, que")
        print("exige repo publico o GitHub Pro). Lo que hace es que no pase")
        print("inadvertido: revisa el cambio y, si procede, revierte o abre el PR.")
        return 1
    print("main integra: todo llego por PR revisado.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
