# Stacks Tecnológicos Recomendados

Stacks battle-tested para 2026. Cuando el usuario pide recomendación, sugiere basándote en tipo + tamaño. Justifica brevemente.

---

## Web App con Usuarios

### Pequeño (1 dev, < 1 mes)
- **Backend**: Django o Rails (incluye todo: auth, ORM, admin)
- **Frontend**: Templates del backend (no SPA)
- **DB**: SQLite o PostgreSQL
- **Despliegue**: Render, Railway, o Fly.io

### Mediano (recomendado para la mayoría)
- **Backend**: FastAPI (Python) o NestJS (TypeScript)
- **Frontend**: React + Vite + Tailwind + Zustand
- **DB**: PostgreSQL
- **Auth**: JWT propio o Supabase Auth
- **Despliegue**: Docker Compose en VPS, o Vercel + Railway

### Grande
- **Backend**: NestJS o Spring Boot
- **Frontend**: Next.js o Nuxt
- **DB**: PostgreSQL + Redis (cache)
- **Auth**: Auth0 o Keycloak
- **Infra**: Kubernetes o AWS ECS

---

## API REST Pura

### Pequeño
- FastAPI (Python) o Express (Node)
- SQLite o PostgreSQL
- Swagger automático

### Mediano
- FastAPI o NestJS
- PostgreSQL
- Redis para cache
- Tests con pytest o Jest

### Grande
- NestJS o Go (Gin/Echo) o Java Spring Boot
- PostgreSQL + Redis + posible Kafka
- API Gateway (Kong o Traefik)
- Observabilidad: Prometheus + Grafana

---

## App Móvil

### Pequeño
- React Native con Expo (no requiere Mac para iOS)
- Backend: Firebase o Supabase
- Almacenamiento local: AsyncStorage

### Mediano
- Flutter (mejor UI) o React Native
- Backend: Firebase, Supabase, o backend propio
- DB local: SQLite o Hive

### Grande
- Nativo: Swift + Kotlin (mejor performance y UX)
- O Flutter si tiempo limitado
- Backend propio escalable
- CI/CD: Fastlane + App Center

---

## App de Escritorio

### Pequeño
- Electron o Tauri (web tech)
- Tauri es más liviano y seguro

### Mediano
- Tauri + React/Vue (recomendado)
- O .NET con Avalonia (multiplataforma)

### Grande
- Tauri o Qt
- Empaquetado profesional con installers firmados

---

## Script o Automatización

### Pequeño
- Python con type hints + Click (CLI args)
- Logging básico
- Sin Docker, ejecución directa

### Mediano
- Python + Pydantic (validación) + Click
- pytest para tests
- Docker para distribuir
- Logs estructurados (structlog)

### Grande
- Python + Pydantic + Click
- Orquestador: Airflow o Prefect
- Observabilidad: Prometheus + Grafana
- CI/CD completo

---

## Bot o Agente IA

### Pequeño
- Python + python-telegram-bot (o equivalente para la plataforma)
- LLM: OpenAI API o Anthropic Claude API
- Sin memoria persistente (solo en RAM)

### Mediano
- Python + framework de la plataforma
- LLM con tools (function calling)
- Memoria: Redis o SQLite
- Vector DB para RAG: Chroma o Qdrant

### Grande
- Python + LangGraph o framework multi-agente
- LLM con tools complejas
- Vector DB: Qdrant o Weaviate
- Cola de mensajes: Redis Queue o Celery
- Observabilidad para razonamiento del agente

---

## Videojuego

### Pequeño
- **2D**: Godot (gratis, ligero) o Phaser (web)
- **3D**: Godot o Unity LTS
- Arte: assets gratis de OpenGameArt o Itch

### Mediano
- **2D**: Godot o Unity
- **3D**: Unity LTS o Unreal 5
- Audio: Audacity + sfxr
- Versionado: Git con LFS

### Grande
- Unity con HDRP o Unreal 5
- Plástico SCM o Git LFS para arte
- Multijugador: Mirror, Photon, o Unreal Replication
- CI/CD: GitLab/GitHub Actions + Steam upload

---

## Justificación para el usuario

Cuando le recomiendes un stack al usuario:

1. Menciona los componentes principales (3-5 elementos)
2. Una razón clara por componente (no más)
3. Mencionar si es "battle-tested" o "moderno emergente"
4. Si hay alternativas válidas, mencionar 1 alternativa

Ejemplo:
```
"Para tu app de delivery (web mediana) recomiendo:

- FastAPI (backend): rápido, auto-documenta APIs, gran ecosistema Python
- React + Vite (frontend): el más usado, fácil de contratar talento
- PostgreSQL (DB): robusto, gratuito, escala bien
- Tailwind (estilos): velocidad de desarrollo
- Docker (despliegue): portabilidad entre máquinas

Alternativa válida: cambiar FastAPI por NestJS si prefieren TypeScript en backend.
¿Aceptas este stack o quieres ajustar algo?"
```
