#!/usr/bin/env python3
"""Texto del aviso de la auditoria programada: que dice el issue.

Separado de `audit_report.py` a proposito: aquel decide *que hacer* (abrir,
actualizar, cerrar o callarse) y habla con `gh`; este decide *que se dice*. La
division no es estetica — el texto es lo unico que se puede comprobar sin red, y
esa era la costura real.

Estilo: ASCII sin tildes, como el resto de guardas — el texto viaja a logs de
runner y a consolas Windows.

Tests: python3 scripts/test_audit_report.py
"""

from __future__ import annotations

import hashlib
import os
import re

# El cuerpo de un issue de GitHub topa en 65536 caracteres. Se trunca muy por
# debajo: el log completo esta en el runner, aqui solo hace falta el diagnostico.
MAX_LOG = 25000

# Las lineas de problema que imprime `scripts/audit_check.py` ("  - <problema>").
#
# ACOPLAMIENTO DECLARADO: si cambia el formato de esa salida, esta expresion deja
# de encontrar nada y el aviso se abre sin lista de problemas — degradado, no
# roto, pero peor. En el proyecto de origen este acoplamiento existia sin estar
# escrito en ninguno de los dos ficheros, y se anoto como deuda en su review.
RE_PROBLEMA = re.compile(r"^ {2}- (.+)$")

# Marca de la huella en el cuerpo. Es como se sabe, sin estado externo, si lo que
# falla hoy es lo mismo que fallaba ayer.
RE_HUELLA = re.compile(r"<!-- audit-huella: ([0-9a-f]{12}) -->")


def analizar(log: str) -> tuple[list[str], str]:
    """Extrae los problemas del log y calcula su huella.

    La huella se calcula sobre el CONJUNTO de problemas, no sobre el log entero:
    el log trae recuentos y texto informativo que cambian sin que cambie nada
    real, y eso convertiria el anti-ruido en ruido diario.
    """
    problemas = [m.group(1).strip() for m in map(RE_PROBLEMA.match, log.splitlines()) if m]

    if problemas:
        base = "\n".join(sorted(problemas))
    else:
        # Fallo sin problemas listados (gestor ausente, JSON ilegible, runner
        # roto...). No es una vulnerabilidad: es la auditoria que no pudo
        # concluir, y se avisa igual pero sin disfrazarla de lo otro.
        base = " ".join(log.split())[:2000] or "sin-log"

    return problemas, hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]


def enlace_ejecucion() -> str:
    """URL de la ejecucion del workflow, para poder leer el log del runner."""
    servidor = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if repo and run_id:
        return f"{servidor}/{repo}/actions/runs/{run_id}"
    return "(ejecucion local)"


def construir_titulo(problemas: list[str], ejecutada: bool) -> str:
    if not ejecutada:
        return "[auto] La auditoria programada de `main` no pudo ejecutarse"
    if not problemas:
        return "[auto] La auditoria de `main` fallo sin listar problemas"
    plural = "s" if len(problemas) != 1 else ""
    return f"[auto] Auditoria de `main` en rojo: {len(problemas)} problema{plural}"


def _cabecera(problemas: list[str], ejecutada: bool) -> str:
    if not ejecutada:
        return (
            "## La auditoria NO llego a ejecutarse\n\n"
            "El paso de auditoria no dejo resultado, asi que **no se sabe** si "
            "`main` esta limpio. Esto no se cuenta como verde a proposito: no "
            "poder comprobarlo no es estar en regla.\n"
        )
    if problemas:
        return "## Problemas detectados\n\n" + "\n".join(f"- {p}" for p in problemas) + "\n"
    return (
        "## La auditoria fallo sin listar problemas\n\n"
        "`scripts/audit_check.py` salio con codigo distinto de cero pero no "
        "imprimio ninguna linea de problema. Suele ser un fallo de la propia "
        "auditoria (gestor de paquetes ausente, JSON ilegible), no una "
        "vulnerabilidad. Mira el log.\n"
    )


def construir_cuerpo(problemas: list[str], log: str, huella: str, ejecutada: bool) -> str:
    """Cuerpo del issue.

    El log va dentro de un bloque cercado de CUATRO backticks: contiene texto de
    advisories publicados por terceros y podria traer ``` dentro, ademas de
    arrobas que fuera del bloque mencionarian a gente al azar.
    """
    log_recortado = log[:MAX_LOG]
    aviso_recorte = (
        ""
        if len(log) <= MAX_LOG
        else f"\n_(log recortado a {MAX_LOG} caracteres; el completo esta en la ejecucion)_\n"
    )

    return f"""> Issue **automatico**. Lo abre, lo actualiza y lo cierra el paso de aviso de
> `.github/workflows/audit.yml`. El cuerpo se sobrescribe cuando cambian los
> problemas: escribe el analisis en un comentario, no aqui.

La auditoria de dependencias falla sobre `main`. Nadie lo ha causado
necesariamente: los avisos se publican a cualquier hora contra dependencias
transitivas que nadie esta tocando. Llega como tarea propia y no como
interrupcion justamente para eso.

{_cabecera(problemas, ejecutada)}
## Antes de arreglarlo

**El arreglo correcto no es siempre el mismo**, y esto no es teorico: en el
proyecto donde nacio esta guarda, un aviso se resolvio con un override de version
y el siguiente demostro que el override era IMPOSIBLE, porque la version
parcheada rompia la herramienta que la arrastraba (`TypeError` al arrancar el
linter). Por eso este aviso no arregla nada solo: un bot que suba versiones a
ciegas habria tumbado la herramienta. Decide caso a caso:

1. Hay parche aguas arriba y el rango del padre lo admite -> **override acotado**.
   Mira el `git diff --stat` del lockfile, no solo que el audit quede verde: un
   `update` puede arrastrar decenas de paquetes de propina.
2. No hay arreglo aplicable -> **`security/audit-allowlist.json`**, con motivo
   **verificado contra el grafo real** y caducidad. Un motivo sin verificar
   convierte la allowlist en un registro de lo que creimos: ya paso una vez, con
   una aceptacion que afirmaba "solo llega por el tooling de desarrollo" cuando
   el propio audit la marcaba en la ruta de produccion.

## Log de la auditoria

````text
{log_recortado}
````
{aviso_recorte}
Ejecucion: {enlace_ejecucion()}

<!-- audit-huella: {huella} -->
"""
