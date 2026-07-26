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

Uso:
    python3 scripts/tablero.py --comprobar          # diagnostico (exit 1 si falla)
    python3 scripts/tablero.py --ids                # JSON con los IDs resueltos
    python3 scripts/tablero.py --mover <ITEM_ID> "En progreso"
Tests:
    python3 scripts/test_tablero.py
"""

from __future__ import annotations

import json
import subprocess
import sys

# --- Configuracion del proyecto (lo unico que hay que rellenar) -------------
OWNER = "{{OWNER}}"
PROJECT_NUMBER = "{{PROJECT_NUMBER}}"

# Nombre del campo de estado y de las columnas, tal y como se ven en el tablero.
# Si renombras una columna en GitHub, cambiala aqui: el script te dira cual no
# encuentra y con que nombres cuenta el Project.
CAMPO_ESTADO = "Status"
ESTADOS = ["Disponible", "Bloqueada", "En progreso", "Review", "Terminado"]

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
    r = subprocess.run(cmd, capture_output=True, text=True)
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


def main(argv: list[str]) -> int:
    try:
        if argv and argv[0] == "--mover":
            if len(argv) < 3:
                print('Uso: tablero.py --mover <ITEM_ID> "En progreso"')
                return 2
            mover(argv[1], argv[2])
            print(f"OK  tarjeta {argv[1]} en '{argv[2]}' (releido del tablero)")
            return 0

        datos = resolver()
    except ErrorDeConfiguracion as e:
        print(f"FALLO {e}")
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
