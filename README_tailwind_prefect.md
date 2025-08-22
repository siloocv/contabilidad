# Bitácora de Cambios - Proyecto Contabilidad

Este documento registra de forma técnica los cambios y nuevas implementaciones hechas en el proyecto, antes de integrarlos al README principal.

---
### Frontend (con TailwindCSS)
1. Entra a la carpeta `frontend/`:  
   ```bash
   cd frontend
   npm install
   ```
2. Si es la primera vez, instala Tailwind manualmente:  
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init
   ```
3. Compila TailwindCSS en modo watch:  
   ```bash
   npx tailwindcss -i ./src/tailwind.css -o ./dist/tailwind.css --watch
   ```
4. Sirve el frontend:  
   ```bash
   python3 -m http.server 5500
   ```
   Luego abre [http://localhost:5500/index.html](http://localhost:5500/index.html).

---

## Uso del sistema

### Backend
1. Levanta el backend con Uvicorn:  
   ```bash
   uvicorn main:app --reload
   ```

### Frontend
1. Abre el archivo `frontend/index.html` en tu navegador.  
2. Funcionalidades:  
   - Registrar facturas de venta o compra (guardadas en `raw_data`).  
   - Acceder a la pestaña **Admin / ETL** para:  
     - Ejecutar el pipeline manualmente.  
     - Visualizar datos limpios en `cleaned_data`.  

---

## Ejecución del pipeline

### Modo Prefect 3 (recomendado)
#### Automático (cada 15 minutos con cron)
```bash
python -m orchestrator.prefect_flow
```

#### Con interfaz (UI de Prefect)
```bash
prefect server start
export PREFECT_API_URL=http://127.0.0.1:4200/api
prefect work-pool create default --type process
prefect worker start --pool default
python -m orchestrator.prefect_flow
```
- UI: http://127.0.0.1:4200  
- API: http://127.0.0.1:4200/api  

**Notas técnicas:**  
- Cron: `*/15 * * * *`  
- Respaldos `.csv` en `backups/` y logs `.json` en `logs/`.  
- Tipos válidos en `raw_data.tipo`: `ingreso`, `gasto`, `orden_compra`, `factura_recurrente`, `pago_recibido`, `pago_proveedor`.  

### Modo manual (desde frontend)
- Ir a Admin / ETL → “Ejecutar limpieza manual”.  
- Procesa `raw_data` → guarda en `cleaned_data`. 

---

## Sobre Orquestador ETL con Prefect

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

---

## Estructura relevante del proyecto
```
frontend/
│── dist/               # CSS generado por Tailwind
│── src/                # Archivos fuente (tailwind.css)
│── main.js             # Lógica JS
│── index.html          # Página principal
orchestrator/
│── prefect_flow.py     # Flow ETL con Prefect 3
```
