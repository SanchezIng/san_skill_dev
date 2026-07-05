# Marcos de gestión de seguridad

Estos marcos no son sobre líneas de código, sino sobre cómo se gobierna y
gestiona el riesgo del sistema. Úsalos para postura general, decisiones de
arquitectura y cuando el usuario pregunte por cumplimiento.

## NIST Cybersecurity Framework (CSF)

Estándar del gobierno de EE. UU. para gestionar riesgo de ciberseguridad. Se
organiza en funciones:

1. **Identificar (Identify)** — conoce tus activos, datos, flujos y riesgos. No
   puedes proteger lo que no sabes que tienes.
2. **Proteger (Protect)** — controles de acceso, cifrado, hardening,
   capacitación, mantenimiento.
3. **Detectar (Detect)** — monitoreo, logging, detección de anomalías.
4. **Responder (Respond)** — plan de respuesta a incidentes, contención,
   comunicación.
5. **Recuperar (Recover)** — backups, restauración, lecciones aprendidas.

*(CSF 2.0 añadió una función transversal:* **Gobernar / Govern** *— roles,
políticas y supervisión de riesgo.)*

Aplicación práctica en código: asegúrate de que la app **registre** eventos de
seguridad (Detectar), tenga **backups** y manejo de errores que no tumbe el
sistema (Recuperar), y permisos claros (Proteger).

## ISO/IEC 27001

Estándar internacional para un **Sistema de Gestión de Seguridad de la
Información (SGSI)**. Define cómo una organización gestiona riesgos, datos,
proveedores y personas mediante controles y mejora continua (ciclo
Planificar-Hacer-Verificar-Actuar). Su anexo de controles cubre criptografía,
control de acceso, seguridad de operaciones, gestión de incidentes y desarrollo
seguro. Relevante cuando el proyecto necesita certificación o cumplimiento
empresarial.

## CIS Controls (Center for Internet Security)

Lista **priorizada** de acciones defensivas concretas, ordenadas por impacto.
Entre las más relevantes para desarrollo:

- Inventario de activos de hardware y software.
- Gestión segura de configuración.
- Gestión de cuentas y control de acceso (incluye PoLP y MFA).
- Gestión continua de vulnerabilidades (parcheo).
- Defensas contra malware.
- Protección de datos (cifrado, clasificación).
- Logs de auditoría centralizados.
- Seguridad del software de aplicación (validación, dependencias, pruebas).

Úsalos como hoja de ruta priorizada: empieza por inventario y control de acceso
antes que por controles avanzados.
