#!/usr/bin/env python3
"""Tests de la guarda del cuerpo del PR (`scripts/pr_body_check.py`).

Que se prueba y por que: esta guarda tiene dos formas de ser inutil, y las dos
ocurrieron de verdad antes de existir estos casos.

  1. **Que no vea el cierre en español** y deje pasar el PR que va a dejar su
     issue abierto — el fallo que la tarea existe para matar.
  2. **Que se dispare contra una CITA.** El PR que la introdujo explicaba el
     problema escribiendo `Cierra #52` en prosa, y la guarda exigio cerrar un
     issue que solo vivia en una tabla de casos de prueba. Una guarda ruidosa
     acaba desactivada, que es peor que no tenerla (casos `cita_*`).

Se prueba la funcion `revisar()` y ademas el script entero por subproceso, que es
como corre en el CI: el codigo de salida es lo que hace fallar el workflow, y en
el proyecto de origen se llego a leer el exit de `head` en vez del de Python.

Uso: python3 scripts/test_pr_body_check.py
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "pr_body_check.py"

CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


def cargar():
    spec = importlib.util.spec_from_file_location("pr_body_check", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PBC = cargar()


def correr_script(cuerpo: str) -> tuple[int, str]:
    """Ejecuta el script como en el CI, con el cuerpo por entorno."""
    entorno = dict(os.environ, PR_BODY=cuerpo)
    proc = subprocess.run(
        [sys.executable, str(MODULO)],
        capture_output=True, text=True, env=entorno,
    )
    return proc.returncode, proc.stdout


# --- lo que debe DENUNCIAR ---------------------------------------------------

@caso("'Cierra #52' a secas: lo denuncia (es el fallo original, PR #53 -> #52)")
def _():
    assert PBC.revisar("Este PR arregla el login.\n\nCierra #52") == ["52"]


@caso("con dos puntos y en mayusculas: tambien")
def _():
    assert PBC.revisar("RESUELVE: #7") == ["7"]


@caso("varios verbos y varios issues, sin duplicados y en orden")
def _():
    cuerpo = "Cierra #10\nCorrige #11\nCierra #10 otra vez\nSoluciona #12"
    assert PBC.revisar(cuerpo) == ["10", "11", "12"]


@caso("el ingles de OTRO numero no salva al declarado en español")
def _():
    assert PBC.revisar("Cierra #52\n\nCloses #99") == ["52"]


# --- lo que debe DEJAR PASAR -------------------------------------------------

@caso("español + ingles del MISMO numero: correcto, no molesta")
def _():
    assert PBC.revisar("Cierra #52 (Closes #52)") == []


@caso("solo ingles: correcto")
def _():
    assert PBC.revisar("Closes #52") == []


@caso("cuerpo sin ningun cierre: nada que decir")
def _():
    assert PBC.revisar("Refactor sin issue asociado.") == []


@caso("cita_1: `Cierra #52` en code span es cita, no declaracion")
def _():
    assert PBC.revisar("El bug: escribir `Cierra #52` no cierra nada.") == []


@caso("cita_2: dentro de un bloque cercado tampoco declara")
def _():
    cuerpo = "Ejemplo de lo que NO funciona:\n\n```\nCierra #52\n```\n"
    assert PBC.revisar(cuerpo) == []


@caso("cita_3: en un comentario HTML de la plantilla tampoco")
def _():
    assert PBC.revisar("<!-- ejemplo: Cierra #52 -->\n\nCloses #7") == []


@caso("una palabra que CONTIENE el verbo no cuenta (frontera \\b)")
def _():
    # "encierra" contiene "cierra". Sin la frontera de palabra en el patron,
    # esta frase se denunciaria como un cierre declarado — y el primer intento
    # de este caso usaba "reconstruye", que no contiene ningun verbo de la
    # lista: pasaba igual con el patron roto, o sea que no probaba nada.
    assert PBC.revisar("El PR encierra #52 casos de prueba") == []


# --- el contrato con el CI: el codigo de salida ------------------------------

@caso("el script sale 1 cuando denuncia (es lo que rompe el CI)")
def _():
    codigo, salida = correr_script("Cierra #52")
    assert codigo == 1, f"exit={codigo} · {salida}"
    assert "Closes #52" in salida, salida


@caso("el script sale 0 cuando esta bien, y lo dice")
def _():
    codigo, salida = correr_script("Closes #52")
    assert codigo == 0, f"exit={codigo} · {salida}"
    assert "OK" in salida, salida


@caso("cuerpo vacio: sale 0 sin inventarse problemas")
def _():
    codigo, salida = correr_script("   \n  ")
    assert codigo == 0, f"exit={codigo} · {salida}"
    assert "vacio" in salida, salida


@caso("tambien acepta el cuerpo por fichero (para probarlo a mano)")
def _():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "cuerpo.md"
        f.write_text("Cierra #33", encoding="utf-8")
        proc = subprocess.run([sys.executable, str(MODULO), str(f)],
                              capture_output=True, text=True)
        assert proc.returncode == 1, proc.stdout
        assert "#33" in proc.stdout, proc.stdout


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
