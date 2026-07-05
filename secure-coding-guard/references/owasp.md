# OWASP — Vulnerabilidades a evitar

OWASP (Open Worldwide Application Security Project) es la referencia central de
seguridad en software. Usa estas listas para revisar código concreto.

## OWASP Web Top 10

1. **Broken Access Control** — el #1. Un usuario accede a datos/acciones que no
   le corresponden (IDOR, escalada de privilegios). *Fix:* verifica autorización
   en el servidor en cada endpoint; deniega por defecto; nunca confíes en IDs del
   cliente sin comprobar ownership.
2. **Cryptographic Failures** — datos sensibles sin cifrar o con cripto débil.
   *Fix:* TLS 1.3 en tránsito, AES-256 en reposo, hashing fuerte para passwords.
3. **Injection** — SQL, NoSQL, OS command, LDAP. *Fix:* consultas
   parametrizadas / ORM, validación y *allow-listing* de input, escapado por
   contexto.
4. **Insecure Design** — fallos de arquitectura, no de implementación. *Fix:*
   threat modeling, patrones seguros desde el diseño.
5. **Security Misconfiguration** — defaults inseguros, puertos abiertos, errores
   verbosos, headers ausentes. *Fix:* hardening, deshabilitar lo no usado,
   ocultar detalles de error.
6. **Vulnerable and Outdated Components** — dependencias con CVEs. *Fix:* SCA
   (dependabot, npm audit, pip-audit), actualizar, fijar versiones.
7. **Identification and Authentication Failures** — login débil, sesiones mal
   manejadas, fuerza bruta. *Fix:* MFA, rate limiting, gestión segura de sesión,
   no exponer si el usuario existe.
8. **Software and Data Integrity Failures** — CI/CD comprometido,
   deserialización insegura, updates sin firmar. *Fix:* verifica integridad y
   firmas, evita deserializar datos no confiables.
9. **Security Logging and Monitoring Failures** — sin trazas no detectas
   ataques. *Fix:* loguea eventos de seguridad (sin datos sensibles), alerta.
10. **Server-Side Request Forgery (SSRF)** — el servidor hace peticiones a URLs
    controladas por el atacante. *Fix:* allow-list de destinos, bloquea IPs
    internas/metadata, valida y normaliza URLs.

## OWASP API Security Top 10

Crítico cuando web y móvil comparten el mismo backend.

1. **Broken Object Level Authorization (BOLA/IDOR)** — el más común en APIs.
   Verifica ownership del objeto en cada request.
2. **Broken Authentication** — tokens mal validados, JWT sin verificar firma.
3. **Broken Object Property Level Authorization** — exponer/aceptar campos de más
   (excessive data exposure + mass assignment).
4. **Unrestricted Resource Consumption** — sin rate limiting / cuotas → DoS y
   costos. Aplica throttling y límites de payload.
5. **Broken Function Level Authorization** — endpoints admin accesibles a users
   normales.
6. **Unrestricted Access to Sensitive Business Flows** — abuso de lógica de
   negocio (ej. comprar todo el stock). Limita y detecta bots.
7. **SSRF** (ver arriba).
8. **Security Misconfiguration**.
9. **Improper Inventory Management** — endpoints viejos/`/v1` y entornos de test
   expuestos. Mantén inventario de APIs.
10. **Unsafe Consumption of APIs** — confiar ciegamente en APIs de terceros.
    Valida también sus respuestas.

## OWASP Mobile Top 10

Para apps iOS/Android.

- **Improper Credential Usage** — credenciales hardcodeadas o mal guardadas.
- **Inadequate Supply Chain Security** — SDKs/dependencias maliciosas.
- **Insecure Authentication/Authorization**.
- **Insufficient Input/Output Validation**.
- **Insecure Communication** — sin TLS o sin pinning donde aplique.
- **Inadequate Privacy Controls** — manejo indebido de datos personales.
- **Insufficient Binary Protections** — falta ofuscación/anti-tamper.
- **Security Misconfiguration**.
- **Insecure Data Storage** — datos sensibles en texto plano en el dispositivo.
  Usa Keychain (iOS) / Keystore (Android), nunca SharedPreferences/UserDefaults
  para secretos.
- **Insufficient Cryptography**.

## ASVS (Application Security Verification Standard)

Checklist exhaustivo y por niveles (L1 básico → L3 alto) para *verificar* la
seguridad de una app de forma sistemática. Úsalo como guía de testing: cubre
autenticación, gestión de sesión, control de acceso, validación, criptografía,
manejo de errores, logging, datos, comunicaciones y configuración. Para repos
existentes, recorrer las categorías ASVS es la forma más ordenada de auditar.
