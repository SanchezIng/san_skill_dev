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
# Dos agujeros corregidos en un proyecto real, y los dos eran el MISMO fallo que este bloque
# denuncia: la guarda contra el fallo invisible lo tenía ella misma.
#
#   1. Antes solo miraba `pre-push`. Un clon con `pre-commit` y sin `pre-push`
#      —o al revés— pasaba callado, y ese es el caso REAL: quien instaló los
#      hooks cuando el repo solo declaraba uno tiene exactamente ese clon.
#   2. Antes bastaba con que el fichero EXISTIERA. Un hook heredado de otro
#      flujo, o escrito a mano, daba falso verde: fichero presente, guarda
#      ausente. Ahora se exige el marcador que pre-commit escribe en su
#      cabecera, o sea que el hook sea REALMENTE el suyo.
#
# Los tipos NO se escriben aquí, se leen del propio `.pre-commit-config.yaml`.
# Hardcodearlos es justo lo que dejó a este bloque mirando un solo hook cuando
# el repo ya usaba dos; así, el día que se añada un tercero queda cubierto solo.
if [ -f .pre-commit-config.yaml ]; then
    # Base: lo que `pre-commit install` instalaría. Si el repo lo declara, manda
    # esa lista; si no, pre-commit instala solo el tipo `pre-commit`.
    tipos_hook=$(sed -n 's/^default_install_hook_types:[[:space:]]*\[\([^]]*\)\].*/\1/p' \
        .pre-commit-config.yaml | tr -d ' ' | tr ',' ' ')

    # Y además, cualquier `stages: [...]` de un hook: si algo declara correr en
    # pre-push, ese hook de git tiene que existir o ese paso NO corre nunca.
    # Anclado a principio de línea: `.*stages:` cogía también `default_stages:` y
    # cualquier ejemplo COMENTADO, y un aviso fantasma se aprende a ignorar
    # exactamente igual que uno de verdad (lo pidio una review).
    etapas=$(sed -n 's/^[[:space:]]*stages:[[:space:]]*\[\([^]]*\)\].*/\1/p' \
        .pre-commit-config.yaml | tr -d ' ' | tr ',' ' ')

    # Los dos `sed` de arriba solo entienden YAML de FLUJO (`clave: [a, b]`). La
    # forma de BLOQUE es igual de válida y la escribiría cualquier formateador:
    #
    #     default_install_hook_types:
    #       - pre-commit
    #
    # Ahí no matchean, `tipos_hook` cae al defecto y `etapas` sale vacío — o sea
    # que el agujero 1 vuelve entero y SIN SÍNTOMA. Una guarda que existe
    # para denunciar fallos invisibles no puede permitirse uno: si la clave está
    # y no se pudo leer, se dice. No hace falta un parser de
    # YAML; hace falta no callarse.
    #
    # Se cuenta —declaradas contra leídas— y no se mira si el resultado quedó
    # vacío, porque «vacío» solo caza el caso en que TODAS están en bloque. Con
    # un fichero MIXTO (una lista corta en flujo y otra expandida, que es
    # justo lo que producen los formateadores al pasar de cierto largo) la
    # primera llena `etapas`, la condición de vacío no se cumple, y el `pre-push`
    # de la segunda desaparece sin rastro: el agujero 1 en version estrecha.
    # Reproducido en una segunda review sobre un proyecto real, no supuesto.
    sin_leer=""
    if [ "$(grep -c '^default_install_hook_types:' .pre-commit-config.yaml)" -ne \
         "$(sed -n 's/^default_install_hook_types:[[:space:]]*\[[^]]*\].*/x/p' .pre-commit-config.yaml | wc -l)" ]; then
        sin_leer="default_install_hook_types"
    fi
    if [ "$(grep -c '^[[:space:]]*stages:' .pre-commit-config.yaml)" -ne \
         "$(sed -n 's/^[[:space:]]*stages:[[:space:]]*\[[^]]*\].*/x/p' .pre-commit-config.yaml | wc -l)" ]; then
        sin_leer="${sin_leer:+$sin_leer y }stages"
    fi
    if [ -n "$sin_leer" ]; then
        echo "--- ⚠ No consigo leer $sin_leer de .pre-commit-config.yaml."
        echo "      Solo entiendo la forma de flujo: 'clave: [pre-commit, pre-push]'."
        echo "      Escrito en bloque ('- pre-commit') esta comprobación NO cubre lo"
        echo "      que crees: verifica a mano con 'pre-commit install'."
    fi

    [ -n "$tipos_hook" ] || tipos_hook="pre-commit"

    faltan=""
    # `set -f` mientras se recorre: el `$(...)` va sin comillas a propósito
    # —hace falta el word splitting— pero sin esto pasaría también por globbing,
    # y un `stages: [*]` en el config expandiría a los ficheros del directorio.
    # El `case` de abajo ya lo contendría, pero el aviso saldría absurdo.
    set -f
    for tipo in $(printf '%s %s\n' "$tipos_hook" "$etapas" | tr ' ' '\n' | sort -u); do
        # Solo tipos que son hooks de git de verdad: `stages` admite tambien
        # valores como `manual`, que no instalan nada.
        case "$tipo" in
            pre-commit|pre-merge-commit|pre-push|prepare-commit-msg|commit-msg|post-commit|post-checkout|post-merge|post-rewrite) ;;
            *) continue ;;
        esac
        if ! grep -q 'generated by pre-commit' ".git/hooks/$tipo" 2>/dev/null; then
            faltan="$faltan $tipo"
        fi
    done
    set +f

    for tipo in $faltan; do
        echo "--- ⚠ Te falta el hook $tipo (o el que tienes no lo generó pre-commit)."
        echo "      Tu clon NO tiene esa guarda, y no hay ningún síntoma que lo delate."
        echo "      Instalar (inofensivo repetirlo):  pre-commit install"
    done
fi

echo "--- Protocolo: sin tarea En progreso → /que-toca · al terminar → /cerrar-sesion · leer SIEMPRE progreso/estado-actual.md"
exit 0
