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

# Entre el verbo y el `#N` se interpone lo que los equipos escriben de
# verdad — `Cierra **T-214 (#77)**` —, y exigirlos pegados hacia que la guarda
# dijera "OK" justo sobre lo que venia a cazar. NO se usa un comodin: un `.*`
# habria convertido "Cierra la sesion y abre #77" en un falso positivo, y una
# guarda ruidosa acaba desactivada, que es peor que no tenerla. Solo se admite
# lo que de verdad se interpone: enfasis markdown, un articulo, el id de tarea
# y el parentesis que lo envuelve. Repeticion ACOTADA a proposito, para que un
# cuerpo de PR raro no dispare backtracking exponencial.
CONECTOR = r"(?:[\s:*_(\[]|\b(?:el|la|los|las)\b|\bT-\d+\b){0,12}"

RE_ES = re.compile(rf"\b{ES}\b{CONECTOR}#(\d+)", re.IGNORECASE)

# El ingles se acepta SOLO en la forma que GitHub honra de verdad: la palabra
# clave y el `#N` sin nada en medio salvo enfasis o dos puntos. Los 25 PRs
# mergeados del proyecto piloto usan TODOS `Closes #N` pelado, o sea que no hay
# evidencia de que la forma decorada cierre nada — y darlo por supuesto es
# exactamente como se quedaron abiertos dos issues alli.
RE_EN = re.compile(rf"\b{EN}\b[\s:*_]{{0,6}}#(\d+)", re.IGNORECASE)

# Misma tolerancia que el español, para poder distinguir "no lo declaraste en
# ingles" de "lo declaraste en ingles pero GitHub no lo va a leer asi".
RE_EN_LAXO = re.compile(rf"\b{EN}\b{CONECTOR}#(\d+)", re.IGNORECASE)

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
    """Numeros declarados SOLO en español (lista vacia = todo bien)."""
    texto = RE_IGNORAR.sub("", cuerpo)

    en_numeros = {n for n in RE_EN.findall(texto)}
    problemas = []
    for numero in dict.fromkeys(RE_ES.findall(texto)):  # sin duplicados, en orden
        if numero not in en_numeros:
            problemas.append(numero)
    return problemas


def revisar_ingles_inerte(cuerpo: str) -> list[str]:
    """Numeros con palabra clave inglesa que GitHub NO va a parsear.

    `Closes **T-101 (#77)**` tiene el verbo correcto y aun asi deja
    el issue abierto, porque GitHub quiere la referencia pegada a la palabra
    clave. Es el mismo agujero que el del español —el PR se mergea y el issue
    se queda— pero con el sintoma invertido: aqui el autor CREE que lo hizo
    bien, asi que nadie lo revisa a mano.

    Se separa de `revisar()` porque el arreglo es distinto (no traducir, sino
    despegar la referencia) y porque el mensaje tiene que decir eso.
    """
    texto = RE_IGNORAR.sub("", cuerpo)

    validos = {n for n in RE_EN.findall(texto)}
    return [n for n in dict.fromkeys(RE_EN_LAXO.findall(texto)) if n not in validos]


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
    inertes = revisar_ingles_inerte(cuerpo)

    if not problemas and not inertes:
        print("Cuerpo del PR OK: todo cierre declarado lo va a ejecutar GitHub.")
        return 0

    if problemas:
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

    if inertes:
        if problemas:
            print()
        lista = ", ".join(f"#{n}" for n in inertes)
        print(f"ERROR: el PR usa la palabra clave inglesa para {lista}, pero con algo en")
        print("medio, y asi GitHub NO la parsea. El verbo es correcto; la referencia no")
        print("esta pegada a el.")
        print()
        print("Es el caso mas traicionero de los dos: el autor cree que lo hizo bien, asi")
        print("que nadie va a comprobar el issue a mano despues de mergear.")
        print()
        print("Arreglo: deja la referencia pelada y pegada a la palabra clave.")
        for numero in inertes:
            print(f"    Closes #{numero}          (no `Closes **T-nnn (#{numero})**`)")

    return 1


if __name__ == "__main__":
    sys.exit(main())
