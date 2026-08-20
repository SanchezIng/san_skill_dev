#!/usr/bin/env python3
"""Hook PreToolUse: `secure-coding-guard` obligatoria ANTES de tocar codigo.

Sustituye a `recordar-seguridad.sh`, que avisaba en cada edicion y nunca
bloqueaba. Nacio y se midio en un proyecto real (portal-web-api-sunat, T-204):
la obligacion vivia solo en el paso 6.4 de `/que-toca`, o sea en el flujo
"reclamo una tarea nueva". Toda otra puerta a la sesion —mergear, resolver
conflictos, revisar un PR, un hotfix, retomar tras una pausa— la saltaba en
silencio: hubo una sesion que mergeo ~2160 lineas de codigo de auth sin
invocarla una sola vez. El modo de fallo no fue descuido sino de encuadre: la
sesion arranco como tarea de git y nadie reevaluo el disparador cuando el
trabajo cambio de forma. Por eso el recordatorio no puede vivir en la memoria
de nadie: lo dispara la herramienta.

Comportamiento:
  - Fichero que no es codigo             -> callado (no molesta al escribir docs)
  - La skill no esta instalada           -> callado (no hay nada que invocar)
  - Codigo + la skill YA se invoco       -> callado (una vez por sesion, no mas)
  - Codigo + sin rastro de la skill      -> BLOQUEA la edicion y explica que hacer
  - No se puede leer el transcript       -> bloquea la primera vez y avisa despues
                                            (visible, nunca un pase silencioso)

Dos decisiones que parecen detalles y son el mecanismo entero:

1. **Se busca la ESTRUCTURA de la invocacion, no el nombre de la skill.** El
   aviso que emite esta guarda queda escrito en el transcript, y la
   documentacion del proyecto nombra la skill en su seccion de obligaciones:
   un patron laxo leeria su propio texto —o el CLAUDE.md que se lee al
   arrancar— como prueba de que la skill corrio, y se daria por satisfecho
   solo. Falso negativo perfecto y silencioso, justo lo que esta guarda existe
   para matar.

2. **Nunca devuelve `permissionDecision: "allow"`.** Eso auto-aprobaria
   ediciones que el usuario habria querido revisar. Solo sabe callarse o
   bloquear.

Y una tercera, heredada del hook que sustituye: si no puede comprobar si la
skill se invoco, **bloquea** en vez de dejar pasar. No poder preguntar no es que
la respuesta sea "si".

Tests: python3 .claude/hooks/test_secure_guard.py

Uso (para probarlo a mano):
    echo '{"tool_name":"Edit","tool_input":{"file_path":"src/x.ts"},
           "transcript_path":"...","session_id":"test"}' | python3 secure_guard.py
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Extensiones que cuentan como codigo. Los .md quedan fuera a proposito: en un
# proyecto con documentacion viva, una guarda que salta ahi se vuelve ruido de
# fondo, que es como mueren estos recordatorios. Config incluida (yml/json)
# porque el CI y las allowlists son superficie de seguridad.
EXT_CODIGO = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".py", ".rb", ".php", ".go", ".rs", ".java", ".kt", ".swift", ".cs",
    ".c", ".h", ".cpp", ".hpp", ".sh", ".bash", ".ps1",
    ".sql", ".prisma", ".graphql", ".yml", ".yaml", ".json", ".toml",
}

# Generados por herramientas: nadie los escribe a mano y su diff es enorme.
EXCLUIDOS = {
    "pnpm-lock.yaml", "package-lock.json", "yarn.lock", "bun.lockb",
    "poetry.lock", "Cargo.lock", "composer.lock", "Gemfile.lock", "go.sum",
}

# Evidencia de que la skill se invoco DE VERDAD en esta sesion. Ver la decision 1
# de la cabecera: se exige la estructura del acto, no su nombre.
#
# La lectura directa exige ademas el "file_path" delante. Sin el valia como
# prueba cualquier MENCION de la ruta del SKILL.md — y la documentacion del
# proyecto la nombra en su seccion de skill obligatoria: bastaba con leer ese
# fichero, cosa que se hace al arrancar, para que la guarda se diera por
# satisfecha el resto de la sesion.
RE_EVIDENCIA = re.compile(
    r'"skill"\s*:\s*"secure-coding-guard"'  # invocacion via herramienta Skill
    r'|"file_path"\s*:\s*"[^"]*secure-coding-guard[\\/]+SKILL\.md"'  # lectura directa
    r"|command-name>[^<]*secure-coding-guard"  # invocada por el dev como /slash
)

# Tope de lectura del transcript: una sesion larga son megas de JSONL y el hook
# corre antes de CADA edicion. Se corta al primer acierto, asi que el tope solo
# muerde en el caso "no hay evidencia", que ya es el caso lento.
MAX_BYTES = 20 * 1024 * 1024

AVISO = """[secure-coding-guard] BLOQUEADO: la skill de seguridad del proyecto es
obligatoria ANTES de crear, modificar o revisar codigo, y en esta sesion no hay
rastro de que se haya invocado.

Que hacer:
  1. Invoca la skill del proyecto llamada  secure-coding-guard  (herramienta Skill).
  2. Aplicala a lo que ibas a escribir: input validado, nada de secretos en
     codigo ni en logs, autorizacion comprobada, queries parametrizadas.
  3. Repite esta edicion. La guarda se queda callada el resto de la sesion.

No la improvises: sus references/ (owasp, estandares-tecnicos, checklist-revision)
existen para no depender de que se te ocurra mirar lo correcto. Fichero: {ruta}"""

AVISO_SIN_VERIFICAR = """[secure-coding-guard] BLOQUEADO: la guarda no ha podido
verificar si la skill de seguridad se invoco en esta sesion ({motivo}).

No poder comprobarlo NO es lo mismo que estar en regla, asi que bloquea una vez
en vez de dejar pasar. Invoca la skill del proyecto  secure-coding-guard  y
repite la edicion: el segundo intento no se bloquea. Fichero: {ruta}"""

AVISO_DEGRADADO = (
    "[secure-coding-guard] La guarda corre DEGRADADA: no puede leer el transcript "
    "de la sesion, asi que no verifica nada y deja pasar las ediciones. Revisa a "
    "mano que la skill de seguridad se haya aplicado."
)


def es_codigo(ruta: str) -> bool:
    """True si el fichero editado cuenta como codigo para esta guarda."""
    if not ruta:
        return False
    nombre = Path(ruta).name
    if nombre in EXCLUIDOS:
        return False
    return Path(ruta).suffix.lower() in EXT_CODIGO


def skill_instalada(raiz: str | None) -> bool:
    """True si el proyecto tiene la skill que esta guarda exige.

    Heredado del hook `recordar-seguridad.sh` al que sustituye, y es la razon de
    que el port no sea una copia: sin esta comprobacion, un proyecto que instale
    el kit sin la skill quedaria con TODA edicion de codigo bloqueada y sin nada
    que invocar para desbloquearla. Exigir algo que no existe no es rigor.
    """
    base = Path(raiz) if raiz else Path.cwd()
    return (base / ".claude" / "skills" / "secure-coding-guard").is_dir()


def abrir_transcript(ruta: str):
    """Abre el transcript tolerando las dos formas del disco en Windows.

    Bash y los binarios nativos no comparten mapa: /c/Users/x lo entiende bash y
    C:/Users/x lo entiende Python de Windows. Aqui se traduce en vez de fallar,
    porque fallar aqui significa bloquear a alguien que si estaba en regla.
    """
    candidatas = [ruta]
    if len(ruta) > 2 and ruta[0] == "/" and ruta[2] == "/":
        candidatas.append(f"{ruta[1]}:/{ruta[3:]}")  # /c/Users/... -> c:/Users/...
    for candidata in candidatas:
        try:
            return open(candidata, encoding="utf-8", errors="replace")
        except OSError:
            continue
    return None


def hay_evidencia(ruta: str | None) -> bool | None:
    """True si la skill se invoco, False si no, None si no se pudo comprobar.

    Los tres estados son el punto: colapsar "no" y "no pude preguntar" en un
    solo valor es como una comprobacion acaba certificando lo que no miro.
    """
    if not ruta:
        return None
    fh = abrir_transcript(ruta)
    if fh is None:
        return None
    leidos = 0
    try:
        with fh:
            for linea in fh:
                if RE_EVIDENCIA.search(linea):
                    return True
                leidos += len(linea)
                if leidos > MAX_BYTES:
                    return None  # truncado: no se puede afirmar que no esta
    except OSError:
        return None
    return False


def marcador(session_id: str) -> Path | None:
    """Fichero de marca para no bloquear en bucle cuando no se puede verificar.

    El session_id se sanea antes de tocar el disco: llega de fuera y se usa como
    nombre de fichero, asi que sin filtrar seria una ruta controlada por la
    entrada (`../..`). Lista blanca, no lista negra.
    """
    limpio = re.sub(r"[^A-Za-z0-9_-]", "", session_id or "")[:64]
    if not limpio:
        return None
    carpeta = Path(tempfile.gettempdir()) / "claude-secure-guard"
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return carpeta / f"{limpio}.avisado"


def bloquear(motivo: str) -> int:
    salida = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": motivo,
        }
    }
    print(json.dumps(salida, ensure_ascii=True))
    return 0


def avisar(mensaje: str) -> int:
    print(json.dumps({"systemMessage": mensaje}, ensure_ascii=True))
    return 0


def main() -> int:
    try:
        datos = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        datos = {}

    if datos.get("tool_name") not in TOOLS:
        return 0

    entrada = datos.get("tool_input") or {}
    ruta = entrada.get("file_path") or entrada.get("notebook_path") or ""
    if not es_codigo(str(ruta)):
        return 0

    if not skill_instalada(datos.get("cwd") or None):
        return 0

    evidencia = hay_evidencia(datos.get("transcript_path"))
    if evidencia is True:
        return 0
    if evidencia is False:
        return bloquear(AVISO.format(ruta=ruta))

    # No se pudo verificar. Bloquea una vez y a partir de ahi avisa en cada
    # edicion: quedarse bloqueando eternamente dejaria la sesion muerta, y
    # callarse convertiria la guarda en un adorno sin que nadie se entere.
    marca = marcador(datos.get("session_id", ""))
    if marca is not None and marca.exists():
        return avisar(AVISO_DEGRADADO)
    if marca is not None:
        try:
            marca.touch()
        except OSError:
            pass
    motivo = "no se encontro el transcript de la sesion"
    return bloquear(AVISO_SIN_VERIFICAR.format(motivo=motivo, ruta=ruta))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - una guarda no puede morir callada
        sys.exit(bloquear(AVISO_SIN_VERIFICAR.format(motivo=f"error interno: {exc}", ruta="?")))
