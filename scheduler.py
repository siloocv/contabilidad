import schedule
import time
import subprocess

def ejecutar_pipeline():
    print("Ejecutando ETL automáticamente...")
    result = subprocess.run(["python", "etl_pipeline.py"], capture_output=True, text=True)
    print(result.stdout)

# Programar cada 10 minutos
schedule.every(10).minutes.do(ejecutar_pipeline)

print("Scheduler iniciado. El pipeline se ejecutará cada 10 minutos.")

# Bucle infinito
while True:
    schedule.run_pending()
    time.sleep(1)
