// MentorIA – interfaz web/móvil. Todo el contenido dinámico se inserta con
// textContent (nunca innerHTML) para evitar inyección de código (OWASP A03).
"use strict";

const estado = { rol: "estudiante", curso: "GPC", estudiante: "E001", cursos: [], codigos: [], historial: {},
  filtroAlertas: "alerta", busqueda: "" };

const SUGERENCIAS = {
  GPC: ["¿Cómo se calcula el CPI?", "¿Qué es la ruta crítica?", "Fórmula PERT", "¿Qué contiene el acta de constitución?"],
  IHC: ["¿Cuántos usuarios necesito para una prueba de usabilidad?", "¿Qué es el cuestionario SUS?", "Heurísticas de Nielsen", "¿Qué dice la ley de Fitts?"],
};

function h(tag, attrs = {}, ...hijos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of hijos.flat()) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

async function api(ruta, opciones = {}) {
  const r = await fetch("/api/" + ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
    body: opciones.body ? JSON.stringify(opciones.body) : undefined,
  });
  const datos = await r.json();
  if (!r.ok) throw new Error(datos.error || "Error del servidor");
  return datos;
}

const vista = () => document.getElementById("vista");
const nombreCurso = (c) => (estado.cursos.find((x) => x.codigo === c) || {}).nombre || c;

// ---------------------------------------------------------------- navegación
const RUTAS = {
  estudiante: [["chat", "Chatbot"], ["plan", "Mi plan de estudio"], ["progreso", "Mi progreso"]],
  docente: [["tablero", "Tablero docente"], ["alertas", "Alertas de riesgo"]],
};

function pintarPestanas(actual) {
  const nav = document.getElementById("pestanas");
  nav.replaceChildren(...RUTAS[estado.rol].map(([id, texto]) =>
    h("a", { href: `#${id}`, class: id === actual ? "activa" : "" }, texto)));
}

async function navegar() {
  const id = location.hash.slice(1) || (estado.rol === "docente" ? "tablero" : "chat");
  const valida = RUTAS[estado.rol].some(([r]) => r === id);
  const ruta = valida ? id : RUTAS[estado.rol][0][0];
  pintarPestanas(ruta);
  document.getElementById("campo-est").style.display = estado.rol === "estudiante" ? "" : "none";
  const v = vista();
  v.replaceChildren(h("p", { class: "vacio" }, "Cargando…"));
  try {
    await ({ chat: vistaChat, plan: vistaPlan, progreso: vistaProgreso, tablero: vistaTablero, alertas: vistaAlertas })[ruta]();
  } catch (e) {
    v.replaceChildren(h("p", { class: "error" }, e.message));
  }
}

// ---------------------------------------------------------------- chatbot
function burbuja(m) {
  if (m.yo) return h("div", { class: "msg yo" }, m.texto);
  if (m.modo === "bienvenida") return h("div", { class: "msg bot" }, m.texto);
  const meta = m.en_silabo
    ? `Confianza ${(m.confianza * 100).toFixed(0)} % · ${m.ms} ms · modo ${m.modo}`
    : `Fuera del sílabo · ${m.ms} ms`;
  return h("div", { class: "msg bot" + (m.en_silabo ? "" : " fuera") }, m.texto, h("span", { class: "meta" }, meta));
}

async function vistaChat() {
  const plantilla = document.getElementById("t-chat").content.cloneNode(true);
  vista().replaceChildren(
    h("section", { class: "tarjeta" },
      h("h2", {}, `Chatbot académico – ${nombreCurso(estado.curso)}`),
      h("p", { class: "sub" }, "Responde con el contenido del sílabo oficial del curso y cita la unidad de donde sale la respuesta.")),
    plantilla);
  const clave = estado.estudiante + estado.curso;
  const historial = (estado.historial[clave] ||= [
    { en_silabo: true, confianza: 1, ms: 0, modo: "bienvenida",
      texto: `Hola, ${estado.estudiante}. Soy MentorIA. Pregúntame cualquier tema de ${nombreCurso(estado.curso)}.` },
  ]);
  const caja = document.getElementById("mensajes");
  const pintar = () => { caja.replaceChildren(...historial.map(burbuja)); caja.scrollTop = caja.scrollHeight; };
  pintar();
  const enviar = async (texto) => {
    if (!texto.trim()) return;
    historial.push({ yo: true, texto });
    pintar();
    const r = await api("chat", { method: "POST", body: { estudiante: estado.estudiante, curso: estado.curso, pregunta: texto } });
    historial.push({ texto: r.respuesta, en_silabo: r.en_silabo, confianza: r.confianza, ms: r.ms, modo: r.modo });
    pintar();
  };
  document.getElementById("form-chat").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const inp = document.getElementById("pregunta");
    const t = inp.value; inp.value = "";
    enviar(t).catch((e) => alert(e.message));
  });
  document.getElementById("sugerencias").replaceChildren(
    ...SUGERENCIAS[estado.curso].map((s) => h("button", { type: "button", onclick: () => enviar(s) }, s)));
  // Modo demostración: ?preguntar=pregunta1|pregunta2 envía las preguntas al abrir la vista.
  const demo = new URLSearchParams(location.search).get("preguntar");
  if (demo && historial.length === 1) for (const q of demo.split("|")) await enviar(q);
}

// ---------------------------------------------------------------- plan de estudio
async function vistaPlan() {
  const plan = await api(`estudiantes/${estado.estudiante}/plan?curso=${estado.curso}`);
  const curso = estado.cursos.find((c) => c.codigo === estado.curso);
  const unidades = curso.unidades.filter((u) => !u.startsWith("Evaluación"));
  const form = h("form", { class: "tarjeta" },
    h("h2", {}, plan ? "Generar un nuevo plan" : "Crea tu plan de estudio"),
    h("p", { class: "sub" }, "Indica tu tiempo disponible y marca las unidades que te cuestan más: recibirán el doble de práctica."),
    h("div", { class: "formulario" },
      h("label", {}, "Horas por semana", h("input", { name: "horas", type: "number", min: 1, max: 20, value: 4, required: true })),
      h("label", {}, "Semanas hasta el examen", h("input", { name: "semanas", type: "number", min: 1, max: 16, value: 3, required: true })),
      h("button", { class: "primario", type: "submit" }, "Generar plan")),
    h("div", { class: "checks" }, unidades.map((u) => h("label", {}, h("input", { type: "checkbox", name: "debil", value: u }), " ", u))));
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(form);
    await api("planes", { method: "POST", body: {
      estudiante: estado.estudiante, curso: estado.curso,
      horas_semana: Number(fd.get("horas")), semanas: Number(fd.get("semanas")),
      unidades_debiles: fd.getAll("debil") } });
    vistaPlan();
  });
  const bloques = [form];
  if (plan) {
    const porSemana = {};
    plan.tareas.forEach((t) => (porSemana[t.semana] ||= []).push(t));
    bloques.unshift(h("section", { class: "tarjeta" },
      h("h2", {}, `Mi plan – ${nombreCurso(estado.curso)}`),
      h("p", { class: "sub" }, `${plan.horas_semana} h por semana durante ${plan.semanas} semanas · avance ${plan.avance} %`),
      h("div", { class: "progreso" }, h("div", { style: `width:${plan.avance}%` })),
      Object.entries(porSemana).map(([s, tareas]) => h("div", { class: "semana" },
        h("h4", {}, `Semana ${s}`),
        tareas.map((t) => h("label", { class: "tarea" + (t.completada ? " hecha" : "") },
          h("input", { type: "checkbox", checked: !!t.completada, disabled: !!t.completada,
            onchange: async () => { await api(`tareas/${t.id}/completar`, { method: "POST", body: { estudiante: estado.estudiante } }); vistaPlan(); } }),
          h("div", {}, h("div", { class: "t-tema" }, t.tema),
            h("div", { class: "t-det" }, `${t.unidad} · ${t.actividad} · ${t.minutos} min`))))))));
  }
  vista().replaceChildren(...bloques);
}

// ---------------------------------------------------------------- progreso y riesgo
async function vistaProgreso() {
  const [g, r] = await Promise.all([api(`estudiantes/${estado.estudiante}/logros`), api(`estudiantes/${estado.estudiante}/riesgo`)]);
  const etiquetas = { nota_pc1: "Práctica 1", nota_pc2: "Práctica 2", asistencia: "Asistencia (%)", tareas: "Tareas entregadas (%)" };
  vista().replaceChildren(
    h("div", { class: "rejilla" },
      h("div", { class: "kpi" }, h("div", { class: "valor" }, g.puntos), h("div", { class: "etiqueta" }, "Puntos")),
      h("div", { class: "kpi" }, h("div", { class: "valor" }, `${g.racha_dias} 🔥`), h("div", { class: "etiqueta" }, "Días de racha")),
      h("div", { class: "kpi" }, h("div", { class: "valor" }, `${g.tareas_completadas}/${g.tareas_totales}`), h("div", { class: "etiqueta" }, "Tareas del plan")),
      h("div", { class: "kpi" }, h("div", { class: "valor" }, g.preguntas_chatbot), h("div", { class: "etiqueta" }, "Preguntas válidas al chatbot"))),
    h("section", { class: "tarjeta", style: "margin-top:16px" },
      h("h2", {}, "Insignias"),
      h("div", { class: "insignias" },
        g.insignias.map((i) => h("div", { class: "insignia ok" }, h("b", {}, "🏅 Obtenida"), i.descripcion)),
        g.insignias_pendientes.map((i) => h("div", { class: "insignia no" }, h("b", {}, "🔒 Pendiente"), i.descripcion)))),
    h("section", { class: "tarjeta" },
      h("h2", {}, "Mi alerta académica ", h("span", { class: `semaforo ${r.nivel}` }, `Riesgo ${r.nivel}`)),
      h("p", { class: "sub" }, `Probabilidad estimada de desaprobar: ${(r.probabilidad * 100).toFixed(0)} % (curso ${r.curso}).`),
      h("table", {}, h("tbody", {}, Object.entries(r.variables).map(([k, v]) => h("tr", {}, h("td", {}, etiquetas[k]), h("td", { class: "num" }, v))))),
      h("h3", { style: "margin-top:14px" }, "Recomendaciones"),
      h("ul", {}, r.recomendaciones.map((x) => h("li", {}, x)))));
}

// ---------------------------------------------------------------- tablero docente
async function vistaTablero() {
  const t = await api(`tablero?curso=${estado.curso}`);
  const max = Math.max(1, ...t.temas.map((x) => x.consultas));
  vista().replaceChildren(
    h("section", { class: "tarjeta" },
      h("h2", {}, `Tablero docente – ${nombreCurso(estado.curso)}`),
      h("p", { class: "sub" }, "Datos agregados de las consultas al chatbot. No se muestra información personal.")),
    h("div", { class: "rejilla" },
      h("div", { class: "kpi" }, h("div", { class: "valor" }, t.total_consultas), h("div", { class: "etiqueta" }, "Consultas al chatbot")),
      h("div", { class: "kpi" }, h("div", { class: "valor" }, `${t.estudiantes_activos} / ${t.estudiantes_curso}`),
        h("div", { class: "etiqueta" }, `Activos esta semana (${t.porcentaje_activos} %) · chatbot o plan`)),
      h("div", { class: "kpi" }, h("div", { class: "valor" }, t.consultas_fuera_de_silabo), h("div", { class: "etiqueta" }, "Preguntas fuera del sílabo (temas que el curso no cubre)")),
      h("div", { class: "kpi" }, h("div", { class: "valor" }, `${t.alertas.alto} / ${t.alertas.medio}`), h("div", { class: "etiqueta" }, "Alertas de riesgo alto / medio"))),
    h("section", { class: "tarjeta", style: "margin-top:16px" },
      h("h3", {}, "Temas con más dudas"),
      t.total_consultas ? h("div", { class: "barras" }, t.temas.filter((x) => x.consultas).slice(0, 10).map((x) =>
        h("div", { class: "barra-fila" }, h("span", { title: x.unidad }, x.tema),
          h("div", { class: "pista" }, h("div", { style: `width:${(100 * x.consultas) / max}%` })),
          h("span", { class: "num" }, x.consultas))))
        : h("p", { class: "vacio" }, "Aún no hay consultas registradas en este curso.")),
    h("section", { class: "tarjeta" },
      h("h3", {}, "Consultas recientes"),
      h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Pregunta"), h("th", {}, "Tema"), h("th", {}, "Fecha"))),
        h("tbody", {}, t.consultas_recientes.map((c) => h("tr", {}, h("td", {}, c.pregunta), h("td", {}, c.tema), h("td", {}, c.fecha)))))));
}

function tarjetaCargaNotas(origen) {
  const mensaje = h("p", { class: "sub", role: "status" });
  const archivo = h("input", { type: "file", accept: ".csv,text/csv", "aria-label": "Archivo CSV de notas" });
  const cargar = async () => {
    if (!archivo.files.length) { mensaje.className = "error"; mensaje.textContent = "Elija un archivo CSV."; return; }
    mensaje.className = "sub"; mensaje.textContent = "Validando el archivo…";
    try {
      const r = await api("notas", { method: "POST", body: { curso: estado.curso, csv: await archivo.files[0].text() } });
      sessionStorage.setItem("aviso-notas", `Se cargaron ${r.registros} estudiantes; ${r.con_alerta} quedan con alerta.`);
      await cargarEstudiantes();
      vistaAlertas();
    } catch (e) { mensaje.className = "error"; mensaje.textContent = e.message; }
  };
  const plantilla = async () => {
    const { csv } = await api("notas/plantilla");
    const a = h("a", { href: URL.createObjectURL(new Blob(["﻿" + csv], { type: "text/csv" })), download: "plantilla_notas.csv" });
    document.body.append(a); a.click(); a.remove();
  };
  const restaurar = async () => {
    await api("notas/restaurar", { method: "POST", body: { curso: estado.curso } });
    sessionStorage.setItem("aviso-notas", "Se restauraron los datos simulados del curso.");
    await cargarEstudiantes();
    vistaAlertas();
  };
  const aviso = sessionStorage.getItem("aviso-notas");
  if (aviso) { mensaje.textContent = aviso; sessionStorage.removeItem("aviso-notas"); }
  return h("section", { class: "tarjeta" },
    h("h2", {}, "Notas del curso ", h("span", { class: `semaforo ${origen === "simulado" ? "medio" : "bajo"}` },
      origen === "simulado" ? "Datos simulados" : "Cargadas por el docente")),
    h("p", { class: "sub" }, "Cargue el extracto de su registro en CSV (exportado desde Excel) con las columnas codigo, nota_pc1, " +
      "nota_pc2, asistencia y tareas. Use solo códigos anonimizados E###: el sistema rechaza nombres, DNI o correos (Ley N.° 29733)."),
    h("div", { class: "carga" }, archivo,
      h("button", { class: "primario", type: "button", onclick: cargar }, "Cargar notas"),
      h("button", { class: "secundario", type: "button", onclick: plantilla }, "Descargar plantilla"),
      origen === "simulado" ? null : h("button", { class: "secundario", type: "button", onclick: restaurar }, "Restaurar datos simulados")),
    mensaje);
}

async function vistaAlertas() {
  const [lista, modelo, origen] = await Promise.all([
    api(`alertas?curso=${estado.curso}`), api("modelo"), api(`notas/origen?curso=${estado.curso}`)]);
  const enAlerta = lista.filter((a) => a.alerta);
  const cuerpo = h("tbody");
  const resumen = h("p", { class: "sub" });
  const pintar = () => {
    const q = estado.busqueda.trim().toUpperCase();
    const base = estado.filtroAlertas === "alerta" ? enAlerta : lista;
    const filas = base.filter((a) => !q || a.codigo.includes(q));
    cuerpo.replaceChildren(...(filas.length ? filas.map((a) => h("tr", {},
      h("td", {}, h("button", { class: "enlace", type: "button", title: "Ver como estudiante", onclick: () => verComoEstudiante(a.codigo) }, a.codigo)),
      h("td", {}, h("span", { class: `semaforo ${a.nivel}` }, a.nivel)),
      h("td", { class: "num" }, `${(a.probabilidad * 100).toFixed(0)} %`),
      h("td", { class: "num" }, a.variables.nota_pc1), h("td", { class: "num" }, a.variables.nota_pc2),
      h("td", { class: "num" }, a.variables.asistencia), h("td", { class: "num" }, a.variables.tareas),
      h("td", {}, a.recomendaciones[0])))
      : [h("tr", {}, h("td", { colspan: 8, class: "vacio" }, "Ningún estudiante coincide con la búsqueda."))]));
    resumen.textContent = `${enAlerta.length} de ${lista.length} estudiantes con alerta · mostrando ${filas.length}. ` +
      `Sensibilidad del modelo en datos de prueba: ${(modelo.metricas.sensibilidad * 100).toFixed(1)} % (meta ≥ 70 %).`;
  };
  const filtro = (valor, texto) => h("button", {
    type: "button", class: estado.filtroAlertas === valor ? "activo" : "", "aria-pressed": String(estado.filtroAlertas === valor),
    onclick: (ev) => {
      estado.filtroAlertas = valor;
      ev.target.parentElement.querySelectorAll("button").forEach((b) => {
        b.classList.toggle("activo", b === ev.target); b.setAttribute("aria-pressed", String(b === ev.target)); });
      pintar();
    } }, texto);
  const buscador = h("input", { type: "search", placeholder: "Buscar código…", value: estado.busqueda, "aria-label": "Buscar código",
    oninput: (ev) => { estado.busqueda = ev.target.value; pintar(); } });
  vista().replaceChildren(
    tarjetaCargaNotas(origen.origen),
    h("section", { class: "tarjeta" },
      h("h2", {}, `Alertas tempranas – ${nombreCurso(estado.curso)}`),
      resumen,
      h("div", { class: "filtros" },
        h("div", { class: "segmentado", role: "group", "aria-label": "Filtro" }, filtro("alerta", "Solo con alerta"), filtro("todos", "Todos")),
        buscador),
      h("table", {},
        h("thead", {}, h("tr", {}, ["Código", "Riesgo", "Prob.", "PC1", "PC2", "Asist. %", "Tareas %", "Recomendación principal"].map((x) => h("th", {}, x)))),
        cuerpo),
      h("p", { class: "sub", style: "margin-top:10px" }, "Haga clic en un código para ver MentorIA como ese estudiante.")));
  pintar();
}

function marcarRol() {
  document.querySelectorAll(".rol button").forEach((x) => x.classList.toggle("activo", x.dataset.rol === estado.rol));
}

function verComoEstudiante(codigo) {
  estado.rol = "estudiante";
  estado.estudiante = codigo;
  document.getElementById("estudiante").value = codigo;
  marcarRol();
  if (location.hash === "#progreso") navegar(); else location.hash = "progreso";
}

// ---------------------------------------------------------------- arranque
async function cargarEstudiantes() {
  estado.codigos = await api(`estudiantes?curso=${estado.curso}`);
  if (!estado.codigos.includes(estado.estudiante)) estado.estudiante = estado.codigos[0];
  document.getElementById("codigos").replaceChildren(...estado.codigos.map((c) => h("option", { value: c })));
  const campo = document.getElementById("estudiante");
  campo.value = estado.estudiante;
  campo.placeholder = `${estado.codigos.length} códigos`;
}

function elegirEstudiante(campo) {
  const codigo = campo.value.trim().toUpperCase();
  if (estado.codigos.includes(codigo)) {
    campo.setCustomValidity("");
    campo.value = codigo;
    if (codigo !== estado.estudiante) { estado.estudiante = codigo; navegar(); }
  } else {
    campo.setCustomValidity(`El código ${codigo || "(vacío)"} no pertenece a este curso.`);
    campo.reportValidity();
    campo.value = estado.estudiante;
  }
}

async function iniciar() {
  const p = new URLSearchParams(location.search);
  if (p.get("rol")) estado.rol = p.get("rol");
  if (p.get("curso")) estado.curso = p.get("curso");
  if (p.get("e")) estado.estudiante = p.get("e");
  const [salud, cursos] = await Promise.all([api("health"), api("cursos")]);
  estado.cursos = cursos;
  document.getElementById("version").textContent = salud.version;
  document.getElementById("modo").textContent = `Generación: ${salud.modo_generacion}`;
  const selCurso = document.getElementById("curso");
  selCurso.replaceChildren(...cursos.map((c) => h("option", { value: c.codigo, selected: c.codigo === estado.curso }, c.nombre)));
  selCurso.addEventListener("change", async () => { estado.curso = selCurso.value; await cargarEstudiantes(); navegar(); });
  const campo = document.getElementById("estudiante");
  campo.addEventListener("change", () => elegirEstudiante(campo));
  campo.addEventListener("input", () => campo.setCustomValidity(""));
  document.querySelectorAll(".rol button").forEach((b) => b.addEventListener("click", () => {
    estado.rol = b.dataset.rol;
    document.querySelectorAll(".rol button").forEach((x) => x.classList.toggle("activo", x === b));
    location.hash = estado.rol === "docente" ? "tablero" : "chat";
    navegar();
  }));
  marcarRol();
  await cargarEstudiantes();
  window.addEventListener("hashchange", navegar);
  navegar();
}

iniciar().catch((e) => vista().replaceChildren(h("p", { class: "error" }, "No se pudo conectar con el servidor: " + e.message)));
