#!/bin/sh
# Hook SessionStart del kit portable: inyecta contexto de orientación al abrir una
# sesión de Claude Code, para no gastar los primeros turnos leyendo el protocolo.
# Solo lectura; sale silencioso si algo falta (jamás debe romper el arranque).

echo "=== Contexto de arranque (hook del equipo) ==="

echo "--- Últimos commits en la rama actual:"
git log --oneline -5 2>/dev/null || echo "(sin git)"

RAMA=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
echo "--- Rama: ${RAMA:-desconocida}"

DEV=$(git config user.name 2>/dev/null)
if [ -n "$DEV" ] && [ -f progreso/tablero-equipo.md ]; then
    echo "--- Últimas líneas del log del tablero que te mencionan ($DEV):"
    grep -i -- "$DEV" progreso/tablero-equipo.md | tail -3
fi

ULTIMO_HANDOFF=$(ls -t progreso/fase-*.md 2>/dev/null | head -1)
if [ -n "$ULTIMO_HANDOFF" ]; then
    echo "--- Handoff más reciente: $ULTIMO_HANDOFF (léelo si retomas ese módulo)"
fi

echo "--- Protocolo: sin tarea En progreso → /que-toca · al terminar → /cerrar-sesion · leer SIEMPRE progreso/estado-actual.md"
exit 0
