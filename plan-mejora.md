# Plan de mejora — `kit-construction-project`

Objetivo: que el kit sostenga **proyectos serios de larga vida**, no solo MVPs.
Criterio transversal, heredado de los hallazgos: *una regla sin mecanismo que la
aplique no está resuelta, y un mecanismo al que no se le ha visto **morder** no
está verificado.*

Estado: `pendiente` · `en curso` · `hecho` · `descartado`.
Origen: `auditoría 2026-07-25` (verificado ejecutando) o `hallazgo N` (de
[`hallazgos/2026-07-22-aplicacion-de-reglas.md`](hallazgos/2026-07-22-aplicacion-de-reglas.md)).

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

**Estado:** pendiente · **Origen:** auditoría 2026-07-25

`/que-toca` lleva 5+ IDs de GraphQL hardcodeados. Nada comprueba que sigan
vivos: si el Project se recrea, cambian y la skill falla a medias (asigna el
issue, no mueve la tarjeta).

- [ ] Descubrir los IDs en ejecución, o autocomprobarlos antes de usarlos.
- [ ] Si siguen sin rellenar (`{{...}}`), decirlo y parar antes de asignar nada.

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

**Estado:** pendiente · **Origen:** auditoría 2026-07-25

`project-kickstart` son ~2.900 líneas sin verificación. Es prosa y no se testea
directa, pero **su salida sí**.

- [ ] Smoke test: generar el kit para una idea de prueba y correr `docs_check`
      sobre lo generado (enlaces rotos, estructura, placeholders sin resolver).

## M-07 · 🟠 El tablero se mantiene a mano siendo un espejo

**Estado:** pendiente · **Origen:** hallazgo 3 · **Relacionado:** M-02

Project (verdad) → tablero (resumen) → `estado-actual` (espejo del tablero), los
dos últimos a mano. En el piloto produjo deriva tres veces en dos días.

- [ ] Generar `tablero-equipo.md` desde el Project en vez de escribirlo.
- [ ] Eliminar una de las dos instantáneas manuales.

## M-08 · 🟠 `npm audit` prescrito sin decir qué hacer con el resultado

**Estado:** pendiente · **Origen:** hallazgo 2

Implementación de referencia ya en producción (`portal-web-api-sunat` PR #48):
allowlist caducable que falla en cuatro casos. Portarla exige parametrizar el
gestor de paquetes.

## M-09 · 🟠 Deriva de ramas largas sin mecanismo

**Estado:** pendiente · **Origen:** hallazgo 4

El kit prescribe módulos paralelos (que producen ramas de vida larga) y ninguna
plantilla de CI vigila la deriva. Un PR con cuatro días de retraso costó cuatro
conflictos, uno no mecánico.

---

## Orden recomendado

**M-02 → M-03 → M-01** son el bloque que hoy impide escalar: sin coherencia
`main`/protección no puedes activar la única barrera que impide mergear sin
revisar; y sin ruta de actualización, cada proyecto queda congelado en la
versión con la que nació. Después M-04 y M-05 (fragilidad del candado), y luego
M-06 a M-09.

## Hecho

- **2026-07-25** — Hook `PreToolUse` de `secure-coding-guard` verificado
  (hallazgo 1) y guarda de deriva sin falsos positivos, ambos con tests que
  muerden. Ver [`CHANGELOG.md`](CHANGELOG.md).
