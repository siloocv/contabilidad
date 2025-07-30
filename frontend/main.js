// Cambiar entre secciones visibles
function mostrarSeccion(id) {
  const secciones = document.querySelectorAll('.contenido-seccion');
  secciones.forEach(sec => sec.style.display = 'none');

  const activa = document.getElementById(id);
  if (activa) {
    activa.style.display = 'block';

    // Si es la sección Admin / ETL, cargar los datos limpios
    if (id === "admin-etl") {
      cargarDatosLimpios();
    }
  }
}

// Enviar factura de venta (como ingreso a raw_data)
document.getElementById("form-venta").addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    tipo: "ingreso",
    descripcion: `${e.target.cliente.value} - ${e.target.descripcion.value}`,
    monto: parseFloat(e.target.monto.value),
    fecha: e.target.fecha.value
  };

  try {
    const res = await fetch("http://127.0.0.1:8000/api/raw/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    if (res.ok) {
      alert("✅ Factura de venta guardada en datos crudos");
      e.target.reset();
    } else {
      alert("❌ Error al guardar");
    }
  } catch (err) {
    alert("❌ Error de conexión");
  }
});

// Enviar factura de compra (como gasto a raw_data)
document.getElementById("form-compra").addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    tipo: "gasto",
    descripcion: `${e.target.proveedor.value} - ${e.target.descripcion.value}`,
    monto: parseFloat(e.target.monto.value),
    fecha: e.target.fecha.value
  };

  try {
    const res = await fetch("http://127.0.0.1:8000/api/raw/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    if (res.ok) {
      alert("✅ Factura de compra guardada en datos crudos");
      e.target.reset();
    } else {
      alert("❌ Error al guardar");
    }
  } catch (err) {
    alert("❌ Error de conexión");
  }
});

// Ejecutar el pipeline manualmente
async function ejecutarPipeline() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/pipeline/run", {
      method: "POST"
    });
    const data = await res.json();
    if (data.status === "ok") {
      alert("🧼 Limpieza ejecutada correctamente.");
      cargarDatosLimpios();
    } else {
      alert("❌ Error al ejecutar el pipeline.");
    }
  } catch (err) {
    alert("❌ Error al ejecutar el pipeline.");
  }
}

// Cargar tabla de cleaned_data
async function cargarDatosLimpios() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/cleaned/");
    const datos = await res.json();

    const tbody = document.getElementById("tabla-etl");
    tbody.innerHTML = "";

    datos.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.id}</td>
        <td>${row.tipo}</td>
        <td>${row.descripcion}</td>
        <td>${row.monto}</td>
        <td>${row.fecha}</td>
        <td>${row.validado_por}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error cargando datos limpios:", err);
  }
}