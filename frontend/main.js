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
  const target = document.getElementById(id);
  if (!target) {
    // si el id no existe, no ocultamos nada; mostramos todo para no “perder” formularios
    document.querySelectorAll(".contenido-seccion").forEach(s => s.style.display = "block");
    return;
  }
  document.querySelectorAll(".contenido-seccion").forEach(s => s.style.display = "none");
  target.style.display = "block";
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
  if (!tbody) return;
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
  cargarTabla("/api/pagos/recibidos/",            "tabla-pagos-recibidos", ["id","factura_venta_id","monto","fecha"]);
  cargarTabla("/api/ordenes/compra/",             "tabla-ordenes",         ["id","proveedor","descripcion","monto","fecha"]);
  cargarTabla("/api/pagos/proveedor/",            "tabla-pagos-proveedor", ["id","factura_compra_id","orden_compra_id","monto","fecha"]);
  cargarTabla("/api/clientes/",                   "tabla-clientes",        ["id","nombre","identificacion","correo","telefono","direccion"]);
  cargarTabla("/api/proveedores/",                "tabla-proveedores",     ["id","nombre","identificacion","correo","telefono","direccion","contacto_nombre","contacto_telefono"]);
  cargarTabla("/api/productos/",                  "tabla-productos",       ["id","nombre","sku","precio_unitario","descripcion"]);
  cargarTabla("/api/cleaned/",                    "tabla-etl",             ["id","tipo","descripcion","monto","fecha","validado_por","tabla_destino"]);
  cargarTabla("/api/factura-items/",              "tabla-factura-items",   ["id","factura_tipo","factura_venta_id","factura_compra_id","producto_id","cantidad","precio","subtotal"]);
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

    const result = await res.json();

    // Verificar si es una respuesta del nuevo sistema ETL
    if (result.status === "pending_etl") {
      mostrarMensaje(form, `✅ ${result.message}. Raw ID: ${result.raw_id}. Ejecute el pipeline ETL para procesar.`, "success");
    } else {
      mostrarMensaje(form, "✅ Éxito", "success");
    }

    form.reset();
    cargarTodo();

    // Refrescar dashboards si aplica
    try {
      if (typeof window.refreshDashboards === 'function') {
        if (endpoint.includes('/api/facturas/venta') ||
            endpoint.includes('/api/facturas/compra') ||
            endpoint.includes('/api/factura-items')) {
          window.refreshDashboards();
        }
      }
    } catch (_) {}
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
    try {
      const res = await fetch(`${API_BASE}${path}${id}/`, { method: "DELETE" });
      if (!res.ok) {
        const error = await res.json();
        alert(`Error: ${error.detail || res.statusText}`);
      }
    } catch (err) {
      alert(`Error al eliminar: ${err.message}`);
    }
    cargarTodo();
  }
  // EDIT: fetch data, cargarlo en el form correspondiente
  if (e.target.matches(".btn-edit")) {
    const path = e.target.dataset.path;
    const id   = e.target.dataset.id;
    try {
      const res  = await fetch(`${API_BASE}${path}${id}/`);
      if (!res.ok) {
        const error = await res.json();
        alert(`Error: ${error.detail || res.statusText}`);
        return;
      }
      const data = await res.json();
      // Determinar qué formulario usar según path
      let formId, seccionId;
      if (path.startsWith("/api/cliente")) {
        formId = "form-clientes";
        seccionId = "clientes";
      } else if (path.startsWith("/api/producto")) {
        formId = "form-productos";
        seccionId = "productos";
      } else if (path.includes("/facturas/venta")) {
        formId = "form-venta";
        seccionId = "factura-venta";
      } else if (path.includes("/facturas/compra")) {
        formId = "form-compra";
        seccionId = "factura-compra";
      } else if (path.includes("recibidos")) {
        formId = "form-pago-recibido";
        seccionId = "pagos-recibidos";
      } else if (path.includes("ordenes")) {
        formId = "form-orden-compra";
        seccionId = "orden-compra";
      } else if (path.startsWith("/api/proveedores")) {
        formId = "form-proveedores";
        seccionId = "proveedores";
      } else if (path.includes("proveedor")) {
        formId = "form-pago-proveedor";
        seccionId = "pagos-proveedor";
      }
      // Cargar cada campo
      const form = document.getElementById(formId);
      if (!form) return;
      for (const [k,v] of Object.entries(data)) {
        if (form[k]) form[k].value = v;
      }

      // Guardar el handler original
      const originalHandler = form._originalHandler;

      // Cambiar submit para PUT
      form.onsubmit = async e2 => {
        e2.preventDefault();
        await submitForm(form, path + id + "/", "PUT");
        // Restaurar el handler original
        form.onsubmit = originalHandler;
        form.reset();
      };
      mostrarSeccion(seccionId);
    } catch (err) {
      alert(`Error al cargar datos: ${err.message}`);
    }
  }
}

// Cargar clientes en dropdown
async function cargarClientesDropdown() {
  try {
    const response = await fetch(`${API_BASE}/api/clientes/`);
    const clientes = await response.json();
    const select = document.getElementById("select-cliente-venta");

    // Limpiar opciones existentes (excepto las primeras dos)
    while (select.options.length > 2) {
      select.remove(2);
    }

    // Agregar clientes
    clientes.forEach(cliente => {
      const option = document.createElement("option");
      option.value = cliente.nombre;
      option.textContent = `${cliente.nombre} (${cliente.identificacion || 'Sin ID'})`
      ;
      select.appendChild(option);
    });
  } catch (error) {
    console.error("Error cargando clientes:", error);
  }
}

// Cargar proveedores en dropdowns
async function cargarProveedoresDropdowns() {
  try {
    const response = await fetch(`${API_BASE}/api/proveedores/`);
    const proveedores = await response.json();

    // Cargar en dropdown de compra y orden
    const selectCompra = document.getElementById("select-proveedor-compra");
    const selectOrden = document.getElementById("select-proveedor-orden");

    [selectCompra, selectOrden].forEach(select => {
      if (!select) return;
      // Limpiar opciones existentes (excepto las primeras dos)
      while (select.options.length > 2) {
        select.remove(2);
      }

      // Agregar proveedores
      proveedores.forEach(proveedor => {
        const option = document.createElement("option");
        option.value = proveedor.nombre;
        option.textContent = `${proveedor.nombre} (${proveedor.identificacion || 'Sin ID'})`;
        select.appendChild(option);
      });
    });
  } catch (error) {
    console.error("Error cargando proveedores:", error);
  }
}

// Cargar productos en dropdowns
async function cargarProductosDropdowns() {
  try {
    const response = await fetch(`${API_BASE}/api/productos/`);
    const productos = await response.json();

    // Cargar en dropdown de venta
    const selectVenta = document.getElementById("select-producto-venta");
    const selectCompra = document.getElementById("select-producto-compra");

    [selectVenta, selectCompra].filter(Boolean).forEach(select => {
      // Limpiar opciones existentes (excepto las primeras dos)
      while (select.options.length > 2) {
        select.remove(2);
      }

      // Agregar productos
      productos.forEach(producto => {
        const option = document.createElement("option");
        option.value = producto.id;
        option.textContent = `${producto.nombre} - ₡${producto.precio_unitario}`;
        option.dataset.precio = producto.precio_unitario;
        option.dataset.nombre = producto.nombre;
        select.appendChild(option);
      });
    });
  } catch (error) {
    console.error("Error cargando productos:", error);
  }
}

/* ============================================================
   UI mínima para manejar ítems
   ============================================================ */
function setupItemsUI({ form, selectProductoId, cantidadName, totalInputName, itemsStateKey }) {
  // Estado por formulario
  form[itemsStateKey] = [];

  // Contenedor visual
  let box = form.querySelector(".items-box");
  if (!box) {
    box = document.createElement("div");
    box.className = "items-box";
    box.style.margin = "10px 0";
    box.innerHTML = `
      <div style="display:flex; gap:8px; align-items:center; margin:6px 0;">
        <button type="button"
        class="btn-add-item !inline-flex !items-center !gap-2
               !px-4 !py-2 !rounded-md
               !bg-blue-600 !text-white hover:!bg-blue-700 active:!bg-blue-800">
  <span>➕</span> Agregar ítem
</button>
        <span style="opacity:.7">Use el selector de producto y la cantidad del formulario, luego pulse "Agregar ítem".</span>
      </div>
      <table style="width:100%; border-collapse: collapse; margin-top:6px;">
        <thead>
          <tr>
            <th style="text-align:left">Producto</th>
            <th style="text-align:right">Cantidad</th>
            <th style="text-align:right">Precio</th>
            <th style="text-align:right">Subtotal</th>
            <th style="text-align:center">Acciones</th>
          </tr>
        </thead>
        <tbody class="items-tbody"></tbody>
        <tfoot>
          <tr>
            <td colspan="3" style="text-align:right; font-weight:bold;">Total</td>
            <td class="items-total" style="text-align:right; font-weight:bold;">0.00</td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    `;
    form.appendChild(box);
  }

  const btnAdd = box.querySelector(".btn-add-item");
  const tbody  = box.querySelector(".items-tbody");
  const totalCell = box.querySelector(".items-total");

  function getSelectedProduct(select) {
    if (!select || !select.value || select.value === "nuevo") return null;
    const opt = select.options[select.selectedIndex];
    const precio = parseFloat(opt?.dataset?.precio || "0");
    return { id: Number(select.value), nombre: opt?.dataset?.nombre || opt.textContent, precio };
  }

  function recalc() {
    let total = 0;
    form[itemsStateKey].forEach(it => total += it.cantidad * it.precio);
    totalCell.textContent = total.toFixed(2);
    if (form[totalInputName]) form[totalInputName].value = total.toFixed(2);
  }

  function render() {
    tbody.innerHTML = "";
    form[itemsStateKey].forEach((it, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${it.nombre}</td>
        <td style="text-align:right">${it.cantidad}</td>
        <td style="text-align:right">${it.precio.toFixed(2)}</td>
        <td style="text-align:right">${(it.cantidad * it.precio).toFixed(2)}</td>
        <td style="text-align:center">
          <button type="button" data-idx="${idx}" class="btn-del-item">🗑️</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    recalc();
  }

  btnAdd.addEventListener("click", () => {
    const select = document.getElementById(selectProductoId);
    const p = getSelectedProduct(select);
    const cantInput = form.querySelector(`[name="${cantidadName}"]`);
    const cantidad = parseFloat(cantInput?.value || "1");
    if (!p) { mostrarMensaje(form, "Seleccione un producto válido", "error"); return; }
    if (isNaN(cantidad) || cantidad <= 0) { mostrarMensaje(form, "Cantidad debe ser > 0", "error"); return; }
    form[itemsStateKey].push({ producto_id: p.id, nombre: p.nombre, cantidad, precio: p.precio });
    render();
  });

  tbody.addEventListener("click", (e) => {
    if (e.target.matches(".btn-del-item")) {
      const idx = Number(e.target.dataset.idx);
      form[itemsStateKey].splice(idx, 1);
      render();
    }
  });

  return {
    getItems: () => form[itemsStateKey].map(({ producto_id, cantidad, precio }) => ({ producto_id, cantidad, precio })),
    clear: () => { form[itemsStateKey] = []; render(); }
  };
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('main section h2').forEach(h => h.classList.add('subtitle'));
  // Cargar dropdowns al inicio
  cargarClientesDropdown();
  cargarProveedoresDropdowns();
  cargarProductosDropdowns();

  // Sidebar
  // Sidebar robusto con delegación
const asideNav = document.querySelector('aside nav');
if (asideNav) {
  asideNav.addEventListener('click', (e) => {
    const li = e.target.closest('li[data-target]');
    if (!li) return;
    // Antes de ocultar/mostrar, asegúrate de que el resto del JS no rompa
    try { mostrarSeccion(li.dataset.target); }
    catch {
      // fallback: si algo truena, muestra todas
      document.querySelectorAll('.contenido-seccion').forEach(s => s.style.display = 'block');
    }
  });
}
// Muestra por defecto factura-venta (si existe); si no, muestra todo
try { mostrarSeccion('factura-venta'); }
catch { document.querySelectorAll('.contenido-seccion').forEach(s => s.style.display = 'block'); }

  /* ===============================
     Factura de Venta (con ítems)
     =============================== */
  const formVenta = document.getElementById("form-venta");
  if (formVenta) {
    const ventaItems = setupItemsUI({
      form: formVenta,
      selectProductoId: "select-producto-venta",
      cantidadName: "cantidad",
      totalInputName: "monto",
      itemsStateKey: "__ventaItems__"
    });

    // Manejar selección de cliente
    const selectCliente = document.getElementById("select-cliente-venta");
    selectCliente.addEventListener("change", () => {
      if (selectCliente.value === "nuevo") {
        mostrarSeccion("clientes");
        selectCliente.value = "";
      } else if (selectCliente.value) {
        formVenta.querySelector('[name="cliente"]').value = selectCliente.value;
      }
    });

    // Submit al endpoint NUEVO con ítems
    const handler = async e => {
      e.preventDefault();
      if (selectCliente.value && selectCliente.value !== "nuevo") {
        formVenta.querySelector('[name="cliente"]').value = selectCliente.value;
      }
      const items = ventaItems.getItems();
      if (!items.length) {
        mostrarMensaje(formVenta, "Agregue al menos un ítem antes de guardar.", "error");
        return;
      }
      const payload = {
        cliente: formVenta.cliente.value.trim(),
        descripcion: formVenta.descripcion.value.trim(),
        fecha: formVenta.fecha.value,
        items
      };
      try {
        formVenta.querySelector("button").disabled = true;
        mostrarMensaje(formVenta, "Enviando...", "loading");
        const res = await fetch(`${API_BASE}/api/facturas/venta/con-items/`, {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || res.statusText);
        mostrarMensaje(formVenta, `✅ ${result.message}. Raw ID: ${result.raw_id}.`, "success");

        // opcional: ejecutar ETL
        try { await fetch(`${API_BASE}/api/pipeline/run`, { method: "POST" }); } catch {}

        // refrescar dashboards
        try { if (typeof window.refreshDashboards === 'function') window.refreshDashboards(); } catch {}

        formVenta.reset();
        ventaItems.clear();
        cargarTodo();
      } catch (err) {
        mostrarMensaje(formVenta, `❌ ${err.message}`, "error");
      } finally {
        formVenta.querySelector("button").disabled = false;
      }
    };
    formVenta.addEventListener("submit", handler);
    formVenta._originalHandler = handler;
  }

  /* ===============================
     Factura de Compra (con ítems)
     =============================== */
  const formCompra = document.getElementById("form-compra");
  if (formCompra) {
    const compraItems = setupItemsUI({
      form: formCompra,
      selectProductoId: "select-producto-compra",
      cantidadName: "cantidad",
      totalInputName: "monto",
      itemsStateKey: "__compraItems__"
    });

    // Manejar selección de proveedor
    const selectProveedor = document.getElementById("select-proveedor-compra");
    selectProveedor?.addEventListener("change", () => {
      if (selectProveedor.value === "nuevo") {
        mostrarSeccion("proveedores");
        selectProveedor.value = "";
      } else if (selectProveedor.value) {
        formCompra.querySelector('[name="proveedor"]').value = selectProveedor.value;
      }
    });

    // Submit al endpoint NUEVO con ítems
    const handler = async e => {
      e.preventDefault();
      if (selectProveedor && selectProveedor.value && selectProveedor.value !== "nuevo") {
        formCompra.querySelector('[name="proveedor"]').value = selectProveedor.value;
      }
      const items = compraItems.getItems();
      if (!items.length) {
        mostrarMensaje(formCompra, "Agregue al menos un ítem antes de guardar.", "error");
        return;
      }
      const payload = {
        proveedor: formCompra.proveedor.value.trim(),
        descripcion: formCompra.descripcion.value.trim(),
        fecha: formCompra.fecha.value,
        items
      };
      try {
        formCompra.querySelector("button").disabled = true;
        mostrarMensaje(formCompra, "Enviando...", "loading");
        const res = await fetch(`${API_BASE}/api/facturas/compra/con-items/`, {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || res.statusText);
        mostrarMensaje(formCompra, `✅ ${result.message}. Raw ID: ${result.raw_id}.`, "success");

        try { await fetch(`${API_BASE}/api/pipeline/run`, { method: "POST" }); } catch {}

        // refrescar dashboards
        try { if (typeof window.refreshDashboards === 'function') window.refreshDashboards(); } catch {}

        formCompra.reset();
        compraItems.clear();
        cargarTodo();
      } catch (err) {
        mostrarMensaje(formCompra, `❌ ${err.message}`, "error");
      } finally {
        formCompra.querySelector("button").disabled = false;
      }
    };
    formCompra.addEventListener("submit", handler);
    formCompra._originalHandler = handler;
  }

  // Pagos Recibidos
  const formPagoRecibido = document.getElementById("form-pago-recibido");
  if (formPagoRecibido) {
    const handler = e => {
      e.preventDefault();
      submitForm(e.target, "/api/pagos/recibidos/");
    };
    formPagoRecibido.addEventListener("submit", handler);
    formPagoRecibido._originalHandler = handler;
  }

  // Orden de Compra
  const formOrdenCompra = document.getElementById("form-orden-compra");
  if (formOrdenCompra) {
    const handler = e => {
      e.preventDefault();
      const selectProveedor = document.getElementById("select-proveedor-orden");
      const inputProveedor = formOrdenCompra.querySelector('[name="proveedor"]');
      if (selectProveedor.value && selectProveedor.value !== "nuevo") {
        inputProveedor.value = selectProveedor.value;
      }
      submitForm(e.target, "/api/ordenes/compra/");
    };
    formOrdenCompra.addEventListener("submit", handler);
    formOrdenCompra._originalHandler = handler;

    const selectProveedor = document.getElementById("select-proveedor-orden");
    selectProveedor?.addEventListener("change", () => {
      if (selectProveedor.value === "nuevo") {
        mostrarSeccion("proveedores");
        selectProveedor.value = "";
      } else if (selectProveedor.value) {
        formOrdenCompra.querySelector('[name="proveedor"]').value = selectProveedor.value;
      }
    });
  }

  // Pago Proveedor
  const formPagoProveedor = document.getElementById("form-pago-proveedor");
  if (formPagoProveedor) {
    const handler = e => {
      e.preventDefault();
      submitForm(e.target, "/api/pagos/proveedor/");
    };
    formPagoProveedor.addEventListener("submit", handler);
    formPagoProveedor._originalHandler = handler;
  }

  // Clientes
  const formClientes = document.getElementById("form-clientes");
  if (formClientes) {
    const handler = e => {
      e.preventDefault();
      submitForm(e.target, "/api/clientes/");
    };
    formClientes.addEventListener("submit", handler);
    formClientes._originalHandler = handler;
  }

  // Proveedores
  const formProveedores = document.getElementById("form-proveedores");
  if (formProveedores) {
    const handler = e => {
      e.preventDefault();
      submitForm(e.target, "/api/proveedores/");
    };
    formProveedores.addEventListener("submit", handler);
    formProveedores._originalHandler = handler;
  }

  // Productos
  const formProductos = document.getElementById("form-productos");
  if (formProductos) {
    const handler = e => {
      e.preventDefault();
      submitForm(e.target, "/api/productos/");
    };
    formProductos.addEventListener("submit", handler);
    formProductos._originalHandler = handler;
  }

  // Formulario para Items de Factura (sección separada existente)
  const formFacturaItem = document.getElementById("form-factura-item");
  if (formFacturaItem) {
    const handler = e => {
      e.preventDefault();
      submitForm(e.target, "/api/factura-items/");
    };
    formFacturaItem.addEventListener("submit", handler);
    formFacturaItem._originalHandler = handler;

    const cargarFacturasDropdowns = async () => {
      try {
        // Cargar facturas de venta
        const resVenta = await fetch(`${API_BASE}/api/facturas/venta/`);
        const facturasVenta = await resVenta.json();
        const selectVenta = document.getElementById("select-factura-venta-item");
        selectVenta.innerHTML = '<option value="">-- Seleccione factura de venta --</option>';
        facturasVenta.forEach(f => {
          const option = document.createElement("option");
          option.value = f.id;
          option.textContent = `#${f.id} - ${f.cliente} - ₡${f.monto}`;
          selectVenta.appendChild(option);
        });

        // Cargar facturas de compra
        const resCompra = await fetch(`${API_BASE}/api/facturas/compra/`);
        const facturasCompra = await resCompra.json();
        const selectCompra = document.getElementById("select-factura-compra-item");
        selectCompra.innerHTML = '<option value="">-- Seleccione factura de compra --</option>';
        facturasCompra.forEach(f => {
          const option = document.createElement("option");
          option.value = f.id;
          option.textContent = `#${f.id} - ${f.proveedor} - ₡${f.monto}`;
          selectCompra.appendChild(option);
        });

        // Cargar productos
        const resProductos = await fetch(`${API_BASE}/api/productos/`);
        const productos = await resProductos.json();
        const selectProducto = document.getElementById("select-producto-item");
        selectProducto.innerHTML = '<option value="">-- Seleccione producto --</option>';
        productos.forEach(p => {
          const option = document.createElement("option");
          option.value = p.id;
          option.textContent = `${p.nombre} - ₡${p.precio_unitario}`;
          option.dataset.precio = p.precio_unitario;
          selectProducto.appendChild(option);
        });
      } catch (error) {
        console.error("Error cargando dropdowns:", error);
      }
    };

    cargarFacturasDropdowns();

    const tipoSelect = document.getElementById("select-tipo-factura-item");
    const selectVenta = document.getElementById("select-factura-venta-item");
    const selectCompra = document.getElementById("select-factura-compra-item");
    const labelVenta = document.getElementById("label-factura-venta");
    const labelCompra = document.getElementById("label-factura-compra");

    tipoSelect?.addEventListener("change", () => {
      if (tipoSelect.value === "venta") {
        selectVenta.style.display = "block";
        labelVenta.style.display = "block";
        selectVenta.required = true;
        selectCompra.style.display = "none";
        labelCompra.style.display = "none";
        selectCompra.required = false;
        selectCompra.value = "";
      } else if (tipoSelect.value === "compra") {
        selectVenta.style.display = "none";
        labelVenta.style.display = "none";
        selectVenta.required = false;
        selectVenta.value = "";
        selectCompra.style.display = "block";
        labelCompra.style.display = "block";
        selectCompra.required = true;
      } else {
        selectVenta.style.display = "none";
        labelVenta.style.display = "none";
        selectCompra.style.display = "none";
        labelCompra.style.display = "none";
        selectVenta.required = false;
        selectCompra.required = false;
      }
    });

    const selectProducto = document.getElementById("select-producto-item");
    const precioInput = document.getElementById("precio-item");
    const cantidadInput = document.getElementById("cantidad-item");
    const subtotalInput = document.getElementById("subtotal-item");

    const calcularSubtotal = () => {
      const precio = parseFloat(precioInput.value) || 0;
      const cantidad = parseInt(cantidadInput.value) || 0;
      subtotalInput.value = (precio * cantidad).toFixed(2);
    };

    selectProducto?.addEventListener("change", () => {
      if (selectProducto.value) {
        const option = selectProducto.options[selectProducto.selectedIndex];
        precioInput.value = option.dataset.precio;
        calcularSubtotal();
      }
    });

    cantidadInput?.addEventListener("input", calcularSubtotal);
    precioInput?.addEventListener("input", calcularSubtotal);

    tipoSelect.dispatchEvent(new Event("change"));
  }

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

  // Reportes
  document.getElementById("btn-generar-reportes")?.addEventListener("click", async () => {
    const sec = document.getElementById("reportes");
    mostrarMensaje(sec, "Generando reportes...", "loading");
    try {
      // Cargar resumen financiero
      const resResumen = await fetch(`${API_BASE}/api/reportes/resumen/`);
      if (!resResumen.ok) throw new Error(await resResumen.text());
      const resumen = await resResumen.json();

      // Cargar facturas pendientes
      const resPendientes = await fetch(`${API_BASE}/api/reportes/facturas-pendientes/`);
      if (!resPendientes.ok) throw new Error(await resPendientes.text());
      const pendientes = await resPendientes.json();

      // Actualizar resumen financiero
      const resumenContent = document.getElementById("resumen-content");
      resumenContent.innerHTML = `
        <div style="padding: 10px; background: #e8f5e9; border-radius: 5px;">
          <h4>💵 Total Ingresos</h4>
          <p style="font-size: 24px; font-weight: bold;">₡${resumen.total_ingresos.toFixed(2)}</p>
        </div>
        <div style="padding: 10px; background: #ffebee; border-radius: 5px;">
          <h4>💸 Total Gastos</h4>
          <p style="font-size: 24px; font-weight: bold;">₡${resumen.total_gastos.toFixed(2)}</p>
        </div>
        <div style="padding: 10px; background: #e3f2fd; border-radius: 5px;">
          <h4>✅ Pagos Recibidos</h4>
          <p style="font-size: 24px; font-weight: bold;">₡${resumen.total_pagos_recibidos.toFixed(2)}</p>
        </div>
        <div style="padding: 10px; background: #fff3e0; border-radius: 5px;">
          <h4>💰 Pagos a Proveedores</h4>
          <p style="font-size: 24px; font-weight: bold;">₡${resumen.total_pagos_proveedor.toFixed(2)}</p>
        </div>
        <div style="padding: 10px; background: #f3e5f5; border-radius: 5px;">
          <h4>📊 Cuentas por Cobrar</h4>
          <p style="font-size: 24px; font-weight: bold;">₡${resumen.cuentas_por_cobrar.toFixed(2)}</p>
        </div>
        <div style="padding: 10px; background: #fce4ec; border-radius: 5px;">
          <h4>📋 Cuentas por Pagar</h4>
          <p style="font-size: 24px; font-weight: bold;">₡${resumen.cuentas_por_pagar.toFixed(2)}</p>
        </div>
        <div style="padding: 10px; background: ${resumen.balance >= 0 ? '#c8e6c9' : '#ffcdd2'}; border-radius: 5px; grid-column: span 2;">
          <h4>🎯 Balance General</h4>
          <p style="font-size: 32px; font-weight: bold;">₡${resumen.balance.toFixed(2)}</p>
        </div>
      `;

      // Ventas pendientes
      const tbodyVentas = document.getElementById("tabla-ventas-pendientes");
      if (tbodyVentas) {
        tbodyVentas.innerHTML = "";
        pendientes.facturas_venta_pendientes.forEach(f => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${f.id}</td>
            <td>${f.cliente}</td>
            <td>₡${f.monto.toFixed(2)}</td>
            <td>₡${f.pagado.toFixed(2)}</td>
            <td style="color: red; font-weight: bold;">₡${f.pendiente.toFixed(2)}</td>
            <td>${f.fecha}</td>
          `;
          tbodyVentas.append(tr);
        });
      }

      // Compras pendientes
      const tbodyCompras = document.getElementById("tabla-compras-pendientes");
      if (tbodyCompras) {
        tbodyCompras.innerHTML = "";
        pendientes.facturas_compra_pendientes.forEach(f => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${f.id}</td>
            <td>${f.proveedor}</td>
            <td>₡${f.monto.toFixed(2)}</td>
            <td>₡${f.pagado.toFixed(2)}</td>
            <td style="color: red; font-weight: bold;">₡${f.pendiente.toFixed(2)}</td>
            <td>${f.fecha}</td>
          `;
          tbodyCompras.append(tr);
        });
      }

      mostrarMensaje(sec, "✅ Reportes actualizados", "success");
    } catch (e) {
      mostrarMensaje(sec, `❌ ${e.message}`, "error");
    }
  });

  // Delegación para editar/borrar
  document.querySelector("main").addEventListener("click", handleTableClick);

  // Carga inicial
  cargarTodo();
});
