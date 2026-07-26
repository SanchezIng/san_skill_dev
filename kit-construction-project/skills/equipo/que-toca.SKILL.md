---
name: equipo-que-toca
description: Protocolo de reclamo de tareas del equipo (el candado central entre los devs). Úsala SIEMPRE que el dev diga "¿qué toca?", "qué fase toca", "toma una tarea", "toma T-nnn", "reclama", "qué hago ahora" o similar, ANTES de escribir cualquier código. Sincroniza main, busca la tarea Disponible sin assignee en el Project de GitHub, la reclama (assignee + En progreso), la espeja en el tablero del repo y prepara la rama y el contexto de arranque.
---

# /que-toca — Protocolo de reclamo de tareas

Eres el ejecutor del **candado central de convivencia** entre los devs del equipo:
el reclamo en GitHub es lo que impide que dos Claudes codeen lo mismo. Ejecuta
TODOS los pasos en orden. No escribas código de la tarea hasta terminar el paso 7.

**El candado es el paso 4** (assignee + estado del Project), no el tablero del repo:
ocurre en GitHub, es atómico y lo ve el equipo entero al instante. Todo lo demás es
preparación o resumen.

## Datos fijos de este repo

| Qué | Valor |
|---|---|
| Project | `gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --limit 500` |
| projectId | `{{PROJECT_ID}}` |
| fieldId Status | `{{STATUS_FIELD_ID}}` |
| Opciones Status | Disponible=`{{OPT_DISPONIBLE}}` · Bloqueada=`{{OPT_BLOQUEADA}}` · En progreso=`{{OPT_EN_PROGRESO}}` · Review=`{{OPT_REVIEW}}` · Terminado=`{{OPT_TERMINADO}}` |
| Ramas | `{{PREFIJO_RAMA}}` |

## Paso 1 — Sincronizar

```bash
git checkout main && git pull origin main
```

Tablero y handoffs frescos. Si hay cambios locales sin commitear, resuélvelos antes.

## Paso 2 — ¿Ya tiene tarea el dev?

```bash
gh issue list --state open --assignee @me --limit 200 --json number,title
```

Si ya tiene una `En progreso` asignada → **retomarla** (WIP máx 1-2), no reclamar otra.
Salvo que el dev haya pedido una tarea concreta ("toma T-nnn"): en ese caso esa es la elegida
(verificar igualmente que está Disponible y sin assignee).

## Paso 3 — Buscar tarea disponible

```bash
# Estado por tarea. El limite va alto A PROPOSITO: por defecto gh trae 30.
gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --format json --limit 500

# Quien NO tiene dueño. Filtra el SERVIDOR, no nosotros: traerse todos los
# issues y descartar aqui es lo que hacía que se colaran los de más allá del tope.
gh issue list --state open --search "no:assignee" --limit 500 --json number,title
```

**Antes de concluir nada, comprueba que las listas no vienen cortadas:** si
alguna devuelve exactamente tantos elementos como el `--limit`, es que hay más y
no los estás viendo. En ese caso **sube el límite y repite** — nunca decidas
sobre una lista truncada.

> Por qué este aviso, y por qué el filtro va en el servidor: antes se pedían
> **todos** los issues y se descartaban aquí los que tuvieran assignee. Con el
> tope por defecto (30), en un proyecto normal la lista se cortaba y las tareas
> de más allá del tope no aparecían — con lo cual **parecían sin dueño por
> ausencia de datos**. Eso no es "faltan opciones": es `/que-toca` dando por
> libre una tarea que otro dev ya tiene, justo lo que el candado existe para
> impedir.
>
> Preguntando directamente por `no:assignee`, una lista truncada ya solo puede
> **ocultar** tareas libres, nunca inventarlas. El fallo pasa de "dos devs sobre
> la misma tarea" a "hoy ves menos opciones": sigue siendo un fallo, pero cae del
> lado seguro. Por eso el aviso de arriba sigue haciendo falta, y por eso el
> orden importa — un límite que miente en silencio es peor que un error.

Elegir la de **menor número** entre las `Disponible` sin assignee (o del módulo que el
dev prefiera). Anotar el `id` del item (campo `id` donde `content.number == N`).

Si el Project dice `Disponible` pero el issue **no** sale en la lista de "sin
assignee", está cogido: el Project va desactualizado, no al revés. La verdad
sobre quién tiene qué es el assignee del issue.

## Paso 4 — Reclamar (el candado)

Re-verificar que `assignees` sigue vacío JUSTO antes, y entonces:

```bash
gh issue edit <N> --add-assignee @me
```

Mover a En progreso (lanzar desde el tool Bash, no PowerShell — las comillas del query se pierden):

```bash
gh api graphql -f query='mutation { updateProjectV2ItemFieldValue(input: {projectId: "{{PROJECT_ID}}", itemId: "<ITEM_ID>", fieldId: "{{STATUS_FIELD_ID}}", value: {singleSelectOptionId: "{{OPT_EN_PROGRESO}}"}}) { projectV2Item { id } } }'
```

**Colisión:** si `--add-assignee` falla o al re-verificar ya tiene assignee → otro dev la
ganó: volver al paso 3 y elegir otra.

## Paso 5 — Rama de trabajo

```bash
git checkout -b {{PREFIJO_RAMA}}
```

## Paso 6 — Espejo en el repo (en la rama, NO en main)

En `progreso/tablero-equipo.md`: actualizar la fila del módulo y añadir línea al log
append-only (`- YYYY-MM-DD {dev} reclama T-nnn (#N) — {resumen}`). Se commitea **en la
rama de la tarea** y entra a `main` con el PR:

```bash
git add progreso/tablero-equipo.md
git commit -m "chore(tablero): reclamar T-nnn"
```

**Por qué no va directo a main:** el candado ya se echó en el paso 4. El assignee y el
estado del Project son visibles para todo el equipo **al instante**, y son la verdad
sobre quién tiene qué. El tablero del repo es un resumen de eso: si llegara tarde, no
pasa nada, porque nadie decide mirándolo. Mandarlo a `main` obligaría a dejar la rama
sin proteger para siempre — precio altísimo por sincronizar un resumen.

> **Excepción — proyecto SIN GitHub Project:** si el tablero markdown es el único
> registro (no hay Issues ni Project), entonces **el tablero SÍ es el candado**: hay
> que publicarlo antes de codear y, por tanto, **antes del paso 5** — estando todavía
> en `main`, no en la rama (desde la rama, `git push origin main` empuja el `main`
> local, que no tiene el commit):
>
> ```bash
> git add progreso/tablero-equipo.md
> git commit -m "chore(tablero): reclamar T-nnn"
> git push origin main          # y solo despues, el paso 5 crea la rama
> ```
>
> Si el push rebota → `git pull --rebase` y reintentar; si el log muestra que otro
> reclamó la misma T-nnn primero, ceder y volver al paso 3.
>
> En ese modo `main` no puede estar protegida del todo: es el precio de no tener el
> candado en GitHub. Elegir un modo u otro, nunca los dos. Ver `trabajo_en_equipo.md` §9.

## Paso 7 — Arrancar con contexto

1. Leer el **handoff más reciente del módulo** (`progreso/fase-*-{modulo}.md`).
2. Leer la sección de la subfase en `docs/guia_desarrollo.md` (o el issue si es bug/DX).
3. Invocar la skill **`secure-coding-guard`** (obligatoria antes de la primera línea).
4. Recién ahora, codear.

## Al terminar la tarea

No cierres a mano: usa **`/cerrar-sesion`**, que ejecuta el checklist completo de cierre.
