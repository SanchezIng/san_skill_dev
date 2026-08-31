---
name: equipo-cerrar-sesion
description: Checklist ejecutable de cierre de sesión/tarea del equipo. Úsala SIEMPRE que el dev diga "cierra la sesión", "cerremos", "termina la tarea", "haz el cierre", o cuando una subfase/tarea quede completa, o antes de abandonar una sesión larga. Verifica tests y calidad, commitea, mete el cierre documental EN el PR de la tarea y mueve el item del Project. Se NIEGA a cerrar con tests rojos.
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

La suite **COMPLETA**, una sola vez, antes de abrir o actualizar el PR. Si el
proyecto tiene un modo rápido enganchado al `git push`, lo que ese modo omite no
se perdona: se aplaza y se paga aquí. Empujar varias veces por cierre y pagar la
suite entera en cada push es el grueso de la lentitud que este paso evita.

**No pongas la rama al día para que te revisen.** Al día hace falta para
**mergear**, no antes: se revisa el diff contra su base. Perseguir a la rama base
mientras esperas review reinicia la verificación, y mientras tanto la base se
vuelve a mover: es una carrera que no se gana, y encima invalida la review que ya
te hicieron. Rebase al final, una vez.

- Tests rojos → arreglar antes de seguir (o declarar el bloqueo, ver regla dura).
- Si el cambio toca {{AREAS_CRITICAS}}: correr también `/verificar` (smoke E2E real).

**ROJO PRIMERO.** Si algún test de esta sesión cierra un bug, tienes que haberlo
visto **fallar** contra el código sin arreglar, y pegas esa salida roja en el PR.
Un test verde no demuestra que guarde nada: en el proyecto piloto aparecieron dos
que se creían protección y no lo eran (uno con 2 de 3 casos que seguían verdes al
mutar la implementación; un E2E que pasaba igual con el bug reintroducido). Un
test que nunca se vio rojo convierte "sin probar" en "creído probado".

**Si tocaste una frontera compartida**, antes de dar por buenas las docs: busca
dónde se **ENSEÑA** ese símbolo, no solo dónde se usa. El compilador vigila el
código; la prosa no la vigila nadie, y en el piloto cambiar una función de acceso
a datos dejó nueve documentos enseñando el camino viejo.

**Checkpoint de seguridad — proporcional, no un muro al final.**

La seguridad se mira **mientras se escribe el código**, y para eso está el hook
`PreToolUse`, que la recuerda en cada edición. Aquí, al cerrar, ya no se rehace:
revisar al final es cuando corregir cuesta lo máximo, y los devs reportaron
justo eso — *"cuando terminé la tarea hizo revisión y me mandó a corregir lo
que ya estaba hecho"*. Una red que llega tarde no protege más: solo cuesta más.

- **Si el cambio toca una zona sensible** —{{AREAS_CRITICAS}}, o donde vivan la
  autenticación y el acceso a datos— **y `secure-coding-guard` no se aplicó:
  aplícala ahora.** Aquí sí para el cierre: el coste de encontrarlo después es
  mayor que el de rehacerlo hoy.
- **En cualquier otro caso, no la rehagas: decláralo.** Una línea en el PR —
  `secure-coding-guard: aplicada` / `no aplicada` — y el revisor decide si mirar
  con lupa. Ocultarlo sería lo grave; llegar tarde a rehacerlo, solo caro.

No des por hecho que ya se hizo: la skill se salta con facilidad cuando el
trabajo **no entró por `/que-toca`** — mergear un PR aprobado, resolver
conflictos, revisar código ajeno, un hotfix, o retomar tras una pausa. Por eso
se declara siempre, aunque solo se rehaga en las zonas sensibles.

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

## Paso 3 — El cierre documental va EN ESTE PR

1. **Pregúntate qué prosa deja caducada tu merge** —hoja de ruta, backlog, handoffs
   de otros, pendientes— y actualízala **en el MISMO PR**. El «PR de cierre de DoD
   post-merge» no existe: en el piloto hubo seis en dos días, cada uno con su rama,
   su review y su merge, solo para arreglar documentación que el PR original pudo
   dejar bien — la mitad del tráfico de proceso de esa jornada. Post-merge quedan
   solo los gestos que no existen antes del merge: tag si toca, tarjeta, desbloqueos.
2. Lo demás es **OPCIONAL, no ritual**:
   - Una decisión que afecta a quien venga detrás → un fichero **nuevo** en
     `progreso/decisiones/`. Una deuda o trampa con contexto → `progreso/pendientes/`.
     Nunca editar los existentes: **fichero por item = conflictos imposibles.**
   - **Handoff** `progreso/fase-{n}.{m}-{modulo}.md` **solo si dejas el módulo a
     medias** o con trampas que contar. Módulo terminado y limpio = sin handoff:
     el issue y el PR ya cuentan la historia.
   - `progreso/estado-actual.md` casi nunca se toca: solo si cambió algo estable
     (una fase entera, una trampa de arranque nueva). **No lleva tabla de estado
     por módulo** ni decisiones sueltas: eso vive en el Project y en los ficheros
     de arriba. Tenerlo todo aquí lo convertía en el archivo que tocaban TODAS las
     ramas, y por tanto en el segundo motivo estructural de conflicto tras el
     tablero.
3. **Un TODO que sobrevive a la subfase se convierte en issue SOLO si es
   obligatorio o si bloquea de verdad a alguien** (paso 4.2). Dos filtros:

   - **¿Gatea o bloquea trabajo de otro?** → issue. Y escríbelo en el
     `Depende de:` de la tarea que gatea, que es donde se va a leer.
   - **¿Es obligatorio aunque hoy no bloquee?** —lo exige el contrato con el
     negocio, una guarda de CI, una norma de seguridad— → issue.
   - **Ninguna de las dos** → es **contexto, no trabajo**: `progreso/pendientes/`
     si es una deuda o una trampa, `progreso/decisiones/` si es una decisión. Ahí
     se queda, y no ocupa una columna del tablero.

   «Alguien debería mirar esto» no es lo mismo que «esto es trabajo reclamable».
   Un issue es la promesa de que alguien lo va a coger; una duda anotada, no.

   > **Esto acota la regla anterior, no la anula.** Antes aquí ponía que *«un
   > pendiente sin issue es invisible para `/que-toca`»*, y sigue siendo verdad —
   > por eso lo que SÍ pasa los filtros tiene que acabar en el Project, con los
   > tres pasos del 4.2. Pero se leyó como «ante la duda, abre issue», y el
   > péndulo se fue al otro extremo: ver el caso real del paso 4.2.

## Paso 4 — Tablero y Project

1. **El estado real se mueve en el Project** (IDs en `/que-toca`): a **Review** al
   abrir el PR; a **Terminado** al mergear **el ÚLTIMO PR de la tarea**. Poner en
   **Disponible** los items cuyas dependencias quedaron cumplidas ("Depende de" en
   cada issue). Esto es lo que ve el equipo y lo que leen las skills: hazlo aunque no
   toques el tablero.

   **Si este cierre deja trabajo post-merge, la tarjeta se queda en Review.** Handoff,
   entrada de log o cierre de documentación en un PR aparte cuentan: mientras quede
   uno abierto, la tarea no está Terminada. Y en el otro sentido, **cerrar el issue
   no es mergear el PR**: son dos gestos y el primero no implica el segundo.

   > **Por qué, si el trabajo "ya está hecho":** el Project sigue *issues*, no PRs —
   > los items son los issues del repo, ninguno es un PR. Un PR esperando revisión
   > **no sale en la columna de nadie**, así que en cuanto mueves la tarjeta a
   > Terminado ese PR se vuelve invisible y se para sin que nadie sea culpable (en el
   > piloto, un día parado). Al revés muerde peor: un issue cerrado con su PR sin
   > mergear es el tablero diciendo «hecho» con el código fuera de la rama principal —
   > y si le pasa a una tarea de seguridad, el equipo cree tener desplegada una
   > mitigación que no existe.
   >
   > Sí, la columna Review se alarga. Es el precio, y es justo lo que quieres ver.
2. **Los issues que abras en este cierre también van al Project — crearlos no basta.**
   `gh issue create` no los añade: se quedan en Issues, invisibles para el tablero y
   para `/que-toca`, que busca tareas Disponibles **en el Project**. Son tres pasos, y
   los dos últimos se olvidan porque `item-add` no protesta: no imprime nada y deja el
   `Status` en **`null`**, y un item sin estado no cae en ninguna columna.

   ```bash
   gh project item-add {{PROJECT_NUMBER}} --owner {{OWNER}} --url <url-del-issue>

   gh issue edit <N> --add-label "modulo:<X>"   # si el tablero saca el modulo de una
                                                # LABEL, no lo deduce del titulo

   # item-add NO devuelve el id del item; hay que buscarlo por el numero de issue:
   ITEM_ID=$(gh project item-list {{PROJECT_NUMBER}} --owner {{OWNER}} --format json --limit 500 \
     --jq ".items[]|select(.content.number==<N>)|.id")
   python3 scripts/tablero.py --mover "$ITEM_ID" "Disponible"   # o "Bloqueada" si algo la frena
   ```

   Si además es una **tarea** (no un aviso al equipo), su entrada en el backlog con
   `T-nnn`, módulo, `Depende de:` y criterios de aceptación — y que el título del issue
   empiece por `T-nnn ·`, o el tablero lo muestra sin número y no se puede cruzar con
   el backlog.

   **`Disponible` significa «reclamable AHORA», y afirmarlo es trabajo, no un
   vistazo.** Antes de poner una tarjeta ahí, haz las tres cosas — las tres, no la
   primera:

   1. **Mira de qué depende.** Si espera a otra tarea, o a un PR que aún no está
      mergeado, va a **`Bloqueada`**. Una tarea que en realidad espera le cuesta
      una sesión entera al que la coja: ramifica de un `main` que no tiene el
      código sobre el que iba a construir.
   2. **Mira a quién desbloquea**, y escríbelo en el `Depende de:` de **esa** otra
      tarjeta. El análisis que no acaba escrito no lo hereda nadie: lo repite el
      siguiente, o no lo hace.
   3. **Mira qué queda en `Disponible` al terminar.** Si son todo avisos y
      decisiones, el tablero no ofrece trabajo aunque parezca lleno.

   > **Caso real (2026-08-31, FARMICROW).** Al cerrar dos subfases quedaron **7
   > items en `Disponible` y ni una sola tarea `T-nnn`**: todos eran decisiones
   > («¿merece ADR propio?», «¿qué versión de pnpm manda?») y vigilancias
   > («postcss sin fix aguas arriba»). Como `/que-toca` elige la de **menor
   > número**, al siguiente dev le tocaba *vigilar postcss* — un aviso sin nada
   > que hacer hasta que arreglaran upstream. Y en el mismo tablero, una tarjeta
   > estaba en `Disponible` dependiendo de un PR todavía abierto.
   >
   > El mismo cierre dejó **3 pendientes sin issue** mientras otros sí lo tenían.
   > O sea: no sobraban issues ni faltaban — **cuál se convertía en issue salía
   > arbitrario**, porque no había filtro. De ahí los dos del paso 3.3.

   > Caso real anterior, por el otro lado: seis issues abiertos de tres personas
   > estaban fuera del Project, incluidas una deuda de RLS y el rate limiting de
   > OWASP A04. Ninguna era reclamable. Los dos fallos son opuestos y `/que-toca`
   > (pasos 2-3, vía `scripts/estado.py`) lleva ya la comprobación de ambos.

3. **El tablero NO se comitea** (está en `.gitignore`): es un espejo del Project y ya
   quedó actualizado con los puntos 1 y 2. Regenéralo cuando quieras verlo:

   ```bash
   python3 scripts/tablero.py --generar   # tabla + log ensamblado, solo en local
   ```

   ⛔ **Regenerarlo es gratis; ABRIRLO no.** El fichero crece con el Project: en un
   proyecto real de ~90 tareas pesaba **~40.700 tokens**, el 20% de una ventana de
   200k. Es para leerlo una persona; el estado que necesitas para cerrar ya lo
   tienes de los puntos 1 y 2. Por eso `--generar` imprime su peso al terminar.

4. **Entrada de log: OPCIONAL.** Solo si hay algo que el Project no pueda contar —
   por qué se atascó, qué trampa costó un intento fallido, qué acuerdo se tomó. Un
   cierre normal NO lleva entrada de log: `git log` y el PR ya lo cuentan.

   ```bash
   cat > progreso/log/$(date +%F)-pr-N-t-nnn.md <<'EOF'
   YYYY-MM-DD {dev} abre PR #N (T-nnn/#issue) — {lo que el Project no cuenta}
   EOF
   ```

   **Si la escribes: un fichero nuevo, nunca editar los existentes.** Así dos ramas
   que escriben a la vez no pueden conflictar. Va **en la rama, dentro del PR** — es
   contexto, no estado, así que no justifica saltarse la protección de la rama
   principal.

> **Excepción — proyecto SIN GitHub Project:** el tablero es el único registro, la
> tabla se mantiene a mano (no hay de dónde generarla) y sí va directo a `main`
> (`git checkout main && git pull` → editar → commit → push), volviendo después a la
> rama de trabajo. En ese modo `main` no puede estar protegida del todo.
> Ver `trabajo_en_equipo.md` §9.

## Paso 5 — Reporte final al dev

Resumen con: qué se entregó (PR + CI), qué queda pendiente (review humana, deploy,
migraciones, rebuild de imagen si cambió), y cualquier decisión que
haya quedado registrada (ADR nuevo, tarea nueva en backlog).
