#!/usr/bin/env python3
"""Guarda de integridad de `main` — el complemento detectivo de la proteccion de
rama, no su sustituto.

    Proteccion de rama  ->  el push se RECHAZA          (preventivo)
    Esta guarda         ->  el commit entro y se DENUNCIA (detectivo)

**Sirve en los DOS escenarios, y conviene saber en cual estas.** Nacio para repos
sin proteccion de rama disponible (privados en plan Free: la API responde 403
"Upgrade to GitHub Pro or make this repository public"), donde es la unica
barrera que hay. Cuando la proteccion de rama SI esta disponible, no sobra: sigue
cubriendo dos huecos que esa proteccion deja abiertos y que a nadie se le ocurre
vigilar (en el proyecto piloto se conservo por esto mismo al llegar GitHub Pro):

1. **El bypass del owner.** Si dejas `enforce_admins: false` —deliberado en la
   mayoria de equipos: el lead tiene que poder desatascar el repo sin depender de
   nadie— sus merges con `--admin` y sus pushes directos SI entran. No son una
   violacion, pero tampoco deben ser invisibles: se REGISTRAN y no rompen el CI.
   Un mecanismo que se pone rojo por acciones autorizadas ensena a ignorar el
   rojo, que es el fallo que este kit persigue en todas partes.
2. **Que la proteccion siga encendida.** Apagarla es un clic en una pantalla de
   ajustes: no deja rastro en el repo, no lo revisa nadie y no hay CI que lo
   note. Si un dia entra a `main` un commit sin PR, o mergeado sin aprobacion por
   alguien que NO es el owner, esta guarda se pone roja — y esa es la senal de
   que la barrera preventiva se cayo.

O sea: donde no hay proteccion de rama es la barrera entera, y donde la hay es el
detector de que esa barrera desaparecio. En ninguno de los dos casos denuncia al
owner por usar un bypass que el propio equipo dejo abierto a proposito.

Uso: python3 scripts/proteccion_main.py <sha_antes> <sha_ahora>
     (lo invoca .github/workflows/proteccion-main.yml en cada push a main)
Tests: python3 scripts/test_proteccion_main.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Commits que SI pueden ir directo a main. Depende del MODO del proyecto:
#
#   - Con GitHub Project (modo espejado, el que recomienda el kit): dejalo
#     VACIO. El candado vive en el assignee/estado del Project y el tablero viaja
#     en el PR, asi que ningun commit necesita saltarse el PR.
#   - Sin Project (el tablero markdown ES el candado, ver trabajo_en_equipo.md
#     §9): el reclamo tiene que publicarse al instante y por tanto va directo a
#     main. Ahi hace falta  ("chore(tablero):",).
#
# El defecto es vacio A PROPOSITO, aunque eso ponga en rojo el modo sin Project
# hasta que alguien lo rellene: un defecto permisivo abre un agujero silencioso
# (cualquiera empuja a main con ese prefijo y la guarda sigue verde), mientras
# que uno restrictivo falla ruidoso, se ve el primer dia y se corrige en una
# linea. Entre fallar en rojo y callar, esta guarda falla en rojo.
PREFIJOS_PERMITIDOS: tuple[str, ...] = ()

# Exigir >=1 aprobacion humana en el PR de origen. La regla del kit es
# "respondes por lo que tu Claude Code genero": sin revision, no se mergea.
#
# Se puede poner en False trabajando en SOLITARIO, porque GitHub no deja aprobar
# tu propio PR y si no la guarda seria inaplicable. Pero eso caduca solo: en
# cuanto entra un segundo colaborador humano, esta guarda EXIGE volver a True
# (ver `revision_desactivada_con_equipo`). "Acuerdate de subirlo cuando entre
# alguien" no es un mecanismo: es la clase de regla que este kit existe para
# eliminar.
EXIGIR_REVISION = True

# Excepcion DECLARADA a lo anterior. Si el equipo decide a sabiendas seguir con
# EXIGIR_REVISION=False aun teniendo mas de un colaborador (p.ej. el segundo
# tiene acceso pero no revisa aqui), se anota aqui y la guarda pasa a AVISAR en
# vez de fallar. Misma forma que la allowlist del audit y por la misma razon: una
# excepcion sin motivo escrito y sin caducidad deja de ser una excepcion y se
# convierte en el estado normal, que es el que nadie vuelve a mirar.
#
#   REVISION_RELAJADA = {"motivo": "...", "vence": "AAAA-MM-DD"}
#
# Mal declarada (sin motivo, sin fecha, caducada, o a mas de MAX_DIAS_EXCEPCION
# vista) NO silencia nada: la guarda falla igual.
REVISION_RELAJADA: dict[str, str] | None = None
MAX_DIAS_EXCEPCION = 180

SHA_NULO = "0" * 40

# Prefijo de los hallazgos que son de CONFIGURACION de la guarda, no de commits
# que se saltaron el protocolo. Los remedios son distintos y el resumen final los
# separa: contarlos juntos haria que el reporte mintiera sobre lo que paso.
MARCA_CONFIG = "configuracion: "

# Prefijo de lo que SE ANOTA pero NO es un fallo: el bypass del owner, que la
# proteccion de rama permite a proposito (`enforce_admins: false`).
# Va por el mismo canal que los fallos para no duplicar el recorrido de commits,
# y `main()` lo separa antes de decidir el codigo de salida.
MARCA_REGISTRO = "registro: "


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True,
                          text=True, check=True).stdout.strip()


def _api(ruta: str) -> list | dict | None:
    """GET a la API de GitHub. `None` = no se pudo consultar (404 de un commit
    que aun no esta publicado, falta de permisos, corte de red...).

    Punto unico de contacto con la red: los tests lo sustituyen para no depender
    de un repo real.
    """
    r = subprocess.run(["gh", "api", ruta], cwd=RAIZ, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout) if r.stdout.strip() else []


def commits_nuevos(antes: str, ahora: str) -> list[str]:
    if antes in ("", SHA_NULO):
        # Primer push de la rama: no hay rango anterior con el que comparar.
        return []
    return [c for c in _git("rev-list", f"{antes}..{ahora}").splitlines() if c]


def _asunto(sha: str) -> str:
    return _git("log", "-1", "--format=%s", sha)


def _es_merge(sha: str) -> bool:
    return len(_git("log", "-1", "--format=%P", sha).split()) > 1


def _humanos_con_acceso() -> list[str] | None:
    """Colaboradores humanos del repo. `None` = no se pudo consultar.

    Son los que PODRIAN aprobar un PR: la pregunta que decide si `EXIGIR_REVISION`
    en False sigue estando justificado. Los bots (dependabot y compañia) no
    cuentan — no revisan nada.
    """
    datos = _api("repos/{owner}/{repo}/collaborators?per_page=100")
    if datos is None:
        return None
    return sorted(
        c["login"] for c in datos
        if c.get("type") != "Bot" and not c.get("login", "").endswith("[bot]")
    )


def _owner_del_repo() -> str | None:
    """El login del owner del repo. `None` = no se pudo averiguar.

    Es quien la proteccion de rama exime a proposito (`enforce_admins: false`).
    Se consulta en vez de hardcodearse para que el kit siga siendo portable: un
    login pegado aqui seria una mentira en cuanto alguien clone el kit a otro repo.
    """
    datos = _api("repos/{owner}/{repo}")
    if not isinstance(datos, dict):
        return None
    return (datos.get("owner") or {}).get("login") or None


def _quien_mergeo(numero: int) -> str | None:
    """Quien pulso el merge del PR. `None` = no se pudo averiguar.

    Hace falta su propia llamada: `commits/{sha}/pulls` devuelve el PR en forma
    reducida y NO trae `merged_by` (comprobado contra la API, no supuesto).
    """
    datos = _api(f"repos/{{owner}}/{{repo}}/pulls/{numero}")
    if not isinstance(datos, dict):
        return None
    return (datos.get("merged_by") or {}).get("login") or None


def _excepcion_mal_declarada(exc: dict, hoy: date | None = None) -> str:
    """Cadena vacia si la excepcion es valida; el problema concreto si no.

    Una excepcion mal escrita no silencia nada: si lo hiciera, bastaria con poner
    cualquier cosa ahi para apagar la guarda, que es lo contrario de decidir a
    sabiendas.
    """
    hoy = hoy or date.today()
    if not exc.get("motivo"):
        return ("REVISION_RELAJADA no declara 'motivo'. Una excepcion sin razon "
                "escrita no se puede reevaluar: nadie sabra por que se acepto.")
    texto = exc.get("vence")
    if not texto:
        return ("REVISION_RELAJADA no declara 'vence'. Sin caducidad la excepcion "
                "se vuelve el estado normal, y el estado normal no se revisa.")
    try:
        vence = datetime.strptime(str(texto), "%Y-%m-%d").date()
    except ValueError:
        return f"REVISION_RELAJADA tiene 'vence' invalido ({texto}), formato AAAA-MM-DD."
    if vence < hoy:
        return (f"La excepcion de revision CADUCO el {texto}. Reevalua: o el "
                f"segundo colaborador revisa de verdad (EXIGIR_REVISION = True), "
                f"o su acceso sobra en este repo, o renuevas con motivo nuevo.")
    if vence > hoy + timedelta(days=MAX_DIAS_EXCEPCION):
        return (f"La excepcion vence el {texto}, a mas de {MAX_DIAS_EXCEPCION} dias "
                f"vista. Una excepcion tan larga deja de revisarse; acorta la fecha.")
    return ""


def revision_desactivada_con_equipo() -> list[str]:
    """La excusa de trabajar en solitario caduca cuando deja de ser cierto."""
    if EXIGIR_REVISION:
        return []
    humanos = _humanos_con_acceso()
    if humanos is None:
        # Aviso, no fallo: esto es una comprobacion de configuracion, no un
        # veredicto de seguridad. Poner el CI en rojo porque la API de
        # colaboradores no respondio seria una falsa alarma, y las falsas
        # alarmas es lo que ensena a ignorar el rojo.
        print("(AVISO: EXIGIR_REVISION=False y no se pudo comprobar si sigues "
              "en solitario. Si ya hay mas gente en el repo, subelo a True.)")
        return []
    if len(humanos) < 2:
        return []

    if REVISION_RELAJADA is not None:
        problema = _excepcion_mal_declarada(REVISION_RELAJADA)
        if problema:
            return [MARCA_CONFIG + problema]
        print(f"(AVISO: revision relajada a sabiendas hasta "
              f"{REVISION_RELAJADA.get('vence')} — {REVISION_RELAJADA.get('motivo')})")
        return []

    return [
        MARCA_CONFIG
        + f"EXIGIR_REVISION=False pero el repo ya tiene {len(humanos)} colaboradores "
        f"humanos ({', '.join(humanos)}).\n"
        f"        Esa excepcion existia solo para trabajar en solitario, porque "
        f"GitHub no deja aprobar el PR propio.\n"
        f"        Ya no es el caso: pon EXIGIR_REVISION = True en "
        f"scripts/proteccion_main.py.\n"
        f"        Mientras siga en False, esta guarda exige PR pero NO revision "
        f"— media barrera que aparenta ser entera."
    ]


def revisar(antes: str, ahora: str) -> list[str]:
    fallos: list[str] = revision_desactivada_con_equipo()
    owner: str | None = None
    owner_consultado = False
    for sha in commits_nuevos(antes, ahora):
        asunto = _asunto(sha)
        corto = sha[:8]

        if asunto.startswith(PREFIJOS_PERMITIDOS):
            continue
        if _es_merge(sha):
            # El merge del propio PR: lo que se juzga son sus commits.
            continue

        prs = _api(f"repos/{{owner}}/{{repo}}/commits/{sha}/pulls")
        if prs is None:
            # No se calla: un commit en main que no se puede verificar es un
            # agujero, y una guarda que se salta lo que no entiende no sirve.
            fallos.append(
                f"{corto} \"{asunto}\" no se pudo verificar contra GitHub "
                f"(commit sin publicar, permisos del token o API caida)"
            )
            continue
        if not prs:
            fallos.append(
                f"{corto} \"{asunto}\" llego a main sin PR (push directo)"
            )
            continue

        if not EXIGIR_REVISION:
            continue

        numero = prs[0].get("number")
        revisiones = _api(f"repos/{{owner}}/{{repo}}/pulls/{numero}/reviews")
        if revisiones is None:
            fallos.append(
                f"{corto} \"{asunto}\": no se pudieron leer las revisiones del PR #{numero}"
            )
            continue
        aprobaciones = [r for r in revisiones if r.get("state") == "APPROVED"]
        if aprobaciones:
            continue

        # Sin aprobacion. Antes de denunciar, hay que saber QUIEN lo mergeo: la
        # proteccion de rama exime al owner a proposito, asi que su
        # merge con `--admin` es autorizado y solo hay que dejarlo anotado.
        # Cualquier otro sin aprobacion significa que la barrera preventiva ya no
        # esta: ahi la guarda muerde, y ESA es su razon de existir hoy.
        if not owner_consultado:
            owner, owner_consultado = _owner_del_repo(), True
        quien = _quien_mergeo(numero)

        if quien is None or owner is None:
            # Fail-closed: si no se puede saber quien fue, no se concede el
            # beneficio de la duda. Una guarda que absuelve lo que no entiende
            # es peor que no tenerla, porque aparenta cubrir.
            fallos.append(
                f"{corto} \"{asunto}\" entro por el PR #{numero} SIN aprobacion y "
                f"no se pudo comprobar quien lo mergeo ni quien es el owner "
                f"(permisos del token o API caida): se trata como violacion"
            )
        elif quien == owner:
            fallos.append(
                MARCA_REGISTRO
                + f"{corto} \"{asunto}\" — PR #{numero} mergeado por el OWNER "
                f"({quien}) sin aprobacion. Bypass autorizado "
                f"(`enforce_admins: false`): queda anotado, no es un fallo"
            )
        else:
            fallos.append(
                f"{corto} \"{asunto}\" entro por el PR #{numero}, mergeado SIN "
                f"ninguna aprobacion por {quien}, que NO es el owner.\n"
                f"        La proteccion de rama deberia haberlo impedido: "
                f"comprueba si sigue activa\n"
                f"        (gh api repos/{{owner}}/{{repo}}/branches/main/protection)."
            )
    return fallos


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("Uso: proteccion_main.py <sha_antes> <sha_ahora>")
        return 2
    hallazgos = revisar(argv[1], argv[2])

    # Tres clases con remedios distintos, y solo dos son fallos: un commit que se
    # salto el protocolo se revisa o se revierte; una guarda mal configurada se
    # reconfigura; y un bypass del owner no se remedia, se deja anotado.
    # Contarlos juntos haria que el resumen mintiera sobre lo que acaba de pasar,
    # que es justo el falso exito que este kit persigue.
    registros = [f for f in hallazgos if f.startswith(MARCA_REGISTRO)]
    de_config = [f for f in hallazgos if f.startswith(MARCA_CONFIG)]
    de_commits = [
        f for f in hallazgos
        if not f.startswith((MARCA_REGISTRO, MARCA_CONFIG))
    ]

    for r in registros:
        print(f"REGISTRO {r[len(MARCA_REGISTRO):]}")
    for f in de_config + de_commits:
        print(f"FALLO {f}")

    if de_commits:
        print(f"\n{len(de_commits)} commit(s) entraron a main saltandose el protocolo.")
        print("`main` TIENE proteccion de rama, asi que esto no")
        print("deberia haber podido ocurrir: lo primero es comprobar si sigue")
        print("activa —gh api repos/{owner}/{repo}/branches/main/protection— y")
        print("luego revisar el cambio y, si procede, revertirlo.")
    if de_config:
        print(f"\n{len(de_config)} problema(s) de CONFIGURACION de la guarda.")
        print("Nadie se salto el protocolo: lo que pasa es que la guarda ya no")
        print("vigila lo que cree vigilar. Se arregla en scripts/proteccion_main.py.")
    if de_commits or de_config:
        return 1

    if registros:
        print(f"\nmain integra: {len(registros)} bypass del owner (autorizado), "
              f"0 violaciones.")
    else:
        print("main integra: todo llego por PR revisado.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
