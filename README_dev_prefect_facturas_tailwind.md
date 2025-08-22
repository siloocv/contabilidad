# Bitácora de Cambios - Proyecto Contabilidad

Este documento registra de forma técnica los cambios y nuevas implementaciones hechas en el proyecto, antes de integrarlos al README principal.

---

## 1. Orquestador ETL con Prefect

### Descripción
Se integró **Prefect 3** para orquestar la ejecución del pipeline ETL (`etl_pipeline.py`), que antes se ejecutaba manualmente desde un botón en el frontend.  
Ahora el ETL puede ejecutarse:
- **Automáticamente cada 15 minutos** mediante un cron programado.
- **Manual** desde la terminal (o en un futuro desde un endpoint en FastAPI).

Se mantiene la funcionalidad original del ETL:
1. Leer datos desde `raw_data`.
2. Validar y respaldar datos en `backups/` y `logs/`.
3. Insertar registros procesados en las tablas correspondientes.
4. Generar métricas básicas en un archivo JSON de log.

### Archivos y cambios realizados
- Nuevo archivo: `orchestrator/prefect_flow.py` → define el flow `etl_flow` y su tarea `etl_task`.
- `requirements.txt` → agregado `prefect>=3.0.0`.

### Instrucciones de uso

#### **Modo simple (sin UI, recomendado para pruebas locales)**
1. Activar el entorno virtual:
   ```bash
   source venv/bin/activate
2. Instalar dependencias:
    pip install -r requirements.txt
3. Ejecutar el flow con cron:
    python -m orchestrator.prefect_flow
4. Mantener esa terminal especifica abierta para que ejecute cada 15 minutos.

#### **Modo con UI y worker (monitoreo y logs históricos)**
1. Activar entorno virtual:
    source venv/bin/activate
2. Instalar dependencias:
    pip install -r requirements.txt
3. Iniciar servidor Prefect (UI local):
    prefect server start

- UI: http://127.0.0.1:4200
- API: http://127.0.0.1:4200/api

4. Exportar la variable de API y crear pool:
    export PREFECT_API_URL=http://127.0.0.1:4200/api
    prefect work-pool create default --type process
5. Iniciar worker:
    prefect worker start --pool default
6. En otra terminal, servir el flow:
    python -m orchestrator.prefect_flow

**Notas técnicas**
- Cron configurado en prefect_flow.py: */15 * * * * (cada 15 minutos).
- Tipos válidos de raw_data.tipo: ingreso, gasto, orden_compra, factura_recurrente, pago_recibido, pago_proveedor.
- Si total_cleaned es 0, probablemente se deba a registros con campos inválidos o tipos no incluidos en VALID_TYPES.
- Respaldos .csv en backups/ y logs .json en logs/.
- Archivos recomendados en .gitignore:
    backups/*.csv
    logs/*.json

## **Facturas con múltiples productos**


## **Integración de Tailwind + dashboards**

Este proyecto ahora incluye integración con **TailwindCSS** para los estilos de la interfaz.  
Sigue estas instrucciones para levantar el entorno correctamente.

---

## 📦 Requisitos previos

- **Node.js** (v18 o superior)
- **npm** o **yarn**
- Tener el backend corriendo (para que las API funcionen)

---

## 🚀 Instalación

1. Clonar el repositorio y entrar en la carpeta del frontend:
   ```bash
   git clone https://github.com/siloocv/contabilidad.git
   cd frontend
   ```

2. Instalar dependencias (incluye TailwindCSS y PostCSS):
   ```bash
   npm install
   ```

   Si es la primera vez que instalas Tailwind en tu máquina o hay problemas, puedes reinstalar manualmente:
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init
   ```

---

## 🛠️ Compilar TailwindCSS

Este proyecto usa Tailwind con la configuración en `src/tailwind.css`.  
Para compilar el CSS y ver los cambios en vivo:

```bash
npx tailwindcss -i ./src/tailwind.css -o ./dist/tailwind.css --watch
```

⚠ **Nota:** Deja este comando corriendo en una terminal mientras trabajas en el frontend para que Tailwind regenere el CSS al hacer cambios.

---

## ▶ Ejecutar el Frontend

Este frontend es HTML/JS puro, así que puedes servirlo con una extensión de servidor local o con Python, por ejemplo:

```bash
# Opción 1: Servidor con Python
python3 -m http.server 5500

# Opción 2: Extensión de VSCode "Live Server"
```

Luego abre en el navegador:
```
http://localhost:5500/index.html
```

---

## 📁 Estructura relevante

```
frontend/
│── dist/               # CSS generado por Tailwind
│── src/                # Archivos fuente (tailwind.css)
│── main.js             # Lógica JS de la aplicación
│── index.html          # Página principal
```

---

## 👩‍💻 Consejos para desarrollo

- Edita estilos en `src/tailwind.css`, **no** en `dist/tailwind.css`.
- No borres el archivo generado `dist/tailwind.css`, es necesario para que el proyecto funcione.
- Usa clases de Tailwind directamente en el HTML para nuevos estilos.