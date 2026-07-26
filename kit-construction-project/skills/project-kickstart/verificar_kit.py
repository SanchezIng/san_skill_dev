#!/usr/bin/env python3
"""Verifica el kit RECIÉN GENERADO por project-kickstart, antes de entregarlo.

Por qué existe: `kickstart_check.py` (en la raíz del paquete) comprueba que la
skill no prometa lo que sus plantillas no describen. Eso valida la PLANTILLA. Lo
que nadie validaba es la GENERACIÓN: que el kit que acaba de salir tenga de
verdad los archivos prometidos, sin placeholders a medio rellenar y sin enlaces
que apunten a documentos que nunca se escribieron.

No se puede testear ejecutando la skill: es prosa que interpreta un Claude, y no
hay forma de correr eso en CI. Lo que sí se puede es **verificar el artefacto en
el momento en que se produce**, que es cuando el error todavía es gratis de
arreglar. Por eso esto se ejecuta en el Paso 10, antes de `present_files`.

Qué comprueba, todo contra `.kickstart-state.json` (lo que la propia entrevista
decidió, no lo que este script suponga):

  1. Están los archivos que ese estado obliga a generar — núcleo y soporte
     siempre; equipo si hay 2+ devs; ADR si es mediano/grande.
  2. Cero `{{PLACEHOLDER}}` sin resolver fuera de bloques de código.
  3. Los enlaces relativos entre los documentos resuelven.
  4. CLAUDE.md trae las secciones que lo hacen útil (mapa, archivos críticos,
     indicador de cierre de sesión), no solo el nombre correcto.
  5. El propio `.kickstart-state.json` es JSON válido y declara lo que dice
     declarar — es la fuente de las otras cuatro comprobaciones.

Límite conocido, dicho en voz alta: esto verifica el ARTEFACTO, no el criterio.
Un kit puede pasar estas cinco reglas y tener una guía de desarrollo mediocre.
Lo que impide es la clase de fallo que se cuela en silencio y aparece semanas
después, cuando el proyecto ya se apoyó en un documento que no existe.

Uso:
    python3 verificar_kit.py [directorio]     # por defecto, el actual
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ESTADO = ".kickstart-state.json"

# Siempre, según el Paso 9 (núcleo + soporte).
OBLIGATORIOS = [
    "CLAUDE.md",
    "docs/especificaciones.md",
    "docs/guia_desarrollo.md",
    "ROADMAP.md",
    "README.md",
    "docs/glosario.md",
    "progreso/estado-actual.md",
    ".gitignore",
    ".env.example",
]

# Solo en modo colaborativo (2+ devs).
DE_EQUIPO = [
    "docs/equipo.md",
    "docs/backlog.md",
    "progreso/tablero-equipo.md",
    ".github/workflows/ci.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
]

# Solo mediano/grande.
DE_TAMANO = {"mediano", "grande"}
ADR_INICIAL = "docs/adr/0001-decisiones-iniciales.md"

# Secciones que CLAUDE.md debe tener para servir de mapa. Se buscan como
# subcadenas en minúsculas: el título exacto puede variar, la función no.
SECCIONES_CLAUDE = {
    "dónde encontrar": "el mapa de dónde está cada cosa (sin él, cada sesión relee todo)",
    "no tocar": "la lista de archivos críticos que no se tocan sin avisar",
    "cerrar esta sesión": "el indicador de cuándo cerrar la sesión",
}

FENCE = re.compile(r"^(```|~~~)")
ENLACE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
PLACEHOLDER = re.compile(r"\{\{([^}]+)\}\}")
# Igual que en el resto del kit: `${{ secrets.X }}` de Actions y `{{owner}}` de
# `gh api` NO son placeholders nuestros, y confundirlos convierte esto en ruido.
NOMBRE_PLACEHOLDER = re.compile(r"^[A-Z][A-Z0-9_]*$")

EXTENSIONES = (".md", ".json", ".yml", ".yaml", ".example", ".gitignore")


class KitIlegible(Exception):
    """No se puede emitir veredicto. NO es "el kit está bien"."""


def _sin_fences(texto: str) -> list[str]:
    fuera, en_fence = [], False
    for linea in texto.splitlines():
        if FENCE.match(linea.strip()):
            en_fence = not en_fence
            continue
        if not en_fence:
            fuera.append(linea)
    return fuera


def leer_estado(raiz: Path) -> dict:
    ruta = raiz / ESTADO
    if not ruta.is_file():
        raise KitIlegible(
            f"No hay {ESTADO} en {raiz}.\n"
            f"   El Paso 9 lo genera SIEMPRE: si falta, o no se generó el kit ahí,\n"
            f"   o falta el archivo que guarda las decisiones de la entrevista.\n"
            f"   Sin él no se sabe qué se prometió, así que no se verifica nada."
        )
    try:
        estado = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise KitIlegible(f"{ESTADO} no es JSON válido ({e}).") from None
    if not isinstance(estado.get("proyecto"), dict):
        raise KitIlegible(f"{ESTADO} no declara 'proyecto': no se puede saber "
                          f"tamaño ni modo, que es lo que decide qué es obligatorio.")
    return estado


def archivos_del_kit(raiz: Path) -> list[Path]:
    salida = [
        p for p in raiz.rglob("*")
        if p.is_file()
        and p.suffix in EXTENSIONES or p.name in (".gitignore", ".env.example")
    ]
    return sorted(p for p in salida if ".git" not in p.parts and "node_modules" not in p.parts)


def obligatorios_segun(estado: dict) -> list[str]:
    proyecto = estado.get("proyecto") or {}
    esperados = list(OBLIGATORIOS) + [ESTADO]

    tamano = str(proyecto.get("tamaño") or proyecto.get("tamano") or "").lower()
    if tamano in DE_TAMANO:
        esperados.append(ADR_INICIAL)

    devs = proyecto.get("num_devs") or 1
    if proyecto.get("modo_equipo") or (isinstance(devs, int) and devs >= 2):
        esperados += DE_EQUIPO
    return esperados


def faltan_archivos(raiz: Path, estado: dict) -> list[str]:
    """Un documento prometido y no escrito es el fallo más caro del kickstart:
    aparece semanas después, cuando alguien lo busca porque el índice lo cita."""
    fallos = []
    for rel in obligatorios_segun(estado):
        if not (raiz / rel).is_file():
            fallos.append(f"falta `{rel}`, que este kit se comprometió a generar")
    return fallos


def placeholders_sin_resolver(archivos: list[Path], raiz: Path) -> list[str]:
    fallos = []
    for archivo in archivos:
        for num, linea in enumerate(_sin_fences(archivo.read_text(encoding="utf-8")), 1):
            for crudo in PLACEHOLDER.findall(linea):
                if NOMBRE_PLACEHOLDER.match(crudo.strip()):
                    fallos.append(
                        f"{archivo.relative_to(raiz).as_posix()}:{num}: "
                        f"`{{{{{crudo.strip()}}}}}` sin rellenar"
                    )
    return fallos


def enlaces_rotos(archivos: list[Path], raiz: Path) -> list[str]:
    fallos = []
    for archivo in (a for a in archivos if a.suffix == ".md"):
        for num, linea in enumerate(_sin_fences(archivo.read_text(encoding="utf-8")), 1):
            for destino in ENLACE.findall(linea):
                if destino.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                ruta = destino.split("#", 1)[0]
                if not ruta or "{" in ruta:
                    continue
                if (archivo.parent / ruta).exists() or (raiz / ruta).exists():
                    continue
                fallos.append(f"{archivo.relative_to(raiz).as_posix()}:{num}: "
                              f"enlace roto -> {destino}")
    return fallos


def claude_md_incompleto(raiz: Path, estado: dict) -> list[str]:
    """CLAUDE.md es el único archivo que se lee en TODAS las sesiones. Que exista
    no basta: si no trae el mapa, cada sesión vuelve a leer el proyecto entero."""
    idioma = str((estado.get("config") or {}).get("idioma") or "español").lower()
    if not idioma.startswith(("es", "sp")):
        print(f"(idioma '{idioma}': se salta la revisión de secciones de CLAUDE.md, "
              f"escritas para español)")
        return []
    ruta = raiz / "CLAUDE.md"
    if not ruta.is_file():
        return []  # ya lo denuncia faltan_archivos
    texto = ruta.read_text(encoding="utf-8").lower()
    return [f"CLAUDE.md no incluye {para_que} (falta '{clave}')"
            for clave, para_que in SECCIONES_CLAUDE.items() if clave not in texto]


def revisar(raiz: Path) -> list[str]:
    estado = leer_estado(raiz)
    archivos = archivos_del_kit(raiz)
    if not archivos:
        raise KitIlegible(f"No se encontró ningún archivo de kit en {raiz}: un "
                          f"'todo OK' sobre una carpeta vacía no significaría nada.")
    return (faltan_archivos(raiz, estado)
            + placeholders_sin_resolver(archivos, raiz)
            + enlaces_rotos(archivos, raiz)
            + claude_md_incompleto(raiz, estado))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    raiz = Path(argv[0] if argv else ".").resolve()
    try:
        fallos = revisar(raiz)
    except KitIlegible as e:
        print(f"FALLO {e}")
        print("\nNo se ha podido verificar el kit. No lo entregues como bueno.")
        return 1

    for fallo in fallos:
        print(f"FALLO {fallo}")
    if fallos:
        print(f"\n{len(fallos)} problema(s) en el kit generado. Arréglalos ANTES de "
              f"entregarlo: ahora cuestan un minuto y luego cuestan una sesión.")
        return 1
    print("Kit generado coherente: archivos prometidos, sin placeholders sueltos, "
          "enlaces OK y CLAUDE.md completo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
