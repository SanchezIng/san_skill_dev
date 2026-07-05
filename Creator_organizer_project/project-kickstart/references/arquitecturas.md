# Arquitecturas Recomendadas según Tipo y Tamaño

Esta guía indica QUÉ arquitectura recomendar en cada combinación tipo+tamaño. Justifica brevemente cada elección al usuario.

---

## Principios generales

- **Pequeño** → priorizar simplicidad sobre flexibilidad. Monolito modular.
- **Mediano** → separar capas claramente. Permitir cambios futuros.
- **Grande** → arquitecturas que escalen y permitan trabajo en paralelo entre múltiples desarrolladores.

---

## Web App con Usuarios

| Tamaño | Arquitectura | Justificación |
|--------|-------------|---------------|
| Pequeño | Monolito MVC (un solo proyecto con vistas, controladores, modelos) | Fácil de mantener por una persona, despliegue simple |
| Mediano | Backend + Frontend separados (API REST + SPA) | Permite escalar frontend y backend independientemente |
| Grande | Arquitectura hexagonal o capas + microservicios opcionales | Escalable, mantenible, varios equipos pueden trabajar en paralelo |

**Stack típico por tamaño:**
- Pequeño: Django/Rails/Laravel monolito con templates
- Mediano: FastAPI/Express/NestJS + React/Vue + base de datos
- Grande: Backend modular + frontend + cache + base de datos + posiblemente cola de mensajes

---

## API REST Pura

| Tamaño | Arquitectura | Justificación |
|--------|-------------|---------------|
| Pequeño | Capas simples: routers → servicios → modelos | Suficiente para CRUD básico |
| Mediano | Arquitectura limpia (Clean Architecture): controllers → use cases → entities → repositories | Separación clara de responsabilidades |
| Grande | Hexagonal + DDD (Domain-Driven Design) | Permite escalar y mantener dominio complejo |

---

## App Móvil

| Tamaño | Arquitectura | Justificación |
|--------|-------------|---------------|
| Pequeño | MVC simple o MVVM básico | Suficiente para apps con pocas pantallas |
| Mediano | MVVM completo + Repository Pattern | Separación de UI, lógica y datos. Facilita testing |
| Grande | Clean Architecture (presentación → dominio → datos) + módulos | Escalable, testeable, soporta equipos múltiples |

---

## App de Escritorio

| Tamaño | Arquitectura | Justificación |
|--------|-------------|---------------|
| Pequeño | MVC o estructura por carpetas (views/logic/data) | Aplicaciones de utilidad simple |
| Mediano | MVVM o MVP | Mejor separación UI/lógica, especialmente con frameworks como WPF, Electron |
| Grande | Plugin architecture o modular | Permite extensibilidad y separar funcionalidades |

---

## Script o Automatización

| Tamaño | Arquitectura | Justificación |
|--------|-------------|---------------|
| Pequeño | Un solo archivo bien estructurado con funciones | Mantener simple, no sobre-ingeniar |
| Mediano | Módulos separados: input → processing → output → utils | Reutilización de funciones, testing más fácil |
| Grande | Pipeline architecture o ETL formal con orquestador | Para flujos complejos con muchas etapas y manejo de errores robusto |

---

## Bot o Agente IA

| Tamaño | Arquitectura | Justificación |
|--------|-------------|---------------|
| Pequeño | Handler + LLM client + storage simple | Bots con flujos lineales |
| Mediano | Estado conversacional + tools + memoria + LLM | Bots con herramientas externas y memoria persistente |
| Grande | Multi-agente con orchestrator + tools + RAG + vector DB | Sistemas complejos con múltiples agentes especializados |

---

## Videojuego

| Tamaño | Arquitectura | Justificación |
|--------|-------------|---------------|
| Pequeño | Estructura por escenas (Godot) o por GameObjects (Unity) | Para juegos cortos y prototipos |
| Mediano | Component-based + Event System + State Machines | Manejar mecánicas variadas sin acoplamiento alto |
| Grande | ECS (Entity-Component-System) + servicios + módulos | Performance y escalabilidad para juegos complejos |

---

## Cómo presentar la arquitectura al usuario

Cuando elijas una arquitectura, comunícala así al usuario:

```
"Para tu proyecto [TIPO] de tamaño [TAMAÑO], recomiendo [ARQUITECTURA].

Por qué:
- [Razón 1 práctica]
- [Razón 2 práctica]

Esto significa que la estructura tendrá [N capas/módulos]:
- [Capa 1: responsabilidad]
- [Capa 2: responsabilidad]
- [Capa 3: responsabilidad]

¿Te parece bien o prefieres una arquitectura distinta?"
```

Si el usuario propone otra, respeta su decisión pero advierte si crees que tendrá problemas (ej: "Microservicios para un proyecto pequeño suele ser sobreingeniería, pero adelante si quieres").
