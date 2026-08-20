#!/usr/bin/env python3
"""Tests del aviso de la auditoria programada (`audit_report.py` + `audit_issue_text.py`).

Que se prueba y por que: esta guarda existe para que un `main` roto llegue como
tarea con dueno ANTES de bloquear a nadie. Tiene cinco estados y **el que suele
faltar es el quinto**: que la auditoria no llegara a ejecutarse NO es que este
verde. Un aviso que se calla cuando no pudo mirar deja al equipo creyendo que hay
vigilancia cuando no la hay, que es peor que no tener ninguna.

Los cinco:

  verde + sin aviso   -> no hace nada, y lo dice
  verde + con aviso   -> comenta y CIERRA
  rojo  + sin aviso   -> ABRE
  rojo  + mismo rojo  -> CALLA (anti-ruido: un recordatorio diario identico se
                         acaba silenciando, y con el la guarda entera)
  no ejecutada        -> ABRE un aviso distinto que dice que no se pudo auditar

Se simula unicamente la frontera con `gh`. Lo demas corre de verdad.

Uso: python3 scripts/test_audit_report.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "audit_report.py"

CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


LOG_ROJO = """Auditoria de dependencias FALLIDA:
  - vulnerabilidad HIGH sin aceptar: fast-uri - GHSA-7p8r
  - vulnerabilidad HIGH sin aceptar: nanoid - GHSA-2v37
"""


def cargar(issues=None, exit_code="1", log=LOG_ROJO, extra_env=None, gh_falla=None):
    """El modulo con la frontera `gh` sustituida, y las llamadas registradas."""
    entorno = {"AUDIT_EXIT": exit_code}
    entorno.update(extra_env or {})
    previo = {k: os.environ.get(k) for k in
              ("AUDIT_EXIT", "AUDIT_DRY_RUN", "AUDIT_ISSUE_LABELS_EXTRA", "AUDIT_ISSUE_LABEL")}
    for k in previo:
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in entorno.items() if v is not None})

    if str(AQUI) not in sys.path:
        sys.path.insert(0, str(AQUI))
    spec = importlib.util.spec_from_file_location("audit_report", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    llamadas = []

    def falso_gh(*args):
        llamadas.append(list(args))
        if gh_falla is not None:
            raise gh_falla
        if args[0] == "issue" and args[1] == "list":
            return json.dumps(issues or [])
        return "https://github.com/x/y/issues/1\n"

    mod.gh = falso_gh
    mod.llamadas = llamadas
    mod._restaurar = previo
    return mod


def ejecutar(mod, log=LOG_ROJO, escribir_log=True, tmp=None):
    """Corre main() con un log en disco (o sin el)."""
    import tempfile
    carpeta = tmp or tempfile.mkdtemp()
    ruta = Path(carpeta) / "audit.log"
    if escribir_log:
        ruta.write_text(log, encoding="utf-8")
    argv = sys.argv
    sys.argv = ["audit_report.py", str(ruta)]
    try:
        return mod.main()
    finally:
        sys.argv = argv
        for k, v in mod._restaurar.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def acciones(mod) -> list[str]:
    """Los verbos de `gh` que se ejecutaron: create / comment / close / edit."""
    return [c[1] for c in mod.llamadas if c[0] == "issue"]


# --- los cinco estados ------------------------------------------------------

@caso("verde y sin aviso abierto: no toca nada")
def _():
    mod = cargar(issues=[], exit_code="0")
    assert ejecutar(mod, log="") == 0
    assert acciones(mod) == ["list"], mod.llamadas


@caso("verde con aviso abierto: comenta y CIERRA")
def _():
    mod = cargar(issues=[{"number": 7, "body": "<!-- audit-huella: abc123abc123 -->"}],
                 exit_code="0")
    assert ejecutar(mod, log="") == 0
    assert acciones(mod) == ["list", "comment", "close"], mod.llamadas


@caso("rojo y sin aviso: ABRE el issue con los problemas dentro")
def _():
    mod = cargar(issues=[], exit_code="1")
    assert ejecutar(mod) == 0
    assert acciones(mod) == ["list", "create"], mod.llamadas
    # El cuerpo viaja por `--body-file` y no como argumento (evita la inyeccion
    # de comandos con texto de advisories de terceros): su contenido se
    # comprueba en los casos de `audit_issue_text`, no aqui.


@caso("rojo con el MISMO rojo de ayer: no comenta (anti-ruido)")
def _():
    from audit_issue_text import analizar
    _p, huella = analizar(LOG_ROJO)
    mod = cargar(issues=[{"number": 7, "body": f"<!-- audit-huella: {huella} -->"}])
    assert ejecutar(mod) == 0
    assert acciones(mod) == ["list"], mod.llamadas


@caso("rojo con problemas DISTINTOS: actualiza el cuerpo y comenta el cambio")
def _():
    mod = cargar(issues=[{"number": 7, "body": "<!-- audit-huella: 000000000000 -->"}])
    assert ejecutar(mod) == 0
    assert acciones(mod) == ["list", "edit", "comment"], mod.llamadas


@caso("EL QUINTO: sin AUDIT_EXIT no es verde — abre aviso de 'no se pudo auditar'")
def _():
    mod = cargar(issues=[], exit_code=None)  # variable ausente
    assert ejecutar(mod) == 0
    assert acciones(mod) == ["list", "create"], mod.llamadas


@caso("EL QUINTO bis: con el log ausente tampoco se da por verde")
def _():
    # AUDIT_EXIT dice 0, pero el log no esta: el paso anterior no dejo rastro, y
    # "no pude mirar" no es "esta limpio". Se comprueba ademas el TITULO, porque
    # abrir el aviso equivocado (uno que dice "en rojo: N problemas") contaria
    # una historia falsa sobre un repo que quiza este sano.
    mod = cargar(issues=[], exit_code="0")
    assert ejecutar(mod, escribir_log=False) == 0
    assert acciones(mod) == ["list", "create"], mod.llamadas
    create = [c for c in mod.llamadas if len(c) > 1 and c[1] == "create"][0]
    titulo = create[create.index("--title") + 1]
    assert "no pudo ejecutarse" in titulo, titulo


@caso("AUDIT_EXIT que no es un numero: se trata como fallo, no como verde")
def _():
    mod = cargar(issues=[], exit_code="pendiente")
    assert ejecutar(mod) == 0
    assert acciones(mod) == ["list", "create"], mod.llamadas


# --- si no puede avisar, no devuelve 0 --------------------------------------

@caso("`gh` en error: NO se traga — propaga ErrorDeAviso")
def _():
    mod = cargar(issues=[])
    mod.gh = lambda *a: (_ for _ in ()).throw(mod.ErrorDeAviso("403"))
    try:
        ejecutar(mod)
    except Exception as e:  # noqa: BLE001
        assert type(e).__name__ == "ErrorDeAviso", type(e)
        return
    raise AssertionError("no propago el error: la guardia se quedo muda en verde")


# --- la huella, que es todo el anti-ruido -----------------------------------

@caso("misma huella si los problemas son los mismos en otro orden")
def _():
    from audit_issue_text import analizar
    a = "Auditoria FALLIDA:\n  - uno\n  - dos\n"
    b = "Auditoria FALLIDA:\n  - dos\n  - uno\n"
    assert analizar(a)[1] == analizar(b)[1]


@caso("misma huella aunque el resto del log cambie (recuentos, tiempos)")
def _():
    from audit_issue_text import analizar
    a = "234 paquetes auditados en 3s\n  - uno\n"
    b = "998 paquetes auditados en 11s\n  - uno\nresumen distinto\n"
    assert analizar(a)[1] == analizar(b)[1]


@caso("huella DISTINTA si aparece un problema nuevo")
def _():
    from audit_issue_text import analizar
    assert analizar("  - uno\n")[1] != analizar("  - uno\n  - dos\n")[1]


@caso("fallo sin problemas listados: no se disfraza de vulnerabilidad")
def _():
    from audit_issue_text import analizar, construir_titulo
    problemas, _h = analizar("pnpm: command not found\n")
    assert problemas == []
    assert "sin listar problemas" in construir_titulo(problemas, ejecutada=True)


# --- el texto del issue -----------------------------------------------------

@caso("el cuerpo lleva la huella y el log en bloque de CUATRO backticks")
def _():
    from audit_issue_text import RE_HUELLA, analizar, construir_cuerpo
    problemas, huella = analizar(LOG_ROJO)
    cuerpo = construir_cuerpo(problemas, LOG_ROJO, huella, ejecutada=True)
    m = RE_HUELLA.search(cuerpo)
    assert m and m.group(1) == huella, cuerpo[-200:]
    assert "````text" in cuerpo, "el log iria en un bloque que su propio contenido puede cerrar"


@caso("un log gigante se recorta y el cuerpo lo DICE")
def _():
    from audit_issue_text import MAX_LOG, analizar, construir_cuerpo
    log = "  - uno\n" + ("x" * (MAX_LOG + 5000))
    problemas, huella = analizar(log)
    cuerpo = construir_cuerpo(problemas, log, huella, ejecutada=True)
    assert "recortado" in cuerpo
    assert len(cuerpo) < MAX_LOG + 5000


@caso("el aviso de 'no ejecutada' dice que NO cuenta como verde")
def _():
    from audit_issue_text import construir_cuerpo, construir_titulo
    cuerpo = construir_cuerpo([], "", "0" * 12, ejecutada=False)
    assert "no se sabe" in cuerpo.lower()
    assert "no pudo ejecutarse" in construir_titulo([], ejecutada=False)


# --- etiquetas: no inventar las que el repo no tiene ------------------------

@caso("por defecto solo se pone la etiqueta del aviso (una que no existe falla el `gh`)")
def _():
    mod = cargar(issues=[])
    ejecutar(mod)
    create = [c for c in mod.llamadas if len(c) > 1 and c[1] == "create"][0]
    assert create.count("--label") == 1, create


@caso("con AUDIT_ISSUE_LABELS_EXTRA se anaden, separadas por coma")
def _():
    mod = cargar(issues=[], extra_env={"AUDIT_ISSUE_LABELS_EXTRA": "modulo:comun, seguridad"})
    ejecutar(mod)
    create = [c for c in mod.llamadas if len(c) > 1 and c[1] == "create"][0]
    assert create.count("--label") == 3, create
    assert "modulo:comun" in create and "seguridad" in create, create


def main() -> int:
    fallidos = 0
    for nombre, prueba in CASOS:
        try:
            prueba()
            print(f"  ok    {nombre}")
        except AssertionError as e:
            fallidos += 1
            print(f"  FALLO {nombre}\n        {e}")
        except Exception as e:  # noqa: BLE001
            fallidos += 1
            print(f"  ERROR {nombre}\n        {type(e).__name__}: {e}")
    print(f"\n{len(CASOS) - fallidos}/{len(CASOS)} casos OK")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
