#!/bin/sh
# Instala el kit en un proyecto destino. Uso:
#
#   sh instalar.sh /ruta/al/proyecto            # fábrica: kickstart + guardián
#   sh instalar.sh /ruta/al/proyecto --protocolo # además, las 3 skills del protocolo
#
# Regla: NADA global. Todo queda dentro del proyecto destino, para comitearlo
# ahí y que viaje al equipo por git pull.
set -eu

KIT="$(cd "$(dirname "$0")" && pwd)"
DESTINO="${1:-}"
MODO="${2:-}"

if [ -z "$DESTINO" ] || [ ! -d "$DESTINO" ]; then
    echo "ERROR: pasa la ruta de un proyecto existente."
    echo "Uso: sh instalar.sh /ruta/al/proyecto [--protocolo]"
    exit 1
fi

mkdir -p "$DESTINO/.claude/skills"

# --- Siempre: la fábrica y el guardián (listos para usar, sin placeholders) ---
cp -r "$KIT/skills/project-kickstart" "$DESTINO/.claude/skills/"
cp -r "$KIT/skills/secure-coding-guard" "$DESTINO/.claude/skills/"
echo "OK  .claude/skills/project-kickstart"
echo "OK  .claude/skills/secure-coding-guard"

# El kickstart necesita sus plantillas al lado: se lleva el kit entero.
if [ "$KIT" != "$(cd "$DESTINO" && pwd)/SKILLS-PORTABLE" ]; then
    mkdir -p "$DESTINO/SKILLS-PORTABLE"
    cp -r "$KIT/skills" "$KIT/plantillas" "$KIT/README.md" "$KIT/instalar.sh" "$DESTINO/SKILLS-PORTABLE/"
    echo "OK  SKILLS-PORTABLE/ (el kickstart busca aqui sus plantillas)"
fi

# --- Siempre: los hooks ---
# El recordatorio de seguridad va con el GUARDIAN, no con el protocolo de
# equipo: la skill se salta igual en un proyecto de un solo dev cuando el
# trabajo entra por una puerta imprevista (merge, conflicto, hotfix, revision).
mkdir -p "$DESTINO/.claude/hooks"
cp "$KIT/plantillas/hooks/arranque.sh" "$DESTINO/.claude/hooks/"
cp "$KIT/plantillas/hooks/recordar-seguridad.sh" "$DESTINO/.claude/hooks/"
# El test viaja con el hook: un hook silencioso es indistinguible de un hook
# roto, asi que el equipo tiene que poder comprobarlo en su maquina.
cp "$KIT/plantillas/hooks/test_recordar-seguridad.sh" "$DESTINO/.claude/hooks/"
if [ -f "$DESTINO/.claude/settings.json" ]; then
    # No se pisa un settings.json existente: puede tener config propia del dev.
    # Pero entonces el hook PreToolUse no llega solo, y ese es justo el caso de
    # los proyectos ya instalados — los que mas lo necesitan.
    grep -q "recordar-seguridad" "$DESTINO/.claude/settings.json" || AVISO_HOOK=1
else
    cp "$KIT/plantillas/hooks/settings.json" "$DESTINO/.claude/settings.json"
fi
echo "OK  hooks (arranque + recordatorio de seguridad)"

if [ -n "${AVISO_HOOK:-}" ]; then
    echo
    echo "AVISO: .claude/settings.json ya existia y no se ha tocado, asi que el"
    echo "       hook PreToolUse de secure-coding-guard NO quedo activo. Anadelo"
    echo "       a mano copiando el bloque 'PreToolUse' de:"
    echo "       $KIT/plantillas/hooks/settings.json"
    echo "       Comprueba luego que avisa de verdad:"
    echo "       sh .claude/hooks/test_recordar-seguridad.sh"
fi

if [ "$MODO" != "--protocolo" ]; then
    echo
    echo "Listo. Abre Claude Code en $DESTINO y di \"tengo una idea...\"."
    echo "El kickstart generara la documentacion Y las 3 skills del protocolo ya rellenadas."
    exit 0
fi

# --- Solo con --protocolo: las 3 skills del equipo, SIN rellenar ---
echo
echo "Instalando las skills del protocolo (quedan con placeholders):"
for nombre in que-toca cerrar-sesion verificar; do
    mkdir -p "$DESTINO/.claude/skills/equipo-$nombre"
    cp "$KIT/skills/equipo/$nombre.SKILL.md" "$DESTINO/.claude/skills/equipo-$nombre/SKILL.md"
    echo "OK  .claude/skills/equipo-$nombre/SKILL.md"
done

mkdir -p "$DESTINO/scripts" "$DESTINO/.github/workflows"
cp "$KIT/plantillas/ci/docs_check.py" "$DESTINO/scripts/"
cp "$KIT/plantillas/ci/docs-check.yml" "$DESTINO/.github/workflows/"
echo "OK  guardas de deriva doc<->realidad"

echo
echo "FALTA (a mano, o pideselo a Claude):"
echo "  1. Rellenar los {{PLACEHOLDERS}} de las 3 skills — tabla en el README del kit."
echo "  2. Descubrir los IDs del GitHub Project (query en el README) y pegarlos en"
echo "     .claude/skills/equipo-que-toca/SKILL.md."
echo "  3. Pegar plantillas/CLAUDE-fragmento.md en el CLAUDE.md del proyecto."
echo "  4. Anadir .claude/settings.local.json al .gitignore y COMITEAR todo lo demas."
grep -rho '{{[A-Z_]*}}' "$DESTINO/.claude/skills/equipo-"*/SKILL.md | sort -u | tr '\n' ' '
echo
