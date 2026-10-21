# Guía para usar y mostrar el prototipo de MentorIA

## Parte 1. Preparación (hacerlo el día anterior)

### 1. Verificar que la laptop tiene Python
Abrir **PowerShell** o **Símbolo del sistema** y escribir:
```
python --version
```
Debe aparecer `Python 3.10` o una versión mayor. Si sale un error, instalar Python desde python.org y marcar la casilla **"Add Python to PATH"** al instalar.

### 2. Copiar la carpeta
Copiar la carpeta `MentorIA_MVP` completa a la laptop que se usará en la exposición. No hace falta instalar nada más.

### 3. Entrar a la carpeta
En PowerShell (cambiar la ruta por la de su laptop):
```
cd "C:\ruta\a\MentorIA_MVP"
```
Atajo: abrir la carpeta en el Explorador, escribir `powershell` en la barra de direcciones y presionar Enter.

### 4. Cargar los datos de demostración
```
python seed_demo.py
```
Debe decir: `Datos de demostración cargados: 148 consultas...`.
Esto llena el tablero docente con preguntas de ejemplo y deja al estudiante E001 con un plan avanzado y 3 insignias.
**Ojo:** cada vez que se ejecuta borra todo y vuelve a empezar. Úsenlo para "reiniciar" la demo.

### 5. Probar que todo funciona
```
python run_quality.py
```
Al final debe decir `19/19 aprobados` y cinco líneas con `OK`.

### 6. Ensayar la demo completa una vez (Parte 3)

---

## Parte 2. Antes de exponer (5 minutos antes)

1. Abrir PowerShell en la carpeta (paso 3) y ejecutar `python seed_demo.py` para empezar con datos limpios (si MentorIA está abierto, primero ciérrenlo con Ctrl + C).
2. Iniciar la app:
   ```
   python app.py
   ```
   Se abre sola en el navegador, en **http://127.0.0.1:8000**. Si no se abre, copiar esa dirección en Chrome.
3. **No cerrar la ventana de PowerShell**: si se cierra, la app se apaga.
4. Poner el navegador en pantalla completa (F11) y el zoom al 110–125 % (Ctrl +) para que se lea en el proyector.

---

## Parte 3. Guion de la demo (unos 6 minutos)

### Escena 1 – El estudiante pregunta (Chatbot) · 1,5 min
Arriba deben estar seleccionados **Estudiante** y el curso **Gestión de Proyectos de Computación**, y en el campo **Código** debe decir **E001** (se puede escribir cualquier código del curso o elegirlo de la lista que aparece al hacer clic).

1. Presionar la sugerencia **"¿Cómo se calcula el CPI?"**.
   > *Decir:* "Responde con el sílabo del curso y cita de qué unidad lo sacó. Abajo se ve el tiempo de respuesta, muy por debajo de los 5 segundos que exige el acta."
2. Escribir: **¿Quién ganó el mundial 2022?** y presionar Enter.
   > *Decir:* "Si la pregunta no está en el sílabo, no inventa una respuesta: lo dice. Así controlamos el riesgo R1, la veracidad de las respuestas."
3. (Opcional) Cambiar el curso a **Interacción Humano-Computador** y preguntar **¿Qué es el cuestionario SUS?**, para mostrar que funciona con otro curso.

### Escena 2 – El plan de estudio · 1 min
1. Volver al curso **Gestión de Proyectos** y al código **E001**. Ir a la pestaña **Mi plan de estudio**.
   > *Decir:* "El estudiante indicó 4 horas por semana, 3 semanas y marcó como difíciles las unidades de cronograma y costos. El plan les da el doble de práctica."
2. Marcar la casilla de una tarea pendiente: se tacha y sube el porcentaje de avance.

### Escena 3 – Gamificación y alerta personal · 45 s
1. Ir a **Mi progreso**.
   > *Decir:* "Puntos, racha de días e insignias para motivar. Abajo, el estudiante ve su propio nivel de riesgo y recomendaciones concretas."

### Escena 4 – El docente · 2,5 min
1. Arriba, cambiar a **Docente**. Se abre el **Tablero docente**.
   > *Decir:* "El docente ve en qué temas se concentran las dudas. Aquí, valor ganado y ruta crítica: son los temas que conviene reforzar en clase. Solo se muestran datos agregados, sin nombres."
   - Bajar hasta **Consultas recientes**: arriba aparece la pregunta del CPI que se hizo en la escena 1.
     > *Decir:* "Lo que el alumno le pregunta al chatbot llega al docente al instante, sin decir quién preguntó."
2. Ir a **Alertas de riesgo**.
   > *Decir:* "Lista de estudiantes con riesgo de desaprobar, ordenada por probabilidad. El modelo detecta el 82,6 % de los casos en riesgo, por encima de la meta de 70 % del acta."
   - Presionar **Todos** para ver a los 120 alumnos del curso, no solo a los que tienen alerta. En **Buscar código** se puede escribir, por ejemplo, `E007`.
   - Hacer clic en un código, por ejemplo el primero de la lista: se abre MentorIA como ese estudiante, en *Mi progreso*, con el mismo riesgo y la misma recomendación.
     > *Decir:* "Docente y estudiante ven los mismos datos: lo que el docente ve en la alerta es lo que el alumno ve en su progreso."
   - Volver con el botón **Docente** de arriba (abre el *Tablero*) y entrar otra vez a **Alertas de riesgo**.
3. **Carga de notas por el docente.** En la tarjeta *Notas del curso*:
   1. Presionar **Seleccionar archivo** y elegir `docs/ejemplos/notas_con_error_ejemplo.csv` → **Cargar notas**. Sale un mensaje en rojo: el archivo tiene una columna `nombre`.
      > *Decir:* "Las notas no se conectan con el sistema de USIL, porque está fuera del alcance, ni las escribe el alumno. Las carga el docente desde un Excel, y el sistema rechaza cualquier archivo con nombres, DNI o correos."
   2. Elegir `docs/ejemplos/notas_GPC_ejemplo.csv` → **Cargar notas**. Aparece *"Se cargaron 20 estudiantes; 7 quedan con alerta"* y la tabla cambia a los códigos E301–E320.
      > *Decir:* "Acepta el formato de Excel en español, con punto y coma y coma decimal, y calcula el riesgo al instante."
   3. Para dejar la demo como estaba: **Restaurar datos simulados**. Mientras el CSV está cargado, E001 no existe en ese curso; en la vista estudiante aparecen los códigos E301–E320.
   - **Descargar plantilla** baja un CSV de ejemplo con las columnas correctas, para el docente.

### Escena 5 – La calidad (opcional, 30 s)
En una segunda ventana de PowerShell, en la misma carpeta:
```
python run_quality.py
```
> *Decir:* "Estas son las 19 pruebas automáticas del plan de calidad. Se corren en segundos antes de cada hito."

### Para cerrar
En PowerShell, presionar **Ctrl + C** para apagar la app.

---

## Parte 4. Mostrarlo en un celular (opcional)

1. La laptop y el celular deben estar en **la misma red Wi-Fi**.
2. Iniciar la app con:
   ```
   python app.py --red
   ```
3. La consola muestra una línea `Desde el celular: http://192.168.x.x:8000`. Escribir esa dirección en el navegador del celular.
4. Si Windows pregunta por el **Firewall**, presionar **Permitir acceso**.

La red Wi-Fi de la universidad a veces bloquea la conexión entre equipos. Si no funciona, usen el **punto de acceso (hotspot)** de un celular para conectar ambos equipos, o muestren la captura `docs/capturas/06_movil.png`.

---

### Versión en internet (respaldo)
El MVP también está publicado en **https://mentoria-mvp.onrender.com**, con los mismos datos de demostración. Sirve para abrirlo desde cualquier celular sin estar en la misma Wi-Fi, o si falla la laptop.
- Está en el plan gratuito de Render: **se duerme tras 15 minutos sin visitas** y tarda alrededor de un minuto en despertar. Ábranlo 5 minutos antes de exponer.
- Cada vez que se reinicia vuelve a los datos de demostración. Es público: no carguen datos reales.

---

## Parte 5. Si algo falla

| Problema | Solución |
|---|---|
| `python` no se reconoce | Probar con `py app.py`. Si tampoco funciona, reinstalar Python con "Add to PATH" |
| "Address already in use" o el puerto está ocupado | `python app.py --puerto 8080` y abrir http://127.0.0.1:8080 |
| El tablero sale vacío | Cerrar la app (Ctrl + C), ejecutar `python seed_demo.py` y volver a iniciarla |
| `seed_demo.py` dice "MentorIA está abierto" | Cerrar la app con Ctrl + C en su ventana y volver a ejecutar `seed_demo.py` |
| El código E001 no aparece en Gestión de Proyectos | Quedó cargado el CSV de ejemplo: en *Docente → Alertas de riesgo* presionar **Restaurar datos simulados** |
| La página dice "No se pudo conectar con el servidor" | Se cerró la ventana de PowerShell: volver a ejecutar `python app.py` |
| No hay laptop o falla todo | Mostrar las capturas de `docs/capturas/` (son las mismas figuras del documento) |

---

## Parte 6. Preguntas que podría hacer el docente

- **¿Usa inteligencia artificial de verdad?** Recupera el fragmento correcto del sílabo con un índice vectorial (la parte "R" de RAG). Para redactar la respuesta puede usar Gemini en su capa gratuita si se configura la clave `GEMINI_API_KEY`; sin clave responde con las oraciones del sílabo. El modelo de alertas es una regresión logística entrenada con los datos simulados.
- **¿Por qué no usaron Chroma o FAISS, como decía la arquitectura?** El índice local cumple la misma función y no requiere instalar nada. Se registró como un cambio de impacto bajo, que aprueba el gerente.
- **¿De dónde salen las notas? ¿Se sincronizan con USIL?** No se sincronizan: la integración con los sistemas de notas está excluida en el acta. Tampoco las ingresa el alumno, porque podría alterarlas. El docente exporta un extracto anonimizado (código, PC1, PC2, asistencia, tareas) y lo carga en la pestaña *Alertas de riesgo*.
- **¿Quién crea el plan de estudio?** El sistema, con lo que indica el alumno: horas por semana, semanas hasta el examen y unidades difíciles. Toma los temas del sílabo, da el doble de práctica a las unidades difíciles y reparte las tareas sin pasarse de las horas. No lo redacta la IA: es una regla fija, para que siempre respete el sílabo.
- **¿De dónde salen los sílabos que usa el chatbot? ¿Quién los sube?** Hoy los carga el equipo. Los sílabos son archivos de texto en `data/silabos/`, uno por curso, con las unidades (`#`) y los temas (`##`); cada tema es un fragmento que el chatbot busca y cita. Se indexan solos al iniciar la app. En el plan, los docentes piloto entregan el sílabo oficial, Chapoñan hace el seguimiento, Vega lo pasa al formato e indexa (paquete 1.3.1) y Mendoza verifica las respuestas (LC-06). Los dos sílabos de la demo son de referencia; reemplazarlos por los oficiales es un pendiente del hito H6. Más adelante se puede agregar que el docente lo suba desde la plataforma, igual que las notas.
- **¿Las consultas del tablero son reales?** Son preguntas de demostración que carga `seed_demo.py` (por eso tienen casi la misma hora). Las que se hacen en vivo en la vista estudiante aparecen arriba de la lista.
- **¿Los datos son reales?** No. Son 240 registros sintéticos con códigos E001–E240; el proyecto excluye usar datos reales de USIL.
- **¿Está terminado?** El chatbot cerró su hito (H4). Los planes de estudio, las alertas y el tablero funcionan y están en pruebas hasta el 30/10. Falta desplegarlo en el servidor del patrocinador y validarlo con los docentes antes del piloto (H6, 06/11).
