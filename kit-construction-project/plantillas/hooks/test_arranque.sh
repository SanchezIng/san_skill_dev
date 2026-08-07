#!/bin/sh
# Tests del hook arranque.sh.
#
# Por que existen: un hook de arranque que revienta deja la sesion sin contexto,
# y uno que avisa de lo que no toca se aprende a ignorar. Lo que se protege aqui
# es sobre todo el aviso de guardas SIN ACTIVAR: es el mecanismo que impide que
# "acuerdate de activarla" se quede pendiente para siempre. Tiene que aparecer
# cuando hay decision pendiente, DESAPARECER cuando se toma, y no romper nunca
# el arranque.
#
# Uso: sh test_arranque.sh     (exit 1 si algun caso falla)
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
HOOK="$AQUI/arranque.sh"
TMP="${TMPDIR:-/tmp}/test-arranque.$$"
FALLIDOS=0

limpiar() { rm -rf "$TMP"; mkdir -p "$TMP/.github/workflows"; }
trap 'rm -rf "$TMP"' EXIT

comprobar() { # comprobar <nombre> <condicion-ya-evaluada:0|1>
    if [ "$2" -eq 0 ]; then
        printf '  ok    %s\n' "$1"
    else
        printf '  FALLO %s\n' "$1"
        FALLIDOS=$((FALLIDOS + 1))
    fi
}

correr() { (cd "$TMP" && sh "$HOOK" 2>&1); }

echo "Tests de arranque.sh"

# --- Sin guardas desactivadas: ni una palabra del tema -----------------------
limpiar
: > "$TMP/.github/workflows/ci.yml"
SALIDA="$(correr)"; CODIGO=$?
comprobar "proyecto sin guardas pendientes: no menciona el tema" \
    "$(printf '%s' "$SALIDA" | grep -qi 'SIN ACTIVAR' && echo 1 || echo 0)"
comprobar "y aun asi inyecta el contexto de protocolo" \
    "$(printf '%s' "$SALIDA" | grep -q '/que-toca' && echo 0 || echo 1)"
comprobar "exit 0 (un hook nunca rompe el arranque)" "$CODIGO"

# --- Con una guarda desactivada: avisa Y da el comando exacto ----------------
limpiar
: > "$TMP/.github/workflows/audit.yml.desactivado"
SALIDA="$(correr)"; CODIGO=$?
comprobar "guarda desactivada: AVISA" \
    "$(printf '%s' "$SALIDA" | grep -qi 'SIN ACTIVAR' && echo 0 || echo 1)"
comprobar "dice el comando exacto para activarla" \
    "$(printf '%s' "$SALIDA" | grep -q 'git mv .github/workflows/audit.yml.desactivado .github/workflows/audit.yml' && echo 0 || echo 1)"
comprobar "explica el prerrequisito de esa guarda (GESTOR)" \
    "$(printf '%s' "$SALIDA" | grep -q 'GESTOR' && echo 0 || echo 1)"
comprobar "ofrece la salida de borrarla (no decidir tambien es un estado)" \
    "$(printf '%s' "$SALIDA" | grep -q 'sin tomar' && echo 0 || echo 1)"
comprobar "exit 0" "$CODIGO"

# --- Varias a la vez: las nombra todas ---------------------------------------
limpiar
: > "$TMP/.github/workflows/audit.yml.desactivado"
: > "$TMP/.github/workflows/proteccion-main.yml.desactivado"
SALIDA="$(correr)"
comprobar "dos guardas pendientes: nombra las dos" \
    "$(printf '%s' "$SALIDA" | grep -q 'audit.yml' && printf '%s' "$SALIDA" | grep -q 'proteccion-main.yml' && echo 0 || echo 1)"
comprobar "cada una con su prerrequisito propio (rulesets)" \
    "$(printf '%s' "$SALIDA" | grep -q 'rulesets' && echo 0 || echo 1)"

# --- Al ACTIVARLA, el aviso desaparece solo ----------------------------------
limpiar
: > "$TMP/.github/workflows/audit.yml"
SALIDA="$(correr)"
comprobar "TRAS ACTIVARLA: el aviso desaparece (no se vuelve ruido de fondo)" \
    "$(printf '%s' "$SALIDA" | grep -qi 'SIN ACTIVAR' && echo 1 || echo 0)"

# --- Guarda desconocida: se nombra igual, sin inventarse instrucciones -------
limpiar
: > "$TMP/.github/workflows/lo-que-sea.yml.desactivado"
SALIDA="$(correr)"
comprobar "workflow desconocido: lo nombra sin inventar prerrequisitos" \
    "$(printf '%s' "$SALIDA" | grep -q 'lo-que-sea.yml' && echo 0 || echo 1)"

# --- Hook pre-push declarado pero NO instalado: avisa -------------------------
# Es el caso que motiva el aviso: .git/hooks no viaja con git pull, asi que un
# clon anterior al hook se queda sin la guarda y nada se lo dice.
limpiar
printf 'repos:\n  - repo: local\n    hooks:\n      - id: ci-local\n        stages: [pre-push]\n' > "$TMP/.pre-commit-config.yaml"
mkdir -p "$TMP/.git/hooks"
SALIDA="$(correr)"; CODIGO=$?
comprobar "pre-push declarado y NO instalado: AVISA" \
    "$(printf '%s' "$SALIDA" | grep -qi 'falta el hook pre-push' && echo 0 || echo 1)"
comprobar "dice el comando exacto para instalarlo" \
    "$(printf '%s' "$SALIDA" | grep -q 'pre-commit install' && echo 0 || echo 1)"
comprobar "exit 0 (avisar no es romper el arranque)" "$CODIGO"

# --- Ya instalado: silencio (si no, se vuelve ruido de fondo) ----------------
limpiar
printf 'repos:\n  - repo: local\n    hooks:\n      - id: ci-local\n        stages: [pre-push]\n' > "$TMP/.pre-commit-config.yaml"
mkdir -p "$TMP/.git/hooks"; : > "$TMP/.git/hooks/pre-push"
SALIDA="$(correr)"
comprobar "TRAS INSTALARLO: el aviso desaparece solo" \
    "$(printf '%s' "$SALIDA" | grep -qi 'falta el hook pre-push' && echo 1 || echo 0)"

# --- Config sin stage pre-push: no se inventa un aviso -----------------------
limpiar
printf 'repos:\n  - repo: local\n    hooks:\n      - id: algo\n' > "$TMP/.pre-commit-config.yaml"
mkdir -p "$TMP/.git/hooks"
SALIDA="$(correr)"
comprobar "sin stage pre-push declarado: NO avisa de nada" \
    "$(printf '%s' "$SALIDA" | grep -qi 'falta el hook pre-push' && echo 1 || echo 0)"

# --- Sin git y sin nada: sigue sin romperse ----------------------------------
rm -rf "$TMP"; mkdir -p "$TMP"
SALIDA="$(correr)"; CODIGO=$?
comprobar "directorio pelado (sin .github, sin progreso): exit 0" "$CODIGO"
comprobar "sin .pre-commit-config.yaml: tampoco avisa del pre-push" \
    "$(printf '%s' "$SALIDA" | grep -qi 'falta el hook pre-push' && echo 1 || echo 0)"

echo
if [ "$FALLIDOS" -eq 0 ]; then
    echo "Todos los casos OK."
else
    echo "$FALLIDOS caso(s) fallidos."
fi
[ "$FALLIDOS" -eq 0 ]
