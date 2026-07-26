#!/bin/sh
# Tests del instalador, con foco en la ACTUALIZACION.
#
# Por que existen: hasta 2026-07-26 reinstalar el kit sobre un proyecto ya
# configurado sobrescribia las skills del protocolo y borraba los IDs del
# Project y los comandos del stack. En silencio, con exit 0 y mensajes "OK".
# El resultado era que ninguna mejora del kit podia llegar a los proyectos ya
# instalados, porque la unica via para traersela destruia su configuracion.
#
# Se ejercita el ciclo real: instalar -> el equipo configura -> sale una version
# nueva del kit -> actualizar. Y se comprueba lo que de verdad importa: que la
# configuracion sobrevive Y que lo nuevo llega.
#
# Uso: sh test_instalar.sh     (exit 1 si algun caso falla)
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
TMP="${TMPDIR:-/tmp}/test-instalar.$$"
FALLIDOS=0
mkdir -p "$TMP"
trap 'rm -rf "$TMP"' EXIT

comprobar() {  # comprobar <descripcion> <condicion-ya-evaluada:0|1>
    if [ "$2" -eq 0 ]; then
        printf '  ok    %s\n' "$1"
    else
        printf '  FALLO %s\n' "$1"
        FALLIDOS=$((FALLIDOS + 1))
    fi
}

PROY="$TMP/proyecto"
KIT2="$TMP/kit-v2"
SKILL="$PROY/.claude/skills/equipo-que-toca/SKILL.md"

echo "Tests del instalador"
echo

# --- 1. Instalacion inicial -------------------------------------------------
mkdir -p "$PROY"
sh "$KIT/instalar.sh" "$PROY" --protocolo >/dev/null 2>&1
[ -f "$SKILL" ]; comprobar "instala las skills del protocolo" $?
[ -f "$PROY/SKILLS-PORTABLE/.manifiesto" ]; comprobar "deja un manifiesto de lo instalado" $?
grep -q '^# modo=--protocolo' "$PROY/SKILLS-PORTABLE/.manifiesto"
comprobar "el manifiesto recuerda el modo de instalacion" $?

# --- 2. El equipo configura su proyecto -------------------------------------
sed -i 's/{{PROJECT_ID}}/PVT_kwHOreal123/g; s/{{OWNER}}/MiEquipo/g' "$SKILL"
# Y ajusta una constante de un script (configuracion que NO es un placeholder).
sed -i 's/^EXIGIR_REVISION = True/EXIGIR_REVISION = False/' "$PROY/scripts/proteccion_main.py"

# --- 3. Sale una version nueva del kit --------------------------------------
cp -r "$KIT" "$KIT2"
echo "2099-01-01" > "$KIT2/VERSION"
#   a) mejora en un archivo que el equipo TOCO
printf '\n<!-- mejora del kit en un archivo configurado -->\n' >> "$KIT2/skills/equipo/que-toca.SKILL.md"
#   b) mejora en un archivo que el equipo NO toco
printf '\n# mejora del kit en un archivo intacto\n' >> "$KIT2/plantillas/hooks/arranque.sh"
#   c) archivo completamente nuevo
printf 'echo nuevo\n' > "$KIT2/plantillas/hooks/hook-nuevo.sh"
sed -i 's|^copiar "$KIT/plantillas/hooks/arranque.sh".*|&\ncopiar "$KIT/plantillas/hooks/hook-nuevo.sh" "$DESTINO/.claude/hooks/hook-nuevo.sh"|' \
    "$KIT2/instalar.sh"

# --- 4. Actualizar ----------------------------------------------------------
SALIDA="$(sh "$KIT2/instalar.sh" "$PROY" --actualizar 2>&1)"

grep -q "PVT_kwHOreal123" "$SKILL"
comprobar "LA CONFIGURACION SOBREVIVE (IDs del Project intactos)" $?
grep -q "MiEquipo" "$SKILL"
comprobar "la configuracion sobrevive (owner intacto)" $?
grep -q "^EXIGIR_REVISION = False" "$PROY/scripts/proteccion_main.py"
comprobar "sobrevive la config que NO es placeholder (constante de script)" $?

[ -f "$SKILL.nuevo" ]; comprobar "deja la version nueva al lado como .nuevo" $?
grep -q "mejora del kit en un archivo configurado" "$SKILL.nuevo" 2>/dev/null
comprobar "el .nuevo trae de verdad la mejora" $?

grep -q "mejora del kit en un archivo intacto" "$PROY/.claude/hooks/arranque.sh"
comprobar "SI actualiza los archivos que nadie toco" $?
[ -f "$PROY/.claude/hooks/hook-nuevo.sh" ]
comprobar "trae los archivos nuevos de la version nueva" $?

printf '%s' "$SALIDA" | grep -q "CONSERVADOS"
comprobar "informa de lo que conservo" $?
printf '%s' "$SALIDA" | grep -q "equipo-que-toca"
comprobar "nombra el archivo conservado" $?
grep -q '^# kit=2099-01-01' "$PROY/SKILLS-PORTABLE/.manifiesto"
comprobar "el manifiesto queda sellado con la version nueva" $?

# --- 5. Actualizar dos veces seguidas es idempotente ------------------------
# El caso que mas duele: si al conservar un archivo se registrara el hash del
# EQUIPO, la segunda pasada lo veria "igual a lo registrado", lo daria por
# intacto y lo pisaria. La config sobreviviria una vez y moriria a la siguiente.
SALIDA2="$(sh "$KIT2/instalar.sh" "$PROY" --actualizar 2>&1)"
if printf '%s' "$SALIDA2" | sed -n '/^Actualizados/,/^$/p' | grep -q "arranque.sh"; then
    false
else
    true
fi
comprobar "la segunda pasada no reactualiza lo ya actualizado" $?
grep -q "PVT_kwHOreal123" "$SKILL"
comprobar "LA CONFIG SIGUE VIVA TRAS DOS ACTUALIZACIONES" $?
printf '%s' "$SALIDA2" | grep -q "CONSERVADOS"
comprobar "y se sigue avisando de que esta conservado" $?

# --- 5b. Reconciliar: al aceptar el .nuevo, el archivo vuelve a gestionarse --
cp "$SKILL.nuevo" "$SKILL" && rm -f "$SKILL.nuevo"
SALIDA2B="$(sh "$KIT2/instalar.sh" "$PROY" --actualizar 2>&1)"
printf '%s' "$SALIDA2B" | grep -q "CONSERVADOS" && false || true
comprobar "tras reconciliar deja de estar conservado" $?

# --- 5c. Repetir el comando de instalacion (sin --actualizar) no destruye ---
# El reflejo del equipo es repetir el comando con el que instalaron. Si eso
# pisara la configuracion, la proteccion dependeria de acordarse de un flag.
PROY3="$TMP/proyecto-reflejo"
mkdir -p "$PROY3"
sh "$KIT/instalar.sh" "$PROY3" --protocolo >/dev/null 2>&1
SKILL3="$PROY3/.claude/skills/equipo-que-toca/SKILL.md"
sed -i 's/{{PROJECT_ID}}/PVT_reflejo/g' "$SKILL3"
SALIDA4="$(sh "$KIT2/instalar.sh" "$PROY3" --protocolo 2>&1)"
grep -q "PVT_reflejo" "$SKILL3"
comprobar "REINSTALAR con el mismo comando tampoco pisa la config" $?
printf '%s' "$SALIDA4" | grep -q "se ACTUALIZA en vez de reinstalar"
comprobar "y avisa de que ha cambiado a modo actualizacion" $?

# --- 5d. --protocolo amplia una instalacion de fabrica ----------------------
PROY4="$TMP/proyecto-fabrica"
mkdir -p "$PROY4"
sh "$KIT/instalar.sh" "$PROY4" >/dev/null 2>&1
[ ! -f "$PROY4/.claude/skills/equipo-que-toca/SKILL.md" ]
comprobar "en modo fabrica no se instala el protocolo" $?
sh "$KIT/instalar.sh" "$PROY4" --protocolo >/dev/null 2>&1
[ -f "$PROY4/.claude/skills/equipo-que-toca/SKILL.md" ]
comprobar "--protocolo SI amplia una instalacion de fabrica existente" $?

# --- 6. Instalacion vieja, sin manifiesto: no pisa nada ---------------------
PROY2="$TMP/proyecto-viejo"
mkdir -p "$PROY2"
sh "$KIT/instalar.sh" "$PROY2" --protocolo >/dev/null 2>&1
SKILL2="$PROY2/.claude/skills/equipo-que-toca/SKILL.md"
sed -i 's/{{PROJECT_ID}}/PVT_legado/g' "$SKILL2"
rm -f "$PROY2/SKILLS-PORTABLE/.manifiesto"        # simula instalacion pre-manifiesto
SALIDA3="$(sh "$KIT2/instalar.sh" "$PROY2" --actualizar 2>&1)"
grep -q "PVT_legado" "$SKILL2"
comprobar "sin manifiesto tampoco pisa la configuracion" $?
printf '%s' "$SALIDA3" | grep -q "no hay SKILLS-PORTABLE/.manifiesto"
comprobar "y lo dice claramente" $?

echo
if [ "$FALLIDOS" -gt 0 ]; then
    echo "$FALLIDOS comprobacion(es) fallida(s)."
    exit 1
fi
echo "Todos los casos OK."
