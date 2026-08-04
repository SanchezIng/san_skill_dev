#!/usr/bin/env python3
"""Tests del trato con el GitHub Project (resolver IDs y mover tarjetas).

Se simula unicamente la frontera con `gh api graphql`. Lo que se prueba es justo
lo que antes no tenia quien lo probara: que ante cualquier configuracion rota el
protocolo PARE con un diagnostico util, en vez de dejar el candado a medias
(issue asignado, tarjeta sin mover).

Uso: python3 scripts/test_tablero.py     (exit 1 si algun caso falla)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "tablero.py"


def cargar(owner="MiEquipo", numero="1"):
    spec = importlib.util.spec_from_file_location("tablero", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.OWNER = owner
    mod.PROJECT_NUMBER = numero
    return mod


def proyecto(columnas, titulo="Tablero", campo=True):
    campo_valor = None
    if campo:
        campo_valor = {
            "id": "PVTSSF_status",
            "options": [{"id": f"opt_{i}", "name": n} for i, n in enumerate(columnas)],
        }
    return {"projectV2": {"id": "PVT_123", "title": titulo, "field": campo_valor}}


TODAS = ["Disponible", "Bloqueada", "En progreso", "Review", "Terminado"]

CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


@caso("Project de un USUARIO: resuelve todo")
def _():
    mod = cargar()
    mod._graphql = lambda ambito: proyecto(TODAS) if ambito == "user" else None
    d = mod.resolver()
    assert d["projectId"] == "PVT_123", d
    assert d["statusFieldId"] == "PVTSSF_status", d
    assert len(d["opciones"]) == 5, d
    assert d["opciones"]["En progreso"] == "opt_2", d


@caso("Project de una ORGANIZACION: cae al segundo ambito")
def _():
    mod = cargar()
    mod._graphql = lambda ambito: proyecto(TODAS) if ambito == "organization" else None
    d = mod.resolver()
    assert d["projectId"] == "PVT_123", d


@caso("placeholders sin rellenar: para y explica cuales")
def _():
    mod = cargar(owner="{{OWNER}}", numero="{{PROJECT_NUMBER}}")
    llamadas = []
    mod._graphql = lambda ambito: llamadas.append(ambito)
    try:
        mod.resolver()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "OWNER y PROJECT_NUMBER" in str(e), e
    assert llamadas == [], "no debe consultar la API sin configuracion"


@caso("el Project no existe: lo dice y sugiere como listarlos")
def _():
    mod = cargar()
    mod._graphql = lambda ambito: None
    try:
        mod.resolver()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "No se encuentra el Project" in str(e), e
        assert "gh project list" in str(e), e


@caso("el owner existe pero sin ese Project: mensaje distinto")
def _():
    mod = cargar()
    mod._graphql = lambda ambito: {"projectV2": None} if ambito == "user" else None
    try:
        mod.resolver()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "no tiene un Project numero" in str(e), e


@caso("campo Status renombrado: lo dice")
def _():
    mod = cargar()
    mod._graphql = lambda ambito: proyecto(TODAS, campo=False) if ambito == "user" else None
    try:
        mod.resolver()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "no tiene un campo de seleccion" in str(e), e
        assert "CAMPO_ESTADO" in str(e), e


@caso("una columna renombrada: dice cual falta Y cuales hay")
def _():
    mod = cargar()
    reales = ["Disponible", "Bloqueada", "Doing", "Review", "Terminado"]
    mod._graphql = lambda ambito: proyecto(reales) if ambito == "user" else None
    try:
        mod.resolver()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "En progreso" in str(e), e      # la que falta
        assert "Doing" in str(e), e            # y las que hay, para poder corregir


@caso("main() sale 1 y avisa de NO reclamar cuando algo falla")
def _(capsys=None):
    import io
    import contextlib
    mod = cargar(owner="{{OWNER}}")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        codigo = mod.main([])
    salida = buf.getvalue()
    assert codigo == 1, codigo
    assert "NO des por hecho el reclamo" in salida, salida


@caso("main() --comprobar sale 0 y resume el tablero")
def _():
    import io
    import contextlib
    mod = cargar()
    mod._graphql = lambda ambito: proyecto(TODAS, titulo="Facturacion") if ambito == "user" else None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        codigo = mod.main(["--comprobar"])
    assert codigo == 0, codigo
    assert "Facturacion" in buf.getvalue(), buf.getvalue()


def preparar_mover(mod, respuesta_mutacion, estado_leido):
    """Deja el modulo listo para --mover con una API simulada."""
    mod._graphql = lambda ambito: proyecto(TODAS) if ambito == "user" else None
    mod._gh_graphql = lambda consulta, variables: respuesta_mutacion
    mod.estado_actual = lambda item_id: estado_leido


@caso("mover: la tarjeta queda donde se pidio")
def _():
    mod = cargar()
    preparar_mover(mod, {"data": {"updateProjectV2ItemFieldValue": {}}}, "En progreso")
    mod.mover("PVTI_item1", "En progreso")     # no lanza


@caso("mover a una columna inexistente: para antes de tocar la API")
def _():
    mod = cargar()
    tocada = []
    mod._graphql = lambda ambito: proyecto(TODAS) if ambito == "user" else None
    mod._gh_graphql = lambda c, v: tocada.append(1)
    try:
        mod.mover("PVTI_item1", "Doing")
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "no es una columna" in str(e), e
    assert tocada == [], "no debe llamar a la API con una columna invalida"


@caso("mover: la API rechaza -> lo dice y orienta sobre el ITEM_ID")
def _():
    mod = cargar()
    preparar_mover(mod, None, None)
    try:
        mod.mover("42", "En progreso")
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "rechazo mover" in str(e), e
        assert "no el numero del issue" in str(e), e


@caso("mover: la API dice OK pero la tarjeta NO se movio -> MUERDE")
def _():
    # El falso exito exacto que el kit persigue: 200 no es "quedo donde queria".
    mod = cargar()
    preparar_mover(mod, {"data": {"updateProjectV2ItemFieldValue": {}}}, "Disponible")
    try:
        mod.mover("PVTI_item1", "En progreso")
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "quedo en 'Disponible'" in str(e), e
        assert "NO des la tarea por reclamada" in str(e), e


@caso("mover: errors en la respuesta GraphQL tambien muerde")
def _():
    mod = cargar()
    preparar_mover(mod, {"errors": [{"message": "Could not resolve to a node"}]},
                   "En progreso")
    try:
        mod.mover("PVTI_item1", "En progreso")
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "rechazo mover" in str(e), e


@caso("la mutacion NO incrusta literales en la query (trampa de PowerShell)")
def _():
    mod = cargar()
    # Los valores viajan como variables -f clave=valor, no dentro del texto.
    assert "$projectId" in mod.MUTACION and "$optionId" in mod.MUTACION, mod.MUTACION
    assert "PVT_" not in mod.MUTACION, "la query no debe llevar IDs literales"
    capturado = {}
    mod._graphql = lambda ambito: proyecto(TODAS) if ambito == "user" else None

    def espia(consulta, variables):
        capturado["consulta"] = consulta
        capturado["variables"] = variables
        return {"data": {}}
    mod._gh_graphql = espia
    mod.estado_actual = lambda i: "En progreso"
    mod.mover("PVTI_item1", "En progreso")
    assert capturado["variables"]["optionId"] == "opt_2", capturado
    assert "opt_2" not in capturado["consulta"], "el id no puede ir en el texto"


# --- Generacion del tablero -------------------------------------------------
#
# Aqui lo que se protege es distinto: no que la API se use bien, sino que el
# archivo del repo diga la verdad Y que lo escrito por una persona sobreviva.
# La tabla se genera; el log de reclamos NO se genera jamas, y estos casos son
# los que impiden que alguien lo automatice por comodidad mas adelante.

def preparar_generar(mod, items, total=None, titulo="Facturacion"):
    mod._graphql = lambda ambito: proyecto(TODAS, titulo=titulo) if ambito == "user" else None
    salida = json.dumps({"items": items,
                         "totalCount": total if total is not None else len(items)})
    mod.subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, salida, "")
    return mod


def tarea(titulo, estado, modulos=(), devs=(), numero=None):
    return {
        "id": f"PVTI_{titulo}",
        "status": estado,
        "assignees": list(devs),
        "labels": [f"modulo:{m}" for m in modulos],
        "content": {"title": titulo, "number": numero, "type": "Issue"},
    }


TRES = [
    tarea("T-001 Login", "Terminado", ["A"], ["ana"], 1),
    tarea("T-002 API", "En progreso", ["B"], ["luis"], 2),
    tarea("T-003 Cola", "Bloqueada", ["C"], [], 3),
]


def generar_en(tmp, mod, contenido_previo=None):
    ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
    if contenido_previo is not None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido_previo, encoding="utf-8")
    mod.generar(str(ruta), hoy="2026-07-26")
    return ruta.read_text(encoding="utf-8")


@caso("generar de cero: tablas, aviso de que no se comitea y log vacio pero dicho")
def _():
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        texto = generar_en(tmp, mod)
    assert "T-002 API (#2)" in texto, texto
    assert "| B |" in texto, texto
    assert "NO se comitea" in texto, texto
    # Sin entradas se DICE que no las hay, en vez de dejar un hueco mudo que
    # se lee igual que "aqui no ha pasado nada".
    assert "todavía sin entradas" in texto, texto


@caso("las tareas Terminado no se listan, pero se DICE cuantas hay")
def _():
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        texto = generar_en(tmp, mod)
    assert "T-001 Login" not in texto.split("## Tareas abiertas")[1], texto
    assert "1 tarea(s) en Terminado no se listan" in texto, texto


@caso("EL LOG ESCRITO A MANO SOBREVIVE a regenerar (ahora, desde progreso/log/)")
def _():
    # La garantia no cambia —lo que escribio una persona no se pierde— pero el
    # sitio si: antes se conservaba por posicion dentro del archivo, ahora
    # sobrevive porque vive fuera de el.
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        log = ruta.parent / "log"
        log.mkdir(parents=True)
        nota = "2026-07-26 Ana: el endpoint choca con la migracion; NO tocar hasta F4\n"
        (log / "2026-07-26-ana-endpoint.md").write_text(nota, encoding="utf-8")
        mod.generar(str(ruta), hoy="2026-07-26")
        mod2 = preparar_generar(cargar(), [tarea("T-009 Nueva", "Disponible", ["A"])])
        mod2.generar(str(ruta), hoy="2026-07-27")
        despues = ruta.read_text(encoding="utf-8")
    assert nota.strip() in despues, "se ha perdido una linea escrita por una persona"
    assert "T-009 Nueva" in despues, "no llego el estado nuevo"
    assert "T-002 API" not in despues, "quedo estado viejo en la tabla"


@caso("lo que alguien escriba en el tablero SE PIERDE al regenerar, a proposito")
def _():
    # Antes se conservaba lo de fuera del bloque. Ya no: el archivo no se
    # comitea y es 100% generado, asi que conservar texto suelto solo serviria
    # para que alguien creyera que ahi se puede escribir. Lo que hay que contar
    # va en progreso/log/, que si sobrevive.
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        primero = generar_en(tmp, mod)
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        ruta.write_text(primero.replace(
            "# Tablero del Equipo",
            "# Tablero\n\n> Ojo: los viernes no se reclama nada."), encoding="utf-8")
        mod.generar(str(ruta), hoy="2026-07-26")
        despues = ruta.read_text(encoding="utf-8")
    assert "los viernes no se reclama nada" not in despues, despues
    assert "# Tablero del Equipo" in despues, despues


@caso("regenerar dos veces sin cambios: mismo texto (no ensucia el diff)")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        preparar_generar(cargar(), TRES).generar(str(ruta), hoy="2026-07-26")
        uno = ruta.read_text(encoding="utf-8")
        preparar_generar(cargar(), list(reversed(TRES))).generar(str(ruta), hoy="2026-07-26")
        dos = ruta.read_text(encoding="utf-8")
    assert uno == dos, "el orden de la API no debe cambiar el archivo"


@caso("TABLERO VIEJO con el log DENTRO: no se regenera, se explica como migrar")
def _():
    # Lo unico irrecuperable del tablero es el log: nadie puede reescribir por
    # que se atasco algo hace tres semanas. Regenerar encima lo borraria.
    mod = preparar_generar(cargar(), TRES)
    viejo = (
        "# Tablero del Equipo\n\n## Log de reclamos\n\n"
        "- 2026-07-01 alguien reclama T-001 — y explica por que\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        ruta.parent.mkdir(parents=True)
        ruta.write_text(viejo, encoding="utf-8")
        try:
            mod.generar(str(ruta))
            raise AssertionError("deberia haber fallado")
        except mod.ErrorDeConfiguracion as e:
            assert "todavia lleva el log DENTRO" in str(e), e
            assert "Migralas primero" in str(e), e
        assert ruta.read_text(encoding="utf-8") == viejo, "ha modificado el archivo"


@caso("con el log YA migrado, regenerar encima del viejo es seguro")
def _():
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        ruta.parent.mkdir(parents=True)
        ruta.write_text("# T\n\n## Log de reclamos\n\n- 2026-07-01 x\n", encoding="utf-8")
        log = ruta.parent / "log"
        log.mkdir()
        (log / "2026-07-01-x.md").write_text("2026-07-01 x\n", encoding="utf-8")
        mod.generar(str(ruta))  # no debe lanzar
        assert "2026-07-01 x" in ruta.read_text(encoding="utf-8")


@caso("el log se ensambla ORDENADO y desde la carpeta del tablero, no del CWD")
def _():
    # Atarlo al directorio actual hacia que generar en otra ruta ensamblara el
    # log del repo real: el archivo parecia bueno y hablaba de otra cosa.
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        log = ruta.parent / "log"
        log.mkdir(parents=True)
        (log / "2026-07-09-tarde.md").write_text("2026-07-09 ENTRADA TARDIA\n", encoding="utf-8")
        (log / "2026-07-02-pronto.md").write_text(
            "2026-07-02 ENTRADA TEMPRANA\n  con continuacion indentada\n", encoding="utf-8")
        mod.generar(str(ruta))
        texto = ruta.read_text(encoding="utf-8")
        assert texto.index("ENTRADA TEMPRANA") < texto.index("ENTRADA TARDIA"), "sin ordenar"
        assert "- 2026-07-02 ENTRADA TEMPRANA" in texto, "no la pinta como vineta"
        assert "  con continuacion indentada" in texto, "pierde continuaciones"


@caso("decisiones y pendientes se ensamblan desde sus carpetas")
def _():
    # Mismo remedio que el log, aplicado a las tres secciones de estado-actual
    # que cambiaban en cada PR. Si esto deja de ensamblarse, el generado no
    # miente: se queda MUDO, que es peor — parece que no hay decisiones.
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        ruta.parent.mkdir(parents=True)
        (ruta.parent / "decisiones").mkdir()
        (ruta.parent / "pendientes").mkdir()
        (ruta.parent / "decisiones" / "a.md").write_text(
            "El dinero va en Decimal, jamas en number\n", encoding="utf-8")
        (ruta.parent / "pendientes" / "b.md").write_text(
            "Playwright no corre en CI todavia\n", encoding="utf-8")
        mod.generar(str(ruta))
        texto = ruta.read_text(encoding="utf-8")
    assert "- El dinero va en Decimal" in texto, texto
    assert "- Playwright no corre en CI" in texto, texto


@caso("sin decisiones, se DICE que no hay (no un hueco mudo)")
def _():
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        texto = generar_en(tmp, mod)
    assert "Decisiones técnicas vivas" in texto, texto
    assert "_(sin entradas)_" in texto, texto


@caso("dos ramas que añaden entradas DISTINTAS no pueden conflictar")
def _():
    # Es la razon de ser del cambio: cada entrada es un fichero propio, asi que
    # dos ramas escriben ficheros distintos y git las une sin preguntar.
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        log = ruta.parent / "log"
        log.mkdir(parents=True)
        (log / "2026-07-02-rama-a.md").write_text("2026-07-02 rama A\n", encoding="utf-8")
        (log / "2026-07-02-rama-b.md").write_text("2026-07-02 rama B\n", encoding="utf-8")
        mod.generar(str(ruta))
        texto = ruta.read_text(encoding="utf-8")
        assert "rama A" in texto and "rama B" in texto, "se ha perdido una entrada"


@caso("LISTADO RECORTADO: no escribe media verdad, muerde")
def _():
    # totalCount dice 40 y solo llegan 3: el tablero omitiria 37 tareas y esas
    # no se leerian como ausentes, sino como inexistentes.
    mod = preparar_generar(cargar(), TRES, total=40)
    with tempfile.TemporaryDirectory() as tmp:
        try:
            generar_en(tmp, mod)
            raise AssertionError("deberia haber fallado")
        except mod.ErrorDeConfiguracion as e:
            assert "RECORTADO" in str(e), e
            assert "LIMITE_ITEMS" in str(e), e
        assert not (Path(tmp) / "progreso" / "tablero-equipo.md").exists(), \
            "no debe dejar un tablero a medias"


@caso("listado justo en el tope: se asume que hay mas")
def _():
    mod = cargar()
    mod.LIMITE_ITEMS = 3
    preparar_generar(mod, TRES, total=3)
    with tempfile.TemporaryDirectory() as tmp:
        try:
            generar_en(tmp, mod)
            raise AssertionError("deberia haber fallado")
        except mod.ErrorDeConfiguracion as e:
            assert "justo el tope" in str(e), e


@caso("una tarea sin label de modulo NO desaparece: cae en (sin módulo)")
def _():
    mod = preparar_generar(cargar(), [tarea("T-050 Huerfana", "Disponible")])
    with tempfile.TemporaryDirectory() as tmp:
        texto = generar_en(tmp, mod)
    assert "T-050 Huerfana" in texto, texto
    assert mod.SIN_MODULO in texto, texto


@caso("un hito con dos modulos sale en las dos filas")
def _():
    mod = preparar_generar(cargar(), [tarea("T-023 HITO", "En progreso", ["A", "B"])])
    with tempfile.TemporaryDirectory() as tmp:
        texto = generar_en(tmp, mod)
    modulos = texto.split("## Módulos")[1].split("## Tareas")[0]
    assert "| A |" in modulos and "| B |" in modulos, modulos


@caso("estado del modulo: derivado con la regla, y la regla se imprime")
def _():
    mod = cargar()
    assert mod._estado_del_modulo(["Terminado", "En progreso"]) == "En progreso"
    assert mod._estado_del_modulo(["Terminado", "Terminado"]) == "Terminado"
    assert mod._estado_del_modulo(["Bloqueada", "Terminado"]) == "Bloqueado"
    assert mod._estado_del_modulo(["Bloqueada", "Disponible"]) == "Disponible"
    assert mod._estado_del_modulo([]) == "Sin tareas"
    preparar_generar(mod, TRES)
    with tempfile.TemporaryDirectory() as tmp:
        texto = generar_en(tmp, mod)
    assert "derivado de sus tareas" in texto, "un estado derivado debe decir cómo"


@caso("columna renombrada a medias (ESTADOS y semantica no cuadran): MUERDE")
def _():
    mod = cargar()
    mod.ESTADOS = ["Disponible", "Bloqueada", "Doing", "Review", "Terminado"]
    try:
        mod.tablas(TRES, "X", "2026-07-26")
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeConfiguracion as e:
        assert "En progreso" in str(e) and "EN_CURSO" in str(e), e


@caso("`gh` falla al listar: no se escribe nada y se orienta sobre el scope")
def _():
    mod = cargar()
    mod._graphql = lambda ambito: proyecto(TODAS) if ambito == "user" else None
    mod.subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(
        cmd, 1, "", "your token has not been granted the required scopes")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            generar_en(tmp, mod)
            raise AssertionError("deberia haber fallado")
        except mod.ErrorDeConfiguracion as e:
            assert "gh auth refresh -s project" in str(e), e
        assert not (Path(tmp) / "progreso" / "tablero-equipo.md").exists()


@caso("toda llamada a `gh` decodifica en utf-8, no en la codepage de Windows ")
def _():
    # El bug real: `text=True` sin `encoding=` decodifica con la codepage del
    # sistema (cp1252 en el equipo, que es Windows entero), y el ⏸️ del titulo
    # de T-016 reventaba la herramienta con UnicodeDecodeError. Los mocks de
    # esta suite se tragan la decodificacion, asi que lo que se asevera es el
    # kwarg — que ES el arreglo — y ademas se pasa un titulo con ⏸️ de punta a
    # punta para que el resto del camino (parseo y escritura) lo digiera.
    kwargs_vistos = []

    def espia(cmd, **kw):
        kwargs_vistos.append(kw)
        salida = json.dumps({"items": [tarea("T-016 ⏸️ Facturacion", "Bloqueada",
                                             ["C"], [], 16)], "totalCount": 1})
        return subprocess.CompletedProcess(cmd, 0, salida, "")

    mod = cargar()
    mod._graphql = lambda ambito: proyecto(TODAS) if ambito == "user" else None
    mod.subprocess.run = espia
    with tempfile.TemporaryDirectory() as tmp:
        contenido = generar_en(tmp, mod)
    assert "⏸" in contenido, "el titulo con el emoji debe llegar al tablero"
    assert kwargs_vistos, "no hubo ninguna llamada a gh"
    for kw in kwargs_vistos:
        assert kw.get("encoding") == "utf-8", f"llamada a gh sin encoding utf-8: {kw}"

    # Y la otra frontera con gh (_gh_graphql, la que usa --mover):
    kwargs_vistos.clear()
    mod2 = cargar()
    mod2.subprocess.run = espia
    mod2._gh_graphql("query {}", {})
    assert kwargs_vistos and kwargs_vistos[0].get("encoding") == "utf-8", kwargs_vistos


@caso("main() --generar cuenta las entradas y recuerda que NO se comitea")
def _():
    import io
    import contextlib
    mod = preparar_generar(cargar(), TRES)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "progreso" / "tablero-equipo.md"
        log = ruta.parent / "log"
        log.mkdir(parents=True)
        (log / "2026-07-02-una.md").write_text("2026-07-02 una\n", encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            codigo = mod.main(["--generar", str(ruta)])
    salida = buf.getvalue()
    assert codigo == 0, codigo
    assert "1 entrada(s)" in salida, salida
    assert "NO se comitea" in salida, salida


@caso("main() --generar que falla: avisa de que el archivo es de ANTES")
def _():
    import io
    import contextlib
    mod = cargar(owner="{{OWNER}}")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        codigo = mod.main(["--generar"])
    salida = buf.getvalue()
    assert codigo == 1, codigo
    assert "NO se ha actualizado" in salida, salida
    assert "reclamo" not in salida, "ese aviso es el de --mover, aqui no aplica"


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
