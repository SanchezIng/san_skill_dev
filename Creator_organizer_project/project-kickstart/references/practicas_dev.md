# Mejores Prácticas de Desarrollo

Reglas que se integran en `especificaciones.md` y se aplican en cada fase/subfase de `guia_desarrollo.md`.

---

## 1. Testing Strategy

### Niveles de testing

- **Unit tests:** prueban funciones/clases aisladas (sin BD, sin red)
- **Integration tests:** prueban módulos juntos (con BD de test, mocks de servicios externos)
- **E2E tests:** prueban flujos completos como usuario (Playwright, Cypress, Detox)

### Qué se testea por tamaño de proyecto

**Pequeño:**

- Unit tests de la lógica de negocio crítica (mínimo: las funciones que tocan dinero, auth o datos sensibles)
- 1-2 tests de integración del happy path
- Sin E2E obligatorios

**Mediano:**

- Unit tests con cobertura ≥60% en lógica de negocio
- Integration tests de todos los endpoints/casos de uso principales
- E2E para los 3-5 flujos críticos
- Tests de regresión cuando se fixea un bug

**Grande:**

- Unit tests con cobertura ≥70-80% en lógica de negocio
- Integration tests exhaustivos
- E2E para todos los flujos críticos
- Performance tests para endpoints de alto tráfico
- Security tests automatizados (OWASP ZAP, similar)

### Stack de testing recomendado

| Lenguaje | Unit/Integration | E2E |
|----------|------------------|-----|
| JS/TS | vitest, jest | Playwright |
| Python | pytest | Playwright (Python) |
| Rust | cargo test, nextest | — |
| Go | testing, testify | — |
| Java | JUnit 5, Mockito | Selenium, Playwright |
| C#/.NET | xUnit, NUnit | Playwright |
| Móvil RN | jest, react-native-testing-library | Detox / Maestro |
| Móvil nativo | XCTest / Espresso | Maestro |

### Reglas en la guía

- Fase 1 debe incluir setup del framework de testing
- Cada fase posterior introduce sus propios tests; no se acumulan para "el final"
- Definition of Done de la fase: tests verdes en CI

---

## 2. Pre-commit Hooks

### Setup obligatorio en Fase 1

Usar `pre-commit` (https://pre-commit.com/) como framework universal. Configuración en `.pre-commit-config.yaml`.

### Hooks mínimos

- **Linter** del lenguaje principal (eslint, ruff, clippy, golangci-lint)
- **Formatter** (prettier, black, rustfmt, gofmt)
- **Secrets scanner:** gitleaks o detect-secrets
- **Verificación de archivos** grandes accidentales
- **End of file fixer** y **trailing whitespace**

### Ejemplo `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: check-merge-conflict

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks

  # Agregar linter/formatter del stack
```

### Comando de instalación documentado en README

```bash
pip install pre-commit
pre-commit install
```

---

## 3. Architecture Decision Records (ADRs)

### Cuándo usar

- Proyectos **mediano/grande** siempre
- Proyectos **pequeños** solo si hay decisión técnicamente compleja (ej: elección de motor de juego, framework principal)

### Estructura

Carpeta `docs/adr/` con archivos numerados secuencialmente.

### Plantilla

```markdown
# ADR-{{NNNN}}: {{Título corto de la decisión}}

**Fecha:** YYYY-MM-DD
**Estado:** Propuesto | Aceptado | Reemplazado por ADR-XXXX | Deprecado

## Contexto

{{Qué problema se está resolviendo. Restricciones, requisitos, fuerzas en juego.}}

## Decisión

{{Qué se decidió, en una frase. Luego desarrollo.}}

## Alternativas consideradas

### Opción A: {{...}}
- ✅ Pros
- ❌ Contras

### Opción B: {{...}}
- ✅ Pros
- ❌ Contras

## Consecuencias

**Positivas:**
- {{...}}

**Negativas:**
- {{...}}

**Riesgos:**
- {{...}}

## Referencias

- {{links a documentación, benchmarks, otros ADRs relacionados}}
```

### Ejemplos típicos de ADR

- "Por qué Postgres y no MongoDB"
- "Por qué Next.js App Router y no Pages Router"
- "Por qué autenticación con JWT propio y no Auth0"
- "Por qué arquitectura modular monolítica y no microservicios"
- "Por qué Tailwind y no CSS Modules"

### ADR-0001 obligatorio

Generar ADR-0001 con las decisiones tomadas en Paso 5 (stack) y Paso 6 (seguridad).

---

## 4. README.md para humanos (no para Claude)

### Diferencia clave con CLAUDE.md

- **CLAUDE.md:** denso, optimizado para tokens, con mapa de "dónde encontrar X", orientado a una IA
- **README.md:** narrativo, orientado a un humano (dev o usuario final), con instrucciones paso a paso

### Plantilla

```markdown
# {{Nombre del Proyecto}}

{{1-2 párrafos: qué es, para qué sirve, quién lo usa}}

## Características principales

- {{Feature 1}}
- {{Feature 2}}
- {{Feature 3}}

## Capturas / Demo

{{Imágenes o link a demo}}

## Stack

- {{Lenguaje + framework}}
- {{Base de datos}}
- {{Otros componentes relevantes}}

## Requisitos previos

- {{Node 20+, Python 3.11+, Docker, etc.}}

## Instalación local

```bash
git clone {{url}}
cd {{repo}}
{{comandos de setup}}
cp .env.example .env
# Editar .env con valores reales
{{comando de migración / seed}}
{{comando de arranque}}
```

## Estructura del proyecto

```
{{tree breve, alto nivel}}
```

## Cómo correr los tests

```bash
{{comando}}
```

## Cómo contribuir

- Conventional Commits
- PRs apuntan a `develop`
- Tests verdes son obligatorios
- {{Link a CONTRIBUTING.md si existe}}

## Cómo deployar

{{Pasos o link a docs/despliegue.md}}

## Licencia

{{MIT / Apache 2 / proprietary / etc.}}

## Autores / Contacto

- {{Nombre + email}}
```

---

## 5. Conventional Commits

### Formato

```
<tipo>(<scope opcional>): <descripción corta>

<cuerpo opcional con más detalle>

<footer opcional con BREAKING CHANGE o referencias a issues>
```

### Tipos estándar

- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` solo cambios en documentación
- `style:` cambios de formato (sin afectar lógica)
- `refactor:` cambio de código que no agrega feature ni arregla bug
- `perf:` mejora de performance
- `test:` agregar o corregir tests
- `chore:` mantenimiento (deps, configs, build tools)
- `ci:` cambios en pipelines de CI/CD
- `build:` cambios en sistema de build o deps externas
- `revert:` revierte commit anterior

### Ejemplos

```
feat(auth): agregar login con Google OAuth
fix(api): corregir 500 cuando email tiene espacios
docs(readme): actualizar pasos de instalación
refactor(db): extraer queries de user a repository
test(auth): agregar tests de logout
chore(deps): actualizar express a 4.19.2
```

### Hook opcional

`commitlint` puede validar el formato en pre-commit o commit-msg hook. Recomendado en proyectos mediano/grande.

### Por qué importa

- Facilita generación automática de CHANGELOG
- Permite versionado semántico automático
- Hace el git log legible

---

## 6. Definition of Done (DoD) por fase/subfase

Criterios verificables que TODA fase/subfase debe cumplir antes de cerrarse. Se documentan en cada fase/subfase de `guia_desarrollo.md`.

### DoD mínimo (todos los proyectos)

- [ ] Funcionalidad de la fase implementada según especificación
- [ ] Tests de la fase escritos y pasando
- [ ] Linter pasa sin errores
- [ ] Formatter aplicado (no diff en archivos formateados)
- [ ] Pre-commit hooks pasan
- [ ] Comando de auditoría de dependencias pasa
- [ ] Commit hecho con mensaje en Conventional Commits
- [ ] `progreso/estado-actual.md` actualizado
- [ ] Si era subfase: handoff doc creado/actualizado

### DoD adicional (mediano/grande)

- [ ] Documentación actualizada (README, especificaciones, ADR si aplica)
- [ ] Code review realizado (humano o herramienta)
- [ ] Tests de regresión pasando
- [ ] Cobertura no bajó respecto a la fase anterior

### DoD adicional (grande / producción)

- [ ] Deploy a staging exitoso
- [ ] Smoke tests en staging pasando
- [ ] Monitoring/alertas configurados para la nueva funcionalidad
- [ ] Plan de rollback documentado

---

## 7. Convenciones de Git

### Branching strategy

**Proyectos pequeños:**
- Trabajar directo en `main` con commits frecuentes
- Tags para versiones (`v1.0.0`)

**Proyectos mediano/grande:**
- `main`: producción
- `develop`: integración (opcional, alternativa: trunk-based)
- `feature/{nombre}`: trabajo de feature, se mergea a develop/main vía PR
- `hotfix/{nombre}`: arreglos urgentes desde main

### Tags y versionado

Semantic Versioning: `vMAJOR.MINOR.PATCH`

- MAJOR: cambios incompatibles
- MINOR: nueva funcionalidad compatible
- PATCH: bugfixes

### Tags al final de cada fase

Recomendar al usuario crear un tag al cierre de cada fase importante (`v0.1.0` tras F1, etc.) para tener puntos de regreso claros.

---

## 8. CI/CD básico

Aun en proyectos pequeños, configurar CI básico en Fase 1 o Fase 2:

### Pipeline mínimo (GitHub Actions ejemplo)

```yaml
name: CI
on: [push, pull_request]
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - {{setup del runtime}}
      - run: {{install deps}}
      - run: {{lint}}
      - run: {{test}}
      - run: {{audit de deps}}
```

### CD

- **Pequeño:** deploy manual con script documentado
- **Mediano:** deploy automático a staging tras merge a develop
- **Grande:** deploy automático a staging, deploy a prod con aprobación manual

---

## 9. Checklist consolidado de buenas prácticas

Para validar antes de generar `especificaciones.md` y `guia_desarrollo.md`:

- [ ] Testing strategy definida según tamaño
- [ ] Pre-commit hooks listados con su configuración
- [ ] Conventional Commits adoptado
- [ ] README.md humano planeado además de CLAUDE.md
- [ ] DoD por fase explicitado
- [ ] Branching strategy elegida
- [ ] CI/CD básico planeado (mínimo en Fase 1 o 2)
- [ ] ADR-0001 con decisiones iniciales (mediano/grande)
