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
  6. Ninguna orden de MIRAR un diseño se queda sin el comando que la hace
     ejecutable. Claude Code no tiene renderizador: «abre el prototipo» no es
     una instrucción, es una orden imposible. Ver `ordenes_sin_procedimiento`.

Qué NO mira, y a propósito: `SKILLS-PORTABLE/` y `.claude/`. Eso es el kit
INSTALADO —el paquete y el protocolo— no el kit GENERADO; sus placeholders son
plantilla. Ver `EXCLUIDAS`.

Límites conocidos, dichos en voz alta: esto verifica el ARTEFACTO, no el
criterio. Un kit puede pasar estas seis reglas y tener una guía de desarrollo
mediocre. Lo que impide es la clase de fallo que se cuela en silencio y aparece
semanas después, cuando el proyecto ya se apoyó en un documento que no existe.

Y la regla 6 es DELIBERADAMENTE estrecha: cubre el caso que ya costó una sesión
—mirar un diseño— y no intenta juzgar si una instrucción cualquiera es ejecutable,
que es un problema abierto. La regla general vive en la skill (regla 8 de calidad);
aquí solo muerde la forma concreta que se sabe que aparece. Prometer más sería
prometer una cobertura que no hay.

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

# --- Órdenes que el entorno de destino no puede cumplir (regla 6) -----------
#
# El caso real: entró un prototipo HTML cuyo texto decía "abre el prototipo y
# míralo", y el kickstart lo copió literal a ~16 subfases de la guía. Claude Code
# no tiene renderizador, así que ninguna se podía cumplir; y el desempaquetador
# que hizo falta para leerlo se quedó en la sesión, no en el repo.
#
# El objeto se limita a artefactos de diseño con forma de archivo. `diseño` a
# secas queda FUERA a propósito: en español cubre "el diseño de la base de
# datos" o "el diseño de la arquitectura", que se miran leyendo un .md y son
# perfectamente ejecutables. Meterlo convertiría esta regla en el ruido que
# M-10 enseñó a no volver a fabricar.
_VERBO = (r"(?<!se )\b(?:abre|ábre\w*|abrir|abrid|mira|míra\w*|mirar|mirad|"
          r"visualiza|previsualiza|inspecciona)\b")
_OBJETO = r"\b(?:prototipo|mockup|maqueta|wireframe|[\w./-]+\.html)\b"
# Las dos direcciones, porque en el corpus real aparecen las dos: "ABRE el
# prototipo" y "(pantalla 8 del prototipo — ábrelo)". Con una sola se escapaban
# órdenes idénticas por el orden de las palabras.
ORDEN_VISUAL = re.compile(
    rf"{_VERBO}[^.;\n]{{0,60}}?{_OBJETO}|{_OBJETO}[^.;\n]{{0,60}}?{_VERBO}",
    re.IGNORECASE,
)
# Lo que convierte la orden en procedimiento: una invocación de verdad, y a una
# herramienta que está EN EL REPO. No basta con citar el archivo de diseño —que
# exista no lo hace legible— ni con nombrar un script que se quedó en la sesión,
# que fue la otra mitad del fallo.
INVOCACION = re.compile(
    r"(?:python3?|node|sh|bash)\s+([\w./-]+)|(?:^|\s)(\./[\w./-]+|[\w./-]+\.(?:py|sh|js|mjs))\b"
)
HERRAMIENTA = (".py", ".sh", ".js", ".mjs")
VENTANA = 3  # líneas tras la orden: el comando casi siempre va justo debajo

# Carpetas que NO son el kit generado, aunque vivan dentro del proyecto.
#
# `SKILLS-PORTABLE/` es la copia del paquete que deja `instalar.sh` (de ahí lee
# el kickstart sus plantillas) y `.claude/` son las skills y hooks del
# protocolo. Sus `{{...}}` son documentación de plantilla y sus enlaces apuntan
# al paquete, no al proyecto. Escanearlas hacía que en un proyecto con el kit
# instalado —o sea, el caso normal— la primera ejecución saliera roja con 37
# fallos y ninguno señalando un archivo generado. Y una guarda que sale roja con
# ruido no se lee: se rodea. Eso fue exactamente lo que pasó en la primera
# ejecución real.
#
# Los placeholders que SÍ hay que rellenar dentro de `.claude/` (`OWNER`,
# `PROJECT_NUMBER` de las skills de equipo) los reclama el checklist de
# `instalar.sh`, que es quien los puso ahí. Este verificador responde por lo que
# generó el kickstart; repartir esa responsabilidad es lo que evita el ruido.
EXCLUIDAS = frozenset({".git", "node_modules", "SKILLS-PORTABLE", ".claude"})


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
    # Los paréntesis de la disyunción no son estilo: `and` liga más fuerte que
    # `or`, así que sin ellos un DIRECTORIO llamado `.gitignore` o
    # `.env.example` entraba en la lista y reventaba al leerlo.
    # Y la exclusión se mide sobre la ruta RELATIVA a la raíz: si el proyecto
    # vive dentro de una carpeta llamada `.claude`, lo que hay que verificar es
    # el proyecto, no callarse entero.
    return sorted(
        p for p in raiz.rglob("*")
        if p.is_file()
        and (p.suffix in EXTENSIONES or p.name in (".gitignore", ".env.example"))
        and EXCLUIDAS.isdisjoint(p.relative_to(raiz).parts)
    )


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


def herramientas_del_repo(raiz: Path) -> set[str]:
    """Scripts que el proyecto se lleva puestos, por nombre.

    Mismo criterio de exclusión que el resto: una herramienta dentro de
    `SKILLS-PORTABLE/` es del kit instalado, no algo que esta guía pueda
    prometer que estará ahí."""
    return {
        p.name for p in raiz.rglob("*")
        if p.is_file() and p.suffix in HERRAMIENTA
        and EXCLUIDAS.isdisjoint(p.relative_to(raiz).parts)
    }


def _hay_procedimiento(lineas: list[str], herramientas: set[str]) -> bool:
    """¿Alguna de estas líneas invoca una herramienta que existe en el repo?

    Las dos mitades importan y las dos fallaron de verdad: sin invocación, la
    orden sigue siendo «míralo»; y con una invocación a un script que se quedó
    en la sesión, la siguiente sesión tiene que rehacerlo."""
    for linea in lineas:
        for grupos in INVOCACION.findall(linea):
            for candidato in grupos:
                ruta = (candidato or "").strip()
                if ruta.endswith(HERRAMIENTA) and Path(ruta).name in herramientas:
                    return True
    return False


def ordenes_sin_procedimiento(raiz: Path) -> list[str]:
    """Órdenes de MIRAR un diseño que el entorno de destino no puede cumplir.

    Claude Code no tiene renderizador. «Abre el prototipo y míralo» no es una
    instrucción difícil: es imposible, y quien la lea o repite la ingeniería
    inversa que ya se hizo una vez o se inventa el diseño. La orden vale si al
    lado está el comando que sí funciona, apuntando a una herramienta del repo.

    Esta regla SÍ mira dentro de los bloques de código, y es la única que lo
    hace. El resto los salta porque ahí viven plantillas y ejemplos; aquí no:
    en la guía generada, los bloques son los PROMPTS que el dev pega en Claude
    Code (regla 2 de calidad: literales y copy-pasteables). Comprobado contra el
    proyecto real — saltándolos, de las ~16 órdenes imposibles que tenía la guía
    no se veía ni una, porque todas vivían dentro del prompt de su subfase.
    """
    fallos = []
    herramientas = herramientas_del_repo(raiz)
    for archivo in (a for a in archivos_del_kit(raiz) if a.suffix == ".md"):
        lineas = archivo.read_text(encoding="utf-8").splitlines()
        for num, linea in enumerate(lineas, 1):
            m = ORDEN_VISUAL.search(linea)
            if not m or _hay_procedimiento(lineas[num - 1:num + VENTANA], herramientas):
                continue
            fallos.append(
                f"{archivo.relative_to(raiz).as_posix()}:{num}: "
                f"«{m.group(0).strip()}» no se puede cumplir en Claude Code, que no "
                f"tiene renderizador. Escribe el comando que sí funciona y deja la "
                f"herramienta en el repo (regla 8 de calidad de la skill)"
            )
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
            + claude_md_incompleto(raiz, estado)
            + ordenes_sin_procedimiento(raiz))


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
          "enlaces OK, CLAUDE.md completo y ninguna orden que su entorno no pueda "
          "cumplir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
