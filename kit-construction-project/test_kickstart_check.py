#!/usr/bin/env python3
"""Tests de la guarda kickstart_check.py.

Por que existen: una guarda que nunca se ha visto FALLAR no esta verificada.
Cada regla se prueba en los DOS sentidos — que deja pasar el paquete sano y que
muerde el roto. Se monta un paquete sintetico minimo en un directorio temporal
(mismo patron que test_instalar.sh) y se le rompe una cosa cada vez: asi el fallo
que se observa es el de la regla bajo prueba y no ruido de otra.

Uso: python3 test_kickstart_check.py     (exit 1 si algun caso falla)
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "kickstart_check.py"


def cargar(raiz: Path):
    spec = importlib.util.spec_from_file_location("kickstart_check", MODULO)
    kc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kc)
    kc.RAIZ = raiz
    return kc


# --------------------------------------------------------- paquete sintetico

SKILL_MD = """---
name: project-kickstart
---

# Project Kickstart

### Paso 9 - Generacion de archivos

1. `CLAUDE.md` con el mapa de archivos
2. `docs/especificaciones.md` con seguridad integrada
3. `progreso/estado-actual.md` - plantilla vacia

Las plantillas del protocolo viajan JUNTO a esta skill:

```
<paquete>/skills/equipo/*.SKILL.md     <- las skills parametrizadas
<paquete>/plantillas/hooks/            <- hook SessionStart
<paquete>/plantillas/CLAUDE-fragmento.md
```

4. `.claude/skills/equipo-que-toca/SKILL.md` - reclamo de tareas

Ver [el README del paquete](../../README.md) antes de instanciar.
Aplica ademas las secciones 1 y 2 de `references/trabajo_en_equipo.md`.

### Paso 10 - Entrega

Entrega todo.

## Archivos de referencia

- `references/plantillas.md` - estructura exacta de los archivos
- `references/trabajo_en_equipo.md` - modo colaborativo
"""

PLANTILLAS_MD = """# Plantillas

## Lista de archivos a generar

1. `CLAUDE.md`
2. `docs/especificaciones.md`
3. `progreso/estado-actual.md` (plantilla vacia)

La de `estado-actual.md` esta en `trabajo_en_equipo.md` (secciones 1 y 2).

---

## ARCHIVO 1: CLAUDE.md

```markdown
# CLAUDE.md - {{NOMBRE_PROYECTO}}

## ARCHIVO 99: esto es un ejemplo dentro de un bloque, no una plantilla real
```

## ARCHIVO 2: docs/especificaciones.md

Ver `references/trabajo_en_equipo.md` seccion 2 para el detalle.
"""

EQUIPO_MD = """# /que-toca

Rama: `{{PREFIJO_RAMA}}`. Tests: `{{CMD_TEST}}`.
Listado: `gh api repos/{{owner}}/{{repo}}/issues`.
"""

CI_YML = """name: ci
on: [push]
jobs:
  x:
    steps:
      - env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 scripts/docs_check.py
"""

README_MD = """# SKILLS-PORTABLE

## Placeholders a rellenar

| Placeholder | Ejemplo | De donde sale |
|---|---|---|
| `OWNER` (constante en `scripts/tablero.py`) | `SanchezIng` | dueno del Project |
| `{{PREFIJO_RAMA}}` | `{modulo}/{tarea}` | convencion |
| `{{CMD_TEST}}` | `pytest` | stack |

## Otra cosa

Nada que ver.
"""

TRABAJO_MD = """# Trabajo en equipo

## 1. Principio central

Propiedad colectiva.

## 2. El tablero vivo

Plantilla de `progreso/estado-actual.md`:

```markdown
## 4. Esta cabecera vive dentro de un bloque: NO es una seccion real
```
"""

BASE = {
    "README.md": README_MD,
    "skills/project-kickstart/SKILL.md": SKILL_MD,
    "skills/project-kickstart/references/plantillas.md": PLANTILLAS_MD,
    "skills/project-kickstart/references/trabajo_en_equipo.md": TRABAJO_MD,
    "skills/equipo/que-toca.SKILL.md": EQUIPO_MD,
    "plantillas/CLAUDE-fragmento.md": "# Fragmento\n",
    "plantillas/hooks/arranque.sh": "#!/bin/sh\necho hola\n",
    "plantillas/ci/ci.yml": CI_YML,
}


def construir(tmp: Path, cambios: dict[str, str | None] | None = None) -> Path:
    """Escribe el paquete base con `cambios` aplicados (None = borrar archivo)."""
    archivos = dict(BASE)
    for ruta, contenido in (cambios or {}).items():
        if contenido is None:
            archivos.pop(ruta, None)
        else:
            archivos[ruta] = contenido
    for ruta, contenido in archivos.items():
        destino = tmp / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido, encoding="utf-8")
    return tmp


def revisar(cambios: dict[str, str | None] | None = None) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        raiz = construir(Path(tmp), cambios)
        return cargar(raiz).revisar()


def sustituir(texto: str, viejo: str, nuevo: str) -> str:
    assert viejo in texto, f"el test se escribio contra un texto que ya no existe: {viejo!r}"
    return texto.replace(viejo, nuevo)


CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


# ------------------------------------------------------------------- el sano

@caso("paquete sano: ningun fallo")
def _():
    assert revisar() == [], revisar()


# --------------------------------------------------------------- 1 inventario

@caso("directorio vacio: MUERDE en vez de decir que todo esta bien")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        fallos = cargar(Path(tmp)).revisar()
    assert fallos, "un paquete inexistente no puede salir 'coherente'"
    assert "no existe" in fallos[0]


@caso("sin plantillas instalables: MUERDE (la lista vacia no sostiene un OK)")
def _():
    fallos = revisar({
        "skills/equipo/que-toca.SKILL.md": None,
        "plantillas/CLAUDE-fragmento.md": None,
        "plantillas/hooks/arranque.sh": None,
        "plantillas/ci/ci.yml": None,
    })
    assert any("inventario esta vacio" in f for f in fallos), fallos


# ---------------------------------------------------------- 2 listas cuadradas

@caso("las dos listas nombran archivos distintos: MUERDE")
def _():
    roto = sustituir(PLANTILLAS_MD, "2. `docs/especificaciones.md`", "2. `docs/specs.md`")
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": roto})
    assert any("archivo 2: SKILL.md dice `docs/especificaciones.md`" in f
               for f in fallos), fallos


@caso("el Paso 9 promete uno que la lista no tiene: MUERDE")
def _():
    roto = sustituir(PLANTILLAS_MD, "2. `docs/especificaciones.md`\n", "")
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": roto})
    assert any("plantillas.md no lista" in f for f in fallos), fallos


@caso("la lista tiene uno que el Paso 9 no promete: MUERDE")
def _():
    roto = sustituir(SKILL_MD, "2. `docs/especificaciones.md` con seguridad integrada\n", "")
    fallos = revisar({"skills/project-kickstart/SKILL.md": roto})
    assert any("que el Paso 9 de SKILL.md no promete" in f for f in fallos), fallos


@caso("los numeros >= tope de la lista (piezas del paquete) no se exigen")
def _():
    # El item 4 del Paso 9 es una skill del protocolo, no un archivo generado.
    assert revisar() == []


# ------------------------------------------------------- 3 plantilla presente

@caso("archivo prometido sin plantilla ni delegacion: MUERDE")
def _():
    roto = sustituir(PLANTILLAS_MD, "## ARCHIVO 2: docs/especificaciones.md",
                     "## Cualquier otra cosa")
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": roto})
    assert any("se promete `docs/especificaciones.md` (archivo 2) y ninguna plantilla"
               in f for f in fallos), fallos


@caso("delegado a otra referencia (no tiene seccion propia): PASA")
def _():
    # `progreso/estado-actual.md` no tiene ARCHIVO 3; vive en trabajo_en_equipo.md.
    assert not any("estado-actual" in f for f in revisar())


@caso("la cabecera ARCHIVO n describe otra ruta que la lista: MUERDE")
def _():
    roto = sustituir(PLANTILLAS_MD, "## ARCHIVO 2: docs/especificaciones.md",
                     "## ARCHIVO 2: docs/otra-cosa.md")
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": roto})
    assert any("describe `docs/otra-cosa.md` pero la lista dice" in f
               for f in fallos), fallos


@caso("cabecera ARCHIVO de ejemplo DENTRO de un bloque: no cuenta como plantilla")
def _():
    # El paquete base ya tiene `## ARCHIVO 99:` dentro de un fence. Si contara,
    # una plantilla de ejemplo taparia la ausencia de la real.
    roto = sustituir(PLANTILLAS_MD, "## ARCHIVO 1: CLAUDE.md", "## Sin plantilla")
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": roto})
    assert any("se promete `CLAUDE.md` (archivo 1)" in f for f in fallos), fallos


# ------------------------------------------------------ 4 rutas del paquete

@caso("el Paso 9 declara un directorio del paquete que no existe: MUERDE")
def _():
    fallos = revisar({"plantillas/hooks/arranque.sh": None})
    assert any("plantillas/hooks/" in f and "no existe" in f for f in fallos), fallos


@caso("el glob de las skills del equipo no encaja con nada: MUERDE")
def _():
    fallos = revisar({"skills/equipo/que-toca.SKILL.md": None,
                      "skills/equipo/otra.md": "# no es una SKILL\n"})
    assert any("*.SKILL.md" in f for f in fallos), fallos


@caso("archivo suelto del paquete que se renombra: MUERDE")
def _():
    fallos = revisar({"plantillas/CLAUDE-fragmento.md": None,
                      "plantillas/CLAUDE-trozo.md": "# Fragmento\n"})
    assert any("CLAUDE-fragmento.md" in f for f in fallos), fallos


# --------------------------------------------------- 5 enlaces y referencias

@caso("enlace relativo roto: MUERDE")
def _():
    roto = sustituir(SKILL_MD, "(../../README.md)", "(../../LEEME.md)")
    fallos = revisar({"skills/project-kickstart/SKILL.md": roto})
    assert any("enlace roto -> ../../LEEME.md" in f for f in fallos), fallos


@caso("enlaces http y anclas: no se tocan")
def _():
    extra = SKILL_MD + "\nVer [la web](https://example.com) y [arriba](#paso-9).\n"
    fallos = revisar({"skills/project-kickstart/SKILL.md": extra})
    assert not any("enlace roto" in f for f in fallos), fallos


@caso("`references/x.md` que no existe: MUERDE")
def _():
    roto = sustituir(SKILL_MD, "`references/trabajo_en_equipo.md` - modo colaborativo",
                     "`references/inventado.md` - fantasma")
    fallos = revisar({"skills/project-kickstart/SKILL.md": roto})
    assert any("`references/inventado.md`, que no existe" in f for f in fallos), fallos


@caso("otra skill con SUS propias references: no se acusa en falso")
def _():
    # Regresion: la primera version resolvia todo contra las del kickstart y
    # denunciaba las cinco referencias reales de secure-coding-guard.
    fallos = revisar({
        "skills/secure-coding-guard/SKILL.md": "Lee `references/owasp.md`.\n",
        "skills/secure-coding-guard/references/owasp.md": "# OWASP\n",
    })
    assert fallos == [], fallos


@caso("referencia que existe y SKILL.md no lista: MUERDE (nadie la cargara)")
def _():
    fallos = revisar({"skills/project-kickstart/references/huerfana.md": "# Sola\n"})
    assert any("huerfana.md existe y SKILL.md no lo lista" in f for f in fallos), fallos


# --------------------------------------------------------- 6 secciones citadas

@caso("citar una seccion que no existe: MUERDE")
def _():
    roto = sustituir(PLANTILLAS_MD, "seccion 2 para el detalle", "seccion 9 para el detalle")
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": roto})
    assert any("seccion 9, que no existe" in f for f in fallos), fallos


@caso("citar varias secciones y una no existir: MUERDE")
def _():
    roto = sustituir(SKILL_MD, "las secciones 1 y 2 de", "las secciones 1 y 7 de")
    fallos = revisar({"skills/project-kickstart/SKILL.md": roto})
    assert any("seccion 7" in f for f in fallos), fallos


@caso("cabecera numerada DENTRO de un bloque: no cuenta como seccion real")
def _():
    # trabajo_en_equipo.md tiene un `## 4.` de ejemplo dentro de un fence.
    roto = sustituir(PLANTILLAS_MD, "seccion 2 para el detalle", "seccion 4 para el detalle")
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": roto})
    assert any("seccion 4, que no existe" in f for f in fallos), fallos


@caso("citar una seccion de un archivo GENERADO: no se audita (aun no existe)")
def _():
    extra = PLANTILLAS_MD + "\nVer `especificaciones.md` seccion 11 (regulacion).\n"
    fallos = revisar({"skills/project-kickstart/references/plantillas.md": extra})
    assert fallos == [], fallos


@caso("las citas desde codigo (.py) tambien se auditan")
def _():
    fallos = revisar({"plantillas/ci/docs_check.py":
                      "# Ver trabajo_en_equipo.md §6 para el formato.\n"})
    assert any("seccion 6, que no existe" in f for f in fallos), fallos


# ------------------------------------------------------------ 7 placeholders

@caso("placeholder usado y no documentado: MUERDE")
def _():
    roto = EQUIPO_MD + "\nSuite: `{{CMD_LINT}}`.\n"
    fallos = revisar({"skills/equipo/que-toca.SKILL.md": roto})
    assert any("`{{CMD_LINT}}` se usa en" in f for f in fallos), fallos


@caso("placeholder documentado que ya no usa nadie: MUERDE")
def _():
    roto = sustituir(README_MD, "| `{{CMD_TEST}}` | `pytest` | stack |",
                     "| `{{CMD_TEST}}` | `pytest` | stack |\n| `{{CMD_VIEJO}}` | - | - |")
    fallos = revisar({"README.md": roto})
    assert any("documenta `{{CMD_VIEJO}}` y ninguna plantilla lo usa" in f
               for f in fallos), fallos


@caso("expresiones de GitHub Actions y de `gh api`: NO son placeholders del kit")
def _():
    # El paquete base ya trae `${{ secrets.GITHUB_TOKEN }}` y `{{owner}}/{{repo}}`.
    fallos = revisar()
    assert not any("secrets" in f or "owner" in f for f in fallos), fallos


@caso("documentado a secas (sin llaves, como OWNER): se acepta")
def _():
    roto = EQUIPO_MD + "\nDueno: `{{OWNER}}`.\n"
    fallos = revisar({"skills/equipo/que-toca.SKILL.md": roto})
    assert fallos == [], fallos


@caso("sin la seccion de placeholders en el README: MUERDE")
def _():
    roto = sustituir(README_MD, "## Placeholders a rellenar", "## Variables")
    fallos = revisar({"README.md": roto})
    assert any("no se encontro la seccion" in f for f in fallos), fallos


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
