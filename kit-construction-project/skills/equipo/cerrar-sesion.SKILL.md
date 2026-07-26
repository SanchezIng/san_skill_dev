---
name: equipo-cerrar-sesion
description: Checklist ejecutable de cierre de sesión/tarea del equipo. Úsala SIEMPRE que el dev diga "cierra la sesión", "cerremos", "termina la tarea", "haz el cierre", o cuando una subfase/tarea quede completa, o antes de abandonar una sesión larga. Verifica tests y calidad, commitea, actualiza estado-actual + handoff + tablero, abre/actualiza el PR y mueve el item del Project. Se NIEGA a cerrar con tests rojos.
---

# /cerrar-sesion — Cierre disciplinado

El cierre es lo que mantiene viva la memoria del proyecto: el siguiente dev (o tu
siguiente sesión) arranca de lo que dejes escrito AQUÍ. Ejecuta los pasos en orden.

**Regla dura: si los tests fallan, NO se cierra.** Se arreglan, o se documenta el
fallo como bloqueo explícito en el handoff y se avisa al dev — nunca cierre silencioso.

## Paso 1 — Verificación (gate)

```bash
{{CMD_TEST}}   # suite completa
{{CMD_LINT}}          # lint
{{CMD_ESTATICO}}
```

- Tests rojos → arreglar antes de seguir (o declarar el bloqueo, ver regla dura).
- Si el cambio toca {{AREAS_CRITICAS}}: correr también `/verificar` (smoke E2E real).

**Checkpoint de seguridad (segunda red).** Si la sesión tocó código y
**`secure-coding-guard` no se aplicó**, aplícala AHORA antes de cerrar, y anota
su resumen (qué se aseguró, hallazgos por severidad, pendientes) en el handoff.

No des por hecho que ya se hizo: la skill se salta con facilidad cuando el
trabajo **no entró por `/que-toca`** — mergear un PR aprobado, resolver
conflictos, revisar código ajeno, un hotfix, o retomar tras una pausa. En esos
casos nadie pasó por el paso que la exige. Haber hecho comprobaciones de
seguridad sueltas sobre la marcha **no cuenta como haberla aplicado**: sus
`references/` existen para no depender de qué se le ocurra mirar a quien esté
al mando.

## Paso 2 — Commit y PR

1. Stage **explícito** de los archivos de la tarea (nunca `git add -A`: puede arrastrar
   basura de herramientas o carpetas ajenas sin trackear).
2. Conventional Commit con módulo en el scope: `feat(B): ...`, `fix(A): ...`, `dx: ...`.
   Si los hooks de pre-commit corren en contenedor, el commit tarda: usar timeout largo.
3. Push de la rama y PR con `gh pr create` usando `--body-file` (nunca body inline
   multilínea en PowerShell — se corrompe). El body debe incluir `Resolves #N`
   (keyword EN INGLÉS — "Cierra #N" no cierra el issue) y terminar con la firma
   de Claude Code. PRs < ~400 líneas de diff; subfase grande = varios PRs.
4. Si el PR toca algún archivo de la lista "no tocar sin avisar" del CLAUDE.md
   (imagen/contenedores, workflows de CI, fronteras entre módulos) → destacarlo en el body.

## Paso 3 — Documentar el estado

1. **`progreso/estado-actual.md`**: actualizar la fila del módulo y, si el hito lo
   amerita, la cabecera de "Última actualización".
2. **Handoff** `progreso/fase-{n}.{m}-{modulo}.md` (o el del área): qué quedó hecho,
   qué quedó a medias, **trampas descubiertas**, y el siguiente paso concreto.
   TODOs pendientes → SIEMPRE al handoff (y si sobreviven a la subfase → abrir issue).
3. Estos dos archivos van **en el PR** (documentan el cambio), no directo a main.

## Paso 4 — Tablero y Project

1. **El estado real se mueve en el Project** (IDs en `/que-toca`): a **Review** al
   abrir el PR; a **Terminado** al mergear. Poner en **Disponible** los items cuyas
   dependencias quedaron cumplidas ("Depende de" en cada issue). Esto es lo que ve el
   equipo y lo que leen las skills: hazlo aunque no toques el tablero.
2. `progreso/tablero-equipo.md`: fila del módulo + línea de log
   (`- YYYY-MM-DD {dev} abre PR #N (T-nnn/#issue) — {resumen}`). Va **en la rama de la
   tarea, dentro del PR** — es un resumen del Project, no una fuente de verdad, así que
   no justifica saltarse la protección de `main`.

> **Excepción — proyecto SIN GitHub Project:** el tablero es el único registro y sí va
> directo a `main` (`git checkout main && git pull` → editar → commit → push), volviendo
> después a la rama de trabajo. En ese modo `main` no puede estar protegida del todo.
> Ver `trabajo_en_equipo.md` §9.

## Paso 5 — Reporte final al dev

Resumen con: qué se entregó (PR + CI), qué queda pendiente (review humana, deploy,
migraciones, rebuild de imagen si cambió), y cualquier decisión que
haya quedado registrada (ADR nuevo, tarea nueva en backlog).
