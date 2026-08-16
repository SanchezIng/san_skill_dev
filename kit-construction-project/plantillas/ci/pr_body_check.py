#!/usr/bin/env python3
"""Guarda del cuerpo del PR: palabras clave de cierre que no cierran nada.

GitHub solo reconoce las closing keywords **en ingles**. Un equipo que escribe
los PRs en español acaba poniendo "Cierra #52", el PR se mergea, y el issue se
queda ABIERTO. Paso de verdad en el proyecto donde nacio esta guarda: el PR #53
llevaba `Cierra #52`, se mergeo y hubo que cerrar el issue a mano; el PR #57 con
`Closes #56` cerro el suyo solo. La unica diferencia era el idioma.

Sin una guarda esto se repite en cada PR, y el fallo es **silencioso**: nadie se
entera hasta que alguien mira la lista de issues y ve basura acumulada.

Falla si el cuerpo declara un cierre en español y NO trae el equivalente ingles
apuntando al mismo numero de issue.

Se engancha en `pull_request` con el cuerpo pasado **por entorno**, nunca
interpolado en el `run:` del workflow — ver el comentario de `docs-check.yml`.

Tests: python3 scripts/test_pr_body_check.py

Uso:
    python3 scripts/pr_body_check.py            # lee el cuerpo de $PR_BODY
    python3 scripts/pr_body_check.py fichero    # o de un fichero (para probarlo)
"""

from __future__ import annotations

import os
import re
import sys

# Verbos de cierre en español que la gente escribe creyendo que cierran el issue.
# Se aceptan con o sin tilde y en las personas que aparecen de verdad en los PRs.
ES = r"(?:cierra|cierran|cerrando|resuelve|resuelven|resolviendo|arregla|arreglan|corrige|corrigen|soluciona|solucionan|fija)"

# Las que GitHub reconoce de verdad (docs.github.com/issues/tracking-your-work).
EN = r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)"

RE_ES = re.compile(rf"\b{ES}\b\s*:?\s*#(\d+)", re.IGNORECASE)
RE_EN = re.compile(rf"\b{EN}\b\s*:?\s*#(\d+)", re.IGNORECASE)

# Zonas donde un verbo de cierre es una CITA, no una declaracion. Sin esto la
# guarda se dispara contra su propia documentacion: el PR que la introdujo
# explicaba el problema escribiendo `Cierra #52` en prosa, y el primer intento lo
# conto como un cierre de verdad, exigiendo cerrar un issue que no existia.
# Regla: si esta escrito como codigo o comentado, es cita. Una guarda ruidosa
# acaba desactivada, que es peor que no tenerla.
RE_IGNORAR = re.compile(
    r"<!--.*?-->"  # comentarios HTML (los de la plantilla de PR)
    r"|```.*?```"  # bloques de codigo cercados
    r"|`[^`\n]*`",  # code spans en linea
    re.DOTALL,
)


def revisar(cuerpo: str) -> list[str]:
    """Devuelve la lista de numeros declarados solo en español (vacia = todo bien)."""
    texto = RE_IGNORAR.sub("", cuerpo)

    en_numeros = {n for n in RE_EN.findall(texto)}
    problemas = []
    for numero in dict.fromkeys(RE_ES.findall(texto)):  # sin duplicados, en orden
        if numero not in en_numeros:
            problemas.append(numero)
    return problemas


def main() -> int:
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as fh:
            cuerpo = fh.read()
    else:
        cuerpo = os.environ.get("PR_BODY", "")

    if not cuerpo.strip():
        print("Cuerpo del PR vacio: nada que revisar.")
        return 0

    problemas = revisar(cuerpo)
    if not problemas:
        print("Cuerpo del PR OK: ningun cierre declarado en español sin su equivalente.")
        return 0

    lista = ", ".join(f"#{n}" for n in problemas)
    print(f"ERROR: el PR declara en español que cierra {lista}, pero GitHub NO lo hara.")
    print()
    print("GitHub solo reconoce las closing keywords en ingles. Tal como esta, el PR")
    print("se mergeara y esos issues seguiran ABIERTOS.")
    print()
    print("Arreglo: anade al cuerpo del PR una linea por issue, en ingles:")
    for numero in problemas:
        print(f"    Closes #{numero}")
    print()
    print("El resto del PR sigue en español; solo esa linea va en ingles.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
