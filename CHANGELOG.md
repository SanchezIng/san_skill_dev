# Changelog

Cambios del catálogo. Cada entrada dice **qué se rompía**, no solo qué se tocó:
un changelog que solo lista archivos no evita repetir el error.

## 2026-07-25 — Los mecanismos del kit pasan a estar verificados

Se integran los PRs #1 y #2 (`kit-construction-project`), corrigiendo antes seis
defectos que se detectaron **ejecutándolos**, no leyéndolos.

### `secure-coding-guard` deja de depender de `/que-toca` (PR #2)

La obligación de la skill solo se ejecutaba en el paso 6.4 de `/que-toca`. Todo
trabajo que entra por otra puerta —mergear un PR, resolver conflictos, revisar
código ajeno, un hotfix, retomar tras una pausa— la saltaba en silencio.
Corrección en dos capas: hook `PreToolUse` al tocar código, y checkpoint en
`/cerrar-sesion` por si el hook se ignoró.

- **El hook de la propuesta original no funcionaba.** Leía la ruta de una
  variable de entorno inexistente (`CLAUDE_TOOL_FILE_PATH`) y escribía por
  stdout plano, que en `PreToolUse` va solo al log de depuración. Hacía
  `exit 0` en la primera línea **siempre**: se ejecutaba en cada edición sin
  hacer nada, dando el hallazgo por cerrado.
  El contrato real es: la ruta llega en el **JSON de stdin**
  (`.tool_input.file_path`, o `.tool_input.notebook_path` en `NotebookEdit`), y
  el aviso debe salir como `hookSpecificOutput.additionalContext`.
- **`NotebookEdit` no estaba cubierto** (usa `notebook_path`, no `file_path`).
- **Sin `jq`:** Git Bash en Windows no lo trae; la extracción es con `sed`.
- **El hook vivía dentro de la rama `--protocolo` del instalador**, pero
  `secure-coding-guard` se instala siempre: un proyecto en modo fábrica se
  quedaba con la skill y sin recordatorio. El hook pertenece al guardián, no al
  protocolo de equipo → se movió al bloque que corre siempre.
- **Límite conocido, documentado:** cubre `Edit|Write|NotebookEdit`. Un merge
  resuelto solo con comandos git (`git checkout --theirs`) mete código sin pasar
  por ninguna de esas herramientas; ahí la red es el checkpoint de
  `/cerrar-sesion`.

Los hallazgos de uso real salen de la carpeta del kit (viajaban a cada proyecto
instalado dentro de `SKILLS-PORTABLE/`) a [`hallazgos/`](hallazgos/) en la raíz.

### El estado del backlog vive en el Project (PR #1)

El campo `Estado:` del backlog se desfasa porque ningún automatismo lo lee: al
espejar a GitHub, el estado pasa a vivir solo en el Project. Sobre la propuesta
original se corrigieron tres falsos positivos que habrían tumbado el CI de
proyectos sanos:

| Escenario | Antes | Ahora |
|---|---|---|
| Espejado a medias (issues creados uno a uno) | CI rojo en mitad del arranque | `MODO_BACKLOG` explícito: `auto` valida lo verificable y **avisa** del resto; `espejado` es el modo estricto |
| Repo con >300 issues | acusaba de inexistentes los issues **más viejos** (las primeras tareas) | límite a 1000 + confirmación individual contra la API antes de acusar |
| Ejemplo de formato en un bloque de código | contaba como tarea real | se reutiliza el filtro de fences de la revisión de enlaces |
| `{{RUTA_BACKLOG}}` sin rellenar | traceback de Python en CI | mensaje accionable |

También se corrigió la incoherencia de `trabajo_en_equipo.md` §6: el bloque de
formato canónico seguía mostrando `- Estado:` justo encima del texto que manda
quitarlo, así que el kickstart generaba backlogs en modo legado por defecto.

### Los mecanismos ahora llevan tests

Convención nueva del catálogo: **un mecanismo que nunca se ha visto fallar no
está verificado.** Cada guarda se prueba en los dos sentidos —que deja pasar lo
correcto y que **muerde** lo incorrecto— y los tests viajan con el mecanismo al
proyecto instalado.

| Suite | Casos | Contra la versión sin corregir |
|---|---|---|
| `plantillas/ci/test_docs_check.py` (corre en CI **antes** de que la guarda juzgue el repo) | 12/12 OK | 7 fallos |
| `plantillas/hooks/test_recordar-seguridad.sh` (se instala en el proyecto) | 9/9 OK | 4 fallos |

Verificación del **efecto**, no de la invocación: una edición real vía
`claude -p` sobre un proyecto instalado por `instalar.sh` mete el aviso 2 veces
en el contexto del modelo (una como `hook_additional_context`). Con la versión
anterior: 0.

### Pendiente

Los hallazgos **2–5** siguen documentados sin implementar en
[`hallazgos/2026-07-22-aplicacion-de-reglas.md`](hallazgos/2026-07-22-aplicacion-de-reglas.md):
allowlist caducable para `npm audit`, el espejo del espejo del tablero, la
deriva de ramas largas, y la protección de rama (con la trampa de que **no
existe en repos privados con plan Free**). Los cuatro comparten el patrón que
originó todo esto: *regla declarada sin mecanismo que la aplique*.
