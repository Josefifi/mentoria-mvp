"""Persistencia en SQLite (consultas al chatbot, planes, tareas y gamificación)."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "mentoria.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante TEXT NOT NULL,
    curso TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    unidad TEXT,
    tema TEXT,
    confianza REAL,
    en_silabo INTEGER,
    ms REAL,
    fecha TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS planes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante TEXT NOT NULL,
    curso TEXT NOT NULL,
    horas_semana REAL,
    semanas INTEGER,
    creado TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES planes(id),
    semana INTEGER,
    unidad TEXT,
    tema TEXT,
    actividad TEXT,
    minutos INTEGER,
    completada INTEGER DEFAULT 0,
    completada_en TEXT
);
CREATE TABLE IF NOT EXISTS logros (
    estudiante TEXT NOT NULL,
    insignia TEXT NOT NULL,
    obtenida TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (estudiante, insignia)
);
"""


def conectar(ruta=None):
    con = sqlite3.connect(str(ruta or DB_PATH), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con
