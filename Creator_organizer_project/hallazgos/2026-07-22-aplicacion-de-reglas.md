# Hallazgos de uso real — 2026-07-22

> Origen: sesión de trabajo en `portal-web-api-sunat`, un proyecto instalado con
> este kit. Los seis hallazgos son **fallos de diseño del kit**, no del proyecto:
> se reproducen en cualquier repo que lo instale.
>
> | # | Hallazgo | Severidad | Estado |
> |---|---|---|---|
> | 1 | `secure-coding-guard` solo se exige al reclamar tarea | 🔴 | **Corregido aquí** |
> | 2 | Comando de auditoría prescrito sin decir qué hacer con él | 🟠 | Propuesto |
> | 3 | El kit prescribe un espejo de un espejo | 🟠 | Propuesto |
> | 4 | Crea las condiciones para la deriva de ramas, sin mecanismo | 🟠 | Propuesto |
> | 5 | Declara la regla de revisión sin decir cómo se aplica | 🔴 | Propuesto |
> | 6 | Trata los falsos éxitos como anécdotas sueltas | 🔴 | **Corregido aquí** |
>
> Los 1–5 comparten un patrón: **regla declarada sin mecanismo que la aplique**.
> El 6 es distinto y más incómodo: es un fallo en cómo el kit enseña a
> **comprobar** que algo se hizo. Un mecanismo que verifica lo que no importa da
> la misma falsa tranquilidad que no tener ninguno.
>
> El patrón común es el mismo en los tres: **el kit declara una regla y confía en
> que alguien se acuerde de cumplirla.** Cuando el kit sí tiene mecanismo
> (guardas de CI, hook de arranque), la regla se sostiene. Cuando solo hay texto,
> se cae en cuanto el trabajo entra por una puerta imprevista.

---

## Hallazgo 1 🔴 — `secure-coding-guard` solo se exige al reclamar tarea

**Estado: corregido en este PR.**

### Qué pasó

En una sesión completa se resolvieron conflictos de merge en `package.json` y
`vitest.config.ts`, y se mergearon ~2160 líneas de código de autenticación a
`main`. **La skill obligatoria no se invocó ni una vez.**

No fue descuido. La sesión entró por la petición *"revisa las reviews y mergea
lo aprobado"*, que es una tarea de coordinación git. Cuando el trabajo cambió de
forma y pasó a ser resolución de conflictos en código, nadie reevaluó el
disparador.

### La causa en el kit

`skills/equipo/que-toca.SKILL.md`, paso 6.4:

> `4. Invocar la skill secure-coding-guard (obligatoria antes de la primera línea).`

**Ese es el único punto del kit donde la obligación se ejecuta.** Verificado:
`cerrar-sesion.SKILL.md` y `verificar.SKILL.md` no la mencionan, y
`plantillas/hooks/settings.json` solo declara `SessionStart`.

Resultado: la skill está acoplada al flujo "reclamo una tarea nueva". Todo
trabajo que entra por otra puerta la salta en silencio:

| Puerta de entrada | ¿Pasa por `/que-toca`? |
|---|---|
| Reclamar tarea nueva | Sí — cubierto |
| Mergear un PR aprobado | **No** |
| Resolver conflictos | **No** |
| Revisar código ajeno | **No** |
| Hotfix urgente | **No** |
| Retomar tras una pausa | **No** — no se re-reclama |

Agravante observado: al no haber checklist, se hizo seguridad *ad hoc*
(auditoría de dependencias, pruebas anti-enumeración, búsqueda de fugas en
logs). Eso **da falsa sensación de cobertura**: improvisar no equivale a la
skill, cuyos `references/` existen justamente para no depender de qué se le
ocurra mirar a quien esté al mando.

### Corrección aplicada

1. **`plantillas/hooks/settings.json`** — hook `PreToolUse` sobre `Edit|Write`
   que recuerda la skill al tocar código. Es el único punto que *toda* puerta de
   entrada atraviesa: no se puede modificar código sin pasar por ahí.
2. **`skills/equipo/cerrar-sesion.SKILL.md`** — el cierre exige el resumen de
   seguridad de la skill. Segunda red: si el hook se ignoró, el cierre lo caza.

Dos capas a propósito. El hook es un recordatorio y **puede volverse ruido de
fondo** si dispara en cada edición; el checkpoint del cierre no depende de que
nadie lo lea al vuelo.

---

## Hallazgo 2 🟠 — El comando de auditoría se prescribe sin decir qué hacer con él

**Estado: propuesto, no implementado.**

### Qué pasó

El CI del proyecto tenía el paso de auditoría como `continue-on-error: true`.
**Ninguna vulnerabilidad rompía el build, ni siquiera una `critical`.** Dos
`high` vivieron días en `main` con el CI en verde y se descubrieron por
casualidad, al auditar a mano durante un merge.

### La causa en el kit

`references/seguridad_ampliada.md` prescribe el comando por lenguaje
(`npm audit --audit-level=high`, `pip-audit`, `cargo audit`…) y
`practicas_dev.md` lo mete en el checklist de cada fase. Pero **no dice qué debe
pasar cuando encuentra algo**.

Quien genera el CI se topa entonces con un dilema real y sin guía:

- Bloqueante → el CI queda rojo desde el primer día por vulnerabilidades
  transitivas sin fix aguas arriba, y el equipo aprende a ignorar el rojo.
- `continue-on-error` → nunca avisa de nada.

Se elige lo segundo porque lo primero es insostenible, y el resultado es un paso
de CI decorativo.

### Corrección propuesta

Plantilla `plantillas/ci/audit_check.py` + `plantillas/ci/audit-allowlist.json`
con el patrón de **allowlist caducable**: lo aceptado a sabiendas no bloquea, lo
nuevo sí.

Lo que evita que degenere en un `ignore` general es que falle en cuatro casos,
no solo el obvio:

1. Vulnerabilidad `high`/`critical` no listada → lo nuevo para en seco.
2. Entrada **caducada** → obliga a reevaluar; sin caducidad, una excepción se
   vuelve permanente y deja de ser excepción.
3. Entrada que **ya no aparece** en el audit → se arregló aguas arriba y sobra.
   Si se queda, tapa el próximo aviso del mismo paquete.
4. Vencimiento a **más de N días** → sin techo, la fecha se rellena con un año
   lejano y la caducidad no significa nada.

Detalle adicional: la clave debe ser el **identificador del aviso** (GHSA/CVE),
nunca el nombre del paquete — silenciar `sharp` en bloque taparía su próximo CVE.

**Implementación de referencia ya en producción:** `portal-web-api-sunat`,
`scripts/audit_check.py` + `security/audit-allowlist.json` (PR #48). Está escrita
para pnpm; portarla al kit exige parametrizar el gestor de paquetes, que es el
grueso del trabajo pendiente.

---

## Hallazgo 3 🟠 — El kit prescribe un espejo de un espejo

**Estado: propuesto, no implementado. Adyacente al PR #1 de este repo.**

### Qué pasó

El estado de una tarea vive duplicado a mano en cuatro sitios: Project de
GitHub, labels del issue, tabla de `tablero-equipo.md` y tabla de
`estado-actual.md`. En dos días de uso real la duplicación produjo deriva
**tres veces**:

1. `docs/backlog.md` llevaba `Estado:` desfasado desde el kickstart — el campo
   nunca se leyó por ningún automatismo. (Es justo lo que corrige el PR #1.)
2. Al mergear una rama de 4 días: la rama decía que una tarea estaba
   `Disponible`, `main` decía `Review`, y la verdad era `Done`. **Tres fuentes,
   tres respuestas.** Hubo que ir al `git log` a dirimirlo, y resolver el
   conflicto con `--theirs` a ciegas habría metido una regresión documental en
   `main` con el CI en verde.
3. Un PR escribió "sin tarea asignada" sobre unas vulnerabilidades y otro PR lo
   volvió falso media hora después; hizo falta un tercer PR solo para arreglarlo.

### La causa en el kit

`references/trabajo_en_equipo.md` lo prescribe explícitamente:

- Línea 98: *"`progreso/estado-actual.md` incluye la tabla de estado por módulo
  (espejo del tablero)."*
- Línea 182: *"`estado-actual.md` añade tabla de estado por módulo."*
- Línea 73: *"GitHub es la verdad para tareas; `tablero-equipo.md` queda como
  resumen rápido de módulos."*

Encadenado: Project (verdad) → tablero (resumen) → estado-actual (espejo del
resumen). **Un espejo de un espejo, ambos a mano.**

### El matiz que importa

No toda redundancia sobra. Que el estado esté **en el repo** y no solo en GitHub
tiene valor real: leer un fichero es local y gratis, consultar la API cuesta
llamada y autenticación, y el hook de arranque puede inyectar un fichero pero no
una query. Eso es redundancia que se paga sola.

La distinción correcta:

- **Repo ↔ GitHub**: útil. Arranque de contexto. Se mantiene.
- **`tablero` ↔ `estado-actual`**: ambos en el repo, ambos instantáneas del mismo
  hecho, ambos a mano. **Esta es la que sobra.**

Y la condición que lo decide todo: **la redundancia solo preserva contexto si las
copias coinciden. Cuando discrepan es peor que no tenerla**, porque quien lee no
tiene forma de saber cuál manda — y si elige mal, propaga la mentira con el CI
en verde.

### Corrección propuesta

Dos caminos, y **hay que tomar uno**; mantener dos instantáneas a mano y confiar
en la disciplina es lo que ya falló tres veces:

- **Preferido — generar:** la tabla del tablero se genera desde la API del
  Project. Si nadie la teclea, no puede desviarse. Encaja con la convención que
  el kit ya define de que los commits del tablero van directo a `main` por ser
  coordinación.
- **Mínimo — guardar:** extender `docs_check.py` para exigir que tablero y
  Project coincidan. Avisa *después* de romperlo, pero es barato.

En ambos casos, `estado-actual.md` **pierde su tabla de estado** y se queda con
lo que solo él tiene: decisiones vivas, deudas técnicas y convenciones que
cambiaron.

### Frontera que no se debe cruzar

**El log append-only del tablero se queda a mano y no se genera nunca.**

La tabla es un hecho mecánico; el log es causalidad — por qué una tarea se
atascó, qué trampa costó un intento fallido. En la sesión que originó estos
hallazgos, una nota de handoff sobre una fuga por la *status line* de un HTTP 401
evitó confiar en 36 tests en verde que no cubrían esa propiedad. **Ninguna
automatización habría escrito esa nota.**

Automatizar el espejo, jamás el porqué.

---

## Hallazgo 4 🟠 — El kit crea las condiciones para la deriva de ramas y no da mecanismo

**Estado: propuesto, no implementado.**

### Qué pasó

Un PR salió de su base el día 18 y se mergeó el 22, arrastrando **cuatro días de
deriva**. Resultado: cuatro conflictos, uno de ellos **no mecánico** — la rama
afirmaba un estado de tarea que ya era falso, y resolverlo con `--theirs` a
ciegas habría metido una regresión documental en `main` con el CI en verde.

Fue el mayor sumidero de tiempo de la sesión. El día 19 habría sido trivial.

### La causa en el kit

`trabajo_en_equipo.md` prescribe módulos reclamables trabajados **en paralelo**
por varios devs. Eso produce estructuralmente ramas de vida larga que divergen
entre sí — es una consecuencia del diseño, no un accidente.

El kit ya envía plantillas de CI (`plantillas/ci/`), pero **ninguna vigila esa
deriva**. Crea la condición y no da el instrumento.

Además, la opción nativa de GitHub (*"Require branches to be up to date before
merging"*) depende de protección de rama, que puede no estar disponible — ver
Hallazgo 5. De ahí que haga falta un workflow propio.

### Corrección propuesta

Plantilla de workflow programado que comente en PRs cuya base esté más de N
commits por detrás. Requisitos que importan más que el umbral:

- **Un aviso por PR, no uno por ejecución.** Si spamea, se filtra y deja de leerse.
- Umbral configurable: el número correcto depende del ritmo del equipo.

---

## Hallazgo 5 🔴 — El kit declara la regla de revisión sin decir cómo se aplica (ni que puede ser inaplicable)

**Estado: propuesto, no implementado. Es el caso más puro del patrón.**

### Qué pasó

En la sesión se mergearon **ocho PRs sin la revisión de otro dev** que la regla
exige. Ningún mecanismo lo impidió ni lo señaló. Eran documentación y fueron
pedidos explícitamente por el lead, así que no hubo daño — pero el próximo PR con
código entra por el mismo hueco.

### La causa en el kit

`trabajo_en_equipo.md` declara las dos reglas de forma tajante:

- Línea 152: *"**Nadie hace push directo a main.** Todo entra por Pull Request."*
- Línea 156: *"**Todo PR requiere >=1 revisión humana de otro dev.**"*

Y **en ningún punto del kit** se menciona la protección de rama, cómo
configurarla, ni —lo más importante— que **no está disponible en repos privados
con plan Free**. Verificado por búsqueda en todo el documento.

El resultado es una regla que el equipo cree activa y que en realidad no lo está.
**Una regla escrita que no se cumple es peor que no tenerla**: da sensación de
control y desgasta la credibilidad del resto del documento.

Este hallazgo es el patrón en estado puro: no es que el mecanismo falle, es que
**nunca se planteó que hiciera falta uno**.

### Corrección propuesta

El kit no puede decidir por el equipo —las tres salidas tienen coste distinto—
pero sí debe **forzar la decisión** en vez de dejar la regla flotando:

1. **GitHub Pro** — habilita protección en repos privados. Cuesta dinero.
2. **Repo público** — protección gratis. Exige revisar el histórico.
3. **Ajustar la regla** a lo que de verdad se hace (p. ej. revisión obligatoria
   solo en PRs con código).

Concretamente, en `trabajo_en_equipo.md`:

- Añadir el paso de configurar la protección de rama al montar el repo, con la
  **advertencia explícita** de la limitación del plan Free.
- Si no se puede activar, que el kit obligue a **registrar la excepción**
  (en el `CLAUDE.md` generado) en lugar de dejar escrita una regla inaplicable.
- Contemplar la excepción que el propio kit ya define: los commits de
  coordinación del tablero van directo a `main` por diseño, así que cualquier
  protección debe permitirlos.

---

## Límite general: qué NO debe automatizar el kit

Los cinco hallazgos empujan en la misma dirección —poner mecanismo donde solo hay
texto—, así que conviene dejar escrito dónde para ese impulso.

**No se automatizan handoffs, ADRs ni el log del tablero.** Son juicio, no
estado. Un generador produciría texto plausible y vacío, y se perdería justo lo
que hoy funciona mejor del kit.

El criterio para distinguirlos:

| Se puede generar | No se genera nunca |
|---|---|
| Estado de una tarea | Por qué se atascó |
| Qué ficheros cambiaron | Qué trampa costó un intento fallido |
| Si los tests pasan | Qué NO prueban los tests |

La última fila es la que más pesa. En la sesión que originó estos hallazgos, una
nota de handoff advertía de que la suite comparaba solo el cuerpo JSON de una
respuesta HTTP mientras la *status line* seguía filtrando información. Gracias a
ella se verificó la propiedad a mano en vez de confiar en 36 tests en verde.

**Ninguna automatización habría escrito esa advertencia**, porque nace de un
intento fallido, no del estado del repo. Automatizar el espejo; jamás el porqué.

---

## Hallazgo 6 🔴 — El kit trata los falsos éxitos como anécdotas sueltas

**Estado: corregido en este PR.**

### Qué pasó

Un comando para actualizar la descripción de un PR reportó `PR #2 actualizado`.
**Era falso en lo que importaba**: el script previo había muerto, el fichero
nunca se modificó y `gh` reaplicó la descripción antigua. Se detectó solo porque
después se releyó el contenido del PR.

Tres fallos encadenados, cada uno inocuo por separado:

1. **Rutas.** Un intérprete nativo recibió una ruta del shell POSIX (`/tmp/x`) y
   la resolvió contra otro mapa del disco. El shell abría ese fichero sin
   problema; el intérprete no.
2. **Propagación.** Los dos comandos estaban en líneas separadas. Un salto de
   línea es `;`, **no propaga el fallo**: el segundo corrió igual y el exit final
   fue 0.
3. **Verificación.** El `&&` unía el segundo comando con el mensaje de éxito, y
   ese comando sí funcionó — solo que sobre datos viejos. El mensaje era
   técnicamente cierto y prácticamente falso.

### La causa en el kit

El kit **ya sabe** que esta clase de problema existe, pero la trata como
anécdotas dispersas, cada una en la skill donde alguien tropezó:

- `cerrar-sesion.SKILL.md:42` — *"si los hooks corren en contenedor, usar timeout largo"*
- `cerrar-sesion.SKILL.md:43` — *"`--body-file`, nunca body inline multilínea en PowerShell — se corrompe"*
- `que-toca.SKILL.md:58` — *"lanzar desde el tool Bash, no PowerShell — las comillas se pierden"*

Tres síntomas del mismo mecanismo, sin nombre común y sin la regla que los une.
Quien lea una de ellas aprende a esquivar **ese** caso concreto, no la clase.

Y lo más revelador: `verificar.SKILL.md` —la skill cuyo trabajo entero es
*"demostrar que un cambio funciona DE VERDAD"*— **no cubría el caso**. Su
sección "Qué NO es verificar" hablaba de mocks y happy paths, pero no de que un
comando con exit 0 no demuestra nada sobre el objetivo.

### Corrección aplicada

1. **`verificar.SKILL.md`** — la regla que unifica todo: *verifica el efecto, no
   la invocación*, con la taxonomía de los tres casos reales de la sesión (CI en
   verde con `continue-on-error`, tests que comparaban solo el JSON, `gh` con
   contenido viejo). En los tres el paso hizo su trabajo y el resultado era
   falso, porque **lo comprobado no era lo que importaba**. Se añaden las tres
   trampas de shell que producen exactamente esto.
2. **`plantillas/CLAUDE-fragmento.md`** — versión densa (6 líneas) en el contexto
   permanente de cada proyecto. Va aquí y no solo en la skill porque el fallo
   ocurre **mientras se ejecutan comandos**, no cuando alguien decide verificar:
   si solo vive en `verificar`, se lee después de haberlo cometido.
3. **`{{CMD_CONVERTIR_RUTA}}`** añadido a la tabla de placeholders del README —
   la conversión de rutas depende de la plataforma.

### El criterio de fondo

Un reporte de "hecho" debe apoyarse en algo **observado**. Un comando sin error
no es una observación: es una ausencia de queja. La diferencia entre las dos
cosas es todo este hallazgo.
