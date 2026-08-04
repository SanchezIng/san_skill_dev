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
> **Todo entra por PR, sin excepciones.** El reclamo de una tarea sí debe verse al
> instante, y por eso el candado vive en GitHub (assignee + estado del Project):
> es atómico y visible al segundo, sin necesidad de empujar nada. Así `main` puede
> estar protegida al 100%.
>
> **El tablero (`progreso/tablero-equipo.md`) NO se comitea** — está en
> `.gitignore`. Es un espejo del Project y se regenera cuando lo quieras ver con
> `python3 scripts/tablero.py --generar`, que ensambla la tabla **y** el log.
>
> **El log sí se comitea, en `progreso/log/`, UN FICHERO POR ENTRADA.** Nunca se
> edita una entrada existente: se crea una nueva. Así dos ramas que escriben a la
> vez no pueden conflictar — que es exactamente lo que pasaba antes, cuando tabla
> y log compartían archivo y ese archivo lo tocaba toda rama (en el piloto: 3 PRs
> abiertos, los 3 conflictando ahí el mismo día).
>
> Estado → se genera. Por qué se atascó algo → lo escribes tú, en su propio fichero.
>
> *(Si este proyecto NO usa GitHub Project, el tablero es el candado, hay que
> sacarlo del `.gitignore` y sí va directo a `main`; entonces `main` no puede
> protegerse del todo. Un modo u otro, no ambos.)*

## 📜 Reglas del sistema de conocimiento

- **Regla de densidad:** este CLAUDE.md solo gana líneas si otro archivo las pierde
  — es un MAPA, no una enciclopedia. Lo que madure baja a `docs/` y deja un puntero.
  Se lee entero en cada sesión: cada línea de más es contexto que se paga siempre.
- **El porqué en el punto de uso:** toda decisión no-obvia en código referencia su
  issue o ADR en el comentario (`T-nnn/ADR-nnnn`). Regla de PR. Es la diferencia
  entre leer una función y adivinar, o saltar directo a la historia completa.
- **Deriva vigilada:** el CI falla si la documentación referencia archivos
  inexistentes o si una tarea del backlog apunta a un issue que no existe (y, si
  el backlog conserva `Estado:`, si marca `Done` una tarea con issue abierto).
  El rigor lo fija `MODO_BACKLOG` en `scripts/docs_check.py`; la guarda se prueba
  a sí misma en CI (`scripts/test_docs_check.py`) antes de juzgar el repo.
- **Rotación:** el log ya no necesita archivarse (un fichero por entrada en
  `progreso/log/`; crecer no estorba a nadie). Entradas viejas de "actualización
  previa" del estado → histórico.
- **Antes de cambiar una frontera, mira dónde se ENSEÑA**, no solo dónde se usa.
  El compilador vigila el código; la prosa no la vigila nadie, y en el piloto
  cambiar una función de acceso a datos dejó nueve documentos enseñando el camino
  viejo — el peor de ellos no estaba en la lista de nadie.
- **Una sola fuente de verdad:** el conocimiento compartido vive en el repo
  (versionado, revisado por PR). Nada de wikis paralelas ni memorias externas
  para lo que el equipo debe compartir.

## ⚙️ Ejecución: no confundir éxito de la herramienta con éxito de la tarea

- **Exit 0 significa "la herramienta funcionó", no "conseguí lo que quería".**
  Antes de escribir "hecho", pregúntate qué observaste que lo demuestre; si la
  respuesta es "el comando no dio error", no está verificado. Relee el efecto.
- **Un salto de línea NO propaga el fallo:** el paso siguiente corre igual y el
  exit final puede ser 0. Multi-paso → `set -euo pipefail` o encadenar con `&&`.
- **Shell POSIX y binarios nativos no comparten mapa del disco:** una ruta válida
  para el shell puede no serlo para el intérprete. Convertir con
  `{{CMD_CONVERTIR_RUTA}}` antes de pasarla.
- **Toda lista viene con tope y no avisa** (`gh` trae 30 por defecto). Si vas a
  concluir "no hay ninguno" o "está libre", pide más de lo que esperas y mira si
  te devolvieron exactamente el límite: entonces hay más y no los estás viendo.

## 🗂️ Dónde vive cada cosa

| Tipo de conocimiento | Dónde | Vida útil |
|---|---|---|
| Decisiones de arquitectura (con alternativas descartadas) | `docs/adr/` | Largo plazo |
| Bugs y tareas (contexto, alcance, resolución) | `docs/backlog.md` + Issues | Mediano |
| Cronología del equipo (quién, qué, cuándo) | `progreso/log/` (un fichero por entrada) | Mediano |
| Foto del presente | Project + `progreso/decisiones/` y `pendientes/` | Un fichero por item: se añade, no se reescribe |
| Contexto para retomar un módulo (TODOs, trampas) | handoffs | Corto: se consume al retomar |
| Reglas y rumbo global | `CLAUDE.md` + especificaciones | Largo plazo |
