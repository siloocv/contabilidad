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
(Pendiente de implementación)

## **Integración de Tailwind + gráficos**
(Pendiente de implementación)