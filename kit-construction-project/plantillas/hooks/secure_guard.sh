#!/bin/sh
# Envoltura del hook PreToolUse: localiza Python y le pasa el JSON del hook por
# stdin (`exec` conserva stdin). Existe porque el nombre del interprete no es el
# mismo en las maquinas del equipo: en Git Bash sobre Windows suele haber
# `python` y no `python3`, y `settings.json` no sabe elegir.
#
# Si NO hay Python, la guarda no puede correr — y entonces BLOQUEA en vez de
# dejar pasar. Es la regla que atraviesa todo el kit: una guarda que solo emite
# señal cuando todo va bien no distingue "paso" de "no corrio". El silencio no
# es un estado de exito.

RAIZ="${CLAUDE_PROJECT_DIR:-.}"
GUARDA="$RAIZ/.claude/hooks/secure_guard.py"

for PY in python3 python py; do
    if command -v "$PY" >/dev/null 2>&1; then
        exec "$PY" "$GUARDA"
    fi
done

printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[secure-coding-guard] BLOQUEADO: la guarda de seguridad no pudo ejecutarse porque no hay Python en el PATH, asi que no puede comprobar si la skill obligatoria se invoco. Instala Python o corrige el PATH; mientras tanto, invoca la skill secure-coding-guard a mano antes de tocar codigo."}}'
exit 0
