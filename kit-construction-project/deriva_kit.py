#!/usr/bin/env python3
"""Detector de deriva entre el kit y los proyectos que lo tienen instalado.

POR QUE EXISTE
--------------
El kit viaja a los proyectos por copia. A partir de ahi las dos copias evolucionan
por su cuenta y nadie se entera: el 2026-07-29 barber-king llevaba una semana
divergiendo en 15 ficheros / 1.157 lineas, y se descubrio de casualidad. El
2026-08-06 volvio a pasar tres dias despues de un port que se creia completo
(`plantillas/hooks/arranque.sh` seguia detectando hooks con `grep pre-push`
mientras el proyecto ya leia los tipos del `.pre-commit-config.yaml`).

Las dos veces el problema no fue portar mal: fue no poder PREGUNTAR. Esto
responde en segundos "¿en que difiere hoy este proyecto del kit?".

QUE NO ES
---------
No es una guarda de CI. Un proyecto vivo SIEMPRE tendra divergencia legitima
—barber-king fusiono `docs-check.yml` dentro de su `ci.yml` (T-034), y eso esta
bien— asi que una señal que nunca puede salir verde se aprende a ignorar, que es
justo la leccion que este repo ya pago tres veces. Se ejecuta a mano: antes de
portar, despues de portar, y antes de dar por bueno un "ya esta sincronizado".

COMO SABE QUE ESCRIBE EL KIT
----------------------------
Instalando el kit en un directorio temporal y leyendo el manifiesto que el propio
instalador deja. El mapa origen->destino vive en `instalar.sh` y NO se copia aqui:
un detector de deriva que duplica el mapa acaba derivando el mismo.

PLACEHOLDERS
------------
El kit escribe `{{OWNER}}` donde el proyecto tiene `SanchezIng`. Eso no es deriva,
es configuracion, y contarlo como diferencia haria el informe inservible: las
piezas mas importantes (las 3 skills, `tablero.py`, `audit_check.py`) saldrian
siempre en rojo. Una linea que solo difiere en la posicion de un `{{...}}` se
clasifica como CONFIGURADA, no como divergente.

Uso:
    python3 deriva_kit.py <ruta-proyecto> [<ruta-proyecto>...]
    python3 deriva_kit.py --desde <arbol-ya-instalado> <ruta-proyecto>
    python3 deriva_kit.py --resumen <ruta-proyecto> [...]

Salida: 0 si no hay divergencia real en ningun proyecto, 1 si la hay.
"""

import difflib
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")

IGUAL = "igual"
CONFIGURADO = "configurado"
DIVERGENTE = "divergente"
AUSENTE = "ausente"


def hash_git(datos):
    """SHA-1 del blob, igual que `git hash-object`.

    Se calcula aqui en vez de invocar a git una vez por fichero: son ~40 ficheros
    por proyecto y lanzar 40 procesos en Windows es la diferencia entre "responde"
    y "te vas a por un cafe" — y una herramienta lenta no se ejecuta.
    """
    cabecera = b"blob %d\0" % len(datos)
    return hashlib.sha1(cabecera + datos).hexdigest()


def leer_manifiesto(ruta):
    """[(hash, ruta_relativa)] del manifiesto que deja el instalador.

    El `\\r` se quita a proposito: en Windows el fichero puede llegar con CRLF y
    entonces cada ruta acaba en un caracter invisible que hace que TODO salga
    "ausente". Paso de verdad al medir barber-king el 2026-08-06.
    """
    entradas = []
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        for linea in f:
            linea = linea.replace("\r", "").rstrip("\n")
            if not linea or linea.startswith("#"):
                continue
            partes = linea.split("\t", 1)
            if len(partes) != 2:
                partes = linea.split(None, 1)
            if len(partes) == 2:
                entradas.append((partes[0].strip(), partes[1].strip()))
    return entradas


def instalar_en_temporal():
    """Instala el kit en un temporal y devuelve (directorio, manifiesto).

    Modo `--protocolo` porque es el superconjunto: instala todo lo que instala el
    modo fabrica y ademas las skills del equipo y las guardas.
    """
    destino = tempfile.mkdtemp(prefix="deriva-kit.")
    instalador = os.path.join(AQUI, "instalar.sh")
    try:
        proc = subprocess.run(
            ["sh", instalador, destino, "--protocolo"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        shutil.rmtree(destino, ignore_errors=True)
        sys.exit(
            "No se encuentra `sh`. Este detector instala el kit en un temporal para\n"
            "saber que escribe hoy, y para eso necesita un shell POSIX (Git Bash en\n"
            "Windows). Alternativa sin shell: --desde <arbol-ya-instalado>."
        )
    manifiesto = os.path.join(destino, "SKILLS-PORTABLE", ".manifiesto")
    if proc.returncode != 0 or not os.path.exists(manifiesto):
        shutil.rmtree(destino, ignore_errors=True)
        sys.exit(
            "El instalador no dejo manifiesto (exit %s). Salida:\n%s"
            % (proc.returncode, (proc.stdout or "") + (proc.stderr or ""))
        )
    return destino, manifiesto


def linea_encaja(linea_kit, linea_proyecto):
    """¿La linea del proyecto es la del kit con los placeholders rellenados?"""
    if not PLACEHOLDER.search(linea_kit):
        return False
    # El patron se construye troceando a mano —literal, comodin, literal...— y
    # con `re.escape` en los literales: la linea del kit es texto arbitrario y
    # sin escapar, un `(` suyo convertiria el patron en otra cosa.
    patron = ""
    resto = linea_kit
    while True:
        m = PLACEHOLDER.search(resto)
        if not m:
            patron += re.escape(resto)
            break
        patron += re.escape(resto[: m.start()]) + ".*"
        resto = resto[m.end() :]
    return re.fullmatch(patron, linea_proyecto) is not None


def clasificar(datos_kit, datos_proyecto):
    """(estado, lineas_no_explicadas) comparando el fichero del kit con el del proyecto."""
    if datos_kit == datos_proyecto:
        return IGUAL, 0

    lineas_kit = datos_kit.decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
    lineas_pro = datos_proyecto.decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
    if lineas_kit == lineas_pro:
        # Solo cambian los finales de linea. No es deriva de contenido y decirlo
        # como tal mandaria a alguien a leer un diff vacio.
        return IGUAL, 0

    sin_explicar = 0
    matcher = difflib.SequenceMatcher(None, lineas_kit, lineas_pro, autojunk=False)
    for etiqueta, i1, i2, j1, j2 in matcher.get_opcodes():
        if etiqueta == "equal":
            continue
        if etiqueta == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                if not linea_encaja(lineas_kit[i1 + k], lineas_pro[j1 + k]):
                    sin_explicar += 1
        else:
            sin_explicar += max(i2 - i1, j2 - j1)

    if sin_explicar == 0:
        return CONFIGURADO, 0
    return DIVERGENTE, sin_explicar


def candidatos(destino, relativa):
    """Rutas donde puede estar el fichero en el proyecto.

    Los workflows se instalan con sufijo `.desactivado` y el equipo los activa
    renombrandolos — el propio `instalar.sh` lo contempla. Buscar solo el nombre
    de fabrica los daria por ausentes justo en los proyectos que SI los usan.
    """
    rutas = [os.path.join(destino, relativa)]
    if relativa.endswith(".desactivado"):
        rutas.append(os.path.join(destino, relativa[: -len(".desactivado")]))
    else:
        rutas.append(os.path.join(destino, relativa + ".desactivado"))
    return rutas


def revisar(proyecto, entradas, raiz_kit):
    """[(estado, relativa, detalle)] de un proyecto contra el kit."""
    filas = []
    for hash_kit, relativa in entradas:
        ruta_kit = os.path.join(raiz_kit, relativa)
        encontrado = None
        for ruta in candidatos(proyecto, relativa):
            if os.path.isfile(ruta):
                encontrado = ruta
                break
        if encontrado is None:
            filas.append((AUSENTE, relativa, ""))
            continue

        # El nombre bajo el que se encontro se calcula ANTES de mirar el
        # contenido y acompaña a los cuatro estados: un workflow activado que
        # ademas esta identico seguia siendo un dato que el informe se callaba.
        nombre = os.path.relpath(encontrado, proyecto).replace("\\", "/")
        detalle_nombre = "como %s" % nombre if nombre != relativa else ""

        def fila(estado, extra=""):
            partes = [p for p in (extra, detalle_nombre) if p]
            return estado, relativa, " · ".join(partes)

        with open(encontrado, "rb") as f:
            datos_pro = f.read()
        if hash_git(datos_pro) == hash_kit:
            filas.append(fila(IGUAL))
            continue
        try:
            with open(ruta_kit, "rb") as f:
                datos_kit = f.read()
        except OSError:
            filas.append(fila(DIVERGENTE, "no se pudo leer el original"))
            continue
        estado, lineas = clasificar(datos_kit, datos_pro)
        filas.append(fila(estado, "%d lineas" % lineas if estado == DIVERGENTE else ""))
    return filas


def informar(proyecto, filas, solo_resumen):
    marcas = {IGUAL: "=", CONFIGURADO: "~", DIVERGENTE: "!", AUSENTE: "-"}
    cuenta = {IGUAL: 0, CONFIGURADO: 0, DIVERGENTE: 0, AUSENTE: 0}
    print("\n%s" % proyecto)
    for estado, relativa, detalle in filas:
        cuenta[estado] += 1
        if solo_resumen or estado in (IGUAL, CONFIGURADO):
            continue
        print("  %s %s%s" % (marcas[estado], relativa, "  (%s)" % detalle if detalle else ""))
    print(
        "  -> %d iguales · %d configurados · %d DIVERGENTES · %d ausentes"
        % (cuenta[IGUAL], cuenta[CONFIGURADO], cuenta[DIVERGENTE], cuenta[AUSENTE])
    )
    return cuenta


def main(argv):
    solo_resumen = "--resumen" in argv
    argv = [a for a in argv if a != "--resumen"]

    desde = None
    if "--desde" in argv:
        i = argv.index("--desde")
        try:
            desde = argv[i + 1]
        except IndexError:
            sys.exit("--desde necesita la ruta de un arbol ya instalado.")
        argv = argv[:i] + argv[i + 2 :]

    proyectos = [a for a in argv if not a.startswith("--")]
    if not proyectos:
        sys.exit(__doc__.strip().split("Uso:")[-1].strip())

    temporal = None
    if desde:
        raiz_kit = desde
        manifiesto = os.path.join(desde, "SKILLS-PORTABLE", ".manifiesto")
        if not os.path.exists(manifiesto):
            sys.exit("No hay SKILLS-PORTABLE/.manifiesto en %s" % desde)
    else:
        temporal, manifiesto = instalar_en_temporal()
        raiz_kit = temporal

    try:
        entradas = leer_manifiesto(manifiesto)
        print("Kit: %d ficheros instalables (manifiesto de %s)" % (len(entradas), raiz_kit))
        divergencia_total = 0
        for proyecto in proyectos:
            if not os.path.isdir(proyecto):
                print("\n%s\n  (no existe)" % proyecto)
                divergencia_total += 1
                continue
            cuenta = informar(proyecto, revisar(proyecto, entradas, raiz_kit), solo_resumen)
            divergencia_total += cuenta[DIVERGENTE]
    finally:
        if temporal:
            shutil.rmtree(temporal, ignore_errors=True)

    print(
        "\n= identico · ~ solo configuracion (placeholders) · ! divergente · - ausente"
    )
    return 1 if divergencia_total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
