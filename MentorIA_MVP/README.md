# MentorIA – MVP (Grupo 1)

Asistente académico con IA para estudiantes y docentes de USIL. Proyecto del curso
Gestión de Proyectos de Computación (2026-02).

## Cómo ejecutarlo

Solo necesita **Python 3.10 o superior**; no hay que instalar librerías.

```
python seed_demo.py     # (opcional) carga datos de demostración para la exposición
python app.py           # abre http://127.0.0.1:8000 en el navegador
python app.py --red     # además permite entrar desde un celular en la misma red Wi-Fi
python run_quality.py   # ejecuta las 19 pruebas y genera reports/reporte_calidad.md
```

Para usar el modelo generativo (capa gratuita de Gemini), definir la variable
`GEMINI_API_KEY` antes de iniciar. Sin clave, el chatbot responde en modo extractivo
con las oraciones del sílabo; en ambos modos cita la fuente y rechaza lo que no está
en el sílabo.

## Módulos

| Módulo | EDT | Archivo |
|---|---|---|
| Base de conocimiento RAG y chatbot | 1.3.1 – 1.3.2 | `mentoria/rag.py` |
| Planes de estudio y gamificación | 1.3.3 | `mentoria/planes.py` |
| Alertas tempranas de riesgo y carga de notas (CSV) | 1.3.4 | `mentoria/alertas.py`, `mentoria/cargas.py` |
| Tablero docente | 1.3.5 | `mentoria/tablero.py` |
| Integración (API + interfaz web/móvil) | 1.3.6 | `mentoria/server.py`, `static/` |
| Pruebas | 1.4.1 – 1.4.3 | `tests/`, `run_quality.py` |

## Datos

- `data/silabos/`: sílabos de referencia de los 2 cursos piloto (GPC e IHC). Para
  reemplazarlos por los oficiales basta con dejar los `.md` con el mismo formato
  (`#` unidad, `##` tema); el índice se reconstruye solo.
- `data/estudiantes_simulados.csv`: 240 registros sintéticos y anonimizados
  (códigos E001–E240), conforme a la Ley N.° 29733. No contiene datos reales.
- Carga de notas: el docente sube en *Alertas de riesgo* un CSV con `codigo, nota_pc1,
  nota_pc2, asistencia, tareas` (ejemplos en `docs/ejemplos/`). Se guarda en `data/cargas/`
  y reemplaza los datos simulados de ese curso; `seed_demo.py` lo restablece.
- Guía para la exposición: `GUIA_DEMO.md`.
