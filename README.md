# san_skill_dev

Catálogo personal de skills para Claude Code. **Una carpeta por skill o kit**, cada una
autocontenida con su propio README: se pueden añadir skills nuevas sin interferir con
las existentes.

## Catálogo

| Carpeta | Qué es |
|---|---|
| [`Creator_organizer_project/`](Creator_organizer_project/) | **Kit portable completo para arrancar proyectos**: `project-kickstart` (idea → documentación lista para desarrollar, con fases, seguridad OWASP y modo equipo), `secure-coding-guard` (guardián de seguridad al escribir código), las 3 skills del protocolo de equipo (`/que-toca`, `/cerrar-sesion`, `/verificar`), hook `SessionStart`, guardas de deriva doc↔realidad para CI e instalador. |

## Uso rápido (kit de proyectos)

Desde la raíz del proyecto donde quieras usarlo:

```bash
git clone https://github.com/SanchezIng/san_skill_dev.git
sh san_skill_dev/Creator_organizer_project/instalar.sh .
rm -rf san_skill_dev   # opcional: el instalador ya dejó el kit en SKILLS-PORTABLE/
```

Después abre Claude Code en la raíz del proyecto y di **"tengo una idea…"**.
Los detalles (modo `--protocolo` para proyectos existentes, placeholders, arranque de
GitHub) están en el [README del kit](Creator_organizer_project/README.md).

## Convenciones del repo

- Cada skill/kit vive en su carpeta con README propio; este README raíz solo es el índice.
- Los kits son autocontenidos: no dependen de nada fuera de su carpeta.
- Recordatorio al instalar en un proyecto: cada skill va en
  `.claude/skills/<nombre>/SKILL.md` (carpeta = `name:` del frontmatter) — los
  instaladores de cada kit ya lo hacen bien.
