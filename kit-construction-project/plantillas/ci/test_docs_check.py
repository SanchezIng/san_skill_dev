#!/usr/bin/env python3
"""Tests de la guarda docs_check.py.

Por que existen: una guarda que nunca se ha visto FALLAR no esta verificada.
Aqui cada regla se prueba en los dos sentidos — que deja pasar lo correcto y
que MUERDE lo incorrecto. Se simula unicamente la frontera con `gh`; el parseo
del backlog, los modos y los mensajes son los reales.

Uso: python3 scripts/test_docs_check.py     (exit 1 si algun caso falla)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "docs_check.py"


def cargar():
    spec = importlib.util.spec_from_file_location("docs_check", MODULO)
    dc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dc)
    return dc


class GhSimulado:
    """Sustituye solo las llamadas a `gh`. Todo lo demas pasa de largo."""

    def __init__(self, listado, existentes=None):
        self.listado = listado
        # Numeros que la API confirma aunque no salgan en el listado masivo.
        self.existentes = set(existentes or [n["number"] for n in listado])
        self.real = subprocess.run
        self.consultas_api = 0

    def __call__(self, cmd, **kw):
        if not cmd or cmd[0] != "gh":
            return self.real(cmd, **kw)
        if cmd[1] == "issue":
            return subprocess.CompletedProcess(cmd, 0, json.dumps(self.listado), "")
        self.consultas_api += 1
        numero = int(cmd[2].rsplit("/", 1)[-1])
        if numero in self.existentes:
            return subprocess.CompletedProcess(cmd, 0, str(numero), "")
        return subprocess.CompletedProcess(cmd, 1, "", "gh: Not Found (HTTP 404)")


def ejecutar(backlog, listado, existentes=None, modo="auto", ruta="docs/backlog.md",
             crear_backlog=True):
    """Devuelve (fallos, salida_impresa)."""
    dc = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        if crear_backlog:
            (raiz / "docs").mkdir(parents=True)
            (raiz / "docs" / "backlog.md").write_text(backlog, encoding="utf-8")
        dc.RAIZ = raiz
        dc.RUTA_BACKLOG = ruta
        dc.MODO_BACKLOG = modo
        dc.os.environ["GH_TOKEN"] = "test"
        dc.subprocess.run = GhSimulado(listado, existentes)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fallos = dc.backlog_incoherente()
        return fallos, buf.getvalue()


CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


ABIERTO = [{"number": 1, "state": "OPEN"}]
CERRADO = [{"number": 1, "state": "CLOSED"}]

TAREA_1 = "### T-001 · [A] Login (#1)\n- Modulo: A\n"
BOOTSTRAP = (TAREA_1 + "\n### T-002 · [A] Logout\n\n### T-003 · [B] API\n")


@caso("modo local: no cotejar nada")
def _():
    fallos, salida = ejecutar(TAREA_1, ABIERTO, modo="local")
    assert fallos == [], fallos
    assert "MODO_BACKLOG=local" in salida


@caso("auto + sin espejar: se salta")
def _():
    fallos, salida = ejecutar("### T-001 · [A] Login\n- Estado: Done\n", [])
    assert fallos == [], fallos
    assert "sin espejar" in salida


@caso("auto + espejado coherente: pasa")
def _():
    fallos, _s = ejecutar(TAREA_1, CERRADO)
    assert fallos == [], fallos


@caso("auto + espejado A MEDIAS: avisa pero NO tumba el CI")
def _():
    fallos, salida = ejecutar(BOOTSTRAP, ABIERTO)
    assert fallos == [], fallos
    assert "espejado incompleto" in salida
    assert "T-002" in salida and "T-003" in salida


@caso("espejado (estricto): las tareas sin issue MUERDEN")
def _():
    fallos, _s = ejecutar(BOOTSTRAP, ABIERTO, modo="espejado")
    assert len(fallos) == 2, fallos
    assert "T-002 no declara su issue" in fallos[0]


@caso("issue viejo fuera del listado pero existente: NO se acusa")
def _():
    # El listado masivo tiene tope y deja fuera a los mas viejos.
    listado = [{"number": n, "state": "OPEN"} for n in range(400, 100, -1)]
    fallos, _s = ejecutar("### T-001 · [A] Login (#12)\n", listado, existentes={12})
    assert fallos == [], fallos


@caso("issue realmente borrado (404): MUERDE")
def _():
    listado = [{"number": n, "state": "OPEN"} for n in range(400, 100, -1)]
    fallos, _s = ejecutar("### T-001 · [A] Login (#12)\n", listado, existentes=set())
    assert len(fallos) == 1, fallos
    assert "#12, que no existe" in fallos[0]


@caso("ejemplo de formato dentro de un bloque de codigo: se ignora")
def _():
    backlog = ("# Backlog\n\n```markdown\n### T-000 · [X] Ejemplo (#999)\n"
               "- Estado: Done\n```\n\n" + TAREA_1)
    fallos, _s = ejecutar(backlog, CERRADO)
    assert fallos == [], fallos


@caso("legado (Estado: Done con issue abierto): MUERDE")
def _():
    fallos, _s = ejecutar("### T-001 · [A] Login (#1)\n- Estado: Done\n", ABIERTO)
    assert len(fallos) == 1, fallos
    assert "sigue OPEN" in fallos[0]


@caso("RUTA_BACKLOG sin rellenar: aviso claro, sin traceback")
def _():
    fallos, salida = ejecutar(TAREA_1, ABIERTO, ruta="{{RUTA_BACKLOG}}")
    assert fallos == [], fallos
    assert "sin rellenar" in salida


@caso("RUTA_BACKLOG apunta a un archivo inexistente: MUERDE con mensaje util")
def _():
    fallos, _s = ejecutar(TAREA_1, ABIERTO, crear_backlog=False)
    assert len(fallos) == 1, fallos
    assert "no existe" in fallos[0]


@caso("MODO_BACKLOG invalido: MUERDE")
def _():
    fallos, _s = ejecutar(TAREA_1, ABIERTO, modo="espejito")
    assert len(fallos) == 1 and "no es valido" in fallos[0], fallos


def main() -> int:
    fallidos = 0
    for nombre, prueba in CASOS:
        try:
            prueba()
            print(f"  ok    {nombre}")
        except AssertionError as e:
            fallidos += 1
            print(f"  FALLO {nombre}\n        {e}")
        except Exception as e:  # noqa: BLE001 - el test no debe ocultar errores
            fallidos += 1
            print(f"  ERROR {nombre}\n        {type(e).__name__}: {e}")
    print(f"\n{len(CASOS) - fallidos}/{len(CASOS)} casos OK")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
