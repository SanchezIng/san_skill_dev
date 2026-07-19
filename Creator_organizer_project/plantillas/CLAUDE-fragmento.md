<!--
  Pegar este bloque en el CLAUDE.md del proyecto generado.
  Son las reglas que mantienen VIVO el sistema de conocimiento: sin ellas, la
  documentación se degrada hasta mentir, y un doc que miente envenena a humanos
  y LLMs con confianza falsa.
-->

## 🤖 Protocolo de equipo (ejecutable)

> El protocolo NO es texto que recordar: son skills. **`/que-toca`** reclama tarea
> (candado en GitHub + espejo en el tablero), **`/cerrar-sesion`** cierra
> (tests → commit → PR → handoff → tablero → Project) y **`/verificar`** demuestra
> que el cambio funciona de verdad. Un hook `SessionStart` inyecta contexto de
> orientación al arrancar. Lo de abajo queda como referencia de lo que hacen.
>
> **Excepción al "todo por PR":** los commits de coordinación del tablero
> (`progreso/tablero-equipo.md`) van directo a `main` — son coordinación, no código;
> el reclamo de una tarea debe verse al instante. Todo lo demás entra por PR.

## 📜 Reglas del sistema de conocimiento

- **Regla de densidad:** este CLAUDE.md solo gana líneas si otro archivo las pierde
  — es un MAPA, no una enciclopedia. Lo que madure baja a `docs/` y deja un puntero.
  Se lee entero en cada sesión: cada línea de más es contexto que se paga siempre.
- **El porqué en el punto de uso:** toda decisión no-obvia en código referencia su
  issue o ADR en el comentario (`T-nnn/ADR-nnnn`). Regla de PR. Es la diferencia
  entre leer una función y adivinar, o saltar directo a la historia completa.
- **Deriva vigilada:** el CI falla si la documentación referencia archivos
  inexistentes o si el backlog marca `Done` una tarea con issue abierto.
- **Rotación:** log del tablero > ~400 líneas → archivar por periodo; entradas
  viejas de "actualización previa" del estado → histórico.
- **Una sola fuente de verdad:** el conocimiento compartido vive en el repo
  (versionado, revisado por PR). Nada de wikis paralelas ni memorias externas
  para lo que el equipo debe compartir.

## 🗂️ Dónde vive cada cosa

| Tipo de conocimiento | Dónde | Vida útil |
|---|---|---|
| Decisiones de arquitectura (con alternativas descartadas) | `docs/adr/` | Largo plazo |
| Bugs y tareas (contexto, alcance, resolución) | `docs/backlog.md` + Issues | Mediano |
| Cronología del equipo (quién, qué, cuándo) | log del tablero | Mediano |
| Foto del presente | `progreso/estado-actual.md` | Se sobrescribe |
| Contexto para retomar un módulo (TODOs, trampas) | handoffs | Corto: se consume al retomar |
| Reglas y rumbo global | `CLAUDE.md` + especificaciones | Largo plazo |
