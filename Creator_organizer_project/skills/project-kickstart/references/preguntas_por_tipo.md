# Preguntas por Tipo de Proyecto

Cada bloque tiene preguntas específicas. Hazlas en grupos de 3 máximo usando `ask_user_input_v0`.

---

## Preguntas comunes a todos los tipos

**Bloque A — Usuarios y roles**
1. ¿Cuántos tipos de usuarios usarán el sistema? (admin, operador, cliente, invitado, etc.)
2. ¿Qué puede hacer cada tipo? (define permisos por rol)
3. ¿Cuántos usuarios concurrentes esperas como máximo?

**Bloque B — Funcionalidades principales**
1. Lista las top 5-10 funcionalidades que el sistema DEBE tener (sin opcionales)
2. ¿Hay funcionalidades que claramente quedan fuera de esta versión?
3. ¿Hay alguna funcionalidad crítica o de alto riesgo técnico?

**Bloque C — Restricciones**
1. ¿Cuál es el plazo de desarrollo? (semanas/meses)
2. ¿Hay presupuesto para servicios pagos (cloud, APIs, etc.) o todo debe ser gratis?
3. ¿Hardware o entorno específico requerido? (GPU, dispositivos IoT, sensores, etc.)

**Bloque D — Datos**
1. ¿Qué datos almacenará el sistema? (personales, financieros, médicos, contenido público, etc.)
2. ¿Hay normativas legales que cumplir? (GDPR, HIPAA, Ley de Datos Personales del país)
3. ¿Cuánto tiempo se conservan los datos? ¿Hay borrado automático?

**Bloque E — Entorno de ejecución**
1. ¿Dónde correrá el sistema? (PC local, red LAN, internet público, cloud, dispositivo del usuario)
2. ¿Necesita estar siempre online o puede funcionar offline?
3. ¿Hay integraciones con sistemas externos? (APIs de terceros, ERPs, etc.)

**Bloque F — Validación**
1. ¿Cómo sabrás que el proyecto está completado/funcionando bien?
2. ¿Hay métricas específicas de éxito? (rendimiento, precisión, tiempo de respuesta)
3. ¿Quién validará el resultado? (tú, cliente, comité, usuarios reales)

---

## Web App con Usuarios (frontend + backend)

Después de los bloques comunes, agrega:

**Bloque G1 — Autenticación**
1. ¿Cómo se autentican los usuarios? (email/password, SSO, OAuth, magic link, 2FA)
2. ¿Necesitas registro público o solo el admin crea cuentas?
3. ¿Manejas sesiones, JWT o ambos?

**Bloque H1 — Frontend**
1. ¿Aplicación de una sola página (SPA) o multipágina con SEO?
2. ¿Hay diseño previo (Figma, mockups) o se diseña sobre la marcha?
3. ¿Modo claro/oscuro, idiomas múltiples, accesibilidad?

**Bloque I1 — Backend y datos**
1. ¿Base de datos relacional, NoSQL, o grafo? Si no sabes, pregúntame.
2. ¿Necesita tiempo real? (WebSocket, SSE, polling)
3. ¿Archivos pesados (imágenes, videos, documentos)? ¿Dónde se almacenan?

---

## API REST Pura (sin frontend)

**Bloque G2 — Consumidores**
1. ¿Quiénes consumirán la API? (apps móviles internas, terceros públicos, microservicios propios)
2. ¿Necesitas versionado de API (v1, v2)?
3. ¿Documentación pública (Swagger/Redoc) o privada?

**Bloque H2 — Recursos**
1. ¿Cuáles son los recursos/entidades principales? (usuarios, productos, pedidos, etc.)
2. ¿Operaciones por recurso? (CRUD básico o lógica compleja)
3. ¿Endpoints batch o solo individuales?

**Bloque I2 — Rendimiento**
1. ¿Cuántas requests por segundo esperas en pico?
2. ¿Necesitas cache (Redis, Memcached)?
3. ¿Rate limiting por usuario/API key?

---

## App Móvil

**Bloque G3 — Plataformas**
1. ¿iOS, Android, o ambos?
2. ¿Nativo (Swift/Kotlin), híbrido (React Native/Flutter), o web app (PWA)?
3. ¿Necesitas publicarla en App Store / Google Play o es uso interno?

**Bloque H3 — Capacidades del dispositivo**
1. ¿Usa cámara, GPS, sensores, NFC, Bluetooth?
2. ¿Notificaciones push?
3. ¿Funciona offline? Si sí, ¿cómo sincroniza datos cuando vuelva online?

**Bloque I3 — Backend**
1. ¿La app es standalone o necesita un backend?
2. Si necesita backend, ¿cuál? (Firebase, Supabase, propio, etc.)
3. ¿Almacenamiento local? (SQLite, Room, Core Data)

---

## App de Escritorio

**Bloque G4 — Plataformas**
1. ¿Windows, macOS, Linux, o multiplataforma?
2. ¿Tecnología? (Electron, Tauri, .NET, Qt, JavaFX, nativo)
3. ¿Necesita instalador o portable?

**Bloque H4 — Capacidades**
1. ¿Acceso al sistema de archivos? ¿Qué carpetas?
2. ¿Hardware específico? (impresoras, escáneres, dispositivos USB)
3. ¿Funciona online u offline?

**Bloque I4 — Distribución**
1. ¿Cómo se distribuye? (instalador local, web download, store)
2. ¿Auto-actualización?
3. ¿Licenciamiento? (gratuito, freemium, pago)

---

## Script o Automatización

**Bloque G5 — Ejecución**
1. ¿Se ejecuta manualmente o programado? (cron, Task Scheduler)
2. ¿En qué sistema corre? (servidor Linux, Windows local, contenedor)
3. ¿Necesita interfaz CLI con argumentos o solo se ejecuta y listo?

**Bloque H5 — Entrada y salida**
1. ¿De dónde toma los datos? (archivos, API, base de datos, web scraping)
2. ¿A dónde van los resultados? (archivo CSV/JSON, BD, email, mensaje en Slack)
3. ¿Manejo de errores: notifica, reintenta, ignora?

**Bloque I5 — Mantenimiento**
1. ¿Cuán frecuente es la ejecución? (cada hora, diaria, mensual)
2. ¿Logs? ¿Dónde se almacenan?
3. ¿Alguien lo monitorea o debe ser 100% autónomo?

---

## Bot o Agente IA

**Bloque G6 — Plataforma**
1. ¿En qué plataforma vive el bot? (Telegram, WhatsApp, Discord, Slack, web propio, móvil)
2. ¿Interactúa por texto, voz, o ambos?
3. ¿Es público o solo para usuarios autorizados?

**Bloque H6 — Inteligencia**
1. ¿Qué proveedor de LLM? (OpenAI, Anthropic, local con Ollama, etc.)
2. ¿Necesita acceso a herramientas/tools? (búsqueda web, calculadora, base de datos, APIs)
3. ¿Memoria conversacional? ¿Por cuánto tiempo recuerda?

**Bloque I6 — Casos de uso**
1. ¿Para qué se usará principalmente? (atención al cliente, asistente personal, análisis de datos, etc.)
2. ¿Cómo manejas conversaciones largas? (resumen automático, ventana deslizante)
3. ¿Hay temas que el bot NO debe responder?

---

## Videojuego

**Bloque G7 — Tipo**
1. ¿Género? (plataformas, RPG, FPS, puzzle, idle, etc.)
2. ¿2D o 3D?
3. ¿Single player, multijugador local, multijugador online?

**Bloque H7 — Motor y plataforma**
1. ¿Qué motor? (Unity, Godot, Unreal, Phaser para web, custom)
2. ¿Plataformas objetivo? (PC, móvil, consola, web)
3. ¿Distribución? (Steam, itch.io, App Store, web pública)

**Bloque I7 — Mecánicas y contenido**
1. ¿Mecánicas principales del juego? (ej: salto, disparo, recolección, construcción)
2. ¿Arte: pixel art, low poly, 3D realista, etc.?
3. ¿Música y efectos? ¿Originales o licenciados?

---

## Otro / Mixto

Si el usuario elige "Otro" o describe un proyecto que mezcla varios tipos (ej: web app + móvil + bot IA):

1. Pídele que describa el proyecto en 2-3 párrafos detalladamente
2. Identifica los subcomponentes principales
3. Aplica las preguntas relevantes de cada tipo a cada subcomponente
4. Trata el proyecto como uno solo en la documentación final, mencionando cada subcomponente como un módulo
