#!/usr/bin/env python3
"""Tests de la guarda deriva_ramas.py.

Por que existen: esta guarda comenta en los PRs de gente real. Sus dos formas de
fallar son opuestas y las dos la inutilizan — si spamea, se filtra y deja de
leerse; si calla cuando deberia hablar, no vigila nada. Aqui se prueban ambas,
mas la tercera que es peor que las dos: quedarse callada porque NO PUDO mirar y
que eso se lea como "no hay deriva".

Se simula unicamente la frontera con `gh`; el resto (umbral, redaccion del
comentario, decidir entre crear y editar) es el real.

Uso: python3 scripts/test_deriva_ramas.py     (exit 1 si algun caso falla)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "deriva_ramas.py"


def cargar():
    spec = importlib.util.spec_from_file_location("deriva_ramas", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class GhSimulado:
    """Sustituye a `gh`. Registra lo que se le pide para poder afirmarlo."""

    def __init__(self, prs, detras, comentarios=None, falla=None):
        self.prs = prs
        self.detras = detras                      # {rama: commits por detras}
        self.comentarios = comentarios or {}      # {numero: [ {id, body} ]}
        self.falla = falla                        # subcadena del comando que peta
        self.publicados = []                      # (numero, cuerpo)
        self.editados = []                        # (id, cuerpo)

    def __call__(self, cmd, **kw):
        texto = " ".join(cmd)
        if self.falla and self.falla in texto:
            return subprocess.CompletedProcess(cmd, 1, "", "gh: algo se rompio")

        if cmd[1] == "pr" and cmd[2] == "list":
            return self._ok(json.dumps(self.prs))

        if "/compare/" in texto:
            rama = texto.split("...", 1)[1].split(" ", 1)[0]
            valor = self.detras.get(rama)
            if valor is None:
                return self._ok(json.dumps({"ahead": 1}))   # sin 'behind'
            return self._ok(json.dumps({"behind": valor, "ahead": 1}))

        if "--method POST" in texto or ("issues/" in texto and "--method" in texto
                                        and "POST" in texto):
            numero = int(texto.split("issues/")[1].split("/")[0])
            self.publicados.append((numero, self._cuerpo(cmd)))
            return self._ok("{}")

        if "--method" in texto and "PATCH" in texto:
            ident = int(texto.split("issues/comments/")[1].split(" ")[0])
            self.editados.append((ident, self._cuerpo(cmd)))
            return self._ok("{}")

        if "/comments" in texto:
            numero = int(texto.split("issues/")[1].split("/")[0])
            return self._ok(json.dumps(self.comentarios.get(numero, [])))

        raise AssertionError(f"comando no simulado: {texto}")

    @staticmethod
    def _cuerpo(cmd):
        for i, a in enumerate(cmd):
            if a == "-f" and cmd[i + 1].startswith("body="):
                return cmd[i + 1][len("body="):]
        return ""

    @staticmethod
    def _ok(salida):
        return subprocess.CompletedProcess(["gh"], 0, salida, "")


def pr(numero, rama, base="main", borrador=False, mergeable="MERGEABLE"):
    return {"number": numero, "title": f"PR {numero}", "url": f"http://x/{numero}",
            "baseRefName": base, "headRefName": rama, "isDraft": borrador,
            "createdAt": "2026-07-20T10:00:00Z", "mergeable": mergeable}


def preparar(prs, detras, comentarios=None, falla=None, umbral=15):
    mod = cargar()
    mod.UMBRAL_COMMITS = umbral
    gh = GhSimulado(prs, detras, comentarios, falla)
    mod.subprocess.run = gh
    return mod, gh


CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


# --- Hablar cuando toca, callar cuando no -----------------------------------

@caso("rama por encima del umbral: comenta UNA vez")
def _():
    mod, gh = preparar([pr(1, "a")], {"a": 20})
    reporte = mod.revisar()
    assert len(gh.publicados) == 1, gh.publicados
    assert "20 commits por detrás" in gh.publicados[0][1]
    assert "comentado" in reporte[0]


@caso("rama al dia: no comenta nada (el silencio tambien informa)")
def _():
    mod, gh = preparar([pr(1, "a")], {"a": 0})
    assert mod.revisar() == []
    assert gh.publicados == []


@caso("justo en el umbral: avisa (>=, no >)")
def _():
    mod, gh = preparar([pr(1, "a")], {"a": 15}, umbral=15)
    mod.revisar()
    assert len(gh.publicados) == 1


@caso("un commit por debajo del umbral: calla")
def _():
    mod, gh = preparar([pr(1, "a")], {"a": 14}, umbral=15)
    mod.revisar()
    assert gh.publicados == []


@caso("borradores: se saltan por defecto (trabajo declarado en curso)")
def _():
    mod, gh = preparar([pr(1, "a", borrador=True)], {"a": 40})
    assert mod.revisar() == []
    assert gh.publicados == []


@caso("borradores: se avisan si el equipo lo activa")
def _():
    mod, gh = preparar([pr(1, "a", borrador=True)], {"a": 40})
    mod.AVISAR_EN_BORRADORES = True
    mod.revisar()
    assert len(gh.publicados) == 1


# --- Un aviso por PR, no uno por ejecucion ----------------------------------

@caso("SEGUNDA PASADA: edita el comentario, NO publica otro")
def _():
    viejo = {"id": 900, "body": "algo\n" + cargar().MARCA + "\nviejo"}
    mod, gh = preparar([pr(1, "a")], {"a": 30}, comentarios={1: [viejo]})
    reporte = mod.revisar()
    assert gh.publicados == [], "no puede notificar dos veces por lo mismo"
    assert len(gh.editados) == 1 and gh.editados[0][0] == 900
    assert "30 commits" in gh.editados[0][1], "la cifra tiene que quedar al dia"
    assert "actualizado" in reporte[0]


@caso("nada que cambiar: ni publica ni edita (no toca la API por gusto)")
def _():
    mod, _g = preparar([pr(1, "a")], {"a": 30})
    cuerpo = mod.comentario(pr(1, "a"), 30, mod._dias("2026-07-20T10:00:00Z"))
    mod2, gh2 = preparar([pr(1, "a")], {"a": 30},
                         comentarios={1: [{"id": 900, "body": cuerpo}]})
    reporte = mod2.revisar()
    assert gh2.publicados == [] and gh2.editados == []
    assert "sin cambios" in reporte[0]


@caso("comentarios de HUMANOS no se confunden con el del bot")
def _():
    humano = {"id": 1, "body": "esto va 30 commits por detras, ojo"}
    mod, gh = preparar([pr(1, "a")], {"a": 30}, comentarios={1: [humano]})
    mod.revisar()
    assert len(gh.publicados) == 1, "debe crear el suyo, no editar el del humano"
    assert gh.editados == []


@caso("la rama se pone al dia: el aviso viejo se corrige, no se queda mintiendo")
def _():
    viejo = {"id": 900, "body": cargar().MARCA + "\nva 30 commits por detrás"}
    mod, gh = preparar([pr(1, "a")], {"a": 1}, comentarios={1: [viejo]})
    mod.revisar()
    assert gh.publicados == []
    assert len(gh.editados) == 1
    assert "resuelto" in gh.editados[0][1], gh.editados[0][1]


# --- No poder mirar NO es "no hay deriva" -----------------------------------

@caso("`gh pr list` falla: MUERDE (no se reporta 'sin deriva')")
def _():
    mod, _gh = preparar([pr(1, "a")], {"a": 30}, falla="pr list")
    try:
        mod.revisar()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeGuarda as e:
        assert "no se puede afirmar que no hay deriva" in str(e), e


@caso("la comparacion no trae 'behind_by': no se inventa un 0")
def _():
    mod, _gh = preparar([pr(1, "desconocida")], {})
    try:
        mod.revisar()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeGuarda as e:
        assert "No se inventa un 0" in str(e), e


@caso("listado en el tope: para en vez de vigilar solo una parte")
def _():
    mod, _gh = preparar([pr(i, f"r{i}") for i in range(100)], {})
    try:
        mod.revisar()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeGuarda as e:
        assert "justo el tope" in str(e), e


@caso("main() con la API rota: exit 1 y avisa de que hoy no se ha vigilado")
def _():
    mod, _gh = preparar([pr(1, "a")], {"a": 30}, falla="pr list")
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        codigo = mod.main([])
    assert codigo == 1, codigo
    assert "no significa que las ramas esten al dia" in buf.getvalue(), buf.getvalue()


# --- Simulacion y contenido -------------------------------------------------

@caso("--simular no toca NADA")
def _():
    mod, gh = preparar([pr(1, "a")], {"a": 30})
    reporte = mod.revisar(simular=True)
    assert gh.publicados == [] and gh.editados == []
    assert "COMENTARIA" in reporte[0]


@caso("el aviso explica el conflicto NO mecanico, que es el caro")
def _():
    mod, gh = preparar([pr(1, "a")], {"a": 30})
    mod.revisar()
    cuerpo = gh.publicados[0][1]
    assert "no es mecánico" in cuerpo
    assert "CI en verde" in cuerpo, "el riesgo real es la regresion que nadie ve"
    assert "git rebase origin/main" in cuerpo, "hay que decir como salir"
    assert "no se repite" in cuerpo, "hay que prometer que no habra spam"


@caso("si GitHub ya reporta conflictos, se dice")
def _():
    mod, gh = preparar([pr(1, "a", mergeable="CONFLICTING")], {"a": 30})
    mod.revisar()
    assert "ya reporta **conflictos**" in gh.publicados[0][1]


@caso("la base no siempre es main: el mensaje usa la de verdad")
def _():
    mod, gh = preparar([pr(1, "a", base="develop")], {"a": 30})
    mod.revisar()
    assert "origin/develop" in gh.publicados[0][1]
    assert "origin/main" not in gh.publicados[0][1]


def main() -> int:
    fallidos = 0
    for nombre, prueba in CASOS:
        try:
            prueba()
            print(f"  ok    {nombre}")
        except AssertionError as e:
            fallidos += 1
            print(f"  FALLO {nombre}\n        {e}")
        except Exception as e:  # noqa: BLE001 - el test no debe ocultar errores
            fallidos += 1
            print(f"  ERROR {nombre}\n        {type(e).__name__}: {e}")
    print(f"\n{len(CASOS) - fallidos}/{len(CASOS)} casos OK")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
