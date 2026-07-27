#!/bin/sh
# Instala o ACTUALIZA el kit en un proyecto destino. Uso:
#
#   sh instalar.sh /ruta/al/proyecto              # fábrica: kickstart + guardián
#   sh instalar.sh /ruta/al/proyecto --protocolo  # además, las 3 skills del protocolo
#   sh instalar.sh /ruta/al/proyecto --actualizar # traerse una versión nueva del kit
#
# Regla: NADA global. Todo queda dentro del proyecto destino, para comitearlo
# ahí y que viaje al equipo por git pull.
#
# Regla de la actualización: NUNCA se pisa un archivo que el equipo haya tocado.
# Para saberlo no se adivina — se registra el hash de cada archivo al instalar
# (SKILLS-PORTABLE/.manifiesto) y se compara. Si el archivo cambió respecto a lo
# que dejó el kit, es del equipo: se conserva y la versión nueva se deja al lado
# como `<archivo>.nuevo` para que decidan ellos.
set -eu

KIT="$(cd "$(dirname "$0")" && pwd)"
VERSION_KIT="$(cat "$KIT/VERSION" 2>/dev/null || echo desconocida)"
DESTINO="${1:-}"
MODO="${2:-}"

if [ -z "$DESTINO" ] || [ ! -d "$DESTINO" ]; then
    echo "ERROR: pasa la ruta de un proyecto existente."
    echo "Uso: sh instalar.sh /ruta/al/proyecto [--protocolo|--actualizar]"
    exit 1
fi
DESTINO="$(cd "$DESTINO" && pwd)"

MANIFIESTO="$DESTINO/SKILLS-PORTABLE/.manifiesto"
PARCIAL="$DESTINO/SKILLS-PORTABLE/.manifiesto.parcial"
ACTUALIZAR=0
CONSERVADOS=""
ACTUALIZADOS=""

MODO_PREVIO="$(sed -n 's/^# modo=//p' "$MANIFIESTO" 2>/dev/null || true)"

# Si ya hay una instalacion aqui, SIEMPRE se actualiza, aunque no lo pidan.
# Nadie recuerda el flag: el reflejo es repetir el comando con el que instalo.
# Que ese reflejo destruya la configuracion del equipo es exactamente el fallo
# que esto viene a arreglar, asi que la proteccion no puede depender de acordarse.
if [ -f "$MANIFIESTO" ] || [ -d "$DESTINO/SKILLS-PORTABLE" ]; then
    ACTUALIZAR=1
    if [ "$MODO" != "--actualizar" ]; then
        echo "(ya hay una instalacion del kit aqui: se ACTUALIZA en vez de reinstalar,"
        echo " para no pisar lo que tengais configurado)"
        echo
    fi
fi

case "$MODO" in
    --protocolo) ;;                       # explicito: manda, puede ampliar el modo
    *)           MODO="$MODO_PREVIO" ;;   # actualizar o sin flags: se conserva
esac

if [ "$ACTUALIZAR" = 1 ]; then
    if [ ! -f "$MANIFIESTO" ]; then
        echo "AVISO: no hay SKILLS-PORTABLE/.manifiesto en el destino."
        echo "       Es una instalacion anterior a los manifiestos, asi que no se puede"
        echo "       saber que archivos tocasteis. Por seguridad NO se pisara ninguno:"
        echo "       los cambios llegaran como <archivo>.nuevo para que los compares."
        echo
    fi
    # El modo ya se resolvio arriba: se conserva el previo salvo que pidan
    # --protocolo explicitamente, que si puede ampliar una instalacion de fabrica.
    VERSION_PREVIA="$(sed -n 's/^# kit=//p' "$MANIFIESTO" 2>/dev/null || true)"
    echo "Actualizando: kit ${VERSION_PREVIA:-desconocida} -> $VERSION_KIT (modo ${MODO:-fabrica})"
    if [ -n "${VERSION_PREVIA:-}" ] && [ "$VERSION_PREVIA" = "$VERSION_KIT" ]; then
        echo "(el destino ya esta en esta version; se comprobara igualmente archivo a archivo)"
    fi
    echo
fi

mkdir -p "$DESTINO/SKILLS-PORTABLE"
: > "$PARCIAL"

hash_de() { git hash-object "$1"; }

hash_registrado() {  # <ruta_relativa> -> hash o vacio
    [ -f "$MANIFIESTO" ] || return 0
    awk -F'\t' -v r="$1" '$2 == r { print $1; exit }' "$MANIFIESTO"
}

# copiar <origen> <destino_absoluto>
copiar() {
    _o="$1"; _d="$2"
    _rel="${_d#"$DESTINO"/}"
    mkdir -p "$(dirname "$_d")"

    if [ "$ACTUALIZAR" = 1 ] && [ -f "$_d" ]; then
        _actual="$(hash_de "$_d")"
        _nuevo="$(hash_de "$_o")"
        if [ "$_actual" = "$_nuevo" ]; then
            printf '%s\t%s\n' "$_nuevo" "$_rel" >> "$PARCIAL"
            return 0
        fi
        _registrado="$(hash_registrado "$_rel")"
        # Sin registro no se puede saber si lo tocaron -> se trata como suyo.
        if [ -z "$_registrado" ] || [ "$_registrado" != "$_actual" ]; then
            cp "$_o" "$_d.nuevo"
            CONSERVADOS="$CONSERVADOS$_rel
"
            # OJO: se re-registra lo que el KIT dejo la ultima vez, NO lo que hay
            # ahora. El manifiesto es "que escribio el kit", no "que hay en disco":
            # si aqui se guardara el hash del equipo, la proxima actualizacion lo
            # veria igual al registrado, lo daria por intacto y lo pisaria. La
            # config sobreviviria una actualizacion y moriria en la siguiente.
            # Sin registro previo se deja sin registrar: el archivo queda como del
            # equipo hasta que lo reconcilien (al copiar el .nuevo encima, el hash
            # coincide con el del kit y vuelve solo a estar gestionado).
            [ -n "$_registrado" ] && printf '%s\t%s\n' "$_registrado" "$_rel" >> "$PARCIAL"
            return 0
        fi
        ACTUALIZADOS="$ACTUALIZADOS$_rel
"
    fi

    cp "$_o" "$_d"
    printf '%s\t%s\n' "$(hash_de "$_d")" "$_rel" >> "$PARCIAL"
}

resumen_actualizacion() {
    echo
    if [ -n "$ACTUALIZADOS" ]; then
        echo "Actualizados (seguian tal cual los dejo el kit):"
        printf '%s' "$ACTUALIZADOS" | sed 's/^/  /'
    else
        echo "Nada que actualizar: todo estaba al dia o lo mantiene el equipo."
    fi
    if [ -n "$CONSERVADOS" ]; then
        echo
        echo "CONSERVADOS (los tocasteis vosotros; NO se han pisado):"
        printf '%s' "$CONSERVADOS" | sed 's/^/  /'
        echo
        echo "De cada uno tienes la version nueva del kit al lado, como <archivo>.nuevo."
        echo "Compara y traete lo que te interese, p.ej.:"
        echo "  git diff --no-index .claude/skills/equipo-que-toca/SKILL.md \\"
        echo "                      .claude/skills/equipo-que-toca/SKILL.md.nuevo"
        echo "Borra los .nuevo cuando termines."
    fi
    echo
    echo "Kit en version $VERSION_KIT. Comprueba que todo sigue verde:"
    echo "  sh .claude/hooks/test_recordar-seguridad.sh"
    [ -f "$DESTINO/scripts/test_docs_check.py" ] && echo "  python3 scripts/test_docs_check.py"
    [ -f "$DESTINO/scripts/test_proteccion_main.py" ] && echo "  python3 scripts/test_proteccion_main.py"
    return 0
}

# El repaso de lo que queda por configurar a mano.
#
# Vive en una funcion porque hace falta en LOS DOS caminos, y durante meses solo
# se imprimio en el primero: el bloque estaba escrito DESPUES del `exit 0` de la
# ruta de actualizacion. Y como el instalador FUERZA el modo actualizacion en
# cuanto detecta una instalacion previa, la ruta que se lo perdia era la mas
# probable de todas: la segunda ejecucion. En la primera ejecucion real del kit
# la lista hubo que reconstruirla a mano leyendo el codigo.
#
# El arreglo no es moverlo por encima del exit: es que ya no haya un exit del
# que depender. Se llama una sola vez, al final, en los dos caminos.
pendiente_de_configurar() {
    echo
    if [ "$ACTUALIZAR" = 1 ]; then
        # Al actualizar no se sabe que hicisteis ya, y decir "FALTA" sobre algo
        # hecho es la clase de ruido que se aprende a saltar. Se enmarca como
        # repaso, y la lista de placeholders de abajo es la que si sabe.
        echo "REPASO de configuracion (lo que ya hicisteis, ignoradlo):"
    else
        echo "FALTA (a mano, o pideselo a Claude):"
    fi
    echo "  1. Rellenar los {{PLACEHOLDERS}} de las 3 skills — tabla en el README del kit."
    echo "  2. Poner OWNER y PROJECT_NUMBER en scripts/tablero.py y comprobarlo:"
    echo "       python3 scripts/tablero.py --comprobar"
    echo "     (los IDs de GraphQL ya NO se pegan a mano: se resuelven solos)"
    echo "  3. Pegar plantillas/CLAUDE-fragmento.md en el CLAUDE.md del proyecto."
    echo "  4. Anadir .claude/settings.local.json al .gitignore y COMITEAR todo lo demas."
    echo "  5. Proteger main. Averigua primero cual te toca:"
    echo "       gh api repos/{owner}/{repo}/rulesets"
    echo "     Lista       -> proteccion de rama (el push se rechaza). README, opcion A."
    echo "     Error 403   -> privado en plan Free: activa la guarda de CI renombrando"
    echo "                    .github/workflows/proteccion-main.yml.desactivado sin el"
    echo "                    sufijo (el push entra, pero se denuncia). README, opcion B."
    # Todo lo INSTANCIADO, no solo las skills: `{{GESTOR_PAQUETES}}` vive en
    # scripts/audit_check.py y `{{RUTA_BACKLOG}}` en scripts/docs_check.py, y listar
    # solo las skills los dejaba fuera — se rellenaba lo que salía y el resto se
    # quedaba sin poner. El kickstart NO se mira: sus plantillas están llenas de
    # {{...}} a propósito, que son documentación, no configuración pendiente.
    # El patrón lleva dígitos ([A-Z0-9_]) porque {{CUANDO_NIVEL_2}} existe.
    grep -rho '{{[A-Z][A-Z0-9_]*}}' \
        "$DESTINO/.claude/skills/equipo-"*/SKILL.md \
        "$DESTINO/scripts/" "$DESTINO/security/" 2>/dev/null | sort -u | tr '\n' ' '
    echo
    return 0
}

# copiar_arbol <dir_origen> <dir_destino>
copiar_arbol() {
    _base="$1"; _dst="$2"
    # __pycache__ fuera: son binarios del intérprete de OTRA máquina. Ya paso una
    # vez con las plantillas (M-05) y volvió a pasar al meter un .py dentro de la
    # skill del kickstart, así que se excluye aquí, en el sitio que copia árboles.
    (cd "$_base" && find . -type f -not -path '*/__pycache__/*') | sed 's|^\./||' | while IFS= read -r _f; do
        echo "$_base/$_f|$_dst/$_f"
    done > "$PARCIAL.arbol"
    while IFS='|' read -r _org _dest; do
        [ -n "$_org" ] && copiar "$_org" "$_dest"
    done < "$PARCIAL.arbol"
    rm -f "$PARCIAL.arbol"
}

# --- Siempre: la fábrica y el guardián (listos para usar, sin placeholders) ---
copiar_arbol "$KIT/skills/project-kickstart" "$DESTINO/.claude/skills/project-kickstart"
copiar_arbol "$KIT/skills/secure-coding-guard" "$DESTINO/.claude/skills/secure-coding-guard"
echo "OK  .claude/skills/project-kickstart"
echo "OK  .claude/skills/secure-coding-guard"

# El kickstart necesita sus plantillas al lado: se lleva el kit entero. Es una
# copia literal del kit, no superficie de configuracion: se refresca entera.
if [ "$KIT" != "$DESTINO/SKILLS-PORTABLE" ]; then
    cp -r "$KIT/skills" "$KIT/plantillas" "$KIT/README.md" "$KIT/instalar.sh" \
          "$KIT/VERSION" "$DESTINO/SKILLS-PORTABLE/"
    # Basura de haber ejecutado los tests en la maquina de origen: no tiene por
    # que viajar al proyecto del equipo.
    find "$DESTINO/SKILLS-PORTABLE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
    echo "OK  SKILLS-PORTABLE/ (el kickstart busca aqui sus plantillas)"
fi

# --- Siempre: los hooks ---
# El recordatorio de seguridad va con el GUARDIAN, no con el protocolo de
# equipo: la skill se salta igual en un proyecto de un solo dev cuando el
# trabajo entra por una puerta imprevista (merge, conflicto, hotfix, revision).
copiar "$KIT/plantillas/hooks/arranque.sh" "$DESTINO/.claude/hooks/arranque.sh"
copiar "$KIT/plantillas/hooks/recordar-seguridad.sh" "$DESTINO/.claude/hooks/recordar-seguridad.sh"
# El test viaja con el hook: un hook silencioso es indistinguible de un hook
# roto, asi que el equipo tiene que poder comprobarlo en su maquina.
copiar "$KIT/plantillas/hooks/test_recordar-seguridad.sh" "$DESTINO/.claude/hooks/test_recordar-seguridad.sh"
copiar "$KIT/plantillas/hooks/test_arranque.sh" "$DESTINO/.claude/hooks/test_arranque.sh"
if [ -f "$DESTINO/.claude/settings.json" ]; then
    # No se pisa un settings.json existente: puede tener config propia del dev.
    # Pero entonces el hook PreToolUse no llega solo, y ese es justo el caso de
    # los proyectos ya instalados — los que mas lo necesitan.
    grep -q "recordar-seguridad" "$DESTINO/.claude/settings.json" || AVISO_HOOK=1
else
    copiar "$KIT/plantillas/hooks/settings.json" "$DESTINO/.claude/settings.json"
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
    { echo "# kit=$VERSION_KIT"; echo "# modo=$MODO"; cat "$PARCIAL"; } > "$MANIFIESTO"
    rm -f "$PARCIAL"
    if [ "$ACTUALIZAR" = 1 ]; then
        resumen_actualizacion
    else
        echo
        echo "Listo. Abre Claude Code en $DESTINO y di \"tengo una idea...\"."
        echo "El kickstart generara la documentacion Y las 3 skills del protocolo ya rellenadas."
    fi
    exit 0
fi

# --- Solo con --protocolo: las 3 skills del equipo, SIN rellenar ---
echo
echo "Skills del protocolo:"
for nombre in que-toca cerrar-sesion verificar; do
    copiar "$KIT/skills/equipo/$nombre.SKILL.md" \
           "$DESTINO/.claude/skills/equipo-$nombre/SKILL.md"
    echo "OK  .claude/skills/equipo-$nombre/SKILL.md"
done

# Trato con el GitHub Project: resuelve los IDs en ejecucion (antes eran 7
# placeholders pegados a mano que nadie comprobaba) y mueve las tarjetas.
copiar "$KIT/plantillas/protocolo/tablero.py" "$DESTINO/scripts/tablero.py"
copiar "$KIT/plantillas/protocolo/test_tablero.py" "$DESTINO/scripts/test_tablero.py"

copiar "$KIT/plantillas/ci/docs_check.py" "$DESTINO/scripts/docs_check.py"
copiar "$KIT/plantillas/ci/test_docs_check.py" "$DESTINO/scripts/test_docs_check.py"
copiar "$KIT/plantillas/ci/docs-check.yml" "$DESTINO/.github/workflows/docs-check.yml"
echo "OK  guardas de deriva doc<->realidad"

# Auditoria de dependencias con allowlist caducable. El workflow se instala
# DESACTIVADO: necesita que se rellene GESTOR y que se descomente la instalacion
# de dependencias del stack. Activarlo antes de eso solo produce un rojo que no
# es una vulnerabilidad, y un rojo que no significa nada se aprende a ignorar.
copiar "$KIT/plantillas/ci/audit_check.py" "$DESTINO/scripts/audit_check.py"
copiar "$KIT/plantillas/ci/test_audit_check.py" "$DESTINO/scripts/test_audit_check.py"
copiar "$KIT/plantillas/ci/audit-allowlist.json" "$DESTINO/security/audit-allowlist.json"
if [ ! -f "$DESTINO/.github/workflows/audit.yml" ]; then
    copiar "$KIT/plantillas/ci/audit.yml" "$DESTINO/.github/workflows/audit.yml.desactivado"
else
    copiar "$KIT/plantillas/ci/audit.yml" "$DESTINO/.github/workflows/audit.yml"
fi
echo "OK  auditoria de dependencias (allowlist caducable)"

# Aviso de deriva en ramas largas. Se instala ACTIVO: no necesita configuracion
# para funcionar (el umbral tiene un valor razonable) y su unico efecto es
# comentar en PRs propios. Ajustar UMBRAL_COMMITS al ritmo del equipo.
copiar "$KIT/plantillas/ci/deriva_ramas.py" "$DESTINO/scripts/deriva_ramas.py"
copiar "$KIT/plantillas/ci/test_deriva_ramas.py" "$DESTINO/scripts/test_deriva_ramas.py"
copiar "$KIT/plantillas/ci/deriva-ramas.yml" "$DESTINO/.github/workflows/deriva-ramas.yml"
echo "OK  aviso de deriva de ramas"

# Guarda de integridad de main: solo sirve donde NO hay proteccion de rama.
# Se instala desactivada para no prometer una barrera que quiza no haga falta.
copiar "$KIT/plantillas/ci/proteccion_main.py" "$DESTINO/scripts/proteccion_main.py"
copiar "$KIT/plantillas/ci/test_proteccion_main.py" "$DESTINO/scripts/test_proteccion_main.py"
if [ ! -f "$DESTINO/.github/workflows/proteccion-main.yml" ]; then
    # Si ya la activaron (renombrada sin sufijo), no se reintroduce la desactivada.
    copiar "$KIT/plantillas/ci/proteccion-main.yml" \
           "$DESTINO/.github/workflows/proteccion-main.yml.desactivado"
else
    copiar "$KIT/plantillas/ci/proteccion-main.yml" \
           "$DESTINO/.github/workflows/proteccion-main.yml"
fi
echo "OK  guarda de integridad de main"

{ echo "# kit=$VERSION_KIT"; echo "# modo=$MODO"; cat "$PARCIAL"; } > "$MANIFIESTO"
rm -f "$PARCIAL"

if [ "$ACTUALIZAR" = 1 ]; then
    resumen_actualizacion
fi

pendiente_de_configurar
