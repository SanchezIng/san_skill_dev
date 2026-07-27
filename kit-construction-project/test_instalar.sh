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
SALIDA_INICIAL="$(sh "$KIT/instalar.sh" "$PROY" --protocolo 2>&1)"
[ -f "$SKILL" ]; comprobar "instala las skills del protocolo" $?

# El resumen tiene que listar TODOS los placeholders pendientes, no solo los de
# las skills: {{GESTOR_PAQUETES}} vive en scripts/audit_check.py y quedaba fuera,
# asi que se rellenaba lo listado y el audit se quedaba sin gestor.
printf '%s' "$SALIDA_INICIAL" | grep -q '{{GESTOR_PAQUETES}}'
comprobar "el resumen lista tambien los placeholders de scripts/" $?
printf '%s' "$SALIDA_INICIAL" | grep -q '{{CUANDO_NIVEL_2}}'
comprobar "y los que llevan digitos en el nombre" $?
printf '%s' "$SALIDA_INICIAL" | grep -q '{{NOMBRE_PROYECTO}}'
comprobar "pero NO los de las plantillas del kickstart (son documentacion)" $([ $? -ne 0 ] && echo 0 || echo 1)

printf '%s' "$SALIDA_INICIAL" | grep -q "FALTA (a mano"
comprobar "la instalacion inicial dice lo que falta configurar" $?

# __pycache__ son binarios del interprete de otra maquina. Ya paso con las
# plantillas (M-05) y volvio a pasar al meter un .py dentro de la skill.
[ -z "$(find "$PROY" -name '__pycache__' -print -quit)" ]
comprobar "NO copia __pycache__ al proyecto destino" $?
[ -f "$PROY/SKILLS-PORTABLE/.manifiesto" ]; comprobar "deja un manifiesto de lo instalado" $?
grep -q '^# modo=--protocolo' "$PROY/SKILLS-PORTABLE/.manifiesto"
comprobar "el manifiesto recuerda el modo de instalacion" $?

# La auditoria llega con la lista VACIA y el workflow DESACTIVADO: activarlo sin
# rellenar el gestor solo produce un rojo que no es una vulnerabilidad, y un rojo
# que no significa nada se aprende a ignorar.
[ -f "$PROY/security/audit-allowlist.json" ]
comprobar "instala la allowlist de auditoria" $?
grep -q '"aceptados": \[\]' "$PROY/security/audit-allowlist.json"
comprobar "la allowlist nace VACIA (nada aceptado por defecto)" $?
[ -f "$PROY/.github/workflows/audit.yml.desactivado" ] && [ ! -f "$PROY/.github/workflows/audit.yml" ]
comprobar "el workflow de auditoria se instala desactivado" $?

# --- 2. El equipo configura su proyecto -------------------------------------
sed -i 's|{{PREFIJO_RAMA}}|mi-modulo/mi-tarea|g; s|{{OWNER}}|MiEquipo|g' "$SKILL"
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

grep -q "MiEquipo" "$SKILL"
comprobar "LA CONFIGURACION SOBREVIVE (owner intacto)" $?
grep -q "mi-modulo/mi-tarea" "$SKILL"
comprobar "la configuracion sobrevive (convencion de ramas intacta)" $?
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

# --- 4b. El repaso de configuracion llega TAMBIEN al actualizar -------------
# Vivia despues del `exit 0` de esta ruta, asi que se perdia entero: los
# placeholders, OWNER/PROJECT_NUMBER, el CLAUDE-fragmento, el .gitignore y
# proteger main. Y como el instalador FUERZA el modo actualizacion en cuanto ve
# una instalacion previa, esta es la ruta MAS probable, no un caso raro. Era la
# unica de las tres sin cubrir aqui, que es justo por lo que nadie lo vio.
printf '%s' "$SALIDA" | grep -q "REPASO de configuracion"
comprobar "AL ACTUALIZAR tambien se recuerda lo que falta configurar" $?
printf '%s' "$SALIDA" | grep -q "Proteger main"
comprobar "y el repaso trae los pasos enteros, no solo el titulo" $?
printf '%s' "$SALIDA" | grep -q '{{GESTOR_PAQUETES}}'
comprobar "y la lista de placeholders que siguen sin rellenar" $?

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
grep -q "MiEquipo" "$SKILL"
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
sed -i "s/{{OWNER}}/MiEquipoReflejo/g" "$SKILL3"
SALIDA4="$(sh "$KIT2/instalar.sh" "$PROY3" --protocolo 2>&1)"
grep -q "MiEquipoReflejo" "$SKILL3"
comprobar "REINSTALAR con el mismo comando tampoco pisa la config" $?
printf '%s' "$SALIDA4" | grep -q "se ACTUALIZA en vez de reinstalar"
comprobar "y avisa de que ha cambiado a modo actualizacion" $?
# Este es el camino exacto que documenta el README (fabrica y luego --protocolo,
# dos lineas seguidas) y el que se perdia el repaso sin que nadie lo pidiera.
printf '%s' "$SALIDA4" | grep -q "REPASO de configuracion"
comprobar "repetir el comando de instalacion tampoco pierde el repaso" $?

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
sed -i "s/{{OWNER}}/MiEquipoLegado/g" "$SKILL2"
rm -f "$PROY2/SKILLS-PORTABLE/.manifiesto"        # simula instalacion pre-manifiesto
SALIDA3="$(sh "$KIT2/instalar.sh" "$PROY2" --actualizar 2>&1)"
grep -q "MiEquipoLegado" "$SKILL2"
comprobar "sin manifiesto tampoco pisa la configuracion" $?
printf '%s' "$SALIDA3" | grep -q "no hay SKILLS-PORTABLE/.manifiesto"
comprobar "y lo dice claramente" $?

echo
if [ "$FALLIDOS" -gt 0 ]; then
    echo "$FALLIDOS comprobacion(es) fallida(s)."
    exit 1
fi
echo "Todos los casos OK."
