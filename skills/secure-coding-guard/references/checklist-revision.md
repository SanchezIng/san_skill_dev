# Checklist de revisión / auditoría

Pensado para **repos existentes o ajenos** y para revisar tu propio código antes
de entregar. No es un proceso por fases: es un recorrido por áreas. Marca cada
hallazgo con severidad (🔴 crítico / 🟠 medio / 🟡 bajo).

## Entrada y validación
- [ ] Todo input externo (formularios, query params, headers, body, archivos) se
      valida en el **backend** con *allow-list*, no solo en el cliente.
- [ ] Sin concatenación de input en SQL/NoSQL/comandos → consultas
      parametrizadas / ORM.
- [ ] Salida escapada por contexto (HTML, JS, URL) para prevenir XSS.
- [ ] Subida de archivos: valida tipo real, tamaño, nombre; guarda fuera del
      webroot; no ejecutable.
- [ ] Sin `eval`, sin deserialización de datos no confiables.

## Autenticación y sesión
- [ ] Contraseñas con Argon2id/bcrypt (nunca MD5/SHA-1/plano).
- [ ] Rate limiting / bloqueo ante fuerza bruta en login.
- [ ] MFA disponible para cuentas sensibles.
- [ ] JWT: firma verificada, `alg` fijo en servidor, `exp`/`iss`/`aud`
      validados, sin datos sensibles en el payload.
- [ ] Cookies de sesión `HttpOnly` + `Secure` + `SameSite`.
- [ ] Logout y expiración funcionan; rotación de tokens.
- [ ] Mensajes de error de login no revelan si el usuario existe.

## Autorización (Access Control)
- [ ] Cada endpoint verifica permisos en el servidor (denegar por defecto).
- [ ] Sin IDOR: se comprueba *ownership* del objeto, no solo que el ID exista.
- [ ] Endpoints admin separados y protegidos por rol.
- [ ] PoLP aplicado a usuarios, tokens y servicios.

## Datos y criptografía
- [ ] TLS 1.2+ (idealmente 1.3) en todas las comunicaciones; certificados
      válidos verificados.
- [ ] Datos sensibles en reposo cifrados (AES-256-GCM).
- [ ] Claves gestionadas fuera del código (KMS / gestor de secretos).
- [ ] Datos personales minimizados y conforme a privacidad (GDPR/LGPD si aplica).

## Secretos y configuración
- [ ] Sin secretos hardcodeados ni en el historial de git.
- [ ] `.env`, claves y certificados en `.gitignore`.
- [ ] Configuración segura por defecto; servicios/puertos no usados deshabilitados.
- [ ] Modo debug y errores verbosos **desactivados** en producción.

## Cabeceras y navegador
- [ ] CSP estricta (sin `unsafe-inline`/`unsafe-eval`).
- [ ] HSTS activo.
- [ ] CORS con allow-list explícito (sin `*` con credenciales).
- [ ] `nosniff`, anti-clickjacking, `Referrer-Policy`.

## APIs
- [ ] BOLA/IDOR cubierto en cada objeto.
- [ ] Rate limiting y límites de tamaño de payload.
- [ ] Sin *excessive data exposure* ni *mass assignment* (campos controlados).
- [ ] Validación de respuestas de APIs de terceros.
- [ ] Inventario de endpoints; versiones viejas/test no expuestas.

## Dependencias y supply chain
- [ ] SCA ejecutado (npm audit / pip-audit / dependabot) sin CVEs críticos.
- [ ] Versiones fijadas (lockfile) y de fuentes confiables.
- [ ] Integridad verificada en el pipeline CI/CD.

## Logging y monitoreo
- [ ] Eventos de seguridad registrados (login, cambios de permiso, fallos).
- [ ] **Sin** datos sensibles en logs (contraseñas, tokens, PII, tarjetas).
- [ ] Backups y plan de recuperación existen.

## Móvil (si aplica)
- [ ] Secretos/credenciales en Keychain (iOS) / Keystore (Android), no en
      UserDefaults/SharedPreferences.
- [ ] Comunicación con TLS; pinning donde el riesgo lo amerite.
- [ ] Sin datos sensibles en logs ni en almacenamiento local en claro.

---

**Cómo reportar la auditoría:** agrupa por severidad, corrige lo 🔴 de inmediato,
propone fixes para 🟠, y lista 🟡 como mejoras. No reescribas todo el repo de
golpe; prioriza por riesgo y avisa antes de cambios amplios.
