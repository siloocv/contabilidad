Sistema Contable Web con Pipeline ETL

DESCRIPCIÓN
Aplicación web contable para registrar ingresos, gastos, órdenes de compra y pagos. Los registros de tipo ingreso, gasto y orden_compra entran en raw_data; el pipeline ETL los valida y normaliza en cleaned_data y a partir de ahí genera automáticamente facturas de venta, facturas de compra y órdenes de compra. Los pagos recibidos y pagos a proveedor se crean directamente y no pasan por el ETL.

REQUISITOS
Python 3.9+ (recomendado 3.11)
MySQL Server corriendo localmente
Cliente MySQL Workbench o CLI
Navegador moderno
Terminal (PowerShell o cmd)

ESTRUCTURA
create_tables.sql (script que crea la base, usuario, permisos y todas las tablas necesarias)
database.py (configuración de SQLAlchemy y URL de conexión)
etl_pipeline.py (pipeline: extrae de raw_data, limpia, escribe en cleaned_data y genera facturas/órdenes)
main.py (API FastAPI)
scheduler.py (ejecuta el pipeline automáticamente cada 10 minutos)
frontend/index.html, main.js, style.css (UI)
backups/ (CSV de raw y cleaned generados por el ETL)
logs/ (resúmenes de ejecución)

PREPARACIÓN Y PUESTA EN MARCHA
Entrar al directorio del proyecto.
Crear la base y esquema: abrir MySQL Workbench, pegar y ejecutar el contenido de create_tables.sql. Ese script debe crear la base "contabilidad", el usuario "sebas"@localhost con contraseña "YES" (u otros si se cambian) con privilegios, y las tablas: raw_data, cleaned_data, facturas_venta, facturas_compra, ordenes_compra, pagos_recibidos, pagos_proveedor, facturas_recurrentes_template/instance, etc. Si se modifican credenciales o nombre de base, esos mismos valores deben actualizarse en los archivos de código.
Crear y activar el entorno virtual: ejecutar python -m venv .venv. En PowerShell, si hay restricción, ejecutar una sola vez Set-ExecutionPolicy RemoteSigned -Scope CurrentUser y luego ..venv\Scripts\Activate.ps1. En cmd.exe usar ..venv\Scripts\activate.bat.
Instalar dependencias: pip install -r requirements.txt. 

CONFIGURACIÓN DE LA CONEXIÓN
En database.py y etl_pipeline.py deben usar la misma cadena de conexión. Por defecto: mysql+pymysql://sebas:YES@localhost:3306/contabilidad?charset=utf8mb4. Si se cambió usuario, contraseña o nombre de base en el script SQL, actualizar esa URL en ambos archivos.

LEVANTAR SERVICIOS
Backend: ejecutar uvicorn main:app --reload. La documentación está disponible en http://127.0.0.1:8000/docs.
En otro terminal:
Frontend: desde la carpeta frontend ejecutar python -m http.server 8080. Abrir en el navegador http://localhost:8080/index.html. Siempre vía HTTP, no con file://.

FLUJO DE DATOS
Se crean raws de tipo ingreso, gasto u orden_compra desde el frontend o por API. El pipeline se ejecuta manual desde la UI en Admin/ETL o automáticamente si se corre scheduler.py cada 10 minutos. El pipeline extrae los raws válidos, los limpia y los inserta en cleaned_data con metadatos como validado_por y tabla_destino. A partir de cleaned_data crea facturas_venta (desde ingreso), facturas_compra (desde gasto) y ordenes_compra (desde orden_compra). El pipeline genera respaldos en backups/ y escribe un resumen en logs/.

PAGOS (QUÉ NO PASA POR EL ETL)
Pagos recibidos y pagos a proveedor no se incluyen en cleaned_data. Se crean directamente en sus tablas correspondientes mediante sus endpoints.

ENDPOINTS
POST /api/raw/ para crear raw_data.
GET /api/raw/ para listar raws.
POST /api/pipeline/run para ejecutar el ETL.
GET /api/cleaned/ para obtener datos limpios.
GET /api/facturas/venta/ para listar facturas de venta.
GET /api/facturas/compra/ para listar facturas de compra.
POST /api/pagos/recibidos/ para registrar pago recibido (requiere factura_venta_id, monto, fecha).
POST /api/pagos/proveedor/ para registrar pago a proveedor (requiere al menos factura_compra_id o orden_compra_id, monto y fecha).

DATOS PERSISTIDOS
El pipeline guarda backups en la carpeta backups y el resumen de cada corrida en logs. Las relaciones entre raw, cleaned y entidades finales se conservan mediante raw_id y tabla_destino.

CONSIDERACIONES FINALES
Cambios de credenciales o nombre de base deben reflejarse en el script SQL y en database.py y etl_pipeline.py. No hay autenticación. Los pagos no se normalizan en el ETL por decisión de diseño actual. Mejores futuras incluyen integrar pagos en el ETL o añadir una vista unificada por raw_id.

ATAJOS
Frontend: http://localhost:8080/index.html
Swagger / documentación: http://127.0.0.1:8000/docs
