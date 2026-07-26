#!/bin/sh
# Tests del hook recordar-seguridad.sh contra el CONTRATO REAL de PreToolUse:
# JSON por stdin, aviso por hookSpecificOutput.additionalContext.
#
# Por que existen: la primera version de este hook leia una variable de entorno
# que no existe y escribia el aviso por stdout plano, que en PreToolUse no llega
# a nadie. Pasaba sus propias pruebas porque estaban escritas contra el contrato
# imaginado, no contra el real. Estos casos usan el payload que Claude Code
# manda de verdad.
#
# Uso: sh test_recordar-seguridad.sh     (exit 1 si algun caso falla)
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
HOOK="$AQUI/recordar-seguridad.sh"
TMP="${TMPDIR:-/tmp}/test-recordar-seguridad.$$"
mkdir -p "$TMP/.claude/skills/secure-coding-guard"
trap 'rm -rf "$TMP"' EXIT

FALLIDOS=0

probar() { # probar <nombre> <avisa|calla> <payload> [dir_proyecto]
    nombre="$1"; esperado="$2"; payload="$3"; proyecto="${4:-$TMP}"
    salida=$(printf '%s' "$payload" | CLAUDE_PROJECT_DIR="$proyecto" sh "$HOOK" 2>&1)
    codigo=$?
    if printf '%s' "$salida" | grep -q "additionalContext"; then real=avisa; else real=calla; fi

    veredicto="ok   "
    if [ "$real" != "$esperado" ]; then veredicto="FALLO"; FALLIDOS=$((FALLIDOS + 1)); fi
    # Un hook que bloquea una edicion es peor que un hook que no avisa.
    if [ "$codigo" -ne 0 ]; then veredicto="FALLO"; FALLIDOS=$((FALLIDOS + 1)); fi

    printf '  %s %-46s esperado=%-5s real=%-5s exit=%s\n' \
        "$veredicto" "$nombre" "$esperado" "$real" "$codigo"
}

echo "Tests de recordar-seguridad.sh"

probar "Edit de codigo (.ts)" avisa \
    '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"src/auth.ts","old_string":"a","new_string":"b"}}'
probar "Write de codigo (.py)" avisa \
    '{"tool_name":"Write","tool_input":{"file_path":"src/api.py","content":"print(1)"}}'
probar "NotebookEdit (notebook_path, no file_path)" avisa \
    '{"tool_name":"NotebookEdit","tool_input":{"notebook_path":"analisis.ipynb","new_source":"x=1"}}'
probar "ruta absoluta con unidad de Windows" avisa \
    '{"tool_name":"Edit","tool_input":{"file_path":"C:/proy/src/auth.ts"}}'
probar "documentacion (.md): no ensordecer el aviso" calla \
    '{"tool_name":"Edit","tool_input":{"file_path":"README.md","old_string":"a","new_string":"b"}}'
probar "doc cuyo TEXTO simula un JSON de otra ruta" calla \
    '{"tool_name":"Edit","tool_input":{"file_path":"guia.md","new_string":"ejemplo: \"file_path\": \"src/auth.ts\""}}'
probar "stdin vacio: no colgarse ni romper" calla ''
probar "JSON corrupto: no romper" calla '{"tool_input": {'
probar "proyecto sin la skill instalada: callar" calla \
    '{"tool_name":"Edit","tool_input":{"file_path":"src/auth.ts"}}' "$TMP/sin-skill"

echo
if [ "$FALLIDOS" -gt 0 ]; then
    echo "$FALLIDOS comprobacion(es) fallida(s)."
    exit 1
fi
echo "Todos los casos OK."
