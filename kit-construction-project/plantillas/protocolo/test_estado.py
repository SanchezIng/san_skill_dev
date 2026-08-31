#!/usr/bin/env python3
"""Tests del estado del reclamo (`scripts/estado.py`).

Que se prueba y por que: este script existe para que TRES comprobaciones dejen de
depender de que el agente se acuerde. Si esas tres no tienen un caso que muerda,
el script no vale mas que la prosa que sustituye — vale menos, porque ademas
parece automatico.

Las tres:
  1. Una lista cortada por el `--limit` se DENUNCIA. Decidir sobre una lista
     truncada es dar por libre lo que otro ya tiene.
  2. El titulo sale de `.content.title`, no del `.title` del item, que es una
     copia congelada al añadir la tarjeta. Hay items donde el numero del titulo
     apunta a OTRA tarea real.
  3. Un issue abierto que no esta en el Project se ve. `gh issue create` no lo
     añade y entonces es invisible para todo el mundo.

Se simula unicamente la frontera con `gh`. Uso: python3 scripts/test_estado.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import types
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "estado.py"

CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


def cargar(items, issues, yo="ana", tope=None):
    """El modulo con la frontera `gh` sustituida por las respuestas dadas."""
    spec = importlib.util.spec_from_file_location("estado", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if tope is not None:
        mod.TOPE = tope

    def falso_run(cmd, **kw):
        if "project" in cmd:
            salida = json.dumps({"items": items})
        elif "api" in cmd:
            salida = yo + "\n"
        else:
            salida = json.dumps(issues)
        return subprocess.CompletedProcess(cmd, 0, salida, "")

    _fingir_gh(mod, falso_run)
    return mod


def _fingir_gh(mod, falso_run):
    """Sustituye `subprocess` SOLO dentro del modulo bajo prueba.

    Antes esto hacia `mod.subprocess.run = falso_run`, y `mod.subprocess` *es* el
    modulo global: parcheaba el proceso entero y no lo restauraba nunca.
    Aislamiento aparente. Rebindear el NOMBRE en el modulo deja el `subprocess`
    de verdad intacto para todos los demas.
    """
    mod.subprocess = types.SimpleNamespace(
        run=falso_run, CompletedProcess=subprocess.CompletedProcess
    )


def item(numero, estado="Disponible", devs=(), titulo=None, titulo_item=None):
    """Tarjeta del Project. `titulo_item` es la copia congelada; `titulo`, el vivo."""
    return {
        "id": f"PVTI_{numero}",
        "status": estado,
        "assignees": list(devs),
        "title": titulo_item if titulo_item is not None else (titulo or ""),
        "content": {"number": numero, "title": titulo or ""},
    }


def issue(numero, titulo="", devs=()):
    return {
        "number": numero,
        "title": titulo,
        "assignees": [{"login": d} for d in devs],
    }


@caso("las candidatas son las Disponible SIN dueño, en orden por numero")
def _():
    mod = cargar(
        items=[
            item(30, titulo="T-030 tarde"),
            item(12, titulo="T-012 pronto"),
            item(20, titulo="T-020 con dueño", devs=["luis"]),
            item(15, estado="Bloqueada", titulo="T-015 bloqueada"),
        ],
        issues=[issue(30), issue(12), issue(20, devs=["luis"]), issue(15)],
    )
    estado = mod.reunir()
    assert [t["numero"] for t in estado["libres"]] == [12, 30], estado["libres"]


@caso("el titulo sale del ISSUE, no de la copia congelada de la tarjeta")
def _():
    # El caso real que lo motivo: el item decia T-062 y el issue decia T-072, y
    # T-062 era otra tarea distinta y viva. Quien elija por el titulo del item
    # reclama otra cosa.
    mod = cargar(
        items=[item(183, titulo="T-072 · lo que la tarea es HOY",
                    titulo_item="T-062 · el nombre con el que nacio")],
        issues=[issue(183)],
    )
    estado = mod.reunir()
    assert estado["libres"][0]["titulo"].startswith("T-072"), estado["libres"][0]


@caso("una lista del Project que llega al tope se DENUNCIA")
def _():
    # `issues` se queda LEJOS del tope a proposito, y el assert nombra "items".
    # Antes las dos listas llegaban al tope a la vez y bastaba con que apareciera
    # la palabra "tope": borrando el check de items el caso seguia verde, porque
    # lo tapaba el aviso de issues. Cada garantia se prueba sola.
    mod = cargar(
        items=[item(n) for n in range(1, 6)],
        issues=[issue(1), issue(2)],
        tope=5,
    )
    estado = mod.reunir()
    assert any("items" in a and "tope" in a for a in estado["avisos"]), estado["avisos"]


@caso("y una lista de issues que llega al tope, tambien")
def _():
    mod = cargar(
        items=[item(1)],
        issues=[issue(n) for n in range(1, 4)],
        tope=3,
    )
    estado = mod.reunir()
    assert any("issues" in a for a in estado["avisos"]), estado["avisos"]


@caso("con holgura NO hay aviso: la señal puede salir limpia")
def _():
    # Una señal que nunca puede estar en verde se aprende a ignorar. La tarjeta
    # lleva titulo de tarea a proposito: un tablero sano no es solo "sin errores
    # de estado", es uno que ADEMAS ofrece algo que reclamar.
    mod = cargar(
        items=[item(1, titulo="T-001 · Andamiaje del proyecto")],
        issues=[issue(1)],
        tope=500,
    )
    estado = mod.reunir()
    assert estado["avisos"] == [], estado["avisos"]


@caso("un issue abierto FUERA del Project se ve")
def _():
    mod = cargar(items=[item(1)], issues=[issue(1), issue(99, "recien creado")])
    estado = mod.reunir()
    assert estado["fuera_del_project"] == [99], estado["fuera_del_project"]


@caso("lo que ya tienes asignado sale, para no reclamar encima")
def _():
    mod = cargar(
        items=[item(7, estado="En progreso", devs=["ana"])],
        issues=[issue(7, "T-007 mia", devs=["ana"]), issue(8, "de otro", devs=["luis"])],
        yo="ana",
    )
    estado = mod.reunir()
    assert [t["numero"] for t in estado["mias"]] == [7], estado["mias"]


@caso("Disponible CON assignee es contradiccion y se denuncia")
def _():
    # El candado son dos cosas (estado + assignee) y pueden desincronizarse: si
    # se ignora, dos devs acaban sobre la misma tarea.
    mod = cargar(items=[item(5, devs=["luis"])], issues=[issue(5, devs=["luis"])])
    estado = mod.reunir()
    assert any("assignee" in a for a in estado["avisos"]), estado["avisos"]
    assert estado["libres"] == [], estado["libres"]


@caso("un Project vacio no revienta: dice que no hay candidatas")
def _():
    mod = cargar(items=[], issues=[])
    estado = mod.reunir()
    assert estado["libres"] == [] and estado["avisos"] == []


@caso("si `gh` falla, PARA con el error a la vista")
def _():
    spec = importlib.util.spec_from_file_location("estado", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _fingir_gh(
        mod,
        lambda cmd, **kw: subprocess.CompletedProcess(
            cmd, 1, "", "gh: could not resolve to a Project"
        ),
    )
    try:
        mod.reunir()
    except SystemExit as e:
        assert "could not resolve" in str(e), e
    else:
        raise AssertionError("deberia haber parado")


@caso("el informe imprime lo que hay que decidir, sin volcar JSON")
def _():
    mod = cargar(
        items=[item(12, titulo="T-012 pronto")],
        issues=[issue(12), issue(99)],
    )
    import builtins

    salida = []
    original = builtins.print
    builtins.print = lambda *a, **k: salida.append(" ".join(str(x) for x in a))
    try:
        mod.imprimir(mod.reunir())
    finally:
        builtins.print = original
    texto = "\n".join(salida)
    assert "#12 T-012 pronto" in texto, texto
    assert "#99" in texto, texto
    # Que el informe sea PROSA y no un volcado del dict. Se comprueba por las
    # CLAVES y no por las llaves `{}`: el aserto original era `"{" not in texto`
    # y eso no mide el formato, mide la CONFIGURACION — con `PROJECT_NUMBER`
    # todavia en `{{PROJECT_NUMBER}}` (o sea, en el kit recien instalado y antes
    # de rellenarlo) la cabecera lleva llaves y el caso daba rojo sin que nada
    # estuviera mal. Un test que depende de si alguien ya configuro el proyecto
    # no prueba lo que dice su nombre.
    for clave in ("numero", "libres", "avisos", "fuera_del_project"):
        assert f'"{clave}"' not in texto and f"'{clave}'" not in texto, texto


@caso("un item DENTRO del Project pero SIN estado se denuncia")
def _():
    # El hueco entre las dos listas: no es "Disponible" (no sale en libres) y si
    # esta en el Project (no sale en fuera_del_project). Invisible para todos.
    # `item-add` son tres pasos y los dos ultimos no protestan si se olvidan.
    mod = cargar(
        items=[item(1), item(77, estado="")],
        issues=[issue(1), issue(77, "T-077 añadida a medias")],
    )
    estado = mod.reunir()
    assert estado["sin_estado"] == [77], estado["sin_estado"]
    assert any("SIN estado" in a for a in estado["avisos"]), estado["avisos"]
    assert estado["fuera_del_project"] == [], estado["fuera_del_project"]


@caso("un borrador Disponible no se ofrece como candidata (#None no se reclama)")
def _():
    borrador = {"id": "PVTI_d", "status": "Disponible", "assignees": [],
                "title": "idea suelta", "content": {}}
    mod = cargar(items=[item(12, titulo="T-012"), borrador], issues=[issue(12)])
    estado = mod.reunir()
    assert [t["numero"] for t in estado["libres"]] == [12], estado["libres"]
    assert any("borrador" in a for a in estado["avisos"]), estado["avisos"]


@caso("el informe SOBREVIVE a un stdout cp1252 (Windows/Git Bash)")
def _():
    # Este caso corre el script COMO SUBPROCESO a proposito: los demas parchean
    # `print`, y con `print` parcheado la codificacion de stdout no se toca jamas
    # — el unico camino donde vive el bug es justo el que el resto de la suite
    # evita. Basta un item con un emoji en el titulo para tumbar el reclamo.
    driver = (
        "import importlib.util, json, subprocess, sys, types\n"
        "spec = importlib.util.spec_from_file_location('estado', %r)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "items = [{'id': 'i', 'status': 'Disponible', 'assignees': [],\n"
        "          'title': '', 'content': {'number': 115,\n"
        "                                   'title': 'T-0xx \\u26a0\\ufe0f ojo'}}]\n"
        "issues = [{'number': 115, 'title': 'x', 'assignees': []}]\n"
        "def run(cmd, **kw):\n"
        "    if 'project' in cmd: s = json.dumps({'items': items})\n"
        "    elif 'api' in cmd: s = 'ana\\n'\n"
        "    else: s = json.dumps(issues)\n"
        "    return subprocess.CompletedProcess(cmd, 0, s, '')\n"
        "mod.subprocess = types.SimpleNamespace(\n"
        "    run=run, CompletedProcess=subprocess.CompletedProcess)\n"
        "sys.exit(mod.main([]))\n"
    ) % str(MODULO)

    entorno = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    entorno.pop("PYTHONUTF8", None)  # el modo UTF-8 taparia justo lo que se prueba
    r = subprocess.run(
        [sys.executable, "-c", driver],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=entorno,
    )
    assert r.returncode == 0, (
        "el reclamo se cae con stdout cp1252:\n%s" % (r.stderr or "").strip()
    )
    assert "#115" in r.stdout, r.stdout


@caso("--json sale entero y parseable, tambien con un borrador delante")
def _():
    borrador = {"id": "PVTI_d", "status": "Disponible", "assignees": [],
                "title": "idea", "content": {}}
    mod = cargar(items=[borrador, item(12, titulo="T-012")], issues=[issue(12)])
    import builtins

    salida = []
    original = builtins.print
    builtins.print = lambda *a, **k: salida.append(" ".join(str(x) for x in a))
    try:
        mod.main(["--json"])
    finally:
        builtins.print = original
    datos = json.loads("\n".join(salida))
    assert [t["numero"] for t in datos["libres"]] == [12], datos["libres"]
    assert "None" not in json.dumps(datos["libres"]), datos["libres"]


@caso("si TODO lo Disponible son avisos, se denuncia que no hay tarea reclamable")
def _():
    # El caso de FARMICROW: 7 decisiones y vigilancias en Disponible, cero
    # `T-nnn`. `libres` sale con siete candidatas y el dev se lleva la de menor
    # numero -- que era "vigilar postcss", sin nada que hacer aguas arriba.
    mod = cargar(
        items=[
            item(39, titulo="Vigilar postcss: dos avisos HIGH sin fix aguas arriba"),
            item(41, titulo="Decidir si la CSP con nonce merece ADR propio"),
        ],
        issues=[issue(39), issue(41)],
    )
    estado = mod.reunir()
    assert len(estado["libres"]) == 2, estado["libres"]
    assert any("NINGUNA es una tarea" in a for a in estado["avisos"]), estado["avisos"]


@caso("con una sola tarea `T-nnn` entre los avisos, NO se denuncia")
def _():
    # El aviso mide "no hay trabajo", no "hay avisos". Mezclar las dos cosas lo
    # volveria ruido permanente: un tablero sano tiene avisos Y tareas.
    mod = cargar(
        items=[
            item(39, titulo="Vigilar postcss: dos avisos HIGH sin fix aguas arriba"),
            item(4, titulo="T-004 · Sistema de diseño y armazón responsive (F1.4)"),
        ],
        issues=[issue(39), issue(4)],
    )
    estado = mod.reunir()
    assert not any("NINGUNA es una tarea" in a for a in estado["avisos"]), estado["avisos"]


@caso("el aviso lee el titulo VIVO, no la copia congelada de la tarjeta")
def _():
    # Mismo motivo que el caso del titulo vivo: la copia del item se congela al
    # anadir la tarjeta. Si el aviso mirase `title` en vez de `.content.title`,
    # una tarea renombrada a `T-nnn` seguiria contando como aviso.
    mod = cargar(
        items=[
            item(
                7,
                titulo="T-007 · Recuperacion de contraseña",
                titulo_item="Pendiente: decidir el proveedor de correo",
            )
        ],
        issues=[issue(7)],
    )
    estado = mod.reunir()
    assert not any("NINGUNA es una tarea" in a for a in estado["avisos"]), estado["avisos"]


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
