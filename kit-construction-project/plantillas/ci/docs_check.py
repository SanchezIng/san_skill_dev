#!/usr/bin/env python3
"""Guardas de deriva doc<->realidad.

1. Enlaces markdown relativos rotos: un doc que apunta a un archivo que ya no
   existe miente, y un doc que miente envenena a cualquier lector (humano o LLM)
   con confianza falsa.
2. Coherencia backlog<->issues (se salta sin token o sin `gh`), en tres modos
   segun MODO_BACKLOG:

   - "local": el backlog es la unica fuente de estado (campo `Estado:` a mano).
     No hay contra que cotejar -> la guarda se salta.
   - "espejado": el estado vive en el Project. TODA T-nnn debe declarar su issue
     y ese issue debe existir. Es el modo estricto: activalo cuando el espejado
     ya este completo.
   - "auto" (por defecto): se valida lo que se puede verificar. Las tareas que
     declaran `(#N)` se comprueban a fondo; las que no, salen como AVISO y no
     tumban el CI. Asi el arranque (crear los issues uno a uno, paso 2 del
     README) no deja el CI en rojo a medio camino, y aun asi nadie se olvida de
     terminar el espejado.

   Recomendacion al espejar: quitar `Estado:` del backlog y dejar el estado solo
   en el Project. Un estado duplicado en dos sitios se desfasa, y el que se
   desfasa es el del doc, porque ningun automatismo lo lee. Ver trabajo_en_equipo.md §6.

Uso:   python3 scripts/docs_check.py        (desde la raiz; exit 1 si hay fallos)
Tests: python3 scripts/test_docs_check.py   (las guardas tambien se prueban)
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

# "auto" | "espejado" | "local". Ver cabecera del modulo.
# "auto" | "espejado" | "local". Ver cabecera del modulo.
MODO_BACKLOG = "auto"

# Solo archivos trackeados: lo no versionado (notas locales) no se audita.
ARBOLES = ["CLAUDE.md", "README.md", "ROADMAP.md", "docs", "progreso"]

ENLACE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^(```|~~~)")

# Formato del backlog que genera el kickstart (trabajo_en_equipo.md §6):
#   ### T-014 · [B] Endpoint POST /facturas (#14)   ← (#N) al espejar como issues
#   - Estado: Done                                  ← solo en modo "local"
CABECERA_TAREA = re.compile(r"### (T-\d+)\b(?:.*\(#(\d+)\))?")
ESTADO_DONE = re.compile(r"^[-*]?\s*Estado:\s*\**\s*Done\b", re.IGNORECASE)

# Tope de comprobaciones individuales contra la API (una peticion por issue que
# no venia en el listado masivo). Por encima, se informa en vez de acusar.
MAX_COMPROBACIONES = 50

# Ruta del ROADMAP relativa a la raiz. Vacia => no se comprueba el contador.
RUTA_ROADMAP = "ROADMAP.md"

# El ROADMAP declara su avance TRES veces: la tabla de cabecera (dos filas) y la
# frase en prosa. Son tres copias del mismo hecho, escritas a mano, y por eso se
# desincronizan. Lo que sigue las coteja contra las marcas reales del documento.
SECCION_FASE = re.compile(r"^### F\d+")
SUBFASE = re.compile(r"^- (\S+) F\d+\.\d+")
ESTADO_FASE = re.compile(r"^\*\*Estado:\*\*\s*(\S+)")
FILA_COMPLETADAS = re.compile(r"^\|\s*Completadas\s*\|\s*(\d+)\s*/\s*(\d+)\s*\|")
FILA_SUBFASES = re.compile(r"^\|\s*Subfases totales\s*\|\s*(\d+)\s*\|")
FILA_AVANCE = re.compile(r"^\|\s*%\s*avance\s*\|\s*(\d+)\s*%\s*\|")
PROSA_COMPLETADAS = re.compile(r"^Las (\d+),\s+en orden de cierre")
HECHO = "✅"


def _lineas_fuera_de_fence(texto: str) -> list[str]:
    """Lineas que NO estan dentro de un bloque ``` o ~~~.

    Un ejemplo de formato dentro de un bloque de codigo no es una tarea real:
    tratarlo como tal convierte la documentacion del propio backlog en un fallo
    de CI.
    """
    fuera: list[str] = []
    en_fence = False
    for linea in texto.splitlines():
        if FENCE.match(linea.strip()):
            en_fence = not en_fence
            continue
        if not en_fence:
            fuera.append(linea)
    return fuera


def archivos_md() -> list[Path]:
    try:
        salida = subprocess.run(
            ["git", "ls-files", "--", *ARBOLES],
            cwd=RAIZ, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"(git no disponible, se salta la revision de enlaces: {e})")
        return []
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


def _issue_existe(numero: int) -> bool | None:
    """True / False / None (no se ha podido comprobar).

    El listado masivo tiene tope, y los que se quedan fuera son los MAS VIEJOS:
    justo las primeras tareas del proyecto. Dar por inexistente lo que solo esta
    fuera del tope es acusar en falso, asi que se confirma uno a uno.
    """
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{{owner}}/{{repo}}/issues/{numero}", "--jq", ".number"],
            cwd=RAIZ, capture_output=True, text=True,
        )
    except FileNotFoundError:
        return None
    if r.returncode == 0:
        return True
    if "404" in (r.stderr or "") or "Not Found" in (r.stderr or ""):
        return False
    return None


def tareas_del_backlog(contenido: str) -> list[tuple[str, str | None, bool]]:
    """[(tarea, numero_de_issue|None, marcada_Done)] ignorando bloques de codigo."""
    texto = "\n".join(_lineas_fuera_de_fence(contenido))
    tareas = []
    for seccion in re.split(r"\n(?=### )", texto):
        lineas = seccion.splitlines()
        m = CABECERA_TAREA.match(lineas[0]) if lineas else None
        if m:
            hecha = any(ESTADO_DONE.match(l.strip()) for l in lineas[1:])
            tareas.append((m.group(1), m.group(2), hecha))
    return tareas


def backlog_incoherente() -> list[str]:
    if MODO_BACKLOG == "local":
        print("(MODO_BACKLOG=local: el estado vive en el backlog, no hay issues que cotejar)")
        return []
    if MODO_BACKLOG not in ("auto", "espejado"):
        return [f"scripts/docs_check.py: MODO_BACKLOG='{MODO_BACKLOG}' no es valido "
                f"(usa 'auto', 'espejado' o 'local')"]

    if "{{" in RUTA_BACKLOG:
        print("(RUTA_BACKLOG sin rellenar en scripts/docs_check.py: se salta la "
              "coherencia backlog<->issues. Pon ahi la ruta real, p.ej. docs/backlog.md)")
        return []
    backlog = RAIZ / RUTA_BACKLOG
    if not backlog.exists():
        return [f"scripts/docs_check.py apunta a {RUTA_BACKLOG}, que no existe "
                f"(corrige RUTA_BACKLOG o restaura el archivo)"]

    if not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"):
        print("(sin GH_TOKEN: se salta la coherencia backlog<->issues)")
        return []
    try:
        crudo = subprocess.run(
            ["gh", "issue", "list", "--state", "all", "--limit", "1000",
             "--json", "number,state"],
            cwd=RAIZ, capture_output=True, text=True, check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"(gh no disponible, se salta la coherencia backlog<->issues: {e})")
        return []

    estados = {i["number"]: i["state"] for i in json.loads(crudo)}
    tareas = tareas_del_backlog(backlog.read_text(encoding="utf-8"))
    sin_issue = [t for t, numero, _ in tareas if numero is None]

    if not any(numero for _, numero, _ in tareas):
        if MODO_BACKLOG == "auto":
            print("(backlog sin espejar a issues: se salta la coherencia backlog<->issues)")
            return []
        return [f"{RUTA_BACKLOG}: MODO_BACKLOG='espejado' pero ninguna tarea declara "
                f"su issue (#N en la cabecera)"]

    fallos = []
    comprobaciones = 0
    for tarea, numero, hecha in tareas:
        if numero is None:
            if MODO_BACKLOG == "espejado":
                fallos.append(
                    f"{RUTA_BACKLOG}: {tarea} no declara su issue (#N en la cabecera)"
                )
            continue
        n = int(numero)
        if n not in estados:
            # Puede ser un issue borrado... o uno viejo fuera del tope del listado.
            if comprobaciones >= MAX_COMPROBACIONES:
                print(f"(AVISO {tarea}: el issue #{n} no salio en el listado y se "
                      f"alcanzo el tope de comprobaciones; queda sin verificar)")
                continue
            comprobaciones += 1
            existe = _issue_existe(n)
            if existe is False:
                fallos.append(
                    f"{RUTA_BACKLOG}: {tarea} apunta al issue #{n}, que no existe en GitHub"
                )
            elif existe is None:
                print(f"(AVISO {tarea}: no se pudo comprobar el issue #{n})")
            continue
        if hecha and estados[n] == "OPEN":
            # Solo aplica si el backlog conserva `Estado:` (proyectos en modo
            # local que ya usaban el campo). Ver cabecera del modulo.
            fallos.append(
                f"{RUTA_BACKLOG}: {tarea} marcada Done pero el issue #{n} sigue OPEN"
            )

    if sin_issue and MODO_BACKLOG == "auto":
        print(f"(AVISO espejado incompleto: {len(sin_issue)} tarea(s) sin issue declarado: "
              f"{', '.join(sin_issue[:8])}{'...' if len(sin_issue) > 8 else ''}. "
              f"Al terminar de espejar, pon MODO_BACKLOG='espejado' para exigirlo)")
    return fallos


def _avance_real(texto: str) -> tuple[int, int]:
    """(completadas, totales) contando las MARCAS del ROADMAP, no lo que declara.

    Se cuenta por estructura y no por la frase "sin subfases": una fase con
    subfases aporta sus subfases; una fase sin ellas aporta 1, hecha o no. Asi
    la cuenta no depende de que nadie olvide escribir una coletilla.
    """
    completadas = totales = 0
    # Se corta tambien en `## ` y no solo en `### ` (lo cazo una review en un proyecto real): si no, todo
    # lo que va DETRAS de la ultima fase —`## Hitos clave`, `## Bitacora de
    # cierres`— sigue dentro de su bloque, y una viñeta `- ✅ Fn.m` escrita alli
    # (la bitacora pide justo eso al cerrar cada subfase) subiria el total en
    # silencio. Los trozos que abren con `## ` no casan SECCION_FASE y se
    # descartan solos.
    for seccion in re.split(r"\n(?=#{2,3} )", "\n".join(_lineas_fuera_de_fence(texto))):
        lineas = seccion.splitlines()
        if not lineas or not SECCION_FASE.match(lineas[0]):
            continue
        subfases = [m.group(1) for m in (SUBFASE.match(l) for l in lineas) if m]
        if subfases:
            totales += len(subfases)
            completadas += sum(1 for e in subfases if e == HECHO)
            continue
        # Fase sin subfases (F3, F6): cuenta como una, y su estado es el de la
        # linea `**Estado:**`, que es donde vive su unica marca.
        estado = next((m.group(1) for m in (ESTADO_FASE.match(l) for l in lineas) if m), "")
        totales += 1
        completadas += 1 if estado.startswith(HECHO) else 0
    return completadas, totales


def roadmap_incoherente() -> list[str]:
    """El contador del ROADMAP contra sus propias marcas.

    Por que existe: el avance esta escrito a mano en TRES sitios y se calcula
    solo. Ya fallo dos veces. La segunda es la que justifica la guarda: dos
    ramas subieron el contador al MISMO numero por motivos distintos (una por
    F5.1, otra por F6), git auto-fusiono el texto identico sin marcar conflicto
    y el resultado quedo declarando una menos de las que habia. Un conflicto lo
    ve el que mergea; esto no lo ve nadie.
    """
    if not RUTA_ROADMAP:
        return []
    roadmap = RAIZ / RUTA_ROADMAP
    if not roadmap.exists():
        # No se calla: si la ruta apunta a un sitio que no existe, la guarda no
        # esta cubriendo lo que cree cubrir.
        return [f"scripts/docs_check.py apunta a {RUTA_ROADMAP}, que no existe "
                f"(corrige RUTA_ROADMAP o restaura el archivo)"]

    texto = roadmap.read_text(encoding="utf-8")
    completadas, totales = _avance_real(texto)
    if totales == 0:
        return [f"{RUTA_ROADMAP}: no se encontro ninguna fase (### Fn). La guarda del "
                f"contador no puede emitir veredicto: revisa el formato del documento"]

    lineas = _lineas_fuera_de_fence(texto)
    fallos = []

    def declarado(patron):
        return next((m for m in (patron.match(l) for l in lineas) if m), None)

    m = declarado(FILA_COMPLETADAS)
    if m is None:
        fallos.append(f"{RUTA_ROADMAP}: falta la fila '| Completadas | N / M |' de la tabla "
                      f"de cabecera; sin ella nadie sabe el avance de un vistazo")
    else:
        if int(m.group(1)) != completadas:
            fallos.append(f"{RUTA_ROADMAP}: la tabla dice {m.group(1)} subfases completadas "
                          f"y las marcas ✅ del propio documento son {completadas}")
        if int(m.group(2)) != totales:
            fallos.append(f"{RUTA_ROADMAP}: la tabla dice un total de {m.group(2)} subfases "
                          f"y las que sé leer en el documento son {totales} "
                          f"(revisa también que ninguna esté escrita en un formato "
                          f"distinto de `- ✅ Fn.m`)")

    m = declarado(FILA_SUBFASES)
    if m and int(m.group(1)) != totales:
        fallos.append(f"{RUTA_ROADMAP}: 'Subfases totales' dice {m.group(1)} y las que sé "
                      f"leer en el documento son {totales} (revisa también que ninguna "
                      f"esté escrita en un formato distinto de `- ✅ Fn.m`)")

    m = declarado(FILA_AVANCE)
    if m:
        esperado = round(100 * completadas / totales)
        # Tolerancia de 1 punto a proposito: quien lo escriba puede redondear de
        # otra forma y eso no es un defecto. Un rojo que no significa nada se
        # aprende a ignorar, y esta guarda existe justo para lo contrario.
        if abs(int(m.group(1)) - esperado) > 1:
            fallos.append(f"{RUTA_ROADMAP}: '% avance' dice {m.group(1)}% y "
                          f"{completadas}/{totales} es {esperado}%")

    m = declarado(PROSA_COMPLETADAS)
    if m and int(m.group(1)) != completadas:
        fallos.append(f"{RUTA_ROADMAP}: la frase 'Las {m.group(1)}, en orden de cierre' "
                      f"contradice a las marcas ✅, que son {completadas}")

    return fallos


def main() -> int:
    fallos = enlaces_rotos() + backlog_incoherente() + roadmap_incoherente()
    for fallo in fallos:
        print(f"FALLO {fallo}")
    if fallos:
        print(f"\n{len(fallos)} problema(s) de coherencia en la documentacion.")
        return 1
    print("Documentacion coherente: enlaces OK, backlog<->issues OK, contador del ROADMAP OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
