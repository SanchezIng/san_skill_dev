# SKILLS-PORTABLE

Paquete **autocontenido y portátil**: llévate esta carpeta entera a donde quieras
arrancar o mejorar un proyecto. No depende de nada externo ni de ninguna instalación
global — todo lo necesario está aquí dentro.

> Origen: T-111 (#123) del motor de facturación SUNAT. Las skills del protocolo se
> pilotaron ahí y se **validaron ejecutando una tarea real de punta a punta**
> (T-102/#111) antes de empaquetarlas. Las lecciones de ese uso ya están dentro.

## Contenido

```
SKILLS-PORTABLE/
├── skills/
│   ├── project-kickstart/      La fábrica: idea → kit completo de documentación.
│   │                           Ya instancia el autopilotaje de abajo (Paso 9).
│   ├── secure-coding-guard/    Guardián de seguridad (OWASP/ASVS) al escribir código.
│   └── equipo/                 Las 3 skills del protocolo, PARAMETRIZADAS:
│       ├── que-toca.SKILL.md       reclamar tarea (candado entre devs)
│       ├── cerrar-sesion.SKILL.md  cierre disciplinado (se niega con tests rojos)
│       └── verificar.SKILL.md      demostrar que funciona de verdad
└── plantillas/
    ├── hooks/                  Hook SessionStart: contexto de orientación al arrancar
    ├── ci/                     Guardas de deriva doc↔realidad para CI
    └── CLAUDE-fragmento.md     Bloque a pegar en el CLAUDE.md generado
```

## Uso

### Conseguir el kit

Vive en el repo-catálogo [san_skill_dev](https://github.com/SanchezIng/san_skill_dev),
carpeta `kit-construction-project/`. Tres formas equivalentes — el kit es autocontenido:

**A) Clonar el repo (temporal, no deja nada de más):**

```bash
cd /ruta/al/proyecto
git clone https://github.com/SanchezIng/san_skill_dev.git
sh san_skill_dev/kit-construction-project/instalar.sh .
rm -rf san_skill_dev   # el instalador ya dejó el kit en SKILLS-PORTABLE/
```

Aunque el repo tenga más skills, en el proyecto solo quedan `SKILLS-PORTABLE/` y
`.claude/skills/` — el clon completo se borra.

**B) Copiar/descargar SOLO la carpeta del kit, con cualquier nombre:**

El instalador usa su propia ruta, así que el nombre y la ubicación de la carpeta de
origen dan igual (`mi_kit/`, un ZIP descargado, un pendrive…):

```bash
sh /donde/sea/mi_kit/instalar.sh /ruta/al/proyecto
```

**C) Copiar `SKILLS-PORTABLE/` desde cualquier proyecto que ya la tenga.**

> **El único nombre que importa es el del destino:** el instalador siempre deja la
> copia dentro del proyecto como `SKILLS-PORTABLE/` — ese nombre está fijado en el
> instalador y es donde el kickstart busca sus plantillas. **No renombres esa copia.**
> La carpeta de origen, tras instalar, queda redundante: puedes borrarla.

### Lo más rápido: el instalador

```bash
sh instalar.sh /ruta/al/proyecto              # fábrica: kickstart + guardián
sh instalar.sh /ruta/al/proyecto --protocolo  # además, las 3 skills del protocolo
```

Copia todo a `.claude/skills/` del destino y deja una copia del kit ahí (el kickstart
busca sus plantillas al lado). Con `--protocolo` te lista al final los placeholders
que quedan por rellenar.

> **Regla que evita el error más común:** una skill vive en
> `.claude/skills/<nombre>/SKILL.md` — carpeta por skill, y el nombre de la carpeta
> igual al `name:` del frontmatter. Soltar los `.SKILL.md` sueltos en `.claude/skills/`
> NO funciona. El instalador ya lo hace bien.

### A) Proyecto nuevo (desde una idea)

1. Copia `skills/project-kickstart/` y `skills/secure-coding-guard/` a `.claude/skills/`
   del proyecto (o de la carpeta desde la que trabajes).
2. Deja **este paquete accesible** junto a ellas: el kickstart busca sus plantillas en
   `skills/equipo/` y `plantillas/` de este mismo paquete.
3. Di *"tengo una idea…"* e invoca `project-kickstart`. Él genera la documentación **y**
   el autopilotaje del protocolo, ya rellenado con el stack que elijas.

### B) Proyecto que ya existe (solo el protocolo)

1. Copia las 3 skills de `skills/equipo/` a `.claude/skills/` del proyecto, una carpeta
   por skill: `equipo-que-toca/SKILL.md`, `equipo-cerrar-sesion/SKILL.md`,
   `equipo-verificar/SKILL.md`.
2. Copia `plantillas/hooks/` → `.claude/hooks/` y `.claude/settings.json`.
3. Copia `plantillas/ci/` → `scripts/docs_check.py` y `.github/workflows/docs-check.yml`.
4. Pega `plantillas/CLAUDE-fragmento.md` en el `CLAUDE.md` del proyecto.
5. Rellena los placeholders (tabla abajo) y **comitéalo todo**.

## Regla de oro de la distribución

Las skills se **comitean en el repo del proyecto destino**, nunca se instalan como
skills globales. Dos razones:

1. Viajan por `git pull`: un dev nuevo clona y su Claude ya las tiene, sin instalar nada.
2. Llevan dentro valores del proyecto (IDs del Project, comandos del stack). Como skill
   global dispararían contra el proyecto equivocado.

## Placeholders a rellenar

| Placeholder | Ejemplo | De dónde sale |
|---|---|---|
| `{{OWNER}}` | `SanchezIng` | dueño del repo/Project |
| `{{PROJECT_NUMBER}}` | `1` | número del GitHub Project |
| `{{PROJECT_ID}}` | `PVT_kwHO…` | descubrimiento post-creación (ver abajo) |
| `{{STATUS_FIELD_ID}}` | `PVTSSF_lAHO…` | ídem |
| `{{OPT_DISPONIBLE}}` … `{{OPT_TERMINADO}}` | `dc541ee6` | ídem |
| `{{PREFIJO_RAMA}}` | `{modulo}/{tarea-corta}` | convención del proyecto |
| `{{CMD_TEST}}` | `docker compose exec app ./vendor/bin/pest` | stack |
| `{{CMD_LINT}}` | `./vendor/bin/pint --test --dirty` | stack |
| `{{CMD_ESTATICO}}` | `./vendor/bin/phpstan analyse` | stack |
| `{{RUTA_BACKLOG}}` | `docs/backlog.md` | estructura de docs |
| `{{SMOKE_E2E}}`, `{{AREAS_CRITICAS}}`, `{{CRITERIO_EXITO}}`… | — | el flujo real del proyecto (ver `verificar.SKILL.md`) |

## Arranque GitHub (Claude lo ejecuta, el usuario decide)

Todo el arranque de GitHub puede hacerlo Claude con `gh` — pero **SIEMPRE preguntando
primero al usuario si desea hacerlo, paso a paso**, explicando el beneficio de cada uno.
Son acciones sobre su cuenta (crear repos, issues, invitar gente): nada se ejecuta sin
su confirmación explícita, y el nombre del repo, la visibilidad y a quién invitar los
decide él.

**Beneficios de completarlo:** el candado de `/que-toca` funciona de verdad (reclamo
visible al instante para todo el equipo), el backlog y los issues quedan enlazados (la
guarda de CI puede cotejar `Done`↔issue cerrado), y cada colaborador que clona recibe
por `git pull` las skills, el protocolo y el tablero — onboarding sin instalar nada.

**Prerrequisitos (los hace el usuario, son interactivos):**

```bash
gh auth login                    # una sola vez; desde Claude Code: `! gh auth login`
gh auth refresh -s project       # TRAMPA COMÚN: el token normal NO trae scope de
                                 # Projects v2; sin esto, crear/mover tarjetas falla
```

**Secuencia (ofrecer cada paso, no ejecutarlo de golpe):**

1. **Repo:** `git init` + primer commit + `gh repo create` (preguntar nombre y
   visibilidad). Beneficio: el repo compartido es la fuente de verdad del equipo.
2. **Issues desde el backlog:** un `gh issue create` por tarea T-nnn, y añadir el
   `(#N)` resultante a la cabecera de cada tarea en el backlog. Beneficio: activa la
   guarda de coherencia backlog↔issues del CI.
3. **Project:** `gh project create` + enlazar al repo + añadir los issues como items.
   Beneficio: tablero con estados que `/que-toca` y `/cerrar-sesion` mueven solos.
4. **IDs:** correr el query de la sección siguiente y pegar los valores en
   `.claude/skills/equipo-que-toca/SKILL.md`. Beneficio: sin esto las skills asignan
   el issue pero no mueven la tarjeta.
5. **Colaboradores (si hay equipo):** `gh api repos/{owner}/{repo}/collaborators/{usuario} -X PUT`
   (les llega invitación por email) y darles acceso al Project. Beneficio: cada dev
   clona y su Claude ya trae el protocolo completo.

Si el usuario prefiere hacerlo a mano o más tarde, respetar la decisión: el paso de
los IDs queda documentado como tarea de arranque en el CLAUDE.md generado y cualquier
sesión futura lo detectará pendiente (placeholders `{{…}}` sin rellenar en `/que-toca`).

## Paso obligatorio: descubrir los IDs del Project

Los IDs GraphQL **no existen hasta crear el GitHub Project**, que ocurre después de
generar el kit. Una vez creado:

```bash
gh api graphql -f query='
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      id
      field(name: "Status") {
        ... on ProjectV2SingleSelectField { id options { id name } }
      }
    }
  }
}' -f owner=TU_USUARIO -F number=1
```

Pega los valores en `equipo-que-toca/SKILL.md`. Sin esto, `/que-toca` puede reclamar el
issue en GitHub pero no mover el estado en el tablero.

## Lecciones del piloto (ya pagadas — no las repitas)

- **`gh api graphql` con literales entre comillas falla desde PowerShell** (pierde las
  comillas → error `ID!`). Lanzarlo desde Bash.
- **Prueba que las guardas MUERDEN**, no solo que pasan en verde: rompe un enlace a
  propósito y marca una tarea `Done` con su issue abierto. Una guarda que nunca se ha
  visto fallar no está verificada.
- Cuidado al probar contra texto que vive en **otra rama**: un reemplazo que no encuentra
  su patrón es un no-op silencioso que parece éxito.
- El hook debe ser solo lectura y salir siempre con `exit 0`: si falla, rompe el arranque
  de todas las sesiones del equipo.
- **No asumas el efecto colateral, ejecútalo.** En el piloto, una afirmación "obvia" sobre
  el efecto de un error iba a escribirse en un contrato público; al comprobarla resultó
  falsa y destapó un bug real que nadie había visto.
