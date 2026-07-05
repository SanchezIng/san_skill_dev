# Modo Colaborativo — Módulos Disponibles y Tablero Vivo

Este archivo se lee cuando el proyecto tiene **2 o más desarrolladores** (modo equipo). También aporta valor con **1 dev**: el catálogo de módulos se convierte en su mapa de avance. Define un modelo donde el trabajo se organiza en **módulos independientes reclamables**, no en asignaciones fijas de "un dev = un módulo".

---

## 1. Principio central: propiedad colectiva, no asignación fija

**Error a evitar:** acoplar cada módulo a una persona ("Dev A siempre hace el Módulo A"). Es frágil: si esa persona falta, su módulo se congela; si termina rápido, queda ociosa mientras otro se ahoga.

**Modelo correcto:** los módulos son **unidades de trabajo disponibles**. Cualquier desarrollador reclama un módulo (o una tarea dentro de un módulo) que esté **disponible**, lo marca en un tablero vivo, trabaja, y lo libera al terminar. Otro dev, viendo el tablero, toma un módulo distinto e independiente. Esto es *collective code ownership* y es lo óptimo para equipos pequeños.

**Consecuencia clave:** el número de módulos lo define la **arquitectura del dominio** (cuántas fronteras verticales limpias existen), NO el número de desarrolladores. Con más devs que módulos, varios trabajan tareas internas del mismo módulo coordinando fronteras, o preparan los bloqueados. Con más módulos que devs, se toman de a uno; los demás esperan disponibles. El sistema es **indiferente al número de devs** — por eso sumar o quitar gente no exige rediseñar nada.

---

## 2. Definir los módulos (por dominio, no por headcount)

### Criterios

- Cada módulo agrupa una responsabilidad de dominio **vertical y completa**, desarrollable y testeable con **mocks** de los demás. "Emisión de comprobantes" sí; "todos los controllers" no.
- La frontera entre módulos es SIEMPRE una interfaz o contrato documentado (service, puerto, evento), nunca acceso directo a las tablas o clases internas de otro módulo.
- Se derivan de la arquitectura definida en el Paso 5-6, partiendo el sistema donde las dependencias son más débiles.
- Cantidad: la que pida el dominio (típicamente 3-6 en un proyecto mediano), independientemente de cuántos devs haya.

### Catálogo de módulos (docs/equipo.md)

En vez de una matriz "modulo->dev fija", se genera un **catálogo con estado**:

| Módulo | Frontera (interfaz) | Depende de | Estado | Trabajando |
|--------|---------------------|------------|--------|-----------|
| A — {nombre} | {Service/contrato} | — | Disponible | — |
| B — {nombre} | {Service/contrato} | A (interfaz X) | Bloqueado por A | — |
| C — {nombre} | {Service/contrato} | — | Disponible | — |

Estados posibles: **Disponible** · **En progreso** (+ quién) · **Bloqueado** (+ por qué) · **Terminado**.

---

## 3. El tablero vivo (fuente de verdad de "quién hace qué")

Se generan **ambos** mecanismos; el equipo elige cuál usar al arrancar (o usa los dos, con uno como espejo):

### Opción A — Markdown en el repo: progreso/tablero-equipo.md

Cero setup, funciona offline. Estructura:

```markdown
# Tablero del Equipo — actualizar ANTES de empezar y AL terminar

## Módulos
| Módulo | Estado | Dev | Desde |
|--------|--------|-----|-------|
| A — Emisión | En progreso | Félix | 2026-07-05 |
| B — Plataforma API | Disponible | — | — |
| C — Procesos async | Bloqueado por A | — | — |

## Tareas en curso (dentro de módulos)
| Tarea | Módulo | Dev | Estado |
|-------|--------|-----|--------|
| T-014 Endpoint /facturas | B | — | Disponible |

## Log de reclamos (append-only, evita disputas)
- 2026-07-05 Félix reclama Módulo A
```

**Regla anti-conflictos:** el log es *append-only* (solo se añaden líneas al final) para minimizar merge-conflicts. Si dos editan la tabla a la vez y colisiona, se aceptan ambas filas y se reconcilia el estado mirando el log.

### Opción B — GitHub Project + Issues

Sin merge-conflicts, visual. Columnas: Disponible -> En progreso -> Review -> Terminado. Cada módulo es un **milestone** o label; cada tarea un Issue con su dependencia (bloqueado por #N). Reclamar = autoasignarse el Issue y moverlo a "En progreso". Se ofrece generarlo con `gh` al final del kickstart.

**Si usan ambos:** GitHub es la verdad para tareas; tablero-equipo.md queda como resumen rápido de módulos que se actualiza en el mismo PR que cierra trabajo.

---

## 4. Reglas de convivencia (lo que hace que "toma lo disponible" no sea caos)

1. **Reclamar antes de codificar.** Nadie toca un módulo/tarea sin marcarlo En progreso en el tablero primero. Este único hábito es lo que previene choques — no la asignación previa.
2. **Un módulo En progreso no lo toma otro dev.** Pero sus **tareas internas independientes** sí pueden repartirse entre dos si acuerdan explícitamente las fronteras y lo anotan.
3. **Las dependencias mandan.** Un módulo Bloqueado no se reclama hasta que su dependencia esté Terminada. El tablero muestra siempre qué está realmente disponible.
4. **WIP máximo 1-2 por dev.** Terminar y liberar > acaparar módulos.
5. **Si te quedas sin módulos disponibles:** ayuda a desbloquear (review, pairing en el módulo que bloquea) en vez de abrir un frente nuevo a medias.
6. **Cambios a una frontera (interfaz compartida):** avisar al equipo ANTES de codificar; si es de largo plazo, registrar ADR.
7. **Liberar al terminar:** marcar Terminado, y si desbloquea otros módulos, actualizar sus estados a Disponible.

---

## 5. Fases y subfases en modo colaborativo

Al aplicar el Paso 8 (división en subfases):

1. Cada subfase se etiqueta con su **módulo** ([A], [B]...) y sus **dependencias** entre subfases.
2. Subfases de módulos sin dependencia mutua se marcan **paralelizables**: pueden estar disponibles a la vez.
3. **F1 es siempre compartida y secuencial** (repo, entorno/Docker, CI, esqueleto de módulos e interfaces). La ejecuta **un** dev (el "integrador" de arranque) para no chocar en el andamiaje. Solo tras F1 se abre el catálogo de módulos para reclamar.
4. Cada fase cierra con un **hito de integración**: los módulos se conectan sin mocks y se prueba el flujo completo (el "demo" del equipo).

Handoff docs **por módulo**: progreso/fase-{n}.{m}-{modulo}.md. progreso/estado-actual.md incluye la tabla de estado por módulo (espejo del tablero).

---

## 6. Backlog con dependencias (docs/backlog.md)

Tareas mapeadas desde las subfases. Formato:

```markdown
### T-014 · [B] Endpoint POST /facturas
- Módulo: B — Plataforma API
- Depende de: T-008 (interfaz EmisionService definida)
- Criterios de aceptación:
  - [ ] Request validado
  - [ ] Test de integración pasa
  - [ ] Documentado en OpenAPI
- Estado: Disponible | En progreso | Review | Done
```

Una tarea está **disponible** solo si sus dependencias están Terminadas. Cada dev toma tareas disponibles de cualquier módulo no bloqueado, respetando la regla de no invadir un módulo que otro tiene En progreso (salvo tareas internas coordinadas).

---

## 7. Metodología (Scrum-lite, opcional)

- **Iteración semanal:** reunión corta (15-30 min) para revisar el tablero, desbloquear dependencias y fijar el objetivo de la semana.
- **Hito de integración = sprint review:** se demuestra el flujo funcionando.
- **Retro exprés** al cerrar cada fase (5 min, 2 preguntas).
- Si el equipo tiene Scrum impuesto (curso/empresa): iteración semanal = sprint, backlog.md = product backlog, tablero = Scrum board, hito = review. Mapea 1:1.

---

## 8. Onboarding de un dev que se suma a un proyecto en marcha

**No se regenera el kickstart.** Sumar (o quitar) un dev es incremental, porque el sistema no depende del número de personas:

1. Clona el repo, lee CLAUDE.md y docs/equipo.md para entender módulos y fronteras.
2. Mira el **tablero vivo**: toma cualquier módulo Disponible, o una tarea disponible dentro de un módulo activo (coordinando frontera).
3. Lo marca En progreso en el tablero (reclamar antes de codificar).
4. Arranca su sesión de Claude Code: "Lee CLAUDE.md y el handoff del módulo {X}; tomo la tarea T-{nnn}".

Si el dominio lo pide, se puede **añadir un módulo nuevo** al catálogo (ej. un frente que estaba fuera del MVP) en vez de subdividir uno existente — frontera limpia, cero fricción con lo que ya está en progreso.

---

## 9. Convenciones de equipo (se integran al CLAUDE.md)

Añadir sección "## Convenciones de Equipo" al CLAUDE.md:

1. **Nadie hace push directo a main.** Todo entra por Pull Request.
2. **Todo PR requiere >=1 revisión humana de otro dev.** Regla con IA: *"respondes por lo que tu Claude Code generó"* — si no puedes explicar una línea, no se mergea.
3. **PRs pequeños** (< ~400 líneas de diff). Subfase grande = varios PRs.
4. **CI verde obligatorio** para mergear (sección 10).
5. **Reclamar antes de codificar** (tablero) — la regla central de convivencia.
6. **Conventional Commits** con módulo en el scope: feat(B): endpoint POST /facturas.
7. **Ramas:** modulo/tarea-corta -> b/endpoint-facturas.
8. **Cambios a fronteras compartidas:** avisar antes; ADR si es de largo plazo.

---

## 10. CI mínimo (.github/workflows/ci.yml)

En cada PR, adaptado al stack: **lint/formato**, **análisis estático** (si el stack lo tiene maduro), **tests** (al menos del módulo tocado), **auditoría de dependencias** (modo advertencia). Además .github/PULL_REQUEST_TEMPLATE.md con: qué hace, módulo, tarea (T-nnn), checklist (tests, lint, docs, sin secrets, tablero actualizado).

---

## 11. Archivos que genera el modo colaborativo

| Archivo | Contenido |
|---------|-----------|
| docs/equipo.md | Catálogo de módulos con estado, fronteras, reglas de convivencia, metodología |
| docs/backlog.md | Backlog inicial con tareas, dependencias y estado (sección 6) |
| progreso/tablero-equipo.md | Tablero vivo en Markdown (sección 3, opción A) |
| .github/workflows/ci.yml | CI mínimo según stack |
| .github/PULL_REQUEST_TEMPLATE.md | Plantilla de PR con checklist |

Modificaciones a archivos núcleo: **CLAUDE.md** gana "## Convenciones de Equipo"; **guia_desarrollo.md** etiqueta subfases por módulo con dependencias, paralelizables e hitos; **ROADMAP.md** añade columna "Módulo"; **estado-actual.md** añade tabla de estado por módulo. Al entregar, ofrecer generar el backlog como GitHub Issues + Project con `gh`.

---

## 12. Preguntas de entrevista adicionales (modo equipo)

Cuando hay 2+ devs (máx 3 por turno):

1. ¿Cuántos desarrolladores y qué nivel/rol? (calibra cuántos frentes paralelos abrir y a quién *sugerir* el módulo más delicado — como sugerencia, no asignación fija).
2. ¿Usarán GitHub/GitLab? ¿Quieren tablero en Markdown, GitHub Project, o ambos?
3. ¿Metodología impuesta (curso/empresa exige Scrum) o el Scrum-lite del kit?
4. ¿Dedicación full-time o part-time? (calibra iteración semanal vs quincenal).

> Nota: aunque los módulos NO se asignan fijo a personas, conocer el número de devs ayuda a decidir cuántos módulos conviene tener disponibles en paralelo y el tamaño de las iteraciones.
