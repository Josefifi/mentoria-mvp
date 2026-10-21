"""Servidor web de MentorIA (EDT 1.3.6): API JSON + interfaz web/móvil.

Solo usa la biblioteca estándar de Python para que el MVP se ejecute en
cualquier equipo del equipo o del patrocinador sin instalar dependencias.
"""
import json
import mimetypes
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import alertas, cargas, planes, rag, tablero
from .db import conectar

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
VERSION = "0.9.1"
CODIGO = re.compile(r"^E\d{3}$")


class MentorIA:
    """Estado compartido de la aplicación."""

    def __init__(self, ruta_db=None, dir_cargas=None):
        self.indice = rag.IndiceRAG.cargar()
        self.modelo = alertas.ModeloRiesgo.cargar()
        self.simulados = alertas.cargar_dataset()
        self.dir_cargas = Path(dir_cargas) if dir_cargas else cargas.DIR_CARGAS
        self.origen = {}  # curso -> "simulado" | "cargado por el docente"
        self.dataset = list(self.simulados)
        for c in {r["curso"] for r in self.simulados}:
            ruta = self._ruta_carga(c)
            if ruta.exists():
                self._reemplazar_curso(c, cargas.leer_guardado(ruta, c))
        self._indexar()
        self.con = conectar(ruta_db)
        self.lock = threading.Lock()

    # --- notas del curso -----------------------------------------------------
    def _ruta_carga(self, curso):
        return self.dir_cargas / f"notas_{curso}.csv"

    def _indexar(self):
        self.registros = {r["codigo"]: r for r in self.dataset}

    def _reemplazar_curso(self, curso, registros):
        self.dataset = [r for r in self.dataset if r["curso"] != curso] + registros
        self.origen[curso] = "cargado por el docente"

    def _validar_curso(self, curso):
        if curso not in {c["codigo"] for c in self.indice.cursos()}:
            raise ValueError("Curso no válido.")

    def cargar_notas(self, curso, texto):
        self._validar_curso(curso)
        registros = cargas.leer_csv(texto, curso)
        otros = {r["codigo"] for r in self.dataset if r["curso"] != curso}
        choque = sorted({r["codigo"] for r in registros} & otros)
        if choque:
            raise ValueError("Estos códigos ya pertenecen a otro curso: " + ", ".join(choque[:5]) + ".")
        with self.lock:
            cargas.guardar(registros, self._ruta_carga(curso))
            self._reemplazar_curso(curso, registros)
            self._indexar()
        lista = self.alertas(curso)
        return {"curso": curso, "registros": len(registros), "con_alerta": sum(a["alerta"] for a in lista),
                "origen": self.origen[curso]}

    def restaurar_notas(self, curso):
        self._validar_curso(curso)
        with self.lock:
            ruta = self._ruta_carga(curso)
            if ruta.exists():
                ruta.unlink()
            self.dataset = [r for r in self.dataset if r["curso"] != curso] + \
                           [r for r in self.simulados if r["curso"] == curso]
            self.origen.pop(curso, None)
            self._indexar()
        return {"curso": curso, "origen": "simulado"}

    def origen_notas(self, curso):
        return self.origen.get(curso, "simulado")

    # --- casos de uso ------------------------------------------------------
    def chat(self, estudiante, curso, pregunta):
        self._validar_estudiante(estudiante)
        r = rag.responder(self.indice, pregunta, curso)
        if pregunta and pregunta.strip():
            with self.lock:
                self.con.execute("""INSERT INTO consultas (estudiante, curso, pregunta, unidad, tema, confianza,
                                    en_silabo, ms) VALUES (?,?,?,?,?,?,?,?)""",
                                 (estudiante, curso, pregunta.strip()[:500], r["unidad"], r["tema"],
                                  r["confianza"], int(r["en_silabo"]), r["ms"]))
                self.con.commit()
        return r

    def riesgo(self, estudiante):
        self._validar_estudiante(estudiante)
        return alertas.evaluar_estudiante(self.modelo, self.registros[estudiante])

    def crear_plan(self, d):
        self._validar_estudiante(d.get("estudiante"))
        with self.lock:
            return planes.generar_plan(self.con, self.indice, d["estudiante"], d["curso"],
                                       float(d.get("horas_semana", 4)), int(d.get("semanas", 4)),
                                       d.get("unidades_debiles", []))

    def plan(self, estudiante, curso):
        with self.lock:
            return planes.plan_vigente(self.con, estudiante, curso)

    def completar(self, tarea_id, estudiante):
        with self.lock:
            return planes.completar_tarea(self.con, tarea_id, estudiante)

    def logros(self, estudiante):
        with self.lock:
            return planes.gamificacion(self.con, estudiante)

    def tablero(self, curso):
        with self.lock:
            return tablero.metricas_curso(self.con, self.indice, self.modelo, self.dataset, curso)

    def alertas(self, curso):
        return tablero.alertas_curso(self.modelo, self.dataset, curso)

    def _validar_estudiante(self, codigo):
        if not codigo or not CODIGO.match(codigo) or codigo not in self.registros:
            raise ValueError("Código de estudiante no válido.")


def crear_handler(app):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"MentorIA/{VERSION}"

        def log_message(self, fmt, *args):  # silencio en consola salvo errores
            pass

        def _json(self, datos, estado=200):
            cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
            self.send_response(estado)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def _cuerpo(self, limite=20000):
            largo = int(self.headers.get("Content-Length") or 0)
            if largo > limite:
                raise ValueError("Solicitud demasiado grande.")
            return json.loads(self.rfile.read(largo) or b"{}")

        def _estatico(self, ruta):
            archivo = (STATIC_DIR / (ruta.lstrip("/") or "index.html")).resolve()
            if STATIC_DIR not in archivo.parents or not archivo.is_file():
                archivo = STATIC_DIR / "index.html"
            datos = archivo.read_bytes()
            self.send_response(200)
            tipo = mimetypes.guess_type(str(archivo))[0] or "application/octet-stream"
            self.send_header("Content-Type", tipo + ("; charset=utf-8" if tipo.startswith("text") else ""))
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            partes = [p for p in u.path.split("/") if p]
            try:
                if not partes or partes[0] != "api":
                    return self._estatico(u.path)
                ruta = partes[1:]
                if ruta == ["health"]:
                    return self._json({"estado": "ok", "version": VERSION,
                                       "fragmentos_indexados": len(app.indice.fragmentos),
                                       "modo_generacion": "generativo" if rag.os.environ.get("GEMINI_API_KEY")
                                       else "extractivo"})
                if ruta == ["cursos"]:
                    return self._json(app.indice.cursos())
                if ruta == ["estudiantes"]:
                    curso = q.get("curso")
                    return self._json(sorted(r["codigo"] for r in app.dataset if not curso or r["curso"] == curso))
                if len(ruta) == 3 and ruta[0] == "estudiantes" and ruta[2] == "riesgo":
                    return self._json(app.riesgo(ruta[1]))
                if len(ruta) == 3 and ruta[0] == "estudiantes" and ruta[2] == "logros":
                    return self._json(app.logros(ruta[1]))
                if len(ruta) == 3 and ruta[0] == "estudiantes" and ruta[2] == "plan":
                    return self._json(app.plan(ruta[1], q.get("curso", "GPC")))
                if ruta == ["tablero"]:
                    return self._json(app.tablero(q.get("curso", "GPC")))
                if ruta == ["alertas"]:
                    return self._json(app.alertas(q.get("curso", "GPC")))
                if ruta == ["notas", "origen"]:
                    return self._json({"curso": q.get("curso", "GPC"), "origen": app.origen_notas(q.get("curso", "GPC"))})
                if ruta == ["notas", "plantilla"]:
                    return self._json({"csv": cargas.PLANTILLA})
                if ruta == ["modelo"]:
                    return self._json({"umbral": app.modelo.umbral, "metricas": app.modelo.metricas})
                return self._json({"error": "Recurso no encontrado."}, 404)
            except ValueError as e:
                return self._json({"error": str(e)}, 400)

        def do_POST(self):
            partes = [p for p in urlparse(self.path).path.split("/") if p]
            try:
                es_carga = partes == ["api", "notas"]
                d = self._cuerpo(cargas.MAX_BYTES * 2 if es_carga else 20000)
                if es_carga:
                    return self._json(app.cargar_notas(d.get("curso"), d.get("csv", "")), 201)
                if partes == ["api", "notas", "restaurar"]:
                    return self._json(app.restaurar_notas(d.get("curso")))
                if partes == ["api", "chat"]:
                    return self._json(app.chat(d.get("estudiante"), d.get("curso"), d.get("pregunta", "")))
                if partes == ["api", "planes"]:
                    return self._json(app.crear_plan(d), 201)
                if len(partes) == 4 and partes[:2] == ["api", "tareas"] and partes[3] == "completar":
                    return self._json(app.completar(int(partes[2]), d.get("estudiante")))
                return self._json({"error": "Recurso no encontrado."}, 404)
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                return self._json({"error": str(e) or "Solicitud no válida."}, 400)

    return Handler


def iniciar(host="127.0.0.1", puerto=8000, ruta_db=None):
    app = MentorIA(ruta_db)
    servidor = ThreadingHTTPServer((host, puerto), crear_handler(app))
    return servidor, app
