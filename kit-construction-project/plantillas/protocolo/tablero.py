#!/usr/bin/env python3
"""Resuelve en EJECUCION los IDs del GitHub Project que necesita /que-toca.

Antes estaban pegados a mano en la skill (projectId, fieldId de Status y un id
por cada opcion del tablero: 7 valores GraphQL). Eso tenia dos problemas:

1. Nada comprobaba que siguieran vivos. Si el Project se recreaba, los IDs
   cambiaban y `/que-toca` fallaba A MEDIAS: asignaba el issue (paso 4 usa `gh
   issue edit`, que no necesita IDs) y luego no movia la tarjeta. Un candado a
   medias es peor que ninguno: el equipo cree que el tablero dice la verdad.
2. Eran 7 placeholders que alguien tenia que descubrir y pegar sin equivocarse,
   en el momento de menos contexto del proyecto.

Un ID que se descubre no se puede quedar obsoleto. El coste es una llamada a la
API por invocacion.

La mutacion que mueve una tarjeta tambien vive aqui, y no en la skill. Ambas
cosas eliminan una trampa que el kit tenia documentada como leccion pagada:
`gh api graphql` con literales entre comillas se rompia al lanzarlo desde
PowerShell. Aqui la query viaja en una lista argv (sin shell de por medio) y los
valores van como VARIABLES de GraphQL, nunca incrustados en el texto. Sin
literales no hay comillas que perder, y deja de importar desde que shell se
lance.

Y despues de mover, RELEE el estado de la tarjeta: que la mutacion devuelva 200
dice que la API acepto la peticion, no que la tarjeta este donde quieres. Es la
regla de /verificar aplicada al propio protocolo.

Y GENERA el tablero en Markdown desde el Project (--generar). El estado vivia
duplicado a mano en el Project y en `progreso/tablero-equipo.md`; en dos dias de
uso real eso derivo tres veces, y una de ellas hubo que ir al `git log` para
dirimir cual de las tres fuentes decia la verdad. Lo que nadie teclea no puede
desviarse. El LOG de reclamos, en cambio, no se genera jamas: la tabla es un
hecho mecanico, el log es causalidad (por que una tarea se atasco, que trampa
costo un intento fallido) y ninguna automatizacion escribiria eso.

Desde 2026-07-28 el log vive en `progreso/log/`, UNA ENTRADA POR FICHERO, y la
tabla NO se comitea (.gitignore). Antes compartian archivo y ese archivo lo
tocaba toda rama, asi que conflictaba en cada PR: el 2026-07-28, con 3 PRs
abiertos, los 3 chocaban ahi. Ficheros separados hacen el conflicto imposible en
vez de gestionarlo. `--generar` ensambla tabla + log para leerlo de un tirón.

Uso:
    python3 scripts/tablero.py --comprobar          # diagnostico (exit 1 si falla)
    python3 scripts/tablero.py --ids                # JSON con los IDs resueltos
    python3 scripts/tablero.py --mover <ITEM_ID> "En progreso"
    python3 scripts/tablero.py --generar [ruta]     # reescribe la tabla del tablero
Tests:
    python3 scripts/test_tablero.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

# --- Configuracion del proyecto (lo unico que hay que rellenar) -------------
OWNER = "{{OWNER}}"
PROJECT_NUMBER = "{{PROJECT_NUMBER}}"

# Nombre del campo de estado y de las columnas, tal y como se ven en el tablero.
# Si renombras una columna en GitHub, cambiala aqui: el script te dira cual no
# encuentra y con que nombres cuenta el Project.
CAMPO_ESTADO = "Status"
ESTADOS = ["Disponible", "Bloqueada", "En progreso", "Review", "Terminado"]

# Como se marca a que modulo pertenece cada tarea: label `modulo:A`, `modulo:B`...
# Una tarea puede llevar varias (un hito de integracion toca dos modulos) y
# entonces sale en las dos filas.
PREFIJO_MODULO = "modulo:"
SIN_MODULO = "(sin módulo)"

# Semantica de las columnas para resumir el estado de un modulo. Si renombras
# una columna, cambiala en ESTADOS y aqui: el script comprueba que cuadren.
EN_CURSO = ("En progreso", "Review")
TERMINADO = "Terminado"
BLOQUEADA = "Bloqueada"
DISPONIBLE = "Disponible"

# Tope del listado de items. `gh` devuelve tambien `totalCount`, asi que se
# puede saber si vino recortado en vez de suponerlo (leccion pagada: una lista
# truncada parece completa y las conclusiones que se sacan de ella son falsas).
LIMITE_ITEMS = 500

RUTA_TABLERO = "progreso/tablero-equipo.md"
MARCA_INICIO = "<!-- TABLERO GENERADO por scripts/tablero.py --generar · NO EDITAR A MANO -->"
MARCA_FIN = "<!-- FIN DEL TABLERO GENERADO · lo de abajo es tuyo -->"

# El log YA NO vive dentro del tablero: cada entrada es un fichero suelto aqui.
#
# El motivo no es orden, es aritmetica de merges. Antes la tabla y el log
# compartian archivo, y ese archivo lo tocaba TODA rama: la tabla porque cada
# quien la regeneraba en un momento distinto, y el log porque todos añadian al
# final. El comentario del esqueleto llegó a afirmar que añadir al final "evita
# conflictos de merge" — es exactamente al reves, y es el caso de conflicto mas
# clasico que hay. El 2026-07-28, con 3 PRs abiertos, los 3 conflictaban aqui.
#
# Un fichero por entrada lo hace IMPOSIBLE: dos ramas que escriben entradas
# distintas crean ficheros distintos y git las une sin preguntar. Y la tabla
# deja de comitearse (va en .gitignore): es un espejo del Project y se regenera
# con un comando, asi que no hay nada que conciliar.
RUTA_LOG = "progreso/log"

# Mismo remedio, mismo motivo, otras tres secciones. `estado-actual.md` llevaba
# dentro las decisiones vivas, las deudas y los issues, y las tres cambiaban en
# CADA PR: era el segundo fichero que hacia conflictar todas las ramas (el
# primero fue el tablero). Ahora cada item es su propio fichero y aqui se
# ensamblan solo para leerlos de un tiron.
CARPETAS_ENSAMBLADAS = (
    ("decisiones", "Decisiones técnicas vivas", "Léelas antes de codificar."),
    ("pendientes", "Pendientes: deudas, trampas e issues con contexto", ""),
)

CONSULTA = """
query($owner: String!, $number: Int!) {
  %(ambito)s(login: $owner) {
    projectV2(number: $number) {
      id
      title
      field(name: "%(campo)s") {
        ... on ProjectV2SingleSelectField {
          id
          options { id name }
        }
      }
    }
  }
}
"""


class ErrorDeConfiguracion(Exception):
    """Algo que el equipo tiene que arreglar antes de reclamar nada."""


def _graphql(ambito: str) -> dict | None:
    """Consulta el Project como usuario u organizacion. None si no existe ahi."""
    consulta = CONSULTA % {"ambito": ambito, "campo": CAMPO_ESTADO}
    r = subprocess.run(
        ["gh", "api", "graphql",
         "-f", f"query={consulta}",
         "-f", f"owner={OWNER}",
         "-F", f"number={PROJECT_NUMBER}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        # Un owner de tipo usuario consultado como organizacion da NOT_FOUND:
        # es esperado y se resuelve probando el otro ambito.
        return None
    try:
        datos = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    return (datos.get("data") or {}).get(ambito)


def resolver() -> dict:
    if "{{" in OWNER or "{{" in PROJECT_NUMBER:
        raise ErrorDeConfiguracion(
            "OWNER y PROJECT_NUMBER siguen sin rellenar en scripts/tablero.py.\n"
            "   Son los dos unicos datos del Project que hay que poner a mano:\n"
            "     OWNER          = dueño del repo/Project (p.ej. 'MiEquipo')\n"
            "     PROJECT_NUMBER = numero del Project (lo ves en su URL)\n"
            "   Descubrelos con: gh project list --owner <tu-usuario-u-org>"
        )

    duenyo = None
    for ambito in ("user", "organization"):
        duenyo = _graphql(ambito)
        if duenyo:
            break
    if not duenyo:
        raise ErrorDeConfiguracion(
            f"No se encuentra el Project numero {PROJECT_NUMBER} de '{OWNER}'\n"
            f"   (se ha buscado como usuario y como organizacion).\n"
            f"   Comprueba el numero con: gh project list --owner {OWNER}\n"
            f"   Y que el token tenga alcance de Projects: gh auth refresh -s project"
        )

    proyecto = duenyo.get("projectV2")
    if not proyecto:
        raise ErrorDeConfiguracion(
            f"'{OWNER}' existe pero no tiene un Project numero {PROJECT_NUMBER}.\n"
            f"   Listalos con: gh project list --owner {OWNER}"
        )

    campo = proyecto.get("field")
    if not campo:
        raise ErrorDeConfiguracion(
            f"El Project '{proyecto.get('title', PROJECT_NUMBER)}' no tiene un campo "
            f"de seleccion llamado '{CAMPO_ESTADO}'.\n"
            f"   Si lo renombraste, actualiza CAMPO_ESTADO en scripts/tablero.py."
        )

    opciones = {o["name"]: o["id"] for o in campo.get("options", [])}
    faltan = [e for e in ESTADOS if e not in opciones]
    if faltan:
        raise ErrorDeConfiguracion(
            f"Al campo '{CAMPO_ESTADO}' le faltan columnas: {', '.join(faltan)}.\n"
            f"   El Project tiene: {', '.join(opciones) or '(ninguna)'}\n"
            f"   Crea esas columnas en el tablero o ajusta ESTADOS en "
            f"scripts/tablero.py para que coincidan con los nombres reales."
        )

    return {
        "projectId": proyecto["id"],
        "titulo": proyecto.get("title", ""),
        "statusFieldId": campo["id"],
        "opciones": {e: opciones[e] for e in ESTADOS},
    }


MUTACION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId, itemId: $itemId, fieldId: $fieldId,
    value: { singleSelectOptionId: $optionId }
  }) { projectV2Item { id } }
}
"""

LECTURA = """
query($itemId: ID!) {
  node(id: $itemId) {
    ... on ProjectV2Item {
      fieldValueByName(name: "%(campo)s") {
        ... on ProjectV2ItemFieldSingleSelectValue { name }
      }
    }
  }
}
"""


def _gh_graphql(consulta: str, variables: dict) -> dict | None:
    """Ejecuta una operacion pasando los valores como VARIABLES, nunca
    incrustados en el texto de la query."""
    cmd = ["gh", "api", "graphql", "-f", f"query={consulta}"]
    for clave, valor in variables.items():
        cmd += ["-f", f"{clave}={valor}"]
    # encoding explicito: sin el, Windows decodifica en cp1252 y
    # cualquier caracter fuera de esa tabla (el ⏸️ de T-016) revienta el script.
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def estado_actual(item_id: str) -> str | None:
    datos = _gh_graphql(LECTURA % {"campo": CAMPO_ESTADO}, {"itemId": item_id})
    if not datos:
        return None
    nodo = (datos.get("data") or {}).get("node") or {}
    return (nodo.get("fieldValueByName") or {}).get("name")


def mover(item_id: str, estado: str) -> None:
    """Mueve la tarjeta y COMPRUEBA el efecto. Lanza si no quedo donde debia."""
    ids = resolver()
    if estado not in ids["opciones"]:
        raise ErrorDeConfiguracion(
            f"'{estado}' no es una columna del tablero.\n"
            f"   Columnas validas: {', '.join(ids['opciones'])}"
        )
    respuesta = _gh_graphql(MUTACION, {
        "projectId": ids["projectId"],
        "itemId": item_id,
        "fieldId": ids["statusFieldId"],
        "optionId": ids["opciones"][estado],
    })
    if respuesta is None or "errors" in respuesta:
        raise ErrorDeConfiguracion(
            f"La API rechazo mover el item {item_id} a '{estado}'.\n"
            f"   Comprueba que el ITEM_ID es el del Project (campo 'id' de\n"
            f"   `gh project item-list`), no el numero del issue."
        )
    # Que la API responda OK no es que la tarjeta este donde quieres.
    quedo = estado_actual(item_id)
    if quedo != estado:
        raise ErrorDeConfiguracion(
            f"La mutacion se acepto pero la tarjeta quedo en '{quedo or 'desconocido'}', "
            f"no en '{estado}'.\n"
            f"   NO des la tarea por reclamada: el tablero no dice lo que crees."
        )


# --- Generacion del tablero en Markdown -------------------------------------

def _items() -> list[dict]:
    """Los items del Project. PARA si el listado vino recortado.

    Escribir un tablero a partir de media lista es peor que no tenerlo: las
    tareas que faltan no se ven como "faltan", se leen como "no existen".
    """
    r = subprocess.run(
        ["gh", "project", "item-list", str(PROJECT_NUMBER), "--owner", OWNER,
         "--format", "json", "--limit", str(LIMITE_ITEMS)],
        # encoding explicito: ver _gh_graphql.
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        raise ErrorDeConfiguracion(
            f"No se pudo listar el Project {PROJECT_NUMBER} de '{OWNER}':\n"
            f"   {(r.stderr or '').strip()}\n"
            f"   Comprueba el alcance del token: gh auth refresh -s project"
        )
    try:
        datos = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise ErrorDeConfiguracion(
            "`gh project item-list` no devolvio JSON valido; no se escribe nada."
        ) from None

    items = datos.get("items") or []
    total = datos.get("totalCount")
    if isinstance(total, int) and total > len(items):
        raise ErrorDeConfiguracion(
            f"El Project tiene {total} items y el listado trajo {len(items)}: "
            f"vino RECORTADO.\n"
            f"   Sube LIMITE_ITEMS en scripts/tablero.py (ahora {LIMITE_ITEMS}) y "
            f"vuelve a generar.\n"
            f"   No se escribe un tablero a medias: las tareas que faltan no "
            f"parecen ausentes, parecen inexistentes."
        )
    if len(items) >= LIMITE_ITEMS:
        raise ErrorDeConfiguracion(
            f"El listado trajo justo el tope ({LIMITE_ITEMS} items): asume que hay "
            f"mas.\n   Sube LIMITE_ITEMS en scripts/tablero.py y vuelve a generar."
        )
    return items


def _comprobar_semantica() -> None:
    """Las columnas con significado tienen que existir de verdad."""
    declaradas = set(ESTADOS)
    faltan = [e for e in (*EN_CURSO, TERMINADO, BLOQUEADA, DISPONIBLE)
              if e not in declaradas]
    if faltan:
        raise ErrorDeConfiguracion(
            f"scripts/tablero.py: {', '.join(sorted(set(faltan)))} no esta(n) en "
            f"ESTADOS ({', '.join(ESTADOS)}).\n"
            f"   Si renombraste columnas, ajusta ESTADOS Y las constantes de "
            f"semantica (EN_CURSO, TERMINADO, BLOQUEADA, DISPONIBLE)."
        )


def _modulos_de(item: dict) -> list[str]:
    etiquetas = item.get("labels") or []
    modulos = sorted(e[len(PREFIJO_MODULO):] for e in etiquetas
                     if e.startswith(PREFIJO_MODULO))
    return modulos or [SIN_MODULO]


def _titulo_de(item: dict) -> str:
    contenido = item.get("content") or {}
    titulo = contenido.get("title") or item.get("title") or "(sin título)"
    numero = contenido.get("number")
    return f"{titulo} (#{numero})" if numero else titulo


def _estado_del_modulo(estados: list[str]) -> str:
    """Resumen de un modulo a partir de sus tareas. La regla se imprime en el
    propio tablero: un estado derivado que no dice como se deriva es otra cosa
    que hay que creerse."""
    if not estados:
        return "Sin tareas"
    if any(e in EN_CURSO for e in estados):
        return "En progreso"
    if all(e == TERMINADO for e in estados):
        return "Terminado"
    if not any(e == DISPONIBLE for e in estados) and any(e == BLOQUEADA for e in estados):
        return "Bloqueado"
    return "Disponible"


def tablas(items: list[dict], titulo_proyecto: str, hoy: str) -> str:
    """El bloque generado, entero y determinista (mismo Project -> mismo texto)."""
    _comprobar_semantica()

    por_modulo: dict[str, list[dict]] = {}
    for item in items:
        for modulo in _modulos_de(item):
            por_modulo.setdefault(modulo, []).append(item)

    filas_mod = []
    for modulo in sorted(por_modulo, key=lambda m: (m == SIN_MODULO, m)):
        suyas = por_modulo[modulo]
        estados = [i.get("status") or "(sin estado)" for i in suyas]
        abiertas = [i for i, e in zip(suyas, estados) if e != TERMINADO]
        devs = sorted({a for i in abiertas for a in (i.get("assignees") or [])})
        filas_mod.append(
            f"| {modulo} | {_estado_del_modulo(estados)} | {', '.join(devs) or '—'} "
            f"| {len(abiertas)} / {len(suyas)} |"
        )

    abiertos = [i for i in items if (i.get("status") or "") != TERMINADO]
    filas_tar = []
    for item in sorted(abiertos, key=_titulo_de):
        devs = ", ".join(item.get("assignees") or []) or "—"
        filas_tar.append(
            f"| {_titulo_de(item)} | {', '.join(_modulos_de(item))} | {devs} "
            f"| {item.get('status') or '(sin estado)'} |"
        )

    cerradas = len(items) - len(abiertos)
    return "\n".join([
        MARCA_INICIO,
        "",
        f"**Project:** {titulo_proyecto} · **Generado:** {hoy} · "
        f"**Tareas:** {len(abiertos)} abiertas de {len(items)}",
        "",
        "El estado real vive en el Project; esto es su espejo, y se reescribe entero",
        "cada vez. Si algo aquí no cuadra, se arregla **en el Project** y se vuelve a",
        "generar: editar esta tabla a mano solo dura hasta la siguiente generación.",
        "",
        "## Módulos",
        "",
        "| Módulo | Estado | Devs con tarea abierta | Abiertas / total |",
        "|---|---|---|---|",
        *(filas_mod or ["| — | Sin tareas | — | 0 / 0 |"]),
        "",
        f"Estado del módulo, derivado de sus tareas: **En progreso** si alguna está en "
        f"{' o '.join(EN_CURSO)}; **Terminado** si todas lo están; **Bloqueado** si no "
        f"queda ninguna {DISPONIBLE} y hay alguna {BLOQUEADA}; si no, **{DISPONIBLE}**.",
        "",
        "## Tareas abiertas",
        "",
        "| Tarea | Módulo | Dev | Estado |",
        "|---|---|---|---|",
        *(filas_tar or ["| — | — | — | (ninguna abierta) |"]),
        "",
        f"{cerradas} tarea(s) en {TERMINADO} no se listan aquí (están en el Project): "
        f"arriba solo lo que sigue vivo.",
        "",
        MARCA_FIN,
    ]) + "\n"


ESQUELETO = """# Tablero del Equipo

> ⚠️ **Este archivo NO se comitea** (está en `.gitignore`) y se reescribe entero
> cada vez que corres `python3 scripts/tablero.py --generar`. No edites aquí:
> el estado se arregla en el Project; el log, las decisiones y los pendientes,
> en sus carpetas de `progreso/` (un fichero por entrada).

{bloque}
{ensambladas}
## Log de reclamos

Ensamblado desde `progreso/log/` (un fichero por entrada, ordenados por nombre).
La tabla de arriba es un hecho mecánico; esto es lo otro: por qué una tarea se
atascó, qué trampa costó un intento fallido, qué acuerdo se tomó al repartir un
módulo. Ninguna automatización escribiría estas líneas.

**Para añadir una entrada, crea un fichero nuevo** — no toques los existentes:

    progreso/log/AAAA-MM-DD-de-que-va.md

{log}
"""


def _carpeta_log(destino: Path | None = None) -> Path:
    """El log vive JUNTO al tablero, no respecto al directorio actual.

    Atarlo al CWD hacia que generar en otra ruta (un tmpdir de los tests, por
    ejemplo) ensamblara el log del repo real: el archivo escrito parecia bueno
    y hablaba de otra cosa.
    """
    if destino is None:
        return Path(RUTA_LOG)
    return destino.parent / Path(RUTA_LOG).name


def _entradas_del_log(destino: Path | None = None) -> list[Path]:
    """Ficheros del log, ordenados por nombre (o sea, por fecha)."""
    carpeta = _carpeta_log(destino)
    if not carpeta.is_dir():
        return []
    return sorted(p for p in carpeta.glob("*.md") if p.is_file())


def _log_ensamblado(destino: Path | None = None) -> str:
    """El log entero como viñetas, para LEERLO de un tirón.

    Se ensambla al generar en vez de vivir comiteado: asi cada entrada es un
    fichero que nadie mas toca (imposible que conflicte) y aun asi se lee
    seguido, que es como lo necesita quien llega nuevo o quien retoma.
    """
    piezas = []
    for fichero in _entradas_del_log(destino):
        lineas = fichero.read_text(encoding="utf-8").rstrip().splitlines()
        if not lineas:
            continue
        piezas.append("\n".join([f"- {lineas[0]}", *lineas[1:]]))
    return "\n".join(piezas) + "\n" if piezas else "_(todavía sin entradas)_\n"


def _seccion_ensamblada(destino: Path, carpeta: str, titulo: str, nota: str) -> str:
    """Una carpeta de items sueltos, pintada como seccion de vinetas."""
    base = destino.parent / carpeta
    ficheros = sorted(p for p in base.glob("*.md")) if base.is_dir() else []
    piezas = []
    for fichero in ficheros:
        lineas = fichero.read_text(encoding="utf-8").rstrip().splitlines()
        if lineas:
            piezas.append("\n".join([f"- {lineas[0]}", *lineas[1:]]))
    cuerpo = "\n".join(piezas) if piezas else "_(sin entradas)_"
    cabecera = f"## {titulo}\n\n"
    if nota:
        cabecera += f"{nota}\n\n"
    return f"{cabecera}{cuerpo}\n"


def _ensambladas(destino: Path) -> str:
    return "\n".join(
        _seccion_ensamblada(destino, c, t, n) for c, t, n in CARPETAS_ENSAMBLADAS
    )


def _avisar_si_log_sin_migrar(destino: Path) -> None:
    """Un tablero viejo trae el log DENTRO. Regenerar sin mas lo borraria."""
    if not destino.exists() or _entradas_del_log(destino):
        return
    contenido = destino.read_text(encoding="utf-8")
    if "## Log de reclamos" not in contenido:
        return
    cuerpo = contenido.split("## Log de reclamos", 1)[1]
    if not re.search(r"^- \d{4}-\d{2}-\d{2} ", cuerpo, re.MULTILINE):
        return
    raise ErrorDeConfiguracion(
        f"{destino} todavia lleva el log DENTRO y {_carpeta_log(destino)}/ esta vacio.\n"
        f"   Regenerar ahora se llevaria por delante esas entradas, que nadie\n"
        f"   puede reescribir: son el porque de lo que paso.\n"
        f"   Migralas primero a {_carpeta_log(destino)}/AAAA-MM-DD-de-que-va.md (una por\n"
        f"   fichero) y vuelve a intentarlo."
    )


def generar(ruta: str | None = None, hoy: str | None = None) -> str:
    """Reescribe el tablero ENTERO (tabla + log ensamblado). Devuelve la ruta.

    Ya no se conserva nada del archivo anterior: no se comitea y no tiene
    partes escritas a mano. Lo unico irrecuperable es el log, y ese vive
    ahora en ficheros aparte.
    """
    destino = Path(ruta or RUTA_TABLERO)
    hoy = hoy or date.today().isoformat()
    _avisar_si_log_sin_migrar(destino)

    ids = resolver()  # valida configuracion y da el titulo del Project
    bloque = tablas(_items(), ids["titulo"] or f"{OWNER}/{PROJECT_NUMBER}", hoy)

    destino.parent.mkdir(parents=True, exist_ok=True)
    nuevo = ESQUELETO.format(
        bloque=bloque,
        log=_log_ensamblado(destino),
        ensambladas=_ensambladas(destino),
    )
    destino.write_text(nuevo, encoding="utf-8", newline="\n")

    # Que write_text no lance no es que el archivo diga lo que crees.
    escrito = destino.read_text(encoding="utf-8")
    if MARCA_INICIO not in escrito or bloque.strip() not in escrito:
        raise ErrorDeConfiguracion(
            f"Se escribio {destino} pero al releerlo no contiene el bloque generado.\n"
            f"   NO des el tablero por actualizado."
        )
    return str(destino)


def main(argv: list[str]) -> int:
    try:
        if argv and argv[0] == "--mover":
            if len(argv) < 3:
                print('Uso: tablero.py --mover <ITEM_ID> "En progreso"')
                return 2
            mover(argv[1], argv[2])
            print(f"OK  tarjeta {argv[1]} en '{argv[2]}' (releido del tablero)")
            return 0

        if argv and argv[0] == "--generar":
            escrito = generar(argv[1] if len(argv) > 1 else None)
            entradas = len(_entradas_del_log(Path(escrito)))
            print(f"OK  {escrito} regenerado desde el Project "
                  f"(+ {entradas} entrada(s) de {RUTA_LOG}/)")
            print("    Recuerda: este archivo NO se comitea; se genera cuando lo necesites.")
            return 0

        datos = resolver()
    except ErrorDeConfiguracion as e:
        print(f"FALLO {e}")
        if argv and argv[0] == "--generar":
            print("\nEl tablero NO se ha actualizado. No lo cites como estado del")
            print("equipo hasta regenerarlo: lo que hay en el archivo es de antes.")
        else:
            print("\nNO des por hecho el reclamo: si el tablero no se puede tocar, /que-toca")
            print("puede asignarte el issue y NO mover la tarjeta, y el tablero mentiria.")
        return 1

    if "--comprobar" in argv:
        print(f"OK  Project '{datos['titulo']}' resuelto; columnas: "
              f"{', '.join(datos['opciones'])}")
        return 0
    print(json.dumps(datos, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
