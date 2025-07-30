import csv
import json
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuración
DATABASE_URL = "mysql+pymysql://root:siloe461@localhost:3306/contabilidad"
engine = create_engine(DATABASE_URL)

# Timestamp para nombres de archivos
now = datetime.now().strftime("%Y%m%d_%H%M%S")

def run_etl():
    with engine.begin() as conn:
        # 1. EXTRAER desde raw_data
        result = conn.execute(text("SELECT * FROM raw_data"))
        rows = result.fetchall()
        columns = result.keys()

        # Backup de raw_data
        with open(f"backups/raw_{now}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        cleaned = []
        for row in rows:
            row_dict = dict(zip(columns, row))

            # Validaciones básicas
            if not row_dict["descripcion"] or row_dict["monto"] is None or row_dict["tipo"] not in ["ingreso", "gasto"]:
                continue

            cleaned.append({
                "id": row_dict["id"],
                "tipo": row_dict["tipo"],
                "descripcion": row_dict["descripcion"].strip(),
                "monto": float(row_dict["monto"]),
                "fecha": row_dict["fecha"],
                "creado_en": row_dict["creado_en"],
                "validado_por": "etl_pipeline"
            })

        # Backup de cleaned_data
        if cleaned:
            with open(f"backups/cleaned_{now}.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=cleaned[0].keys())
                writer.writeheader()
                writer.writerows(cleaned)

        # 3. CARGAR a cleaned_data
        conn.execute(text("TRUNCATE TABLE cleaned_data"))
        for item in cleaned:
            conn.execute(text("""
                INSERT INTO cleaned_data (id, tipo, descripcion, monto, fecha, creado_en, validado_por)
                VALUES (:id, :tipo, :descripcion, :monto, :fecha, :creado_en, :validado_por)
            """), item)

        # 4. Log del proceso
        log_data = {
            "timestamp": now,
            "registros_totales": len(rows),
            "registros_limpios": len(cleaned),
            "raw_backup": f"backups/raw_{now}.csv",
            "cleaned_backup": f"backups/cleaned_{now}.csv"
        }

        with open(f"logs/log_{now}.json", "w") as f:
            json.dump(log_data, f, indent=4)

        print(f"ETL completado — {len(cleaned)} registros limpios cargados.")

if __name__ == "__main__":
    run_etl()
