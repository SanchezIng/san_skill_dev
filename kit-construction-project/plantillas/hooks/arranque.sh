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

# Guardas instaladas pero SIN ACTIVAR. Llegan desactivadas a propósito (activar
# `audit` sin rellenar el gestor, o la protección de main sin decidir el modo,
# produce un rojo que no es un fallo real — y un rojo que no significa nada se
# aprende a ignorar). Pero "acuérdate de activarla" no es un mecanismo: sin este
# aviso, la decisión se queda pendiente para siempre y nadie lo nota. Aquí se
# recuerda en cada sesión, con el comando exacto, y desaparece sola al decidir.
DESACTIVADAS=$(ls .github/workflows/*.desactivado 2>/dev/null)
if [ -n "$DESACTIVADAS" ]; then
    echo "--- ⚠ Guardas instaladas y SIN ACTIVAR (decisión pendiente):"
    for f in $DESACTIVADAS; do
        activo=${f%.desactivado}
        case "$(basename "$activo")" in
            audit.yml)
                echo "    $(basename "$activo") — auditoría de dependencias. Antes: rellena GESTOR"
                echo "      en scripts/audit_check.py y descomenta la instalación de deps del stack." ;;
            proteccion-main.yml)
                echo "    $(basename "$activo") — integridad de main. Solo si NO tienes protección de"
                echo "      rama: gh api repos/{owner}/{repo}/rulesets (403 ⇒ no la tienes)." ;;
            *)
                echo "    $(basename "$activo")" ;;
        esac
        echo "      Activar:  git mv $f $activo"
    done
    echo "    Si decides NO usar alguna, bórrala: dejarla ahí es una decisión sin tomar."
fi

echo "--- Protocolo: sin tarea En progreso → /que-toca · al terminar → /cerrar-sesion · leer SIEMPRE progreso/estado-actual.md"
exit 0
