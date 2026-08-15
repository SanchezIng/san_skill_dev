#!/usr/bin/env python3
"""Tests de la guarda de integridad de main.

Se monta un repo git REAL (commits, merges, mensajes de verdad) y se simula solo
la API de GitHub, que es lo unico que no se puede tener en local. Cada regla se
prueba en los dos sentidos: que deja pasar lo legitimo y que MUERDE lo que no.

Uso: python3 scripts/test_proteccion_main.py     (exit 1 si algun caso falla)
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "proteccion_main.py"


def cargar(raiz: Path):
    """Carga el modulo con una configuracion FIJA de test.

    No se heredan `PREFIJOS_PERMITIDOS`, `EXIGIR_REVISION` ni `REVISION_RELAJADA`
    del archivo desplegado: cada proyecto los ajusta a su modo, y unos tests que
    cambian de resultado segun la configuracion del repo no prueban nada. Los
    casos que dependen de esos valores los fijan ellos mismos.

    (Se aprendio ejecutando: al declarar una excepcion de revision en este repo,
    dos casos que exigian el comportamiento estricto empezaron a pasar por la
    excepcion. Los tests median la configuracion local, no la regla.)
    """
    spec = importlib.util.spec_from_file_location("proteccion_main", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.RAIZ = raiz
    mod.PREFIJOS_PERMITIDOS = ("chore(tablero):",)
    mod.EXIGIR_REVISION = True
    mod.REVISION_RELAJADA = None
    return mod


class RepoDePrueba:
    """Repo git real: los SHAs, los merges y los asuntos son autenticos."""

    def __init__(self, tmp: Path):
        self.raiz = tmp
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.email", "t@t.t")
        self._git("config", "user.name", "test")

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.raiz, capture_output=True,
                              text=True, check=True).stdout.strip()

    def commit(self, asunto: str, archivo: str = "a.txt") -> str:
        p = self.raiz / archivo
        p.write_text((p.read_text(encoding="utf-8") if p.exists() else "") + asunto + "\n",
                     encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", asunto)
        return self._git("rev-parse", "HEAD")

    def merge_de_rama(self, rama: str, asunto: str) -> str:
        """Simula el merge commit que crea GitHub al cerrar un PR."""
        self._git("checkout", "-q", "-b", rama)
        self.commit(f"feat: trabajo de {rama}", archivo=f"{rama}.txt")
        self._git("checkout", "-q", "main")
        self._git("merge", "-q", "--no-ff", rama, "-m", asunto)
        return self._git("rev-parse", "HEAD")

    def sha(self, ref: str = "HEAD") -> str:
        return self._git("rev-parse", ref)


CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


def api_simulada(prs_por_commit=None, revisiones_por_pr=None, colaboradores=None,
                 owner=None, mergeado_por=None):
    """prs_por_commit: {sha_corto_o_'*': [{'number': N}]}; ausente = sin PR.

    `colaboradores`: lista de dicts como los de la API, o `None` para simular
    que la consulta no se pudo hacer.
    `owner`: login del owner del repo, o `None` = no se pudo averiguar.
    `mergeado_por`: {numero_de_pr: login}, para `merged_by` del PR. Un PR ausente
    simula que no se pudo saber quien lo mergeo.
    """
    prs_por_commit = prs_por_commit or {}
    revisiones_por_pr = revisiones_por_pr or {}
    mergeado_por = mergeado_por or {}

    def _api(ruta: str):
        if "/collaborators" in ruta:
            return colaboradores
        if "/pulls/" in ruta and ruta.endswith("/reviews"):
            numero = int(ruta.split("/pulls/")[1].split("/")[0])
            return revisiones_por_pr.get(numero, [])
        if "/commits/" in ruta and ruta.endswith("/pulls"):
            sha = ruta.split("/commits/")[1].rsplit("/", 1)[0]
            if sha in prs_por_commit:
                return prs_por_commit[sha]
            return prs_por_commit.get("*", [])
        if "/pulls/" in ruta:                      # detalle del PR: merged_by
            numero = int(ruta.rsplit("/pulls/", 1)[1])
            if numero not in mergeado_por:
                return []                          # no se pudo averiguar
            return {"merged_by": {"login": mergeado_por[numero]}}
        if ruta == "repos/{owner}/{repo}":          # owner del repo
            return {"owner": {"login": owner}} if owner else []
        return []
    return _api


APROBADO = [{"state": "APPROVED"}]
COMENTADO = [{"state": "COMMENTED"}]


@caso("commit por PR aprobado: pasa")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: algo legitimo")
    mod = cargar(tmp)
    mod._api = api_simulada({"*": [{"number": 7}]}, {7: APROBADO})
    assert mod.revisar(base, sha) == [], mod.revisar(base, sha)


@caso("push directo sin PR: MUERDE")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("fix: parche urgente a main")
    mod = cargar(tmp)
    mod._api = api_simulada({})  # ningun PR asociado
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1, fallos
    assert "sin PR (push directo)" in fallos[0]
    assert "parche urgente" in fallos[0]


@caso("PR mergeado SIN aprobacion: MUERDE")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: sin revisar")
    mod = cargar(tmp)
    mod._api = api_simulada({"*": [{"number": 9}]}, {9: COMENTADO},
                            owner="jefa", mergeado_por={9: "otro_dev"})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1, fallos
    assert "SIN ninguna aprobacion" in fallos[0] and "#9" in fallos[0]
    assert "NO es el owner" in fallos[0], fallos[0]
    # Y orienta hacia la causa real: si un NO-owner pudo mergear sin aprobacion,
    # la proteccion de rama no estaba puesta.
    assert "branches/main/protection" in fallos[0], fallos[0]


# --- El bypass del owner ---------------------------------------
#
# `enforce_admins: false` exime al owner a proposito: tiene que poder desatascar
# el repo sin depender de nadie. Sus merges con `--admin` NO son violaciones, y
# ponerse rojo por ellos entrenaria al equipo a ignorar el rojo — que es el fallo
# que este kit persigue en todas partes. Se anotan y se sigue.

@caso("PR sin aprobacion mergeado por el OWNER: se REGISTRA y no falla")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("docs: cierre del lead")
    mod = cargar(tmp)
    mod._api = api_simulada({"*": [{"number": 116}]}, {116: COMENTADO},
                            owner="jefa", mergeado_por={116: "jefa"})
    hallazgos = mod.revisar(base, sha)
    assert len(hallazgos) == 1, hallazgos
    assert hallazgos[0].startswith(mod.MARCA_REGISTRO), hallazgos[0]
    assert "OWNER (jefa)" in hallazgos[0] and "#116" in hallazgos[0]
    # Lo que de verdad importa: exit 0.
    assert mod.main(["x", base, sha]) == 0


@caso("un REGISTRO no tapa un FALLO que venga en el mismo push")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    del_owner = repo.commit("docs: cierre del lead")
    a_pelo = repo.commit("fix: parche directo")
    mod = cargar(tmp)
    mod._api = api_simulada({del_owner[:40]: [{"number": 116}]}, {116: COMENTADO},
                            owner="jefa", mergeado_por={116: "jefa"})
    hallazgos = mod.revisar(base, a_pelo)
    registros = [h for h in hallazgos if h.startswith(mod.MARCA_REGISTRO)]
    fallos = [h for h in hallazgos if not h.startswith(mod.MARCA_REGISTRO)]
    assert len(registros) == 1, hallazgos
    assert len(fallos) == 1 and "sin PR (push directo)" in fallos[0], fallos
    # Un solo fallo real basta para el rojo, haya los registros que haya.
    assert mod.main(["x", base, a_pelo]) == 1


@caso("no se puede saber quien mergeo: FAIL-CLOSED, se trata como violacion")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: quien sabe")
    mod = cargar(tmp)
    # merged_by no consultable (PR ausente del mapa) aunque el owner si se sepa:
    # absolver por falta de datos convertiria la guarda en un adorno.
    mod._api = api_simulada({"*": [{"number": 12}]}, {12: COMENTADO},
                            owner="jefa", mergeado_por={})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1, fallos
    assert not fallos[0].startswith(mod.MARCA_REGISTRO), fallos[0]
    assert "se trata como violacion" in fallos[0], fallos[0]


@caso("tampoco absuelve si el que no se sabe es el OWNER del repo")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: sin owner conocido")
    mod = cargar(tmp)
    mod._api = api_simulada({"*": [{"number": 13}]}, {13: COMENTADO},
                            owner=None, mergeado_por={13: "jefa"})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1 and "se trata como violacion" in fallos[0], fallos


@caso("el PR aprobado no gasta llamadas de merged_by (no le hacen falta)")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: revisado de verdad")
    mod = cargar(tmp)
    rutas = []
    interna = api_simulada({"*": [{"number": 7}]}, {7: APROBADO}, owner="jefa")

    def espia(ruta):
        rutas.append(ruta)
        return interna(ruta)

    mod._api = espia
    assert mod.revisar(base, sha) == []
    assert not any(r == "repos/{owner}/{repo}" for r in rutas), rutas


@caso("commit del tablero (candado sin Project): permitido")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("chore(tablero): reclamar T-014")
    mod = cargar(tmp)
    mod._api = api_simulada({})
    assert mod.revisar(base, sha) == [], mod.revisar(base, sha)


@caso("con Project (sin prefijos permitidos) el tablero YA no se cuela")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("chore(tablero): reclamar T-014")
    mod = cargar(tmp)
    mod.PREFIJOS_PERMITIDOS = ()   # configuracion del modo espejado
    mod._api = api_simulada({})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1 and "push directo" in fallos[0], fallos


@caso("merge commit del PR: no se juzga (se juzgan sus commits)")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    repo.merge_de_rama("feat-x", "Merge pull request #3 from feat-x")
    mod = cargar(tmp)
    # El commit de dentro de la rama si tiene PR aprobado; el merge se ignora.
    mod._api = api_simulada({"*": [{"number": 3}]}, {3: APROBADO})
    assert mod.revisar(base, repo.sha()) == [], mod.revisar(base, repo.sha())


@caso("primer push de la rama (sha antes nulo): no rompe")
def _(tmp):
    repo = RepoDePrueba(tmp)
    sha = repo.commit("chore: inicial")
    mod = cargar(tmp)
    mod._api = api_simulada({})
    assert mod.revisar("0" * 40, sha) == []


@caso("varios commits: denuncia solo los culpables")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    bueno = repo.commit("feat: revisado")
    repo.commit("fix: colado a main")
    mod = cargar(tmp)
    mod._api = api_simulada({bueno: [{"number": 1}]}, {1: APROBADO})
    fallos = mod.revisar(base, repo.sha())
    assert len(fallos) == 1 and "colado a main" in fallos[0], fallos


@caso("la API falla (commit sin publicar / sin permisos): lo dice, no revienta")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: algo")
    mod = cargar(tmp)
    mod._api = lambda ruta: None          # gh devuelve error
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1, fallos
    assert "no se pudo verificar" in fallos[0], fallos


@caso("EXIGIR_REVISION=False (dev en solitario): exige PR, no aprobacion")
def _(tmp):
    # GitHub no deja aprobar tu propio PR: con un solo dev, exigir aprobacion
    # bloquearia el 100% del trabajo. El PR si se sigue exigiendo.
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    con_pr = repo.commit("feat: por PR sin aprobar")
    mod = cargar(tmp)
    mod.EXIGIR_REVISION = False
    mod._api = api_simulada({con_pr: [{"number": 4}]}, {4: COMENTADO},
                            colaboradores=[{"login": "solo", "type": "User"}])
    assert mod.revisar(base, con_pr) == [], mod.revisar(base, con_pr)

    # Y aun asi, un push directo sigue muriendo: se relaja la revision, no el PR.
    sin_pr = repo.commit("fix: directo a main")
    fallos = mod.revisar(con_pr, sin_pr)
    assert len(fallos) == 1 and "push directo" in fallos[0], fallos


# --- La excepcion de trabajar en solitario caduca sola -----------------------
#
# El agujero que cierran estos casos no es tecnico, es humano: "acuerdate de
# subir EXIGIR_REVISION cuando entre alguien" es exactamente la clase de regla
# sin mecanismo que este kit existe para eliminar.

@caso("SEGUNDO DEV con EXIGIR_REVISION=False: MUERDE y dice quienes son")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: algo")
    mod = cargar(tmp)
    mod.EXIGIR_REVISION = False
    mod._api = api_simulada({"*": [{"number": 4}]}, colaboradores=[
        {"login": "ana", "type": "User"}, {"login": "luis", "type": "User"}])
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1, fallos
    assert "ana, luis" in fallos[0], fallos
    assert "EXIGIR_REVISION = True" in fallos[0], "hay que decir exactamente que hacer"
    assert "media barrera" in fallos[0]


@caso("los BOTS no cuentan como segundo dev (dependabot no revisa nada)")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: algo")
    mod = cargar(tmp)
    mod.EXIGIR_REVISION = False
    mod._api = api_simulada({"*": [{"number": 4}]}, colaboradores=[
        {"login": "solo", "type": "User"},
        {"login": "dependabot[bot]", "type": "Bot"},
        {"login": "renovate[bot]", "type": "User"}])   # type mal puesto: vale el sufijo
    assert mod.revisar(base, sha) == [], mod.revisar(base, sha)


@caso("no se pudo consultar colaboradores: AVISA, no tumba el CI")
def _(tmp):
    import contextlib
    import io
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: algo")
    mod = cargar(tmp)
    mod.EXIGIR_REVISION = False
    mod._api = api_simulada({"*": [{"number": 4}]}, colaboradores=None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fallos = mod.revisar(base, sha)
    # Es una comprobacion de CONFIGURACION, no un veredicto de seguridad: una
    # falsa alarma aqui ensena a ignorar el rojo, que es lo contrario del fin.
    assert fallos == [], fallos
    assert "AVISO" in buf.getvalue(), buf.getvalue()


def con_equipo(tmp, relajada="sin tocar"):
    """Repo con 2 humanos, EXIGIR_REVISION=False y la excepcion que se indique."""
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: algo")
    mod = cargar(tmp)
    mod.EXIGIR_REVISION = False
    if relajada != "sin tocar":
        mod.REVISION_RELAJADA = relajada
    mod._api = api_simulada({"*": [{"number": 4}]}, colaboradores=[
        {"login": "ana", "type": "User"}, {"login": "luis", "type": "User"}])
    return mod, base, sha


def dentro_de(dias):
    from datetime import date, timedelta
    return (date.today() + timedelta(days=dias)).isoformat()


@caso("excepcion DECLARADA y vigente: avisa en vez de fallar")
def _(tmp):
    import contextlib
    import io
    mod, base, sha = con_equipo(tmp, {"motivo": "el segundo no revisa aqui",
                                      "vence": dentro_de(30)})
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fallos = mod.revisar(base, sha)
    assert fallos == [], fallos
    assert "AVISO" in buf.getvalue() and "el segundo no revisa aqui" in buf.getvalue()


@caso("excepcion CADUCADA: vuelve a MORDER (no se vuelve permanente)")
def _(tmp):
    mod, base, sha = con_equipo(tmp, {"motivo": "x", "vence": "2020-01-01"})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1 and "CADUCO" in fallos[0], fallos
    assert "su acceso sobra" in fallos[0], "hay que decir las salidas posibles"


@caso("excepcion sin motivo: no silencia nada")
def _(tmp):
    mod, base, sha = con_equipo(tmp, {"vence": dentro_de(30)})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1 and "no declara 'motivo'" in fallos[0], fallos


@caso("excepcion sin caducidad: no silencia nada")
def _(tmp):
    mod, base, sha = con_equipo(tmp, {"motivo": "porque si"})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1 and "no declara 'vence'" in fallos[0], fallos


@caso("excepcion a 5 anios vista: no silencia nada (la caducidad seria humo)")
def _(tmp):
    mod, base, sha = con_equipo(tmp, {"motivo": "x", "vence": dentro_de(1825)})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1 and "dias vista" in fallos[0], fallos


@caso("el resumen NO llama 'commit que se salto el protocolo' a un fallo de config")
def _(tmp):
    # La primera ejecucion real de esta regla reporto "1 commit(s) entraron a main
    # saltandose el protocolo" cuando lo que pasaba era que la guarda estaba mal
    # configurada. Nadie se habia saltado nada: el resumen mentia sobre el hecho.
    import contextlib
    import io
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: entro por PR, todo correcto")
    mod = cargar(tmp)
    mod.EXIGIR_REVISION = False
    mod._api = api_simulada({"*": [{"number": 4}]}, colaboradores=[
        {"login": "ana", "type": "User"}, {"login": "luis", "type": "User"}])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        codigo = mod.main(["prog", base, sha])
    salida = buf.getvalue()
    assert codigo == 1, codigo
    assert "CONFIGURACION" in salida, salida
    assert "commit(s) entraron a main" not in salida, \
        "ningun commit se salto el protocolo: decirlo seria un falso positivo"


@caso("con EXIGIR_REVISION=True ni se pregunta por los colaboradores")
def _(tmp):
    repo = RepoDePrueba(tmp)
    base = repo.commit("chore: inicial")
    sha = repo.commit("feat: algo")
    mod = cargar(tmp)
    consultas = []
    mod._api = lambda ruta: (consultas.append(ruta) or
                             ([{"number": 4}] if ruta.endswith("/pulls") else APROBADO))
    mod.revisar(base, sha)
    assert not any("collaborators" in r for r in consultas), consultas


def main() -> int:
    fallidos = 0
    for nombre, prueba in CASOS:
        tmp = Path(tempfile.mkdtemp())
        try:
            prueba(tmp)
            print(f"  ok    {nombre}")
        except AssertionError as e:
            fallidos += 1
            print(f"  FALLO {nombre}\n        {e}")
        except Exception as e:  # noqa: BLE001
            fallidos += 1
            print(f"  ERROR {nombre}\n        {type(e).__name__}: {e}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{len(CASOS) - fallidos}/{len(CASOS)} casos OK")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
