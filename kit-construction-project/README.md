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
    ├── hooks/                  SessionStart: contexto de orientación al arrancar.
    │                           PreToolUse: recuerda secure-coding-guard al tocar
    │                           código (con su test — un hook silencioso es
    │                           indistinguible de uno roto).
    ├── ci/                     Guardas de deriva doc↔realidad para CI
    └── CLAUDE-fragmento.md     Bloque a pegar en el CLAUDE.md generado
```

> Los mecanismos del kit (hooks y guardas) llevan tests al lado y se prueban en
> los dos sentidos: que dejan pasar lo correcto y que **muerden** lo incorrecto.
> Un mecanismo que nunca se ha visto fallar no está verificado.

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

### Actualizar a una versión nueva del kit

```bash
sh /ruta/al/kit/instalar.sh /ruta/al/proyecto --actualizar
```

**Nunca se pisa un archivo que hayáis tocado.** Para saberlo no se adivina: al
instalar se registra el hash de cada archivo en `SKILLS-PORTABLE/.manifiesto`, y
al actualizar se compara.

| Estado del archivo en el destino | Qué hace |
|---|---|
| Igual que lo dejó el kit | lo actualiza |
| **Modificado por vosotros** | **lo conserva** y deja la versión nueva como `<archivo>.nuevo` |
| No existe (pieza nueva del kit) | lo trae |
| Instalación anterior a los manifiestos | conserva todo; nada se pisa |

Al terminar te lista qué actualizó y qué conservó. Para reconciliar un
conservado: compara con `git diff --no-index <archivo> <archivo>.nuevo`, traéte
lo que quieras y borra el `.nuevo` — en cuanto el archivo coincida con el del
kit, vuelve a gestionarse solo.

> **No hace falta acordarse del flag.** Si ya hay una instalación en el destino,
> el instalador pasa a modo actualización aunque repitas el comando original.
> El reflejo natural es reinstalar con el mismo comando, y que ese reflejo
> borrara la configuración del equipo era justo el fallo que esto arregla: la
> protección no puede depender de recordar una opción.

La versión del kit está en `VERSION` (fecha) y queda sellada en el manifiesto del
proyecto, así que siempre se puede saber con qué versión se instaló. Verifica el
ciclo completo con `sh test_instalar.sh` (23 casos; en Windows tarda ~1 min
porque hace varias instalaciones reales de punta a punta).

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
| `OWNER` y `PROJECT_NUMBER` (en `scripts/tablero.py`) | `SanchezIng`, `1` | dueño y número del Project (lo ves en su URL) |
| `{{PREFIJO_RAMA}}` | `{modulo}/{tarea-corta}` | convención del proyecto |
| `{{CMD_TEST}}` | `docker compose exec app ./vendor/bin/pest` | stack |
| `{{CMD_LINT}}` | `./vendor/bin/pint --test --dirty` | stack |
| `{{CMD_ESTATICO}}` | `./vendor/bin/phpstan analyse` | stack |
| `{{RUTA_BACKLOG}}` | `docs/backlog.md` | estructura de docs |
| `{{CMD_CONVERTIR_RUTA}}` | `cygpath -w <ruta>` (Windows) · `—` (Linux/macOS) | plataforma |
| `MODO_BACKLOG` (no es placeholder: constante en `scripts/docs_check.py`) | `auto` → `espejado` al terminar de espejar | ver trabajo_en_equipo.md §6 |
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
4. **Conectar el tablero:** poner `OWNER` y `PROJECT_NUMBER` en
   `scripts/tablero.py` y comprobarlo con `python3 scripts/tablero.py --comprobar`.
   Beneficio: sin esto las skills asignan el issue pero no mueven la tarjeta.
5. **Colaboradores (si hay equipo):** `gh api repos/{owner}/{repo}/collaborators/{usuario} -X PUT`
   (les llega invitación por email) y darles acceso al Project. Beneficio: cada dev
   clona y su Claude ya trae el protocolo completo.
6. **Proteger `main`** (ver sección siguiente). Beneficio: es el **único** mecanismo
   que de verdad impide mergear sin revisión; sin él, las reglas "nadie hace push
   directo" y ">=1 revisión" son texto que se cumple por buena voluntad.

Si el usuario prefiere hacerlo a mano o más tarde, respetar la decisión: mientras
`OWNER`/`PROJECT_NUMBER` sigan sin poner, `scripts/tablero.py` **para con un
mensaje que dice exactamente qué falta y dónde**, en vez de dejar el candado a
medias. Cualquier sesión futura lo detecta con `--comprobar`.

## Proteger `main`: primero averigua si puedes

**Antes de prometer nada al equipo, comprueba la disponibilidad.** No es universal:

```bash
gh api repos/{owner}/{repo}/rulesets
```

- Responde con una lista (aunque sea vacía) → **puedes**. Ve a la opción A.
- Responde `403 "Upgrade to GitHub Pro or make this repository public to enable
  this feature"` → **no puedes**: el repo es privado en plan Free. Opción B.

> Esta es la trampa que se llevó por delante al piloto: el kit exigía revisión
> humana sin decir en ningún sitio cómo se aplica ni que pudiera no estar
> disponible. Se mergearon 8 PRs sin revisar y nada lo señaló.

### Opción A — Protección de rama (preventiva: el push se rechaza)

```bash
gh api repos/{owner}/{repo}/rulesets -X POST --input - <<'JSON'
{
  "name": "main protegida",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false,
        "allowed_merge_methods": ["merge", "squash", "rebase"]
      }
    }
  ]
}
JSON
```

**Trabajando solo:** GitHub no te deja aprobar tu propio PR, así que
`required_approving_review_count: 1` te bloquea a ti mismo. Pon `0` — sigues
teniendo el PR obligatorio y el CI como puerta, que es el 80% del valor — y súbelo
a `1` en cuanto entre el segundo dev.

**Si activas esto, el proyecto debe estar en modo espejado** (candado en GitHub).
En modo "solo tablero markdown" el reclamo necesita push directo a `main` y esta
regla lo rompe. Ver `trabajo_en_equipo.md` §9.

### Opción B — Guarda de CI (detectiva: el push entra y se denuncia)

Para repos privados en plan Free. `plantillas/ci/proteccion-main.yml` +
`proteccion_main.py`: en cada push a `main`, todo commit que no venga de un PR
con al menos una aprobación deja el CI en rojo, nombrando el commit y el autor.

**No es equivalente y no hay que fingir que lo sea:**

| | Protección de rama | Guarda de CI |
|---|---|---|
| El push directo | se **rechaza** | entra, y se **denuncia** |
| Requiere | repo público o GitHub Pro | nada |
| Se puede ignorar | no | sí, si nadie mira el CI |

Configurable en la cabecera del script:

- `PREFIJOS_PERMITIDOS` — commits que sí pueden ir directos. Solo tiene sentido
  en modo sin Project, donde el tablero es el candado. Vacíalo en modo espejado.
- `EXIGIR_REVISION` — **ponlo en `False` mientras trabajes solo.** Es la misma
  trampa de la opción A: GitHub no te deja aprobar tu propio PR, así que
  exigirlo con un solo dev marca en rojo el 100% de tu trabajo y acabas
  desactivando la guarda — peor que tenerla en modo suave. Aun en `False` sigue
  exigiendo que **todo pase por PR**: diff revisable, CI ejecutado, historia
  limpia. A `True` en cuanto entre el segundo dev.

**Al activarla en un repo con historia, la primera ejecución saldrá roja** por
los commits que ya entraron directos. Es correcto y es información: o los
asumes como deuda conocida, o empiezas a contar desde ahí.

Las tres salidas para un proyecto serio, en orden: hacer el repo **público**,
pagar **GitHub Pro**, o asumir que la barrera es detectiva y no preventiva —
decisión explícita, no un olvido.

## Los IDs del Project ya no se pegan a mano

Los IDs GraphQL **no existen hasta crear el GitHub Project**, que ocurre después
de generar el kit. Antes eran siete placeholders que alguien tenía que descubrir
con una query y pegar sin equivocarse, en el momento de menos contexto del
proyecto. Y nada comprobaba después que siguieran vivos: si el Project se
recreaba, `/que-toca` fallaba **a medias** — asignaba el issue y no movía la
tarjeta, dejando al equipo creyendo que el tablero dice la verdad.

Ahora los resuelve `scripts/tablero.py` en cada ejecución. **Un ID que se
descubre no puede quedarse obsoleto.** Solo hay que poner dos datos que son
identidad, no derivables:

```python
OWNER = "MiEquipo"        # dueño del repo/Project
PROJECT_NUMBER = "1"      # lo ves en la URL del Project
```

```bash
python3 scripts/tablero.py --comprobar   # ¿está todo conectado?
python3 scripts/tablero.py --ids         # los IDs, en JSON
python3 scripts/tablero.py --mover <ITEM_ID> "En progreso"
```

Si falta configuración, si el Project no existe, si el token no tiene alcance de
Projects o si alguien **renombró una columna**, el script para y dice cuál es el
problema (y qué columnas tiene el tablero de verdad) en vez de fallar a medias.

Mover una tarjeta también pasa por aquí, y después **relee el estado para
confirmar que quedó donde debía**: que la API responda OK no significa que se
haya movido. Eso, de paso, elimina la trampa de PowerShell de la sección
siguiente — los valores viajan como variables de GraphQL, no como literales
entre comillas.

## Lecciones del piloto (ya pagadas — no las repitas)

- **`gh api graphql` con literales entre comillas falla desde PowerShell** (pierde las
  comillas → error `ID!`). *Resuelta de raíz:* todo el GraphQL del protocolo vive en
  `scripts/tablero.py`, que pasa los valores como **variables** de GraphQL en una
  lista argv. Sin literales no hay comillas que perder y da igual el shell. Si
  escribes GraphQL nuevo a mano, la lección sigue aplicando.
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
