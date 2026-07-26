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
import sys
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
