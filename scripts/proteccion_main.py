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

# CONFIGURACION DE ESTE REPO (catalogo de skills, sin protocolo de equipo).
#
# Sin excepciones: aqui no hay tablero markdown que haga de candado, asi que
# nada justifica saltarse el PR.
PREFIJOS_PERMITIDOS: tuple[str, ...] = ()

# En falso MIENTRAS SE TRABAJE EN SOLITARIO. GitHub no deja aprobar tu propio
# PR, asi que exigir una aprobacion con un solo dev bloquea el 100% del trabajo
# y acabaria con la guarda desactivada — que es peor que tenerla en modo suave.
# Lo que si se exige es que todo pase por PR: diff revisable, CI ejecutado,
# historia limpia. PONER A True EN CUANTO ENTRE UN SEGUNDO DEV.
EXIGIR_REVISION = False

SHA_NULO = "0" * 40


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
