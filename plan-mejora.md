# Plan de mejora — `kit-construction-project`

Objetivo: que el kit sostenga **proyectos serios de larga vida**, no solo MVPs.
Criterio transversal, heredado de los hallazgos: *una regla sin mecanismo que la
aplique no está resuelta, y un mecanismo al que no se le ha visto **morder** no
está verificado.*

Estado: `pendiente` · `en curso` · `hecho` · `descartado`.
Origen: `auditoría 2026-07-25` (verificado ejecutando) o `hallazgo N` (de
[`hallazgos/2026-07-22-aplicacion-de-reglas.md`](hallazgos/2026-07-22-aplicacion-de-reglas.md)).

## Dónde estamos (al 2026-07-26)

| | Mejora | Estado |
|---|---|---|
| M-01 🔴 | Ruta de actualización del kit | hecho |
| M-02 🔴 | Push a `main` vs proteger la rama | hecho |
| M-03 🔴 | Protección de rama: del texto al mecanismo | hecho en el kit; activada aquí en modo detectivo |
| M-04 🟠 | IDs del Project sin validar | hecho |
| M-05 🟠 | Límites de paginación que mienten | hecho |
| M-06 🟠 | Smoke test de la salida del kickstart | hecho (camino 2; el 1 queda anotado) |
| M-07 🟠 | Tablero generado en vez de a mano (hallazgo 3) | hecho |
| M-08 🟠 | Allowlist caducable para `audit` (hallazgo 2) | hecho |
| M-09 🟠 | Deriva de ramas largas (hallazgo 4) | hecho |

**Las nueve están cerradas.** Los tres hallazgos que quedaban sin implementar
(2, 3 y 4) tienen ya su mecanismo, y los cinco defectos de la auditoría del
2026-07-25 están corregidos.

Todo el trabajo está **commiteado en local y sin publicar**:
`git log origin/main..HEAD`. Quedan dos cosas por decidir antes de publicar:

1. La nota abierta de **M-03**: la primera ejecución de la guarda de integridad
   saldrá roja por los commits que ya entraron directos a `main`. Asumirlos como
   deuda conocida o empezar a contar desde ese punto.
2. Los commits de M-06 a M-09 viven en la rama `feat/smoke-test-kickstart`, no en
   `main`: el propio kit dice que todo entra por PR.

Lo que sigue abierto **dentro** de mejoras ya cerradas, dicho donde toca y no
escondido: el `--dry-run` del kickstart (M-06, camino 1), la ventana entre dos
generaciones del tablero (M-07) y los cuatro adaptadores de audit sin verificar
contra su herramienta real (M-08).

Para retomar: todas las suites deben estar verdes antes de tocar nada. Las corre
enteras `.github/workflows/kit.yml`; en local, sus nueve pasos.

---

## M-01 · 🔴 Ruta de actualización del kit (hoy reinstalar borra la config)

**Estado:** hecho (2026-07-26) · **Origen:** auditoría 2026-07-25 (reproducido)

Reinstalar `instalar.sh --protocolo` sobre un proyecto ya configurado
**sobrescribe** `.claude/skills/equipo-*/SKILL.md` y borra los IDs del Project y
los comandos del stack ya rellenados. Ocurre en silencio, con exit 0 y mensajes
"OK". El fallo posterior es peor que el borrado: `/que-toca` asigna el issue
(paso 4 funciona) y luego falla al mover la tarjeta — candado a medias.

Consecuencia estructural: **ninguna mejora del kit llega a los proyectos ya
instalados**, porque la única vía para traérsela destruye su configuración.

- [x] Sello de versión (`VERSION`, por fecha) + sellado en el manifiesto del
      proyecto instalado, con la versión previa y la nueva al actualizar.
- [x] `instalar.sh --actualizar`. **Se descartó la heurística de placeholders**
      del plan original: no habría protegido la configuración que no son
      placeholders (las constantes de `proteccion_main.py`, por ejemplo). En su
      lugar, manifiesto de hashes (`git hash-object`, portable y ya disponible):
      se compara lo que hay contra lo que el kit escribió.
- [x] Lo modificado se conserva y la versión nueva llega como `<archivo>.nuevo`,
      con instrucciones de reconciliación. Al reconciliar vuelve a gestionarse solo.
- [x] Instalaciones anteriores a los manifiestos: no se pisa nada y se explica.
- [x] **No depende de acordarse del flag:** si ya hay instalación, repetir el
      comando original también actualiza. El reflejo de reinstalar era justo lo
      que borraba la configuración.
- [x] `test_instalar.sh`, 23 casos sobre el ciclo real (instalar → configurar →
      versión nueva → actualizar ×2 → reconciliar).
- [x] Verificado que muerde: con el instalador anterior la config se borra; con
      el nuevo sobrevive.
- [x] Bug encontrado por los propios tests: al conservar un archivo se registraba
      el hash del **equipo**, así que la siguiente actualización lo veía "intacto"
      y lo pisaba — la config sobrevivía una vez y moría a la segunda. El
      manifiesto registra lo que escribió el **kit**, no lo que hay en disco.

Coste conocido: una instalación pasa de ~1 s a ~5 s en Windows (una llamada a
`git hash-object` por archivo). Aceptable para algo que se ejecuta una vez.

## M-02 · 🔴 `/que-toca` empuja a `main` y eso choca con proteger la rama

**Estado:** hecho (2026-07-25) · **Origen:** auditoría 2026-07-25

`que-toca.SKILL.md` paso 5 y `cerrar-sesion.SKILL.md` paso 4 hacen
`git push origin main`. `trabajo_en_equipo.md` §9.1 lo declara "única excepción"
porque *"el reclamo debe ser visible al instante"*. Pero el reclamo **ya se echó
en el paso 4, en GitHub** (assignee + Project): el push es una segunda copia de
algo ya visible. El kit lo reconoce en §3: *"GitHub es la verdad para tareas;
tablero-equipo.md queda como resumen rápido"*.

Efecto real: al activar protección de rama —lo que pide M-03— la skill central
del protocolo deja de funcionar. Las dos recomendaciones del kit son
incompatibles y nadie lo detectó porque la protección nunca se configuró.

Matiz que hay que preservar: **en un proyecto sin GitHub Project el tablero SÍ
es el candado**, y ahí el push directo es obligatorio. La regla debe enunciarse
por modo, no en general.

- [x] `que-toca`: el espejo del tablero viaja en la rama de la tarea, no a `main`.
      Pasos renumerados (la rama se crea antes del espejo) y cabecera que declara
      dónde está el candado.
- [x] `cerrar-sesion`: paso 4 separa "mover el Project" (siempre) de "actualizar el
      tablero" (en el PR).
- [x] `trabajo_en_equipo.md` §9.1: tabla de los dos modos con la incompatibilidad
      dicha en voz alta.
- [x] `CLAUDE-fragmento.md`: era el sitio más leído y seguía enunciando la excepción
      vieja; ahora dice "todo entra por PR, sin excepciones" + el matiz del modo local.
- [x] Ningún archivo del kit recomienda a la vez proteger `main` y empujar a `main`:
      los dos `push origin main` que quedan están dentro de la excepción declarada.
- [x] Corregido de paso un bug del modo sin Project: publicar el tablero después de
      crear la rama haría `git push origin main` desde la rama, empujando el `main`
      local sin el commit. Ahora se hace antes de crear la rama, estando en `main`.

## M-03 · 🔴 Protección de rama: del texto al mecanismo

**Estado:** hecho en el kit (2026-07-26); pendiente aplicarlo a este repo ·
**Origen:** hallazgo 5 · **Depende de:** M-02

El kit afirma *"nadie hace push directo a main"* y *">=1 revisión humana"* sin
decir en ningún sitio cómo se configura, ni que **no existe en repos privados
con plan Free**. En el piloto se mergearon 8 PRs sin revisión y nada lo impidió.

Confirmado contra este repo (`SanchezIng/san_skill_dev`, privado en Free):
`gh api repos/{owner}/{repo}/rulesets` → `403 "Upgrade to GitHub Pro or make
this repository public to enable this feature"`. Ni rulesets ni protección de
rama legada.

- [x] Sección "Proteger `main`" en el README: **primero el diagnóstico**
      (`gh api …/rulesets`), luego la opción que toque.
- [x] Opción A (preventiva): ruleset completo por `gh api`, con la trampa de
      trabajar solo (GitHub no deja aprobar tu propio PR → `count: 0`).
- [x] Opción B (detectiva): `proteccion-main.yml` + `proteccion_main.py`, que
      denuncia en CI todo commit que llegue a `main` sin PR aprobado. Se instala
      **desactivado** (`.desactivado`) para no prometer una barrera que quizá no
      haga falta. 8 tests, ambos sentidos.
- [x] Tabla explícita de que **detectar no es prevenir**: no se finge equivalencia.
- [x] `trabajo_en_equipo.md` §9.2 deja de enunciar la regla a secas y apunta al
      mecanismo, con el diagnóstico previo.
- [x] **Decidido: opción B** (barrera detectiva) — el repo sigue privado y sin
      coste. Guarda instalada en `scripts/` + `.github/workflows/`, configurada
      para este repo: sin excepciones (`PREFIJOS_PERMITIDOS = ()`) y
      `EXIGIR_REVISION = False` mientras se trabaje en solitario, porque GitHub
      no deja aprobar el PR propio. **Subir a `True` al entrar un segundo dev.**
- [x] Verificada contra el historial real: detecta `5e4ba57` como push directo.
- [ ] Al publicar, la primera ejecución saldrá roja por los commits ya
      existentes que entraron directos. Decidir: asumirlos como deuda conocida
      o empezar a contar desde ese punto.

## M-04 · 🟠 El candado depende de IDs pegados a mano, sin validación

**Estado:** hecho (2026-07-26) · **Origen:** auditoría 2026-07-25

`/que-toca` llevaba **7** IDs de GraphQL pegados a mano. Nada comprobaba que
siguieran vivos: si el Project se recreaba, cambiaban y la skill fallaba a
medias — asignaba el issue (`gh issue edit` no necesita IDs) y no movía la
tarjeta. Un candado a medias es peor que ninguno: el equipo cree que el tablero
dice la verdad.

Se eligió **eliminarlos** en vez de validarlos: un ID que se descubre en
ejecución no puede quedarse obsoleto. Coste: una llamada a la API por
invocación.

- [x] `plantillas/protocolo/tablero.py` resuelve projectId, fieldId y las
      opciones por nombre. Funciona con Projects de usuario y de organización.
- [x] Quedan solo 2 datos a mano (`OWNER`, `PROJECT_NUMBER`): son identidad, no
      derivables. Sin ellos el script **para** y dice exactamente qué falta.
- [x] Para con diagnóstico útil ante: Project inexistente, sin alcance de
      Projects en el token, campo `Status` renombrado, o **columna renombrada**
      (dice cuál falta y cuáles existen de verdad).
- [x] **La mutación también vive ahí**, con variables de GraphQL en vez de
      literales: elimina de raíz la trampa de PowerShell que el kit tenía
      documentada como lección pagada.
- [x] Tras mover, **relee el estado** y falla si la tarjeta no quedó donde debía
      — la regla de `/verificar` aplicada al propio protocolo.
- [x] 15 tests, incluido el falso éxito exacto: la API responde OK y la tarjeta
      no se movió.
- [x] Verificado contra el **Project real** del piloto: resuelve
      `Motor Facturación SUNAT — MVP` y sus 5 columnas.

## M-05 · 🟠 Límites de paginación que mienten en silencio

**Estado:** hecho (2026-07-26) · **Origen:** auditoría 2026-07-25

`gh project item-list --limit 50` en `/que-toca`: misma clase de bug que el
`--limit 300` corregido en `docs_check.py`. Pero al auditar apareció algo peor:
**dos llamadas a `gh issue list` sin `--limit` ninguno**, y el valor por defecto
de `gh` es **30** (verificado en `gh issue list --help`).

La grave era `gh issue list --state open --json number,title,assignees`: se
pedían *todos* los issues para descartar aquí los que tuvieran dueño. Cortada a
30, las tareas de más allá del tope **parecían sin assignee por ausencia de
datos** → `/que-toca` podía dar por libre una tarea que otro dev ya tenía. Es
decir, el tope silencioso rompía el candado, que es la razón de ser de la skill.

- [x] Auditados todos los listados del kit: ninguno queda sin `--limit`
      explícito (500 en Project e issues, 200 en "mis tareas", 1000 en
      `docs_check`).
- [x] **El filtro pasa al servidor** (`--search "no:assignee"`) en vez de
      traérselo todo y filtrar en local. Esto invierte la dirección del fallo:
      una lista truncada ya solo puede **ocultar** tareas libres, nunca
      inventarlas. De "dos devs sobre la misma tarea" a "hoy ves menos opciones".
- [x] Regla de truncado explícita en el paso 3: si la cuenta iguala el `--limit`,
      hay más — subir y repetir, nunca decidir sobre una lista cortada.
- [x] La lección, generalizada, entra en `verificar.SKILL.md` como **cuarta
      trampa** junto a las tres de shell: toda herramienta que lista tiene tope y
      no avisa, y las conclusiones de tipo "no hay ninguno" son justo las que una
      lista recortada no puede sostener. Y una línea en `CLAUDE-fragmento.md`.
- [x] De paso: el instalador copiaba `__pycache__` a los proyectos destino.

## M-06 · 🟠 La pieza más grande no tiene ninguna comprobación

**Estado:** hecho (2026-07-26) · **Origen:** auditoría 2026-07-25

`project-kickstart` son ~2.900 líneas (SKILL.md + 9 referencias) sin ninguna
verificación. Es prosa y no se testea directa, pero **sus promesas sobre sí
misma sí**: hoy nada impedía que la skill prometiera un archivo que ninguna
plantilla describe, apuntara a una sección renumerada o dejara placeholders que
nadie sabe que hay que rellenar. Y es la pieza que todo proyecto nuevo toca
primero.

Se hizo el **camino 2** (comprobar la plantilla). El 1 (`--dry-run` con una
entrevista de fixture) queda pendiente y anotado como límite en la cabecera de
la propia guarda: esto valida la plantilla, **no la generación** — un Claude que
ignore la plantilla sigue pudiendo generar cualquier cosa.

- [x] `kickstart_check.py`: siete reglas sobre el paquete — las dos listas de
      archivos a generar (Paso 9 ↔ `plantillas.md`) cuadran en número y ruta;
      cada archivo prometido tiene plantilla o delegación que resuelve; las
      rutas `<paquete>/…` que declara el Paso 9 existen; enlaces relativos y
      `references/*.md` resuelven; el inventario de `references/` cuadra con la
      lista de SKILL.md; las secciones numeradas que un documento cita de otro
      existen; y todo `{{PLACEHOLDER}}` está documentado en la tabla del README
      (y al revés: lo documentado se sigue usando).
- [x] Fences respetados en las dos direcciones: una cabecera `## 4.` o
      `## ARCHIVO 99:` **dentro** de un bloque es un ejemplo, no estructura. Sin
      esto el kit se denunciaría a sí mismo por documentarse — y, peor, una
      plantilla de ejemplo taparía la ausencia de la real.
- [x] Lección de M-05 aplicada: si el inventario sale vacío la guarda **muerde**
      en vez de anunciar "todo OK". Un paquete que no se pudo leer no sostiene
      ninguna conclusión de ausencia.
- [x] `test_kickstart_check.py`, 29 casos sobre paquetes sintéticos, cada regla
      en los dos sentidos.
- [x] **Verificada que muerde contra el paquete real**, no solo contra los
      sintéticos: renumerar `trabajo_en_equipo.md` §9 destapa las 5 citas reales
      que quedarían mintiendo (README, dos skills, `plantillas.md` y
      `proteccion_main.py`).
- [x] Encontró 10 placeholders reales de `verificar.SKILL.md`
      (`{{CUANDO_NIVEL_2}}`, `{{PASO_PREPARACION}}`, `{{N_TESTS}}`…) que la
      tabla del README cubría con un "…". Se instalaban tal cual y nadie sabía
      que había que rellenarlos. README completado con sus 11 filas.
- [x] Dos falsos positivos propios corregidos antes de dar nada por bueno: las
      cabeceras `## ARCHIVO n` no se buscaban en modo multilínea (ninguna
      contaba), y `references/x.md` se resolvía siempre contra el kickstart, con
      lo que acusaba a las cinco referencias legítimas de `secure-coding-guard`.
      Ambos con test de regresión.
- [x] `.github/workflows/kit.yml`: las siete suites del kit corren en cada push
      y PR. Antes solo existía el workflow de protección de `main`, así que
      ninguna suite se ejecutaba sola.

## M-07 · 🟠 El tablero se mantiene a mano siendo un espejo

**Estado:** hecho (2026-07-26) · **Origen:** hallazgo 3 · **Relacionado:** M-02

Project (verdad) → tablero (resumen) → `estado-actual` (espejo del tablero), los
dos últimos a mano. En el piloto produjo deriva tres veces en dos días; una de
ellas hubo que ir al `git log` para dirimir cuál de las tres fuentes decía la
verdad, y resolver el conflicto a ciegas habría metido una regresión documental
en `main` con el CI en verde.

Se tomó el camino **preferido** del hallazgo (generar), no el mínimo (una guarda
que avisa después de romperlo).

- [x] `tablero.py --generar` reescribe la tabla desde el Project: módulos
      (agregado) y tareas abiertas. Determinista — el mismo Project produce el
      mismo texto, así que regenerar no ensucia el diff.
- [x] **El log de reclamos no se genera jamás**, y es una frontera declarada en
      el propio archivo, en el README y en `CLAUDE-fragmento.md`: la tabla es un
      hecho mecánico, el log es causalidad. El generador escribe solo entre
      marcas y **conserva byte a byte** lo que hay fuera.
- [x] Si el archivo **no lleva marcas** (tablero heredado, escrito a mano), se
      niega a tocarlo y explica cómo adoptarlo. Misma lección que M-01: nunca se
      pisa en silencio lo que escribió una persona.
- [x] Lección de M-05 otra vez: si el listado del Project viene recortado
      (`totalCount` > lo recibido, o justo el tope) **no escribe nada**. Un
      tablero a medias no se lee como incompleto, se lee como si esas tareas no
      existieran.
- [x] Tras escribir, **relee el archivo** y falla si no contiene el bloque — la
      regla de `/verificar` aplicada al propio protocolo, igual que en `--mover`.
- [x] `estado-actual.md` pierde la tabla de estado por módulo (era el espejo del
      espejo) y se queda con lo que solo él tiene: decisiones vivas, deudas y
      convenciones que cambiaron. Corregido en `trabajo_en_equipo.md` §5 y §11,
      en `SKILL.md` y en `cerrar-sesion.SKILL.md`.
- [x] **Tercera copia que el hallazgo no listaba:** `docs/equipo.md` también
      llevaba columna de estado y de "quién trabaja en qué". Se queda con lo que
      no cambia cada día (label, frontera, dependencias).
- [x] `/que-toca` y `/cerrar-sesion` ya no editan la tabla: la regeneran.
- [x] 16 casos nuevos en `test_tablero.py` (31 en total), incluidos los dos que
      de verdad importan: que el log escrito a mano sobrevive a regenerar, y que
      un tablero sin marcas no se pisa.
- [x] **Verificado contra el Project real** del piloto (55 items): resuelve
      `Motor Facturación SUNAT — MVP`, genera, es idempotente, conserva una línea
      de log añadida a mano y se niega a pisar un tablero sin marcas.

Hallazgo de paso, y es justo el tipo de cosa que un tablero a mano tapa: **26 de
las 55 tareas del Project real no llevan label `modulo:`**. Todas las posteriores
al MVP. Con la tabla generada eso ya no se puede disimular — salen agrupadas bajo
`(sin módulo)`, que es la forma de que se note.

Límite conocido: entre dos generaciones, alguien puede editar la tabla a mano y
commitearla. La siguiente generación lo pisa (que es lo correcto), pero hasta
entonces miente. La alternativa —guarda en CI que compare tablero y Project—
necesita un token con alcance de Projects en CI, que `GITHUB_TOKEN` no trae; no
se promete lo que no se puede cumplir.

## M-08 · 🟠 `npm audit` prescrito sin decir qué hacer con el resultado

**Estado:** hecho (2026-07-26) · **Origen:** hallazgo 2

El kit prescribía el comando de auditoría en el checklist de cada fase pero no
decía qué debía pasar cuando encuentra algo. Eso deja un dilema sin salida
buena: bloqueante a secas → CI rojo desde el día uno por transitivas sin fix
aguas arriba, y un rojo permanente enseña a ignorar el rojo; `continue-on-error`
→ no avisa nunca. En el piloto se eligió lo segundo y **dos `high` vivieron días
en `main` con el CI en verde**.

Portada la implementación de referencia (`portal-web-api-sunat` PR #48, escrita
para pnpm), que era el trabajo ya pagado; lo pendiente era parametrizar el gestor.

- [x] `plantillas/ci/audit_check.py` con **adaptadores por gestor**: `npm`,
      `pnpm`, `yarn`, `pip-audit`, `composer`, `cargo`. Cada uno normaliza a un
      aviso `(id, paquete, severidad, título, url)` y el resto de la lógica es
      común.
- [x] Los cuatro modos de fallo del hallazgo, cada uno con su test: sin aceptar,
      caducada, obsoleta (ya no aparece en el audit) y vencimiento a más de 180
      días.
- [x] La clave es el **aviso** (GHSA/CVE/RUSTSEC), nunca el paquete. Verificado
      con el caso real de `minimist`: el paquete sale como `critical` pero uno de
      sus avisos es `moderate` — aceptar por paquete taparía el `critical`.
- [x] **Falla cerrado**, que es lo único imperdonable en una guarda de seguridad:
      gestor ausente, salida no-JSON, o forma inesperada → para. Probado con el
      error real de `pnpm` sin lockfile, que antes se habría leído como "limpio".
- [x] Donde el audit **no reporta severidad** (`pip-audit`, `cargo audit`), todo
      aviso bloquea salvo aceptación explícita: tratar "desconocida" como leve
      convertiría justo esos ecosistemas en un audit decorativo.
- [x] La allowlist nace **vacía** y el workflow se instala **desactivado**
      (`audit.yml.desactivado`): activarlo sin rellenar `GESTOR` ni el paso de
      instalación de dependencias produciría un rojo que no es una
      vulnerabilidad — y eso es literalmente cómo se aprende a ignorar el rojo.
- [x] `--diagnostico` enseña lo que la guarda **leyó** (no lo que el comando
      imprimió), para poder compararlo con la salida cruda: `/verificar` aplicado
      a la propia guarda.
- [x] 26 casos en `test_audit_check.py`, con los ejemplos de `npm` y `pnpm`
      tomados de la salida **real** de esas herramientas.
- [x] Documentado el "qué hacer con el resultado" donde faltaba:
      `seguridad_ampliada.md` §2, `practicas_dev.md` §8 (el paso de CI **nunca**
      lleva `continue-on-error`) y `trabajo_en_equipo.md` §10.
- [x] **Verificado de punta a punta contra dependencias vulnerables reales**
      (`lodash@4.17.15`, `minimist@0.0.8`): con `npm` y con `pnpm`, que además
      coinciden en los mismos 8 avisos. Bloquea los 4 bloqueantes, los acepta al
      declararlos, y muerde al caducar una entrada y al dejar una fantasma.

Límite dicho en voz alta: solo `npm` y `pnpm` están verificados contra la
herramienta real (son los que había instalados). `yarn`, `pip-audit`, `composer`
y `cargo` están escritos contra el formato documentado, marcados como **no
verificados** en el código y en el README, y el fallo cerrado hace que una
sorpresa de formato se note en vez de pasar por "sin vulnerabilidades". La
primera ejecución en un proyecto de esos ecosistemas debería confirmarse con
`--diagnostico`.

## M-09 · 🟠 Deriva de ramas largas sin mecanismo

**Estado:** hecho (2026-07-26) · **Origen:** hallazgo 4

El kit prescribe módulos reclamables trabajados en paralelo, y eso produce
**estructuralmente** ramas de vida larga que divergen: es consecuencia del
diseño, no un accidente. El kit creaba la condición y no daba el instrumento. En
el piloto, un PR salió de su base el 18 y se mergeó el 22: cuatro conflictos, uno
**no mecánico** — la rama afirmaba un estado de tarea que ya era falso, y
resolverlo a ciegas con `--theirs` habría metido una regresión documental en
`main` con el CI en verde. El día 19 habría sido trivial.

- [x] `plantillas/ci/deriva_ramas.py` + `deriva-ramas.yml` (programado, dos veces
      por semana): avisa en los PRs que se han quedado más de `UMBRAL_COMMITS`
      por detrás de su base.
- [x] **Un aviso por PR, no uno por ejecución** — el requisito que el hallazgo
      ponía por encima del umbral. Comenta una vez y después **edita ese mismo
      comentario**: la cifra queda al día sin una sola notificación nueva.
- [x] Y el aviso **se corrige a sí mismo**: si la rama se pone al día, el
      comentario se actualiza para decirlo. Un aviso obsoleto también miente.
- [x] No confunde los comentarios de humanos con el suyo (marca HTML propia), así
      que no edita lo que escribió otro.
- [x] **No poder mirar no es "no hay deriva"**: si `gh` falla, si la comparación
      no trae `behind_by` o si el listado de PRs llega al tope, para y lo dice. La
      alternativa sería un silencio que se lee como tranquilidad.
- [x] El texto del aviso explica el riesgo **real** —el conflicto no mecánico y la
      regresión con el CI en verde— y cómo salir, no solo el número.
- [x] `--simular` dice qué haría sin tocar nada: permite ajustar el umbral y
      probar en un repo real antes de dejar que comente.
- [x] 18 casos en `test_deriva_ramas.py`, incluidos los dos modos de fallo
      opuestos: spamear (se filtra y deja de leerse) y callar cuando debería
      hablar.
- [x] **Verificado contra los PRs reales** de los dos repos del piloto: con
      umbral 8 detecta tres (#126 a 8 commits, #51 a 11, #50 a 12) y deja en paz
      al resto; con umbral 50 calla. La simulación no tocó ningún PR.

Por qué hace falta un workflow propio y no basta lo nativo: *"Require branches to
be up to date before merging"* depende de la protección de rama, que en repos
privados con plan Free **no existe** (es el mismo muro de M-03).

Nota: no se activa en este repo. Trabajando en solitario y sin PRs abiertos no
tendría nada que vigilar, y una guarda que no puede morder no demuestra nada.

---

## Orden en que se hizo (y por qué)

**M-02 → M-03 → M-01** era el bloque que impedía escalar: sin coherencia
`main`/protección no se puede activar la única barrera que impide mergear sin
revisar; y sin ruta de actualización, cada proyecto queda congelado en la versión
con la que nació. Después M-04 y M-05 (fragilidad del candado), y luego M-06 a
M-09. Se respetó ese orden.

## Qué queda del plan

Nada pendiente en la lista. Lo que sale de aquí no es una mejora más, sino la
decisión de publicar (ver los dos puntos de "Dónde estamos") y, después,
**volver a auditar ejecutando** — que es como se encontraron estos nueve. Los
límites conocidos de cada mejora están anotados en su sección, no aquí, para que
quien lea una mejora vea de una vez qué cubre y qué no.

## Hecho

- **2026-07-25** — Hook `PreToolUse` de `secure-coding-guard` verificado
  (hallazgo 1) y guarda de deriva sin falsos positivos, ambos con tests que
  muerden. Ver [`CHANGELOG.md`](CHANGELOG.md).
