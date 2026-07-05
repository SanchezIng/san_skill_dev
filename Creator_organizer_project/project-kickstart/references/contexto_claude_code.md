# Gestión de Contexto en Claude Code

Convenciones para que Claude Code nunca pierda contexto entre sesiones al desarrollar el proyecto. Estas reglas se aplican a CÓMO se diseñan las fases/subfases y a QUÉ archivos se generan.

---

## 1. División de fases en subfases

### Cuándo dividir

Una fase debe dividirse en subfases si cumple **al menos uno** de estos criterios:

- Cruza más de 2 capas (UI + API + DB en una sola fase)
- Introduce más de 5 archivos nuevos
- Modifica más de 8 archivos existentes
- El prompt principal de la fase superaría 30 líneas
- Toca más de un módulo funcional del proyecto
- El usuario pide explícitamente más granularidad

### Cómo dividir

La fase F{n} se convierte en F{n}.1, F{n}.2, ..., F{n}.k.

Cada subfase debe ser **atómica**:

- Una sola responsabilidad clara
- Idealmente una sola capa o módulo
- Producible en UNA sesión de Claude Code
- Con un entregable verificable

### Ejemplo: fase "Sistema de autenticación" dividida

```
F3.1 - Modelo de datos de usuarios y sesiones
F3.2 - Endpoints de registro y login (backend)
F3.3 - Middleware de autorización (backend)
F3.4 - Formularios de login/registro (frontend)
F3.5 - Persistencia de sesión y rutas protegidas (frontend)
F3.6 - Tests de integración del flujo completo
```

Cada subfase se completa, hace commit, y deja un handoff doc para la siguiente.

---

## 2. Handoff doc por subfase

Al cerrar una subfase, Claude Code escribe `progreso/fase-{n}.{m}.md`. Este archivo es lo PRIMERO que lee la siguiente subfase.

### Plantilla del handoff doc

```markdown
# Handoff F{n}.{m} → F{n}.{m+1}

**Subfase completada:** F{n}.{m} — {{título}}
**Fecha:** YYYY-MM-DD
**Commit:** {{hash corto}}

## ✅ Lo que se hizo

- {{archivo nuevo 1}}: {{qué hace}}
- {{archivo nuevo 2}}: {{qué hace}}
- {{archivo modificado}}: {{qué cambió}}

## 🧠 Decisiones tomadas en esta subfase

- {{Decisión 1 + breve justificación}}
- {{Decisión 2}}

## ⚠️ Cosas que descubrí durante el desarrollo

- {{Sorpresa 1: algo del stack/datos/restricción que no estaba claro antes}}
- {{Sorpresa 2}}

## 🔜 Para la siguiente subfase (F{n}.{m+1})

**Objetivo:** {{recordatorio del objetivo de la siguiente}}

**Contexto mínimo a cargar al arrancar la nueva sesión:**
- CLAUDE.md
- docs/guia_desarrollo.md (solo la sección de F{n}.{m+1})
- progreso/estado-actual.md
- progreso/fase-{n}.{m}.md (este archivo)
- {{archivos específicos que la siguiente subfase necesita ver}}

**Lo que NO necesita cargar:**
- {{archivos de subfases muy anteriores, listar para evitar tentación}}

## 🐛 Issues abiertos / TODOs

- [ ] {{TODO 1 que quedó pendiente y debe atenderse en F{n}.{m+1} o después}}
- [ ] {{TODO 2}}
```

---

## 3. Archivo `progreso/estado-actual.md`

Vista panorámica del estado del proyecto. Se actualiza al final de cada sesión (subfase o fase). Es lo SEGUNDO que Claude Code lee al arrancar una sesión nueva.

### Plantilla

```markdown
# Estado Actual del Proyecto

**Última actualización:** YYYY-MM-DD HH:MM
**Última subfase completada:** F{n}.{m} — {{título}}
**Próxima subfase:** F{n}.{m+1} — {{título}}

## Progreso global

- Fases completadas: {{X/N}}
- Subfases completadas: {{Y/M}}
- Porcentaje estimado: {{%}}

## Resumen de lo construido hasta ahora

{{3-5 líneas describiendo qué tiene el proyecto en este momento, sin detalles de implementación}}

## Decisiones técnicas vivas (las que afectan trabajo futuro)

- {{Decisión 1}}
- {{Decisión 2}}

## Issues abiertos del proyecto

- [ ] {{Issue 1}}
- [ ] {{Issue 2}}

## Deudas técnicas anotadas

- {{Deuda 1: qué es, en qué fase se debería atender}}
- {{Deuda 2}}
```

---

## 4. Indicador de cierre de sesión

CLAUDE.md debe incluir una sección con esta regla literal:

```markdown
## 🔌 Cuándo cerrar esta sesión de Claude Code

Cierra esta sesión y abre una nueva si:

- Llevas más de ~60% de tu ventana de contexto usada
- Has completado la subfase en curso
- Necesitas cambiar de módulo/capa drásticamente
- El usuario te pide hacer otra cosa fuera del scope de la subfase actual

**Antes de cerrar, SIEMPRE:**

1. Asegurar que los tests de la subfase pasan
2. Hacer commit con mensaje en Conventional Commits
3. Actualizar `progreso/estado-actual.md`
4. Crear/actualizar `progreso/fase-{n}.{m}.md` (handoff doc)
5. Si quedan TODOs, anotarlos en el handoff doc
```

---

## 5. Convenciones de archivos cortos y naming

### Archivos cortos

- Convención del proyecto: **ningún archivo de código supera ~300 líneas**
- Si se acerca al límite, se divide por responsabilidad
- Esta convención se documenta en CLAUDE.md y se aplica desde Fase 1

### Naming predecible

Nombres claros, en inglés, sin sufijos confusos:

✅ Bien: `services/auth.ts`, `models/user.py`, `components/LoginForm.tsx`

❌ Mal: `services/handler_v2_final.ts`, `models/utils_new.py`, `components/Form2.tsx`

Convenciones según tipo de archivo:

- Servicios/handlers: `{dominio}.{ext}` (`auth.ts`, `payments.ts`)
- Modelos/entidades: singular (`user.py`, no `users.py`)
- Componentes UI: PascalCase (`LoginForm.tsx`)
- Tests: `{nombre}.test.{ext}` o `test_{nombre}.{ext}`
- Migrations: `{timestamp}_{descripcion}.sql`

---

## 6. Archivos críticos marcados en CLAUDE.md

Sección obligatoria en CLAUDE.md: **"Archivos que NO tocar sin avisar"**.

Ejemplos de archivos típicamente críticos:

- `migrations/` — modifican el schema en prod
- `infra/prod.tf` o equivalentes de infraestructura
- `.github/workflows/` — pipelines de CI/CD
- `Dockerfile` y `docker-compose.yml` (en proyectos con docker)
- Archivos de configuración de auth/secrets

Claude Code debe pedir confirmación explícita antes de tocar cualquier archivo de esta lista.

---

## 7. Estructura evolutiva del repositorio

### Regla central

La estructura inicial es **mínima**: solo las carpetas necesarias para F1 o F1.1. Las carpetas posteriores se crean en la fase que las necesita, no antes.

### Cómo documentarlo en la guía

Cada fase/subfase declara explícitamente en su sección "📂 Estructura que introduce esta fase":

```markdown
### 📂 Estructura que introduce esta fase

**Carpetas nuevas:**
- `src/services/` — lógica de negocio
- `src/services/auth/` — autenticación

**Archivos nuevos:**
- `src/services/auth/login.ts`
- `src/services/auth/session.ts`

**Archivos que modifica:**
- `src/index.ts` (registra rutas nuevas)
- `.env.example` (agrega JWT_SECRET)
```

### Ventajas

- Claude Code, al iniciar F1, no se distrae con carpetas vacías para F7
- El usuario ve el proyecto crecer de forma comprensible
- Más fácil hacer revisiones de código por fase

---

## 8. Estimación de contexto por subfase

Al diseñar una subfase, estimar aproximadamente cuánto contexto consume:

- **Subfase ligera** (< 30% del contexto): toca 1-3 archivos pequeños, prompt < 15 líneas
- **Subfase media** (30-50%): toca 4-6 archivos, prompt 15-25 líneas
- **Subfase pesada** (50-70%): toca 7-10 archivos o lógica densa, prompt 25-30 líneas

Si una subfase tiende a **>70%**, debe dividirse otra vez. Una subfase ideal cabe holgadamente en una sesión con margen para iteración.

---

## 9. Lista de chequeo al diseñar la guia_desarrollo.md

Antes de dar por terminada la generación:

- [ ] Cada fase compleja tiene subfases atómicas
- [ ] Cada subfase tiene su sección de handoff a la siguiente
- [ ] Cada subfase declara qué estructura introduce
- [ ] La Fase 1 / F1.1 establece la estructura inicial mínima
- [ ] CLAUDE.md incluye el indicador de cierre de sesión
- [ ] CLAUDE.md incluye la lista de archivos críticos
- [ ] `progreso/estado-actual.md` se incluye como plantilla vacía
- [ ] Existe convención explícita de archivos cortos (~300 líneas máx)
- [ ] Existe convención explícita de naming
