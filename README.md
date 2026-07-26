# san_skill_dev

Catálogo personal de skills para Claude Code. **Una carpeta por skill o kit**, cada una
autocontenida con su propio README: se pueden añadir skills nuevas sin interferir con
las existentes.

## Catálogo

| Carpeta | Qué es |
|---|---|
| [`kit-construction-project/`](kit-construction-project/) | **Kit portable completo para arrancar proyectos**: `project-kickstart` (idea → documentación lista para desarrollar, con fases, seguridad OWASP y modo equipo), `secure-coding-guard` (guardián de seguridad al escribir código), las 3 skills del protocolo de equipo (`/que-toca`, `/cerrar-sesion`, `/verificar`), hook `SessionStart`, guardas de deriva doc↔realidad para CI e instalador. |
| [`formater-apa7-docxs/`](formater-apa7-docxs/) | **Skill empaquetada (`.skill`) para formatear documentos en APA 7.ª edición.** Se instala importando el paquete en Claude Code. |

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
de verdad, con evidencia y corrección. Vive **fuera** de las carpetas de los
kits a propósito: es memoria del catálogo, no contenido que deba viajar a cada
proyecto instalado.

## Convenciones del repo

- Cada skill/kit vive en su carpeta con README propio; este README raíz solo es el índice.
- Los mecanismos (hooks, guardas de CI) llevan tests al lado y se prueban en los
  dos sentidos: que dejan pasar lo correcto y que **muerden** lo incorrecto.
- Los kits son autocontenidos: no dependen de nada fuera de su carpeta.
- Recordatorio al instalar en un proyecto: cada skill va en
  `.claude/skills/<nombre>/SKILL.md` (carpeta = `name:` del frontmatter) — los
  instaladores de cada kit ya lo hacen bien.
