#!/usr/bin/env python3
"""Guarda de vulnerabilidades de dependencias con allowlist caducable.

Por que existe: el kit prescribia el comando de auditoria (`npm audit`,
`pip-audit`, `cargo audit`...) sin decir QUE HACER cuando encuentra algo. Quien
monta el CI se topa entonces con un dilema real y sin guia:

  - bloqueante a secas -> el CI queda rojo desde el primer dia por
    vulnerabilidades transitivas sin fix aguas arriba, y el equipo aprende a
    ignorar el rojo;
  - `continue-on-error` -> no avisa de nada nunca.

Se elige lo segundo porque lo primero es insostenible. En el piloto, con el paso
en `continue-on-error`, dos `high` vivieron dias en `main` con el CI en verde y
se descubrieron por casualidad al auditar a mano durante un merge.

La salida es una allowlist explicita: lo aceptado a sabiendas no bloquea, lo
nuevo si. Lo que impide que degenere en un `ignore` general es que falla en
CUATRO casos, no solo en el obvio:

  1. Vulnerabilidad bloqueante que no esta en la allowlist -> lo nuevo para en seco.
  2. Entrada CADUCADA -> obliga a reevaluar. Sin caducidad, una excepcion se
     vuelve permanente y deja de ser una excepcion.
  3. Entrada que YA NO APARECE en el audit -> se arreglo aguas arriba y sobra.
     Si se queda, tapa el proximo aviso del mismo paquete.
  4. Vencimiento a MAS DE N DIAS -> sin techo, la fecha se rellena con un año
     lejano y la caducidad no significa nada.

(2), (3) y (4) son los que evitan que la allowlist se pudra hasta convertirse en
un `continue-on-error` con mas pasos.

La clave de cada entrada es el IDENTIFICADOR DEL AVISO (GHSA/CVE/RUSTSEC), nunca
el nombre del paquete: silenciar `sharp` en bloque taparia su proximo CVE.

Se falla CERRADO en todo lo demas. Si el gestor no esta, si la salida no se puede
parsear o si no tiene la forma esperada, esto PARA en vez de concluir "no hay
vulnerabilidades": un falso verde en una guarda de seguridad es peor que no
tenerla, porque nadie vuelve a mirar.

Uso:
    python3 scripts/audit_check.py                # guarda (exit 1 si falla)
    python3 scripts/audit_check.py --diagnostico  # que ha leido, sin juzgar
Tests:
    python3 scripts/test_audit_check.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Gestor de paquetes del proyecto. Ver GESTORES para los soportados.
GESTOR = "{{GESTOR_PAQUETES}}"

RUTA_ALLOWLIST = RAIZ / "security" / "audit-allowlist.json"

# Severidades que bloquean. El umbral se comprueba AQUI y no se delega al flag
# del gestor (`--audit-level=high`): la guarda no depende de como se invoque.
BLOQUEANTES = {"high", "critical"}

# Techo de vigencia de una excepcion. Sin techo, "vence" se rellena con una
# fecha lejana y la caducidad deja de significar nada.
MAX_DIAS_VIGENCIA = 180

GHSA_EN_URL = re.compile(r"(GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4})", re.IGNORECASE)


class ErrorDeAuditoria(Exception):
    """Algo impide emitir un veredicto. NO es "no hay vulnerabilidades"."""


class Aviso:
    """Un aviso normalizado, venga del gestor que venga."""

    def __init__(self, ident: str, paquete: str, severidad: str | None,
                 titulo: str = "", url: str = ""):
        self.id = ident
        self.paquete = paquete
        self.severidad = (severidad or "").lower() or None
        self.titulo = titulo
        self.url = url

    def bloquea(self) -> bool:
        """Sin severidad NO es "leve".

        `pip-audit` y `cargo audit` no la reportan. Tratar "desconocida" como
        aceptable convertiria justo esos ecosistemas en un audit decorativo, que
        es el problema que esta guarda existe para arreglar.
        """
        return self.severidad is None or self.severidad in BLOQUEANTES

    @property
    def severidad_texto(self) -> str:
        return self.severidad or "desconocida"


# --- Adaptadores por gestor --------------------------------------------------
#
# Cada uno recibe el JSON ya parseado y devuelve [Aviso]. Si la forma no es la
# esperada, LANZA: el silencio no puede confundirse con "no hay nada".

def _exigir(condicion: bool, que: str) -> None:
    if not condicion:
        raise ErrorDeAuditoria(
            f"La salida del audit no tiene la forma esperada ({que}).\n"
            f"   NO se concluye 'sin vulnerabilidades': puede que el gestor haya\n"
            f"   cambiado de formato o que haya fallado. Corre el comando a mano\n"
            f"   y compara con `--diagnostico`."
        )


def _de_npm(datos: dict) -> list[Aviso]:
    """npm v7+: {"vulnerabilities": {paquete: {severity, via: [...]}}}.

    Se recorre `via` y no el paquete: la severidad del paquete es el maximo de
    sus avisos, y la allowlist se lleva por AVISO (GHSA), no por paquete.
    """
    _exigir(isinstance(datos.get("vulnerabilities"), dict), "falta 'vulnerabilities'")
    avisos = []
    for paquete, info in datos["vulnerabilities"].items():
        for via in info.get("via", []):
            if not isinstance(via, dict):
                continue  # cadena transitiva: el aviso real ya sale por su paquete
            url = via.get("url", "")
            encontrado = GHSA_EN_URL.search(url)
            ident = encontrado.group(1) if encontrado else f"npm-{via.get('source')}"
            avisos.append(Aviso(ident, via.get("name") or paquete,
                                via.get("severity") or info.get("severity"),
                                via.get("title", ""), url))
    return avisos


def _de_advisories(datos: dict) -> list[Aviso]:
    """pnpm y yarn berry: {"advisories": {id: {github_advisory_id, ...}}}."""
    if "error" in datos:
        error = datos["error"]
        mensaje = error.get("message") if isinstance(error, dict) else str(error)
        raise ErrorDeAuditoria(f"El gestor devolvio un error: {mensaje}")
    _exigir(isinstance(datos.get("advisories"), dict), "falta 'advisories'")
    avisos = []
    for clave, adv in datos["advisories"].items():
        ident = adv.get("github_advisory_id") or adv.get("cves", [None])[0] or f"id-{clave}"
        avisos.append(Aviso(ident, adv.get("module_name", "?"), adv.get("severity"),
                            adv.get("title", ""), adv.get("url", "")))
    return avisos


def _de_pip_audit(datos: dict | list) -> list[Aviso]:
    """pip-audit -f json: {"dependencies": [{name, vulns: [{id, ...}]}]}.

    No reporta severidad: todo aviso bloquea salvo que se acepte explicitamente.
    """
    dependencias = datos.get("dependencies") if isinstance(datos, dict) else datos
    _exigir(isinstance(dependencias, list), "falta 'dependencies'")
    avisos = []
    for dep in dependencias:
        for vuln in dep.get("vulns", []) or []:
            avisos.append(Aviso(vuln.get("id", "?"), dep.get("name", "?"), None,
                                (vuln.get("description") or "").split("\n")[0],
                                ""))
    return avisos


def _de_composer(datos: dict) -> list[Aviso]:
    """composer audit --format=json: {"advisories": {paquete: [ {...} ]}}."""
    _exigir(isinstance(datos.get("advisories"), dict), "falta 'advisories'")
    avisos = []
    for paquete, lista in datos["advisories"].items():
        for adv in lista if isinstance(lista, list) else [lista]:
            ident = adv.get("cve") or adv.get("advisoryId") or "?"
            avisos.append(Aviso(ident, adv.get("packageName") or paquete,
                                adv.get("severity"), adv.get("title", ""),
                                adv.get("link", "")))
    return avisos


def _de_cargo(datos: dict) -> list[Aviso]:
    """cargo audit --json: {"vulnerabilities": {"list": [{advisory, package}]}}.

    Tampoco reporta severidad; misma regla que pip-audit.
    """
    bloque = datos.get("vulnerabilities")
    _exigir(isinstance(bloque, dict) and isinstance(bloque.get("list"), list),
            "falta 'vulnerabilities.list'")
    avisos = []
    for item in bloque["list"]:
        advisory = item.get("advisory") or {}
        paquete = (item.get("package") or {}).get("name") or advisory.get("package", "?")
        avisos.append(Aviso(advisory.get("id", "?"), paquete, None,
                            advisory.get("title", ""), advisory.get("url", "") or ""))
    return avisos


# `verificado`: si el adaptador se ha probado contra la salida REAL de la
# herramienta o solo contra su formato documentado. Los no verificados fallan
# cerrado ante cualquier sorpresa, pero conviene mirar `--diagnostico` la primera
# vez y comparar con la salida cruda del comando.
GESTORES = {
    "npm":       {"cmd": ["npm", "audit", "--json"], "parser": _de_npm, "verificado": True},
    "pnpm":      {"cmd": ["pnpm", "audit", "--json"], "parser": _de_advisories, "verificado": True},
    "yarn":      {"cmd": ["yarn", "npm", "audit", "--json", "--all", "--recursive"],
                  "parser": _de_advisories, "verificado": False},
    "pip-audit": {"cmd": ["pip-audit", "-f", "json"], "parser": _de_pip_audit, "verificado": False},
    "composer":  {"cmd": ["composer", "audit", "--format=json"], "parser": _de_composer,
                  "verificado": False},
    "cargo":     {"cmd": ["cargo", "audit", "--json"], "parser": _de_cargo, "verificado": False},
}


def adaptador() -> dict:
    if "{{" in GESTOR:
        raise ErrorDeAuditoria(
            f"GESTOR sigue sin rellenar en scripts/audit_check.py.\n"
            f"   Pon el gestor de paquetes del proyecto: "
            f"{', '.join(sorted(GESTORES))}."
        )
    if GESTOR not in GESTORES:
        raise ErrorDeAuditoria(
            f"GESTOR='{GESTOR}' no tiene adaptador.\n"
            f"   Soportados: {', '.join(sorted(GESTORES))}.\n"
            f"   Para añadir el tuyo: una entrada en GESTORES con el comando que\n"
            f"   saca JSON y una funcion que lo normalice a [Aviso]. Debe LANZAR\n"
            f"   si la forma no es la esperada — nunca devolver [] ante una salida\n"
            f"   que no entiende."
        )
    return GESTORES[GESTOR]


def ejecutar_audit() -> list[Aviso]:
    """Corre el audit y normaliza. Falla cerrado ante cualquier sorpresa."""
    conf = adaptador()
    try:
        proc = subprocess.run(
            conf["cmd"], capture_output=True, text=True, cwd=RAIZ,
            shell=sys.platform == "win32",
        )
    except FileNotFoundError:
        raise ErrorDeAuditoria(
            f"No se encontro '{conf['cmd'][0]}' en el PATH.\n"
            f"   Sin poder auditar NO se da por buena la build."
        ) from None

    # El codigo de salida no sirve de señal: casi todos los gestores salen != 0
    # cuando encuentran algo. Lo que importa es poder parsear el JSON.
    try:
        datos = json.loads(proc.stdout)
    except json.JSONDecodeError:
        salida = (proc.stdout or proc.stderr or "").strip()[:400]
        raise ErrorDeAuditoria(
            f"`{' '.join(conf['cmd'])}` no devolvio JSON valido.\n"
            f"   Salida: {salida or '(vacia)'}\n"
            f"   Se falla cerrado: una salida que no se entiende no es 'sin "
            f"vulnerabilidades'."
        ) from None
    return conf["parser"](datos)


# --- Allowlist ---------------------------------------------------------------

def cargar_allowlist() -> list[dict]:
    if not RUTA_ALLOWLIST.exists():
        return []
    try:
        with RUTA_ALLOWLIST.open(encoding="utf-8") as fh:
            contenido = json.load(fh)
    except json.JSONDecodeError as e:
        raise ErrorDeAuditoria(
            f"{RUTA_ALLOWLIST} no es JSON valido ({e}).\n"
            f"   No se audita con una allowlist ilegible: no se sabe que se acepto."
        ) from None
    aceptados = contenido.get("aceptados", [])
    if not isinstance(aceptados, list):
        raise ErrorDeAuditoria(f"{RUTA_ALLOWLIST}: 'aceptados' debe ser una lista.")
    return aceptados


def validar_entrada(entrada: dict, hoy: date) -> list[str]:
    """Una entrada mal escrita no silencia nada."""
    fallos = []
    ident = entrada.get("id") or entrada.get("ghsa") or "(sin id)"

    for campo in ("paquete", "motivo", "vence", "seguimiento"):
        if not entrada.get(campo):
            fallos.append(f"allowlist: la entrada '{ident}' no declara '{campo}'")
    if not (entrada.get("id") or entrada.get("ghsa")):
        fallos.append("allowlist: hay una entrada sin 'id' (GHSA/CVE/RUSTSEC del aviso)")

    vence_txt = entrada.get("vence")
    if vence_txt:
        try:
            vence = datetime.strptime(str(vence_txt), "%Y-%m-%d").date()
        except ValueError:
            fallos.append(f"allowlist: '{ident}' tiene 'vence' invalido ({vence_txt}), "
                          f"formato AAAA-MM-DD")
            return fallos
        if vence < hoy:
            fallos.append(
                f"allowlist: la aceptacion de '{ident}' ({entrada.get('paquete')}) "
                f"CADUCO el {vence_txt}. Reevalua: o hay fix aguas arriba y se quita, "
                f"o se renueva con motivo actualizado."
            )
        elif vence > hoy + timedelta(days=MAX_DIAS_VIGENCIA):
            fallos.append(
                f"allowlist: '{ident}' vence el {vence_txt}, a mas de "
                f"{MAX_DIAS_VIGENCIA} dias vista. Una excepcion tan larga deja de "
                f"revisarse; acorta la fecha."
            )
    return fallos


def revisar(avisos: list[Aviso], allowlist: list[dict], hoy: date) -> tuple[list[str], list[str]]:
    """(fallos, tolerados). Toda la logica, sin tocar disco ni red."""
    fallos: list[str] = []
    for entrada in allowlist:
        fallos.extend(validar_entrada(entrada, hoy))

    aceptados = {(e.get("id") or e.get("ghsa")): e for e in allowlist
                 if e.get("id") or e.get("ghsa")}
    vistos: set[str] = set()
    tolerados: list[str] = []

    for aviso in avisos:
        if not aviso.bloquea():
            continue
        vistos.add(aviso.id)
        if aviso.id in aceptados:
            tolerados.append(
                f"{aviso.severidad_texto:12} {aviso.paquete:20} {aviso.id}  "
                f"(aceptada hasta {aceptados[aviso.id].get('vence')})"
            )
        else:
            razon = ("severidad desconocida — el gestor no la reporta, asi que se "
                     "trata como bloqueante"
                     if aviso.severidad is None else aviso.severidad.upper())
            fallos.append(
                f"vulnerabilidad sin aceptar [{razon}]: {aviso.paquete} — {aviso.id}\n"
                f"    {aviso.titulo}\n"
                f"    {aviso.url}\n"
                f"    Arreglala, o si se acepta a sabiendas añadela a "
                f"security/audit-allowlist.json con motivo y caducidad."
            )

    for ident, entrada in aceptados.items():
        if ident not in vistos:
            fallos.append(
                f"allowlist: la entrada '{ident}' ({entrada.get('paquete')}) ya no "
                f"aparece en el audit — probablemente se arreglo aguas arriba. "
                f"Quitala: una entrada obsoleta taparia el proximo aviso del mismo "
                f"paquete."
            )
    return fallos, tolerados


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    try:
        avisos = ejecutar_audit()
        allowlist = cargar_allowlist()
    except ErrorDeAuditoria as e:
        print(f"FALLO {e}", file=sys.stderr)
        print("\nLa auditoria NO ha podido concluir. Esto no es una build limpia.",
              file=sys.stderr)
        return 1

    if "--diagnostico" in argv:
        # Verificar el efecto, no la invocacion: aqui se ve lo que la guarda
        # LEYO, para poder compararlo con la salida cruda del comando.
        conf = GESTORES[GESTOR]
        print(f"Gestor: {GESTOR} ({' '.join(conf['cmd'])})"
              f"{'' if conf['verificado'] else '  [adaptador NO verificado contra la herramienta real]'}")
        print(f"Avisos leidos: {len(avisos)} · bloqueantes: "
              f"{sum(1 for a in avisos if a.bloquea())}")
        for aviso in sorted(avisos, key=lambda a: (a.paquete, a.id)):
            marca = "BLOQUEA" if aviso.bloquea() else "   —   "
            print(f"  {marca} {aviso.severidad_texto:12} {aviso.paquete:20} {aviso.id}")
        print(f"\nEntradas en la allowlist: {len(allowlist)}")
        return 0

    fallos, tolerados = revisar(avisos, allowlist, date.today())

    if tolerados:
        print("Vulnerabilidades aceptadas a sabiendas (no bloquean):")
        for linea in tolerados:
            print(f"  {linea}")

    if fallos:
        print("\nAuditoria de dependencias FALLIDA:\n", file=sys.stderr)
        for fallo in fallos:
            print(f"  - {fallo}", file=sys.stderr)
        return 1

    print(f"\nAuditoria OK ({GESTOR}): {len(avisos)} aviso(s) leidos, ninguno "
          f"bloqueante fuera de la allowlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
