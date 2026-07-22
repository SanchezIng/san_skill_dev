# Hallazgos de uso real — 2026-07-22

> Origen: sesión de trabajo en `portal-web-api-sunat`, un proyecto instalado con
> este kit. Los tres hallazgos son **fallos de diseño del kit**, no del proyecto:
> se reproducen en cualquier repo que lo instale.
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
