---
codigo: GPC
curso: Gestión de Proyectos de Computación
version: Sílabo de referencia 2026-02 (versión de prueba para el piloto)
---

# Unidad 1: Fundamentos de la dirección de proyectos

## Proyecto, programa y portafolio
Un proyecto es un esfuerzo temporal que se lleva a cabo para crear un producto, servicio o resultado único. Es temporal porque tiene un inicio y un final definidos, y es único porque su resultado no se repite exactamente. Un programa agrupa proyectos relacionados que se gestionan de forma coordinada para obtener beneficios que no se lograrían por separado. Un portafolio reúne proyectos, programas y operaciones que se gestionan en conjunto para alcanzar los objetivos estratégicos de la organización.

## El PMI y la Guía del PMBOK
El Project Management Institute (PMI) publica la Guía del PMBOK, que reúne buenas prácticas para dirigir proyectos. La sexta edición organiza el trabajo en cinco grupos de procesos (inicio, planificación, ejecución, monitoreo y control, y cierre) y diez áreas de conocimiento: integración, alcance, cronograma, costos, calidad, recursos, comunicaciones, riesgos, adquisiciones e interesados. La séptima edición se basa en doce principios y ocho dominios de desempeño.

## Ciclo de vida del proyecto
El ciclo de vida es la serie de fases que atraviesa un proyecto desde su inicio hasta su cierre. Puede ser predictivo (en cascada, con el alcance definido al inicio), iterativo, incremental, ágil (entregas frecuentes en iteraciones cortas) o híbrido, que combina enfoques. En proyectos de software es común un enfoque híbrido: planificación predictiva de hitos y desarrollo iterativo.

## El director de proyectos
El director o gerente de proyectos es la persona asignada por la organización para liderar al equipo responsable de alcanzar los objetivos del proyecto. Sus competencias, según el triángulo de talentos del PMI, son la dirección técnica de proyectos, el liderazgo y la gestión estratégica y de negocios.

# Unidad 2: Inicio del proyecto e interesados

## Acta de constitución del proyecto
El acta de constitución o project charter es el documento que autoriza formalmente la existencia del proyecto y otorga al director la autoridad para usar los recursos de la organización. Contiene la justificación, los objetivos medibles, los requisitos de alto nivel, los hitos, el presupuesto resumido, los riesgos principales, los interesados clave y los requisitos de aprobación. La firma el patrocinador.

## Objetivos SMART
Los objetivos del proyecto deben ser SMART: específicos, medibles, alcanzables, relevantes y con un plazo definido. Por ejemplo, "pilotar la plataforma con al menos 15 estudiantes entre las semanas 11 y 12" es un objetivo SMART porque indica qué, cuánto y cuándo.

## Identificación y análisis de interesados
Un interesado o stakeholder es una persona, grupo u organización que puede afectar o ser afectado por el proyecto. El registro de interesados documenta su rol, expectativas, influencia y postura. La matriz de poder e interés (Mendelow) los clasifica en cuatro cuadrantes: gestionar de cerca (alto poder y alto interés), mantener satisfecho (alto poder y bajo interés), mantener informado (bajo poder y alto interés) y monitorear (bajo poder y bajo interés).

# Unidad 3: Gestión del alcance

## Plan de gestión del alcance y enunciado del alcance
El plan de gestión del alcance describe cómo se definirá, validará y controlará el alcance. El enunciado del alcance detalla la descripción del producto, los entregables, los criterios de aceptación y las exclusiones. Las exclusiones indican de forma explícita lo que no forma parte del proyecto y ayudan a evitar el crecimiento no controlado del alcance (scope creep).

## Estructura de desglose del trabajo (EDT)
La EDT o WBS es una descomposición jerárquica del trabajo total del proyecto en entregables y paquetes de trabajo. El paquete de trabajo es el nivel más bajo de la EDT, en el que se puede estimar costo y duración. La regla del 100 % indica que la EDT debe incluir todo el trabajo del proyecto y nada más. La cuenta de control es un punto de gestión donde se integran alcance, costo y cronograma.

## Diccionario de la EDT y línea base del alcance
El diccionario de la EDT describe cada paquete de trabajo: responsable, duración, hitos, criterios de calidad y criterios de aceptación. La línea base del alcance está formada por el enunciado del alcance, la EDT y su diccionario, y solo puede modificarse mediante el control integrado de cambios.

## Control de cambios del alcance
Toda solicitud de cambio se registra, se analiza su impacto en alcance, tiempo, costo, calidad y riesgos, y se aprueba o rechaza según los niveles de autoridad definidos. Validar el alcance es obtener la aceptación formal de los entregables por parte del cliente o patrocinador.

# Unidad 4: Gestión del cronograma

## Definición y secuencia de actividades
Las actividades se obtienen al descomponer los paquetes de trabajo. Se secuencian con el método de diagramación por precedencia, que usa cuatro tipos de relación: fin a inicio (FI), inicio a inicio (II o CC), fin a fin (FF) e inicio a fin (IF). Los adelantos y retrasos (desfases) ajustan esas relaciones.

## Estimación de la duración y técnica PERT
La duración puede estimarse por juicio de expertos, por analogía, de forma paramétrica, ascendente o por tres valores. La técnica PERT usa una estimación optimista (O), una más probable (M) y una pesimista (P), y calcula la duración esperada con la fórmula te = (O + 4M + P) / 6. La desviación estándar se aproxima con (P - O) / 6.

## Ruta crítica y holgura
La ruta crítica es la secuencia de actividades más larga del proyecto y determina su duración mínima. Se calcula con el paso hacia adelante (inicio y fin tempranos) y el paso hacia atrás (inicio y fin tardíos). La holgura total es la diferencia entre el inicio tardío y el inicio temprano; las actividades críticas tienen holgura cero. La holgura libre es lo que una actividad puede retrasarse sin retrasar a su sucesora.

## Compresión del cronograma
Para acortar el cronograma sin cambiar el alcance se usan dos técnicas: la intensificación o crashing, que agrega recursos a actividades críticas con un costo adicional, y la ejecución rápida o fast tracking, que realiza en paralelo actividades que normalmente serían secuenciales, con mayor riesgo de retrabajo.

## Diagrama de Gantt y MS Project
El diagrama de Gantt muestra las actividades como barras sobre una línea de tiempo. En MS Project se crean las tareas, se asignan duraciones, se vinculan con dependencias y se activa la vista de tareas críticas para mostrar la ruta crítica en rojo. La línea base guarda el plan aprobado para compararlo con el avance real.

# Unidad 5: Gestión de los costos y valor ganado

## Estimación de costos y presupuesto
Los costos se estiman por actividad y se suman por paquete de trabajo y cuenta de control para obtener la línea base de costos. El presupuesto total incluye la línea base de costos más la reserva de gestión. La reserva de contingencia cubre los riesgos identificados y forma parte de la línea base.

## Gestión del valor ganado
La gestión del valor ganado (EVM) integra alcance, cronograma y costo. El valor planificado (PV) es el presupuesto del trabajo programado a una fecha. El valor ganado (EV) es el presupuesto del trabajo realmente completado. El costo real (AC) es lo que realmente se gastó. La variación del cronograma es SV = EV - PV y la variación del costo es CV = EV - AC.

## Índices de desempeño y pronósticos
El índice de desempeño del cronograma es SPI = EV / PV y el índice de desempeño del costo es CPI = EV / AC. Un índice menor que 1 indica atraso o sobrecosto. El presupuesto a la conclusión (BAC) es el total planificado. La estimación a la conclusión se calcula como EAC = BAC / CPI cuando se espera que el desempeño continúe igual; la estimación hasta la conclusión es ETC = EAC - AC y la variación a la conclusión es VAC = BAC - EAC. El índice TCPI = (BAC - EV) / (BAC - AC) indica el desempeño necesario para terminar dentro del presupuesto. La curva S muestra PV, EV y AC acumulados en el tiempo.

# Unidad 6: Calidad, recursos, comunicaciones y riesgos

## Gestión de la calidad
La gestión de la calidad incluye planificar la calidad (definir normas y métricas), gestionar la calidad o aseguramiento (auditar procesos para prevenir defectos) y controlar la calidad (inspeccionar entregables para detectar defectos). El costo de la calidad agrupa los costos de conformidad (prevención y evaluación) y de no conformidad (fallas internas y externas). Las herramientas incluyen listas de verificación, diagramas de causa y efecto, diagramas de Pareto y el ciclo PDCA de mejora continua.

## Gestión de los recursos
La gestión de los recursos identifica, adquiere y dirige los recursos humanos y físicos del proyecto. La matriz RAM y la matriz RACI (responsable, aprueba, consultado, informado) asignan responsabilidades. Cada actividad debe tener un único responsable de aprobar.

## Gestión de las comunicaciones
El plan de comunicaciones define qué información necesita cada interesado, quién la elabora, con qué método, formato y frecuencia. El número de canales de comunicación se calcula con n(n - 1) / 2, donde n es el número de personas. Los informes de estado describen dónde se encuentra el proyecto y los informes de desempeño comparan el avance con la línea base.

## Gestión de los riesgos
Un riesgo es un evento incierto que, si ocurre, tiene un efecto positivo o negativo en los objetivos. Se identifican en el registro de riesgos, se priorizan con la matriz de probabilidad e impacto y se planifican respuestas: evitar, transferir, mitigar o aceptar para amenazas, y explotar, compartir, mejorar o aceptar para oportunidades.

# Evaluación del curso

## Sistema de evaluación
La nota final se compone de prácticas calificadas, actividades semanales, el trabajo final en avances (Avance 01 en la semana 7 y Avance 02 en la semana 10), el examen parcial en la semana 8 y el examen final en la semana 16. El trabajo final se expone en grupo y debe aplicar las plantillas trabajadas en clase.
