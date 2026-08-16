# Plan de mejora — `kit-construction-project`

Objetivo: que el kit sostenga **proyectos serios de larga vida**, no solo MVPs.
Criterio transversal, heredado de los hallazgos: *una regla sin mecanismo que la
aplique no está resuelta, y un mecanismo al que no se le ha visto **morder** no
está verificado.*

Estado: `pendiente` · `en curso` · `hecho` · `descartado`.
Origen: `auditoría 2026-07-25` (verificado ejecutando) o `hallazgo N` (de
[`hallazgos/2026-07-22-aplicacion-de-reglas.md`](hallazgos/2026-07-22-aplicacion-de-reglas.md)).

## Dónde estamos (al 2026-07-28)

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
| M-10 🔴 | El verificador escanea el propio kit: 37 falsos positivos | hecho |
| M-11 🔴 | El checklist post-instalación es inalcanzable al actualizar | hecho |
| M-12 🟠 | El grep de placeholders nunca puede salir limpio | hecho |
| M-13 🟠 | El kickstart genera instrucciones que su entorno no puede ejecutar | hecho |
| M-14 🟠 | Dos correcciones de texto (tabla del README, Paso 9 vs instalador) | **hecho** (2026-08-16) |
| M-15 🟢 | Precedencia de operadores en `verificar_kit.py` | hecho (cayó dentro de M-10) |
| M-16 🟠 | El DoD generado mezcla ítems post-merge sin marcarlos | **hecho** (2026-08-16) |

**M-01 a M-09 están cerradas.** Los tres hallazgos que quedaban sin implementar
(2, 3 y 4) tienen ya su mecanismo, y los cinco defectos de la auditoría del
2026-07-25 están corregidos.

**M-10 a M-15 son nuevas**, y salieron de la **primera ejecución real** del kit
sobre un proyecto de verdad (BarberCrow, 2026-07-26):
[`INFORME-PRIMERA-EJECUCION-KIT.md`](Projects-Aplicados-kit/Barber-king/INFORME-PRIMERA-EJECUCION-KIT.md).
Confirma el patrón de toda esta jornada: **lo que está testeado aguanta; lo que
nunca se había ejecutado tenía bugs**. Las tres graves son de la propia jornada —
M-12 se introdujo el mismo día que se creyó arreglar el problema contrario.

**M-16 es de la segunda ejecución** del mismo proyecto (2026-07-28):
[`hallazgo-items-post-merge.md`](Projects-Aplicados-kit/Barber-king/hallazgo-items-post-merge.md).
Trae una lección distinta a las anteriores: la regla estaba escrita y era correcta
en los tres sitios donde el kit la enseña, y aun así no se aplicó, porque el sitio
donde se va tachando el trabajo —el DoD— no la reflejaba. **Tener la regla escrita
en el sitio correcto no basta si falta en el sitio que se mira.**

Todo el trabajo está **commiteado en local y sin publicar**:
`git log origin/main..HEAD`. Quedan dos cosas por decidir antes de publicar:

1. La nota abierta de **M-03**: la primera ejecución de la guarda de integridad
   saldrá roja por los commits que ya entraron directos a `main`. Asumirlos como
   deuda conocida o empezar a contar desde ese punto.
2. Los commits de M-06 a M-09 viven en la rama `feat/smoke-test-kickstart`, no en
   `main`: el propio kit dice que todo entra por PR.

Lo que sigue abierto **dentro** de mejoras ya cerradas, dicho donde toca y no
escondido: la ventana entre dos generaciones del tablero (M-07) y los cuatro
adaptadores de audit sin verificar contra su herramienta real (M-08).

**2026-07-26 (tarde)** — se cerraron dos huecos que estaban anotados como
límites, más un ajuste de criterio pedido por el usuario:

- **M-06 · el agujero de cobertura grande.** `kickstart_check.py` validaba la
  plantilla; ahora `verificar_kit.py` valida **el kit generado**, en el Paso 10 y
  antes de entregarlo. No es el `--dry-run` del camino 1 —ejecutar Claude en CI
  no es posible— pero cubre lo que aquel buscaba: que la salida real tenga lo
  prometido, sin placeholders sueltos ni enlaces a documentos que no se
  escribieron. 21 casos.
- **M-03/M-08 · las guardas que llegan desactivadas.** Dependían de que alguien
  se acordara de activarlas, que es la clase de regla que este plan existe para
  eliminar. Dos mecanismos: el hook de arranque las recuerda **cada sesión** con
  el comando exacto y desaparece solo al decidir (13 casos), y
  `proteccion_main.py` detecta la llegada de un **segundo colaborador humano** y
  exige subir `EXIGIR_REVISION` en vez de confiar en la memoria (4 casos nuevos).
- **Regla de las ~300 líneas:** pasa de tope duro a **preferencia**. Superarla
  está bien si el archivo lo pide; lo que se divide es lo que tiene varias
  responsabilidades dentro, aunque tenga 200 líneas. Partir algo cohesionado solo
  para cumplir la cifra deja dos archivos que hay que leer juntos.

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

## M-10 · 🔴 El verificador escanea el propio kit: 37 falsos positivos

**Estado:** hecho (2026-07-27) · **Origen:** primera ejecución real (informe, Bug 2 y §B)

`verificar_kit.py` recorre `raiz.rglob("*")` excluyendo solo `.git` y
`node_modules`, así que **barre `SKILLS-PORTABLE/` y `.claude/skills/`** — cuyos
`{{...}}` son documentación de plantillas, no configuración pendiente. En un
proyecto con el kit instalado (o sea, el caso normal) sale **rojo con 37 fallos y
ninguno señala un archivo generado**.

**La causa de fondo no es el `rglob`, son los tests.** Ninguno de los 21 fixtures
de `test_verificar_kit.py` incluye `SKILLS-PORTABLE/` ni `.claude/`: el
verificador se probó contra un mundo que no existe. Arreglar el escaneo sin
arreglar los fixtures deja la puerta abierta a la siguiente variante.

**Y lo peor no es el falso positivo, es lo que provocó.** El evaluador, ante 37
fallos que sabía ruido, copió el proyecto a un temporal excluyendo esas carpetas,
verificó la copia y reportó verde. Una guarda que sale roja con ruido en su
primera ejecución **no se lee: se rodea**. El incentivo lo fabricó el kit.

- [x] `EXCLUIDAS` en `verificar_kit.py`: `SKILLS-PORTABLE/` y `.claude/` fuera del
      escaneo, con el porqué escrito al lado y el reparto de responsabilidad dicho
      —los placeholders de `.claude/` los reclama el checklist de `instalar.sh`,
      que es quien los puso ahí—. La exclusión se mide sobre la ruta **relativa**
      a la raíz: si mirase la absoluta, un proyecto bajo `~/.claude/...` se
      quedaría sin verificar y en silencio.
- [x] Fixture `INSTALADO` con `SKILLS-PORTABLE/` y `.claude/`, sus `{{...}}` y un
      enlace al paquete que no resuelve. Contra el código anterior el caso sale
      con 8 fallos, ninguno del proyecto.
- [x] El caso que muerde comprueba **la lista de archivos escaneados**, no el
      veredicto: así no basta con silenciar los fallos por otro camino.
- [x] Y su recíproco: con el kit instalado alrededor, un placeholder real en
      `README.md` sigue saliendo, y sale **solo**. Excluir no puede ser cegar.
- [x] En `SKILL.md`, Paso 10: se dice que el rojo señala algo tuyo y que **no se
      rodea** —ni copiando a un temporal ni filtrando la salida—. El rodeo fue lo
      que pasó de verdad, y la herramienta sola no lo impide.

**Verificado bajando el código a la versión anterior:** 4 de los 5 casos nuevos
fallan contra ella (22/26). El quinto —el del proyecto dentro de una carpeta
`.claude`— no muerde contra el original, sino contra el arreglo ingenuo de
excluir por ruta absoluta; comprobado también, y falla (25/26).

**Límite:** esto quita el ruido, no demuestra que el veredicto verde signifique un
kit bueno. Sigue verificando el artefacto, no el criterio.

## M-11 · 🔴 El checklist post-instalación es inalcanzable al actualizar

**Estado:** hecho (2026-07-27) · **Origen:** primera ejecución real (informe, Bug 1 y E2)

`instalar.sh:283-284` hace `resumen_actualizacion; exit 0`. El bloque
`FALTA (a mano, o pideselo a Claude)` y el grep de placeholders viven en las
líneas 288-307, **después de ese `exit`**. Y como el instalador **fuerza** el modo
actualización en cuanto detecta una instalación previa, cualquier segunda
ejecución pierde el checklist entero: los placeholders, `OWNER`/`PROJECT_NUMBER`,
pegar `CLAUDE-fragmento.md`, el `.gitignore` y proteger `main`.

El README lo agrava: documenta fábrica y `--protocolo` como dos líneas seguidas,
que es justo la secuencia que dispara el fallo. En la prueba real pasó exactamente
eso y hubo que derivar la lista a mano.

- [x] **Ni una cosa ni la otra: se quitó el `exit 0`.** El bloque es ahora
      `pendiente_de_configurar()` y se llama una sola vez al final, en los dos
      caminos; la actualización solo añade su resumen antes. Mover el bloque por
      encima del `exit` habría arreglado este caso dejando en pie la estructura
      que lo causó — dos salidas, una de ellas prematura. Ahora no hay un `exit`
      del que depender.
- [x] Al actualizar el título cambia a «REPASO de configuración (lo que ya
      hicisteis, ignoradlo)». Decir "FALTA" sobre algo ya hecho es la clase de
      ruido que enseña a saltarse el bloque entero, que es la lección de M-10.
- [x] 4 casos en `test_instalar.sh`: el repaso en la ruta de actualización
      (título, pasos completos y lista de placeholders) y en la de repetir el
      comando de instalación —el camino que documenta el README—. Más uno que
      fija el «FALTA» de la instalación inicial, que no estaba cubierto.
- [x] README del kit: dice que el repaso sale **siempre**, incluida la segunda
      ejecución, y nombra el fallo que hubo ahí. Y el recuento de casos de
      `test_instalar.sh` pasa de 23 —que llevaba tiempo desfasado— a 33.

**Verificado bajando `instalar.sh` a la versión anterior:** los 4 casos nuevos de
la ruta de actualización fallan (`4 comprobacion(es) fallida(s)`). Con el arreglo,
33/33.

**Límite:** el repaso no sabe qué habéis configurado ya, así que en la
actualización se lee entero aunque solo falte un punto. Lo que sí sabe es la lista
de placeholders — **levantado en M-12**, que la dejó capaz de decir "ninguno
pendiente".

## M-12 · 🟠 El grep de placeholders nunca puede salir limpio

**Estado:** hecho (2026-07-27) · **Origen:** primera ejecución real (informe, Bug 3)

**Corrección:** el grep vive **solo** en `instalar.sh`. El README nunca lo
documentó — grepeado el repo entero, una única copia. La tarea de "arreglarlo
también en el README" no existía.

El grep incluye `scripts/`, donde viajan `test_tablero.py`, `test_audit_check.py` y
`test_docs_check.py` **con placeholders como fixture deliberado**
(`cargar(owner="{{OWNER}}")`) — y son **exactamente los mismos nombres** que los
archivos de verdad, así que tapan la señal entera. Resultado: un "queda trabajo
pendiente" permanente que nunca se puede satisfacer.

Se introdujo el **mismo 2026-07-26**, al ampliar el grep a `scripts/` para que no
se dejara fuera `{{GESTOR_PAQUETES}}`. Se arregló que faltaran y se creó que
sobraran: los dos errores son el mismo, listar sobre un conjunto mal elegido.

**Y había una segunda causa que solo apareció al ejecutarlo.** El primer intento
—excluir `test_*` y nada más— seguía fallando el caso: cuando el instalador
conserva un archivo que el equipo configuró, deja al lado la versión del kit como
`<archivo>.nuevo`, **de fábrica y llena de placeholders**. Es decir, en cuanto un
proyecto configura algo y actualiza —todos, tarde o temprano— la lista volvía a
ser insatisfacible por otro camino. Y no son configuración pendiente: son copias
esperando reconciliación, de las que ya informa `resumen_actualizacion` bajo
CONSERVADOS. Excluir `test_*` era necesario y **no suficiente**.

- [x] `--exclude='test_*'` y `--exclude='*.nuevo'` en el grep de `instalar.sh`
      (en el README no había nada que arreglar). El segundo no estaba en el plan:
      lo encontró el caso al ejecutarse.
- [x] La lista deja de ser un volcado y pasa a decir una de dos cosas: «Sin
      rellenar todavía: …» o **«Placeholders: ninguno pendiente.»**. Poder decir
      lo segundo era el objetivo — una lista que solo sabe decir "queda trabajo"
      no informa de nada, y se aprende a saltarla igual que un rojo que no
      significa nada (M-10).
- [x] Caso 5e: proyecto instalado, configurado y reinstalado → imprime la lista
      vacía. Rellena **solo lo que el repaso mira**, así que si el grep volviera a
      tocar las plantillas del kickstart el caso lo denunciaría; hay una
      comprobación explícita de que esas plantillas siguen con sus `{{...}}`.
- [x] Y el caso recíproco en la instalación inicial: ahí sí tiene que decir que
      quedan.

**Verificado bajando `instalar.sh` a la versión anterior:** fallan 2 de los casos
nuevos. El tercero (`.nuevo` presentes) es una precondición del escenario, no una
mordida: está para que quien lea el caso sepa que ese camino se está ejercitando
de verdad. La segunda causa se comprobó a mano: con `--exclude='test_*'` puesto y
sin `--exclude='*.nuevo'`, la lista seguía sacando 4 placeholders, los cuatro de
archivos `.nuevo`. **37/37** con el arreglo.

## M-13 · 🟠 El kickstart genera instrucciones que su entorno no puede ejecutar

**Estado:** hecho (2026-07-28) · **Origen:** primera ejecución real (informe, E1 y Bug 5)

**Cómo fue la ejecución** (aclarado por quien la hizo): no se ejecutó el kit en
seco. La sesión llevaba puestos, antes de empezar, un contexto inicial, **el diseño
en HTML "que debe seguirse fielmente"** y los requerimientos de Barber-king; con eso
se ejecutó el kit y después el kickstart, alimentado con esos mismos archivos.

**Corrección al informe:** el kit **no** contiene "Fidelidad al diseño §8" ni "abre
el prototipo" — grepeado entero, cero coincidencias. Ese texto entró **por el
material de entrada del usuario**, no por el kit ni por otra skill. El bug estaba
mal atribuido, pero la atribución correcta no lo absuelve.

Porque el kit no controla lo que entra —ni va a controlarlo nunca: la entrada es
material arbitrario, un HTML, unos requerimientos— pero **sí controla lo que
genera**. Y el kickstart tomó "sigue fielmente el diseño" y lo tradujo literalmente
a **~16 subfases que ordenan "ABRE el prototipo"**, algo que Claude Code no puede
hacer (no hay renderizador; y si el diseño es un artifact *bundled*, hay que
desempaquetarlo). Copió la intención sin traducirla al entorno de destino. O sea,
el kit produce documentación **no ejecutable donde va a ejecutarse**, y nada en el
repo generado explica cómo suplirlo. El próximo Claude repetirá el trabajo de
ingeniería inversa o se lo inventará.

La regla que falta, entonces, no es "no digas «abre el prototipo»" — es que **toda
instrucción heredada de la entrada se reescriba en términos ejecutables por quien
va a ejecutarla**.

- [x] Fila en la tabla de entorno («Antes del Paso 0 → A») para "mirar un diseño",
      más el párrafo del caso *bundled*: qué es, por qué un `Read` devuelve base64
      y que el desempaquetador **se deja en `scripts/`**, no en la sesión.
- [x] Regla 8 de «Reglas de calidad de los archivos generados», que es donde vivían
      las otras siete inviolables: lo heredado de la entrada se traduce al
      procedimiento que sí funciona, y la herramienta que hizo falta se queda en el
      repo. Con el caso real escrito debajo, porque una regla sin su historia se
      borra en el primer refactor.
- [x] **El mecanismo, que es lo que separa esto de una recomendación:** regla 6 de
      `verificar_kit.py` (`ordenes_sin_procedimiento`), en el Paso 10. Una orden de
      mirar un diseño sale roja salvo que a su lado esté el comando **y** la
      herramienta exista en el repo. Las dos mitades importan y las dos fallaron:
      sin comando sigue siendo «míralo», y con un comando a un script que se cerró
      con la sesión, la siguiente lo rehace.
- [x] Y que la fila y la regla no puedan desaparecer en silencio:
      `ejecutabilidad_documentada()` en `kickstart_check.py`. La fila se exige
      cuando la tabla existe —borrar la tabla entera ya lo caza
      `entorno_traducido`, y acusar de una fila ausente en una tabla ausente sería
      el ruido de M-10—; la sección de calidad se exige siempre.

**Lo que NO cubre, y se dice aquí en vez de dejarlo implícito:** la regla 6 mira la
forma concreta que ya apareció —órdenes de mirar un artefacto de diseño— y no
juzga si una instrucción cualquiera es ejecutable, que es un problema abierto. En
particular, `diseño` a secas queda fuera del patrón a propósito: en español cubre
«el diseño de la base de datos», que se mira leyendo un `.md`. La regla general
vive en la skill; el que muerde solo muerde lo que se sabe que aparece.

**Verificado bajando el código a la versión anterior:** de los 9 casos nuevos de
`test_verificar_kit.py`, los 5 que acusan fallan contra ella (30/35); los otros 4
son recíprocos —lo que NO debe morder— y por construcción pasan en ambas. En
`test_kickstart_check.py`, 3 de los 4 nuevos fallan (33/36). Con el arreglo, 35/35
y 36/36.

**Y verificado donde importa: contra el proyecto real.** Ejecutado sobre
BarberCrow, el verificador saca **13 fallos y los 13 son verdaderos** — las órdenes
de abrir el prototipo que quedaron en la guía, en el README, en el handoff de F1.3
y en el contexto inicial. Cero ruido, que es la condición que dejó puesta M-10.

Esa ejecución corrigió el arreglo a mitad de camino, y conviene que quede escrito.
La primera versión saltaba los bloques de código, como hacen las otras cuatro
reglas —ahí viven plantillas y ejemplos—, y encontró **2** de los 13. Las once que
faltaban estaban DENTRO de los prompts: en la guía generada los bloques no son
ejemplos, son lo que el dev pega literal (regla 2 de calidad). Esta regla los mira,
es la única que lo hace, y el porqué está escrito a su lado. La segunda corrección
fue el orden de las palabras: «ABRE el prototipo» se veía y «(pantalla 8 del
prototipo — ábrelo)» no.

Sin esa comprobación contra el proyecto real, el mecanismo habría pasado sus 35
casos verdes cubriendo el 15% del fallo que decía cubrir.

## M-14 · 🟠 Dos correcciones de texto que costaron trabajo real

**Estado:** pendiente · **Origen:** primera ejecución real (informe, Bugs 4 y 7)

- La tabla del README sitúa `OWNER` y `PROJECT_NUMBER` solo "en
  `scripts/tablero.py`". También viven en `que-toca.SKILL.md:20,51`. Quien siga la
  tabla al pie de la letra deja la skill del candado con un `gh project item-list`
  inválido.
- El Paso 9 pide generar los ítems 21 y 25 (`arranque.sh` + `settings.json`, y la
  copia en `SKILLS-PORTABLE/`) que **`instalar.sh` ya dejó**. En la prueba real el
  evaluador dudó y decidió no regenerarlos, con buen criterio: habría cambiado los
  hashes del manifiesto y la siguiente actualización habría creído que los tocó el
  equipo. Ese razonamiento debería estar en la skill, no depender de que lo deduzca
  quien la ejecuta.

- [x] Completar la fila de la tabla. Hecho el 2026-08-16, y **peor de lo que decía
      la ficha**: no son "también en `que-toca.SKILL.md:20,51`" sino **6 veces en
      `que-toca` y 2 en `cerrar-sesion`** (contadas, no estimadas). La fila dice
      ahora las tres ubicaciones, añade que `estado.py` **no** los declara —los
      importa de `tablero.py`, desde el PR #21— y explica el modo de fallo: quien
      rellene solo el script se lleva el error **al reclamar**, no al configurar.
- [x] Nota en el Paso 9: hecha, con el motivo completo. No es solo "ya existen":
      el instalador **registra su hash** en el manifiesto, así que regenerarlos
      hace que la siguiente actualización los trate como tocados por el equipo —
      llegarían como `.nuevo` y alguien reconciliaría a mano algo que nadie
      cambió. Ese era exactamente el razonamiento que el evaluador tuvo que
      deducir solo en la prueba real.

## M-15 · 🟢 Precedencia de operadores en `verificar_kit.py`

**Estado:** hecho (2026-07-27, dentro de M-10) · **Origen:** primera ejecución
real (informe, Bug 6)

Cayó aquí porque es **la misma expresión** que M-10 tenía que reescribir. Volver a
emitirla con el bug dentro, sabiendo que estaba, no era una opción defendible.

```python
if p.is_file()
and p.suffix in EXTENSIONES or p.name in (".gitignore", ".env.example")
```

`and` liga más fuerte que `or`, así que evalúa
`(is_file and suffix) or (name in ...)`: un **directorio** llamado `.gitignore` o
`.env.example` entraría en la lista y reventaría en `read_text()`. Latente —
requiere un directorio con ese nombre— pero es un fallo de lectura, no de estilo.

- [x] Paréntesis alrededor de la disyunción, con un caso que crea `docs/.env.example`
      y `docs/.gitignore` **como directorios**. Contra el código anterior el caso
      no falla: revienta (`PermissionError` al abrir el directorio), que es
      exactamente el modo de fallo descrito.

## M-16 · 🟠 El DoD generado mezcla ítems post-merge sin marcarlos

**Estado:** pendiente · **Origen:** segunda ejecución real (BarberCrow, 2026-07-28)

En F1.5 se abrió el catálogo —pasar F2/F3/F7.1 a `Disponible`— **con la tarea
todavía En progreso**, o sea antes de mergear. No la reclamó nadie en esa ventana,
pero el riesgo era real: otro dev habría empezado sobre un contrato que la revisión
aún podía cambiar. El tag, que es la misma clase de acción, sí se hizo después de
mergear. No había un criterio equivocado detrás: se estaba improvisando ítem a
ítem.

El DoD de F1.5 es una lista plana donde conviven cosas de naturaleza distinta y
nada marca cuáles van después del merge:

```
- [ ] 8 módulos con contrato tipado y regla de frontera activa
- [ ] Hito F1 demostrado
- [ ] Tag v0.1.0                                        ← post-merge
- [ ] DoD estándar + handoff
- [ ] Se abre el catálogo: F2/F3/F7.1 pasan a Disponible ← post-merge
```

**Corrección a la primera atribución, y va en contra de lo que se dijo al
reportarlo:** la sospecha era que la skill se quedaba en el PR y no cubría el
post-merge. Es falso. `cerrar-sesion.SKILL.md:65-66` lo dice con estas palabras:
«a **Terminado** al mergear. Poner en **Disponible** los items cuyas dependencias
quedaron cumplidas». Y `trabajo_en_equipo.md:94` es la regla 7, que llega intacta
al `equipo.md` generado. La regla estaba escrita en tres sitios —`equipo.md`,
`/cerrar-sesion` y el propio log del tablero, que lo dejó dicho al cerrar T-002 y
T-003—, y se leyó, y no se aplicó.

Así que el reparto es **peor para quien ejecutó y más estrecho para el kit** de lo
que parecía: el kit no enseña la regla mal, la enseña en todas partes **menos en
el sitio que uno va tachando**. Es un hueco de presentación, no de contenido. Pero
es exactamente el mismo patrón del bloque M-10..M-12: la señal existe y es
correcta, y aun así no funciona por cómo se presenta.

**Y aquí está lo que le toca al kit,** que es lo único accionable: el arreglo ya
se aplicó **en el archivo generado** de BarberCrow —tabla en el preámbulo de
`guia_desarrollo.md:15-23` y marcas `⏭️ post-merge` en las líneas 298, 299, 576,
674, 938 y 995—. En el kit no hay nada. `F1.5`, `post-merge` y el desbloqueo del
catálogo no aparecen en ningún archivo de `kit-construction-project/` (grepeado).
El próximo proyecto generado nace con el mismo DoD plano.

Misma familia que **M-13**: el kit no controla lo que entra, pero sí lo que
genera, y lo que genera no es ejecutable en el orden en que se va a ejecutar. La
diferencia es que M-13 es sobre instrucciones imposibles y esta es sobre
instrucciones posibles **en el orden equivocado**.

- [x] Regla al generar los DoD, en el Paso 9 de la skill: lo que depende del merge
      se emite `- [ ] ⏭️ **post-merge:** …`, nunca al mismo nivel. Y la plantilla
      de `guia_desarrollo.md` trae la tabla del preámbulo que explica por qué,
      generalizada de la que se validó en el proyecto real.
- [x] Y dicho en esa misma tabla: **toda** subfase desbloquea a las que dependen
      de ella, no solo las que lo escriben, y el orden es siempre
      **mergear → Terminado → desbloquear**.
- [x] Caso que muerde, en `verificar_kit.py` (`dod_post_merge_sin_marcar`):
      **6 casos**, y la suite pasa de 35 a 41. Se eligió `verificar_kit` y no
      `kickstart_check` porque este juzga la **plantilla** y aquel el **kit
      generado**, que es donde el DoD plano hace daño.

**Lo que apareció al implementarlo, y no estaba en la ficha:** la comprobación se
dispara contra **la tabla que enseña la regla**, porque esa tabla nombra el tag y
el desbloqueo. Es el mismo auto-disparo que ya suspendió otra guarda de este kit
contra el PR que la introducía. Resuelto exigiendo que la línea sea un ítem de
checklist (`- [ ]`), con un caso dedicado — verificado quitando el filtro y
viéndolo fallar. **La documentación de un kit habla de sus propias guardas: toda
guarda que lea texto acabará leyendo la explicación de sí misma.**

Las tres mutaciones, todas vistas en rojo: función desenchufada del agregador
(caen 3 casos), sin filtro de checkbox (cae el de auto-disparo), sin condición de
modo equipo (cae el de un solo dev). La primera importa especialmente: es el modo
de fallo que dejó las guardas de `docs_check` en verde estando desconectadas.

**Límite:** marcar el orden no impide saltárselo. Lo que quita es la excusa de que
la lista no lo decía — que es lo único que el kit puede quitar desde aquí.

---

## Orden en que se hizo (y por qué)

**M-02 → M-03 → M-01** era el bloque que impedía escalar: sin coherencia
`main`/protección no se puede activar la única barrera que impide mergear sin
revisar; y sin ruta de actualización, cada proyecto queda congelado en la versión
con la que nació. Después M-04 y M-05 (fragilidad del candado), y luego M-06 a
M-09. Se respetó ese orden.

## Qué queda del plan

**M-14 y M-16**, las dos que quedan de ejecutar el kit en un proyecto real — que
es exactamente como se encontraron las nueve anteriores.

El bloque M-10 → M-11 → M-12 se hizo en ese orden y por un hilo común: las tres
eran señales que gritaban en falso. El verificador salía rojo con ruido (M-10), el
repaso de configuración no llegaba a la ruta más usada (M-11), y la lista de
placeholders no podía salir limpia nunca (M-12). Una señal que no puede estar en
verde no es una señal, y se aprende a saltarla. M-15 cayó dentro de M-10 por vivir
en la misma expresión.

**M-13 se hizo el 2026-07-28** y dejó puesta la mitad del andamio que M-16
necesita: la regla 8 de calidad ya dice que lo generado tiene que ser ejecutable
por quien va a ejecutarlo, y `verificar_kit.py` ya sabe morder sobre el texto de
la guía generada. M-16 es la otra mitad de la misma frase —**y en el orden en que
va a ejecutarlo**— y entra por ahí en vez de inventarse un sitio nuevo.

Sigue **M-16**, y **M-14** al final, que son dos correcciones de texto.

Los límites conocidos de cada mejora están anotados en su sección, no aquí, para
que quien lea una mejora vea de una vez qué cubre y qué no.

## Hecho

- **2026-07-25** — Hook `PreToolUse` de `secure-coding-guard` verificado
  (hallazgo 1) y guarda de deriva sin falsos positivos, ambos con tests que
  muerden. Ver [`CHANGELOG.md`](CHANGELOG.md).
