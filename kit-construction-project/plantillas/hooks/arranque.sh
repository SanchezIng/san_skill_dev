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
# Se lee progreso/log/ y NO progreso/tablero-equipo.md: el tablero es generado y
# ya no se comitea, asi que en un clon recien hecho no existe y esto callaria
# sin decir por que. El log si viaja en git, un fichero por entrada.
if [ -n "$DEV" ] && [ -d progreso/log ]; then
    MENCIONES=$(grep -ril -- "$DEV" progreso/log/*.md 2>/dev/null | sort | tail -3)
    if [ -n "$MENCIONES" ]; then
        echo "--- Últimas entradas del log que te mencionan ($DEV):"
        # shellcheck disable=SC2086
        head -n 2 $MENCIONES | sed 's/^/    /'
    fi
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

# Mismo mecanismo que el bloque de arriba, aplicado a los hooks de git: un aviso
# que se muestra solo a quien le falta algo y desaparece solo al arreglarlo.
#
# El caso concreto: `.git/hooks/` NO viaja con `git pull`. Cuando el repo añade
# un tipo de hook nuevo, los clones que ya existían no se enteran y siguen
# trabajando sin esa guarda — sin error, sin aviso, sin nada que lo delate. El
# dev cree estar cubierto porque "ya ejecuté pre-commit install" (y es verdad:
# lo ejecutó cuando ese hook todavía no existía). Documentarlo no basta; hay que
# detectarlo, y el arranque de sesión es el único punto por el que se pasa
# siempre.
if [ -f .pre-commit-config.yaml ] && grep -q 'pre-push' .pre-commit-config.yaml 2>/dev/null; then
    if [ ! -f .git/hooks/pre-push ]; then
        echo "--- ⚠ Te falta el hook pre-push: tu clon es anterior a él y NO tienes esa guarda."
        echo "      Instalar (inofensivo repetirlo):  pre-commit install"
    fi
fi

echo "--- Protocolo: sin tarea En progreso → /que-toca · al terminar → /cerrar-sesion · leer SIEMPRE progreso/estado-actual.md"
exit 0
