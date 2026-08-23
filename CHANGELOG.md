# Changelog

Cambios del catálogo. Cada entrada dice **qué se rompía**, no solo qué se tocó:
un changelog que solo lista archivos no evita repetir el error.

## 2026-08-22 — La guarda de cierres decía «OK» justo sobre lo que venía a cazar

Quinto retorno proyecto→kit. Arreglo de `pr_body_check.py` y su suite (15 → 26 casos).

**Qué se rompía.** La guarda exigía el `#N` **pegado** al verbo de cierre. Pero un
cuerpo de PR real no se escribe así: se escribe `` `Cierra **T-101 (#77)**` ``, con
la negrita y el id de tarea en medio. Resultado: **la guarda emitía verde sobre
exactamente el caso que existía para cazar.** No es que no corriera — es el modo de
fallo peor, porque un check en verde nadie lo revisa. En el proyecto de origen la
descubrió su propio caso de uso: un PR pasó el check con su issue todavía abierto,
y ya habían quedado dos issues sin cerrar por lo mismo.

**Eran dos agujeros, y el segundo es peor.** Con la palabra clave **inglesa**
decorada (`` `Closes **T-101 (#77)**` ``) GitHub tampoco cierra, pero el autor cree
que lo hizo bien, así que nadie comprueba el issue después de mergear. En el caso
español al menos queda la duda. Se detecta aparte y con su propio mensaje, porque el
arreglo es distinto: despegar la referencia, no traducirla.

**Por qué el conector no es un comodín.** El arreglo fácil era `.*` entre el verbo y
el `#N`, y habría convertido «Cierra la sesión y abre #77 cuando puedas» en una
denuncia. Es una lista **cerrada** — énfasis markdown, un artículo, un id de tarea,
el paréntesis que lo envuelve — y con repetición acotada para que un cuerpo raro no
dispare backtracking. Una guarda ruidosa acaba desactivada, que es peor que no
tenerla; esta guarda ya se disparó una vez contra su propia documentación.

**No se supuso qué acepta GitHub: se miró.** Antes de decidir qué forma inglesa dar
por buena se revisaron los 25 PRs mergeados del proyecto de origen. **Todos** usan
`Closes #N` pelado, así que no hay ni un caso que demuestre que la forma decorada
cierre algo. Se acepta solo la referencia pegada (con énfasis o dos puntos, nada
más). Dar por bueno lo contrario es justo como se quedaron issues abiertos.

**Fijado por los dos lados.** Las dos roturas deliberadas se vieron en rojo: con el
conector viejo caen los 6 casos del agujero; con un comodín caen los 2 que evitan el
falso positivo. Si alguien lo aprieta vuelve el bug, si lo afloja vuelve el ruido.

**Y una lección sobre el propio acto de comprobar.** El primer intento de romper la
guarda **no llegó a aplicarse** (el ancla del parche no coincidió) y la suite dijo
`26/26` — a un paso de leerse como «la guarda aguanta». *Un saboteo que no sabotea
produce exactamente el mismo verde que una guarda que funciona.* Desde aquí, un
script de rotura imprime la línea después de escribirla y verifica que cambió.

## 2026-08-16 (3) — El rojo de la auditoría llegaba siempre en el peor momento

Cuarto retorno proyecto→kit. Entra la **vigilancia programada** de la auditoría
(`audit_report.py` + `audit_issue_text.py` + `audit-programado.yml`) y la mitad que
le faltaba al kit para que los hooks de git no dependan de nadie
(`install-git-hooks.mjs`).

**Qué se rompía.** El audit bloqueante solo corre cuando alguien abre un PR, pero
los avisos de seguridad se publican a cualquier hora contra dependencias
transitivas que nadie está tocando. Resultado: **el rojo siempre lo descubre quien
venía a hacer otra cosa.** En el proyecto de origen, `main` se rompió tres veces en
un día sin que nadie del equipo causara ninguna, y costó dos desvíos completos a un
dev que venía a otra tarea. Ahora una ejecución programada convierte el rojo en un
issue con dueño antes de bloquear a nadie — y lo **cierra sola** cuando vuelve el
verde.

**Solo avisa, nunca arregla.** No es prudencia genérica: quedó demostrado que el
arreglo correcto no es siempre el mismo — un caso se resolvió con un override de
versión y el siguiente lo prohibía, porque ese override rompía el linter que
arrastraba el paquete. Un bot que suba versiones a ciegas habría tumbado la
herramienta.

**El quinto estado, que es el que suele faltar.** Los cuatro obvios son verde/rojo
× hay aviso/no hay aviso. El quinto es que la auditoría **no llegara a ejecutarse**:
sin código de salida o sin log no se sabe nada, y eso NO se cuenta como verde —
abre un aviso distinto que dice justo eso. Es la misma regla que ya gobierna el
resto del kit: *no poder preguntar no es que la respuesta sea no*.

**Anti-ruido con el estado en el propio issue.** El cuerpo lleva embebida una
huella del conjunto de problemas, así que el mismo rojo dos días seguidos no
comenta nada. La huella se calcula sobre los problemas y **no sobre el log**, que
trae recuentos y tiempos que cambian solos: calcularla sobre el log entero
convertiría el anti-ruido en ruido diario.

**El `schedule:` sale de `audit.yml`**, y no es cosmético: corriendo ahí, un rojo
programado solo dejaba una X en la pestaña de Actions — que la ve quien la mira.
En el workflow nuevo el mismo rojo abre un issue con dueño. Dos `schedule:`
auditando lo mismo habrían sido además ruido duplicado.

**`install-git-hooks.mjs`: solo la mitad que faltaba.** El kit ya **delataba** al
que no tuviera los hooks (el hook de arranque lo comprueba leyendo los tipos del
`.pre-commit-config.yaml`); lo que no tenía es que se instalaran solos. Se comprobó
antes de portar, para no duplicar un mecanismo que ya existía. Se instala **solo si
el destino tiene `package.json`** —fuera de Node nadie ejecuta `prepare`, y un
fichero instalado que nadie llama se parece demasiado a una guarda activa— y si
falta el script `prepare`, el instalador lo dice.

**Una mutación que no mordió, y por qué se cuenta.** Al probar el quinto estado,
mutar `if ejecutada and codigo == 0` no tumbó ningún caso: `leer_resultado` ya
devuelve código 1 cuando no concluye, así que esa condición es **defensa
redundante** y su mutación no cambia nada observable. La mutación que sí representa
el fallo real —dar por bueno un log que no existe— tumba el caso a la primera. *No
basta con ver un test en rojo: hay que ver que se pone rojo por el motivo
correcto,* y su reverso, que un verde bajo mutación puede significar que la
mutación no era un fallo.
## 2026-08-16 (2) — La guarda de seguridad deja de avisar y pasa a bloquear

Tercer retorno proyecto→kit. `recordar-seguridad.sh` **sale del kit** y lo
sustituyen `secure_guard.sh` + `secure_guard.py`, que no recuerdan: **deniegan la
edición**. Entra también `pr_body_check.py`, la guarda de los cierres de issue.
Las dos nacieron y se midieron en portal-web-api-sunat (T-204 y T-208).

**Qué se rompía.** El hook viejo emitía un `additionalContext` en **cada** edición
de código y nunca comprobaba nada: no sabía si la skill se había invocado, así que
avisaba igual al que ya la había aplicado. Un recordatorio que se repite sin mirar
es ruido, y el ruido se aprende a ignorar — que es como muere un recordatorio. El
nuevo verifica contra el transcript de la sesión y **se calla en cuanto la
obligación se cumple**; si no hay rastro, bloquea la edición y explica qué hacer.

**Los dos falsos negativos que casi lo dejan inútil**, encontrados provocándolos y
hoy con un caso que muerde cada uno:

- **Auto-disparo.** El aviso que emite la guarda queda escrito en el transcript.
  Con un patrón laxo, la guarda lee su propio texto y se da por satisfecha el
  resto de la sesión.
- **Mención ≠ invocación.** El `CLAUDE.md` de un proyecto nombra la ruta del
  `SKILL.md` en su sección de obligaciones, y se lee al arrancar cada sesión:
  bastaba con eso para silenciarla siempre.

De ahí la regla, que vale para la próxima guarda que alguien escriba: **al
comprobar "¿pasó X?" leyendo texto, exige la estructura del acto, no su nombre** —
la documentación de un proyecto habla de sus propias guardas y acaba
disparándolas o silenciándolas.

**Lo que el port heredó del hook que sustituye, y por eso no es una copia.** El
`.sh` viejo comprobaba que la skill estuviera instalada antes de decir nada; el
`.py` del proyecto de origen no, porque allí siempre lo está. Sin esa
comprobación, un proyecto que instale el kit sin la skill se queda con **toda**
edición de código bloqueada y sin nada que invocar para desbloquearla. Exigir algo
que no existe no es rigor.

**Una migración que había que decir en voz alta.** El instalador detectaba el hook
mirando si `settings.json` mencionaba `recordar-seguridad`. Al retirar ese fichero,
un proyecto ya instalado se habría quedado invocando una ruta inexistente: **sin
guarda y sin aviso**, servido por su propia actualización. Ahora el instalador
distingue los tres casos (ya migrado · apunta al viejo · sin hook) y el aviso de
migración dice la línea exacta que hay que cambiar.

**`pr_body_check.py`.** `Cierra #N` no cierra nada: GitHub solo reconoce las
closing keywords en inglés. En el proyecto de origen un PR se mergeó dejando su
issue abierto y hubo que cerrarlo a mano; el siguiente, con `Closes #N`, lo cerró
solo — la única diferencia era el idioma. Va enganchada en `docs-check.yml` con el
cuerpo **por `env`, nunca interpolado en el `run:`**: un
`${{ github.event.pull_request.body }}` dentro del script lo escribe cualquiera
que abra un PR y el runner lo ejecutaría como shell. Por entorno es un dato; en el
`run` sería código.

**Dos fallos que destapó escribir los tests, y estaban en los tests.** El primero:
los casos del camino "no se pudo verificar" dejaban su marcador en el temporal del
sistema, así que **pasaban la primera vez y fallaban la segunda** — un test que
cuenta una historia distinta según cuándo lo mires. El segundo: el caso de la
frontera de palabra usaba "reconstruye", que no contiene ningún verbo de la lista,
o sea que **pasaba igual con el patrón roto**; con "encierra" (que sí contiene
"cierra") por fin se pone rojo. Los dos se vieron fallar antes de darlos por
buenos, mutando el código a propósito.
## 2026-08-16 — El DoD generado no decía cuáles de sus ítems van después del merge

Cierra **M-16** y **M-14**, las dos últimas del `plan-mejora.md`. Las dos salieron
de ejecutar el kit sobre un proyecto real, que es como se encontraron las quince
anteriores.

**Qué se rompía (M-16).** El DoD que genera el kickstart era una lista plana donde
convivían cosas de naturaleza distinta sin nada que las distinguiera:

```
- [ ] Tests escritos y pasando
- [ ] Tag v0.1.0                                    ← solo puede hacerse tras mergear
- [ ] Se abre el catálogo: F2/F3 pasan a Disponible ← ídem
```

En un proyecto real **se abrió el catálogo con la tarea todavía En progreso**, o
sea antes de mergear. Nadie la reclamó en esa ventana, pero el riesgo era real:
otro dev habría empezado sobre un contrato que la revisión aún podía cambiar, y se
habría quedado sin suelo.

Lo interesante es dónde estaba el fallo. **La regla no faltaba: estaba escrita en
tres sitios** —`equipo.md`, `/cerrar-sesion` y el propio log del tablero—, y se
había leído. Faltaba en **el sitio que uno va tachando**. De ahí la lección, que es
más general que este arreglo: *tener la regla escrita en el sitio correcto no basta
si falta en el sitio que se mira*.

Ahora la plantilla de `guia_desarrollo.md` trae la tabla que explica los tres ítems
post-merge, el Paso 9 obliga a emitirlos como `- [ ] ⏭️ **post-merge:** …`, y —lo
que lo convierte en mecanismo— `verificar_kit.py` **sale rojo** si un DoD generado
lleva un tag, un "a Terminado" o un desbloqueo sin marcar. Sin ese último punto
sería una recomendación, y este plan existe para no dejar recomendaciones.

**La guarda se disparaba contra la tabla que enseña la regla.** Esa tabla nombra el
tag y el desbloqueo, así que la primera versión acusaba a su propia explicación.
Es el mismo auto-disparo que ya suspendió otra guarda de este kit contra el PR que
la introducía, y la tercera vez que aparece el patrón: **toda guarda que lea texto
acabará leyendo la documentación que habla de ella**. Resuelto exigiendo que la
línea sea un ítem de checklist, con un caso dedicado que se vio fallar.

**M-14, dos correcciones de texto que costaban trabajo real.** La tabla de
placeholders situaba `OWNER` y `PROJECT_NUMBER` solo en `scripts/tablero.py`;
están además **6 veces en `que-toca.SKILL.md` y 2 en `cerrar-sesion.SKILL.md`**
(contadas, no estimadas), así que quien siguiera la tabla al pie de la letra dejaba
las skills del candado con un `gh project item-list {{PROJECT_NUMBER}}` inválido —
y se enteraba **al reclamar**, no al configurar. Y el Paso 9 pedía generar dos
ítems que `instalar.sh` ya deja: regenerarlos cambia su hash en el manifiesto y la
siguiente actualización los trata como tocados por el equipo, con reconciliación a
mano de algo que nadie cambió. Ese razonamiento lo tuvo que deducir solo quien
ejecutó el kit en la prueba real; ahora está escrito donde se decide.

`test_verificar_kit.py`: **35 → 41 casos**. Tres mutaciones vistas en rojo, incluida
la de desenchufar la función del agregador — el modo de fallo que dejó las guardas
de `docs_check` en verde estando desconectadas.

## 2026-08-15 — Los pasos 2-3 del reclamo dejan de depender de que alguien se acuerde

Retorno proyecto→kit, el segundo. `scripts/estado.py` nació y se midió en un
proyecto real y el kit seguía enseñando **cinco invocaciones a `gh` a mano** para
lo mismo. Ahora viaja en el kit, con sus 15 casos.

**Qué se rompía.** Los pasos 2-3 pedían tres comprobaciones que solo existían como
prosa: que ninguna lista viniera cortada por el `--limit`, que el título saliera
del issue y no de la copia congelada de la tarjeta, y que no hubiera issues
abiertos fuera del Project. Las tres dependían de que el agente se acordara, y
**una ya falló de verdad**: el `.title` del item no sigue los renombrados del
issue, así que la tarjeta decía `T-062` cuando la tarea era la `T-072` — reclamar
por ese número es reclamar otra cosa. Ahora las tres las hace el script y cada una
tiene un caso que muerde.

**Lo que NO es.** No es un ahorro de contexto disfrazado. Se midió antes de
construirlo: la agregación ahorra ~500 tokens por reclamo (~1.600 con lo que
adelgaza la skill), no los ~10.000 que estimaba la propuesta de un servidor MCP —
que por eso se descartó. El valor es que el candado deje de apoyarse en la memoria.

**Sin casilla nueva que rellenar.** `estado.py` importa `OWNER` y
`PROJECT_NUMBER` de `tablero.py` en vez de declararlos: dos copias significaban
que quien rellenara solo una leyera el Project equivocado **en silencio**, que es
el peor modo de fallo para un candado.

**Un fallo que destapó el propio port.** El caso «el informe no vuelca JSON»
estaba escrito como `"{" not in texto`, y eso no mide el formato: mide la
configuración. Con `PROJECT_NUMBER` todavía en `{{PROJECT_NUMBER}}` —o sea, en
cualquier kit recién instalado y antes de configurarlo— la cabecera lleva llaves y
el caso daba rojo sin que nada estuviera mal. Ahora se comprueba por las claves
del dict, que es lo que de verdad distingue un informe de un volcado. En el
proyecto de origen el caso pasa porque allí el número está puesto: **un test que
depende de si alguien ya configuró el proyecto no prueba lo que dice su nombre**,
y solo se ve al moverlo.

La skill `/que-toca` funde los pasos 2 y 3 en uno, y conserva los comandos
manuales —con las tres trampas del `--jq`, el tope y `(.assignees // [])`— en un
desplegable, para quien no tenga el script a mano o esté depurando.

## 2026-08-07 — Dos guardas volvían del proyecto donde crecieron, y una no estaba enchufada

Retorno proyecto→kit: `docs_check.py` y `arranque.sh` llevaban semanas mejorando
en un proyecto real y el kit seguía generando la versión de julio. **La mitad que
falla siempre no es cómo baja el kit a los proyectos, es cómo suben los arreglos**
— van dos de tres veces que se descubre por casualidad.

**`docs_check.py` (243 → 359 líneas): el contador del ROADMAP.** El avance está
escrito a mano en TRES sitios —la tabla de cabecera, la fila de subfases y la
frase en prosa— y se calcula solo. Ya falló dos veces en el proyecto de origen; la
segunda es la que justifica la guarda: dos ramas subieron el contador **al mismo
número por motivos distintos**, git auto-fusionó el texto idéntico sin marcar
conflicto, y el resultado quedó declarando una subfase menos de las que había. Un
conflicto lo ve quien mergea; esto no lo ve nadie. Ahora se cuenta por estructura
—una fase con subfases aporta las suyas, una sin ellas aporta 1— y se coteja
contra lo declarado, con 1 punto de tolerancia en el % para que un redondeo
distinto no produzca un rojo que se aprenda a ignorar.

**`arranque.sh` (76 → 160 líneas): el aviso de hooks miraba un solo tipo.** Antes
comprobaba `pre-push` y que el fichero **existiera**. Dos agujeros: un clon con
`pre-commit` y sin `pre-push` pasaba callado, y un hook heredado de otro flujo
daba falso verde —fichero presente, guarda ausente—. Ahora los tipos se **leen**
de `.pre-commit-config.yaml` en vez de hardcodearse (así un tercero queda cubierto
solo) y se exige el marcador que pre-commit escribe en su cabecera. Y cuando la
clave está en YAML de bloque, que estos `sed` no saben leer, **lo dice** en vez de
callarse: una guarda contra fallos invisibles no puede permitirse uno.

**Lo que apareció al portar, y no venía del origen: las guardas de `docs_check`
no estaban probadas a través de `main()`.** Los 25 casos llamaban a
`enlaces_rotos()`, `backlog_incoherente()` y `roadmap_incoherente()` por separado,
así que **desenchufar cualquiera de las tres dejaba la suite en verde**.
Comprobado por mutación, no supuesto. Caso 26 añadido: monta un repo donde las
tres tienen algo que denunciar y exige que las tres salgan. Verificado que muerde
con las tres mutaciones, una a una. Una guarda desconectada es indistinguible de
una que pasa, que es el mismo modo de fallo que el fixture a medias del 06-08.

Suite: 26/26 en `test_docs_check.py` (era 25) y `test_arranque.sh` en verde, más
los otros diez ficheros de test del kit sin tocar. `VERSION` → `2026-08-07`.

## 2026-08-06 (3) — El instalador pisaba la configuración de los tres proyectos reales

`instalar.sh` decidía «aquí ya hay una instalación» mirando dos cosas:
`SKILLS-PORTABLE/.manifiesto` o la carpeta `SKILLS-PORTABLE/`. **Los tres
proyectos que usan el kit no tienen ninguna de las dos** — se instalaron antes de
que esa carpeta existiera, y el propio README dice que la copia de origen «queda
redundante: puedes borrarla».

Sin rastro, el destino se trataba como **virgen**: ruta de instalación limpia,
`cp` directo, y la configuración del equipo **pisada sin aviso y sin dejar
`.nuevo`**. Comprobado ejecutándolo sobre una copia: el `SKILL.md` configurado
cambia de hash y vuelve a estar lleno de `{{PLACEHOLDERS}}`.

Lo que lo vuelve grave no es el bug, es **contra qué comando estaba**: el único
que el README ofrece para actualizar. Y la fila «Instalación anterior a los
manifiestos → conserva todo; nada se pisa» **ya estaba escrita en ese README**.
La promesa existía; la condición para cumplirla, no.

**Por qué los tests no lo vieron, que es la parte que importa:** el caso 6
simulaba una instalación pre-manifiesto borrando el manifiesto **pero dejando la
carpeta**. Con la carpeta ahí quedaba un rastro, el instalador entraba en modo
actualización y el caso pasaba en verde describiendo un mundo que ningún proyecto
habita. Un fixture a medias es peor que ninguno: da por cubierto justo lo que no
lo está.

Ahora el rastro se busca en lo que el instalador escribe **siempre**
(`.claude/skills/project-kickstart/SKILL.md`, `.claude/hooks/arranque.sh`) y en
lo que delata el modo protocolo (`.claude/skills/equipo-que-toca/SKILL.md`). De
paso, **el modo se deduce**: sin manifiesto no hay `# modo=` que leer, y
quedarse en fábrica dejaría fuera justo las guardas que a esos proyectos les
faltan — `deriva_kit.py` mide que a los dos de SUNAT les falta el 40% del kit.

5 casos nuevos (44 en la suite; el README decía 37 desde el 07-27). Verificado
bajando `instalar.sh` a la versión anterior: **fallan 4 de los 5**. El quinto
—«lo que le faltaba del kit sí llega»— pasa también con el viejo, porque en modo
instalación limpia se copia todo igual: es una precondición del escenario, no una
mordida, y se dice para no contarlo como cobertura que no da.

## 2026-08-06 (2) — Nadie podía preguntar en qué se había desviado un proyecto

El kit viaja por copia y a partir de ahí las dos copias evolucionan solas. Ha
costado dos veces: el 2026-07-29 barber-king llevaba una semana divergiendo en 15
archivos / 1.157 líneas y se descubrió de casualidad; el 2026-08-06, tres días
después de un port que se creía completo, `plantillas/hooks/arranque.sh` seguía
detectando hooks con `grep pre-push` mientras el proyecto ya leía los tipos del
`.pre-commit-config.yaml`. Las dos veces el fallo no fue portar mal: fue **no
poder preguntar**.

`deriva_kit.py` responde en segundos, y su primera ejecución sobre los tres
proyectos reales dice lo que nadie sabía:

| Proyecto | `=` | `~` | `!` divergentes | `-` ausentes |
|---|---:|---:|---:|---:|
| barber-king | 21 | 1 | 17 | 1 |
| api-sunat-scr | 10 | 0 | 13 | **17** |
| portal-web-api-sunat | 10 | 0 | 15 | **15** |

Los dos de SUNAT **no tienen el 40% del kit**: les faltan `tablero.py`,
`audit_check.py`, `deriva_ramas.py`, `proteccion_main.py`, sus tests y el hook
del guardián de seguridad. Llevan ahí desde que se instalaron.

**Lo que hace que el informe sirva: separar `~` de `!`.** El kit escribe
`{{OWNER}}` donde el proyecto tiene `SanchezIng`, y contar eso como diferencia
pondría en rojo permanente justo las piezas que más importan —las 3 skills,
`tablero.py`, `audit_check.py`—. Una línea que solo difiere en la posición de un
placeholder se clasifica como configuración, no como deriva.

**Y no duplica el mapa de archivos:** instala el kit en un temporal y lee el
manifiesto que deja el propio instalador. Un detector de deriva que copia el mapa
del instalador acaba derivando él mismo, que sería el chiste completo.

No es una guarda de CI y el README lo dice: un proyecto vivo siempre tendrá
divergencia legítima. Sale 1 si la hay para poder encadenarlo, pero se ejecuta a
mano — antes de portar, después de portar, y antes de creerse que algo está
sincronizado.

19 casos nuevos en `test_deriva_kit.py`, en el CI. Uno mordió durante el
desarrollo: un workflow que el equipo activó renombrándolo salía como idéntico
pero el informe se callaba con qué nombre lo había encontrado.

## 2026-08-06 — `VERSION` decía una cosa y el kit traía otra

Los dos últimos cambios grandes entraron **sin tocar `VERSION` y sin escribir
aquí**: `ebfab29` (#15), que trajo de BarberCrow la arquitectura del protocolo
—el log en un fichero por entrada, el tablero que ya no se comitea, el chequeo de
issues que están fuera del Project— y `a60ef67` (#16), que trajo el ahorro de
contexto medido allí: **64.051 tokens por ciclo de tarea**, el 53% del
presupuesto útil de una sesión, casi todo en el `--jq` del `item-list` de
`/que-toca` (51.807 de esos 64.051).

`VERSION` quedó en `2026-08-04` sobre un kit que ya no era el del 04. Sube a
**`2026-08-06`**, la fecha del contenido portado — que es la convención que ya
usaba el 04, no la fecha del merge.

**Qué se rompía, con precisión, porque es menos de lo que parece:** la
actualización **no** estaba rota. `instalar.sh` compara **hash a hash** con
`git hash-object`, y la igualdad de versión (línea 68) solo imprime un aviso
antes de seguir comparando; un proyecto que actualizara habría recibido los
ficheros nuevos igual. Lo que estaba roto es la **etiqueta**: el manifiesto graba
`# kit=<version>` en cada destino, y ese sello es el único sitio donde consta qué
trae un proyecto instalado. Con el sello congelado, la respuesta a «¿este proyecto
tiene el arreglo de los 51k tokens?» pasa a ser «mira los hashes uno a uno»,
que es justo lo que el sello existe para evitar.

Es el mismo patrón que las tres entradas del 07-27: **una señal que no se
actualiza no es una señal, y se aprende a no mirarla.**

Queda una decisión, no un pendiente disfrazado: o el bump entra en el propio port
como paso obligatorio, o `VERSION` se deriva del hash del manifiesto y deja de
poder mentir. Lo segundo es más trabajo y no se hace hoy.

**No se toca `kit-construction-project/.manifiesto`**, cuyo encabezado dice
`# kit=2026-07-26`: ese fichero es la foto de una instalación pasada (la de
barber-king), no la versión del catálogo. Cambiarlo sería falsear el registro que
va a servir para engancharlo.
## 2026-07-28 — El kit escribía órdenes que su lector no puede cumplir

El usuario trajo un prototipo HTML cuyo texto decía «abre el prototipo y míralo
antes de maquetar». El kickstart lo copió palabra por palabra a ~16 subfases de
la guía generada. **Claude Code no tiene renderizador**: ninguna de esas 16 se
podía cumplir. Y el prototipo era un artifact *bundled* —2,9 MB donde un `Read`
devuelve base64 y la UI vive dentro de `<script type="__bundler/template">`—, así
que la sesión que lo detectó escribió un desempaquetador de ~40 líneas para poder
leerlo, resolvió su parte y **se lo llevó al cerrar**. El repo quedó con 16
órdenes imposibles y sin la herramienta que las hacía posibles.

El kit no controla lo que entra —es material arbitrario del usuario y no va a
controlarlo nunca— pero sí controla lo que sale. Ahí se corta:

- **Fila del diseño** en la tabla de entorno de `project-kickstart`, con el caso
  *bundled* explicado y la orden de dejar el desempaquetador en `scripts/`.
- **Regla 8 de las «Inviolables»:** lo heredado de la entrada se traduce al
  procedimiento que sí funciona donde va a leerse, y la herramienta que hizo
  falta se queda en el repo. Con el caso real escrito debajo — una regla sin su
  historia se borra en el primer refactor.
- **El mecanismo, que es lo que la separa de una recomendación:** regla 6 de
  `verificar_kit.py`, en el Paso 10. Una orden de mirar un diseño sale roja salvo
  que al lado esté el comando **y** la herramienta exista en el repo. Las dos
  mitades fallaron de verdad: sin comando sigue siendo «míralo», y con un comando
  a un script que se cerró con la sesión, la siguiente lo rehace.
- Y `ejecutabilidad_documentada()` en `kickstart_check.py`, para que la fila y la
  regla no puedan caerse en silencio.

**Lo que enseñó ejecutarlo contra el proyecto real, que es la parte que importa.**
La primera versión de la regla saltaba los bloques de código, como hacen las otras
cuatro —ahí viven plantillas y ejemplos—. Contra BarberCrow encontró **2** fallos.
Los otros once estaban DENTRO de los prompts: en la guía generada los bloques no
son ejemplos, son lo que el dev pega literal. Esta regla los mira, y es la única
que lo hace. Después apareció la segunda mitad: «ABRE el prototipo» se veía y
«(pantalla 8 del prototipo — ábrelo)» no, por el orden de las palabras.

Sin esa ejecución, el mecanismo habría pasado sus 35 casos en verde cubriendo el
15% del fallo que decía cubrir. Ahora saca 13 fallos sobre el proyecto real y los
13 son verdaderos: cero ruido, que es la condición que dejó puesta el arreglo del
verificador (M-10) — una guarda que sale roja con ruido no se lee, se rodea.

`diseño` a secas se dejó **fuera** del patrón a propósito: en español cubre «el
diseño de la base de datos», que se mira leyendo un `.md`. La regla general vive
en la skill; el que muerde solo muerde la forma que ya se sabe que aparece.

## 2026-07-27 (3) — Una lista que solo sabe decir "queda trabajo" no informa

El grep de placeholders que imprime `instalar.sh` barría `scripts/` entero, donde
`test_tablero.py`, `test_audit_check.py` y `test_docs_check.py` llevan
placeholders como **fixture deliberado** — y son exactamente los mismos nombres
que los archivos de verdad, así que tapaban la señal completa. La lista no podía
salir vacía nunca: un "queda trabajo pendiente" permanente e insatisfacible.

Se había introducido el mismo 2026-07-26, al ampliar el grep a `scripts/` para no
dejar fuera `{{GESTOR_PAQUETES}}`. Se arregló que faltaran y se creó que sobraran:
los dos errores son el mismo, **listar sobre un conjunto mal elegido**.

**Y había una segunda causa que solo apareció al ejecutar el caso.** Excluir
`test_*` no bastaba: cuando el instalador conserva un archivo que el equipo
configuró, deja al lado la versión del kit como `<archivo>.nuevo`, de fábrica y
llena de placeholders. O sea, en cuanto un proyecto configura algo y actualiza
—todos, tarde o temprano— la lista volvía a ensuciarse por otro camino. Y no son
configuración pendiente: son copias esperando reconciliación, de las que ya
informa `resumen_actualizacion` bajo CONSERVADOS. Vale la pena decirlo porque el
plan daba `test_*` por suficiente, y lo era solo en un proyecto recién instalado —
justo el que nadie tiene después del primer día.

La lista deja de ser un volcado: ahora dice «Sin rellenar todavía: …» o
**«Placeholders: ninguno pendiente.»**. Poder decir lo segundo era el objetivo. Es
la misma lección de las dos entradas anteriores: una señal que no puede estar en
verde no es una señal, y se aprende a saltarla.

De paso, una corrección al plan: ese grep vive **solo** en `instalar.sh`. El
README nunca lo documentó, así que la tarea de arreglarlo "también en el README"
no existía.

Cierra M-12. 4 casos nuevos, **37** en la suite del instalador. Verificado
bajando `instalar.sh` a la versión anterior: fallan 2 (el tercero es una
precondición del escenario, no una mordida). La segunda causa se comprobó a mano:
con `test_*` excluido y sin `*.nuevo`, seguían saliendo 4 placeholders, los cuatro
de archivos `.nuevo`.

## 2026-07-27 (2) — El checklist vivía después del `exit 0`

`instalar.sh` terminaba la ruta de actualización con `resumen_actualizacion;
exit 0`, y el bloque **FALTA (a mano, o pídeselo a Claude)** —los placeholders,
`OWNER`/`PROJECT_NUMBER`, pegar el `CLAUDE-fragmento.md`, el `.gitignore` y
proteger `main`— estaba escrito veinte líneas más abajo. Es decir, después del
`exit`.

Lo que lo vuelve grave no es el descuido, es **qué ruta se lo perdía**. El
instalador *fuerza* el modo actualización en cuanto detecta una instalación
previa —a propósito, para que repetir el comando no destruya la configuración del
equipo—, así que cualquier **segunda ejecución** se quedaba sin el checklist
entero. Y el README documenta fábrica y `--protocolo` como dos líneas seguidas,
que es exactamente esa secuencia. En la primera ejecución real hubo que
reconstruir la lista a mano leyendo el código.

**El arreglo no fue mover el bloque por encima del `exit`.** Eso arreglaba este
caso dejando en pie lo que lo causó: dos salidas, una de ellas prematura, y nada
que impidiera que la siguiente línea útil volviera a caer al lado equivocado.
Ahora el bloque es `pendiente_de_configurar()`, se llama **una sola vez al final**
y la actualización solo añade su resumen antes. No queda un `exit` del que
depender.

Al actualizar, el título cambia a «REPASO de configuración (lo que ya hicisteis,
ignoradlo)». Decir "FALTA" sobre algo hecho es la misma clase de ruido que la
entrada anterior de este changelog: enseña a saltarse el bloque entero.

Y otra vez la causa de fondo estaba en los tests. `test_instalar.sh` cubría las
tres rutas para la *supervivencia de la configuración*, pero ninguna comprobaba
que el checklist llegara: la única sin cubrir era justo la que fallaba. Ahora hay
4 casos —repaso al actualizar (título, pasos y placeholders) y al repetir el
comando de instalación— más uno que fija el «FALTA» de la instalación inicial.
**33 casos** (el README decía 23 desde hacía tiempo).

Cierra M-11. Verificado bajando `instalar.sh` a la versión anterior: los 4 casos
nuevos fallan.

**Límite dicho en voz alta:** el repaso no sabe qué configurasteis ya. Lo único
que podría saberlo es la lista de placeholders, y hoy miente por exceso — eso es
M-12, y hasta entonces la lista no vale como semáforo de "no queda nada".

## 2026-07-27 — Una guarda que sale roja con ruido no se lee: se rodea

`verificar_kit.py` recorría el proyecto entero excluyendo solo `.git` y
`node_modules`, así que barría `SKILLS-PORTABLE/` y `.claude/` — el kit
**instalado**, cuyos `{{...}}` son plantilla y cuyos enlaces apuntan al paquete.
En un proyecto con el kit puesto (o sea, el caso normal) la primera ejecución
salía con **37 fallos y ninguno señalando un archivo generado**.

Lo caro no fue el falso positivo. En la primera ejecución real el evaluador, ante
37 fallos que sabía ruido, **copió el proyecto a un temporal excluyendo esas
carpetas, verificó la copia y reportó verde**. El incentivo lo fabricó el kit: una
guarda que grita en falso en su estreno no se lee, se rodea. Y a partir de ahí
deja de proteger nada.

**La causa de fondo no era el escaneo, eran los tests.** Ninguno de los 21 casos
incluía `SKILLS-PORTABLE/` ni `.claude/`: el verificador se probó contra un mundo
que no existe, y por eso pasó su propia suite y falló el primer día real. Ahora
hay un fixture del kit **instalado**, y el caso que muerde comprueba la **lista de
archivos escaneados**, no el veredicto — así no basta con silenciar los fallos por
otro camino. Con su recíproco: rodeado de kit instalado, un placeholder real en
`README.md` sigue saliendo, y sale solo. Excluir no puede ser cegar.

Reparto de responsabilidad, que es lo que de verdad quita el ruido: los
placeholders que sí hay que rellenar dentro de `.claude/` (`OWNER`,
`PROJECT_NUMBER`) los reclama el checklist de `instalar.sh`, que es quien los puso
ahí. Este verificador responde por lo que generó el kickstart.

De paso, dos cosas que estaban en la misma expresión y no se podían reescribir
fingiendo no verlas: la exclusión se mide sobre la ruta **relativa** a la raíz (si
mirase la absoluta, un proyecto bajo `~/.claude/...` se quedaría sin verificar y
en silencio), y los paréntesis de la disyunción — `and` liga más fuerte que `or`,
así que un **directorio** llamado `.gitignore` o `.env.example` entraba en la
lista y reventaba al leerlo.

Y como la herramienta sola no impide el rodeo, el Paso 10 de `SKILL.md` lo dice
ahora con todas las letras: si sale en rojo señala algo tuyo, no lo rodees, y si
crees que un fallo es ruido dilo en la entrega **con el fallo delante**.

Cierra M-10 y M-15. 5 casos nuevos (26 en esa suite). Verificado bajando el
código a la versión anterior: 4 de los 5 fallan contra ella; el quinto muerde
contra el arreglo ingenuo de excluir por ruta absoluta.

## 2026-07-26 (7) — La skill hablaba el idioma del entorno equivocado

Al preguntar "¿qué errores dará si Claude Code ejecuta el kit?", la respuesta
honesta exigía leer `SKILL.md` como si fuera a ejecutarse. Y ahí estaba: la skill
**nació para el chat de claude.ai** y hoy se instala dentro de proyectos de Claude
Code, donde tres de las herramientas que nombra **no existen** —
`ask_user_input_v0`, `present_files` y la skill `docx`— además de dar por sentado
un "directorio temporal de trabajo" que aquí es la raíz del repo.

No reventaba: Claude improvisa y sale un kit. El problema es *dónde* improvisa —
en el paso de entrega, que era el que garantizaba que salieran **todos** los
archivos.

Peor era la otra: el Paso 9 citaba `<paquete>/...` **sin resolver nunca esa ruta**,
y remataba con *"si no encuentras esas plantillas, dilo y sigue sin autopilotaje"*.
Es decir, ante una ruta no encontrada el kit se entregaba **sin las 3 skills del
protocolo, sin hooks y sin guardas de CI** —más de la mitad de su valor— avisando
en una línea que se pierde entre cincuenta. Degradación silenciosa, que es la
clase de fallo que este kit persigue.

Ahora hay una sección **antes del Paso 0** con dos comprobaciones: la tabla de
equivalencias por entorno, y localizar el paquete con la orden de **parar** si no
aparece, en vez de decidir por su cuenta entregar la mitad.

Y como esto es texto, y el texto se vuelve a romper: `kickstart_check.py` gana una
octava regla — si `SKILL.md` nombra una herramienta que solo existe en claude.ai,
la tabla de equivalencias tiene que existir **y nombrarla**. 3 casos nuevos (32 en
esa suite, 212 en total).

## 2026-07-26 (6) — Se cierran los dos huecos que quedaban anotados

No son mejoras nuevas del plan: son los dos límites que las mejoras ya cerradas
dejaban por escrito, y que al resumir el kit resultaron ser los que más pesaban.

**Verificar la salida, no solo la plantilla.** `kickstart_check.py` comprueba que
la skill no prometa lo que sus plantillas no describen — eso valida la
*plantilla*. Lo que nadie validaba es la *generación*. Ejecutar Claude en CI no es
posible, así que la salida no es un `--dry-run`: es
`skills/project-kickstart/verificar_kit.py`, que se ejecuta **en el Paso 10,
antes de entregar**, y comprueba contra `.kickstart-state.json` que estén los
archivos que esa entrevista obligaba a generar (núcleo, equipo si hay 2+ devs,
ADR si es mediano/grande), que no quede ningún `{{PLACEHOLDER}}`, que los enlaces
resuelvan y que CLAUDE.md traiga sus tres secciones útiles. Verifica **el
artefacto en el momento en que se produce**, que es cuando el error todavía es
gratis. 21 casos, incluidos los que impiden acusar en falso: un placeholder
dentro de un bloque de código es un ejemplo, y un kit en inglés no se juzga con
títulos en español.

**Las guardas desactivadas dejan de depender de la memoria.** `audit.yml` y
`proteccion-main.yml` se instalan desactivadas a propósito (activarlas sin
configurar produce un rojo que no es un fallo, y un rojo que no significa nada se
aprende a ignorar). Pero "acuérdate de activarla" no es un mecanismo — es
justamente lo que este kit existe para eliminar. Ahora:

- El **hook de arranque** las lista en cada sesión, con el prerrequisito de cada
  una y el `git mv` exacto, y **desaparece solo** al decidir. También ofrece la
  otra salida: borrarla, porque dejarla ahí es una decisión sin tomar.
- `proteccion_main.py` **detecta la llegada de un segundo colaborador humano** y
  exige subir `EXIGIR_REVISION`. La excepción de trabajar en solitario existía
  porque GitHub no deja aprobar el PR propio; ahora caduca sola en vez de esperar
  a que alguien lo recuerde. Los bots no cuentan (dependabot no revisa nada), y
  si la API no responde **avisa sin tumbar el CI**: es una comprobación de
  configuración, no un veredicto de seguridad, y una falsa alarma aquí enseña a
  ignorar el rojo.

**La regla de las ~300 líneas pasa de tope a preferencia.** Superarla está bien
cuando el archivo lo pide —una máquina de estados, un parser, un test de tabla
que se lee mejor de corrido—; lo que no vale es superarla por inercia. El criterio
real es cuántas responsabilidades conviven dentro, no el número: se divide algo de
200 líneas con tres responsabilidades, y no se parte uno cohesionado de 500 solo
para cumplir la cifra, porque eso deja dos archivos que hay que leer juntos.

Diez suites, **199 casos**. La guarda de este repo se actualizó **injertando** la
mejora sin tocar su configuración propia — la lección de M-01 aplicada a mano.

## 2026-07-26 (5) — El kit da el instrumento para el problema que él crea

**M-09, y con ella el plan queda cerrado.** El kit prescribe módulos reclamables
trabajados en paralelo, y eso produce **estructuralmente** ramas de vida larga que
divergen: es consecuencia del diseño, no un accidente. Creaba la condición y no
daba el instrumento. En el piloto, un PR salió de su base el 18 y se mergeó el 22:
cuatro conflictos, y uno **no mecánico** — la rama afirmaba un estado de tarea que
ya era falso, y resolverlo a ciegas con `--theirs` habría metido una regresión
documental en `main` con el CI en verde. Fue el mayor sumidero de tiempo de la
sesión; el día 19 habría sido trivial.

`scripts/deriva_ramas.py` (programado, dos veces por semana) avisa en los PRs que
se han quedado más de N commits por detrás de su base.

Lo que decide si sirve, más que el umbral:

- **Un aviso por PR, no uno por ejecución** — el requisito que el hallazgo ponía
  por encima de todo. Comenta una vez y después **edita ese mismo comentario**: la
  cifra queda al día sin una sola notificación nueva. Un bot que avisa en cada
  pasada se filtra, y un aviso filtrado no es un aviso.
- **El aviso se corrige a sí mismo:** si la rama se pone al día, el comentario se
  actualiza para decirlo. Un aviso obsoleto también miente.
- **No poder mirar no es "no hay deriva":** si `gh` falla, si la comparación no
  trae `behind_by` o si el listado de PRs llega al tope, para y lo dice.
- El texto explica el riesgo **real** —el conflicto no mecánico, la regresión que
  ningún test cubre— y cómo salir, no solo el número.

Verificado contra los PRs reales de los dos repos del piloto: con umbral 8 detecta
tres (#126 a 8 commits por detrás, #51 a 11, #50 a 12) y deja en paz al resto; con
umbral 50 calla. La simulación (`--simular`) no tocó ningún PR. 18 casos nuevos,
con los dos modos de fallo opuestos: spamear y callar cuando debería hablar.

Por qué no basta lo nativo: *"Require branches to be up to date before merging"*
depende de la protección de rama, que en repos privados con plan Free no existe —
el mismo muro de M-03.

Con esto, las nueve mejoras del [plan](plan-mejora.md) están cerradas: los cinco
defectos que la auditoría del 25 encontró **ejecutando** el kit, y los cuatro
hallazgos de uso real que seguían siendo texto sin mecanismo.

## 2026-07-26 (4) — El audit deja de ser decorativo

**M-08.** El kit prescribía `npm audit` y compañía en el checklist de cada fase
**sin decir qué hacer cuando encuentra algo**. Quien monta el CI se topa entonces
con un dilema sin salida buena: bloqueante a secas deja el CI rojo desde el primer
día por transitivas sin fix aguas arriba —y un rojo permanente enseña a ignorar el
rojo—, y `continue-on-error` no avisa nunca. En el piloto se eligió lo segundo y
**dos `high` vivieron días en `main` con el CI en verde**, hasta que aparecieron
por casualidad auditando a mano durante un merge.

`scripts/audit_check.py` + `security/audit-allowlist.json`: lo aceptado a sabiendas
no bloquea, lo nuevo sí. Portado de la implementación de referencia ya en producción
(`portal-web-api-sunat` PR #48) y parametrizado por gestor — `npm`, `pnpm`, `yarn`,
`pip-audit`, `composer`, `cargo`.

Lo que impide que degenere en un `ignore` general es que falla en **cuatro** casos,
no solo en el obvio: vulnerabilidad sin aceptar, aceptación **caducada**, entrada
que **ya no aparece** en el audit (se arregló aguas arriba y taparía el próximo
aviso del mismo paquete) y vencimiento a **más de 180 días** (sin techo, la fecha se
pone lejana y la caducidad es humo).

Decisiones que definen el resto:

- **La clave es el aviso (GHSA/CVE/RUSTSEC), nunca el paquete.** Verificado con un
  caso real: `minimist` sale como `critical` de paquete pero uno de sus avisos es
  `moderate` — aceptar por paquete taparía el `critical`.
- **Falla cerrado**, que es lo único imperdonable aquí: si el gestor no está, si la
  salida no es JSON o si no tiene la forma esperada, para. Probado con el error real
  de `pnpm` sin lockfile, que de otro modo se habría leído como "sin
  vulnerabilidades". Un falso verde en una guarda de seguridad es peor que no
  tenerla, porque nadie vuelve a mirar.
- **"Desconocida" no es "leve".** `pip-audit` y `cargo audit` no reportan severidad;
  ahí todo aviso bloquea salvo aceptación explícita.
- **La lista nace vacía y el workflow se instala desactivado.** Activarlo sin
  rellenar el gestor produciría un rojo que no es una vulnerabilidad, que es
  literalmente cómo se aprende a ignorar el rojo.
- `--diagnostico` enseña lo que la guarda **leyó**, no lo que el comando imprimió.

Verificado de punta a punta contra dependencias vulnerables reales
(`lodash@4.17.15`, `minimist@0.0.8`) con `npm` y con `pnpm` — que coinciden en los
mismos 8 avisos: bloquea los 4 bloqueantes, los acepta al declararlos, y muerde al
caducar una entrada y al dejar una fantasma. 26 casos nuevos.

Límite dicho en voz alta: solo `npm` y `pnpm` están verificados contra la
herramienta real. `yarn`, `pip-audit`, `composer` y `cargo` van marcados como no
verificados en el código y en el README; el fallo cerrado hace que una sorpresa de
formato se note en vez de pasar por build limpia.

## 2026-07-26 (3) — El tablero se genera; el porqué se sigue escribiendo

**M-07.** El estado de una tarea vivía duplicado a mano en el Project, en
`progreso/tablero-equipo.md` y en `progreso/estado-actual.md`. En dos días de uso
real eso derivó **tres veces**; en una hubo que ir al `git log` para dirimir cuál
de las tres fuentes decía la verdad, y resolver el conflicto a ciegas habría
metido una regresión documental en `main` con el CI en verde. La redundancia solo
preserva contexto si las copias coinciden: cuando discrepan es peor que no
tenerla, porque quien lee no sabe cuál manda.

`scripts/tablero.py --generar` reescribe la tabla desde el Project. Lo que nadie
teclea no puede desviarse.

**La frontera que define el cambio:** la tabla se genera, el **log de reclamos no
se genera jamás**. La tabla es un hecho mecánico (en qué columna está algo, quién
lo tiene); el log es causalidad (por qué se atascó, qué trampa costó un intento
fallido, qué se acordó al partir un módulo). Un generador de logs produciría texto
plausible y vacío y se perdería justo lo que mejor funciona del kit. El generador
escribe solo entre marcas y conserva byte a byte lo que hay fuera.

Lo que se quitó, no solo lo que se añadió:

- **`estado-actual.md` pierde la tabla de estado por módulo** — era el espejo de un
  espejo. Se queda con lo que solo él tiene: decisiones vivas, deudas y
  convenciones que cambiaron.
- **`docs/equipo.md` pierde las columnas de estado y de "quién trabaja en qué"**,
  una tercera copia que el hallazgo original no había listado. Conserva lo que no
  cambia cada día: label, frontera, dependencias.
- `/que-toca` y `/cerrar-sesion` ya no editan la tabla: la regeneran.

Lecciones anteriores aplicadas de vuelta:

- **Nunca se pisa lo que escribió una persona** (M-01): si el archivo no lleva las
  marcas del bloque generado, se niega a tocarlo y explica cómo adoptarlo.
- **Ninguna conclusión sobre una lista truncada** (M-05): si el Project devuelve
  menos items de los que dice tener, o justo el tope, no escribe nada. Un tablero a
  medias no se lee como incompleto, se lee como si esas tareas no existieran.
- **Verificar el efecto, no la invocación:** tras escribir, relee el archivo y falla
  si no contiene el bloque.

Verificado contra el Project real del piloto (55 items): genera, es idempotente,
conserva una línea de log añadida a mano y se niega a pisar un tablero sin marcas.
Y destapó lo que un tablero a mano tapaba: **26 de las 55 tareas no llevan label
`modulo:`**, todas las posteriores al MVP. Ahora salen agrupadas bajo `(sin
módulo)`, que es la forma de que se note. 16 casos nuevos en `test_tablero.py`
(31 en total).

## 2026-07-26 (2) — La pieza más grande deja de estar sin vigilar

**M-06.** `project-kickstart` son ~2.900 líneas de prosa que nadie ejecuta: una
skill que un Claude lee para generar el kit de un proyecto nuevo. No se puede
testear la prosa, pero sí **las promesas que hace sobre sí misma**, y ninguna
estaba comprobada. `kickstart_check.py` exige que las dos listas de archivos a
generar (Paso 9 y `plantillas.md`) cuadren, que cada archivo prometido tenga
plantilla, que las rutas y enlaces existan, que las secciones citadas de otro
documento sigan ahí, y que todo `{{PLACEHOLDER}}` esté documentado.

Lo que destapó al primer intento:

- **10 placeholders reales sin documentar**, todos de `verificar.SKILL.md`
  (`{{CUANDO_NIVEL_2}}`, `{{PASO_PREPARACION}}`, `{{N_TESTS}}`…). La tabla del
  README los cubría con un "…", así que se instalaban tal cual y el proyecto
  arrancaba con `{{...}}` dentro de su runbook. Ahora tienen sus 11 filas.
- **Dos falsos positivos de la propia guarda**, corregidos antes de dar por
  bueno ningún veredicto: las cabeceras `## ARCHIVO n` no se buscaban en modo
  multilínea (no contaba ninguna, y las delegaciones tapaban el hueco) y
  `references/x.md` se resolvía siempre contra el kickstart, acusando a las
  cinco referencias legítimas de `secure-coding-guard`. Los dos con test de
  regresión: una guarda que acusa en falso se acaba desactivando.

Detalles que importan más de lo que parecen:

- **Los bloques de código no son estructura.** Un `## 4.` o un `## ARCHIVO 99:`
  dentro de un fence es un ejemplo. Sin esa distinción el kit se denunciaría a
  sí mismo por documentarse y —peor— una plantilla de ejemplo taparía la
  ausencia de la real.
- **Lección de M-05 aplicada de vuelta:** si el inventario del paquete sale
  vacío, la guarda muerde en vez de anunciar "todo OK". Un paquete que no se
  pudo leer no sostiene ninguna conclusión sobre lo que le falta.
- **Se dice lo que NO cubre:** esto valida la plantilla, no la generación. Un
  Claude que ignore la plantilla sigue pudiendo generar cualquier cosa; el
  `--dry-run` con entrevista de fixture queda pendiente y anotado.

Verificada que muerde contra el paquete **real**, no solo contra los sintéticos:
renumerar `trabajo_en_equipo.md` §9 destapa las 5 citas que quedarían mintiendo.
29 casos nuevos (`test_kickstart_check.py`), cada regla en los dos sentidos.

Y una ausencia que nadie había notado: **ninguna suite del kit se ejecutaba
sola**. El único workflow era el de protección de `main`. `.github/workflows/kit.yml`
corre las siete en cada push y PR, con las guardas antes que lo que vigilan.

## 2026-07-26 — El kit deja de depender de que alguien se acuerde

Cinco mejoras del [plan](plan-mejora.md), los tres 🔴 incluidos. El hilo común:
donde el kit tenía una regla escrita, ahora hay mecanismo probado; y donde el
mecanismo dependía de un dato pegado a mano, ahora se descubre solo.

- **M-01 · Actualizar ya no destruye la configuración.** Reinstalar sobre un
  proyecto configurado borraba los IDs del Project y los comandos del stack, en
  silencio. Eso mantenía a cada proyecto congelado en la versión con la que
  nació, porque la única vía para traerse mejoras era la que las destruía. Ahora
  hay manifiesto de hashes: lo que tocó el equipo se conserva y la versión nueva
  llega como `<archivo>.nuevo`. No depende de recordar un flag — reinstalar con
  el comando de siempre también actualiza. `VERSION` sella con qué versión se
  instaló cada proyecto.
- **M-02 · El candado de reclamo no justifica saltarse la protección de `main`.**
  El reclamo ya es instantáneo en GitHub (assignee + Project); el push del
  tablero era una segunda copia de algo ya visible, y su precio era dejar la
  rama sin proteger para siempre. Ahora el tablero viaja en el PR. Se preserva
  el matiz real: sin GitHub Project, el tablero **es** el candado y entonces
  `main` no puede protegerse del todo — un modo u otro, nunca los dos.
- **M-03 · Proteger `main`, del texto al mecanismo.** El kit exigía revisión sin
  decir cómo se configura ni que puede no estar disponible. Ahora empieza por el
  diagnóstico (`gh api …/rulesets`) y bifurca: protección de rama si se puede, o
  guarda de CI que denuncia los commits sin PR aprobado. Se dice explícitamente
  que **detectar no es prevenir**. Este repo, privado en Free, usa la detectiva.
- **M-04 · Los IDs del Project se resuelven solos.** Eran siete pegados a mano y
  nadie comprobaba que siguieran vivos; al recrear el Project, `/que-toca`
  asignaba el issue y no movía la tarjeta. `scripts/tablero.py` los descubre en
  ejecución, para con diagnóstico si algo no cuadra, y tras mover **relee** el
  estado. De paso elimina la trampa de PowerShell con GraphQL: los valores van
  como variables, no como literales entre comillas.
- **M-05 · Ningún listado decide sobre una lista truncada.** `gh` trae 30 por
  defecto y dos llamadas no pedían más. La grave: se listaban todos los issues
  para descartar los que tuvieran dueño, así que **más allá del tope parecían
  libres por ausencia de datos** — el candado dando por libre lo que otro tenía.
  Ahora filtra el servidor (`no:assignee`), con lo que una lista corta solo
  puede ocultar tareas, nunca inventarlas.

Cuatro suites nuevas o ampliadas, todas probando también que **muerden**:
`test_instalar.sh` (23), `test_tablero.py` (15), `test_proteccion_main.py` (10),
más las de docs_check (12) y el hook (9).

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
