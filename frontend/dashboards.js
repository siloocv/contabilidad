// frontend/dashboards.js
(function () {
  const API = (window.__API_BASE__ || "").replace(/\/+$/, "");

  const state = {
    ventas: null,
    compras: null,
    loadedOnce: false,
  };

  // ---------- Helpers ----------
  function parseISODate(s) {
    // espera "YYYY-MM-DD"
    if (!s || typeof s !== "string") return null;
    const [y, m, d] = s.split("-").map(Number);
    if (!y || !m || !d) return null;
    return new Date(y, m - 1, d);
  }

  function lastNMonths(n = 12) {
    const base = new Date();
    base.setDate(1); // 1ro del mes actual
    const labels = [];
    const keys = [];
    for (let i = n - 1; i >= 0; i--) {
      const d = new Date(base.getFullYear(), base.getMonth() - i, 1);
      labels.push(d.toLocaleString("es-CR", { month: "short" })); // ene, feb...
      keys.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
    }
    return { labels, keys };
  }

  function monthKey(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  function formatCRC(n) {
    try {
      return new Intl.NumberFormat("es-CR", {
        style: "currency",
        currency: "CRC",
        maximumFractionDigits: 0,
      }).format(n || 0);
    } catch {
      return "₡ " + Math.round(n || 0).toLocaleString("es-CR");
    }
  }

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function sumBetween(rows, fromDate) {
    let s = 0;
    for (const r of rows) {
      const d = parseISODate(r.fecha);
      if (!d) continue;
      if (d >= fromDate) s += Number(r.monto || 0);
    }
    return s;
  }

  function avgAmount(rows) {
    if (!rows.length) return 0;
    const total = rows.reduce((acc, r) => acc + Number(r.monto || 0), 0);
    return rows.length ? total / rows.length : 0;
  }

  function seriesByMonth(rows) {
    const { labels, keys } = lastNMonths(12);
    const map = new Map(keys.map((k) => [k, 0]));
    for (const r of rows) {
      const d = parseISODate(r.fecha);
      if (!d) continue;
      const mk = monthKey(d);
      if (map.has(mk)) {
        map.set(mk, map.get(mk) + Number(r.monto || 0));
      }
    }
    return { labels, values: keys.map((k) => map.get(k) || 0) };
  }

  // ---------- Fetch ----------
  async function getVentas() {
    if (state.ventas) return state.ventas;
    const res = await fetch(`${API}/api/facturas/venta/`);
    if (!res.ok) throw new Error("No se pudo obtener ventas");
    const data = await res.json();
    state.ventas = Array.isArray(data) ? data : [];
    return state.ventas;
  }

  async function getCompras() {
    if (state.compras) return state.compras;
    const res = await fetch(`${API}/api/facturas/compra/`);
    if (!res.ok) throw new Error("No se pudo obtener compras");
    const data = await res.json();
    state.compras = Array.isArray(data) ? data : [];
    return state.compras;
  }

  // ---------- Render ----------
  async function renderIngresos() {
    const ventas = await getVentas();

    // KPIs
    const now = new Date();
    const startMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const start30 = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 30);
    setText("kpi_ingresos_mes", formatCRC(sumBetween(ventas, startMonth)));
    setText("kpi_ingresos_30d", formatCRC(sumBetween(ventas, start30)));
    setText("kpi_ticket_prom", formatCRC(avgAmount(ventas)));

    // Serie mensual
    const serie = seriesByMonth(ventas);

    // Chart
    const canvas = document.getElementById("chart_ingresos");
    if (!canvas) return;
    const existing = Chart.getChart(canvas);
    const data = {
      labels: serie.labels,
      datasets: [
        {
          label: "Ingresos",
          data: serie.values,
          borderWidth: 2,
          tension: 0.3,
          fill: true,
        },
      ],
    };
    if (existing) {
      existing.data = data;
      existing.update();
    } else {
      new Chart(canvas, {
        type: "line",
        data,
        options: { responsive: true, scales: { y: { beginAtZero: true } } },
      });
    }
  }

  async function renderGastos() {
    const compras = await getCompras();

    const now = new Date();
    const startMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const start30 = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 30);
    setText("kpi_gastos_mes", formatCRC(sumBetween(compras, startMonth)));
    setText("kpi_gastos_30d", formatCRC(sumBetween(compras, start30)));
    setText("kpi_categoria_top", "—"); // Si luego tienes categorías, lo calculamos

    const serie = seriesByMonth(compras);

    const canvas = document.getElementById("chart_gastos");
    if (!canvas) return;
    const existing = Chart.getChart(canvas);
    const data = {
      labels: serie.labels,
      datasets: [
        {
          label: "Gastos",
          data: serie.values,
          borderWidth: 2,
          tension: 0.3,
        },
      ],
    };
    if (existing) {
      existing.data = data;
      existing.update();
    } else {
      new Chart(canvas, {
        type: "bar",
        data,
        options: { responsive: true, scales: { y: { beginAtZero: true } } },
      });
    }
  }

  function ensureDashboardsOnOpen() {
    if (state.loadedOnce) return;
    state.loadedOnce = true;
    // Por defecto cargamos la pestaña "Ingresos"
    renderIngresos().catch(console.error);
  }

  // ---------- Hooks ----------
  // 1) Cuando haces click en el sidebar y abres "Dashboards"
  document.addEventListener("click", (e) => {
    const li = e.target.closest("li[data-target]");
    if (!li) return;
    if (li.dataset.target === "dashboards") {
      ensureDashboardsOnOpen();
    }
  });

  // 2) Cuando cambias de pestaña dentro de la sección "Dashboards"
  document.addEventListener("dashboards:show", (e) => {
    const tab = e.detail?.tab;
    if (tab === "ingresos") renderIngresos().catch(console.error);
    if (tab === "gastos") renderGastos().catch(console.error);
  });

  // 3) Si por alguna razón "Dashboards" ya está visible al cargar
  document.addEventListener("DOMContentLoaded", () => {
    const sec = document.getElementById("dashboards");
    if (sec && sec.style.display !== "none") {
      ensureDashboardsOnOpen();
    }
  });
}
)();

// Permite refrescar desde otros módulos (p.ej., main.js)
window.refreshDashboards = async function () {
  try {
    // invalidar caché local
    if (state) {
      state.ventas = null;
      state.compras = null;
    }
    const sec = document.getElementById('dashboards');
    if (!sec) return;

    const ingVisible = document.getElementById('panel-ingresos')?.style.display !== 'none';
    const gasVisible = document.getElementById('panel-gastos')?.style.display !== 'none';

    // si la pestaña está visible, vuelve a renderizar
    if (ingVisible) await renderIngresos();
    if (gasVisible) await renderGastos();
  } catch (e) {
    console.error('refreshDashboards error:', e);
  }
};
