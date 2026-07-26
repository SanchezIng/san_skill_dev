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
    spec = importlib.util.spec_from_file_location("proteccion_main", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.RAIZ = raiz
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


def api_simulada(prs_por_commit=None, revisiones_por_pr=None):
    """prs_por_commit: {sha_corto_o_'*': [{'number': N}]}; ausente = sin PR."""
    prs_por_commit = prs_por_commit or {}
    revisiones_por_pr = revisiones_por_pr or {}

    def _api(ruta: str):
        if "/pulls/" in ruta and ruta.endswith("/reviews"):
            numero = int(ruta.split("/pulls/")[1].split("/")[0])
            return revisiones_por_pr.get(numero, [])
        if "/commits/" in ruta and ruta.endswith("/pulls"):
            sha = ruta.split("/commits/")[1].rsplit("/", 1)[0]
            if sha in prs_por_commit:
                return prs_por_commit[sha]
            return prs_por_commit.get("*", [])
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
    mod._api = api_simulada({"*": [{"number": 9}]}, {9: COMENTADO})
    fallos = mod.revisar(base, sha)
    assert len(fallos) == 1, fallos
    assert "SIN ninguna aprobacion" in fallos[0] and "#9" in fallos[0]


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
