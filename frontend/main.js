// API base
function getApiBase() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("api_base")) return params.get("api_base").replace(/\/+$/, "");
  if (window.__API_BASE__) return window.__API_BASE__.replace(/\/+$/, "");
  return "http://127.0.0.1:8000";
}
const API_BASE = getApiBase();

// Mostrar sección
function mostrarSeccion(id) {
  document.querySelectorAll(".contenido-seccion").forEach(s => (s.style.display = "none"));
  const el = document.getElementById(id);
  if (el) el.style.display = "block";
  // marcar activo
  document.querySelectorAll("aside li").forEach(li => {
    li.classList.toggle("active", li.dataset.target === id);
  });
}

// Mensajes inline
function mostrarMensaje(container, texto, tipo="success") {
  let cont = container.querySelector(".status-container");
  if (!cont) {
    cont = document.createElement("div");
    cont.className = "status-container";
    container.appendChild(cont);
  }
  let msg = cont.querySelector(".mensaje");
  if (!msg) {
    msg = document.createElement("div");
    msg.className = "mensaje";
    cont.appendChild(msg);
  }
  msg.textContent = texto;
  msg.className = `mensaje ${tipo}`;
}

// Cargas y listeners
document.addEventListener("DOMContentLoaded", () => {
  // Sidebar navegación
  document.querySelectorAll("aside li").forEach(li => {
    const target = li.dataset.target;
    if (target) {
      li.addEventListener("click", () => mostrarSeccion(target));
    }
  });

  // Inicial
  mostrarSeccion("factura-venta");

  // Formulario venta
  document.getElementById("form-venta")?.addEventListener("submit", async e => {
    e.preventDefault();
    const form = e.target;
    const cliente = form.cliente.value.trim();
    const descripcion = form.descripcion.value.trim();
    const monto = parseFloat(form.monto.value);
    const fecha = form.fecha.value;
    const payload = {
      tipo: "ingreso",
      descripcion: `${cliente} - ${descripcion}`,
      monto,
      fecha
    };
    try {
      form.querySelector("button").disabled = true;
      mostrarMensaje(form, "Enviando...", "loading");
      const res = await fetch(`${API_BASE}/api/raw/`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        mostrarMensaje(form, "✅ Factura de venta guardada en raw", "success");
        form.reset();
      } else {
        const txt = await res.text();
        mostrarMensaje(form, `❌ ${txt || res.statusText}`, "error");
      }
    } catch {
      mostrarMensaje(form, "❌ Error de conexión", "error");
    } finally {
      form.querySelector("button").disabled = false;
    }
  });

  // Formulario compra
  document.getElementById("form-compra")?.addEventListener("submit", async e => {
    e.preventDefault();
    const form = e.target;
    const proveedor = form.proveedor.value.trim();
    const descripcion = form.descripcion.value.trim();
    const monto = parseFloat(form.monto.value);
    const fecha = form.fecha.value;
    const payload = {
      tipo: "gasto",
      descripcion: `${proveedor} - ${descripcion}`,
      monto,
      fecha
    };
    try {
      form.querySelector("button").disabled = true;
      mostrarMensaje(form, "Enviando...", "loading");
      const res = await fetch(`${API_BASE}/api/raw/`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        mostrarMensaje(form, "✅ Factura de compra guardada en raw", "success");
        form.reset();
      } else {
        const txt = await res.text();
        mostrarMensaje(form, `❌ ${txt || res.statusText}`, "error");
      }
    } catch {
      mostrarMensaje(form, "❌ Error de conexión", "error");
    } finally {
      form.querySelector("button").disabled = false;
    }
  });

  // Recurrentes
  document.getElementById("form-recurrente")?.addEventListener("submit", async e => {
    e.preventDefault();
    const form = e.target;
    const cliente = form.cliente.value.trim();
    const descripcion = form.descripcion.value.trim();
    const monto = parseFloat(form.monto.value);
    const frecuencia = form.frecuencia.value.trim();
    try {
      form.querySelector("button").disabled = true;
      mostrarMensaje(form, "Creando plantilla...", "loading");
      const res = await fetch(`${API_BASE}/api/facturas/recurrentes/template/`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({cliente, descripcion, monto, frecuencia})
      });
      if (res.ok) {
        mostrarMensaje(form, "✅ Plantilla creada", "success");
        form.reset();
        cargarTemplatesRecurrentes();
      } else {
        const txt = await res.text();
        mostrarMensaje(form, `❌ ${txt || res.statusText}`, "error");
      }
    } catch {
      mostrarMensaje(form, "❌ Error de conexión", "error");
    } finally {
      form.querySelector("button").disabled = false;
    }
  });

  // Pago recibido
  document.getElementById("form-pago-recibido")?.addEventListener("submit", async e => {
    e.preventDefault();
    const form = e.target;
    const factura_id = parseInt(form.factura_id.value);
    const monto = parseFloat(form.monto.value);
    const fecha = form.fecha.value;
    try {
      form.querySelector("button").disabled = true;
      mostrarMensaje(form, "Registrando pago...", "loading");
      const res = await fetch(`${API_BASE}/api/pagos/recibidos/`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({factura_venta_id: factura_id, monto, fecha})
      });
      if (res.ok) {
        mostrarMensaje(form, "✅ Pago registrado", "success");
        form.reset();
      } else {
        const txt = await res.text();
        mostrarMensaje(form, `❌ ${txt || res.statusText}`, "error");
      }
    } catch {
      mostrarMensaje(form, "❌ Error de conexión", "error");
    } finally {
      form.querySelector("button").disabled = false;
    }
  });

  // Orden de compra
  document.getElementById("form-orden-compra")?.addEventListener("submit", async e => {
    e.preventDefault();
    const form = e.target;
    const proveedor = form.proveedor.value.trim();
    const descripcion = form.descripcion.value.trim();
    const monto = parseFloat(form.monto.value);
    const fecha = form.fecha.value;
    try {
      form.querySelector("button").disabled = true;
      mostrarMensaje(form, "Registrando orden...", "loading");
      const res = await fetch(`${API_BASE}/api/raw/`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({tipo: "orden_compra", descripcion: `${proveedor} - ${descripcion}`, monto, fecha})
      });
      if (res.ok) {
        mostrarMensaje(form, "✅ Orden guardada en raw", "success");
        form.reset();
      } else {
        const txt = await res.text();
        mostrarMensaje(form, `❌ ${txt || res.statusText}`, "error");
      }
    } catch {
      mostrarMensaje(form, "❌ Error de conexión", "error");
    } finally {
      form.querySelector("button").disabled = false;
    }
  });

  // Pago a proveedor
  document.getElementById("form-pago-proveedor")?.addEventListener("submit", async e => {
    e.preventDefault();
    const form = e.target;
    const factura_compra_id = form.factura_compra_id.value ? parseInt(form.factura_compra_id.value) : null;
    const orden_compra_id = form.orden_compra_id.value ? parseInt(form.orden_compra_id.value) : null;
    const monto = parseFloat(form.monto.value);
    const fecha = form.fecha.value;
    try {
      form.querySelector("button").disabled = true;
      mostrarMensaje(form, "Registrando pago...", "loading");
      const res = await fetch(`${API_BASE}/api/pagos/proveedor/`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({factura_compra_id, orden_compra_id, monto, fecha})
      });
      if (res.ok) {
        mostrarMensaje(form, "✅ Pago registrado", "success");
        form.reset();
      } else {
        const txt = await res.text();
        mostrarMensaje(form, `❌ ${txt || res.statusText}`, "error");
      }
    } catch {
      mostrarMensaje(form, "❌ Error de conexión", "error");
    } finally {
      form.querySelector("button").disabled = false;
    }
  });

  // Pipeline
  document.getElementById("btn-run-pipeline")?.addEventListener("click", async () => {
    const section = document.getElementById("admin-etl");
    mostrarMensaje(section, "Ejecutando pipeline...", "loading");
    try {
      const res = await fetch(`${API_BASE}/api/pipeline/run`, {method:"POST"});
      if (res.ok) {
        mostrarMensaje(section, "✅ Limpieza ejecutada", "success");
        cargarDatosLimpios();
      } else {
        const txt = await res.text();
        mostrarMensaje(section, `❌ ${txt || res.statusText}`, "error");
      }
    } catch {
      mostrarMensaje(section, "❌ Error de conexión", "error");
    }
  });

  // Cargas iniciales
  cargarDatosLimpios();
  cargarTemplatesRecurrentes();
});

// Cargar cleaned_data
async function cargarDatosLimpios() {
  try {
    const res = await fetch(`${API_BASE}/api/cleaned/`);
    const data = await res.json();
    const tbody = document.getElementById("tabla-etl");
    tbody.innerHTML = "";
    data.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.id}</td>
        <td>${r.tipo}</td>
        <td>${r.descripcion}</td>
        <td>${r.monto}</td>
        <td>${r.fecha}</td>
        <td>${r.validado_por}</td>
        <td>${r.tabla_destino || ""}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("cleaned load:", e);
  }
}

// Cargar plantillas recurrentes
async function cargarTemplatesRecurrentes() {
  try {
    const res = await fetch(`${API_BASE}/api/facturas/recurrentes/template/`);
    const data = await res.json();
    const tbody = document.getElementById("tabla-recurrentes");
    tbody.innerHTML = "";
    data.forEach(t => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${t.id}</td>
        <td>${t.cliente}</td>
        <td>${t.descripcion}</td>
        <td>${t.monto}</td>
        <td>${t.frecuencia}</td>
        <td>${t.siguiente_generacion}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("recurrentes load:", e);
  }
}
