// API base
function getApiBase() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("api_base")) return params.get("api_base").replace(/\/+$/, "");
  if (window.__API_BASE__) return window.__API_BASE__.replace(/\/+$/, "");
  return "http://127.0.0.1:8000";
}
const API_BASE = getApiBase();

// Mostrar sección del sidebar
function mostrarSeccion(id) {
  document.querySelectorAll(".contenido-seccion").forEach(s => s.style.display = "none");
  const el = document.getElementById(id);
  if (el) el.style.display = "block";
  document.querySelectorAll("aside li").forEach(li => {
    li.classList.toggle("active", li.dataset.target === id);
  });
}

// Mostrar mensaje en un form
function mostrarMensaje(form, texto, tipo = "success") {
  let cont = form.querySelector(".status-container");
  if (!cont) {
    cont = document.createElement("div");
    cont.className = "status-container";
    form.append(cont);
  }
  cont.innerHTML = `<div class="mensaje ${tipo}">${texto}</div>`;
}

// Hacer fetch y poblar una tabla
async function cargarTabla(path, tbodyId, cols) {
  const res = await fetch(`${API_BASE}${path}`);
  const data = await res.json();
  const tbody = document.getElementById(tbodyId);
  tbody.innerHTML = "";
  data.forEach(item => {
    const tr = document.createElement("tr");
    cols.forEach(c => {
      const td = document.createElement("td");
      td.textContent = item[c] ?? "";
      tr.append(td);
    });
    tr.innerHTML += `
      <td>
        <button class="btn-edit" data-path="${path}" data-id="${item.id}">✏️</button>
        <button class="btn-delete" data-path="${path}" data-id="${item.id}">🗑️</button>
      </td>`;
    tbody.append(tr);
  });
}

// Carga inicial de todas las tablas
function cargarTodo() {
  cargarTabla("/api/facturas/venta/",             "tabla-venta",           ["id","cliente","descripcion","monto","fecha"]);
  cargarTabla("/api/facturas/compra/",            "tabla-compra",          ["id","proveedor","descripcion","monto","fecha"]);
  cargarTabla("/api/facturas/recurrentes/template/","tabla-recurrentes",    ["id","cliente","descripcion","monto","frecuencia","siguiente_generacion"]);
  cargarTabla("/api/pagos/recibidos/",            "tabla-pagos-recibidos", ["id","factura_venta_id","monto","fecha"]);
  cargarTabla("/api/ordenes/compra/",             "tabla-ordenes",         ["id","proveedor","descripcion","monto","fecha"]);
  cargarTabla("/api/pagos/proveedor/",            "tabla-pagos-proveedor", ["id","factura_compra_id","orden_compra_id","monto","fecha"]);
  cargarTabla("/api/clientes/",                   "tabla-clientes",        ["id","nombre","identificacion","correo","telefono","direccion"]);
  cargarTabla("/api/productos/",                  "tabla-productos",       ["id","nombre","sku","precio_unitario","descripcion"]);
  cargarTabla("/api/cleaned/",                    "tabla-etl",             ["id","tipo","descripcion","monto","fecha","validado_por","tabla_destino"]);
}

// Serializa un form a objeto
function formToObject(form) {
  const data = {};
  new FormData(form).forEach((v,k) => data[k] = v);
  return data;
}

// Envía un POST o PUT y refresca
async function submitForm(form, endpoint, method="POST", extra={}) {
  const payload = Object.assign(formToObject(form), extra);
  try {
    form.querySelector("button").disabled = true;
    mostrarMensaje(form, "Enviando...", "loading");
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    mostrarMensaje(form, "✅ Éxito", "success");
    form.reset();
    cargarTodo();
  } catch (e) {
    mostrarMensaje(form, `❌ ${e.message}`, "error");
  } finally {
    form.querySelector("button").disabled = false;
  }
}

// Manejar clics en editar / borrar (delegación)
async function handleTableClick(e) {
  if (e.target.matches(".btn-delete")) {
    const path = e.target.dataset.path;
    const id   = e.target.dataset.id;
    if (!confirm("¿Eliminar registro?")) return;
    await fetch(`${API_BASE}${path}${id}/`, { method: "DELETE" });
    cargarTodo();
  }
  // EDIT: fetch data, cargarlo en el form correspondiente
  if (e.target.matches(".btn-edit")) {
    const path = e.target.dataset.path;
    const id   = e.target.dataset.id;
    const res  = await fetch(`${API_BASE}${path}${id}/`);
    const data = await res.json();
    // Determinar qué formulario usar según path
    let formId;
    if (path.startsWith("/api/cliente"))       formId = "form-clientes";
    else if (path.startsWith("/api/producto")) formId = "form-productos";
    else if (path.includes("venta"))           formId = "form-venta";
    else if (path.includes("compra"))          formId = "form-compra";
    else if (path.includes("recurrentes"))     formId = "form-recurrente";
    else if (path.includes("recibidos"))       formId = "form-pago-recibido";
    else if (path.includes("ordenes"))         formId = "form-orden-compra";
    else if (path.includes("proveedor"))       formId = "form-pago-proveedor";
    // Cargar cada campo
    const form = document.getElementById(formId);
    if (!form) return;
    for (const [k,v] of Object.entries(data)) {
      if (form[k]) form[k].value = v;
    }
    // Cambiar submit para PUT
    form.onsubmit = e2 => {
      e2.preventDefault();
      submitForm(form, path + id + "/", "PUT");
      form.onsubmit = null; // restaurar
    };
    mostrarSeccion(formId.replace("form-",""));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Sidebar
  document.querySelectorAll("aside li").forEach(li => {
    li.addEventListener("click", () => mostrarSeccion(li.dataset.target));
  });
  mostrarSeccion("factura-venta");

  // Vincular formularios
  document.getElementById("form-venta")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/raw/", "POST", { tipo:"ingreso", descripcion:`${e.target.cliente.value} - ${e.target.descripcion.value}` });
  });
  document.getElementById("form-compra")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/raw/", "POST", { tipo:"gasto", descripcion:`${e.target.proveedor.value} - ${e.target.descripcion.value}` });
  });
  document.getElementById("form-recurrente")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/facturas/recurrentes/template/");
  });
  document.getElementById("form-pago-recibido")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/pagos/recibidos/");
  });
  document.getElementById("form-orden-compra")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/raw/", "POST", { tipo:"orden_compra", descripcion:`${e.target.proveedor.value} - ${e.target.descripcion.value}` });
  });
  document.getElementById("form-pago-proveedor")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/pagos/proveedor/");
  });
  document.getElementById("form-clientes")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/clientes/");
  });
  document.getElementById("form-productos")?.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/productos/");
  });

  // Pipeline
  document.getElementById("btn-run-pipeline")?.addEventListener("click", async () => {
    const sec = document.getElementById("admin-etl");
    mostrarMensaje(sec, "Ejecutando pipeline...", "loading");
    try {
      const res = await fetch(`${API_BASE}/api/pipeline/run`, { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      mostrarMensaje(sec, "✅ Pipeline OK", "success");
      cargarTabla("/api/cleaned/", "tabla-etl", ["id","tipo","descripcion","monto","fecha","validado_por","tabla_destino"]);
    } catch (e) {
      mostrarMensaje(sec, `❌ ${e.message}`, "error");
    }
  });

  // Delegación para editar/borrar
  document.querySelector("main").addEventListener("click", handleTableClick);

  // Carga inicial
  cargarTodo();
});





