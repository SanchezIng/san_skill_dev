# OWASP Top 10 por Tipo de Proyecto

OWASP Top 10 (2025) traducido a requisitos concretos. Aplica solo lo relevante según tipo + sensibilidad de datos.

---

## OWASP Top 10 (referencia rápida)

- **A01** Broken Access Control
- **A02** Cryptographic Failures
- **A03** Injection
- **A04** Insecure Design
- **A05** Security Misconfiguration
- **A06** Vulnerable & Outdated Components
- **A07** Identification & Authentication Failures
- **A08** Software & Data Integrity Failures
- **A09** Security Logging & Monitoring Failures
- **A10** Server-Side Request Forgery (SSRF)

---

## Niveles de aplicación

### Nivel Básico (proyectos pequeños o sin datos sensibles)
Aplicar: A01, A02, A03, A07 (los esenciales)

### Nivel Estándar (proyectos medianos con datos personales)
Aplicar: A01, A02, A03, A04, A05, A07, A09

### Nivel Completo (proyectos con datos sensibles, financieros, médicos, o públicos en internet)
Aplicar: los 10 + ASVS Nivel 2

---

## Reglas OWASP traducidas a requisitos

Cuando generes especificaciones.md, incluye los RNF-SEC-XX que correspondan según el caso.

### A01 — Broken Access Control

- **RNF-SEC-A01-1**: Cada endpoint protegido valida el rol del usuario antes de ejecutarse
- **RNF-SEC-A01-2**: Por defecto, todo está denegado. Los permisos se conceden explícitamente (deny by default)
- **RNF-SEC-A01-3**: Los IDs de recursos no son secuenciales predecibles (usar UUIDs para datos sensibles)
- **RNF-SEC-A01-4**: Validar que el usuario actual tiene permiso sobre el recurso específico (no solo el rol)

### A02 — Cryptographic Failures

- **RNF-SEC-A02-1**: Contraseñas con bcrypt factor 12 o argon2id (nunca MD5/SHA simple)
- **RNF-SEC-A02-2**: HTTPS obligatorio en producción (TLS 1.2+)
- **RNF-SEC-A02-3**: Datos sensibles cifrados en reposo (DB-level encryption o columnas cifradas)
- **RNF-SEC-A02-4**: Tokens y secretos en variables de entorno, nunca en código

### A03 — Injection

- **RNF-SEC-A03-1**: Parámetros vinculados/preparados en TODAS las queries (SQL, Cypher, NoSQL)
- **RNF-SEC-A03-2**: Validación estricta de entrada con schemas (Pydantic, Zod, Joi)
- **RNF-SEC-A03-3**: Escape automático en templates HTML (React/Vue ya lo hacen por defecto)
- **RNF-SEC-A03-4**: No usar `eval()` o equivalentes con input del usuario

### A04 — Insecure Design

- **RNF-SEC-A04-1**: Threat modeling realizado para flujos críticos (auth, pagos, datos sensibles)
- **RNF-SEC-A04-2**: Principio de mínimo privilegio aplicado a usuarios, servicios y procesos
- **RNF-SEC-A04-3**: Rate limiting en endpoints críticos (login, pagos, búsqueda)
- **RNF-SEC-A04-4**: Confirmación obligatoria para acciones destructivas (eliminar, transferir)

### A05 — Security Misconfiguration

- **RNF-SEC-A05-1**: Headers de seguridad configurados en producción:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security: max-age=31536000
  - Content-Security-Policy: configurada según necesidades
- **RNF-SEC-A05-2**: Stack traces y errores detallados NUNCA expuestos al cliente
- **RNF-SEC-A05-3**: Servicios de admin/debug deshabilitados en producción
- **RNF-SEC-A05-4**: CORS configurado solo con orígenes permitidos (no `*`)

### A06 — Vulnerable & Outdated Components

- **RNF-SEC-A06-1**: Auditoría de dependencias: `pip audit` / `npm audit` ejecutado en CI
- **RNF-SEC-A06-2**: Versiones fijadas en requirements.txt / package.json (no `*`)
- **RNF-SEC-A06-3**: Actualización mensual de dependencias con vulnerabilidades conocidas
- **RNF-SEC-A06-4**: No usar librerías sin mantenimiento (>1 año sin commits)

### A07 — Identification & Authentication Failures

- **RNF-SEC-A07-1**: Contraseñas mínimo 8 caracteres con complejidad
- **RNF-SEC-A07-2**: Bloqueo temporal tras 5 intentos fallidos consecutivos (15 min)
- **RNF-SEC-A07-3**: Rate limiting en login: 10 intentos por IP en 5 minutos
- **RNF-SEC-A07-4**: JWT con expiración corta (60 min máx) + refresh tokens
- **RNF-SEC-A07-5**: Sesiones invalidan inmediatamente al cerrar sesión
- **RNF-SEC-A07-6**: 2FA disponible para usuarios admin/sensibles (recomendado)

### A08 — Software & Data Integrity Failures

- **RNF-SEC-A08-1**: Firmas digitales en actualizaciones automáticas (apps escritorio/móvil)
- **RNF-SEC-A08-2**: Integridad de archivos sensibles verificada con checksums
- **RNF-SEC-A08-3**: Pipelines de CI/CD con verificación de integridad
- **RNF-SEC-A08-4**: Datos críticos almacenados con hashing/firma (audit trails)

### A09 — Security Logging & Monitoring Failures

- **RNF-SEC-A09-1**: Logs de acciones críticas: login, creación/eliminación de usuarios, accesos a datos sensibles, errores de autorización
- **RNF-SEC-A09-2**: Logs no contienen contraseñas, tokens, ni PII innecesario
- **RNF-SEC-A09-3**: Logs centralizados (no solo locales) en proyectos medianos/grandes
- **RNF-SEC-A09-4**: Alertas automáticas para patrones sospechosos (múltiples logins fallidos, accesos inusuales)

### A10 — Server-Side Request Forgery (SSRF)

- **RNF-SEC-A10-1**: Validar URLs antes de hacer requests desde el servidor (whitelist de dominios)
- **RNF-SEC-A10-2**: No permitir que el usuario controle URLs internas
- **RNF-SEC-A10-3**: Timeout en requests externos
- **RNF-SEC-A10-4**: Servicios internos no accesibles desde la red pública

---

## Aplicación por tipo de proyecto

### Web App con Usuarios
- Tamaño pequeño: A01, A02, A03, A07 + headers básicos de A05
- Tamaño mediano/grande: Aplicar TODOS los Top 10

### API REST Pura
- Énfasis especial: A01, A03, A05, A07, A10
- Si maneja datos personales: agregar A02, A09

### App Móvil
- Énfasis: A02 (almacenamiento local cifrado), A07 (auth segura), A08 (firma de updates)
- Backend asociado: aplicar los relevantes del backend

### App de Escritorio
- A02 (cifrado de datos locales), A08 (firma de instalador), A06 (dependencias)
- Si se conecta a backend: aplicar los relevantes del backend

### Script o Automatización
- A02 (manejo de credenciales), A03 (validar input si toma de fuentes externas), A09 (logs)

### Bot o Agente IA
- A03 (prompt injection), A07 (auth de usuarios), A09 (logs de conversaciones sensibles)
- Específico de IA: prevenir prompt injection, validar tools, rate limiting

### Videojuego
- Único caso donde OWASP es menos crítico
- Aplicar: A02 (si guarda datos en la nube), A08 (anti-cheat es derivado de integridad)
- Si tiene microtransacciones: A02, A07, A09 obligatorios

---

## Cómo presentar al usuario

No le hagas escoger reglas individuales. Preséntale el paquete completo así:

```
"Según tu proyecto [TIPO] con datos de sensibilidad [BAJA/MEDIA/ALTA] que correrá en [ENTORNO], aplicaré las siguientes reglas OWASP:

[Lista de 8-10 reglas más críticas en lenguaje claro]

Esto cubre los riesgos principales para tu caso. ¿Aceptas o quieres agregar/quitar alguna regla específica?"
```

Si el usuario es académico (tesis, proyecto universitario), agrega:
```
"Documentaré estas reglas con el estándar OWASP Top 10 (2025) para que puedas defenderlas en tu sustentación."
```
