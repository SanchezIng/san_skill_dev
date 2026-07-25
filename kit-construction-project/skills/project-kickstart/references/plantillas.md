# Plantillas de los Archivos Generados

Estructura EXACTA de cada archivo. Sigue estas plantillas al pie de la letra, sustituyendo los placeholders entre `{{...}}`.

## Lista de archivos a generar

**Núcleo (siempre):**
1. `CLAUDE.md`
2. `docs/especificaciones.md`
3. `docs/guia_desarrollo.md`

**Soporte (siempre):**
4. `ROADMAP.md`
5. `README.md` (humano)
6. `docs/glosario.md`
7. `progreso/estado-actual.md` (plantilla vacía)
8. `.gitignore`
9. `.env.example`
10. `.kickstart-state.json`

**Solo mediano/grande:**
11. `docs/adr/0001-decisiones-iniciales.md`
12. `docs/threat-model.md` (si datos medio/alto)

**Solo modo equipo (2+ devs):**
13. `docs/equipo.md`
14. `docs/backlog.md`
15. `progreso/tablero-equipo.md`
16. `.github/workflows/ci.yml`
17. `.github/PULL_REQUEST_TEMPLATE.md`

Las plantillas de `estado-actual.md`, handoff docs y ADR están en sus archivos de referencia respectivos. Las de los archivos de equipo (13-17) están en `trabajo_en_equipo.md` (secciones 3, 6, 9, 10 y 11), junto con las modificaciones que el modo equipo hace a CLAUDE.md, guia_desarrollo.md, ROADMAP.md y estado-actual.md.

---

## ARCHIVO 1: CLAUDE.md

```markdown
# CLAUDE.md — {{NOMBRE_PROYECTO}}

> **Archivo de contexto permanente para Claude Code.**
> Se lee automáticamente al abrir el proyecto.
> Contiene el resumen denso del proyecto y referencias a documentación detallada.

---

## 📌 Identidad del Proyecto

**Nombre:** {{NOMBRE_PROYECTO}}

**Descripción breve:** {{1-2 LINEAS}}

**Tipo:** {{TIPO}}

**Tamaño:** {{TAMAÑO}}

{{Si es académico: agregar Institución, Autores, Año}}

---

## 🎯 Problema y Solución

**Problema:** {{QUÉ PROBLEMA RESUELVE}}

**Solución:** {{CÓMO LO RESUELVE}}

**Funcionalidades principales:**
1. {{FUNCIONALIDAD 1}}
2. {{FUNCIONALIDAD 2}}

---

## 🏗️ Arquitectura General

{{Diagrama ASCII de la arquitectura si aplica}}

**Reglas inviolables de arquitectura:**
- {{REGLA 1}}
- {{REGLA 2}}

---

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
|------|-------------|
| {{capa1}} | {{tecs}} |
| {{capa2}} | {{tecs}} |

---

## 📂 Estructura del Repositorio (estado actual)

> Esta estructura **crece por fase**. Aquí está lo que existe en el commit actual.
> Cada fase de `docs/guia_desarrollo.md` declara qué carpetas y archivos nuevos introduce.

```
{{ESTRUCTURA ACTUAL EN ESTE COMMIT — solo lo que la fase actual ya creó}}
```

---

## 🗂️ DÓNDE ENCONTRAR CADA COSA

### docs/especificaciones.md

| Tema | Sección |
|------|---------|
| Roles y usuarios | 2 |
| Requisitos Funcionales | 3 |
| Requisitos No Funcionales | 4 |
| Seguridad (OWASP + ampliada) | 5 |
| Restricciones | 6 |
| Arquitectura y modelo de datos | 7 |
| Especificaciones técnicas detalladas | 8 |
| Infraestructura | 9 |
| Validación y métricas | 10 |
| Cumplimiento regulatorio | 11 (si aplica) |

### docs/guia_desarrollo.md

| Tema | Sección |
|------|---------|
| Mapa de fases y subfases | Inicio |
{{Listar las fases/subfases con sus números}}

### ROADMAP.md

Vista resumida del progreso. Consultar antes de empezar una sesión nueva.

### progreso/estado-actual.md

Snapshot del último cierre de sesión. LEER SIEMPRE al arrancar.

### progreso/fase-{n}.{m}.md

Handoff doc de la última subfase completada. LEER SIEMPRE al arrancar.

---

## 🔒 SEGURIDAD INVIOLABLE

### OWASP (reglas críticas)

{{Listar las reglas OWASP críticas para este proyecto en lenguaje accionable}}

### Secrets

- `.env` NUNCA al repo
- Si encuentras un secret hardcodeado: detente, reemplázalo con `process.env.X` / `os.environ['X']`, agrégalo a `.env.example` con valor dummy

### Logging

- NUNCA loggear: passwords, tokens, datos de tarjeta, PII completa
- Enmascarar emails, DNIs, números sensibles antes de loggear

### Dependencias

- Versiones pinneadas, lockfile comiteado
- Al añadir una dep nueva: revisar mantenimiento, vulnerabilidades, peso

---

## 🎨 Convenciones de Código

### Estilo

{{Por cada lenguaje del stack: estilo, convenciones, librerías permitidas}}

### Archivos cortos

**Regla:** ningún archivo de código supera ~300 líneas. Si se acerca, divide por responsabilidad.

### Naming

- Servicios/handlers: `{dominio}.{ext}` (`auth.ts`, no `handler_v2.ts`)
- Modelos: singular (`user.py`, no `users.py`)
- Componentes UI: PascalCase (`LoginForm.tsx`)
- Tests: `{nombre}.test.{ext}` o `test_{nombre}.{ext}`

### Git

- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- Branch principal: `main`
- Tags semánticos: `v1.0.0`

### Idioma

- {{Idioma elegido para docs/UI/comentarios}}
- Nombres de variables/funciones/clases: inglés (estándar)

---

## 🌐 Variables de Entorno

Ver `.env.example` para la lista completa. Variables sensibles:

```env
{{Variables más importantes del proyecto}}
```

---

## 📈 Métricas Objetivo

| Métrica | Meta |
|---------|------|
{{Métricas del proyecto}}

---

## 🚦 Estado Actual del Proyecto

Ver siempre `ROADMAP.md` y `progreso/estado-actual.md` para el estado más fresco.

**Fase activa actual:** {{Por iniciar — F1.1 / o la que toque}}

---

## 💻 Comandos Útiles del Proyecto

```bash
{{Comandos del proyecto: arranque, tests, lint, audit, etc.}}
```

---

## ⛔ ARCHIVOS QUE NO TOCAR SIN AVISAR

Pedir confirmación explícita al usuario antes de modificar:

- {{archivo crítico 1, ej: migrations/}}
- {{archivo crítico 2, ej: infra/prod.tf}}
- {{archivo crítico 3, ej: .github/workflows/}}
- {{archivo crítico 4 si aplica}}

---

## ⛔ COSAS QUE CLAUDE CODE NO DEBE HACER NUNCA

1. **No inventar requisitos.** Consultar `docs/especificaciones.md`
2. **No saltarse fases/subfases.** Respetar orden de `docs/guia_desarrollo.md`
3. **No mezclar componentes en archivos incorrectos**
4. **No usar bibliotecas fuera del stack** sin consultar
5. **No exponer credenciales en logs ni respuestas**
6. **No hardcodear valores que van en .env**
7. **No crear estructura de carpetas para fases futuras**
8. **No tocar archivos de la lista de "no tocar sin avisar"** sin pedir confirmación
{{Agregar reglas específicas del proyecto}}

---

## 🔌 Cuándo cerrar esta sesión de Claude Code

Cierra esta sesión y abre una nueva si:

- Llevas más de ~60% de tu ventana de contexto usada
- Has completado la subfase en curso
- Necesitas cambiar de módulo/capa drásticamente
- El usuario te pide hacer algo fuera del scope de la subfase actual

**Antes de cerrar, SIEMPRE:**

1. Asegurar que los tests de la subfase pasan
2. Hacer commit con mensaje en Conventional Commits
3. Actualizar `progreso/estado-actual.md`
4. Crear/actualizar `progreso/fase-{n}.{m}.md` (handoff doc)
5. Si quedan TODOs, anotarlos en el handoff doc

**Al arrancar una sesión nueva, SIEMPRE leer en este orden:**

1. CLAUDE.md (este archivo)
2. `progreso/estado-actual.md`
3. `progreso/fase-{n}.{m}.md` (el handoff más reciente)
4. Sección correspondiente de `docs/guia_desarrollo.md`

---

## 🆘 Cuando algo falla

{{Troubleshooting de errores comunes según el stack}}

---

## 📞 Referencia Rápida de Contexto

**¿Qué es esto?** {{Una frase}}
**¿Quién lo usa?** {{Una frase}}
**¿Cuántos usuarios concurrentes?** {{Número}}
**¿Entorno de ejecución?** {{Una frase}}

---

_Última actualización: {{FECHA}}_
_Versión del documento: 2.0_
```

---

## ARCHIVO 2: docs/especificaciones.md

```markdown
# Especificaciones Técnicas — {{NOMBRE_PROYECTO}}

## 1. INTRODUCCIÓN Y PROPÓSITO

{{Párrafo describiendo el documento como contrato técnico}}

## 2. ROLES Y USUARIOS DEL SISTEMA

### 2.1 Definición de Roles
{{Tabla de roles con permisos y restricciones}}

### 2.2 Gestión de Usuarios
{{Reglas de gestión}}

### 2.3 Concurrencia
{{Usuarios simultáneos esperados}}

## 3. REQUISITOS FUNCIONALES

### 3.1 Módulo {{X}}
- **RF-01.** {{Descripción}}
- **RF-02.** {{Descripción}}

### 3.2 Módulo {{Y}}
...

## 4. REQUISITOS NO FUNCIONALES

| ID | Categoría | Descripción |
|----|-----------|-------------|
| RNF-01 | Rendimiento | ... |
| RNF-02 | Disponibilidad | ... |
| RNF-03 | Mantenibilidad | Archivos < 300 líneas; naming consistente |
{{...}}

## 5. SEGURIDAD

### 5.1 OWASP Top 10 — Reglas aplicadas

{{Solo las reglas OWASP que correspondan, formateadas como requisitos}}

- **RNF-SEC-A01-1.** Control de acceso: ...
- **RNF-SEC-A02-1.** Cifrado: ...

### 5.2 Secrets Management

- **RNF-SEC-SEC-1.** `.env` siempre en `.gitignore`
- **RNF-SEC-SEC-2.** `.env.example` con valores dummy obligatorio
- **RNF-SEC-SEC-3.** Pre-commit hook con secrets scanner ({{gitleaks/detect-secrets}})
- **RNF-SEC-SEC-4.** {{Si vault: especificar gestor y método de acceso}}

### 5.3 Dependency Security

- **RNF-SEC-DEP-1.** Versiones pinneadas en {{package.json/requirements.txt/etc.}}
- **RNF-SEC-DEP-2.** Lockfile comiteado
- **RNF-SEC-DEP-3.** Comando de auditoría en checklist de cada fase: `{{npm audit / pip-audit / etc.}}`
- **RNF-SEC-DEP-4.** Revisión obligatoria antes de añadir librerías nuevas

### 5.4 Logging Seguro

- **RNF-SEC-LOG-1.** NO loggear: passwords, tokens, datos de tarjeta, PII completa
- **RNF-SEC-LOG-2.** Enmascarar emails, DNIs, números sensibles
- **RNF-SEC-LOG-3.** Niveles ERROR/WARN/INFO/DEBUG correctamente usados
- **RNF-SEC-LOG-4.** Logging estructurado en JSON

### 5.5 Hardening específico

{{Reglas adicionales según tipo de proyecto — ver seguridad_ampliada.md sección 7}}

### 5.6 Threat Modeling (solo mediano/grande con datos medio/alto)

Ver `docs/threat-model.md`.

### 5.7 Backup y Recovery (solo si persiste datos)

- **Qué se respalda:** {{...}}
- **Frecuencia:** {{...}}
- **Retención:** {{...}}
- **Dónde se guarda:** {{...}}
- **Cómo se restaura:** {{comandos exactos}}
- **Test de restore:** obligatorio en fase de despliegue

### 5.8 Reglas NO aplicadas y justificación

{{Si alguna regla del OWASP Top 10 se omite, justificar por qué no aplica}}

## 6. RESTRICCIONES Y EXCLUSIONES

### 6.1 Restricciones del proyecto
{{Tiempo, presupuesto, hardware, legales}}

### 6.2 Exclusiones (fuera del alcance)
{{Lista clara de qué NO se hace}}

## 7. ARQUITECTURA Y MODELO DE DATOS

### 7.1 Visión General
{{Descripción de la arquitectura}}

### 7.2 Modelo de Datos
{{Esquema de DB o estructura principal}}

### 7.3 Esquema de integración (API y comunicación)
{{Endpoints, eventos, protocolos}}

## 8. ESPECIFICACIONES TÉCNICAS DETALLADAS

### 8.1 Stack
{{Detalles técnicos: versiones, configuraciones, librerías}}

### 8.2 Testing Strategy

- **Unit tests:** {{framework + cobertura objetivo}}
- **Integration tests:** {{cuándo se ejecutan, qué cubren}}
- **E2E tests:** {{si aplica, qué flujos}}
- **CI/CD:** {{pipeline básico desde Fase 1/2}}

### 8.3 Convenciones de desarrollo

- Conventional Commits obligatorio
- Pre-commit hooks: linter, formatter, secrets scanner
- Archivos < 300 líneas
- Naming consistente (ver CLAUDE.md)
- {{Branching strategy}}

## 9. INFRAESTRUCTURA Y DESPLIEGUE

### 9.1 Hardware
{{Especificaciones}}

### 9.2 Variables de entorno
Ver `.env.example`. Lista completa de variables y para qué sirven.

### 9.3 Comandos de despliegue
{{Comandos exactos}}

## 10. EVALUACIÓN Y VALIDACIÓN

### 10.1 Métricas de éxito
| Métrica | Meta | Método de medición |
|---------|------|---------------------|
{{...}}

### 10.2 Casos de prueba
{{Escenarios concretos}}

### 10.3 Criterios mínimos de aprobación
{{Cuándo se considera completado}}

## 11. CUMPLIMIENTO REGULATORIO (solo si maneja PII)

### 11.1 Jurisdicción aplicable
{{GDPR / LGPD / Ley 29733 Perú / etc.}}

### 11.2 Datos personales que maneja el sistema
{{Lista}}

### 11.3 Bases legales de tratamiento
{{Consentimiento, contrato, obligación legal, interés legítimo}}

### 11.4 Derechos del titular implementados
- [ ] Acceso
- [ ] Rectificación
- [ ] Supresión / Olvido
- [ ] Portabilidad
- [ ] Oposición
- [ ] No ser objeto de decisiones automatizadas

### 11.5 Plazos
- Respuesta a solicitud de derechos: {{...}}
- Notificación de brecha: {{...}}
- Retención de datos: {{...}}

### 11.6 Cookies y política de privacidad
{{...}}
```

---

## ARCHIVO 3: docs/guia_desarrollo.md

```markdown
# Guía de Desarrollo Incremental — {{NOMBRE_PROYECTO}}

## Cómo usar esta guía

Esta guía está diseñada para desarrollar el sistema de forma incremental, una fase (o subfase) a la vez, usando Claude Code como asistente.

**Reglas de oro:**
- Una subfase = una sesión de Claude Code
- No saltar fases ni subfases (orden estricto)
- Commit + handoff doc al final de cada subfase
- Validar Definition of Done antes de avanzar

**Al arrancar cada sesión, leer en este orden:**
1. CLAUDE.md
2. `progreso/estado-actual.md`
3. El último handoff doc en `progreso/fase-X.Y.md`
4. La sección de la subfase que toca en esta guía

## Mapa General de Fases y Subfases

| Fase | Componente | Subfases | Duración | Acumulado |
|------|------------|----------|----------|-----------|
| F1 | {{...}} | {{F1.1, F1.2}} | {{...}} | {{...}} |
| F2 | {{...}} | sin subfases | {{...}} | {{...}} |
{{...}}

---

## FASE 1: {{TITULO}}

**Duración estimada:** {{X días/semanas}}
**Subfases:** {{N (si aplica)}}
**Sesiones Claude Code estimadas:** {{N}}
**Dependencia previa:** {{Ninguna / Fase X}}

### 🎯 Objetivo de la fase
{{Párrafo claro del objetivo general}}

### 📂 Estructura que introduce esta fase

**Carpetas nuevas:**
- {{carpeta1/}} — {{para qué}}
- {{carpeta2/}}

**Archivos nuevos al terminar la fase:**
- {{archivo 1}}
- {{archivo 2}}

**Archivos que se modifican:**
- {{archivo 1}} ({{qué cambia}})

{{Si tiene subfases, omitir las secciones de prompt/checklist aquí y mover a cada subfase}}

---

### SUBFASE 1.1: {{TITULO}}

**Sesión Claude Code:** 1
**Capa/módulo:** {{una sola}}

#### 🎯 Objetivo
{{Una sola responsabilidad clara}}

#### 📂 Contexto que cargar al arrancar
- `CLAUDE.md`
- `progreso/estado-actual.md`
- {{archivos específicos que esta subfase necesita}}

#### 📄 Archivos esperados al terminar
- {{archivo nuevo 1}}
- {{archivo nuevo 2}}

#### 💬 Prompt sugerido

```
{{PROMPT LITERAL COPY-PASTEABLE, MÁX 30 LÍNEAS}}
```

#### 🧪 Cómo probar

- **{{Qué probar}}:**
  ```
  {{comando}}
  ```
  Resultado esperado: {{...}}

#### ✅ Definition of Done

- [ ] Funcionalidad implementada según especificación
- [ ] Tests escritos y pasando
- [ ] Linter y formatter pasan
- [ ] Pre-commit hooks pasan
- [ ] Audit de dependencias pasa
- [ ] Commit hecho con Conventional Commits
- [ ] `progreso/estado-actual.md` actualizado
- [ ] `progreso/fase-1.1.md` creado (handoff a F1.2)

#### ⛔ Lo que NO debes hacer en esta subfase
- {{Cosa 1 que NO se implementa aquí}}
- {{Cosa 2}}

#### 🔜 Handoff a la siguiente

Al cerrar esta sesión, crea `progreso/fase-1.1.md` con:
- Lo que se hizo
- Decisiones tomadas
- Sorpresas encontradas
- Qué necesita F1.2 para arrancar

#### 💡 Tip
{{Consejo práctico}}

---

### SUBFASE 1.2: {{TITULO}}
{{Estructura idéntica a F1.1}}

---

## FASE 2: {{TITULO sin subfases}}

**Duración estimada:** {{...}}
**Sesiones Claude Code estimadas:** 1

### 🎯 Objetivo
{{...}}

### 📂 Estructura que introduce
{{...}}

### 💬 Prompt sugerido
```
{{...}}
```

### ✅ Definition of Done
{{checklist}}

### ⛔ Lo que NO debes hacer
{{...}}

---

## CIERRE DE LA GUÍA

Al completar las {{N}} fases tendrás:
- {{Logro 1}}
- {{Logro 2}}

### Después del proyecto
{{Sugerencias de publicación, mantenimiento, escalabilidad}}
```

---

## ARCHIVO 4: ROADMAP.md

```markdown
# Roadmap — {{NOMBRE_PROYECTO}}

> Vista panorámica del progreso. Actualizar manualmente al cerrar cada subfase.

**Inicio estimado:** {{Fecha}}
**Cierre estimado:** {{Fecha}}

## Leyenda

⏳ Pendiente · 🔄 En curso · ✅ Completada · ⚠️ Bloqueada · ⏸️ Pausada

## Estado general

| Métrica | Valor |
|---------|-------|
| Fases totales | {{N}} |
| Subfases totales | {{M}} |
| Completadas | 0 / {{M}} |
| % avance | 0% |

## Detalle por fase

### F1: {{TITULO}}
**Estado:** ⏳ Pendiente
**Subfases:**
- ⏳ F1.1 — {{título}}
- ⏳ F1.2 — {{título}}

### F2: {{TITULO}}
**Estado:** ⏳ Pendiente
**Subfases:** sin subfases

### F3: {{TITULO}}
**Estado:** ⏳ Pendiente
**Subfases:**
- ⏳ F3.1 — {{título}}
- ⏳ F3.2 — {{título}}
- ⏳ F3.3 — {{título}}

{{...todas las fases...}}

## Hitos clave (milestones)

- **M1 — MVP funcional:** al cerrar F{{N}}
- **M2 — Beta pública:** al cerrar F{{N}}
- **M3 — V1.0:** al cerrar F{{N}}

## Bitácora de cierres

> Anotar fecha y commit cada vez que se cierra una subfase.

| Fecha | Subfase | Commit | Notas |
|-------|---------|--------|-------|
| {{YYYY-MM-DD}} | F1.1 | {{hash}} | {{nota breve}} |
```

---

## ARCHIVO 5: README.md (humano)

Ver `references/practicas_dev.md` sección 4 para la plantilla completa.

---

## ARCHIVO 6: docs/glosario.md

```markdown
# Glosario — {{NOMBRE_PROYECTO}}

> Términos del dominio del proyecto. Mantén esta lista actualizada conforme aparezcan términos nuevos.

## Términos del negocio

### {{Término 1}}
**Definición:** {{Una frase clara}}
**Contexto en el sistema:** {{Cómo se materializa en el código/UI}}
**Ejemplo:** {{Ejemplo concreto}}

### {{Término 2}}
{{...}}

## Términos técnicos del proyecto

### {{Término técnico 1}}
**Definición:** {{...}}
**Dónde aparece:** {{archivos/módulos relevantes}}

## Acrónimos

| Acrónimo | Significado | Contexto |
|----------|-------------|----------|
| {{ACR}} | {{Expansión}} | {{Donde aplica}} |

## Términos del dominio externo

{{Si el proyecto está en un dominio especializado: medicina, finanzas, legal, juegos, etc., listar términos técnicos del dominio que el código maneja}}
```

---

## ARCHIVO 7: progreso/estado-actual.md (plantilla vacía inicial)

Ver `references/contexto_claude_code.md` sección 3 para la plantilla completa.

---

## ARCHIVO 8: .gitignore (según stack)

Generar según el stack elegido. Plantillas base:

**Node/TypeScript:**
```
node_modules/
dist/
build/
.env
.env.local
.env.*.local
*.log
.DS_Store
coverage/
.next/
.turbo/
```

**Python:**
```
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
.env
.env.local
dist/
build/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
```

**Rust:**
```
target/
Cargo.lock # solo si es librería; comitearlo si es binario
.env
```

**Java:**
```
target/
build/
*.class
.idea/
.vscode/
.env
```

Agregar siempre:
```
# Specifics del proyecto
.kickstart-state.json # SI el usuario quiere que sea privado; alternativa: comitearlo
progreso/.tmp/
```

---

## ARCHIVO 9: .env.example

Ver `references/seguridad_ampliada.md` sección 1 para plantillas por stack.

---

## ARCHIVO 10: .kickstart-state.json

```json
{
  "version": "2.0",
  "fecha_generacion": "YYYY-MM-DD",
  "skill_version": "project-kickstart v2.0",
  "proyecto": {
    "nombre": "...",
    "descripcion": "...",
    "tipo": "...",
    "tamaño": "..."
  },
  "config": {
    "idioma": "español|inglés",
    "formato": "md|md+docx",
    "modo": "completo|rapido"
  },
  "contexto_inicial": {
    "tenia_contexto_previo": true,
    "archivos_referenciados": []
  },
  "stack": {
    "lenguaje_principal": "...",
    "framework": "...",
    "base_datos": "...",
    "otros": []
  },
  "arquitectura": "...",
  "seguridad": {
    "owasp_aplicado": "basico|asvs_l1|asvs_l2",
    "ampliada": ["secrets", "deps", "logging", "threat_model", "backup", "regulacion"],
    "regulacion": "gdpr|lgpd|ley29733|none"
  },
  "practicas_dev": {
    "testing_strategy": "...",
    "pre_commit_hooks": ["..."],
    "adr_inicial": true,
    "branching": "trunk|gitflow|simple"
  },
  "respuestas_entrevista": {
    "usuarios_roles": "...",
    "funcionalidades_top": [],
    "restricciones": "...",
    "datos_sensibilidad": "bajo|medio|alto",
    "entorno_ejecucion": "...",
    "criterio_exito": "..."
  },
  "fases_planeadas": [
    {
      "id": "F1",
      "titulo": "...",
      "subfases": [
        {"id": "F1.1", "titulo": "..."},
        {"id": "F1.2", "titulo": "..."}
      ]
    }
  ]
}
```

---

## ARCHIVO 11: docs/adr/0001-decisiones-iniciales.md (solo mediano/grande)

Ver `references/practicas_dev.md` sección 3 para la plantilla y ejemplos.

---

## ARCHIVO 12: docs/threat-model.md (solo si datos medio/alto)

Ver `references/seguridad_ampliada.md` sección 4 para la plantilla completa.

---

## Variaciones según tamaño del proyecto

### Pequeño (3-5 fases, mayoría sin subfases)

- CLAUDE.md: versión completa pero sin secciones opcionales (sin threat model, sin métricas detalladas)
- especificaciones.md: sin sección 11 (regulación) salvo que aplique, OWASP básico
- guia_desarrollo.md: fases sin subfases mayormente; prompts breves
- ROADMAP.md: simple
- README.md: simple
- glosario.md: si hay dominio especializado, si no, opcional
- ADR: solo si hay decisión técnicamente compleja
- threat-model.md: omitido salvo datos sensibles

### Mediano (6-9 fases, subfases en 1-3 fases)

- Todo lo anterior + ADR-0001 obligatorio
- OWASP nivel ASVS L1
- Testing con cobertura ≥60%
- CI básico en Fase 1 o 2
- threat-model.md si maneja datos personales

### Grande (10-15 fases, subfases en ≥4 fases)

- Todo lo anterior + múltiples ADRs (uno por decisión arquitectural)
- OWASP nivel ASVS L2
- Testing con cobertura ≥70-80% + E2E
- CI/CD completo con staging
- threat-model.md obligatorio
- Métricas y observabilidad en especificaciones
- Plan de rollback documentado por fase
