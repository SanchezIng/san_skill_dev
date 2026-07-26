---
name: equipo-verificar
description: Runbook canónico para demostrar que un cambio funciona DE VERDAD, end-to-end, no solo que compila o pasa unit tests. Úsala cuando el dev diga "verifica", "pruébalo de verdad", "¿funciona?", antes de cerrar cambios que tocan {{AREAS_CRITICAS}}, o cuando /cerrar-sesion lo indique.
---

# /verificar — Esto funciona de verdad

Verificar = **observar el comportamiento real**, no inferirlo de los tests unitarios.
La escalera tiene 3 niveles; sube hasta el que el cambio amerite.

<!-- PLANTILLA: rellenar los placeholders con los comandos y el flujo REAL del
     proyecto. Si un nivel no aplica (p. ej. no hay servicio externo), bórralo
     en vez de dejarlo vacío: un runbook con pasos falsos es peor que ninguno. -->

{{NOTAS_ENTORNO}}
<!-- Ej.: "Windows: docker compose SIEMPRE desde PowerShell, nunca Git-Bash
     (MSYS corrompe las rutas de los volúmenes)." Trampas del entorno que hacen
     fallar el runbook por motivos ajenos al cambio. -->

## Nivel 1 — Suite completa (siempre)

```bash
{{CMD_LEVANTAR_STACK}}
{{CMD_TEST}}
```

Referencia sana: {{N_TESTS}} tests, ~{{DURACION_SUITE}}. Cualquier test rojo se
investiga — no hay "fallos conocidos" tolerados.

## Nivel 2 — E2E real ({{CUANDO_NIVEL_2}})

```bash
{{CMD_SEMBRAR_DEMO}}
{{SMOKE_E2E}}
```

{{DESCRIPCION_SMOKE}}
<!-- Qué cubre exactamente y qué NO. Si depende de un servicio externo
     inestable, dilo: "un timeout ahí NO es un fallo del cambio". -->

## Nivel 3 — Flujo manual ({{CUANDO_NIVEL_3}})

1. {{PASO_PREPARACION}}
2. Ejercitar el camino tocado:

```bash
{{EJEMPLO_LLAMADA}}
```

3. **Criterio de éxito observable:** {{CRITERIO_EXITO}}
<!-- Concreto y comprobable: estados, códigos, artefactos generados.
     "Funciona bien" no es un criterio. -->

## Qué NO es verificar

- "Compila" / análisis estático en verde — necesario, insuficiente.
- Probar solo el happy path cuando el cambio tocó el manejo de errores.
- Concluir desde un test que mockea justo la pieza que cambiaste.
- **Asumir el efecto colateral en vez de comprobarlo**: si vas a afirmar algo en
  un contrato público o en la documentación, ejecútalo primero. (En el piloto,
  una afirmación "obvia" sobre el efecto de un error resultó falsa al probarla
  y destapó un bug propio que nadie había visto.)
- **Confundir el éxito de la herramienta con el éxito de la tarea** — ver abajo.

## La regla que resume todo: verifica el EFECTO, no la invocación

Que un comando termine con exit 0 significa **"la herramienta hizo su trabajo"**,
nunca **"conseguí lo que quería"**. Son cosas distintas y se separan a menudo:

| Reportaba | Realidad | Qué habría hecho falta |
|---|---|---|
| CI en verde | El paso de auditoría era `continue-on-error` y no rompía nada | Mirar el informe, no que el paso corriera |
| Suite 36/36 | Los tests comparaban solo el cuerpo JSON; la línea de status filtraba información | Comparar la respuesta completa |
| "PR actualizado" | La API respondió OK, pero con contenido viejo: el fichero nunca se modificó | Releer el cuerpo del PR |

En los tres casos el paso **hizo su trabajo** y aun así el resultado era falso,
porque lo que se comprobaba no era lo que importaba. Ninguno se detecta mirando
códigos de salida; los tres se detectan **leyendo de vuelta el resultado**.

Regla práctica: si vas a escribir "hecho" en el reporte, pregúntate *qué observé
que lo demuestre*. Si la respuesta es "el comando no dio error", no lo has
verificado.

### Tres trampas de shell que producen justo esto

Aplican a cualquier proyecto; las dos últimas, sobre todo en entornos mixtos
(Windows con Bash y shell nativa conviviendo):

1. **Un salto de línea NO propaga el fallo.** `cmd_a` en una línea y `cmd_b` en
   la siguiente equivale a `cmd_a ; cmd_b`: si `cmd_a` muere, `cmd_b` corre igual
   y el exit final puede ser 0. En comandos multi-paso: `set -euo pipefail`, o
   encadena con `&&` los pasos que dependen entre sí.
2. **El `&&` mal colocado miente.** `cmd_b && echo "listo"` dice la verdad sobre
   `cmd_b` y nada sobre `cmd_a`. Encadena el mensaje al paso que de verdad
   importa, o mejor: no anuncies éxito, comprueba el efecto.
3. **Los shells POSIX y los binarios nativos no comparten mapa del disco.** Una
   ruta como `/tmp/x` puede ser inválida para un intérprete nativo aunque el
   shell la abra sin problema. Convierte la ruta antes de pasarla
   ({{CMD_CONVERTIR_RUTA}}) o trabaja con rutas nativas de punta a punta.

### Y una cuarta, de la misma familia: la lista truncada

Casi toda herramienta que **lista** cosas tiene un tope por defecto, y casi
ninguna avisa de que lo alcanzó. `gh issue list` y `gh project item-list` traen
30 elementos salvo que pidas más; `git log` pagina; muchas APIs devuelven 100 por
página. El comando termina con exit 0 y una respuesta bien formada: simplemente
**no es toda**.

Es la trampa más peligrosa de las cuatro porque el resultado parcial *parece*
completo, y las conclusiones que se sacan son del tipo "no hay ninguno" o "está
libre" — afirmaciones sobre lo que **no** existe, que es justo lo que una lista
recortada no puede sostener.

Regla: cuando cuentes o concluyas ausencia sobre una lista, **pide más de lo que
esperas y comprueba si te devolvieron exactamente el tope**. Si la cuenta iguala
el límite, asume que hay más. Y cuando se pueda, deja filtrar al servidor
(`--search "no:assignee"`) en vez de traértelo todo y filtrar tú.

## Al terminar

Reporta QUÉ observaste (estados, códigos, tiempos), no solo "todo bien". Si no
pudiste completar un nivel (dependencia externa caída), dilo explícito en el
handoff/PR: es un pendiente real, no un detalle.

Cada "hecho" del reporte debe apoyarse en algo observado. Un comando sin error
no es una observación: es una ausencia de queja.
