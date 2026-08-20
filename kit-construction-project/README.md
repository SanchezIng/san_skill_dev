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
busca sus plantillas al lado). Al terminar te dice **siempre** qué queda por
configurar a mano y qué placeholders siguen sin rellenar — también si el destino ya
tenía el kit, que es cuando el instalador pasa solo a modo actualización. Durante un
tiempo ese repaso se perdía justo ahí, y esas dos líneas seguidas eran la forma más
rápida de perderlo.

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
| Instalación anterior a los manifiestos (o sin `SKILLS-PORTABLE/`) | conserva todo; nada se pisa, y lo que le falte del kit sí llega |

Al terminar te lista qué actualizó y qué conservó. Para reconciliar un
conservado: compara con `git diff --no-index <archivo> <archivo>.nuevo`, traéte
lo que quieras y borra el `.nuevo` — en cuanto el archivo coincida con el del
kit, vuelve a gestionarse solo.

> **No hace falta acordarse del flag.** Si ya hay una instalación en el destino,
> el instalador pasa a modo actualización aunque repitas el comando original.
> El reflejo natural es reinstalar con el mismo comando, y que ese reflejo
> borrara la configuración del equipo era justo el fallo que esto arregla: la
> protección no puede depender de recordar una opción.
>
> **Y «ya hay una instalación» no significa «hay una carpeta `SKILLS-PORTABLE/`».**
> Se buscan los archivos que el instalador escribe siempre, porque los proyectos
> instalados antes de que esa carpeta existiera —o donde alguien la borró, que es
> lo que este mismo README recomienda— no la tienen. Hasta el 2026-08-06 esos
> proyectos se trataban como destino virgen, que es la única forma que había de
> perder la configuración.

La versión del kit está en `VERSION` (fecha) y queda sellada en el manifiesto del
proyecto, así que siempre se puede saber con qué versión se instaló. Verifica el
ciclo completo con `sh test_instalar.sh` (44 casos; en Windows tarda ~3 min
porque hace varias instalaciones reales de punta a punta).

### Saber en qué se ha desviado un proyecto (detector de deriva)

```bash
python3 /ruta/al/kit/deriva_kit.py /ruta/al/proyecto [más proyectos...]
python3 /ruta/al/kit/deriva_kit.py --resumen /ruta/a/proy1 /ruta/a/proy2
```

El kit viaja por copia, así que las dos copias evolucionan por su cuenta y nadie
se entera. Pasó dos veces: una deriva de 15 archivos que se descubrió de
casualidad, y un port que se creyó completo y dejó `plantillas/hooks/arranque.sh`
atrasado tres días. Las dos veces el problema no fue portar mal — fue **no poder
preguntar**. Esto responde en segundos.

| Marca | Significa |
|---|---|
| `=` | idéntico al kit |
| `~` | **solo configuración**: la única diferencia son los `{{PLACEHOLDERS}}` rellenados |
| `!` | divergente de verdad, con cuántas líneas no se explican por configuración |
| `-` | el kit lo instala y el proyecto no lo tiene |

Distinguir `~` de `!` es todo el valor: sin eso, las piezas más importantes —las
3 skills, `tablero.py`, `audit_check.py`— saldrían siempre en rojo por tener
placeholders, y un informe que siempre está en rojo se aprende a ignorar.

Para saber qué escribe el kit **no duplica el mapa de archivos**: lo instala en un
temporal y lee el manifiesto que deja el propio instalador. Un detector de deriva
que copia el mapa acaba derivando él mismo.

Sale 1 si hay divergencia real, pero **no es una guarda de CI**: un proyecto vivo
siempre tendrá divergencia legítima (barber-king fusionó `docs-check.yml` dentro
de su `ci.yml` a propósito). Se ejecuta a mano: antes de portar, después de
portar, y antes de creerse que algo está sincronizado. Sus tests:
`python3 test_deriva_kit.py`.

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
| `OWNER` y `PROJECT_NUMBER` — en `scripts/tablero.py` **y también** en `equipo-que-toca/SKILL.md` (×6) y `equipo-cerrar-sesion/SKILL.md` (×2) | `SanchezIng`, `1` | dueño y número del Project (lo ves en su URL). `scripts/estado.py` NO los declara: los importa de `tablero.py`. Rellenar solo el script deja las skills del candado con un `gh project item-list {{PROJECT_NUMBER}}` inválido — y el fallo aparece al reclamar, no al configurar |
| `{{PREFIJO_RAMA}}` | `{modulo}/{tarea-corta}` | convención del proyecto |
| `{{CMD_TEST}}` | `docker compose exec app ./vendor/bin/pest` | stack |
| `{{CMD_LINT}}` | `./vendor/bin/pint --test --dirty` | stack |
| `{{CMD_ESTATICO}}` | `./vendor/bin/phpstan analyse` | stack |
| `{{RUTA_BACKLOG}}` | `docs/backlog.md` | estructura de docs |
| `{{CMD_CONVERTIR_RUTA}}` | `cygpath -w <ruta>` (Windows) · `—` (Linux/macOS) | plataforma |
| `MODO_BACKLOG` (no es placeholder: constante en `scripts/docs_check.py`) | `auto` → `espejado` al terminar de espejar | ver trabajo_en_equipo.md §6 |
| `{{GESTOR_PAQUETES}}` (en `scripts/audit_check.py`) | `npm`, `pnpm`, `yarn`, `pip-audit`, `composer`, `cargo` | gestor de paquetes del stack |

Los de `verificar.SKILL.md` describen el runbook real del proyecto y van todos
en ese archivo. Si un nivel no aplica, **bórralo entero** en vez de dejar sus
placeholders: un runbook con pasos falsos es peor que no tenerlo.

| Placeholder | Ejemplo | De dónde sale |
|---|---|---|
| `{{AREAS_CRITICAS}}` | `pagos, firma XML` | zonas donde un fallo silencioso duele |
| `{{NOTAS_ENTORNO}}` | `Windows: docker compose solo desde PowerShell` | trampas del entorno (o línea vacía) |
| `{{CMD_LEVANTAR_STACK}}` | `docker compose up -d` | stack |
| `{{N_TESTS}}` y `{{DURACION_SUITE}}` | `142`, `50 s` | referencia sana de la suite verde |
| `{{CUANDO_NIVEL_2}}` y `{{CUANDO_NIVEL_3}}` | `si tocaste API o DB`, `si tocaste UI` | cuándo amerita subir de nivel |
| `{{CMD_SEMBRAR_DEMO}}` | `php artisan db:seed --class=DemoSeeder` | stack |
| `{{SMOKE_E2E}}` | `./scripts/smoke.sh` | el E2E real del proyecto |
| `{{DESCRIPCION_SMOKE}}` | `cubre alta→emisión; NO cubre anulación` | qué cubre y qué **no** |
| `{{PASO_PREPARACION}}` | `iniciar sesión como admin` | el flujo manual |
| `{{EJEMPLO_LLAMADA}}` | `curl -X POST localhost:8000/api/facturas -d @demo.json` | el camino que se ejercita |
| `{{CRITERIO_EXITO}}` | `HTTP 201 y el XML firmado en storage/` | observable, no "funciona bien" |

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
2. **Issues desde el backlog:** un `gh issue create` por tarea T-nnn **con su label
   `modulo:X`** (`--label modulo:A`), y añadir el `(#N)` resultante a la cabecera de
   cada tarea en el backlog. Beneficio: activa la guarda de coherencia backlog↔issues
   del CI, y es el label que agrupa el tablero generado (sin él, la tarea sale bajo
   `(sin módulo)`).
3. **Project:** `gh project create` + enlazar al repo + añadir los issues como items.
   Beneficio: tablero con estados que `/que-toca` y `/cerrar-sesion` mueven solos.
4. **Conectar el tablero:** poner `OWNER` y `PROJECT_NUMBER` en
   `scripts/tablero.py`, comprobarlo con `python3 scripts/tablero.py --comprobar` y
   generarlo por primera vez con `--generar`. Beneficio: sin esto las skills asignan
   el issue pero no mueven la tarjeta, y el tablero del repo no refleja nada.
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
python3 scripts/tablero.py --generar     # reescribe progreso/tablero-equipo.md
```

Si falta configuración, si el Project no existe, si el token no tiene alcance de
Projects o si alguien **renombró una columna**, el script para y dice cuál es el
problema (y qué columnas tiene el tablero de verdad) en vez de fallar a medias.

## El tablero se genera; el log de reclamos jamás

El estado de una tarea vivía duplicado a mano en el Project y en
`progreso/tablero-equipo.md`. En dos días de uso real eso derivó **tres veces**, y
una de ellas hubo que ir al `git log` para dirimir cuál de las tres fuentes decía
la verdad. Lo que nadie teclea no puede desviarse: `--generar` reescribe la tabla
desde el Project.

Lo que **no** se genera nunca es el log de reclamos, y esa frontera importa:

| Se genera | No se genera jamás |
|---|---|
| En qué columna está una tarea | Por qué se atascó |
| Quién la tiene asignada | Qué trampa costó un intento fallido |
| Cuántas quedan abiertas por módulo | Qué acuerdo se tomó al partir un módulo |

La tabla es un hecho mecánico; el log es causalidad. Un generador de logs
produciría texto plausible y vacío, y se perdería justo lo que mejor funciona.

Detalles que evitan sorpresas:

- El módulo de cada tarea sale del **label `modulo:X`** del issue. Las que no lo
  llevan no desaparecen: caen en `(sin módulo)`, que es la forma de que se note.
- Solo se listan las tareas **abiertas**; de las terminadas se da el número. Está
  dicho en el propio archivo, que es lo que separa un resumen de una lista que miente.
- Si el listado del Project viene **recortado**, no escribe nada: un tablero a medias
  no se lee como incompleto, se lee como si esas tareas no existieran.
- Si el archivo **no lleva las marcas** del bloque generado (tablero heredado, escrito
  a mano), se niega a tocarlo y explica cómo adoptarlo. Nunca pisa lo que escribió una
  persona.
- **Sin GitHub Project no hay de dónde generar:** ahí la tabla se mantiene a mano y es
  el candado del equipo (ver `trabajo_en_equipo.md` §9).

Mover una tarjeta también pasa por aquí, y después **relee el estado para
confirmar que quedó donde debía**: que la API responda OK no significa que se
haya movido. Eso, de paso, elimina la trampa de PowerShell de la sección
siguiente — los valores viajan como variables de GraphQL, no como literales
entre comillas.

## Auditoría de dependencias: allowlist caducable

El kit prescribía `npm audit` y compañía **sin decir qué hacer con el resultado**.
Eso deja al equipo ante un dilema sin salida buena: bloqueante a secas → el CI
queda rojo desde el primer día por transitivas sin fix aguas arriba, y un rojo
permanente enseña a ignorar el rojo; `continue-on-error` → no avisa de nada nunca.
En el piloto se eligió lo segundo y **dos `high` vivieron días en `main` con el CI
en verde**, hasta que aparecieron por casualidad auditando a mano en un merge.

`scripts/audit_check.py` + `security/audit-allowlist.json`: lo aceptado a sabiendas
no bloquea, lo nuevo sí.

```bash
python3 scripts/audit_check.py                # la guarda (exit 1 si falla)
python3 scripts/audit_check.py --diagnostico  # qué ha leído, sin juzgar
```

Falla en **cuatro** casos, y son los tres últimos los que impiden que degenere en
un `ignore` general con más pasos:

| Falla cuando | Por qué |
|---|---|
| Hay una vulnerabilidad bloqueante sin aceptar | lo nuevo para en seco |
| Una aceptación **caducó** | sin caducidad, una excepción es permanente y deja de ser excepción |
| Una entrada **ya no aparece** en el audit | se arregló aguas arriba; si se queda, tapa el próximo aviso de ese paquete |
| Una fecha vence a **más de 180 días** | sin techo, se pone un año lejano y la caducidad es humo |

Reglas al usarla:

- La clave es el **identificador del aviso** (GHSA/CVE/RUSTSEC), nunca el paquete.
- Cada entrada declara **motivo** (por qué no nos afecta y **cómo se comprobó**) y
  **seguimiento** (el issue donde vive la reevaluación). "No aplica" no es motivo.
- La lista nace vacía y el workflow se instala **desactivado**: hay que rellenar
  `GESTOR` y el paso de instalación de dependencias del stack. Activarlo antes solo
  produce un rojo que no es una vulnerabilidad.
- **Falla cerrado.** Si el gestor no está, si la salida no es JSON o si no tiene la
  forma esperada, para. No auditar no es lo mismo que no tener vulnerabilidades, y
  un falso verde en una guarda de seguridad es peor que no tenerla.
- Donde el audit **no reporta severidad** (`pip-audit`, `cargo audit`), todo aviso
  bloquea salvo aceptación explícita: "desconocida" no es "leve".

Adaptadores: `npm` y `pnpm` están **verificados contra la salida real** de la
herramienta; `yarn`, `pip-audit`, `composer` y `cargo` están escritos contra el
formato documentado y **sin verificar** — corre `--diagnostico` la primera vez y
compara con la salida cruda del comando. Añadir uno nuevo son dos cosas: el comando
que saca JSON y una función que lo normalice, que debe **lanzar** si no reconoce la
forma, nunca devolver una lista vacía.

## Deriva de ramas: el kit crea la condición, así que da el instrumento

Módulos reclamables trabajados en paralelo producen **estructuralmente** ramas de
vida larga que divergen. En el piloto, un PR salió de su base el día 18 y se
mergeó el 22: cuatro conflictos, y uno **no mecánico** — la rama afirmaba un
estado de tarea que ya era falso, y resolverlo a ciegas con `--theirs` habría
metido una regresión documental en `main` **con el CI en verde**. Fue el mayor
sumidero de tiempo de la sesión; el día 19 habría sido trivial.

```bash
python3 scripts/deriva_ramas.py --simular   # qué haría, sin tocar nada
python3 scripts/deriva_ramas.py             # comenta donde toque
```

Lo que hace que sirva, más que el umbral:

- **Un aviso por PR, no uno por ejecución.** Comenta una vez y después **edita**
  ese mismo comentario: la cifra queda al día sin una sola notificación nueva. Un
  bot que avisa en cada pasada se filtra, y un aviso filtrado no es un aviso.
- **El aviso se corrige a sí mismo.** Si la rama se pone al día, el comentario se
  actualiza para decirlo. Un aviso obsoleto también miente.
- **No bloquea nada** (corre en `schedule`), pero **falla ruidosamente si no pudo
  mirar**: que no haya avisos hoy no puede significar "no he podido consultar los PRs".
- El texto explica el riesgo real —el conflicto no mecánico— y cómo salir, no solo
  el número.

`UMBRAL_COMMITS` se ajusta al ritmo del equipo: el número bueno es el que produce
avisos que la gente lee. Si nadie hace caso, está bajo; si aparecen conflictos sin
aviso previo, está alto.

Por qué no basta la opción nativa: *"Require branches to be up to date before
merging"* depende de la **protección de rama**, que en repos privados con plan Free
no existe (ver la sección de proteger `main`).

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
