---
name: project-kickstart
description: Convierte una idea de proyecto en un kit completo de documentación lista para desarrollar con Claude Code (CLAUDE.md, especificaciones.md, guia_desarrollo.md, ROADMAP.md, README.md, glosario, ADRs). Úsala SIEMPRE cuando el usuario diga "tengo una idea", "kickstart", "nuevo proyecto", "quiero empezar a desarrollar", "ayúdame a estructurar mi proyecto", "preparar para Claude Code", "documentar desde cero", "dividir mi proyecto en fases", o describa una idea de app/sistema/script/bot/juego sin estructura formal. Cubre web, APIs, móviles, escritorio, scripts, bots IA y videojuegos, con OWASP, seguridad ampliada, mejores prácticas dev (tests, hooks, ADRs, Conventional Commits), subfases atómicas para preservar contexto entre sesiones, y estructura evolutiva. Incluye modo equipo para 2+ devs (módulos independientes reclamables con tablero vivo, backlog con dependencias, PR/CI, Scrum-lite) — actívalo también si dicen "somos X desarrolladores", "trabajo en equipo" o "repartir tareas entre devs".
---

# Project Kickstart

Convierte cualquier idea de proyecto en un kit de documentación listo para desarrollar con Claude Code. El kit está diseñado para que **cada sesión de Claude Code arranque con el contexto mínimo necesario** y nunca tenga que cargar todo el proyecto a la vez.

## Lo que se genera

**Núcleo (siempre):**

1. **CLAUDE.md** — contexto permanente que Claude Code lee siempre. Incluye mapa de archivos críticos, indicador de cierre de sesión y referencias a los otros archivos
2. **especificaciones.md** — requisitos funcionales, no funcionales, arquitectura, seguridad ampliada
3. **guia_desarrollo.md** — fases (y subfases atómicas donde apliquen) con prompts copy-pasteables

**Soporte (siempre):**

4. **ROADMAP.md** — vista resumida de todas las fases/subfases con su estado
5. **README.md** — para humanos (devs que se sumen al proyecto), no para Claude
6. **docs/glosario.md** — términos del dominio del proyecto
7. **progreso/estado-actual.md** — snapshot vacío que cada sesión de Claude Code actualiza al cerrar
8. **.gitignore** y **.env.example** según el stack

**Opcional según tamaño:**

9. **docs/adr/0001-decisiones-iniciales.md** — Architecture Decision Record (mediano/grande)
10. **docs/threat-model.md** — modelo de amenazas ligero (mediano/grande con datos sensibles)

**Estructura inicial mínima** del repositorio: SOLO las carpetas necesarias para la Fase 1 (o subfase F1.1). Las fases posteriores indican explícitamente qué carpetas y archivos nuevos introducen. Nunca se crea el árbol completo desde el día cero.

## Cuándo activarte

Triggers explícitos: "tengo una idea", "kickstart", "nuevo proyecto", "preparar para Claude Code", "armar la guía", "crear especificaciones desde cero", "dividir el proyecto en fases", "que Claude Code no pierda contexto".

Triggers implícitos: el usuario describe una idea de aplicación, sistema, bot, script o juego sin tener documentación formal y muestra intención de desarrollarla.

No activarte si: el usuario ya tiene un proyecto en marcha y solo pide un cambio puntual, o si está depurando código existente.

## Modo de operación

Dos modos posibles:

- **Modo completo (default):** entrevista guiada por bloques, máximo 3 preguntas por turno. Recomendado para proyectos medianos/grandes o usuarios que no tienen aún clara la idea.
- **Modo rápido:** una sola tanda de preguntas comprimidas, sin bloques separados. Solo si el usuario explícitamente lo pide ("modo rápido", "soy experto", "voy con prisa") o si en el Paso 0 trajo contexto muy completo.

En modo rápido: combina los Pasos 2–6 en una sola tanda de preguntas (todas a la vez, con `ask_user_input_v0` agrupando todo), salta confirmaciones intermedias, ve directo al Paso 7 (resumen).

## Flujo de trabajo

Sigue estos pasos EN ORDEN. No saltes pasos. No generes archivos antes de completar la entrevista.

### Paso 0 — Contexto inicial del usuario

ANTES de cualquier otra cosa, pregunta:

> "¿Tienes algún contexto previo que deba leer antes de empezar? Por ejemplo: notas tuyas sobre la idea, un documento de requisitos anterior, mockups o screenshots de la UI, código de proyectos similares, transcripción de una reunión, links a referencias, esquemas dibujados, etc."

Si el usuario tiene archivos, pídele que los adjunte y léelos antes de seguir. Úsalos para:

- Pre-rellenar parte de la entrevista (no preguntes lo que ya está claro en el contexto)
- Detectar si ya hay decisiones técnicas tomadas (stack, arquitectura, datos)
- Identificar contradicciones o ambigüedades y preguntarlas explícitamente

Si trae contexto MUY completo (ej: un PRD detallado), ofrece pasar a **modo rápido** automáticamente.

Si no tiene contexto previo, continúa al Paso 1.

### Paso 1 — Recibir la idea

El usuario describirá su idea libremente. Escucha sin interrumpir. Si la descripción es muy corta (1-2 líneas) y no hubo contexto en Paso 0, pídele que amplíe en 3-4 frases qué quiere construir y para qué.

Si en el Paso 0 trajo un documento que ya describe la idea, sáltate esta etapa.

### Paso 2 — Configuración inicial

Pregunta con `ask_user_input_v0` (una sola llamada con las 4 preguntas):

1. **Modo:** completo (con entrevista por bloques) / rápido (todo de una)
2. **Idioma de los archivos:** español / inglés
3. **Formato de entrega:** solo Markdown / Markdown + Word (.docx)
4. **Stack tecnológico:** ya lo tengo definido / quiero recomendación

### Paso 3 — Clasificación del proyecto

Identifica el TIPO con `ask_user_input_v0`. Las opciones:

- Web app con usuarios (frontend + backend)
- API REST pura (sin frontend)
- App móvil (iOS/Android)
- App de escritorio
- Script o automatización
- Bot o agente IA
- Videojuego
- Otro (que el usuario describa)

En la misma llamada, pregunta el TAMAÑO:

- **Pequeño:** 1 desarrollador, < 1 mes, < 5 funcionalidades principales
- **Mediano:** 1-3 desarrolladores, 1-6 meses, 5-15 funcionalidades
- **Grande:** 3+ desarrolladores, 6+ meses, 15+ funcionalidades

En la misma llamada, pregunta el NÚMERO DE DESARROLLADORES:

- 1 (solo yo)
- 2-3
- 4 o más

Si son **2 o más desarrolladores**, se activa el **modo equipo**: lee `references/trabajo_en_equipo.md` antes del Paso 4 y añade sus preguntas de entrevista (roles, GitHub/Issues, metodología impuesta o Scrum-lite, dedicación).

El TAMAÑO determina:

- Arquitectura recomendada (ver `references/arquitecturas.md`)
- Nivel de detalle de la guía (resumida vs detallada con prompts)
- Nivel de OWASP aplicado (básico / ASVS L1 / ASVS L2)
- Cantidad de subfases probable (más grande = más subdivisión)
- Si se genera ADR y threat-model.md (mediano/grande)

El NÚMERO DE DEVS determina (ver `references/trabajo_en_equipo.md`):

- Si se activa el modo colaborativo (módulos independientes reclamables + tablero vivo)
- Cuántos frentes paralelos conviene abrir y el tamaño de las iteraciones
- Si se generan docs/equipo.md, docs/backlog.md, progreso/tablero-equipo.md, CI y plantilla de PR
- Si el CLAUDE.md incluye la sección de Convenciones de Equipo

**Importante:** el número de módulos lo define la ARQUITECTURA del dominio, NO el número de devs. Los módulos NO se asignan fijo a personas: son unidades de trabajo que cualquier dev reclama del tablero cuando están disponibles. El modo colaborativo funciona igual con 1 dev (mapa de avance) que con 5 (trabajo en paralelo), y sumar/quitar devs no exige rediseñar nada.

### Paso 4 — Entrevista específica por tipo

Lee `references/preguntas_por_tipo.md`. Sigue las preguntas indicadas para el tipo. En **modo completo**, agrupa por bloques (máx 3 preguntas por turno). En **modo rápido**, comprime todo en 1-2 tandas grandes.

Bloques mínimos para CUALQUIER proyecto:

- Usuarios y roles
- Funcionalidades principales (top 5-10)
- Restricciones (tiempo, presupuesto, hardware, legales)
- Datos que maneja (sensibilidad: bajo/medio/alto)
- Entorno de ejecución (local, LAN, internet público, cloud)
- Validación y criterio de éxito

Bloques adicionales según tipo:

- **Web app / API:** autenticación, endpoints clave, base de datos
- **Móvil:** plataformas objetivo, online/offline, notificaciones
- **Escritorio:** SO objetivo, instalador, actualizaciones
- **Script:** ejecución manual o programada, entrada/salida
- **Bot IA:** plataforma (Telegram/WhatsApp/Discord/web), proveedor LLM, manejo de contexto
- **Videojuego:** género, motor (Unity/Godot/etc.), 2D/3D, plataforma

### Paso 5 — Stack tecnológico

Si el usuario eligió "ya tengo stack definido": pídele que lo describa (lenguajes, frameworks, base de datos, etc.).

Si eligió "quiero recomendación": lee `references/stacks_recomendados.md` y propón un stack según tipo + tamaño. Justifica brevemente cada elección.

Confirma el stack final antes de continuar.

### Paso 6 — Seguridad

Cubre dos capas:

**6.1 OWASP (siempre):** lee `references/owasp_por_tipo.md` y determina las reglas según tipo, sensibilidad de datos, entorno y si maneja pagos. Presenta el paquete al usuario; NO le hagas escoger reglas individuales.

**6.2 Seguridad ampliada (siempre):** lee `references/seguridad_ampliada.md` y determina qué reglas adicionales aplicar:

- Secrets management (siempre, todos los proyectos)
- Dependency security (siempre, todos los proyectos)
- Logging seguro (qué no loggear)
- Threat modeling ligero (solo mediano/grande con datos sensibilidad medio/alto)
- Backup/recovery strategy (proyectos que persistan datos)
- GDPR/LGPD/regulación regional (si maneja datos personales)

Informa al usuario qué reglas se aplicarán y pregunta si está de acuerdo o quiere ajustes.

### Paso 7 — Confirmación y resumen

Antes de generar archivos, muestra un resumen breve:

| Aspecto | Valor |
|---------|-------|
| Tipo | ... |
| Tamaño | ... |
| Stack | ... |
| Arquitectura | ... |
| OWASP | ... |
| Seguridad ampliada | ... (lista breve) |
| Mejores prácticas dev | ... (testing, hooks, ADRs) |
| Idioma | ... |
| Formato | ... |
| Modo | completo / rápido |
| Nº estimado de fases | ... (X fases, Y subfases) |

Pregunta si todo bien para proceder o si quiere cambiar algo.

### Paso 8 — Detección de fases complejas y división en subfases

ANTES de redactar `guia_desarrollo.md`, analiza cada fase planeada y decide si debe dividirse en subfases.

**Criterios para dividir una fase en subfases** (si cumple ≥1, dividir):

- Cruza más de 2 capas (ej: UI + API + DB en una sola fase)
- Introduce más de 5 archivos nuevos
- Modifica más de 8 archivos existentes
- El prompt principal superaría 30 líneas
- Toca más de un módulo funcional
- El usuario explícitamente pide más granularidad

Cuando una fase debe dividirse, conviértela en F{n}.1, F{n}.2, ... F{n}.k. Cada subfase:

- Es atómica: una sola responsabilidad, idealmente una sola capa o módulo
- Equivale a UNA sola sesión de Claude Code
- Produce un **handoff doc** (`progreso/fase-{n}.{m}.md`) que la siguiente subfase lee al arrancar
- Tiene su propio checklist de aceptación

Lee `references/contexto_claude_code.md` para las convenciones detalladas de subfases, handoff docs, `estado-actual.md` y los indicadores de "cierra esta sesión".

**Si hay 2+ devs (modo colaborativo):** aplica además las secciones 2, 3 y 5 de `references/trabajo_en_equipo.md`: divide la arquitectura en módulos verticales **por dominio** (cantidad según el dominio, no según el número de devs) con fronteras de interfaz, etiqueta cada subfase con su módulo `[A]/[B]/[C]` y sus dependencias, marca las paralelizables, define F1 como fase compartida de arranque a cargo de un solo dev, y cierra cada fase con un hito de integración sin mocks. Los módulos NO se asignan fijo a personas: se reclaman del tablero vivo. Los handoff docs pasan a ser por módulo: `progreso/fase-{n}.{m}-{modulo}.md`.

### Paso 9 — Generación de archivos

Lee `references/plantillas.md` para la estructura exacta de cada archivo. Genera, en este orden:

**Núcleo:**

1. `CLAUDE.md` con: mapa de archivos críticos, archivos que NO tocar, indicador "si llevas X tokens cierra sesión", referencias a los otros docs
2. `docs/especificaciones.md` con secciones de OWASP + seguridad ampliada integradas
3. `docs/guia_desarrollo.md` con fases y subfases. Cada subfase tiene: objetivo, archivos esperados, prompt literal copy-pasteable, comandos de prueba, checklist, "lo que NO hacer", "handoff a la siguiente"

**Soporte:**

4. `ROADMAP.md` — tabla resumida fase/subfase/estado
5. `README.md` (humano) — qué es el proyecto, cómo correrlo, cómo contribuir
6. `docs/glosario.md` — términos del dominio
7. `progreso/estado-actual.md` — plantilla vacía con campos a llenar al cerrar cada sesión
8. `.gitignore` específico para el stack
9. `.env.example` con todas las variables vacías o con valores dummy
10. `.kickstart-state.json` — snapshot de la entrevista (decisiones, respuestas, fecha)

**Solo si mediano/grande:**

11. `docs/adr/0001-decisiones-iniciales.md` con las decisiones clave del Paso 5-6
12. `docs/threat-model.md` (solo si hay datos sensibilidad medio/alto)

**Solo en modo colaborativo (2+ devs), según `references/trabajo_en_equipo.md`:**

13. `docs/equipo.md` — catálogo de módulos con estado (Disponible/En progreso/Bloqueado/Terminado), fronteras, reglas de convivencia, metodología
14. `docs/backlog.md` — backlog inicial con tareas T-nnn, módulo, dependencias, criterios de aceptación y estado
15. `progreso/tablero-equipo.md` — tablero vivo en Markdown (módulos + tareas + log append-only de reclamos)
16. `.github/workflows/ci.yml` — lint + análisis estático + tests + auditoría de deps, adaptado al stack
17. `.github/PULL_REQUEST_TEMPLATE.md` — plantilla con módulo, tarea y checklist

En modo colaborativo, además: CLAUDE.md incluye la sección `## 👥 Convenciones de Equipo`, ROADMAP.md gana la columna "Módulo" y `progreso/estado-actual.md` incluye la tabla de estado por módulo. Al entregar, ofrece generar el backlog como GitHub Issues + Project con `gh` (opción B del tablero) si el usuario lo desea; se pueden usar ambos tableros (Markdown + GitHub) con uno como espejo.

**Estructura inicial del repo:** crea SOLO las carpetas necesarias para la Fase 1 (o F1.1). Por ejemplo, no crees `tests/`, `migrations/`, `docs/api/` si la Fase 1 no los necesita; la guía indicará en qué fase posterior se introducen.

Cantidad de fases según tamaño:

- Pequeño: 3-5 fases, subfases solo donde sea estrictamente necesario
- Mediano: 6-9 fases, subfases en 1-3 fases típicamente
- Grande: 10-15 fases, subfases en al menos 4-5 fases

Si el usuario eligió "Markdown + Word", genera primero los .md y luego convierte los principales (CLAUDE.md, especificaciones.md, guia_desarrollo.md, ROADMAP.md, README.md) a .docx con la skill `docx`.

### Paso 10 — Entrega y guía de arranque

Usa `present_files` para entregar TODOS los archivos generados. En el mensaje final incluye:

- Resumen de cada archivo y para qué sirve
- Pasos exactos para usar el kit con Claude Code:
  1. Crear repo git (`git init`, primer commit, push opcional)
  2. Colocar archivos en raíz / `docs/` / `progreso/` según corresponda
  3. Instalar requisitos previos (Docker, Git, Node, Python, etc. según stack)
  4. Abrir Claude Code en la raíz del repo
  5. Decir literalmente: `"Lee CLAUDE.md y empieza la Fase 1.1"` (o `"Fase 1"` si no hay subfases)
- Recordatorio: al cerrar cada sesión de Claude Code, actualizar `progreso/estado-actual.md` y crear el handoff doc de la subfase correspondiente
- **En modo equipo, además:** subir el repo a GitHub/GitLab ANTES de empezar (el repo compartido es la fuente de verdad), crear el Project/tablero desde docs/backlog.md (ofrecer hacerlo con `gh`), acordar quién ejecuta la F1 compartida, y que cada dev arranque sus sesiones con: `"Lee CLAUDE.md y el handoff de mi módulo ({X}); continúo con la tarea T-{nnn}"`
- Ofrecer: si quiere regenerar solo un archivo después, puede pedir "regenera el README" o "actualiza el ROADMAP" — está todo guardado en `.kickstart-state.json`

## Reglas de gestión de contexto en Claude Code

Estas reglas se aplican AL DISEÑAR las fases/subfases y los archivos generados. Para detalles, lee `references/contexto_claude_code.md`.

1. **Archivos cortos por defecto.** Convención del proyecto: ningún archivo de código supera ~300 líneas. Si lo hace, se divide.
2. **Naming predecible.** Convenciones de nombres claras y consistentes para que Claude Code encuentre archivos rápido (ej: `services/auth.ts`, no `services/handler_v2_final.ts`).
3. **Cada subfase = una sesión.** El handoff doc resume qué se hizo y qué viene.
4. **Indicador de cierre de sesión.** En CLAUDE.md incluir: "Si llevas más de ~60% de tu contexto usado, cierra esta sesión: actualiza `progreso/estado-actual.md`, crea/actualiza el handoff doc de la subfase, y empieza una sesión nueva."
5. **Archivos críticos marcados.** Sección "archivos que NO tocar sin avisar" en CLAUDE.md (ej: `migrations/`, `infra/prod.tf`).
6. **Estructura evolutiva.** La guía explícitamente indica qué carpetas/archivos introduce cada fase. Nunca crear estructura para fases futuras.

## Reglas de seguridad ampliada

Estas se INTEGRAN a las especificaciones generadas, no en apartado separado. Detalle en `references/seguridad_ampliada.md`.

1. **Secrets management:** `.env` siempre en `.gitignore`, `.env.example` con dummies, política explícita de "nunca comitear secrets", uso de variables de entorno o vault según escala
2. **Dependency security:** pinning de versiones, comando de auditoría en checklist de cada fase (`npm audit`, `pip-audit`, `cargo audit`), revisión antes de añadir librería nueva
3. **Logging seguro:** lista explícita de qué NO loggear (PII, tokens, contraseñas, datos de tarjeta, secretos)
4. **Threat modeling ligero** (mediano/grande con datos medio/alto): documento de 1 página con activos, amenazas top, mitigaciones
5. **Backup/recovery** (si persiste datos): estrategia de backup, frecuencia, cómo restaurar, dónde se guarda
6. **Regulación de datos** (si maneja PII): nota de GDPR/LGPD/jurisdicción aplicable con derechos del titular y plazos

## Reglas de mejores prácticas dev

Detalle en `references/practicas_dev.md`.

1. **Testing strategy desde Fase 1.** Definir qué se testea (unit/integration/e2e) y con qué cobertura mínima por fase. Proyectos pequeños: al menos tests de las funciones críticas. Mediano/grande: cobertura ≥60% en lógica de negocio
2. **Pre-commit hooks básicos:** linter, formatter, secrets scanner (ej: `gitleaks`, `detect-secrets`). Setup en Fase 1
3. **ADRs (Architecture Decision Records):** proyectos mediano/grande tienen `docs/adr/`. Decisiones de impacto largo plazo se documentan ahí
4. **README.md humano:** distinto del CLAUDE.md. Orientado a personas: qué es, cómo correr, cómo contribuir, cómo deployar
5. **Conventional Commits** como convención por defecto (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
6. **Definition of Done por fase:** criterios verificables (tests pasan, lint pasa, checklist completo, commit hecho)

## Reglas de calidad de los archivos generados

**Inviolables:**

1. Los archivos deben ser autocontenidos. El usuario los debe poder usar sin necesitar más contexto de esta conversación
2. Los prompts dentro de la guía deben ser literales y copy-pasteables. Nada de "haz algo similar a esto"
3. Cada fase/subfase debe tener: objetivo claro, archivos esperados, prompts (si aplica), comandos de prueba, checklist de aceptación, "qué NO hacer", instrucciones de handoff a la siguiente
4. La sección de seguridad debe estar integrada a las especificaciones, no en apartado separado
5. CLAUDE.md incluye el mapa de dónde encontrar cada cosa en los otros archivos para optimizar tokens
6. Idioma consistente en todos los archivos. Si es español, todo en español (excepto nombres de archivos/variables/funciones que siempre son en inglés)
7. La estructura de carpetas inicial es MÍNIMA. Nunca crear carpetas para fases futuras

## Persistencia del progreso

Guarda en `.kickstart-state.json` (con la skill ejecutándose en el directorio temporal de trabajo) toda la información de la entrevista. Estructura:

```json
{
  "version": "2.0",
  "fecha": "YYYY-MM-DD",
  "proyecto": {
    "nombre": "...",
    "tipo": "...",
    "tamaño": "...",
    "num_devs": 1,
    "modo_equipo": false
  },
  "equipo": {
    "modulos": [],
    "metodologia": "scrum-lite",
    "usa_github_issues": false
  },
  "config": {
    "idioma": "...",
    "formato": "...",
    "modo": "..."
  },
  "stack": { },
  "respuestas_entrevista": { },
  "decisiones_seguridad": [],
  "fases_planeadas": []
}
```

Esto permite al usuario:

- Retomar la entrevista si se cortó
- Pedir "regenera solo el README" o "actualiza el ROADMAP" sin re-entrevistar
- Tener trazabilidad de las decisiones

## Manejo de errores y edge cases

- **Usuario muy vago:** si después de 2 intentos no logras clasificar el tipo, ofrécele 3 ejemplos concretos para que elija el más parecido
- **Tipo "Otro":** pídele que describa el proyecto en detalle y adapta el flujo manualmente, usando las plantillas más cercanas
- **Usuario que pide saltarse pasos:** ofrécele modo rápido en vez de saltar pasos individuales. Sin información mínima no hay buenos archivos
- **Mezcla de tipos** (web + móvil + API): genera la documentación tratándolo como proyecto grande con múltiples subcomponentes, cada uno con sus propias fases
- **Proyecto ya iniciado:** pregunta si quiere documentar lo existente (entonces salta entrevista, pide que comparta su código) o si quiere replantearlo desde cero
- **Contexto inicial contradice respuestas posteriores:** señala la contradicción y pregunta cuál vale

## Archivos de referencia

Lee estos archivos cuando los necesites. NO los leas todos al inicio — cárgalos solo cuando los uses:

- `references/preguntas_por_tipo.md` — preguntas específicas según tipo de proyecto
- `references/arquitecturas.md` — qué arquitectura recomendar según tamaño y tipo
- `references/stacks_recomendados.md` — stacks tecnológicos por tipo y tamaño
- `references/owasp_por_tipo.md` — reglas OWASP a aplicar según el caso
- `references/seguridad_ampliada.md` — secrets, dependencias, threat modeling, logging, backup, regulación
- `references/practicas_dev.md` — testing, hooks, ADRs, Conventional Commits, README humano, DoD
- `references/contexto_claude_code.md` — subfases, handoff docs, estado-actual, indicadores de cierre de sesión
- `references/trabajo_en_equipo.md` — modo colaborativo: módulos independientes reclamables, tablero vivo (Markdown + GitHub), backlog con dependencias, PR/CI, Scrum-lite (leer SOLO si hay 2+ devs)
- `references/plantillas.md` — estructura exacta de TODOS los archivos a generar

## Buenas prácticas durante la entrevista

- Una conversación a la vez, no satures con muchas preguntas (máx 3 por turno en modo completo)
- Reformula la idea del usuario con tus palabras y pregúntale si lo entendiste bien
- Si detectas inconsistencias (ej: dice "proyecto pequeño" pero menciona 20 funcionalidades), señálalo amablemente
- Sé pragmático: si el usuario claramente sabe lo que quiere, no le hagas preguntas obvias
- Si el usuario trajo contexto inicial muy completo, ofrece modo rápido proactivamente
- Al final ofrece la opción de "regenerar archivo X" usando el `.kickstart-state.json`
