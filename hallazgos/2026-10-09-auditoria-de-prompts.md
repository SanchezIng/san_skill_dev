# Las instrucciones del agente se contradicen y envejecen dentro del proyecto

**Fecha:** 2026-10-09 · **Estado:** abierto en el kit (corregido en FARMICROW, [PR #260](https://github.com/KaterineDev/farmicrow/pull/260)) · **Proyecto:** FARMICROW

Salió de una auditoría de los prompts de FARMICROW (`CLAUDE.md`, las skills `equipo-*` y
las del kickstart) contra el modelo con el que trabaja el equipo. FARMICROW no llama a la
API de Claude: todo lo que el modelo lee como texto es la configuración del agente, y casi
toda sale de este kit. De los diez hallazgos, cinco nacen aquí y no en el proyecto. Este
fichero los recoge; el arreglo en el kit está por hacer.

## Lo que se vio

### 1. El CLAUDE.md que genera el kickstart contradice a `/cerrar-sesion` · alta

| Dónde | Qué dice |
|---|---|
| `skills/project-kickstart/references/plantillas.md:262-267` y `references/contexto_claude_code.md:152-157` | «**Antes de cerrar, SIEMPRE:** … 3. Actualizar `progreso/estado-actual.md` · 4. Crear/actualizar el handoff · 5. Si quedan TODOs, anotarlos en el handoff» |
| `skills/equipo/cerrar-sesion.SKILL.md`, paso 3 | «`estado-actual.md` casi nunca se toca» · «Handoff solo si dejas el módulo a medias» · «TODOs que sobreviven → issue en el Project, no un párrafo en un fichero» |

En modo equipo se instalan los dos y **se cargan juntos en cada sesión**. Nada le dice al
agente cuál manda, y en FARMICROW `git blame` no pudo ordenarlos (los dos entraron en el
mismo commit de instalación). El equipo practicaba la skill: los últimos cierres reales no
dejaron handoff. En FARMICROW `estado-actual.md:3` además repetía «se actualiza SIEMPRE al
cerrarla».

**Propuesta:** en modo equipo, la plantilla de CLAUDE.md dice «Antes de cerrar, invoca
`/cerrar-sesion`» y resume lo que hace; la lista de cinco pasos se queda solo para el modo
sin protocolo. Es el mismo patrón que [la deriva del kit portable](2026-07-29-deriva-del-kit-portable.md):
dos piezas del kit que evolucionaron por separado y enseñan reglas distintas.

### 2. `cerrar-sesion.SKILL.md:79-80` trae una lista de «no tocar» inventada · alta

> Si el PR toca algún archivo de la lista "no tocar sin avisar" del CLAUDE.md
> (imagen/contenedores, workflows de CI, fronteras entre módulos)

El paréntesis es un ejemplo de otro proyecto copiado como si fuera la lista. La de
FARMICROW (docs 01-06, `desing/`, `prisma/migrations/`, `src/server/db/`, guardas) no
incluye «imagen/contenedores». **Propuesta:** quitar el paréntesis y apuntar a la sección,
`CLAUDE.md` § ARCHIVOS QUE NO TOCAR SIN AVISAR, en vez de copiarla.

### 3. Los placeholders de `verificar.SKILL.md` envejecen nada más instalarse · media

- `{{N_TESTS}}` y `{{DURACION_SUITE}}` se rellenan el día de la instalación. En FARMICROW
  quedó «Referencia sana: 0 (aun no hay suite: la crea F1.1) tests, ~por medir en F1.1».
  Hoy son 136 ficheros de test y el texto sigue diciendo 0. Un número fijo en una skill es
  justo lo que la regla «lo que el compilador vigila no se copia en prosa» prohíbe.
  **Propuesta:** quitar los dos placeholders; «la suite entera en verde» no caduca.
- Los comentarios `<!-- PLANTILLA: … -->` y `<!-- Ej.: … -->` sobreviven a la instalación.
  Son instrucciones para quien instala, y el agente las lee cada vez que carga la skill.
  **Propuesta:** que `instalar.sh` (o el paso de rellenado) los borre, o que `deriva_kit.py`
  los denuncie igual que hoy denuncia un `{{…}}` sin rellenar.
- `{{CMD_LEVANTAR_STACK}}` seguido de `{{CMD_TEST}}` admite un comando que no termina.
  FARMICROW lo rellenó con `docker compose up -d && pnpm dev`, y `pnpm dev` no vuelve nunca,
  así que `pnpm test` no corría en esa terminal. **Propuesta:** en la tabla del README,
  avisar de que el nivel 1 solo admite comandos que terminan (`docker compose up -d --wait`
  sí; un servidor de desarrollo no).

### 4. Porcentajes de una ventana de 200k · media

| Dónde | Texto |
|---|---|
| `skills/equipo/que-toca.SKILL.md:82` | «el 43% del presupuesto útil de una ventana de 200k» |
| `skills/equipo/que-toca.SKILL.md:205` | «el 20% de una ventana de 200k» |
| `skills/equipo/cerrar-sesion.SKILL.md:208-209` | «el 20% de una ventana de 200k» |
| `plantillas/protocolo/tablero.py:599` (comentario) | «el 20% de una ventana de 200k» |

Las reglas siguen valiendo (no abrir el tablero, `--jq` siempre), pero los porcentajes ya
no: dependen del modelo, y los actuales tienen ventanas de 1M. **Propuesta:** dejar los
tokens medidos (~51.900, ~40.700), que son el dato, y quitar los porcentajes, que son una
cuenta que caduca con cada modelo.

### 5. El pre-commit «en contenedor» de `cerrar-sesion.SKILL.md:74` · baja

> Si los hooks de pre-commit corren en contenedor, el commit tarda: usar timeout largo.

Ya salió como ejemplo en [la aplicación de reglas](2026-07-22-aplicacion-de-reglas.md) y
sigue igual. En FARMICROW el pre-commit (`.husky/pre-commit`) corre en el host: gitleaks y
lint-staged. Lo útil allí era saber que **sin `gitleaks` el commit se para a propósito**.
**Propuesta:** convertirlo en placeholder (`{{NOTA_PRE_COMMIT}}`) o en una línea genérica
que mande a mirar el hook real.

## Lo que quedó en el proyecto, no en el kit

Los otros cinco hallazgos eran de FARMICROW y se corrigieron allí: el párrafo «Fase activa
actual» de `CLAUDE.md` parado en T-022, `pnpm db:migrate` documentado como `prisma migrate
dev` cuando el script es `prisma migrate` (sin subcomando no migra y sale con 0), y las
instancias de los puntos 2 a 5 de arriba.

## Por qué importa

Ninguno de estos textos rompe nada a la vista: el agente los lee, los obedece o los
reconcilia en silencio. Las contradicciones (punto 1) hacen que el cierre dependa de qué
fichero pese más en esa sesión, y las cifras fijas (puntos 3 y 4) le dan al modelo hechos
falsos con la autoridad de una skill. Es la deriva doc↔realidad que `docs_check.py` vigila
en los documentos del proyecto, pero en las instrucciones del agente, donde ninguna guarda
mira.
