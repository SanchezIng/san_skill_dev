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
| Project | `gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --limit 500` — **siempre con `--jq`**, ver paso 3 |
| IDs del Project | **se resuelven solos**: `python3 scripts/tablero.py` |
| Ramas | `{{PREFIJO_RAMA}}` |

> Aquí había siete IDs de GraphQL pegados a mano. Ya no: `scripts/tablero.py`
> los descubre en cada ejecución, así que no pueden quedarse obsoletos. Si el
> Project se recrea o alguien renombra una columna, el script **para** con un
> diagnóstico en vez de dejar el candado a medias.

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
# Estado por tarea. Da dos cosas de una vez: el TOTAL de items (para detectar el
# tope) y solo las candidatas, ya filtradas. El limite va alto A PROPOSITO: por
# defecto gh trae 30.
#
# El `--jq` NO es cosmetico. Sin el, este comando IMPRIME todos los items con su
# `body` integro para elegir UNO, y se quedan en el contexto el resto de la
# sesion. Medido en un proyecto real de ~90 tareas: 186.932 chars (~51.900
# tokens) frente a 427 (~119). Con ventana de 200k y la regla de cerrar al 60%,
# la version sin filtrar se lleva el 43% del presupuesto util de la sesion.
# Escala con el numero de tareas, asi que solo empeora.
#
# Ojo con lo que hace y lo que no: `--jq` filtra la SALIDA, no la peticion. La
# respuesta de la API sigue trayendo los items enteros. Lo que se ahorra es
# contexto, que es el problema real aqui — pero no confundirlo con el filtro
# server-side de la linea de abajo (`--search "no:assignee"`), que es otra cosa.
#
# Este comando TAMBIEN tiene filtro server-side (`--query "status:Disponible"`) y
# NO se usa a proposito: con el, `.items|length` pasaria a contar solo las
# candidatas y se perderia la deteccion del tope de mas abajo. Se prefiere pagar
# la respuesta entera y quedarse con el total honesto.
#
# `(.assignees // [])` no sobra: hay items con `assignees` a null y `join` sobre
# null aborta el filtro entero — imprime el total y NADA mas. Falla de forma
# ruidosa, pero se parece demasiado a "no hay tareas disponibles".
#
# El titulo se lee de `.content.title`, NO del `.title` del item: ese segundo es
# una copia congelada al añadir la tarjeta y NO sigue los renombrados del issue.
# En el proyecto donde se midio esto habia 9 items desincronizados, y en uno el
# item decia una tarea y el issue decia otra REAL distinta: elegir por ese numero
# es reclamar otra cosa.
#
# El `sort_by` esta porque la API no devuelve orden por numero y el criterio de
# eleccion de abajo es "la de menor numero".
gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --format json --limit 500 --jq '
  "items en el Project: \(.items|length)",
  ([.items[] | select(.status=="Disponible")] | sort_by(.content.number) | .[]
            | [.content.number, ((.assignees // []) | join(",")), .content.title] | @tsv)'

# Quien NO tiene dueño. Filtra el SERVIDOR, no nosotros: traerse todos los
# issues y descartar aqui es lo que hacía que se colaran los de más allá del tope.
gh issue list --state open --search "no:assignee" --limit 500 --json number,title
```

**Antes de concluir nada, comprueba que las listas no vienen cortadas:** si
alguna devuelve exactamente tantos elementos como el `--limit`, es que hay más y
no los estás viendo. En ese caso **sube el límite y repite** — nunca decidas
sobre una lista truncada.

> Por eso el primer comando imprime `items en el Project: N` antes de las
> candidatas: recortar la salida te ahorra el contexto, pero también te
> quitaría de la vista el síntoma del tope. Si ese número iguala al `--limit`,
> hay más y el filtro los está descartando sin que se note. El total se mantiene
> visible precisamente porque el detalle deja de estarlo.

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

**Segunda comprobación, y falla al revés que la anterior:** que un issue esté abierto
no significa que esté en el Project. `gh issue create` **no** lo añade, así que una
tarea puede existir en Issues y ser invisible aquí — este paso solo mira el Project.
Una lista truncada te oculta tareas *de la lista*; esto te oculta tareas *que nunca
entraron en la lista*, y no hay síntoma: la búsqueda parece funcionar.

```bash
# Issues abiertos que NO estan en el Project. Vacio = ninguno fuera.
comm -13 \
  <(gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --format json --limit 500 --jq '.items[].content.number' | sort) \
  <(gh issue list --state open --limit 500 --json number --jq '.[].number' | sort)
```

Si sale algún número, **añádelo antes de elegir tarea** — son tareas reales que nadie
puede reclamar. Son tres pasos, no uno, y los dos últimos se olvidan porque `item-add`
no protesta:

```bash
gh project item-add {{PROJECT_NUMBER}} --owner {{OWNER}} --url <url-del-issue>

gh issue edit <N> --add-label "modulo:<X>"      # si el tablero saca el modulo de una
                                                # LABEL, no la deduce del titulo

# item-add NO devuelve el id del item; hay que buscarlo por el numero de issue:
ITEM_ID=$(gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --format json --limit 500 \
  --jq ".items[]|select(.content.number==<N>)|.id")
python3 scripts/tablero.py --mover "$ITEM_ID" "Disponible"   # o "Bloqueada" si algo la frena
```

**`item-add` no imprime nada y deja el `Status` en `null`.** Un item sin estado no
cae en ninguna columna: lo has "añadido" y sigue sin verse. Por eso el tercer paso no
es opcional. Confirmar que no queda ninguno suelto:

```bash
gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --format json --limit 500 \
  --jq '[.items[]|select(.status==null)|.content.number]'   # debe salir []
```

> Caso real (2026-07-29): **seis** issues abiertos de tres personas estaban fuera del
> Project, incluidas una deuda de RLS y el rate limiting de OWASP A04. Ninguna era
> reclamable, y nadie lo notó porque el paso 3 devolvía resultados con normalidad.
> Añadir el issue al Project es parte de crearlo; esta comprobación caza al que se
> olvide.

Elegir la de **menor número** entre las `Disponible` sin assignee (o del módulo que el
dev prefiera). La segunda columna de la salida ES el assignee: si trae algo, esa tarea
tiene dueño aunque el Project la pinte `Disponible`. El `id` del item no hace falta
todavía — se resuelve en el paso 4, por número.

Si el Project dice `Disponible` pero el issue **no** sale en la lista de "sin
assignee", está cogido: el Project va desactualizado, no al revés. La verdad
sobre quién tiene qué es el assignee del issue.

## Paso 4 — Reclamar (el candado)

Re-verificar que `assignees` sigue vacío JUSTO antes, y entonces:

```bash
gh issue edit <N> --add-assignee @me
```

Mover la tarjeta a En progreso. El `id` del item **no** es el número del issue, y el
paso 3 ya no lo imprime — son ~28 chars por item acarreados para usar exactamente uno.
Se resuelve por número:

```bash
ITEM_ID=$(gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --format json --limit 500 \
  --jq ".items[]|select(.content.number==<N>)|.id")

python3 scripts/tablero.py --mover "$ITEM_ID" "En progreso"
```

El script resuelve los IDs, mueve, y **relee el estado para confirmar que la
tarjeta quedó donde debía** — que la API responda OK no es que se haya movido.
Si algo falla, sale con error explicando qué: entonces **no des la tarea por
reclamada**, porque el tablero no dice lo que crees.

**Colisión:** si `--add-assignee` falla o al re-verificar ya tiene assignee → otro dev la
ganó: volver al paso 3 y elegir otra.

## Paso 5 — Rama de trabajo

```bash
git checkout -b {{PREFIJO_RAMA}}
```

## Paso 6 — Espejo en el repo (en la rama, NO en main)

**La tabla NO se comitea** (va en `.gitignore`): es un espejo del Project y se
regenera cuando la quieras ver. Lo único que se comitea es lo que teclea una
persona, y solo si tiene algo que contar que el Project no diga (un acuerdo de
frontera, una trampa que te costó el intento anterior): **una entrada nueva del
log, en su propio fichero.**

```bash
# Opcional, solo si hay algo que contar. UN FICHERO NUEVO — no toques los de nadie:
cat > progreso/log/$(date +%F)-reclamo-t-nnn.md <<'EOF'
YYYY-MM-DD {dev} reclama T-nnn (#N) — {lo que el Project no cuenta}
EOF
git add progreso/log/
git commit -m "chore(tablero): reclamar T-nnn"

# Para VERLO (tabla + log ensamblado). No genera nada que comitear:
python3 scripts/tablero.py --generar
```

**Por qué un fichero por entrada:** antes el log vivía dentro del tablero y todos
añadían al final del mismo archivo. Eso no evita conflictos, los garantiza — en el
proyecto piloto, con 3 PRs abiertos el mismo día, los 3 chocaban ahí. Ficheros
distintos los hacen imposibles: git une sin preguntar.

Si `--generar` falla, **no escribas la tabla a mano**: se arregla en el Project y se
vuelve a generar. La tabla escrita a mano es justo lo que produjo tres derivas en
dos días de uso real.

⛔ **Regenerarlo es gratis; ABRIRLO no.** `--generar` imprime un par de líneas, pero
el fichero que deja crece con el Project: en un proyecto real de ~90 tareas pesaba
**150.661 chars ≈ 40.700 tokens**, el 20% de una ventana de 200k. Es para leerlo una
persona de un tirón. **Un agente no lo abre**: el estado que necesita se lo dio el
paso 3 por ~119 tokens. Por eso `--generar` imprime ahora el peso al terminar — para
que la cifra esté delante de quien vaya a abrirlo, en vez de en un párrafo que
envejece.

**Por qué no va directo a main:** el candado ya se echó en el paso 4. El assignee y el
estado del Project son visibles para todo el equipo **al instante**, y son la verdad
sobre quién tiene qué. La entrada del log es contexto, no estado: si llega tarde no
pasa nada, porque nadie decide mirándola. Mandarla a `main` obligaría a dejar la rama
sin proteger para siempre — precio altísimo por sincronizar una nota.

> **Excepción — proyecto SIN GitHub Project:** si el tablero markdown es el único
> registro (no hay Issues ni Project), entonces **el tablero SÍ es el candado**, y
> ahí la tabla se escribe a mano porque no hay de dónde generarla (`--generar` no
> aplica: no existe la fuente). En ese modo **el tablero se comitea** — hay que
> quitarlo del `.gitignore`, porque ahí sí es la fuente de verdad y no un espejo.
> Hay que publicarlo antes de codear y, por tanto, **antes del paso 5** — estando
> todavía en `main`, no en la rama (desde la rama, `git push origin main` empuja el
> `main` local, que no tiene el commit):
>
> ```bash
> git add progreso/tablero-equipo.md   # requiere haberlo sacado del .gitignore
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
2. Leer **la sección de la subfase, no el fichero**, en `docs/guia_desarrollo.md`
   (o el issue si es bug/DX). La guía cubre TODAS las fases del proyecto y tú vas
   a tocar una: medido en un proyecto real, 45.065 chars el fichero contra
   877–2.646 una subfase — entre **17× y 50×** por la misma información útil.
   Extráela con su cabecera:

   ```bash
   # Ajusta el patron: "### SUBFASE 4[.]2", "## FASE 3", "### SUBFASE 1[.]5"...
   # Corta en la siguiente cabecera de nivel igual o MENOR, asi que sirve tanto
   # para una subfase suelta como para una fase sin subfases, y tambien para la
   # ultima subfase de una fase, que termina en el "## FASE n+1".
   # Los [.] son a proposito: "\." suelta un warning en gawk.
   awk -v pat='^### SUBFASE 4[.]2' \
     '$0 ~ pat {f=1; n=length($1); print; next}
      f && /^#+ / && length($1) <= n {exit}
      f' docs/guia_desarrollo.md
   ```

   Si no sabes el número exacto, `grep -n "^#\+ .*\(FASE\|SUBFASE\)" docs/guia_desarrollo.md`
   da el índice entero en unas decenas de líneas.

   **La regla vale para todo documento de catálogo**, no solo para la guía:
   `docs/backlog.md` crece hasta ser el más pesado del repo (91.302 chars en el
   proyecto medido) y una entrada son ~1.635 — **56× menos**. Se localiza con
   `grep -n "^### T-nnn"` y se lee ese rango. Abrir el fichero entero para mirar
   una tarea es el error por defecto, y no avisa de nada.
3. Invocar la skill **`secure-coding-guard`** (obligatoria antes de la primera línea).
4. Recién ahora, codear.

## Al terminar la tarea

No cierres a mano: usa **`/cerrar-sesion`**, que ejecuta el checklist completo de cierre.
