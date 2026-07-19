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

## Al terminar

Reporta QUÉ observaste (estados, códigos, tiempos), no solo "todo bien". Si no
pudiste completar un nivel (dependencia externa caída), dilo explícito en el
handoff/PR: es un pendiente real, no un detalle.
