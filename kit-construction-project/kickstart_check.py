#!/usr/bin/env python3
"""Guarda de coherencia del paquete `project-kickstart`.

`project-kickstart` son ~3.000 lineas de prosa que NADIE puede ejecutar: es una
skill que un Claude lee para generar el kit de un proyecto nuevo. No se puede
testear la prosa, pero SI las promesas que hace sobre si misma. Hoy nada impide
que la skill prometa un archivo que ninguna plantilla describe, que apunte a una
seccion renumerada, o que deje un placeholder que nadie sabe que hay que
rellenar. Y es la pieza que todo proyecto nuevo toca primero.

Lo que se comprueba (todo dentro del paquete; no hace falta ejecutar la skill):

  1. El Paso 9 de SKILL.md y la "Lista de archivos a generar" de plantillas.md
     describen los MISMOS archivos con los MISMOS numeros.
  2. Cada archivo de esa lista tiene plantilla: seccion `## ARCHIVO n:` propia,
     o delegacion que resuelve (la ruta aparece en otra referencia).
  3. Las rutas del paquete que el Paso 9 declara (`<paquete>/...`) existen.
  4. Enlaces markdown relativos y referencias `references/*.md` que resuelven,
     e inventario de `references/` cuadrado con la lista de SKILL.md.
  5. Las secciones numeradas que un documento del kit cita de otro existen.
  6. Todo `{{PLACEHOLDER}}` de las plantillas instalables esta documentado en la
     tabla del README, y todo el que la tabla documenta se sigue usando.
  7. La skill sigue diciendo que lo que genera tiene que ser EJECUTABLE en su
     entorno de destino: la fila del diseno en la tabla de entorno y la regla
     que la generaliza en las "Inviolables".

Limites conocidos (dichos en voz alta, que es lo contrario de fingir cobertura):

  - No se ejecuta el kickstart. Esto valida la PLANTILLA, no la generacion: un
     Claude que ignore la plantilla sigue pudiendo generar cualquier cosa. El
     paso siguiente seria un `--dry-run` con una entrevista de fixture.
  - Las referencias a secciones de archivos que el kit GENERA (p.ej.
     "especificaciones.md seccion 11") no se comprueban: ese archivo no existe
     hasta que hay proyecto. Solo se exigen las referencias internas al kit.

Uso:   python3 kickstart_check.py          (desde donde sea; exit 1 si hay fallos)
Tests: python3 test_kickstart_check.py     (la guarda tambien se prueba)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

SKILL = "skills/project-kickstart/SKILL.md"
REFERENCIAS = "skills/project-kickstart/references"
PLANTILLAS_MD = f"{REFERENCIAS}/plantillas.md"
LEEME = "README.md"

# Donde viven las plantillas que se INSTALAN en el proyecto destino: son las que
# llevan placeholders que alguien tendra que rellenar.
ARBOLES_INSTALABLES = ["skills/equipo", "plantillas"]

FENCE = re.compile(r"^(```|~~~)")
ENLACE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ITEM = re.compile(r"^(\d+)\.\s+(.*)")
BACKTICK = re.compile(r"`([^`]+)`")
CABECERA_ARCHIVO = re.compile(r"^## ARCHIVO (\d+):\s*(\S+)", re.MULTILINE)
SECCION_NUMERADA = re.compile(r"^## (\d+)\.")

# "`practicas_dev.md` seccion 4"  ·  "trabajo_en_equipo.md §6"
CITA_SIMPLE = re.compile(r"([\w./_-]+\.md)`?\s*(?:§|secci[óo]n\s+)(\d+)")
# "las secciones 2, 3 y 5 de `references/trabajo_en_equipo.md`"
CITA_MULTI_DE = re.compile(r"secciones\s+([\d,\s]+(?:y\s+\d+)?)\s+de\s+`?([\w./_-]+\.md)")
# "`trabajo_en_equipo.md` (secciones 3, 6, 9, 10 y 11)"
CITA_MULTI_PAREN = re.compile(r"([\w./_-]+\.md)`?\s*\(secciones\s+([\d,\s]+(?:y\s+\d+)?)\)")

# Placeholders del kit: MAYUSCULAS. Se dejan fuera a proposito dos lenguajes de
# expresiones que comparten sintaxis y NO son nuestros:
#   - GitHub Actions: `${{ secrets.GITHUB_TOKEN }}`, `${{ github.sha }}` (con
#     espacios y puntos) — los rellena Actions, no el instalador.
#   - `gh api repos/{{owner}}/{{repo}}/...` (minusculas) — los rellena `gh`.
# Confundirlos con placeholders del kit convertiria la guarda en ruido.
PLACEHOLDER = re.compile(r"\{\{([^}]+)\}\}")
NOMBRE_PLACEHOLDER = re.compile(r"^[A-Z][A-Z0-9_]*$")
TOKEN_MAYUSCULAS = re.compile(r"\b[A-Z][A-Z0-9_]{3,}\b")

SECCION_PLACEHOLDERS = "## Placeholders a rellenar"
SECCION_REFERENCIAS_SKILL = "## Archivos de referencia"

# Herramientas que solo existen en el chat de claude.ai. La skill nacio alli y
# hoy viaja dentro de proyectos de Claude Code, donde NO existen: si se nombran
# sin decir por que traducirlas, un Claude Code improvisa en el paso de entrega,
# que es justo donde se pierden archivos.
HERRAMIENTAS_DE_CHAT = ("ask_user_input_v0", "present_files", "skill `docx`")
SECCION_ENTORNO = "## Antes del Paso 0"

# La otra mitad del entorno, y la que costo una sesion entera: no es una
# herramienta que la skill NOMBRE, es una capacidad que sus pasos dan por
# supuesta. El Paso 0 pide "mockups o screenshots de la UI" y en el chat eso se
# ve renderizado; en Claude Code no hay renderizador. Sin esa fila, el kickstart
# copia "abre el prototipo" del material de entrada a la guia generada y produce
# ordenes que su lector no puede cumplir.
SENA_DISENO = "renderizador"
# Y la regla que lo generaliza, en las "Inviolables": lo heredado de la entrada
# se reescribe ejecutable, y la herramienta que hizo falta se queda en el repo.
SECCION_CALIDAD = "## Reglas de calidad de los archivos generados"
SENA_EJECUTABLE = "ejecutable por quien va a ejecutarlo"


# ---------------------------------------------------------------- utilidades

def _leer(rel: str) -> str:
    return (RAIZ / rel).read_text(encoding="utf-8")


def _sin_fences(texto: str) -> list[str]:
    """Lineas fuera de bloques ``` o ~~~.

    Las plantillas del kit son bloques de codigo llenos de cabeceras `## ...`
    de ejemplo. Tratarlas como estructura real haria que el kit se denunciara a
    si mismo por documentarse.
    """
    fuera, en_fence = [], False
    for linea in texto.splitlines():
        if FENCE.match(linea.strip()):
            en_fence = not en_fence
            continue
        if not en_fence:
            fuera.append(linea)
    return fuera


def _tramo(lineas: list[str], desde: str, hasta: tuple[str, ...]) -> list[str]:
    """Lineas entre una cabecera y la siguiente de las de corte."""
    dentro, tramo = False, []
    for linea in lineas:
        if linea.startswith(desde):
            dentro = True
            continue
        if dentro and linea.startswith(hasta):
            break
        if dentro:
            tramo.append(linea)
    return tramo


def _primera_ruta(texto: str) -> str | None:
    """Primer token entre backticks que parezca una ruta de archivo."""
    for token in BACKTICK.findall(texto):
        t = token.strip()
        if t.endswith("/") or re.search(r"\.[a-z]{2,4}$", t) or t.startswith("."):
            return t.rstrip("/")
    return None


def archivos(patron: str, arboles: list[str] | None = None) -> list[Path]:
    """Inventario, saltando `__pycache__`.

    Leccion de M-05: una lista puede venir vacia por error y entonces "no hay
    fallos" es una conclusion que la lista no sostiene. Quien llama comprueba
    que no este vacia (ver `inventario_creible`).
    """
    raices = [RAIZ / a for a in arboles] if arboles else [RAIZ]
    salida: list[Path] = []
    for raiz in raices:
        salida += [p for p in raiz.rglob(patron) if "__pycache__" not in p.parts]
    return sorted(salida)


# ------------------------------------------------------------------- reglas

def inventario_creible() -> list[str]:
    """Sin esto, todas las demas reglas dirian OK sobre un paquete vacio."""
    fallos = []
    for rel in (SKILL, PLANTILLAS_MD, LEEME):
        if not (RAIZ / rel).is_file():
            fallos.append(f"{rel}: no existe (¿RAIZ mal apuntada?); sin el, "
                          f"esta guarda no puede concluir nada")
    if not fallos and not archivos("*.md", ARBOLES_INSTALABLES):
        fallos.append("no se encontro ninguna plantilla instalable en "
                      f"{', '.join(ARBOLES_INSTALABLES)}: el inventario esta vacio, "
                      f"asi que un 'todo OK' no significaria nada")
    return fallos


def promesas_paso_9() -> dict[int, str]:
    """{numero: ruta} de los archivos que el Paso 9 promete generar."""
    lineas = _sin_fences(_leer(SKILL))
    tramo = _tramo(lineas, "### Paso 9", ("### Paso 10", "## "))
    promesas = {}
    for linea in tramo:
        m = ITEM.match(linea)
        if not m:
            continue
        ruta = _primera_ruta(m.group(2))
        if ruta:
            promesas[int(m.group(1))] = ruta
    return promesas


def lista_de_plantillas() -> dict[int, str]:
    """{numero: ruta} de la "Lista de archivos a generar" de plantillas.md."""
    lineas = _sin_fences(_leer(PLANTILLAS_MD))
    tramo = _tramo(lineas, "## Lista de archivos a generar", ("---", "## "))
    lista = {}
    for linea in tramo:
        m = ITEM.match(linea)
        if not m:
            continue
        ruta = _primera_ruta(m.group(2))
        if ruta:
            lista[int(m.group(1))] = ruta
    return lista


def listas_coinciden() -> list[str]:
    """Las dos listas a mano de lo mismo se separan sin que nadie lo note."""
    skill, lista = promesas_paso_9(), lista_de_plantillas()
    if not skill:
        return [f"{SKILL}: el Paso 9 no enumera ningun archivo (¿cambio el formato?)"]
    if not lista:
        return [f"{PLANTILLAS_MD}: 'Lista de archivos a generar' esta vacia"]

    fallos = []
    tope = max(lista)  # a partir de ahi, el Paso 9 promete piezas del paquete
    for n in sorted(set(skill) | set(lista)):
        en_skill, en_lista = skill.get(n), lista.get(n)
        if n > tope:
            continue
        if en_skill is None:
            fallos.append(f"{PLANTILLAS_MD}: lista el archivo {n} (`{en_lista}`) "
                          f"que el Paso 9 de SKILL.md no promete")
        elif en_lista is None:
            fallos.append(f"{SKILL}: el Paso 9 promete el archivo {n} (`{en_skill}`) "
                          f"que plantillas.md no lista")
        elif en_skill != en_lista:
            fallos.append(f"archivo {n}: SKILL.md dice `{en_skill}` y "
                          f"plantillas.md dice `{en_lista}`")
    return fallos


def cada_archivo_tiene_plantilla() -> list[str]:
    """Un archivo prometido sin plantilla es el fallo mas comun del kickstart."""
    lista = lista_de_plantillas()
    # Fuera de fences: dentro de los bloques van las plantillas mismas, y una
    # cabecera de ejemplo no es una plantilla que exista.
    contenido = "\n".join(_sin_fences(_leer(PLANTILLAS_MD)))
    cabeceras = {int(n): ruta for n, ruta in CABECERA_ARCHIVO.findall(contenido)}
    otras_referencias = {
        p: p.read_text(encoding="utf-8")
        for p in archivos("*.md", [REFERENCIAS])
        if p != RAIZ / PLANTILLAS_MD
    }

    fallos = []
    for n, ruta in sorted(lista.items()):
        if n in cabeceras:
            if not cabeceras[n].startswith(ruta):
                fallos.append(f"{PLANTILLAS_MD}: 'ARCHIVO {n}' describe "
                              f"`{cabeceras[n]}` pero la lista dice `{ruta}`")
            continue
        delegado = [p.name for p, texto in otras_referencias.items() if ruta in texto]
        if not delegado:
            fallos.append(f"{PLANTILLAS_MD}: se promete `{ruta}` (archivo {n}) y "
                          f"ninguna plantilla dice como generarlo")
    return fallos


def rutas_del_paquete_existen() -> list[str]:
    """El Paso 9 dice donde viajan las plantillas del protocolo. Si mienten,
    el Claude que lea la skill las dara por perdidas y seguira sin autopilotaje."""
    fallos = []
    for linea in _leer(SKILL).splitlines():
        for crudo in re.findall(r"<paquete>/\S+", linea):
            ruta = crudo[len("<paquete>/"):].rstrip("`,.")
            if "*" in ruta:
                patron = Path(ruta)
                if not [p for p in (RAIZ / patron.parent).glob(patron.name)
                        if "__pycache__" not in p.parts]:
                    fallos.append(f"{SKILL}: declara `<paquete>/{ruta}` y no hay "
                                  f"ningun archivo que encaje")
                continue
            destino = RAIZ / ruta.rstrip("/")
            if ruta.endswith("/") and not destino.is_dir():
                fallos.append(f"{SKILL}: declara el directorio `<paquete>/{ruta}`, "
                              f"que no existe en el paquete")
            elif not ruta.endswith("/") and not destino.exists():
                fallos.append(f"{SKILL}: declara `<paquete>/{ruta}`, "
                              f"que no existe en el paquete")
    return fallos


def enlaces_y_referencias() -> list[str]:
    """Enlaces relativos rotos, `references/*.md` inexistentes, e inventario."""
    fallos = []
    md = archivos("*.md")
    for archivo in md:
        for num, linea in enumerate(_sin_fences(archivo.read_text(encoding="utf-8")), 1):
            rel = archivo.relative_to(RAIZ).as_posix()
            for destino in ENLACE.findall(linea):
                if destino.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                ruta = destino.split("#", 1)[0]
                if not ruta or "{" in ruta:
                    continue
                if (archivo.parent / ruta).exists() or (RAIZ / ruta).exists():
                    continue
                fallos.append(f"{rel}: enlace roto -> {destino}")
            for token in BACKTICK.findall(linea):
                if not token.startswith("references/") or not token.endswith(".md"):
                    continue
                # `references/x.md` se resuelve contra la skill que lo escribe
                # (cada skill tiene las suyas) y, si no, contra las del kickstart:
                # plantillas.md las cita asi desde dentro del propio directorio.
                if ((archivo.parent / token).is_file()
                        or (RAIZ / REFERENCIAS / Path(token).name).is_file()):
                    continue
                fallos.append(f"{rel}: apunta a `{token}`, que no existe")

    # Inventario: una referencia que existe pero que SKILL.md no lista es una
    # referencia que nadie va a leer nunca.
    listadas = set()
    tramo = _tramo(_sin_fences(_leer(SKILL)), SECCION_REFERENCIAS_SKILL, ("## ",))
    for linea in tramo:
        for token in BACKTICK.findall(linea):
            if token.startswith("references/"):
                listadas.add(Path(token).name)
    if not listadas:
        fallos.append(f"{SKILL}: no se pudo leer la lista de '{SECCION_REFERENCIAS_SKILL}'")
    else:
        for p in archivos("*.md", [REFERENCIAS]):
            if p.name not in listadas:
                fallos.append(f"{REFERENCIAS}/{p.name} existe y SKILL.md no lo lista "
                              f"en '{SECCION_REFERENCIAS_SKILL}': nadie lo cargara")
    return fallos


def _numeros(lista: str) -> list[int]:
    return [int(n) for n in re.findall(r"\d+", lista)]


def secciones_citadas_existen() -> list[str]:
    """"ver X.md seccion 4" deja de ser verdad en cuanto alguien renumera X."""
    secciones: dict[str, set[int]] = {}
    for p in archivos("*.md", [REFERENCIAS]):
        secciones[p.name] = {
            int(m.group(1))
            for linea in _sin_fences(p.read_text(encoding="utf-8"))
            if (m := SECCION_NUMERADA.match(linea))
        }

    fallos = []
    for p in archivos("*.md") + archivos("*.py", ARBOLES_INSTALABLES):
        rel = p.relative_to(RAIZ).as_posix()
        texto = p.read_text(encoding="utf-8")
        citas: list[tuple[str, list[int]]] = []
        citas += [(a, [int(n)]) for a, n in CITA_SIMPLE.findall(texto)]
        citas += [(a, _numeros(nums)) for nums, a in CITA_MULTI_DE.findall(texto)]
        citas += [(a, _numeros(nums)) for a, nums in CITA_MULTI_PAREN.findall(texto)]
        for archivo, numeros in citas:
            nombre = Path(archivo).name
            # Solo se auditan las referencias INTERNAS del kit. Las citas a
            # archivos que el kit genera (especificaciones.md, backlog.md...)
            # no se pueden comprobar: no existen hasta que hay proyecto.
            if nombre not in secciones:
                continue
            for n in numeros:
                if n not in secciones[nombre]:
                    fallos.append(f"{rel}: cita `{nombre}` seccion {n}, que no existe "
                                  f"(las que hay: {sorted(secciones[nombre])})")
    return fallos


def placeholders_documentados() -> list[str]:
    """Un placeholder que la tabla no menciona no lo rellena nadie: se instala
    tal cual y el proyecto arranca con `{{...}}` dentro de sus comandos."""
    usados: dict[str, set[str]] = {}
    for patron in ("*.md", "*.py", "*.sh", "*.json", "*.yml"):
        for p in archivos(patron, ARBOLES_INSTALABLES):
            for crudo in PLACEHOLDER.findall(p.read_text(encoding="utf-8")):
                if NOMBRE_PLACEHOLDER.match(crudo.strip()):
                    usados.setdefault(crudo.strip(), set()).add(
                        p.relative_to(RAIZ).as_posix())

    tramo = "\n".join(_tramo(_sin_fences(_leer(LEEME)), SECCION_PLACEHOLDERS, ("## ",)))
    if not tramo.strip():
        return [f"{LEEME}: no se encontro la seccion '{SECCION_PLACEHOLDERS}'"]
    con_llaves = {m.strip() for m in PLACEHOLDER.findall(tramo)
                  if NOMBRE_PLACEHOLDER.match(m.strip())}
    documentados = con_llaves | set(TOKEN_MAYUSCULAS.findall(tramo))

    fallos = []
    for nombre in sorted(usados):
        if nombre not in documentados:
            donde = ", ".join(sorted(usados[nombre])[:3])
            fallos.append(f"{LEEME}: `{{{{{nombre}}}}}` se usa en {donde} y la tabla "
                          f"de placeholders no lo documenta")
    for nombre in sorted(con_llaves - set(usados)):
        fallos.append(f"{LEEME}: la tabla documenta `{{{{{nombre}}}}}` y ninguna "
                      f"plantilla lo usa ya")
    return fallos


def entorno_traducido() -> list[str]:
    """Si la skill nombra herramientas del chat, tiene que decir su equivalencia.

    Sin esa tabla, un Claude Code que ejecute el kickstart improvisa el paso de
    entrega — y la improvisacion en la entrega es donde se pierden archivos. El
    fallo no se ve: sale un kit, solo que incompleto.
    """
    texto = _leer(SKILL)
    usadas = [h for h in HERRAMIENTAS_DE_CHAT if h in texto]
    if not usadas:
        return []
    if SECCION_ENTORNO not in texto:
        return [f"{SKILL}: nombra herramientas que solo existen en claude.ai "
                f"({', '.join(usadas)}) y no tiene la seccion '{SECCION_ENTORNO}' "
                f"que dice como traducirlas en Claude Code."]
    tramo = "\n".join(_tramo(_sin_fences(texto), SECCION_ENTORNO, ("## Flujo",)))
    faltan = [h for h in usadas if h not in tramo]
    return [f"{SKILL}: usa `{h}` pero la seccion '{SECCION_ENTORNO}' no dice su "
            f"equivalente en Claude Code." for h in faltan]


def ejecutabilidad_documentada() -> list[str]:
    """Lo generado tiene que poder ejecutarlo quien lo va a leer.

    Dos piezas, y las dos se borran sin que nada chille si esto no existe:

    - La fila del DISENO en la tabla de entorno. No es una herramienta que la
      skill nombre —por eso `entorno_traducido` no la ve— sino una capacidad que
      sus pasos suponen: el Paso 0 pide mockups, y en el chat esos se ven. En
      Claude Code no. Faltando la fila, el kickstart traduce "abre el prototipo"
      palabra por palabra a la guia y el proyecto nace con ordenes imposibles.
    - La regla que lo generaliza en las "Inviolables". La fila resuelve el caso
      del diseno; la regla resuelve la clase, que es todo lo que venga en el
      material de entrada escrito para un humano con pantalla.

    Pasó de verdad: ~16 subfases con "ABRE el prototipo", y el desempaquetador
    que hizo falta para leerlo se cerro con la sesion.
    """
    texto = _leer(SKILL)
    fallos = []

    # Si la seccion de entorno no existe, el que habla es `entorno_traducido`:
    # decir aqui "te falta una fila" de una tabla que no esta seria ruido, y el
    # ruido es lo que ensena a saltarse la guarda entera (M-10).
    entorno = "\n".join(_tramo(_sin_fences(texto), SECCION_ENTORNO, ("## Flujo",)))
    if entorno.strip() and SENA_DISENO not in entorno:
        fallos.append(
            f"{SKILL}: la seccion '{SECCION_ENTORNO}' no dice que en Claude Code no "
            f"hay {SENA_DISENO} (falta la fila de mirar un diseno). Sin eso, un "
            f"prototipo de la entrada se copia a la guia como 'abrelo y miralo', "
            f"que es una orden que nadie puede cumplir.")

    calidad = "\n".join(_tramo(_sin_fences(texto), SECCION_CALIDAD, ("## ",)))
    if not calidad.strip():
        fallos.append(f"{SKILL}: no se encontro la seccion '{SECCION_CALIDAD}'")
    elif SENA_EJECUTABLE not in calidad:
        fallos.append(
            f"{SKILL}: '{SECCION_CALIDAD}' no exige que lo generado sea "
            f"{SENA_EJECUTABLE}. Es la regla que impide copiar literal lo que trae "
            f"el usuario; sin ella la fila del diseno solo cubre el diseno.")
    return fallos


REGLAS = [
    ("inventario", inventario_creible),
    ("entorno traducido", entorno_traducido),
    ("ejecutabilidad de lo generado", ejecutabilidad_documentada),
    ("listas de archivos", listas_coinciden),
    ("plantilla por archivo", cada_archivo_tiene_plantilla),
    ("rutas del paquete", rutas_del_paquete_existen),
    ("enlaces y referencias", enlaces_y_referencias),
    ("secciones citadas", secciones_citadas_existen),
    ("placeholders", placeholders_documentados),
]


def revisar() -> list[str]:
    fallos = inventario_creible()
    if fallos:  # sin paquete legible, el resto solo produciria ruido
        return fallos
    for _nombre, regla in REGLAS[1:]:
        fallos += regla()
    return fallos


def main() -> int:
    fallos = revisar()
    for fallo in fallos:
        print(f"FALLO {fallo}")
    if fallos:
        print(f"\n{len(fallos)} incoherencia(s) en el paquete project-kickstart.")
        return 1
    print("Paquete project-kickstart coherente: promesas, plantillas, enlaces, "
          "secciones y placeholders OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
