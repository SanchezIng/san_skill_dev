# san_skill_dev

Catálogo personal de skills para Claude Code. **Una carpeta por skill o kit**, cada una
autocontenida con su propio README: se pueden añadir skills nuevas sin interferir con
las existentes.

## Catálogo

| Carpeta | Qué es |
|---|---|
| [`kit-construction-project/`](kit-construction-project/) | **Kit portable completo para arrancar proyectos**: `project-kickstart` (idea → documentación lista para desarrollar, con fases, seguridad OWASP y modo equipo), `secure-coding-guard` (guardián de seguridad al escribir código), las 3 skills del protocolo de equipo (`/que-toca`, `/cerrar-sesion`, `/verificar`), hook `SessionStart`, cuatro guardas de CI (deriva doc↔realidad, integridad de `main`, auditoría de dependencias y deriva de ramas), el tablero generado desde el GitHub Project e instalador con ruta de actualización. |
| [`formater-apa7-docxs/`](formater-apa7-docxs/) | **Skill empaquetada (`.skill`) para formatear documentos en APA 7.ª edición.** Se instala importando el paquete en Claude Code. |

## Estado (2026-07-26)

El [plan de mejora](plan-mejora.md) del kit está **cerrado**: nueve mejoras que
convierten en mecanismo lo que antes eran reglas escritas. El hilo común es el
criterio que las gobierna — *una regla sin mecanismo que la aplique no está
resuelta, y un mecanismo al que no se le ha visto **morder** no está verificado*.

Lo que el kit hace solo desde entonces:

| Antes era | Ahora |
|---|---|
| "Reinstala para actualizar" (y te borraba la configuración) | Manifiesto de hashes: lo que tocaste se conserva |
| "Nadie hace push directo a `main`" | Diagnóstico + ruleset, o guarda de CI que lo denuncia |
| 7 IDs de GraphQL pegados a mano | Se resuelven en ejecución, y tras mover se **relee** |
| Tablero mantenido a mano en tres sitios | Se genera desde el Project — pero el log de reclamos **jamás** |
| `npm audit` sin decir qué hacer con el resultado | Allowlist caducable que falla en cuatro casos |
| Ramas largas por diseño, sin instrumento | Aviso de deriva: uno por PR, que se edita en vez de repetirse |
| ~2.900 líneas de kickstart sin comprobación | Guarda de sus promesas, y **verificador del kit generado** antes de entregarlo |
| Guardas que llegan desactivadas y se olvidan | El hook de arranque las recuerda cada sesión, con el comando exacto |
| "Sube `EXIGIR_REVISION` cuando entre otro dev" | La guarda detecta al segundo colaborador y lo exige |

Los detalles de cada una, **incluidos sus límites conocidos**, están en
[`plan-mejora.md`](plan-mejora.md); qué se rompía en cada caso, en el
[`CHANGELOG.md`](CHANGELOG.md).

## Uso rápido (kit de proyectos)

Desde la raíz del proyecto donde quieras usarlo:

```bash
git clone https://github.com/SanchezIng/san_skill_dev.git
sh san_skill_dev/kit-construction-project/instalar.sh .
rm -rf san_skill_dev   # opcional: el instalador ya dejó el kit en SKILLS-PORTABLE/
```

Después abre Claude Code en la raíz del proyecto y di **"tengo una idea…"**.
Los detalles (modo `--protocolo` para proyectos existentes, placeholders, arranque de
GitHub) están en el [README del kit](kit-construction-project/README.md).

## Historial

[`CHANGELOG.md`](CHANGELOG.md) — qué cambió en cada kit y, sobre todo, **qué se
rompía**. Un changelog que solo lista archivos no evita repetir el error.

## Hallazgos de uso real

[`hallazgos/`](hallazgos/) recoge lo que se rompe al usar los kits en proyectos
de verdad, con evidencia y corrección. Los seis del 2026-07-22 están hoy
implementados, cada uno con su enlace a la mejora que lo cerró. Vive **fuera** de
las carpetas de los kits a propósito: es memoria del catálogo, no contenido que
deba viajar a cada proyecto instalado.

## Cómo se verifica esto

```bash
python3 kit-construction-project/kickstart_check.py        # coherencia del kickstart
sh      kit-construction-project/test_instalar.sh          # el ciclo real de instalación
```

Doce suites, **326 casos**, todas probando también que muerden. Cifras
remedidas ejecutando el 2026-08-15: la tabla llevaba cuatro caducadas y le
faltaba una suite entera, porque una tabla escrita a mano envejece con cada PR
que añade un caso. Cada suite imprime su recuento al correr — esa es la buena:

| Suite | Casos | Qué protege |
|---|---|---|
| `test_tablero.py` | 36 | IDs del Project, mover tarjetas, generar el tablero sin pisar el log |
| `test_estado.py` | 15 | las tres comprobaciones del reclamo: tope que miente, titulo vivo del issue y las dos formas de ser invisible |
| `test_kickstart_check.py` | 36 | que la guarda del kickstart no acuse en falso ni calle |
| `test_audit_check.py` | 26 | los cuatro modos de fallo de la allowlist, y fallar cerrado |
| `test_instalar.sh` | 44 | instalar → configurar → actualizar ×2 → reconciliar, que el repaso llegue en las tres rutas y que un proyecto ya configurado salga limpio |
| `test_verificar_kit.py` | 41 | que el kit **generado** tenga lo prometido, sin placeholders sueltos, sin órdenes que su entorno no pueda cumplir, con los ítems post-merge del DoD marcados — y que las plantillas del kit **instalado** no cuenten como fallos |
| `test_deriva_ramas.py` | 18 | avisar una vez por PR, y no callar cuando no pudo mirar |
| `test_deriva_kit.py` | 18 | en qué se ha desviado un proyecto respecto al kit, separando lo configurado de lo divergente |
| `test_proteccion_main.py` | 25 | commits sin PR, y que la excepción de trabajar solo caduque |
| `test_arranque.sh` | 32 | que las guardas sin activar no se queden pendientes en silencio |
| `test_docs_check.py` | 26 | enlaces rotos y coherencia backlog↔issues |
| `test_recordar-seguridad.sh` | 9 | el hook de seguridad al tocar código |

Las corre [`.github/workflows/kit.yml`](.github/workflows/kit.yml) en cada push y
PR. Las guardas se ejecutan **antes** que lo que vigilan: una guarda rota que dice
"todo OK" es peor que no tenerla.

## Convenciones del repo

- Cada skill/kit vive en su carpeta con README propio; este README raíz solo es el índice.
- Los mecanismos (hooks, guardas de CI) llevan tests al lado y se prueban en los
  dos sentidos: que dejan pasar lo correcto y que **muerden** lo incorrecto.
- Los kits son autocontenidos: no dependen de nada fuera de su carpeta.
- **Todo entra a `main` por PR.** No es solo una regla: `scripts/proteccion_main.py`
  lo comprueba en cada push a `main` ([workflow](.github/workflows/proteccion-main.yml)).
  Este repo es privado con plan Free, donde la protección de rama **no existe**, así
  que la barrera es detectiva, no preventiva — y eso se dice en voz alta en vez de
  fingir equivalencia. `EXIGIR_REVISION` está en `False` mientras se trabaje en
  solitario (GitHub no deja aprobar el PR propio): **subirlo a `True` al entrar un
  segundo dev**.
- Recordatorio al instalar en un proyecto: cada skill va en
  `.claude/skills/<nombre>/SKILL.md` (carpeta = `name:` del frontmatter) — los
  instaladores de cada kit ya lo hacen bien.
