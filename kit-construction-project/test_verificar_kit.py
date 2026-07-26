#!/usr/bin/env python3
"""Tests del verificador de la salida del kickstart.

Por que existen: este verificador es lo unico que se interpone entre "Claude
genero el kit" y "el equipo empieza a trabajar sobre el". Si acusa en falso, se
desactiva a la primera; si calla ante un documento prometido y no escrito, no
sirve para nada. Aqui se monta un kit sintetico completo y se le rompe UNA cosa
cada vez, para que el fallo observado sea el de la regla bajo prueba.

Lo que NO prueban estos casos, y conviene tener presente: que el kit generado
sea BUENO. Se verifica el artefacto, no el criterio.

Uso: python3 test_verificar_kit.py     (exit 1 si algun caso falla)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "skills" / "project-kickstart" / "verificar_kit.py"


def cargar():
    spec = importlib.util.spec_from_file_location("verificar_kit", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CLAUDE_MD = """# CLAUDE.md — Proyecto

## Stack
Python 3.12 + FastAPI.

## DÓNDE ENCONTRAR CADA COSA
- Requisitos: [especificaciones](docs/especificaciones.md)
- Fases: [guía](docs/guia_desarrollo.md)

## ARCHIVOS QUE NO TOCAR SIN AVISAR
- `migrations/`

## Cuándo cerrar esta sesión de Claude Code
Si llevas ~60% del contexto, cierra y abre otra.
"""

ESTADO_BASE = {
    "version": "2.0",
    "fecha": "2026-07-26",
    "proyecto": {"nombre": "Demo", "tipo": "API REST", "tamaño": "pequeño",
                 "num_devs": 1, "modo_equipo": False},
    "config": {"idioma": "español", "formato": "markdown", "modo": "completo"},
    "stack": {"backend": "FastAPI"},
    "fases_planeadas": ["F1", "F2", "F3"],
}

BASE = {
    "CLAUDE.md": CLAUDE_MD,
    "docs/especificaciones.md": "# Especificaciones\n\nRequisitos del sistema.\n",
    "docs/guia_desarrollo.md": "# Guía\n\n## FASE 1\nObjetivo, prompt, checklist.\n",
    "ROADMAP.md": "# Roadmap\n\n| Fase | Estado |\n|---|---|\n| F1 | Pendiente |\n",
    "README.md": "# Demo\n\nCómo correrlo.\n",
    "docs/glosario.md": "# Glosario\n\n### Comprobante\nDocumento fiscal.\n",
    "progreso/estado-actual.md": "# Estado Actual\n\nSin arrancar.\n",
    ".gitignore": ".env\n__pycache__/\n",
    ".env.example": "DATABASE_URL=\nAPI_KEY=\n",
}

DE_EQUIPO = {
    "docs/equipo.md": "# Equipo\n\n| Módulo | Label |\n|---|---|\n| A | `modulo:A` |\n",
    "docs/backlog.md": "# Backlog\n\n### T-001 · [A] Login\n",
    "progreso/tablero-equipo.md": "# Tablero\n\n## Módulos\n",
    ".github/workflows/ci.yml": "name: ci\non: [push]\n",
    ".github/PULL_REQUEST_TEMPLATE.md": "## Qué hace\n\n## Checklist\n",
}


def construir(tmp: Path, extra=None, estado=None, quitar=()) -> Path:
    archivos = dict(BASE)
    archivos.update(extra or {})
    for ruta in quitar:
        archivos.pop(ruta, None)
    for ruta, contenido in archivos.items():
        destino = tmp / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido, encoding="utf-8")
    if estado is not None:
        (tmp / ".kickstart-state.json").write_text(
            json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    return tmp


def revisar(extra=None, estado="base", quitar=()):
    """Devuelve (fallos, salida). `estado=None` => no se escribe el archivo."""
    mod = cargar()
    if estado == "base":
        estado = ESTADO_BASE
    with tempfile.TemporaryDirectory() as tmp:
        raiz = construir(Path(tmp), extra, estado, quitar)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fallos = mod.revisar(raiz)
        return fallos, buf.getvalue()


CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


# --- El kit sano ------------------------------------------------------------

@caso("kit completo y coherente: ningun fallo")
def _():
    fallos, _s = revisar()
    assert fallos == [], fallos


# --- 1. Archivos prometidos y no escritos -----------------------------------

@caso("falta un archivo del nucleo: MUERDE")
def _():
    fallos, _s = revisar(quitar=["docs/glosario.md"])
    assert len(fallos) == 1, fallos
    assert "falta `docs/glosario.md`" in fallos[0]
    assert "se comprometió a generar" in fallos[0]


@caso("proyecto MEDIANO sin ADR: MUERDE (el tamaño lo obliga)")
def _():
    estado = json.loads(json.dumps(ESTADO_BASE))
    estado["proyecto"]["tamaño"] = "mediano"
    fallos, _s = revisar(estado=estado)
    assert any("0001-decisiones-iniciales.md" in f for f in fallos), fallos


@caso("proyecto PEQUENO sin ADR: no se exige")
def _():
    fallos, _s = revisar()
    assert not any("adr" in f for f in fallos), fallos


@caso("MODO EQUIPO sin backlog ni tablero: MUERDE")
def _():
    estado = json.loads(json.dumps(ESTADO_BASE))
    estado["proyecto"].update({"num_devs": 3, "modo_equipo": True})
    fallos, _s = revisar(estado=estado)
    assert any("docs/backlog.md" in f for f in fallos), fallos
    assert any("progreso/tablero-equipo.md" in f for f in fallos), fallos


@caso("modo equipo COMPLETO: pasa")
def _():
    estado = json.loads(json.dumps(ESTADO_BASE))
    estado["proyecto"].update({"num_devs": 3, "modo_equipo": True})
    fallos, _s = revisar(extra=DE_EQUIPO, estado=estado)
    assert fallos == [], fallos


@caso("2+ devs aunque modo_equipo venga en False: se exige igual")
def _():
    # El numero de devs es el hecho; el flag puede quedarse sin poner.
    estado = json.loads(json.dumps(ESTADO_BASE))
    estado["proyecto"].update({"num_devs": 2, "modo_equipo": False})
    fallos, _s = revisar(estado=estado)
    assert any("docs/equipo.md" in f for f in fallos), fallos


# --- 2. Placeholders sin resolver -------------------------------------------

@caso("placeholder sin rellenar: MUERDE y dice donde")
def _():
    fallos, _s = revisar({"README.md": "# Demo\n\nCorrer: `{{CMD_TEST}}`\n"})
    assert len(fallos) == 1, fallos
    assert "{{CMD_TEST}}" in fallos[0] and "README.md:3" in fallos[0], fallos


@caso("placeholder dentro de un bloque de codigo: es un EJEMPLO, no se acusa")
def _():
    fallos, _s = revisar({"docs/guia_desarrollo.md":
                          "# Guía\n\n```markdown\nRellena {{NOMBRE}} aquí\n```\n"})
    assert fallos == [], fallos


@caso("expresiones de GitHub Actions: NO son placeholders del kit")
def _():
    estado = json.loads(json.dumps(ESTADO_BASE))
    estado["proyecto"].update({"num_devs": 2, "modo_equipo": True})
    equipo = dict(DE_EQUIPO)
    equipo[".github/workflows/ci.yml"] = (
        "name: ci\non: [push]\njobs:\n  t:\n    steps:\n"
        "      - env: { TOKEN: ${{ secrets.GITHUB_TOKEN }} }\n")
    fallos, _s = revisar(extra=equipo, estado=estado)
    assert fallos == [], fallos


# --- 3. Enlaces entre documentos --------------------------------------------

@caso("enlace a un documento que no se genero: MUERDE")
def _():
    fallos, _s = revisar({"ROADMAP.md": "# Roadmap\n\nVer [el plan](docs/plan.md).\n"})
    assert len(fallos) == 1 and "enlace roto -> docs/plan.md" in fallos[0], fallos


@caso("enlaces http y anclas: no se tocan")
def _():
    fallos, _s = revisar({"README.md": "# Demo\n\n[web](https://x.com) y [arriba](#demo)\n"})
    assert fallos == [], fallos


# --- 4. CLAUDE.md util, no solo presente ------------------------------------

@caso("CLAUDE.md sin el mapa de donde esta cada cosa: MUERDE")
def _():
    fallos, _s = revisar({"CLAUDE.md": "# CLAUDE.md\n\n## Stack\nPython.\n"})
    assert any("mapa" in f for f in fallos), fallos
    assert len(fallos) == 3, "faltan las tres secciones, y hay que decirlas todas"


@caso("CLAUDE.md sin indicador de cierre de sesion: MUERDE")
def _():
    recortado = CLAUDE_MD.replace("## Cuándo cerrar esta sesión de Claude Code", "## Notas")
    fallos, _s = revisar({"CLAUDE.md": recortado})
    assert len(fallos) == 1 and "cerrar" in fallos[0], fallos


@caso("kit en ingles: se salta esa regla en vez de acusar en falso")
def _():
    estado = json.loads(json.dumps(ESTADO_BASE))
    estado["config"]["idioma"] = "inglés"
    fallos, salida = revisar({"CLAUDE.md": "# CLAUDE.md\n\n## Stack\nPython.\n"},
                             estado=estado)
    assert fallos == [], fallos
    assert "se salta" in salida, salida


# --- 5. No poder verificar NO es "esta bien" --------------------------------

@caso("sin .kickstart-state.json: PARA (no sabe que se prometio)")
def _():
    mod = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = construir(Path(tmp), None, None)
        try:
            mod.revisar(raiz)
            raise AssertionError("deberia haber fallado")
        except mod.KitIlegible as e:
            assert "no se verifica nada" in str(e), e


@caso("estado corrupto: PARA en vez de asumir lo minimo")
def _():
    mod = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = construir(Path(tmp), None, ESTADO_BASE)
        (raiz / ".kickstart-state.json").write_text("{ roto", encoding="utf-8")
        try:
            mod.revisar(raiz)
            raise AssertionError("deberia haber fallado")
        except mod.KitIlegible as e:
            assert "no es JSON válido" in str(e), e


@caso("estado sin 'proyecto': PARA (es lo que decide que es obligatorio)")
def _():
    mod = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = construir(Path(tmp), None, {"version": "2.0"})
        try:
            mod.revisar(raiz)
            raise AssertionError("deberia haber fallado")
        except mod.KitIlegible as e:
            assert "no declara 'proyecto'" in str(e), e


@caso("carpeta vacia: PARA (un OK sobre nada no significa nada)")
def _():
    mod = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / ".kickstart-state.json").write_text(
            json.dumps(ESTADO_BASE), encoding="utf-8")
        fallos = None
        with contextlib.suppress(mod.KitIlegible):
            fallos = mod.revisar(raiz)
        # Con solo el estado presente, o para por vacio o denuncia los que faltan;
        # lo que NO puede es devolver lista vacia.
        assert fallos is None or fallos, "no puede dar el kit por bueno"


# --- Salida de la herramienta -----------------------------------------------

@caso("main() con el kit roto: exit 1 y dice que no lo entregues")
def _():
    mod = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = construir(Path(tmp), None, ESTADO_BASE, quitar=["README.md"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            codigo = mod.main([str(raiz)])
    assert codigo == 1, codigo
    assert "ANTES de entregarlo" in buf.getvalue(), buf.getvalue()


@caso("main() con el kit sano: exit 0")
def _():
    mod = cargar()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = construir(Path(tmp), None, ESTADO_BASE)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            codigo = mod.main([str(raiz)])
    assert codigo == 0, buf.getvalue()


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
