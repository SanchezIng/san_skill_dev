# Seguridad Ampliada (más allá de OWASP Top 10)

Reglas adicionales de seguridad que se INTEGRAN a las especificaciones del proyecto. No van en sección separada; van entrelazadas con los requisitos no funcionales correspondientes.

---

## 1. Secrets Management (todos los proyectos)

### Reglas inviolables

- `.env` SIEMPRE en `.gitignore` desde el primer commit
- `.env.example` con todas las variables y valores dummy (nunca valores reales)
- Política explícita: "ninguna credencial, token, password, API key o secret va comiteado al repo"
- Pre-commit hook con secrets scanner (gitleaks o detect-secrets) — ver `practicas_dev.md`

### Plantilla `.env.example` por stack

**Node/TypeScript:**

```env
# App
NODE_ENV=development
PORT=3000

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/mydb

# Auth
JWT_SECRET=changeme-use-openssl-rand-hex-32
JWT_EXPIRES_IN=24h

# Third party (si aplica)
STRIPE_SECRET_KEY=sk_test_changeme
```

**Python:**

```env
# App
PYTHON_ENV=development
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

# Auth
SECRET_KEY=changeme-generate-with-secrets-token-hex-32
```

### Vault o gestor de secrets (mediano/grande con datos sensibles)

- En cloud: AWS Secrets Manager / GCP Secret Manager / Azure Key Vault
- Auto-hosted: HashiCorp Vault, Doppler
- Para equipos: 1Password Secrets Automation

La especificación menciona qué se usará y cómo se accede en runtime.

---

## 2. Dependency Security (todos los proyectos)

### Reglas inviolables

- **Pinning de versiones.** En `package.json` / `requirements.txt` / `Cargo.toml` se fijan versiones exactas (`1.2.3`), no rangos abiertos (`^1.2.3`, `>=1.0`)
- Usar lockfile: `package-lock.json`, `poetry.lock`, `Cargo.lock`, `Gemfile.lock` — comiteado al repo
- Comando de auditoría en el checklist de CADA fase:
  - Node: `npm audit --audit-level=high`
  - Python: `pip-audit` o `safety check`
  - Rust: `cargo audit`
  - Ruby: `bundle audit`
  - Go: `govulncheck ./...`
- Revisión obligatoria antes de añadir una librería nueva:
  - ¿Está mantenida? (último commit < 12 meses)
  - ¿Cuántos downloads/stars?
  - ¿Tiene vulnerabilidades conocidas?
  - ¿Es razonable el peso de transitive deps que arrastra?

### Renovate / Dependabot

Proyectos mediano/grande deben habilitar Dependabot o Renovate (1 PR por dependencia, con cadencia semanal o mensual). Se configura en Fase 1 o Fase 2.

---

## 3. Logging Seguro

### Qué NO loggear NUNCA

- Passwords (incluso hasheados es mejor evitar)
- Tokens (JWT, OAuth access/refresh, API keys)
- Datos de tarjeta de crédito (PAN, CVV, expiración)
- PII completa (email, teléfono, dirección, DNI) — al menos enmascarar
- Contenido de cookies de sesión
- Secrets del `.env`
- Datos médicos / financieros sensibles

### Cómo enmascarar

- Email: `j***@example.com`
- DNI: `12***789`
- Tarjeta: solo últimos 4 dígitos
- Tokens: nunca completos, máximo primeros 6 caracteres si es necesario para debug

### Niveles de log

- `ERROR`: el sistema no puede continuar la operación
- `WARN`: algo inesperado pero recuperable
- `INFO`: eventos de negocio (login, transacción completada)
- `DEBUG`: detalles para troubleshooting (no en prod por defecto)

### Logging estructurado

JSON estructurado preferido sobre texto plano. Facilita búsqueda y alerta.

```json
{"timestamp":"2026-05-14T10:30:00Z","level":"INFO","event":"user_login","user_id":"u_123","ip":"1.2.3.4"}
```

---

## 4. Threat Modeling Ligero (mediano/grande con datos medio/alto)

Documento `docs/threat-model.md` de 1-2 páginas.

### Plantilla

```markdown
# Modelo de Amenazas — {{Proyecto}}

## Activos a proteger

| Activo | Tipo | Sensibilidad |
|--------|------|--------------|
| Datos de usuarios | PII | Alta |
| Tokens de sesión | Credencial | Alta |
| {{...}} | {{...}} | {{...}} |

## Actores (legítimos y maliciosos)

- **Usuarios finales:** {{descripción}}
- **Administradores:** {{descripción}}
- **Atacantes externos:** anónimos buscando vulnerabilidades comunes
- **Insiders:** {{si aplica}}
- **Bots/scrapers:** automatizados

## Top 5 amenazas

Para cada una: descripción, vector, impacto, mitigación, prioridad.

### A1: Robo de credenciales por phishing
- **Vector:** email falso simulando la app
- **Impacto:** acceso completo a cuenta de víctima
- **Mitigación:** MFA, alertas de login desde IP nueva, educación al usuario
- **Prioridad:** Alta

### A2: Inyección SQL en endpoint X
{{...}}

### A3-A5
{{...}}

## Mitigaciones generales aplicadas

- ✅ HTTPS forzado
- ✅ Rate limiting en endpoints de auth
- ✅ Validación de input en todos los endpoints
- ✅ {{...}}

## Mitigaciones pendientes (riesgo aceptado de momento)

- ⏸️ WAF (se agregará en fase de producción)
- ⏸️ {{...}}
```

---

## 5. Backup y Recovery (proyectos que persistan datos)

### Especificaciones mínimas

En `especificaciones.md` sección de Infraestructura debe incluir:

- **Qué se respalda:** BD principal, archivos subidos por usuarios (si aplica), configuración
- **Frecuencia:** diaria / semanal / continua según criticidad
- **Retención:** 7 días, 30 días, 90 días según necesidad
- **Dónde se guarda:** S3/GCS/Azure Blob con cifrado, región distinta a la de producción
- **Cómo se restaura:** comandos exactos para restore (debe estar documentado y probado)
- **Quién tiene acceso a los backups:** lista explícita de personas/roles

### Test de restore

**Regla:** un backup que nunca se probó restaurar NO es un backup. La fase de despliegue debe incluir al menos UN test de restore exitoso.

---

## 6. Regulación de Datos (si maneja PII)

### Determinar jurisdicción

Preguntar al usuario:

- ¿De dónde son los usuarios? (UE → GDPR, Brasil → LGPD, USA varios estados → CCPA/CPRA, México → LFPDPPP, Perú → Ley 29733)
- ¿Hay datos de menores? (COPPA en USA, mayores protecciones en general)
- ¿Datos médicos? (HIPAA en USA, regulaciones específicas en cada país)
- ¿Datos financieros? (PCI-DSS si maneja tarjetas)

### Sección mínima en `especificaciones.md`

```markdown
## X. Cumplimiento Regulatorio

### Jurisdicción aplicable
{{GDPR / LGPD / Ley 29733 Perú / etc.}}

### Datos personales que maneja el sistema
{{Lista}}

### Bases legales de tratamiento
{{Consentimiento, contrato, obligación legal, interés legítimo}}

### Derechos del titular implementados
- [ ] Acceso (ver mis datos)
- [ ] Rectificación (corregir mis datos)
- [ ] Supresión / Olvido (eliminar mis datos)
- [ ] Portabilidad (exportar mis datos)
- [ ] Oposición al tratamiento
- [ ] No ser objeto de decisiones automatizadas

### Plazos
- Respuesta a solicitud de derechos: {{15-30 días según jurisdicción}}
- Notificación de brecha: {{72h GDPR, similar en otras}}
- Retención de datos: {{X años según finalidad}}

### Cookies y trackers
{{Banner de consentimiento, política de cookies}}

### Política de Privacidad pública
{{URL donde se publica, quién la mantiene}}
```

---

## 7. Hardening adicional por tipo de proyecto

### Web app / API expuesta a internet

- HTTPS forzado (HSTS header)
- Headers de seguridad: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`
- Rate limiting por IP y por usuario (límite distinto para endpoints sensibles)
- CORS configurado de forma estricta (no `*` en producción)
- Cookies con flags: `HttpOnly`, `Secure`, `SameSite=Strict` o `Lax`
- Validación de input con biblioteca dedicada (zod, pydantic, joi)

### Bot IA / agente con LLM

- Sanitización de prompts del usuario para evitar prompt injection
- Lista de comandos/acciones permitidas, no abierto
- Rate limiting por usuario (token y dinero)
- Logging de prompts (con cuidado de PII)
- Si tiene tool use: confirmación humana para acciones destructivas/de pago

### Móvil

- Cifrado de datos sensibles en disco (Keystore / Keychain)
- Pinning de certificado SSL para llamadas al backend
- Detección de jailbreak/root (al menos warning)
- Ofuscación de código en builds de release

### Escritorio

- Code signing del instalador
- Auto-update firmado
- Sandboxing donde el SO lo permita

### Script / automatización

- No correr como root salvo necesidad explícita
- Validación de inputs externos (CLI args, archivos de entrada)
- Manejo seguro de paths (evitar path traversal)

---

## 8. Checklist de Seguridad por Fase

Al final de cada fase, validar:

- [ ] Ninguna credencial en código ni commits
- [ ] `.env.example` actualizado si hay variables nuevas
- [ ] Comando de auditoría de dependencias pasó sin críticos
- [ ] Logs no contienen PII ni secrets
- [ ] Validación de input en endpoints/funciones nuevas
- [ ] Tests de seguridad básicos (si aplica) pasan
- [ ] Si hay cambios en datos personales: política de privacidad actualizada
