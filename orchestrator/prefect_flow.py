# orchestrator/prefect_flow.py
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from prefect import flow, task, get_run_logger
from etl_pipeline import run_etl

@task(retries=2, retry_delay_seconds=30)
def etl_task():
    logger = get_run_logger()
    result = run_etl()
    logger.info(f"ETL OK: {result}")
    return result

@flow(name="etl-flow")
def etl_flow():
    return etl_task()

if __name__ == "__main__":
    # Crea deployment con cron de 15 minutos
    etl_flow.serve(
        name="etl-15min",
        cron="*/15 * * * *",
        tags=["etl", "contabilidad"]
    )
