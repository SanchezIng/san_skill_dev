# El kit portable se quedó congelado en el modelo de antes del 2026-07-28

**Fecha:** 2026-07-29 · **Estado:** anotado, sin issue · **Nota local, no comiteada**
**Revisado:** 2026-07-29 tras mergear #87, #91, #94 y #96 — medidas abajo re-verificadas contra `main`

Salió al añadir el paso del Project a `/que-toca` y `/cerrar-sesion` (PR #94). Al
tocar las dos copias de cada skill se vio que no dicen lo mismo, y al medirlo resultó
que la deriva no es aleatoria: **el kit portable enseña, entero y coherente, el modelo
de trabajo que este repo abandonó el 2026-07-28** — el que hacía que todas las ramas
chocaran en los mismos ficheros.

Medido sobre `origin/main`, no sobre ramas en vuelo.

---

## Lo que NO está derivado (para no perder tiempo ahí)

| Qué | Resultado |
|---|---|
| `project-kickstart/SKILL.md` + sus 9 `references/` | **idénticos** |
| `secure-coding-guard/SKILL.md` + sus 5 `references/` | **idénticos** |
| `project-kickstart/verificar_kit.py` | **idéntico** |
| `equipo/verificar.SKILL.md` | difiere **solo** en `{{PLACEHOLDERS}}` y comentarios de plantilla — por diseño, no es deriva |
| El kit **sí** envía `tablero.py` (`plantillas/protocolo/`) | las skills portables no referencian un script fantasma |

La deriva está confinada a `equipo/que-toca`, `equipo/cerrar-sesion` y
`plantillas/protocolo/tablero.py`. Tres ficheros.

---

## Lo que sí está derivado

### 1. `plantillas/protocolo/tablero.py` — es CÓDIGO, y es lo más grave

```
scripts/tablero.py                             614 líneas
SKILLS-PORTABLE/plantillas/protocolo/tablero.py  510 líneas   (202 líneas de diff)
```

**El portable no menciona `progreso/log/` ni una vez** (el activo, 4 veces). O sea que
no sabe ensamblar el log desde ficheros sueltos: solo entiende el log que vivía dentro
de `tablero-equipo.md`.

Esto es lo que hace que la deriva sea coherente en vez de un despiste suelto — el
script viejo y la prosa vieja encajan entre sí, así que un proyecto nuevo que instale
el kit **funcionará**, con el modelo malo, sin ningún síntoma de que hay otro mejor.

### 2. `equipo/que-toca.SKILL.md` — paso 6

El portable manda comitear el tablero y añadir la línea del log **al final del mismo
archivo compartido**:

```bash
python3 scripts/tablero.py --generar
# opcional, al final del archivo (append-only, NUNCA se genera):
git add progreso/tablero-equipo.md
```

El activo: la tabla está en `.gitignore` y no se comitea, y el log es **un fichero por
entrada** en `progreso/log/`. También falta en el portable la nota de que la excepción
«proyecto sin Project» exige sacar el tablero del `.gitignore`.

### 3. `equipo/cerrar-sesion.SKILL.md` — pasos 3 y 4

- **Paso 3:** el portable dice que `progreso/estado-actual.md` lleva «decisiones vivas,
  deudas anotadas, convenciones que cambiaron». El activo lo parte en un fichero por
  item (`progreso/decisiones/`, `progreso/pendientes/`) y advierte que estado-actual
  **casi nunca se toca**.
- **Paso 4:** mismo modelo viejo de tablero + log que en `que-toca`.

**Por qué importa exactamente esto:** el commit que lo cambió (`ac168ae`, 2026-07-28)
existe porque `estado-actual.md` era el último fichero que tocaban todas las ramas, y
el log dentro del tablero hizo chocar 3 PRs abiertos el mismo día. El kit portable
sigue repartiendo esa trampa a cualquier proyecto nuevo.

---

## La raíz: nada lo vigila

```
grep -rniE "SKILLS-PORTABLE" .github/workflows/ scripts/ .pre-commit-config.yaml
→ NADA
```

No hay guarda de CI, ni hook, ni script que compare las dos copias. `docs_check.py`
vigila que la documentación no referencie ficheros inexistentes, pero **no** que el kit
y el repo digan lo mismo. Por eso la deriva no dio ningún síntoma durante un día entero
de cambios: se actualiza `.claude/` porque es lo que se ejecuta, y nadie se acuerda de
la copia que no corre nunca aquí.

Mientras eso siga así, cada mejora del protocolo abre la brecha un poco más.

---

## Dos cosas menores que aparecieron de paso

- **El `description:` del frontmatter de `cerrar-sesion` está obsoleto en LAS DOS
  copias.** Dice «actualiza estado-actual + handoff + tablero», que contradice el
  cuerpo del propio fichero activo (estado-actual casi nunca se toca; el tablero no se
  comitea). Es lo que lee el modelo para decidir cuándo invocar la skill.
- ~~**El checkpoint de seguridad NO está derivado hoy**, pero lo estará en cuanto
  mergee #87, que reescribe esa sección solo en la copia activa.~~
  **RESUELTO el 2026-07-29, antes de llegar a existir.** #87 se mergeó llevando el
  checkpoint proporcional a **las dos** copias (la portable con `{{AREAS_CRITICAS}}`
  en vez de las rutas de este repo). Verificado en `main`: cero apariciones de
  «segunda red» en ninguna skill, y las dos tienen «proporcional, no un muro al
  final». Es el único caso hasta ahora en que la deriva se cerró en el mismo PR que
  la habría abierto — porque estaba anotada aquí y se miró antes de mergear.

---

## Salidas posibles

1. **Sincronizar los tres ficheros a mano** y seguir igual. Barato hoy, se vuelve a
   abrir a la siguiente mejora.
2. **Sincronizar + guarda en CI** que compare las dos copias ignorando
   `{{PLACEHOLDERS}}`, y falle si el contenido real difiere. Es lo que convierte esto
   en un problema que no vuelve. Lo caro es escribir la comparación tolerante a
   placeholders.
3. **Decidir que el kit se congela a propósito** y versionarlo (`VERSION` ya existe,
   dice qué). Entonces esto no es deuda sino política — pero hay que escribirlo, porque
   hoy nadie puede saber cuál de las dos copias manda.

Sin decidir. Si se abre issue, va también al Project con estado y label — que es
justamente lo que #94 impone desde que mergeó.

---

## Estado tras los merges del 2026-07-29

Re-medido contra `main` en `baab18b`, con #87, #91, #94 y #96 ya dentro:

| Hallazgo | Estado |
|---|---|
| Checkpoint de seguridad | **resuelto** — cerrado en #87, nunca llegó a derivar |
| `plantillas/protocolo/tablero.py` | **sigue igual**: 614 vs 510 líneas, 202 de diff, **cero** menciones a `progreso/log/` |
| `que-toca` paso 6 (comitear el tablero) | **sigue igual** — 2 apariciones de `git add progreso/tablero-equipo.md` |
| `cerrar-sesion` paso 3 (estado-actual como contenedor) | **sigue igual** |
| Nada vigila la sincronía | **sigue igual** |

**#94 no ensanchó la brecha:** añadió el mismo bloque del Project a las dos copias.
Que es la lección aprovechable de hoy — la deriva no se cierra sola, pero **sí se
evita si se mira antes de mergear**, y para eso hace falta que alguien se acuerde.
Ahí sigue el argumento de la guarda en CI: acordarse no escala.
