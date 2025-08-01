import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from etl_pipeline import run_etl
from database import SessionLocal
import models
from decimal import Decimal

# Logging
logging.basicConfig(
    filename="scheduler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

_running = False
_lock = threading.Lock()

def generar_facturas_recurrentes():
    db = SessionLocal()
    try:
        ahora = datetime.utcnow()
        templates = db.query(models.FacturaRecurrenteTemplate).filter(models.FacturaRecurrenteTemplate.siguiente_generacion <= ahora).all()
        for t in templates:
            # Crear instancia
            instancia = models.FacturaRecurrenteInstance(
                template_id=t.id,
                cliente=t.cliente,
                descripcion=t.descripcion,
                monto=t.monto,
                fecha=ahora.date(),
                raw_id=None,
            )
            db.add(instancia)
            # Actualizar siguiente_generacion de acuerdo a frecuencia simple (solo mensual como ejemplo)
            if t.frecuencia.lower() == "mensual":
                # sumar un mes (aproximado)
                mes = t.siguiente_generacion.month + 1
                año = t.siguiente_generacion.year
                if mes > 12:
                    mes = 1
                    año += 1
                try:
                    t.siguiente_generacion = t.siguiente_generacion.replace(year=año, month=mes)
                except ValueError:
                    # falla con día fuera de rango, simplificamos desplazando 30 días
                    t.siguiente_generacion = t.siguiente_generacion + timedelta(days=30)
            else:
                # fallback: sumar 30 días
                t.siguiente_generacion = t.siguiente_generacion + timedelta(days=30)
            db.commit()
            logging.info(f"Generada factura recurrente instance {instancia.id} de template {t.id}")
    except Exception:
        logging.exception("Error generando facturas recurrentes")
    finally:
        db.close()

def ejecutar_pipeline_seguro():
    global _running
    with _lock:
        if _running:
            logging.info("Salteando ejecución: ya hay un pipeline en curso.")
            return
        _running = True
    try:
        logging.info("Generando facturas recurrentes si toca...")
        generar_facturas_recurrentes()
        logging.info("Ejecutando ETL...")
        resumen = run_etl()
        logging.info(f"ETL completado: limpios={resumen.get('registros_limpios')}")
    except Exception as e:
        logging.exception(f"Error en scheduler: {e}")
    finally:
        with _lock:
            _running = False

# Programar cada 10 minutos
schedule.every(10).minutes.do(ejecutar_pipeline_seguro)

logging.info("Scheduler iniciado. Pipeline y recurrentes cada 10 minutos.")

def loop():
    while True:
        try:
            schedule.run_pending()
        except Exception:
            logging.exception("Error en schedule.run_pending()")
        time.sleep(5)

if __name__ == "__main__":
    loop()

