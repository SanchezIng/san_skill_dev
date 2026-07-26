#!/usr/bin/env python3
"""Tests de la guarda audit_check.py.

Por que existen: esta guarda decide si una vulnerabilidad rompe la build. Si se
equivoca hacia el lado permisivo, el resultado es exactamente el problema que
vino a arreglar — un paso de CI decorativo que nadie mira. Asi que cada regla se
prueba en los DOS sentidos, y hay un bloque entero dedicado a lo unico
imperdonable: **concluir "sin vulnerabilidades" cuando en realidad no se ha
podido auditar**.

Los ejemplos de npm y pnpm son la salida REAL de esas herramientas (recortada),
capturada contra un proyecto con `lodash@4.17.15` y `minimist@0.0.8`.

Uso: python3 scripts/test_audit_check.py     (exit 1 si algun caso falla)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODULO = AQUI / "audit_check.py"

HOY = date(2026, 7, 26)


def cargar(gestor="npm"):
    spec = importlib.util.spec_from_file_location("audit_check", MODULO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.GESTOR = gestor
    return mod


# --- Salidas reales (recortadas) --------------------------------------------

NPM_REAL = {
    "auditReportVersion": 2,
    "vulnerabilities": {
        "lodash": {
            "name": "lodash", "severity": "high", "isDirect": True,
            "via": [
                {"source": 1106913, "name": "lodash", "title": "Command Injection in lodash",
                 "url": "https://github.com/advisories/GHSA-35jh-r3h4-6jhm",
                 "severity": "high", "range": "<4.17.21"},
                {"source": 1106920, "name": "lodash", "title": "Prototype Pollution in lodash",
                 "url": "https://github.com/advisories/GHSA-p6mc-m468-83gw",
                 "severity": "high", "range": "<4.17.19"},
            ],
        },
        "minimist": {
            "name": "minimist", "severity": "critical", "isDirect": True,
            "via": [
                {"source": 1096466, "name": "minimist", "title": "Prototype Pollution in minimist",
                 "url": "https://github.com/advisories/GHSA-vh95-rmgr-6w4m",
                 "severity": "moderate", "range": "<0.2.1"},
                {"source": 1096996, "name": "minimist", "title": "Prototype Pollution in minimist",
                 "url": "https://github.com/advisories/GHSA-xvch-5gv4-984h",
                 "severity": "critical", "range": "<0.2.4"},
            ],
        },
    },
    "metadata": {"vulnerabilities": {"info": 0, "low": 0, "moderate": 0,
                                     "high": 1, "critical": 1, "total": 2}},
}

PNPM_REAL = {
    "advisories": {
        "1096466": {"id": 1096466, "title": "Prototype Pollution in minimist",
                    "module_name": "minimist", "severity": "moderate",
                    "github_advisory_id": "GHSA-vh95-rmgr-6w4m",
                    "url": "https://github.com/advisories/GHSA-vh95-rmgr-6w4m"},
        "1106913": {"id": 1106913, "title": "Command Injection in lodash",
                    "module_name": "lodash", "severity": "high",
                    "github_advisory_id": "GHSA-35jh-r3h4-6jhm",
                    "url": "https://github.com/advisories/GHSA-35jh-r3h4-6jhm"},
    },
    "metadata": {"vulnerabilities": {"info": 0, "low": 0, "moderate": 4,
                                     "high": 3, "critical": 1}},
}

# Error real de pnpm sin lockfile: el caso que JAMAS puede leerse como "limpio".
PNPM_SIN_LOCKFILE = {"error": {"code": "ERR_PNPM_AUDIT_NO_LOCKFILE",
                               "message": "No pnpm-lock.yaml found: Cannot audit a "
                                          "project without a lockfile"}}

PIP_AUDIT = {"dependencies": [
    {"name": "flask", "version": "0.5",
     "vulns": [{"id": "PYSEC-2019-179", "fix_versions": ["0.12.3"],
                "description": "Flask before 0.12.3 ..."}]},
    {"name": "requests", "version": "2.31.0", "vulns": []},
]}

COMPOSER = {"advisories": {"laravel/framework": [
    {"advisoryId": "PKSA-1234", "packageName": "laravel/framework",
     "title": "XSS en ...", "cve": "CVE-2026-1234", "severity": "high",
     "link": "https://github.com/advisories/GHSA-aaaa-bbbb-cccc"}]}}

CARGO = {"vulnerabilities": {"found": True, "count": 1, "list": [
    {"advisory": {"id": "RUSTSEC-2020-0071", "title": "Segfault en time",
                  "url": "https://rustsec.org/advisories/RUSTSEC-2020-0071"},
     "package": {"name": "time", "version": "0.1.44"}}]}}


def entrada(ident, paquete="lodash", vence=None, **extra):
    base = {
        "id": ident, "paquete": paquete, "severidad": "high",
        "motivo": "Ruta no ejercitada; sin fix aguas arriba.",
        "vence": vence or (HOY + timedelta(days=30)).isoformat(),
        "seguimiento": "https://github.com/o/r/issues/1",
    }
    base.update(extra)
    return base


CASOS = []


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


# --- Adaptadores: se lee lo que la herramienta dice de verdad ----------------

@caso("npm real: un aviso por GHSA, no uno por paquete")
def _():
    mod = cargar("npm")
    avisos = mod._de_npm(NPM_REAL)
    assert len(avisos) == 4, [a.id for a in avisos]
    ids = {a.id for a in avisos}
    assert "GHSA-35jh-r3h4-6jhm" in ids and "GHSA-xvch-5gv4-984h" in ids, ids


@caso("npm: la severidad es la DEL AVISO, no el maximo del paquete")
def _():
    # minimist sale como 'critical' de paquete, pero uno de sus avisos es
    # 'moderate': aceptar por paquete taparia el critical.
    mod = cargar("npm")
    por_id = {a.id: a for a in mod._de_npm(NPM_REAL)}
    assert por_id["GHSA-vh95-rmgr-6w4m"].severidad == "moderate"
    assert por_id["GHSA-xvch-5gv4-984h"].severidad == "critical"
    assert not por_id["GHSA-vh95-rmgr-6w4m"].bloquea()


@caso("npm: las cadenas transitivas (via de tipo texto) no revientan")
def _():
    mod = cargar("npm")
    datos = {"vulnerabilities": {"a": {"severity": "high", "via": ["b", {
        "source": 1, "name": "b", "severity": "high", "title": "x",
        "url": "https://github.com/advisories/GHSA-1111-2222-3333"}]}}}
    assert len(mod._de_npm(datos)) == 1


@caso("pnpm real: se lee el github_advisory_id")
def _():
    mod = cargar("pnpm")
    avisos = mod._de_advisories(PNPM_REAL)
    assert {a.id for a in avisos} == {"GHSA-vh95-rmgr-6w4m", "GHSA-35jh-r3h4-6jhm"}
    assert [a for a in avisos if a.bloquea()][0].paquete == "lodash"


@caso("pip-audit: sin severidad -> BLOQUEA (no se asume que sea leve)")
def _():
    mod = cargar("pip-audit")
    avisos = mod._de_pip_audit(PIP_AUDIT)
    assert len(avisos) == 1, avisos
    assert avisos[0].id == "PYSEC-2019-179" and avisos[0].severidad is None
    assert avisos[0].bloquea(), "una severidad desconocida no puede pasar por leve"


@caso("composer: se prefiere el CVE como identificador")
def _():
    mod = cargar("composer")
    avisos = mod._de_composer(COMPOSER)
    assert avisos[0].id == "CVE-2026-1234" and avisos[0].severidad == "high"


@caso("cargo: RUSTSEC como id, sin severidad -> bloquea")
def _():
    mod = cargar("cargo")
    avisos = mod._de_cargo(CARGO)
    assert avisos[0].id == "RUSTSEC-2020-0071" and avisos[0].paquete == "time"
    assert avisos[0].bloquea()


# --- Fallar cerrado: lo unico imperdonable ----------------------------------

@caso("pnpm sin lockfile: el error NO se lee como 'no hay vulnerabilidades'")
def _():
    mod = cargar("pnpm")
    try:
        mod._de_advisories(PNPM_SIN_LOCKFILE)
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeAuditoria as e:
        assert "ERR_PNPM_AUDIT_NO_LOCKFILE" in str(e) or "lockfile" in str(e), e


@caso("forma inesperada (cambio de formato del gestor): MUERDE")
def _():
    mod = cargar("npm")
    for datos in ({"algo": "otra cosa"}, {"vulnerabilities": []}, {}):
        try:
            mod._de_npm(datos)
            raise AssertionError(f"deberia haber fallado con {datos}")
        except mod.ErrorDeAuditoria as e:
            assert "no tiene la forma esperada" in str(e), e


@caso("salida que no es JSON: se falla cerrado, no se da build limpia")
def _():
    mod = cargar("npm")
    mod.subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(
        cmd, 1, "npm ERR! code ENOLOCK\n", "")
    try:
        mod.ejecutar_audit()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeAuditoria as e:
        assert "no devolvio JSON valido" in str(e), e
        assert "ENOLOCK" in str(e), "hay que enseñar la salida real para poder arreglarlo"


@caso("el gestor no esta instalado: MUERDE (no se audita = no se aprueba)")
def _():
    mod = cargar("npm")

    def no_existe(cmd, **kw):
        raise FileNotFoundError(cmd[0])
    mod.subprocess.run = no_existe
    try:
        mod.ejecutar_audit()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeAuditoria as e:
        assert "no se encontro" in str(e).lower(), e


@caso("GESTOR sin rellenar: lo dice y lista los soportados")
def _():
    mod = cargar("{{GESTOR_PAQUETES}}")
    try:
        mod.adaptador()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeAuditoria as e:
        assert "sin rellenar" in str(e) and "pnpm" in str(e), e


@caso("GESTOR desconocido: explica como añadir un adaptador")
def _():
    mod = cargar("bun")
    try:
        mod.adaptador()
        raise AssertionError("deberia haber fallado")
    except mod.ErrorDeAuditoria as e:
        assert "no tiene adaptador" in str(e), e
        assert "nunca devolver []" in str(e), "el aviso clave es el de no fallar en silencio"


@caso("allowlist ilegible: no se audita a ciegas")
def _():
    mod = cargar("npm")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "audit-allowlist.json"
        ruta.write_text("{ esto no es json", encoding="utf-8")
        mod.RUTA_ALLOWLIST = ruta
        try:
            mod.cargar_allowlist()
            raise AssertionError("deberia haber fallado")
        except mod.ErrorDeAuditoria as e:
            assert "no es JSON valido" in str(e), e


@caso("main() con el audit roto sale 1 y dice que NO es una build limpia")
def _():
    mod = cargar("npm")
    mod.subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "boom", "")
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        codigo = mod.main([])
    assert codigo == 1, codigo
    assert "no es una build limpia" in buf.getvalue(), buf.getvalue()


# --- Las cuatro formas de fallar de la allowlist ----------------------------

def avisos_de(mod, datos=None):
    return mod._de_npm(datos or NPM_REAL)


@caso("1) vulnerabilidad bloqueante sin aceptar: MUERDE")
def _():
    mod = cargar("npm")
    fallos, tolerados = mod.revisar(avisos_de(mod), [], HOY)
    assert tolerados == [], tolerados
    # 3 bloqueantes: 2 high de lodash + 1 critical de minimist (la moderate no)
    assert len(fallos) == 3, fallos
    assert "sin aceptar" in fallos[0] and "GHSA-" in fallos[0]
    assert "audit-allowlist.json" in fallos[0], "hay que decir como aceptarla"


@caso("aceptada a sabiendas: NO bloquea y se informa de hasta cuando")
def _():
    mod = cargar("npm")
    lista = [entrada("GHSA-35jh-r3h4-6jhm"), entrada("GHSA-p6mc-m468-83gw"),
             entrada("GHSA-xvch-5gv4-984h", "minimist")]
    fallos, tolerados = mod.revisar(avisos_de(mod), lista, HOY)
    assert fallos == [], fallos
    assert len(tolerados) == 3 and "aceptada hasta" in tolerados[0]


@caso("2) entrada CADUCADA: MUERDE aunque la vulnerabilidad siga igual")
def _():
    mod = cargar("npm")
    lista = [entrada("GHSA-35jh-r3h4-6jhm", vence="2026-07-25"),
             entrada("GHSA-p6mc-m468-83gw"), entrada("GHSA-xvch-5gv4-984h", "minimist")]
    fallos, _t = mod.revisar(avisos_de(mod), lista, HOY)
    assert len(fallos) == 1, fallos
    assert "CADUCO" in fallos[0] and "Reevalua" in fallos[0], fallos


@caso("3) entrada que YA NO aparece en el audit: MUERDE (taparia al siguiente)")
def _():
    mod = cargar("npm")
    lista = [entrada("GHSA-35jh-r3h4-6jhm"), entrada("GHSA-p6mc-m468-83gw"),
             entrada("GHSA-xvch-5gv4-984h", "minimist"),
             entrada("GHSA-9999-9999-9999", "sharp")]
    fallos, _t = mod.revisar(avisos_de(mod), lista, HOY)
    assert len(fallos) == 1, fallos
    assert "ya no aparece en el audit" in fallos[0], fallos


@caso("4) vencimiento a mas de 180 dias: MUERDE (si no, la caducidad es humo)")
def _():
    mod = cargar("npm")
    lejos = (HOY + timedelta(days=365)).isoformat()
    lista = [entrada("GHSA-35jh-r3h4-6jhm", vence=lejos),
             entrada("GHSA-p6mc-m468-83gw"), entrada("GHSA-xvch-5gv4-984h", "minimist")]
    fallos, _t = mod.revisar(avisos_de(mod), lista, HOY)
    assert len(fallos) == 1, fallos
    assert "dias vista" in fallos[0], fallos


@caso("entrada sin motivo ni seguimiento: MUERDE (aceptar exige explicar)")
def _():
    mod = cargar("npm")
    floja = {"id": "GHSA-35jh-r3h4-6jhm", "paquete": "lodash",
             "vence": (HOY + timedelta(days=10)).isoformat()}
    fallos, _t = mod.revisar(avisos_de(mod), [floja], HOY)
    assert any("no declara 'motivo'" in f for f in fallos), fallos
    assert any("no declara 'seguimiento'" in f for f in fallos), fallos


@caso("entrada sin id: MUERDE (silenciar por paquete es lo que no se quiere)")
def _():
    mod = cargar("npm")
    sin_id = {"paquete": "lodash", "motivo": "x", "seguimiento": "y",
              "vence": (HOY + timedelta(days=10)).isoformat()}
    fallos, _t = mod.revisar(avisos_de(mod), [sin_id], HOY)
    assert any("sin 'id'" in f for f in fallos), fallos


@caso("'vence' con formato raro: MUERDE en vez de interpretarlo a su manera")
def _():
    mod = cargar("npm")
    fallos, _t = mod.revisar(avisos_de(mod), [entrada("X", vence="20/10/2026")], HOY)
    assert any("formato AAAA-MM-DD" in f for f in fallos), fallos


@caso("compatibilidad: entradas con 'ghsa' (nombre viejo) siguen valiendo")
def _():
    mod = cargar("npm")
    vieja = {"ghsa": "GHSA-35jh-r3h4-6jhm", "paquete": "lodash", "motivo": "x",
             "seguimiento": "y", "vence": (HOY + timedelta(days=10)).isoformat()}
    fallos, tolerados = mod.revisar(mod._de_npm(
        {"vulnerabilities": {"lodash": {"severity": "high", "via": [
            {"source": 1, "name": "lodash", "severity": "high", "title": "t",
             "url": "https://github.com/advisories/GHSA-35jh-r3h4-6jhm"}]}}}),
        [vieja], HOY)
    assert fallos == [] and len(tolerados) == 1, (fallos, tolerados)


@caso("sin vulnerabilidades y sin allowlist: pasa limpio")
def _():
    mod = cargar("npm")
    fallos, tolerados = mod.revisar([], [], HOY)
    assert fallos == [] and tolerados == []


@caso("--diagnostico enseña lo LEIDO y marca los adaptadores no verificados")
def _():
    mod = cargar("cargo")
    mod.subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(
        cmd, 1, json.dumps(CARGO), "")
    mod.RUTA_ALLOWLIST = Path(tempfile.gettempdir()) / "no-existe-allowlist.json"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        codigo = mod.main(["--diagnostico"])
    salida = buf.getvalue()
    assert codigo == 0, codigo
    assert "RUSTSEC-2020-0071" in salida and "BLOQUEA" in salida, salida
    assert "NO verificado" in salida, "hay que avisar de que ese adaptador no se probó"


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
