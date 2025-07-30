Sistema Contable Web con Pipeline ETL

Descripción del proyecto

Este proyecto consiste en una aplicación web contable que permite registrar y visualizar ingresos y gastos mediante formularios de facturas de venta y compra. Los datos se almacenan inicialmente en una tabla raw_data y posteriormente son procesados mediante un pipeline ETL automatizado y manual, generando una tabla cleaned_data que contiene información validada y limpia.
La aplicación fue desarrollada con:
Frontend en HTML, CSS y JavaScript
Backend en FastAPI
Base de datos en MySQL
Orquestación del pipeline con apscheduler


Requisitos previos

Python 3.9 o superior
MySQL Server
MySQL Workbench
Navegador moderno (Chrome, Firefox, Edge, etc.)
Terminal para ejecutar scripts Python


Instalación

Clona o descarga el proyecto.
Crea y activa un entorno virtual:
python -m venv venv
source venv/bin/activate      # En macOS/Linux
venv\Scripts\activate         # En Windows
Instala las dependencias:
pip install -r requirements.txt
Asegurate de tener una base de datos llamada contabilidad en MySQL. Ejecutá los scripts SQL incluidos para crear las tablas necesarias: raw_data, cleaned_data, facturas_venta, facturas_compra.


Uso del sistema

Levantá el backend:
uvicorn main:app --reload
Abrí el archivo frontend/index.html en tu navegador.
Desde el frontend podés:
Registrar facturas de venta o compra (se guardan en raw_data)
Ingresar a la pestaña Admin / ETL para:
Ejecutar el pipeline manualmente
Visualizar los datos limpios (cleaned_data)


Ejecución del pipeline

🔹 Manual (desde el frontend)
Ir a la sección Admin / ETL
Presionar el botón “Ejecutar limpieza manual”
Los datos de raw_data serán procesados y almacenados en cleaned_data
🔹 Automática (cada 10 minutos)
En una terminal aparte, ejecutar:
python scheduler.py
El script se encargará de ejecutar el ETL automáticamente cada 10 minutos.