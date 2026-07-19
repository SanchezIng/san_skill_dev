# Estándares y protocolos técnicos

Los nombres y protocolos concretos que el código debe usar. Si ves alternativas
inseguras (MD5 para passwords, HTTP plano, JWT sin verificar), corrígelas.

## Identidad, autenticación y autorización

- **OAuth 2.0** — protocolo de **autorización**. Es lo que permite "Iniciar
  sesión con Google" sin que la app conozca tu contraseña: delega el acceso
  mediante tokens. Usa siempre el flujo correcto (Authorization Code + PKCE para
  apps web/móviles públicas). No uses el flujo Implicit (obsoleto).
- **OpenID Connect (OIDC)** — capa de **autenticación** sobre OAuth 2.0. Verifica
  *quién* es el usuario (identidad), mientras OAuth dice *qué* puede hacer.
  Devuelve un `id_token` (JWT) con la identidad.
- **SAML 2.0** — autenticación basada en XML, muy usada en entornos corporativos
  para **Single Sign-On (SSO)** empresarial.
- **JWT (JSON Web Tokens)** — estándar de facto para transmitir la sesión del
  usuario entre frontend y backend.
  - **Verifica SIEMPRE la firma** en el backend antes de confiar en el token.
  - Usa algoritmos fuertes (RS256/ES256 o HS256 con secreto robusto). **Rechaza
    `alg: none`** y no aceptes el algoritmo que envíe el cliente.
  - Pon expiración corta (`exp`), valida `iss`/`aud`, y maneja revocación
    (refresh tokens, lista de revocados).
  - **Nunca** guardes datos sensibles en el payload (es solo Base64, no cifrado).
  - En el navegador, prefiere cookies `HttpOnly` + `Secure` + `SameSite` sobre
    `localStorage` para evitar robo por XSS.

## Comunicaciones y criptografía

- **TLS 1.3** — sucesor moderno de SSL; hace que las URLs sean `https://`. Cifra
  los datos en tránsito para que nadie los espíe. Exige TLS 1.2+ como mínimo,
  preferentemente 1.3. Rechaza certificados inválidos; nunca desactives la
  verificación de certificados "para que funcione".
- **AES-256** — estándar para cifrar **datos en reposo** (en la base de datos o
  disco). Usa modos autenticados (GCM) y gestiona las claves fuera del código
  (gestor de secretos / KMS).
- **Bcrypt / Argon2** — algoritmos de *hashing* lentos por diseño, **obligatorios
  para contraseñas**. Preferir **Argon2id**; bcrypt es aceptable. Aplican *salt*
  automático. **Nunca** uses MD5 ni SHA-1 para contraseñas (son rápidos y
  rompibles). Para datos no-password usa SHA-256+ según el caso.

## Cabeceras HTTP de seguridad (defensa del navegador)

El backend debe enviar estas instrucciones para que el navegador proteja al
usuario:

- **CSP (Content Security Policy)** — *allow-list* estricta de desde qué dominios
  se pueden cargar scripts, estilos, imágenes y fuentes. Es la defensa principal
  contra **XSS**. Evita `unsafe-inline` y `unsafe-eval`.
- **HSTS (HTTP Strict Transport Security)** — obliga al navegador a usar siempre
  HTTPS, evitando ataques de degradación/intercepción (man-in-the-middle).
- **CORS (Cross-Origin Resource Sharing)** — define **quién** puede hacer
  peticiones a tu API. Configura un *allow-list* explícito de orígenes (ej. solo
  `tudominio.com`). **Nunca** uses `Access-Control-Allow-Origin: *` junto con
  credenciales.

### Otras cabeceras recomendadas
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (o `frame-ancestors` en CSP) contra clickjacking.
- `Referrer-Policy: no-referrer` o `strict-origin-when-cross-origin`.
- `Permissions-Policy` para limitar APIs del navegador.

## Manejo de secretos (transversal)

- Nunca hardcodees secretos ni los commitees. Usa variables de entorno o un
  gestor (Vault, AWS/GCP Secrets Manager, Doppler).
- Añade `.env`, claves y certificados a `.gitignore`.
- Rota secretos periódicamente y tras cualquier exposición.
- Distintos secretos por entorno (dev/staging/prod).
