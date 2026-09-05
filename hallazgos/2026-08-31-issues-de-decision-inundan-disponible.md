# El tablero se llenó de decisiones y dejó de ofrecer trabajo

**Fecha:** 2026-08-31 · **Estado:** corregido en el kit (esta rama) · **Proyecto:** FARMICROW

Séptimo retorno proyecto→kit. Salió al mirar el Project de FARMICROW después de
cerrar dos subfases (T-001 y T-002) y con una tercera en revisión.

## Lo que se vio

**7 items en `Disponible` y ni una sola tarea `T-nnn`.** Todos eran decisiones o
vigilancias:

| # | Título | Qué era en realidad |
|---|---|---|
| 39 | Vigilar postcss: dos avisos HIGH sin fix aguas arriba | vigilancia, nada que hacer hasta que arreglen upstream |
| 41 | Decidir si la CSP con nonce merece ADR propio | decisión de diez minutos |
| 42 | Decidir quién manda en la versión de pnpm | decisión de diez minutos |
| 44 | Corregir el doc 03: son 30 tablas | corrección real, con guarda de CI detrás |
| 45 | ¿Las notas de ingreso y salida necesitan tabla propia? | gatea T-018 de verdad |
| 46 | Confirmar campos de `cuenta_pagar` y `pago` | gatea T-019 de verdad |
| 48 | Endurecer el aislamiento | **dependía de un PR todavía abierto** |

Las 35 tareas `T-nnn` restantes estaban en `Bloqueada`.

## Por qué importa

`/que-toca` elige **la de menor número** entre las `Disponible` sin dueño. Con ese
tablero, al siguiente dev que reclamara le tocaba **#39, «vigilar postcss»**: un
aviso sin trabajo dentro. El tablero estaba mandando gente a mirar avisos.

Y la #48 estaba `Disponible` dependiendo de un PR sin mergear: quien la cogiera
ramificaba de un `main` que aún no tenía el código que iba a endurecer.

## La causa, que no es la que parece

La primera lectura es «se están abriendo demasiados issues». No es eso. El mismo
cierre dejó **3 pendientes SIN issue** (`configuracion-clave-primaria-y-duplicados`,
`rastro-en-tablas-del-servicio`, `saldo-almacenado-en-cuenta-cobrar`) mientras
abría issue para otros — y uno de los tres, el del saldo, es un choque real entre
`docs/03` y un criterio de aceptación de T-002 que muerde varias fases después.

O sea: **no sobraban ni faltaban issues; cuál se convertía en issue salía
arbitrario**, porque el kit no daba ningún filtro. `cerrar-sesion` decía
literalmente *«TODOs que sobreviven a la subfase → issue en el Project»*, con el
único disparador «sobrevive a la subfase» — que es todo lo que anotas y no
arreglas. Y lo reforzaba con *«un pendiente sin issue es invisible para
`/que-toca`»*, que se lee como «ante la duda, abre issue».

**Esa frase se escribió para arreglar el fallo contrario** (los seis issues fuera
del Project, 2026-07-29). El péndulo se fue al otro extremo: antes había trabajo
real invisible, ahora hay ruido visible tapando el trabajo.

## Lo que se cambió

1. **Dos filtros antes de abrir issue** (`cerrar-sesion`, paso 3.3): ¿gatea o
   bloquea a otro? ¿es obligatorio aunque hoy no bloquee? Si no es ninguna de las
   dos, es contexto — `progreso/pendientes/` o `progreso/decisiones/` — no una
   tarjeta.
2. **`Disponible` pasa a ser una afirmación con trabajo detrás** (paso 4.2): mirar
   de qué depende (y si espera un PR sin mergear, va a `Bloqueada`), escribir a
   quién desbloquea en el `Depende de:` de esa otra, y mirar qué queda al terminar.
3. **Un mecanismo, no solo la regla** — que es el criterio de este repo:
   `estado.py` denuncia el tablero que solo ofrece avisos, y `/que-toca` explica
   qué hacer con ese aviso en vez de coger la de menor número por inercia.

## Límite conocido

El detector reconoce una tarea por el prefijo `T-nnn` del título, que es la
convención que `cerrar-sesion` ya exigía para poder cruzar el issue con el
backlog. **Un proyecto que numere sus tareas de otra forma no dispara el aviso.**
Es aceptable porque la convención la impone el propio kit, pero si algún día se
hace configurable, este detector es uno de los sitios a tocar.

Lo que el aviso **no** puede juzgar es si un issue concreto merecía existir: eso
son los dos filtros del paso 3.3, y son criterio humano. El mecanismo solo caza el
síntoma agregado — que no quede trabajo reclamable.
