# Reporte de calidad – MentorIA MVP

Fecha: 21/10/2026 13:51 · Entorno: Python 3.12.10 · Windows 11

**19 de 19 casos aprobados** en 3.47 s.

## Criterios de aceptación

| Req. | Criterio | Meta | Resultado | Cumple |
|---|---|---|---|---|
| RF-01 | Sílabos de los 2 cursos piloto indexados | 100 % | 100% | Sí |
| RF-02 | Recuperación del tema correcto (top 3) | ≥ 90 % | 100.0% | Sí |
| RF-03 | Rechazo de preguntas fuera del sílabo | 100 % | 100% | Sí |
| RNF-01 | Tiempo de respuesta promedio del chatbot | < 5 s | 14 ms | Sí |
| RNF-02 | Sensibilidad del modelo de alertas | ≥ 70 % | 82.6% | Sí |

## Casos de prueba

| Caso | Req. | Descripción | Resultado |
|---|---|---|---|
| CP-01 | RF-01 | El 100 % de los temas de los sílabos de los 2 cursos piloto queda indexado. | Aprobado |
| CP-02 | RF-02 | La respuesta usa el fragmento pertinente del sílabo y cita curso, unidad y tema. | Aprobado |
| CP-03 | RF-02 | El tema correcto aparece entre los 3 primeros fragmentos en al menos el 90 % del conjunto de referencia. | Aprobado |
| CP-04 | RF-03 | Las preguntas ajenas al sílabo se rechazan sin inventar respuesta (riesgo R1). | Aprobado |
| CP-05 | RF-04 | Cada consulta queda registrada con su tema para alimentar el tablero docente. | Aprobado |
| CP-06 | RF-05 | Se genera un plan para un estudiante de prueba en cada curso piloto, priorizando las unidades débiles. | Aprobado |
| CP-07 | RF-05 | El plan rechaza horas o semanas fuera de rango. | Aprobado |
| CP-08 | RF-06 | Completar tareas otorga puntos, calcula la racha de días e insignias. | Aprobado |
| CP-09 | RF-07 | El modelo devuelve probabilidades entre 0 y 1 y asigna más riesgo a peores notas y asistencia. | Aprobado |
| CP-10 | RF-08 | El estudiante ve su nivel de riesgo (alto/medio/bajo) y recomendaciones. | Aprobado |
| CP-11 | RF-09 | El tablero agrega las consultas por tema y coincide con lo registrado. | Aprobado |
| CP-12 | RF-10 | El docente ve a sus estudiantes ordenados por riesgo; solo se marcan los que superan el umbral. | Aprobado |
| CP-13 | RNF-01 | El tiempo de respuesta promedio del chatbot, medido extremo a extremo, es menor a 5 s. | Aprobado |
| CP-14 | RNF-02 | El modelo detecta al menos el 70 % de los estudiantes en riesgo en los datos simulados de prueba. | Aprobado |
| CP-15 | RNF-03 | Los datos son simulados y anonimizados: solo códigos E###, sin nombres, DNI ni correos. | Aprobado |
| CP-16 | RNF-04 | La API valida las entradas y la interfaz no inserta HTML sin escapar (OWASP). | Aprobado |
| CP-17 | RNF-05 | La interfaz es accesible desde web y móvil (viewport y diseño adaptable). | Aprobado |
| CP-18 | RF-02, RF-05, RF-06, RF-09 | Flujo completo: pregunta, plan, tarea completada, logros y tablero. | Aprobado |
| CP-19 | RF-11 | El docente carga un CSV anonimizado de notas; se rechazan datos personales y valores fuera de rango. | Aprobado |
