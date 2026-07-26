#!/bin/sh
# Hook PreToolUse del kit portable: recuerda `secure-coding-guard` al modificar
# codigo. Solo lectura; sale silencioso si algo falta (jamas debe bloquear una
# edicion) -> siempre exit 0.
#
# Por que existe: la obligacion de la skill solo se ejecutaba en el paso 6.4 de
# /que-toca, es decir, en el flujo "reclamo una tarea nueva". Todo trabajo que
# entra por otra puerta —mergear un PR aprobado, resolver conflictos, revisar
# codigo ajeno, un hotfix, retomar tras una pausa— la saltaba en silencio. Se
# detecto tras una sesion que resolvio conflictos y mergeo ~2160 lineas de
# codigo de auth sin invocarla nunca. Ver hallazgos/2026-07-22-aplicacion-de-reglas.md
# en el repo-catalogo del kit.
#
# CONTRATO REAL de PreToolUse (docs de Claude Code, verificado end-to-end):
#   1. La ruta del archivo NO llega por el entorno: viene en el JSON de stdin,
#      en .tool_input.file_path (Edit/Write) o .tool_input.notebook_path
#      (NotebookEdit).
#   2. El stdout PLANO de un PreToolUse va SOLO al log de depuracion: no lo ve
#      ni Claude ni el usuario. Para que el aviso llegue al modelo hay que
#      emitir JSON con hookSpecificOutput.additionalContext. (Los eventos que
#      SI inyectan stdout como contexto son UserPromptSubmit,
#      UserPromptExpansion y SessionStart — por eso arranque.sh si funciona.)
#
# Sin `jq`: Git Bash en Windows no lo trae y el kit tiene que correr en las
# maquinas del equipo tal cual. Se extrae con sed.
#
# Limite conocido: cubre Edit/Write/NotebookEdit. Un merge resuelto solo con
# comandos git (p.ej. `git checkout --theirs`) mete codigo sin pasar por
# ninguna de esas herramientas; para ese caso la red es el checkpoint de
# /cerrar-sesion.
#
# Tests: sh plantillas/hooks/test_recordar-seguridad.sh

# stdin puede no existir (invocacion manual): no bloquear esperando.
ENTRADA=$(cat 2>/dev/null) || exit 0
[ -z "$ENTRADA" ] && exit 0

# Primer file_path/notebook_path de tool_input. Se ancla en "tool_input" para
# que el contenido de old_string/new_string (que puede traer la cadena literal
# "file_path") no confunda la extraccion.
RUTA=$(printf '%s' "$ENTRADA" \
    | sed -n 's/.*"tool_input"[[:space:]]*:[[:space:]]*{[[:space:]]*"\(file_path\|notebook_path\)"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\2/p')
[ -z "$RUTA" ] && exit 0

# Solo interesa el codigo: recordarlo al editar documentacion es el camino mas
# corto a que el aviso se vuelva ruido de fondo y se ignore por costumbre.
case "$RUTA" in
    *.md|*.MD|*.txt|*.rst|*.adoc) exit 0 ;;
esac

# Sin la skill instalada no hay nada que recordar.
[ -d "${CLAUDE_PROJECT_DIR:-.}/.claude/skills/secure-coding-guard" ] || exit 0

cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[seguridad] Vas a modificar codigo. Si aun no aplicaste secure-coding-guard en esta sesion, leela antes de seguir: es obligatoria tambien en merges, conflictos, hotfixes y revisiones, no solo al reclamar una tarea nueva con /que-toca."
  },
  "suppressOutput": true
}
JSON
exit 0
