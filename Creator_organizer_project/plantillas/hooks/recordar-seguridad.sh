#!/bin/sh
# Hook PreToolUse del kit portable: recuerda `secure-coding-guard` al modificar
# codigo. Solo lectura; sale silencioso si algo falta (jamas debe bloquear una
# edicion).
#
# Por que existe: hasta 2026-07-22 la obligacion de la skill solo se ejecutaba
# en el paso 6.4 de /que-toca, es decir, en el flujo "reclamo una tarea nueva".
# Todo trabajo que entra por otra puerta —mergear un PR aprobado, resolver
# conflictos, revisar codigo ajeno, un hotfix, retomar tras una pausa— la
# saltaba en silencio. Se detecto tras una sesion completa que resolvio
# conflictos y mergeo ~2160 lineas de codigo de auth sin invocarla nunca.
# Ver Creator_organizer_project/hallazgos/2026-07-22-aplicacion-de-reglas.md
#
# La edicion de codigo es el unico punto que TODAS esas puertas atraviesan.

# Solo interesa el codigo: recordarlo al editar documentacion es el camino mas
# corto a que el aviso se vuelva ruido de fondo y se ignore por costumbre.
RUTA="${CLAUDE_TOOL_FILE_PATH:-}"
[ -z "$RUTA" ] && exit 0

case "$RUTA" in
    *.md|*.txt|*.rst|*.adoc) exit 0 ;;
esac

# Sin la skill instalada no hay nada que recordar.
[ -d .claude/skills/secure-coding-guard ] || exit 0

echo "[seguridad] Vas a modificar codigo. Si aun no aplicaste secure-coding-guard"
echo "[seguridad] en esta sesion, leela antes de seguir: es obligatoria tambien"
echo "[seguridad] en merges, conflictos, hotfixes y revisiones — no solo al"
echo "[seguridad] reclamar una tarea nueva con /que-toca."
exit 0
