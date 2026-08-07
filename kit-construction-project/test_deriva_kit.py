#!/usr/bin/env python3
"""Tests del detector de deriva.

Que se comprueba y por que: el valor de este detector es distinguir tres cosas
que a ojo se confunden — un fichero identico, uno que solo tiene los placeholders
rellenados (configuracion, NO deriva) y uno que de verdad cambio. Si esa
distincion falla, el informe o miente o es tan ruidoso que se ignora, que es el
mismo final.

No se instala el kit de verdad: se fabrica un arbol minimo con su manifiesto y se
usa `--desde`. La suite tiene que poder correrse en segundos, o no se corre.
"""

import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import deriva_kit  # noqa: E402

FALLIDOS = 0


def comprobar(descripcion, condicion):
    global FALLIDOS
    if condicion:
        print("  ok    %s" % descripcion)
    else:
        print("  FALLO %s" % descripcion)
        FALLIDOS += 1


def escribir(ruta, texto, nueva_linea="\n"):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline=nueva_linea) as f:
        f.write(texto)


def fabricar_kit(base, ficheros):
    """Arbol con SKILLS-PORTABLE/.manifiesto, como el que deja el instalador."""
    entradas = []
    for relativa, contenido in ficheros.items():
        ruta = os.path.join(base, relativa)
        escribir(ruta, contenido)
        with open(ruta, "rb") as f:
            entradas.append((deriva_kit.hash_git(f.read()), relativa))
    manifiesto = os.path.join(base, "SKILLS-PORTABLE", ".manifiesto")
    os.makedirs(os.path.dirname(manifiesto), exist_ok=True)
    with open(manifiesto, "w", encoding="utf-8") as f:
        f.write("# kit=2026-08-06\n# modo=--protocolo\n")
        for h, relativa in entradas:
            f.write("%s\t%s\n" % (h, relativa))
    return manifiesto


print("Tests del detector de deriva")
print()

TMP = tempfile.mkdtemp(prefix="test-deriva.")
try:
    KIT = os.path.join(TMP, "kit")
    PRO = os.path.join(TMP, "proyecto")

    fabricar_kit(
        KIT,
        {
            "scripts/tablero.py": 'OWNER = "{{OWNER}}"\nPROJECT = {{PROJECT_NUMBER}}\nprint(OWNER)\n',
            "scripts/guarda.py": "print('igual en los dos')\n",
            "scripts/tocado.py": "def a():\n    return 1\n",
            ".github/workflows/audit.yml.desactivado": "name: Audit\n",
            ".claude/hooks/arranque.sh": "echo hola\n",
        },
    )

    # El proyecto: uno identico, uno configurado, uno cambiado de verdad, un
    # workflow activado (renombrado) y uno que el proyecto ya no tiene.
    escribir(os.path.join(PRO, "scripts/guarda.py"), "print('igual en los dos')\n")
    escribir(
        os.path.join(PRO, "scripts/tablero.py"),
        'OWNER = "SanchezIng"\nPROJECT = 4\nprint(OWNER)\n',
    )
    escribir(os.path.join(PRO, "scripts/tocado.py"), "def a():\n    return 2\n")
    escribir(os.path.join(PRO, ".github/workflows/audit.yml"), "name: Audit\n")

    entradas = deriva_kit.leer_manifiesto(
        os.path.join(KIT, "SKILLS-PORTABLE", ".manifiesto")
    )
    comprobar("el manifiesto se lee entero", len(entradas) == 5)

    filas = {r: (e, d) for e, r, d in deriva_kit.revisar(PRO, entradas, KIT)}

    comprobar("un fichero identico sale IGUAL", filas["scripts/guarda.py"][0] == deriva_kit.IGUAL)
    comprobar(
        "los placeholders rellenados NO son deriva",
        filas["scripts/tablero.py"][0] == deriva_kit.CONFIGURADO,
    )
    comprobar(
        "un cambio real SI es deriva",
        filas["scripts/tocado.py"][0] == deriva_kit.DIVERGENTE,
    )
    comprobar(
        "y dice cuantas lineas, que es lo que decide si miras el diff",
        "1 lineas" in filas["scripts/tocado.py"][1],
    )
    comprobar(
        "un workflow ACTIVADO (renombrado) no se da por ausente",
        filas[".github/workflows/audit.yml.desactivado"][0] == deriva_kit.IGUAL,
    )
    comprobar(
        "y se dice con que nombre se encontro",
        "audit.yml" in filas[".github/workflows/audit.yml.desactivado"][1],
    )
    comprobar(
        "lo que el proyecto no tiene sale AUSENTE",
        filas[".claude/hooks/arranque.sh"][0] == deriva_kit.AUSENTE,
    )

    # --- El caso que motivo el detector: el kit atrasado respecto al proyecto ---
    # No se distingue "el kit va atrasado" de "el proyecto se adelanto" mirando
    # solo el contenido, y el detector no lo pretende: lo que tiene que hacer es
    # NO callarse. Este caso muerde si alguien "optimiza" comparando solo tamaño.
    escribir(os.path.join(PRO, "scripts/tocado.py"), "def a():\n    return 1\n\n# extra\n")
    filas2 = {r: e for e, r, _ in deriva_kit.revisar(PRO, entradas, KIT)}
    comprobar(
        "un fichero al que el proyecto AÑADE lineas tambien sale divergente",
        filas2["scripts/tocado.py"] == deriva_kit.DIVERGENTE,
    )

    # --- CRLF: el manifiesto en Windows ---
    manifiesto_crlf = os.path.join(TMP, "manifiesto-crlf")
    with open(manifiesto_crlf, "w", encoding="utf-8", newline="") as f:
        f.write("# kit=x\r\nabc123\tscripts/guarda.py\r\n")
    entradas_crlf = deriva_kit.leer_manifiesto(manifiesto_crlf)
    comprobar(
        "un manifiesto con CRLF no deja rutas con \\r invisible (todo saldria ausente)",
        entradas_crlf == [("abc123", "scripts/guarda.py")],
    )

    # --- Solo cambian los finales de linea ---
    escribir(os.path.join(PRO, "scripts/guarda.py"), "print('igual en los dos')\n", "\r\n")
    filas3 = {r: e for e, r, _ in deriva_kit.revisar(PRO, entradas, KIT)}
    comprobar(
        "CRLF en el fichero del proyecto no se denuncia como cambio de contenido",
        filas3["scripts/guarda.py"] == deriva_kit.IGUAL,
    )

    # --- Un literal de regex en la linea con placeholder ---
    comprobar(
        "un parentesis en la linea del kit no rompe el encaje del placeholder",
        deriva_kit.linea_encaja("gh api repos/{{OWNER}}/x (ojo)", "gh api repos/Ana/x (ojo)"),
    )
    comprobar(
        "y una linea distinta de verdad NO encaja aunque tenga placeholder",
        not deriva_kit.linea_encaja("OWNER = {{OWNER}}", "OTRA_COSA = 3"),
    )
    comprobar(
        "sin placeholder, dos lineas distintas nunca 'encajan'",
        not deriva_kit.linea_encaja("return 1", "return 2"),
    )

    # --- La invocacion completa, tal como la escribe un humano ---
    proc = subprocess.run(
        [sys.executable, os.path.join(AQUI, "deriva_kit.py"), "--desde", KIT, PRO],
        capture_output=True,
        text=True,
    )
    comprobar("ejecutado de punta a punta, sale 1 si hay divergencia", proc.returncode == 1)
    comprobar(
        "y el resumen dice los cuatro numeros",
        "DIVERGENTES" in proc.stdout and "ausentes" in proc.stdout,
    )

    # Sin divergencia real -> verde. Que PUEDA salir verde es el requisito: una
    # señal que siempre esta en rojo se aprende a ignorar (leccion del 2026-07-27).
    LIMPIO = os.path.join(TMP, "limpio")
    escribir(os.path.join(LIMPIO, "scripts/guarda.py"), "print('igual en los dos')\n")
    escribir(
        os.path.join(LIMPIO, "scripts/tablero.py"),
        'OWNER = "SanchezIng"\nPROJECT = 4\nprint(OWNER)\n',
    )
    escribir(os.path.join(LIMPIO, "scripts/tocado.py"), "def a():\n    return 1\n")
    escribir(os.path.join(LIMPIO, ".github/workflows/audit.yml"), "name: Audit\n")
    escribir(os.path.join(LIMPIO, ".claude/hooks/arranque.sh"), "echo hola\n")
    proc_limpio = subprocess.run(
        [sys.executable, os.path.join(AQUI, "deriva_kit.py"), "--desde", KIT, LIMPIO, "--resumen"],
        capture_output=True,
        text=True,
    )
    comprobar("un proyecto al dia sale 0", proc_limpio.returncode == 0)

    proc_sin_args = subprocess.run(
        [sys.executable, os.path.join(AQUI, "deriva_kit.py")],
        capture_output=True,
        text=True,
    )
    comprobar("sin argumentos explica como se usa y no revienta", proc_sin_args.returncode == 1)
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print()
if FALLIDOS:
    print("%d comprobacion(es) fallida(s)." % FALLIDOS)
    sys.exit(1)
print("Todos los casos OK.")
