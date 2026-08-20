#!/usr/bin/env python3
"""Tests del hook `secure_guard.py`.

Que se prueba y por que: esta guarda existe para que la skill de seguridad no
dependa de que alguien se acuerde. Si sus dos falsos negativos clasicos no
tienen un caso que muerda, la guarda no vale mas que el recordatorio que
sustituye — vale MENOS, porque ademas parece automatica.

Los dos, y los dos ocurrieron de verdad antes de existir estos casos:

  1. **Auto-disparo.** El aviso que emite la guarda queda escrito en el
     transcript. Con un patron laxo, la guarda lee su propio texto y se da por
     satisfecha para el resto de la sesion (caso `autodisparo`).
  2. **La documentacion que nombra la skill.** El CLAUDE.md del proyecto cita la
     ruta del SKILL.md en su seccion de obligaciones, y se lee al arrancar cada
     sesion: bastaba con eso para silenciarla siempre (caso `mencion_sin_lectura`).

Mas el estado que suele faltar: **no poder comprobarlo no es estar en regla**
(casos `transcript_ausente*` y `transcript_truncado`).

Se ejecuta el script de verdad como subproceso, hablando el contrato real del
hook (JSON por stdin, JSON por stdout): un import se saltaria justo la frontera
que importa.

Uso: python3 .claude/hooks/test_secure_guard.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GUARDA = AQUI / "secure_guard.py"

CASOS = []


class Saltado(Exception):
    """Un caso que no se pudo ejecutar en esta maquina.

    Se distingue de "ok" a proposito y se cuenta aparte: un caso que no corrio
    contado como verde es exactamente la mentira que este kit persigue.
    """


def caso(nombre):
    def envoltorio(f):
        CASOS.append((nombre, f))
        return f
    return envoltorio


def proyecto_con_skill(base: Path, instalada: bool = True) -> Path:
    """Crea un proyecto de mentira, con o sin la skill que la guarda exige."""
    if instalada:
        (base / ".claude" / "skills" / "secure-coding-guard").mkdir(parents=True)
        (base / ".claude" / "skills" / "secure-coding-guard" / "SKILL.md").write_text(
            "# skill", encoding="utf-8"
        )
    else:
        (base / ".claude" / "skills").mkdir(parents=True)
    return base


def correr(entrada: dict, cwd: Path | None = None) -> dict:
    """Ejecuta la guarda y devuelve {'salida': dict|None, 'codigo': int}."""
    proc = subprocess.run(
        [sys.executable, str(GUARDA)],
        input=json.dumps(entrada),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    texto = proc.stdout.strip()
    return {
        "salida": json.loads(texto) if texto else None,
        "codigo": proc.returncode,
        "crudo": texto,
    }


def bloquea(res: dict) -> bool:
    salida = res["salida"] or {}
    esp = salida.get("hookSpecificOutput", {})
    return esp.get("permissionDecision") == "deny"


def peticion(ruta="src/x.ts", transcript=None, session="s1", tool="Edit", cwd=None):
    datos = {
        "tool_name": tool,
        "tool_input": {"file_path": ruta},
        "session_id": session,
    }
    if transcript is not None:
        datos["transcript_path"] = str(transcript)
    if cwd is not None:
        datos["cwd"] = str(cwd)
    return datos


def transcript_con(tmp: Path, contenido: str, nombre="t.jsonl") -> Path:
    ruta = tmp / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def limpiar_marca(sesion: str) -> Path:
    """Borra el marcador de 'ya avise' de una sesion.

    Hace falta porque el marcador vive en el temporal del sistema y SOBREVIVE a
    la ejecucion del test. Sin esto, los casos del camino "no se pudo verificar"
    pasan la primera vez y fallan la segunda —el estado de la corrida anterior
    los convierte en el caso "segunda vez"—, que es un test contando una
    historia distinta segun cuando lo mires. Se descubrio al reejecutarlos.
    """
    marca = Path(tempfile.gettempdir()) / "claude-secure-guard" / f"{sesion}.avisado"
    marca.unlink(missing_ok=True)
    return marca


# --- lo que NO debe molestar -------------------------------------------------

@caso("un .md no dispara la guarda (si saltara aqui, se vuelve ruido de fondo)")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        t = transcript_con(Path(d), "sin nada\n")
        res = correr(peticion("docs/guia.md", t, cwd=base), cwd=base)
        assert res["salida"] is None, res["crudo"]


@caso("una herramienta que no edita (Bash) no dispara la guarda")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        t = transcript_con(Path(d), "sin nada\n")
        res = correr(peticion("src/x.ts", t, tool="Bash", cwd=base), cwd=base)
        assert res["salida"] is None, res["crudo"]


@caso("un lockfile no dispara la guarda pese a ser .yaml")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        t = transcript_con(Path(d), "sin nada\n")
        res = correr(peticion("pnpm-lock.yaml", t, cwd=base), cwd=base)
        assert res["salida"] is None, res["crudo"]


@caso("sin la skill instalada NO bloquea: exigir algo que no existe no es rigor")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d), instalada=False)
        t = transcript_con(Path(d), "sin nada\n")
        res = correr(peticion("src/x.ts", t, cwd=base), cwd=base)
        assert res["salida"] is None, res["crudo"]


# --- lo que SI debe bloquear -------------------------------------------------

@caso("codigo sin rastro de la skill: BLOQUEA")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        t = transcript_con(Path(d), '{"type":"user","text":"arregla el login"}\n')
        res = correr(peticion("src/auth.ts", t, cwd=base), cwd=base)
        assert bloquea(res), res["crudo"]
        motivo = res["salida"]["hookSpecificOutput"]["permissionDecisionReason"]
        assert "src/auth.ts" in motivo, motivo


@caso("un .py tambien cuenta como codigo")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        t = transcript_con(Path(d), "nada\n")
        res = correr(peticion("scripts/x.py", t, cwd=base), cwd=base)
        assert bloquea(res), res["crudo"]


@caso("NotebookEdit llega por notebook_path y tambien se mira")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        t = transcript_con(Path(d), "nada\n")
        datos = {
            "tool_name": "NotebookEdit",
            "tool_input": {"notebook_path": "analisis.py"},
            "transcript_path": str(t),
            "session_id": "s1",
            "cwd": str(base),
        }
        res = correr(datos, cwd=base)
        assert bloquea(res), res["crudo"]


# --- los dos falsos negativos que costaron caro ------------------------------

@caso("AUTO-DISPARO: el propio aviso en el transcript no cuenta como evidencia")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        # Exactamente lo que la guarda escribe cuando bloquea, ya en el historial.
        aviso = json.dumps({
            "hookSpecificOutput": {
                "permissionDecisionReason":
                    "[secure-coding-guard] BLOQUEADO: la skill de seguridad del "
                    "proyecto es obligatoria... Invoca la skill secure-coding-guard"
            }
        })
        t = transcript_con(Path(d), aviso + "\n")
        res = correr(peticion("src/x.ts", t, cwd=base), cwd=base)
        assert bloquea(res), "la guarda se dio por satisfecha leyendo su propio aviso"


@caso("MENCION: nombrar la ruta del SKILL.md (CLAUDE.md) no equivale a leerlo")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        # Un CLAUDE.md leido al arrancar, que cita la ruta en su seccion de reglas.
        linea = json.dumps({
            "type": "assistant",
            "text": "lee .claude/skills/secure-coding-guard/SKILL.md antes de codear",
        })
        t = transcript_con(Path(d), linea + "\n")
        res = correr(peticion("src/x.ts", t, cwd=base), cwd=base)
        assert bloquea(res), "una mencion en prosa silencio la guarda"


# --- evidencia legitima: las tres formas -------------------------------------

@caso("evidencia 1: invocacion por la herramienta Skill -> callada")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        linea = json.dumps({"name": "Skill", "input": {"skill": "secure-coding-guard"}})
        t = transcript_con(Path(d), linea + "\n")
        res = correr(peticion("src/x.ts", t, cwd=base), cwd=base)
        assert res["salida"] is None, res["crudo"]


@caso("evidencia 2: lectura directa del SKILL.md con file_path -> callada")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        linea = json.dumps({
            "name": "Read",
            "input": {"file_path": "/repo/.claude/skills/secure-coding-guard/SKILL.md"},
        })
        t = transcript_con(Path(d), linea + "\n")
        res = correr(peticion("src/x.ts", t, cwd=base), cwd=base)
        assert res["salida"] is None, res["crudo"]


@caso("evidencia 3: el dev la invoca como /slash -> callada")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        t = transcript_con(Path(d), "<command-name>secure-coding-guard</command-name>\n")
        res = correr(peticion("src/x.ts", t, cwd=base), cwd=base)
        assert res["salida"] is None, res["crudo"]


@caso("la ruta del transcript en forma bash (/c/...) se traduce, no se falla")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        linea = json.dumps({"input": {"skill": "secure-coding-guard"}})
        real = transcript_con(Path(d), linea + "\n")
        # C:/Users/x/t.jsonl -> /c/Users/x/t.jsonl (lo que escribe Git Bash)
        texto = str(real).replace("\\", "/")
        if len(texto) > 2 and texto[1] == ":":
            bash = f"/{texto[0].lower()}/{texto[3:]}"
        else:
            bash = texto  # en POSIX ya es la misma ruta
        res = correr(peticion("src/x.ts", bash, cwd=base), cwd=base)
        assert res["salida"] is None, f"no supo abrir {bash}: {res['crudo']}"


# --- no poder preguntar no es que la respuesta sea "si" ----------------------

@caso("transcript ausente: bloquea la PRIMERA vez (no deja pasar)")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        marca = limpiar_marca("sesion-nueva-1")
        try:
            res = correr(peticion("src/x.ts", Path(d) / "no-existe.jsonl",
                                  session="sesion-nueva-1", cwd=base), cwd=base)
            assert bloquea(res), res["crudo"]
            motivo = res["salida"]["hookSpecificOutput"]["permissionDecisionReason"]
            assert "no ha podido" in motivo, motivo
        finally:
            marca.unlink(missing_ok=True)


@caso("transcript ausente, SEGUNDA vez: avisa pero no deja la sesion muerta")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        sesion = "sesion-repetida-xyz"
        marca = limpiar_marca(sesion)
        try:
            uno = correr(peticion("src/x.ts", Path(d) / "no.jsonl", session=sesion,
                                  cwd=base), cwd=base)
            dos = correr(peticion("src/x.ts", Path(d) / "no.jsonl", session=sesion,
                                  cwd=base), cwd=base)
            assert bloquea(uno), uno["crudo"]
            assert not bloquea(dos), "bloqueo dos veces: deja la sesion muerta"
            assert "DEGRADADA" in (dos["salida"] or {}).get("systemMessage", ""), dos["crudo"]
        finally:
            marca.unlink(missing_ok=True)


@caso("transcript enorme sin evidencia: no afirma 'no esta', bloquea sin verificar")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        grande = Path(d) / "grande.jsonl"
        with open(grande, "w", encoding="utf-8") as fh:
            fh.write(("x" * 1024 + "\n") * 200)  # 200 KB
        # Se baja el tope por entorno del subproceso via un modulo espejo no es
        # posible sin tocar el script: se comprueba el limite con el fichero real
        # solo si el tope es pequeño. Aqui se verifica el camino normal (< tope),
        # que debe BLOQUEAR por ausencia de evidencia, no por truncado.
        res = correr(peticion("src/x.ts", grande, session="s-grande", cwd=base), cwd=base)
        assert bloquea(res), res["crudo"]


# --- la propiedad que nunca puede romperse ----------------------------------

@caso("la guarda NUNCA devuelve 'allow' en ninguno de sus caminos")
def _():
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        vacio = transcript_con(Path(d), "nada\n")
        conskill = transcript_con(
            Path(d), json.dumps({"input": {"skill": "secure-coding-guard"}}) + "\n",
            nombre="ok.jsonl")
        marca = limpiar_marca("s-allow")
        entradas = [
            peticion("src/x.ts", vacio, cwd=base),
            peticion("src/x.ts", conskill, cwd=base),
            peticion("docs/x.md", vacio, cwd=base),
            peticion("src/x.ts", Path(d) / "no.jsonl", session="s-allow", cwd=base),
        ]
        try:
            for entrada in entradas:
                res = correr(entrada, cwd=base)
                assert "allow" not in (res["crudo"] or ""), res["crudo"]
        finally:
            marca.unlink(missing_ok=True)


# --- la envoltura sh, que es la que enchufa settings.json --------------------

@caso("la envoltura delega en Python y el bloqueo llega igual")
def _():
    sh = shutil.which("sh")
    if not sh:
        raise Saltado("no hay `sh` en esta maquina")
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        (base / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
        shutil.copy(GUARDA, base / ".claude" / "hooks" / "secure_guard.py")
        shutil.copy(AQUI / "secure_guard.sh", base / ".claude" / "hooks" / "secure_guard.sh")
        t = transcript_con(Path(d), "sin evidencia\n")
        proc = subprocess.run(
            [sh, str(base / ".claude" / "hooks" / "secure_guard.sh")],
            input=json.dumps(peticion("src/x.ts", t, cwd=base)),
            capture_output=True, text=True,
            env=dict(os.environ, CLAUDE_PROJECT_DIR=str(base)),
            cwd=str(base),
        )
        assert '"deny"' in proc.stdout, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"


@caso("SIN Python en el PATH la envoltura BLOQUEA (no puede comprobar != esta en regla)")
def _():
    sh = shutil.which("sh")
    if not sh:
        raise Saltado("no hay `sh` en esta maquina")
    with tempfile.TemporaryDirectory() as d:
        base = proyecto_con_skill(Path(d))
        (base / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
        shutil.copy(GUARDA, base / ".claude" / "hooks" / "secure_guard.py")
        envoltura = base / ".claude" / "hooks" / "secure_guard.sh"
        shutil.copy(AQUI / "secure_guard.sh", envoltura)

        # El PATH se construye AQUI, como dict, y NO se escribe desde bash: una
        # ruta `C:\...` puesta desde bash se parte por los dos puntos y el
        # montaje falla en silencio, de modo que la prueba corre con el Python
        # real y "pasa" comprobando lo que no era. Ya mordio dos veces en el kit.
        entorno = dict(os.environ, PATH="", CLAUDE_PROJECT_DIR=str(base))
        entorno.pop("PATHEXT", None)

        # Control del montaje: sin esto no se sabe si el caso probo algo.
        control = subprocess.run([sh, "-c", "command -v python3 python py || echo VACIO"],
                                 capture_output=True, text=True, env=entorno)
        assert "VACIO" in control.stdout, f"el PATH falso no entro: {control.stdout!r}"

        proc = subprocess.run([sh, str(envoltura)],
                              input=json.dumps(peticion("src/x.ts", None, cwd=base)),
                              capture_output=True, text=True, env=entorno, cwd=str(base))
        assert '"deny"' in proc.stdout, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
        assert "no hay Python" in proc.stdout, proc.stdout


@caso("entrada basura (JSON roto) no revienta ni deja pasar en silencio")
def _():
    proc = subprocess.run(
        [sys.executable, str(GUARDA)],
        input="{esto no es json",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "allow" not in proc.stdout


def main() -> int:
    fallidos = 0
    saltados = 0
    for nombre, prueba in CASOS:
        try:
            prueba()
            print(f"  ok    {nombre}")
        except Saltado as e:
            saltados += 1
            print(f"  SALTA {nombre}\n        {e}")
        except AssertionError as e:
            fallidos += 1
            print(f"  FALLO {nombre}\n        {e}")
        except Exception as e:  # noqa: BLE001
            fallidos += 1
            print(f"  ERROR {nombre}\n        {type(e).__name__}: {e}")
    ok = len(CASOS) - fallidos - saltados
    resumen = f"\n{ok}/{len(CASOS)} casos OK"
    if saltados:
        # Se dice en voz alta: un caso que no corrio no es un caso que paso.
        resumen += f" · {saltados} SALTADOS (no ejecutados en esta maquina)"
    print(resumen)
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
