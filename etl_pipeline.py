import csv
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from decimal import Decimal
import os

# URL unificado: usa el mismo usuario/DB que tenés en el esquema
DATABASE_URL = "mysql+pymysql://sebas:YES@localhost:3306/contabilidad?charset=utf8mb4"
engine = create_engine(DATABASE_URL)

# Directorios
os.makedirs("backups", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def run_etl():
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    with engine.begin() as conn:
        # 1. EXTRAER
        result = conn.execute(text("SELECT * FROM raw_data"))
        rows = result.fetchall()
        columns = result.keys()

        # Backup raw
        with open(f"backups/raw_{now}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        cleaned = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            tipo = (row_dict.get("tipo") or "").lower()
            if tipo not in ("ingreso", "gasto", "orden_compra"):
                # por ahora solo normalizamos esos tres tipos
                continue

            descripcion = (row_dict.get("descripcion") or "").strip()
            monto = row_dict.get("monto")
            fecha = row_dict.get("fecha")
            creado_en = row_dict.get("creado_en")

            if monto is None or not descripcion or not fecha:
                continue  # fila incompleta

            tabla_destino = None
            if tipo == "ingreso":
                tabla_destino = "facturas_venta"
            elif tipo == "gasto":
                tabla_destino = "facturas_compra"
            elif tipo == "orden_compra":
                tabla_destino = "ordenes_compra"

            cleaned_item = {
                "id": row_dict["id"],
                "tipo": tipo,
                "descripcion": descripcion,
                "monto": float(monto),
                "fecha": fecha,
                "creado_en": creado_en,
                "validado_por": "etl_pipeline",
                "tabla_destino": tabla_destino,
            }
            cleaned.append(cleaned_item)

        # Backup cleaned
        if cleaned:
            with open(f"backups/cleaned_{now}.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=cleaned[0].keys())
                writer.writeheader()
                writer.writerows(cleaned)

        # 2. CARGAR cleaned_data (reemplaza todo)
        conn.execute(text("TRUNCATE TABLE cleaned_data"))
        for item in cleaned:
            conn.execute(text("""
                INSERT INTO cleaned_data (id, tipo, descripcion, monto, fecha, creado_en, validado_por, tabla_destino)
                VALUES (:id, :tipo, :descripcion, :monto, :fecha, :creado_en, :validado_por, :tabla_destino)
            """), item)

        # 3. Generar registros finales según tabla_destino
        for item in cleaned:
            raw_id = item["id"]
            tipo = item["tipo"]
            desc = item["descripcion"]
            monto = item["monto"]
            fecha = item["fecha"]

            # extraer nombre antes de " - " como cliente/proveedor
            partes = desc.split(" - ", 1)
            nombre = partes[0] if partes else ""

            if tipo == "ingreso":
                # factura de venta
                existing = conn.execute(
                    text("SELECT id FROM facturas_venta WHERE raw_id = :rid"), {"rid": raw_id}
                ).fetchone()
                if not existing:
                    conn.execute(text("""
                        INSERT INTO facturas_venta (cliente, descripcion, monto, fecha, raw_id)
                        VALUES (:cliente, :descripcion, :monto, :fecha, :raw_id)
                    """), {
                        "cliente": nombre,
                        "descripcion": desc,
                        "monto": monto,
                        "fecha": fecha.date() if hasattr(fecha, "date") else fecha,
                        "raw_id": raw_id
                    })
            elif tipo == "gasto":
                existing = conn.execute(
                    text("SELECT id FROM facturas_compra WHERE raw_id = :rid"), {"rid": raw_id}
                ).fetchone()
                if not existing:
                    conn.execute(text("""
                        INSERT INTO facturas_compra (proveedor, descripcion, monto, fecha, raw_id)
                        VALUES (:proveedor, :descripcion, :monto, :fecha, :raw_id)
                    """), {
                        "proveedor": nombre,
                        "descripcion": desc,
                        "monto": monto,
                        "fecha": fecha.date() if hasattr(fecha, "date") else fecha,
                        "raw_id": raw_id
                    })
            elif tipo == "orden_compra":
                # orden de compra
                existing = conn.execute(
                    text("SELECT id FROM ordenes_compra WHERE descripcion = :desc AND monto = :monto AND fecha = :fecha"),
                    {"desc": desc, "monto": monto, "fecha": fecha.date() if hasattr(fecha, "date") else fecha}
                ).fetchone()
                if not existing:
                    conn.execute(text("""
                        INSERT INTO ordenes_compra (proveedor, descripcion, monto, fecha)
                        VALUES (:proveedor, :descripcion, :monto, :fecha)
                    """), {
                        "proveedor": nombre,
                        "descripcion": desc,
                        "monto": monto,
                        "fecha": fecha.date() if hasattr(fecha, "date") else fecha,
                    })

        # 4. Log
        log_data = {
            "timestamp": now,
            "registros_raw": len(rows),
            "registros_limpios": len(cleaned),
            "raw_backup": f"backups/raw_{now}.csv",
            "cleaned_backup": f"backups/cleaned_{now}.csv",
        }
        with open(f"logs/log_{now}.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4)

        print(f"ETL completado — {len(cleaned)} registros limpios cargados.")
        return log_data

if __name__ == "__main__":
    run_etl()
