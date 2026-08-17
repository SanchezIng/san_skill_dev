#!/usr/bin/env python3
"""Aviso de la auditoria programada: abre, actualiza o cierra el issue de guardia.

Por que existe: el audit bloqueante solo corre cuando alguien abre un PR, asi que
un aviso publicado contra una dependencia transitiva **siempre lo descubre quien
venia a hacer otra cosa** — el peor momento posible. En el proyecto donde nacio
esta guarda, `main` se rompio TRES veces en un solo dia sin que nadie del equipo
tocara nada, y costo dos desvios completos a un dev que venia a otra tarea. Este
script es la mitad de "avisar" de la ejecucion programada: convierte el rojo en
una tarea con dueno ANTES de bloquear a nadie.

Deliberadamente NO arregla nada. Quedo demostrado que el arreglo correcto no es
siempre el mismo: un caso se resolvio con un override de version y el siguiente
demostro que el override era imposible, porque la version parcheada rompia el
linter que arrastraba el paquete. Un bot que suba versiones a ciegas habria
tumbado la herramienta.

Contrato (los cuatro estados, ninguno silencioso):

  AUDIT_EXIT=0 + hay aviso abierto -> comenta y CIERRA (main volvio a verde).
  AUDIT_EXIT=0 + no hay aviso      -> no hace nada, y lo dice.
  AUDIT_EXIT!=0 + no hay aviso     -> ABRE el issue con el log.
  AUDIT_EXIT!=0 + ya hay aviso     -> si los problemas son los mismos NO comenta
                                      (anti-ruido); si cambiaron, reescribe el
                                      cuerpo y comenta el cambio.

Y el quinto, que es el que suele faltar: si la auditoria **no llego a
ejecutarse** (AUDIT_EXIT vacio o log ausente), eso NO se trata como verde. Se
abre un aviso distinto, que dice que no se pudo auditar. Distinguir "la
respuesta es no" de "no pude preguntar" es una regla del kit; colapsarlas en un
valor es como una guarda acaba certificando lo que no llego a mirar.

El texto de los issues vive en scripts/audit_issue_text.py.

Tests: python3 scripts/test_audit_report.py

Uso:
    AUDIT_EXIT=1 python3 scripts/audit_report.py audit.log
    AUDIT_DRY_RUN=1 ...   # imprime lo que haria, sin tocar GitHub (pruebas)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from audit_issue_text import RE_HUELLA, analizar, construir_cuerpo, construir_titulo, enlace_ejecucion

# Etiqueta que identifica al aviso. La deduplicacion se hace POR ETIQUETA y no
# por titulo: el titulo lleva el numero de problemas y cambia solo.
ETIQUETA = os.environ.get("AUDIT_ISSUE_LABEL", "auditoria-automatica")

# Etiquetas adicionales del aviso (p.ej. "modulo:comun" en un proyecto con
# modulos). Vacio por defecto: `gh` FALLA si la etiqueta no existe en el repo,
# y un aviso que no se puede abrir es justo lo que esta guarda viene a evitar.
ETIQUETAS_EXTRA: list[str] = []
for _etiqueta in os.environ.get("AUDIT_ISSUE_LABELS_EXTRA", "").split(","):
    _etiqueta = _etiqueta.strip()
    if _etiqueta:
        ETIQUETAS_EXTRA += ["--label", _etiqueta]

DRY_RUN = os.environ.get("AUDIT_DRY_RUN") == "1"


class ErrorDeAviso(RuntimeError):
    """No se pudo hablar con GitHub.

    Nunca se traga: un aviso que falla en silencio deja al equipo creyendo que
    hay vigilancia cuando no la hay, que es peor que no tenerla.
    """


def gh(*args: str) -> str:
    """Ejecuta `gh` distinguiendo "GitHub dijo que no" de "no pude preguntar".

    El matiz esta comprobado: en Linux (el runner) un `gh` ausente llega como
    FileNotFoundError y se distingue del error de la API. En Windows, con
    shell=True, cmd.exe se lo traga y devuelve exit 1 — o sea que ahi los dos
    casos se ven iguales. Ambos fallan cerrado igualmente, que es lo que
    importa; lo que cambia es lo especifico del mensaje.
    """
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=sys.platform == "win32",
        )
    except FileNotFoundError as exc:  # gh no existe: no es un "no", es un mudo
        raise ErrorDeAviso(
            "no se encontro `gh` en el PATH. Sin CLI no hay aviso posible: "
            "se falla en rojo en vez de dar la ejecucion por buena."
        ) from exc

    if proc.returncode != 0:
        raise ErrorDeAviso(
            f"`gh {' '.join(args)}` fallo (exit {proc.returncode}): "
            f"{proc.stderr.strip() or '(sin stderr)'}"
        )
    return proc.stdout


def gh_mutacion(*args: str) -> str:
    """Igual que gh(), pero respeta el modo simulacion y lo grita."""
    if DRY_RUN:
        print(f"  [SIMULACION] gh {' '.join(args)}")
        return ""
    return gh(*args)


def escribir_temporal(texto: str) -> str:
    """Vuelca texto a un fichero temporal UTF-8 para pasarlo con --body-file.

    Nunca por argumento de linea de comandos: el cuerpo lleva titulos y URLs de
    advisories publicados por terceros, y meterlos en una shell es una via de
    inyeccion de comandos. Con --body-file el contenido no lo interpreta nadie.
    """
    fh = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8", newline="\n"
    )
    with fh:
        fh.write(texto)
    return fh.name


def buscar_aviso_abierto() -> dict | None:
    salida = gh(
        "issue", "list",
        "--label", ETIQUETA,
        "--state", "open",
        "--limit", "10",
        "--json", "number,body,title",
    )
    try:
        issues = json.loads(salida or "[]")
    except json.JSONDecodeError as exc:
        raise ErrorDeAviso(f"respuesta de `gh issue list` ilegible: {salida[:300]}") from exc

    if not issues:
        return None
    # El mas reciente manda. Si hubiera varios (alguien reabrio uno a mano), se
    # avisa: dos avisos abiertos es exactamente el ruido que esto evita.
    if len(issues) > 1:
        numeros = ", ".join(f"#{i['number']}" for i in issues)
        print(f"AVISO: hay {len(issues)} avisos abiertos con la etiqueta ({numeros}). "
              f"Se usa el primero; cierra los demas a mano.")
    return issues[0]


def cerrar_aviso(issue: dict) -> None:
    numero = str(issue["number"])
    cuerpo = (
        "`main` vuelve a estar en verde: la auditoria pasa sin "
        "vulnerabilidades fuera de la allowlist.\n\n"
        f"Cerrado automaticamente por la auditoria programada. "
        f"Ejecucion: {enlace_ejecucion()}"
    )
    ruta = escribir_temporal(cuerpo)
    try:
        gh_mutacion("issue", "comment", numero, "--body-file", ruta)
        gh_mutacion("issue", "close", numero, "--reason", "completed")
    finally:
        Path(ruta).unlink(missing_ok=True)
    print(f"Auditoria en verde: aviso #{numero} comentado y cerrado.")


def abrir_aviso(titulo: str, cuerpo: str) -> None:
    ruta = escribir_temporal(cuerpo)
    try:
        salida = gh_mutacion(
            "issue", "create",
            "--title", titulo,
            "--body-file", ruta,
            "--label", ETIQUETA,
            *ETIQUETAS_EXTRA,
        )
    finally:
        Path(ruta).unlink(missing_ok=True)
    print(f"Aviso ABIERTO: {salida.strip() or '(simulacion)'}")


def actualizar_aviso(issue: dict, titulo: str, cuerpo: str) -> None:
    numero = str(issue["number"])
    ruta_cuerpo = escribir_temporal(cuerpo)
    comentario = (
        "**El conjunto de problemas ha cambiado** desde la ultima ejecucion: el "
        "cuerpo del issue queda actualizado con el estado de hoy.\n\n"
        f"Ejecucion: {enlace_ejecucion()}"
    )
    ruta_comentario = escribir_temporal(comentario)
    try:
        gh_mutacion("issue", "edit", numero, "--title", titulo, "--body-file", ruta_cuerpo)
        gh_mutacion("issue", "comment", numero, "--body-file", ruta_comentario)
    finally:
        Path(ruta_cuerpo).unlink(missing_ok=True)
        Path(ruta_comentario).unlink(missing_ok=True)
    print(f"Aviso #{numero} ACTUALIZADO (los problemas cambiaron).")


def leer_resultado(ruta_log: Path) -> tuple[bool, int, str]:
    """Devuelve (la auditoria concluyo, codigo, log).

    "No pude preguntar" no es "la respuesta es no": sin codigo de salida
    o sin log, la auditoria no concluyo y se avisa, no se da por verde.
    """
    log = ruta_log.read_text(encoding="utf-8", errors="replace") if ruta_log.exists() else ""
    exit_txt = os.environ.get("AUDIT_EXIT", "").strip()

    if not exit_txt or not ruta_log.exists():
        faltan = []
        if not exit_txt:
            faltan.append("AUDIT_EXIT")
        if not ruta_log.exists():
            faltan.append(f"el log ({ruta_log})")
        print(f"La auditoria no dejo resultado: falta {' y '.join(faltan)}.")
        return False, 1, log or (
            "La auditoria no llego a ejecutarse: el paso anterior del workflow no "
            "dejo ni codigo de salida ni log.\n"
        )

    try:
        return True, int(exit_txt), log
    except ValueError:
        print(f"AUDIT_EXIT no es un numero ({exit_txt!r}): se trata como fallo.")
        return False, 1, log


def main() -> int:
    if DRY_RUN:
        print("MODO SIMULACION (AUDIT_DRY_RUN=1): no se tocara ningun issue.\n")

    ruta_log = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("audit.log")
    ejecutada, codigo, log = leer_resultado(ruta_log)

    aviso = buscar_aviso_abierto()

    if ejecutada and codigo == 0:
        if aviso:
            cerrar_aviso(aviso)
        else:
            print("Auditoria en verde y sin aviso abierto: nada que hacer.")
        return 0

    problemas, huella = analizar(log)
    cuerpo = construir_cuerpo(problemas, log, huella, ejecutada)
    titulo = construir_titulo(problemas, ejecutada)

    if aviso is None:
        abrir_aviso(titulo, cuerpo)
        return 0

    coincide = RE_HUELLA.search(aviso.get("body") or "")
    if coincide and coincide.group(1) == huella:
        print(
            f"El aviso #{aviso['number']} sigue vigente y con los mismos problemas "
            f"(huella {huella}): no se comenta nada. Un recordatorio diario "
            f"identico se convierte en ruido y acaba silenciado."
        )
        return 0

    actualizar_aviso(aviso, titulo, cuerpo)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErrorDeAviso as exc:
        print(f"\nERROR: no se pudo gestionar el aviso: {exc}", file=sys.stderr)
        sys.exit(1)
