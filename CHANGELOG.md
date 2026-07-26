# Changelog

Cambios del catálogo. Cada entrada dice **qué se rompía**, no solo qué se tocó:
un changelog que solo lista archivos no evita repetir el error.

## 2026-07-26 (6) — Se cierran los dos huecos que quedaban anotados

No son mejoras nuevas del plan: son los dos límites que las mejoras ya cerradas
dejaban por escrito, y que al resumir el kit resultaron ser los que más pesaban.

**Verificar la salida, no solo la plantilla.** `kickstart_check.py` comprueba que
la skill no prometa lo que sus plantillas no describen — eso valida la
*plantilla*. Lo que nadie validaba es la *generación*. Ejecutar Claude en CI no es
posible, así que la salida no es un `--dry-run`: es
`skills/project-kickstart/verificar_kit.py`, que se ejecuta **en el Paso 10,
antes de entregar**, y comprueba contra `.kickstart-state.json` que estén los
archivos que esa entrevista obligaba a generar (núcleo, equipo si hay 2+ devs,
ADR si es mediano/grande), que no quede ningún `{{PLACEHOLDER}}`, que los enlaces
resuelvan y que CLAUDE.md traiga sus tres secciones útiles. Verifica **el
artefacto en el momento en que se produce**, que es cuando el error todavía es
gratis. 21 casos, incluidos los que impiden acusar en falso: un placeholder
dentro de un bloque de código es un ejemplo, y un kit en inglés no se juzga con
títulos en español.

**Las guardas desactivadas dejan de depender de la memoria.** `audit.yml` y
`proteccion-main.yml` se instalan desactivadas a propósito (activarlas sin
configurar produce un rojo que no es un fallo, y un rojo que no significa nada se
aprende a ignorar). Pero "acuérdate de activarla" no es un mecanismo — es
justamente lo que este kit existe para eliminar. Ahora:

- El **hook de arranque** las lista en cada sesión, con el prerrequisito de cada
  una y el `git mv` exacto, y **desaparece solo** al decidir. También ofrece la
  otra salida: borrarla, porque dejarla ahí es una decisión sin tomar.
- `proteccion_main.py` **detecta la llegada de un segundo colaborador humano** y
  exige subir `EXIGIR_REVISION`. La excepción de trabajar en solitario existía
  porque GitHub no deja aprobar el PR propio; ahora caduca sola en vez de esperar
  a que alguien lo recuerde. Los bots no cuentan (dependabot no revisa nada), y
  si la API no responde **avisa sin tumbar el CI**: es una comprobación de
  configuración, no un veredicto de seguridad, y una falsa alarma aquí enseña a
  ignorar el rojo.

**La regla de las ~300 líneas pasa de tope a preferencia.** Superarla está bien
cuando el archivo lo pide —una máquina de estados, un parser, un test de tabla
que se lee mejor de corrido—; lo que no vale es superarla por inercia. El criterio
real es cuántas responsabilidades conviven dentro, no el número: se divide algo de
200 líneas con tres responsabilidades, y no se parte uno cohesionado de 500 solo
para cumplir la cifra, porque eso deja dos archivos que hay que leer juntos.

Diez suites, **199 casos**. La guarda de este repo se actualizó **injertando** la
mejora sin tocar su configuración propia — la lección de M-01 aplicada a mano.

## 2026-07-26 (5) — El kit da el instrumento para el problema que él crea

**M-09, y con ella el plan queda cerrado.** El kit prescribe módulos reclamables
trabajados en paralelo, y eso produce **estructuralmente** ramas de vida larga que
divergen: es consecuencia del diseño, no un accidente. Creaba la condición y no
daba el instrumento. En el piloto, un PR salió de su base el 18 y se mergeó el 22:
cuatro conflictos, y uno **no mecánico** — la rama afirmaba un estado de tarea que
ya era falso, y resolverlo a ciegas con `--theirs` habría metido una regresión
documental en `main` con el CI en verde. Fue el mayor sumidero de tiempo de la
sesión; el día 19 habría sido trivial.

`scripts/deriva_ramas.py` (programado, dos veces por semana) avisa en los PRs que
se han quedado más de N commits por detrás de su base.

Lo que decide si sirve, más que el umbral:

- **Un aviso por PR, no uno por ejecución** — el requisito que el hallazgo ponía
  por encima de todo. Comenta una vez y después **edita ese mismo comentario**: la
  cifra queda al día sin una sola notificación nueva. Un bot que avisa en cada
  pasada se filtra, y un aviso filtrado no es un aviso.
- **El aviso se corrige a sí mismo:** si la rama se pone al día, el comentario se
  actualiza para decirlo. Un aviso obsoleto también miente.
- **No poder mirar no es "no hay deriva":** si `gh` falla, si la comparación no
  trae `behind_by` o si el listado de PRs llega al tope, para y lo dice.
- El texto explica el riesgo **real** —el conflicto no mecánico, la regresión que
  ningún test cubre— y cómo salir, no solo el número.

Verificado contra los PRs reales de los dos repos del piloto: con umbral 8 detecta
tres (#126 a 8 commits por detrás, #51 a 11, #50 a 12) y deja en paz al resto; con
umbral 50 calla. La simulación (`--simular`) no tocó ningún PR. 18 casos nuevos,
con los dos modos de fallo opuestos: spamear y callar cuando debería hablar.

Por qué no basta lo nativo: *"Require branches to be up to date before merging"*
depende de la protección de rama, que en repos privados con plan Free no existe —
el mismo muro de M-03.

Con esto, las nueve mejoras del [plan](plan-mejora.md) están cerradas: los cinco
defectos que la auditoría del 25 encontró **ejecutando** el kit, y los cuatro
hallazgos de uso real que seguían siendo texto sin mecanismo.

## 2026-07-26 (4) — El audit deja de ser decorativo

**M-08.** El kit prescribía `npm audit` y compañía en el checklist de cada fase
**sin decir qué hacer cuando encuentra algo**. Quien monta el CI se topa entonces
con un dilema sin salida buena: bloqueante a secas deja el CI rojo desde el primer
día por transitivas sin fix aguas arriba —y un rojo permanente enseña a ignorar el
rojo—, y `continue-on-error` no avisa nunca. En el piloto se eligió lo segundo y
**dos `high` vivieron días en `main` con el CI en verde**, hasta que aparecieron
por casualidad auditando a mano durante un merge.

`scripts/audit_check.py` + `security/audit-allowlist.json`: lo aceptado a sabiendas
no bloquea, lo nuevo sí. Portado de la implementación de referencia ya en producción
(`portal-web-api-sunat` PR #48) y parametrizado por gestor — `npm`, `pnpm`, `yarn`,
`pip-audit`, `composer`, `cargo`.

Lo que impide que degenere en un `ignore` general es que falla en **cuatro** casos,
no solo en el obvio: vulnerabilidad sin aceptar, aceptación **caducada**, entrada
que **ya no aparece** en el audit (se arregló aguas arriba y taparía el próximo
aviso del mismo paquete) y vencimiento a **más de 180 días** (sin techo, la fecha se
pone lejana y la caducidad es humo).

Decisiones que definen el resto:

- **La clave es el aviso (GHSA/CVE/RUSTSEC), nunca el paquete.** Verificado con un
  caso real: `minimist` sale como `critical` de paquete pero uno de sus avisos es
  `moderate` — aceptar por paquete taparía el `critical`.
- **Falla cerrado**, que es lo único imperdonable aquí: si el gestor no está, si la
  salida no es JSON o si no tiene la forma esperada, para. Probado con el error real
  de `pnpm` sin lockfile, que de otro modo se habría leído como "sin
  vulnerabilidades". Un falso verde en una guarda de seguridad es peor que no
  tenerla, porque nadie vuelve a mirar.
- **"Desconocida" no es "leve".** `pip-audit` y `cargo audit` no reportan severidad;
  ahí todo aviso bloquea salvo aceptación explícita.
- **La lista nace vacía y el workflow se instala desactivado.** Activarlo sin
  rellenar el gestor produciría un rojo que no es una vulnerabilidad, que es
  literalmente cómo se aprende a ignorar el rojo.
- `--diagnostico` enseña lo que la guarda **leyó**, no lo que el comando imprimió.

Verificado de punta a punta contra dependencias vulnerables reales
(`lodash@4.17.15`, `minimist@0.0.8`) con `npm` y con `pnpm` — que coinciden en los
mismos 8 avisos: bloquea los 4 bloqueantes, los acepta al declararlos, y muerde al
caducar una entrada y al dejar una fantasma. 26 casos nuevos.

Límite dicho en voz alta: solo `npm` y `pnpm` están verificados contra la
herramienta real. `yarn`, `pip-audit`, `composer` y `cargo` van marcados como no
verificados en el código y en el README; el fallo cerrado hace que una sorpresa de
formato se note en vez de pasar por build limpia.

## 2026-07-26 (3) — El tablero se genera; el porqué se sigue escribiendo

**M-07.** El estado de una tarea vivía duplicado a mano en el Project, en
`progreso/tablero-equipo.md` y en `progreso/estado-actual.md`. En dos días de uso
real eso derivó **tres veces**; en una hubo que ir al `git log` para dirimir cuál
de las tres fuentes decía la verdad, y resolver el conflicto a ciegas habría
metido una regresión documental en `main` con el CI en verde. La redundancia solo
preserva contexto si las copias coinciden: cuando discrepan es peor que no
tenerla, porque quien lee no sabe cuál manda.

`scripts/tablero.py --generar` reescribe la tabla desde el Project. Lo que nadie
teclea no puede desviarse.

**La frontera que define el cambio:** la tabla se genera, el **log de reclamos no
se genera jamás**. La tabla es un hecho mecánico (en qué columna está algo, quién
lo tiene); el log es causalidad (por qué se atascó, qué trampa costó un intento
fallido, qué se acordó al partir un módulo). Un generador de logs produciría texto
plausible y vacío y se perdería justo lo que mejor funciona del kit. El generador
escribe solo entre marcas y conserva byte a byte lo que hay fuera.

Lo que se quitó, no solo lo que se añadió:

- **`estado-actual.md` pierde la tabla de estado por módulo** — era el espejo de un
  espejo. Se queda con lo que solo él tiene: decisiones vivas, deudas y
  convenciones que cambiaron.
- **`docs/equipo.md` pierde las columnas de estado y de "quién trabaja en qué"**,
  una tercera copia que el hallazgo original no había listado. Conserva lo que no
  cambia cada día: label, frontera, dependencias.
- `/que-toca` y `/cerrar-sesion` ya no editan la tabla: la regeneran.

Lecciones anteriores aplicadas de vuelta:

- **Nunca se pisa lo que escribió una persona** (M-01): si el archivo no lleva las
  marcas del bloque generado, se niega a tocarlo y explica cómo adoptarlo.
- **Ninguna conclusión sobre una lista truncada** (M-05): si el Project devuelve
  menos items de los que dice tener, o justo el tope, no escribe nada. Un tablero a
  medias no se lee como incompleto, se lee como si esas tareas no existieran.
- **Verificar el efecto, no la invocación:** tras escribir, relee el archivo y falla
  si no contiene el bloque.

Verificado contra el Project real del piloto (55 items): genera, es idempotente,
conserva una línea de log añadida a mano y se niega a pisar un tablero sin marcas.
Y destapó lo que un tablero a mano tapaba: **26 de las 55 tareas no llevan label
`modulo:`**, todas las posteriores al MVP. Ahora salen agrupadas bajo `(sin
módulo)`, que es la forma de que se note. 16 casos nuevos en `test_tablero.py`
(31 en total).

## 2026-07-26 (2) — La pieza más grande deja de estar sin vigilar

**M-06.** `project-kickstart` son ~2.900 líneas de prosa que nadie ejecuta: una
skill que un Claude lee para generar el kit de un proyecto nuevo. No se puede
testear la prosa, pero sí **las promesas que hace sobre sí misma**, y ninguna
estaba comprobada. `kickstart_check.py` exige que las dos listas de archivos a
generar (Paso 9 y `plantillas.md`) cuadren, que cada archivo prometido tenga
plantilla, que las rutas y enlaces existan, que las secciones citadas de otro
documento sigan ahí, y que todo `{{PLACEHOLDER}}` esté documentado.

Lo que destapó al primer intento:

- **10 placeholders reales sin documentar**, todos de `verificar.SKILL.md`
  (`{{CUANDO_NIVEL_2}}`, `{{PASO_PREPARACION}}`, `{{N_TESTS}}`…). La tabla del
  README los cubría con un "…", así que se instalaban tal cual y el proyecto
  arrancaba con `{{...}}` dentro de su runbook. Ahora tienen sus 11 filas.
- **Dos falsos positivos de la propia guarda**, corregidos antes de dar por
  bueno ningún veredicto: las cabeceras `## ARCHIVO n` no se buscaban en modo
  multilínea (no contaba ninguna, y las delegaciones tapaban el hueco) y
  `references/x.md` se resolvía siempre contra el kickstart, acusando a las
  cinco referencias legítimas de `secure-coding-guard`. Los dos con test de
  regresión: una guarda que acusa en falso se acaba desactivando.

Detalles que importan más de lo que parecen:

- **Los bloques de código no son estructura.** Un `## 4.` o un `## ARCHIVO 99:`
  dentro de un fence es un ejemplo. Sin esa distinción el kit se denunciaría a
  sí mismo por documentarse y —peor— una plantilla de ejemplo taparía la
  ausencia de la real.
- **Lección de M-05 aplicada de vuelta:** si el inventario del paquete sale
  vacío, la guarda muerde en vez de anunciar "todo OK". Un paquete que no se
  pudo leer no sostiene ninguna conclusión sobre lo que le falta.
- **Se dice lo que NO cubre:** esto valida la plantilla, no la generación. Un
  Claude que ignore la plantilla sigue pudiendo generar cualquier cosa; el
  `--dry-run` con entrevista de fixture queda pendiente y anotado.

Verificada que muerde contra el paquete **real**, no solo contra los sintéticos:
renumerar `trabajo_en_equipo.md` §9 destapa las 5 citas que quedarían mintiendo.
29 casos nuevos (`test_kickstart_check.py`), cada regla en los dos sentidos.

Y una ausencia que nadie había notado: **ninguna suite del kit se ejecutaba
sola**. El único workflow era el de protección de `main`. `.github/workflows/kit.yml`
corre las siete en cada push y PR, con las guardas antes que lo que vigilan.

## 2026-07-26 — El kit deja de depender de que alguien se acuerde

Cinco mejoras del [plan](plan-mejora.md), los tres 🔴 incluidos. El hilo común:
donde el kit tenía una regla escrita, ahora hay mecanismo probado; y donde el
mecanismo dependía de un dato pegado a mano, ahora se descubre solo.

- **M-01 · Actualizar ya no destruye la configuración.** Reinstalar sobre un
  proyecto configurado borraba los IDs del Project y los comandos del stack, en
  silencio. Eso mantenía a cada proyecto congelado en la versión con la que
  nació, porque la única vía para traerse mejoras era la que las destruía. Ahora
  hay manifiesto de hashes: lo que tocó el equipo se conserva y la versión nueva
  llega como `<archivo>.nuevo`. No depende de recordar un flag — reinstalar con
  el comando de siempre también actualiza. `VERSION` sella con qué versión se
  instaló cada proyecto.
- **M-02 · El candado de reclamo no justifica saltarse la protección de `main`.**
  El reclamo ya es instantáneo en GitHub (assignee + Project); el push del
  tablero era una segunda copia de algo ya visible, y su precio era dejar la
  rama sin proteger para siempre. Ahora el tablero viaja en el PR. Se preserva
  el matiz real: sin GitHub Project, el tablero **es** el candado y entonces
  `main` no puede protegerse del todo — un modo u otro, nunca los dos.
- **M-03 · Proteger `main`, del texto al mecanismo.** El kit exigía revisión sin
  decir cómo se configura ni que puede no estar disponible. Ahora empieza por el
  diagnóstico (`gh api …/rulesets`) y bifurca: protección de rama si se puede, o
  guarda de CI que denuncia los commits sin PR aprobado. Se dice explícitamente
  que **detectar no es prevenir**. Este repo, privado en Free, usa la detectiva.
- **M-04 · Los IDs del Project se resuelven solos.** Eran siete pegados a mano y
  nadie comprobaba que siguieran vivos; al recrear el Project, `/que-toca`
  asignaba el issue y no movía la tarjeta. `scripts/tablero.py` los descubre en
  ejecución, para con diagnóstico si algo no cuadra, y tras mover **relee** el
  estado. De paso elimina la trampa de PowerShell con GraphQL: los valores van
  como variables, no como literales entre comillas.
- **M-05 · Ningún listado decide sobre una lista truncada.** `gh` trae 30 por
  defecto y dos llamadas no pedían más. La grave: se listaban todos los issues
  para descartar los que tuvieran dueño, así que **más allá del tope parecían
  libres por ausencia de datos** — el candado dando por libre lo que otro tenía.
  Ahora filtra el servidor (`no:assignee`), con lo que una lista corta solo
  puede ocultar tareas, nunca inventarlas.

Cuatro suites nuevas o ampliadas, todas probando también que **muerden**:
`test_instalar.sh` (23), `test_tablero.py` (15), `test_proteccion_main.py` (10),
más las de docs_check (12) y el hook (9).

## 2026-07-25 — Los mecanismos del kit pasan a estar verificados

Se integran los PRs #1 y #2 (`kit-construction-project`), corrigiendo antes seis
defectos que se detectaron **ejecutándolos**, no leyéndolos.

### `secure-coding-guard` deja de depender de `/que-toca` (PR #2)

La obligación de la skill solo se ejecutaba en el paso 6.4 de `/que-toca`. Todo
trabajo que entra por otra puerta —mergear un PR, resolver conflictos, revisar
código ajeno, un hotfix, retomar tras una pausa— la saltaba en silencio.
Corrección en dos capas: hook `PreToolUse` al tocar código, y checkpoint en
`/cerrar-sesion` por si el hook se ignoró.

- **El hook de la propuesta original no funcionaba.** Leía la ruta de una
  variable de entorno inexistente (`CLAUDE_TOOL_FILE_PATH`) y escribía por
  stdout plano, que en `PreToolUse` va solo al log de depuración. Hacía
  `exit 0` en la primera línea **siempre**: se ejecutaba en cada edición sin
  hacer nada, dando el hallazgo por cerrado.
  El contrato real es: la ruta llega en el **JSON de stdin**
  (`.tool_input.file_path`, o `.tool_input.notebook_path` en `NotebookEdit`), y
  el aviso debe salir como `hookSpecificOutput.additionalContext`.
- **`NotebookEdit` no estaba cubierto** (usa `notebook_path`, no `file_path`).
- **Sin `jq`:** Git Bash en Windows no lo trae; la extracción es con `sed`.
- **El hook vivía dentro de la rama `--protocolo` del instalador**, pero
  `secure-coding-guard` se instala siempre: un proyecto en modo fábrica se
  quedaba con la skill y sin recordatorio. El hook pertenece al guardián, no al
  protocolo de equipo → se movió al bloque que corre siempre.
- **Límite conocido, documentado:** cubre `Edit|Write|NotebookEdit`. Un merge
  resuelto solo con comandos git (`git checkout --theirs`) mete código sin pasar
  por ninguna de esas herramientas; ahí la red es el checkpoint de
  `/cerrar-sesion`.

Los hallazgos de uso real salen de la carpeta del kit (viajaban a cada proyecto
instalado dentro de `SKILLS-PORTABLE/`) a [`hallazgos/`](hallazgos/) en la raíz.

### El estado del backlog vive en el Project (PR #1)

El campo `Estado:` del backlog se desfasa porque ningún automatismo lo lee: al
espejar a GitHub, el estado pasa a vivir solo en el Project. Sobre la propuesta
original se corrigieron tres falsos positivos que habrían tumbado el CI de
proyectos sanos:

| Escenario | Antes | Ahora |
|---|---|---|
| Espejado a medias (issues creados uno a uno) | CI rojo en mitad del arranque | `MODO_BACKLOG` explícito: `auto` valida lo verificable y **avisa** del resto; `espejado` es el modo estricto |
| Repo con >300 issues | acusaba de inexistentes los issues **más viejos** (las primeras tareas) | límite a 1000 + confirmación individual contra la API antes de acusar |
| Ejemplo de formato en un bloque de código | contaba como tarea real | se reutiliza el filtro de fences de la revisión de enlaces |
| `{{RUTA_BACKLOG}}` sin rellenar | traceback de Python en CI | mensaje accionable |

También se corrigió la incoherencia de `trabajo_en_equipo.md` §6: el bloque de
formato canónico seguía mostrando `- Estado:` justo encima del texto que manda
quitarlo, así que el kickstart generaba backlogs en modo legado por defecto.

### Los mecanismos ahora llevan tests

Convención nueva del catálogo: **un mecanismo que nunca se ha visto fallar no
está verificado.** Cada guarda se prueba en los dos sentidos —que deja pasar lo
correcto y que **muerde** lo incorrecto— y los tests viajan con el mecanismo al
proyecto instalado.

| Suite | Casos | Contra la versión sin corregir |
|---|---|---|
| `plantillas/ci/test_docs_check.py` (corre en CI **antes** de que la guarda juzgue el repo) | 12/12 OK | 7 fallos |
| `plantillas/hooks/test_recordar-seguridad.sh` (se instala en el proyecto) | 9/9 OK | 4 fallos |

Verificación del **efecto**, no de la invocación: una edición real vía
`claude -p` sobre un proyecto instalado por `instalar.sh` mete el aviso 2 veces
en el contexto del modelo (una como `hook_additional_context`). Con la versión
anterior: 0.

### Pendiente

Los hallazgos **2–5** siguen documentados sin implementar en
[`hallazgos/2026-07-22-aplicacion-de-reglas.md`](hallazgos/2026-07-22-aplicacion-de-reglas.md):
allowlist caducable para `npm audit`, el espejo del espejo del tablero, la
deriva de ramas largas, y la protección de rama (con la trampa de que **no
existe en repos privados con plan Free**). Los cuatro comparten el patrón que
originó todo esto: *regla declarada sin mecanismo que la aplique*.
