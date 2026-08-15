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


# --------------------------------------------------------------------------
# Contador del ROADMAP. Aqui no hay `gh` que simular: se compara
# el documento consigo mismo, asi que los casos son ficheros de verdad.
# --------------------------------------------------------------------------

def ejecutar_roadmap(roadmap, ruta="ROADMAP.md", crear=True):
    """Devuelve la lista de fallos de roadmap_incoherente()."""
    dc = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        if crear:
            (raiz / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
        dc.RAIZ = raiz
        dc.RUTA_ROADMAP = ruta
        return dc.roadmap_incoherente()


def roadmap(completadas=3, totales=4, avance=75, prosa=None, cuerpo=None):
    """ROADMAP sintetico: F1 con dos subfases (una hecha), F2 con una, F3 sin subfases."""
    cabecera = (
        "# ROADMAP\n\n"
        "| Metrica | Valor |\n|---|---|\n"
        f"| Subfases totales | {totales} |\n"
        f"| Completadas | {completadas} / {totales} |\n"
        f"| % avance | {avance}% |\n\n"
    )
    if prosa is not None:
        cabecera += f"Las {prosa}, en orden de cierre: las de F1 y F3.\n\n"
    return cabecera + (cuerpo if cuerpo is not None else (
        "### F1: Base\n**Estado:** ✅ Completada\n- ✅ F1.1 — algo\n- ✅ F1.2 — otra cosa\n\n"
        "### F2: POS\n**Estado:** ⏳ Pendiente\n- ⏳ F2.1 — pendiente\n\n"
        "### F3: Catalogo\n**Estado:** ✅ Completada — sin subfases\n"
    ))


@caso("ROADMAP coherente: no muerde")
def _():
    assert ejecutar_roadmap(roadmap()) == []


@caso("declara MENOS completadas de las que marca: MUERDE (el fallo real que la motivo)")
def _():
    fallos = ejecutar_roadmap(roadmap(completadas=2, avance=50))
    assert any("completadas" in f and "3" in f for f in fallos), fallos


@caso("el total de subfases no cuadra con lo que lista: MUERDE")
def _():
    fallos = ejecutar_roadmap(roadmap(totales=9, avance=33))
    assert any("total" in f for f in fallos), fallos
    assert any("'Subfases totales' dice 9" in f for f in fallos), fallos


@caso("una fase SIN subfases cuenta como una, y su estado es el de su linea")
def _():
    # Misma estructura, pero F3 pendiente: 2 de 4, no 3.
    cuerpo = (
        "### F1: Base\n**Estado:** ✅ Completada\n- ✅ F1.1 — algo\n- ✅ F1.2 — otra\n\n"
        "### F2: POS\n**Estado:** ⏳ Pendiente\n- ⏳ F2.1 — pendiente\n\n"
        "### F3: Catalogo\n**Estado:** ⏳ Pendiente — sin subfases\n"
    )
    assert ejecutar_roadmap(roadmap(completadas=2, avance=50, cuerpo=cuerpo)) == []


@caso("% avance mal: MUERDE")
def _():
    fallos = ejecutar_roadmap(roadmap(avance=99))
    assert any("% avance" in f for f in fallos), fallos


@caso("% avance a 1 punto: NO muerde (redondeo, no defecto)")
def _():
    assert ejecutar_roadmap(roadmap(avance=76)) == []


@caso("la frase en prosa contradice a las marcas: MUERDE")
def _():
    fallos = ejecutar_roadmap(roadmap(prosa=7))
    assert any("en orden de cierre" in f for f in fallos), fallos


@caso("la frase en prosa coherente: no muerde")
def _():
    assert ejecutar_roadmap(roadmap(prosa=3)) == []


@caso("marcas dentro de un bloque de codigo: no cuentan")
def _():
    cuerpo = (
        "### F1: Base\n**Estado:** ✅ Completada\n- ✅ F1.1 — algo\n- ✅ F1.2 — otra\n\n"
        "```\n- ✅ F9.9 — ejemplo de formato, no es una subfase\n```\n\n"
        "### F2: POS\n**Estado:** ⏳ Pendiente\n- ⏳ F2.1 — pendiente\n\n"
        "### F3: Catalogo\n**Estado:** ✅ Completada — sin subfases\n"
    )
    assert ejecutar_roadmap(roadmap(cuerpo=cuerpo)) == []


@caso("vinetas bajo un '## ' posterior a la ultima fase: no cuentan (lo cazo una review)")
def _():
    # La seccion de una fase termina tambien en `## `, no solo en `### `. Si no,
    # todo lo que va detras de la ultima fase sigue dentro de su bloque y estas
    # dos vinetas subirian el total a 6 en silencio — y entonces la guarda
    # exigiria que la tabla escrita a mano cuadre con el numero inflado.
    cuerpo = (
        "### F1: Base\n**Estado:** ✅ Completada\n- ✅ F1.1 — algo\n- ✅ F1.2 — otra\n\n"
        "### F2: POS\n**Estado:** ⏳ Pendiente\n- ⏳ F2.1 — pendiente\n\n"
        "### F3: Catalogo\n**Estado:** ✅ Completada — sin subfases\n\n"
        "## Bitacora de cierres\n- ✅ F1.1 — cerrada el 2026-07-27, commit abc1234\n\n"
        "## Hitos clave\n- ✅ F2.1 — hito M1 desplegado\n"
    )
    assert ejecutar_roadmap(roadmap(cuerpo=cuerpo)) == []


@caso("ROADMAP ausente: lo dice, no se calla")
def _():
    fallos = ejecutar_roadmap("", crear=False)
    assert len(fallos) == 1 and "no existe" in fallos[0], fallos


@caso("documento sin fases: no da veredicto en falso")
def _():
    fallos = ejecutar_roadmap("# ROADMAP\n\nsin nada que contar\n")
    assert len(fallos) == 1 and "no puede emitir veredicto" in fallos[0], fallos


@caso("RUTA_ROADMAP vacia: la comprobacion se apaga entera")
def _():
    assert ejecutar_roadmap(roadmap(completadas=99), ruta="") == []


# --------------------------------------------------------------------------
# El cableado de main().
#
# Todos los casos de arriba llaman a las funciones POR SEPARADO, asi que
# ninguno se entera si una deja de estar enchufada en `main()`. Comprobado por
# mutacion al portar este fichero: quitando `roadmap_incoherente()` de la linea
# de `main` la suite seguia 25/25 en verde. Una guarda desconectada es
# indistinguible de una que pasa, y es justo el modo de fallo que este fichero
# existe para impedir.
#
# Este caso monta un repo donde las TRES tienen algo que denunciar y exige que
# las tres salgan, asi que desenchufar cualquiera pone rojo.
# --------------------------------------------------------------------------

@caso("main() llama a las tres guardas: desenchufar cualquiera pone rojo")
def _():
    dc = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "docs").mkdir(parents=True)
        # 1. Enlace roto.
        (raiz / "README.md").write_text("[a ninguna parte](docs/no-existe.md)\n", encoding="utf-8")
        # 2. Backlog que declara un issue inexistente.
        (raiz / "docs" / "backlog.md").write_text("### T-001 - [A] Login (#404)\n", encoding="utf-8")
        # 3. ROADMAP cuyo contador contradice a sus propias marcas.
        (raiz / "ROADMAP.md").write_text(roadmap(completadas=99), encoding="utf-8")

        # `enlaces_rotos()` solo audita lo TRACKEADO (`git ls-files`), asi que
        # sin repo se salta la revision y este caso dejaria de cubrirla.
        subprocess.run(["git", "init", "-q"], cwd=raiz, check=True)
        subprocess.run(["git", "add", "-A"], cwd=raiz, check=True)

        dc.RAIZ = raiz
        dc.ARBOLES = ["README.md", "ROADMAP.md", "docs"]
        dc.RUTA_BACKLOG = "docs/backlog.md"
        dc.RUTA_ROADMAP = "ROADMAP.md"
        dc.MODO_BACKLOG = "espejado"
        dc.os.environ["GH_TOKEN"] = "test"
        dc.subprocess.run = GhSimulado([], existentes=set())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            codigo = dc.main()
        salida = buf.getvalue()

    assert codigo == 1, f"main() devolvio {codigo} teniendo tres fallos servidos"
    assert "no-existe.md" in salida, f"falta el enlace roto:\n{salida}"
    assert "#404" in salida, f"falta el fallo de backlog:\n{salida}"
    assert "ROADMAP.md" in salida, f"falta el fallo del ROADMAP:\n{salida}"


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
