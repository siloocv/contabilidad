import csv
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from decimal import Decimal
import os

# URL de conexión
DATABASE_URL = "mysql+pymysql://sebas:YES@localhost:3306/contabilidad?charset=utf8mb4"
engine = create_engine(DATABASE_URL)

# Directorios de respaldo y logs
os.makedirs("backups", exist_ok=True)
os.makedirs("logs", exist_ok=True)

VALID_TYPES = {
    "ingreso": "facturas_venta",
    "gasto": "facturas_compra",
    "orden_compra": "ordenes_compra",
    "factura_recurrente": "facturas_recurrentes_template",
    "pago_recibido": "pagos_recibidos",
    "pago_proveedor": "pagos_proveedor",
}


def run_etl():
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    with engine.begin() as conn:
        # 1. EXTRAER raw_data completa
        result = conn.execute(text("SELECT * FROM raw_data"))
        rows = result.fetchall()
        columns = result.keys()

        # 2. RESPALDO raw_data
        raw_file = f"backups/raw_{now}.csv"
        with open(raw_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        # 3. PREPARAR cleaned items
        cleaned = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            tipo = (row_dict.get("tipo") or "").lower()
            if tipo not in VALID_TYPES:
                continue

            descripcion = (row_dict.get("descripcion") or "").strip()
            monto = row_dict.get("monto")
            fecha = row_dict.get("fecha")
            creado_en = row_dict.get("creado_en")
            if monto is None or not descripcion or not fecha:
                continue

            cleaned_item = {
                "id": row_dict["id"],
                "tipo": tipo,
                "descripcion": descripcion,
                "monto": float(monto),
                "fecha": fecha,
                "creado_en": creado_en,
                "validado_por": "etl_pipeline",
                "tabla_destino": VALID_TYPES[tipo],
            }
            cleaned.append(cleaned_item)

        # 4. RESPALDO cleaned_data incremental
        if cleaned:
            clean_file = f"backups/cleaned_{now}.csv"
            with open(clean_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=cleaned[0].keys())
                writer.writeheader()
                writer.writerows(cleaned)

        # 5. INSERTAR/ACTUALIZAR cleaned_data sin borrar históricos
        for item in cleaned:
            conn.execute(text("""
                INSERT INTO cleaned_data (id, tipo, descripcion, monto, fecha, creado_en, validado_por, tabla_destino)
                VALUES (:id, :tipo, :descripcion, :monto, :fecha, :creado_en, :validado_por, :tabla_destino)
                ON DUPLICATE KEY UPDATE
                  descripcion=VALUES(descripcion),
                  monto=VALUES(monto),
                  fecha=VALUES(fecha),
                  creado_en=VALUES(creado_en),
                  validado_por=VALUES(validado_por),
                  tabla_destino=VALUES(tabla_destino)
            """), item)

        # 6. GENERAR registros finales según tipo de tabla
        for item in cleaned:
            raw_id = item["id"]
            tipo = item["tipo"]
            desc = item["descripcion"]
            monto = item["monto"]
            fecha = item["fecha"]

            # Extraer nombre (cliente o proveedor)
            nombre = desc.split(" - ", 1)[0]

            if tipo == "ingreso":
                exists = conn.execute(
                    text("SELECT id FROM facturas_venta WHERE raw_id = :rid"), {"rid": raw_id}
                ).fetchone()
                if not exists:
                    conn.execute(text("""
                        INSERT INTO facturas_venta (cliente, descripcion, monto, fecha, raw_id)
                        VALUES (:cliente, :descripcion, :monto, :fecha, :rid)
                    """), {
                        "cliente": nombre,
                        "descripcion": desc,
                        "monto": monto,
                        "fecha": fecha.date() if hasattr(fecha, "date") else fecha,
                        "rid": raw_id
                    })

            elif tipo == "gasto":
                exists = conn.execute(
                    text("SELECT id FROM facturas_compra WHERE raw_id = :rid"), {"rid": raw_id}
                ).fetchone()
                if not exists:
                    conn.execute(text("""
                        INSERT INTO facturas_compra (proveedor, descripcion, monto, fecha, raw_id)
                        VALUES (:proveedor, :descripcion, :monto, :fecha, :rid)
                    """), {
                        "proveedor": nombre,
                        "descripcion": desc,
                        "monto": monto,
                        "fecha": fecha.date() if hasattr(fecha, "date") else fecha,
                        "rid": raw_id
                    })

            elif tipo == "orden_compra":
                exists = conn.execute(
                    text("SELECT id FROM ordenes_compra WHERE descripcion = :desc AND monto = :monto AND fecha = :fecha"),
                    {"desc": desc, "monto": monto, "fecha": fecha.date() if hasattr(fecha, "date") else fecha}
                ).fetchone()
                if not exists:
                    conn.execute(text("""
                        INSERT INTO ordenes_compra (proveedor, descripcion, monto, fecha)
                        VALUES (:proveedor, :descripcion, :monto, :fecha)
                    """), {
                        "proveedor": nombre,
                        "descripcion": desc,
                        "monto": monto,
                        "fecha": fecha.date() if hasattr(fecha, "date") else fecha,
                    })

            elif tipo == "factura_recurrente":
                # Solo registramos plantilla; instancia es gestionada por scheduler
                exists = conn.execute(
                    text("SELECT id FROM facturas_recurrentes_template WHERE id = :rid"), {"rid": raw_id}
                ).fetchone()
                if not exists:
                    conn.execute(text("""
                        INSERT INTO facturas_recurrentes_template (cliente, descripcion, monto, frecuencia, siguiente_generacion)
                        VALUES (:cliente, :descripcion, :monto, :frecuencia, :siguiente)
                    """), {
                        "cliente": nombre,
                        "descripcion": desc,
                        "monto": monto,
                        "frecuencia": item.get("frecuencia", "mensual"),
                        "siguiente": datetime.utcnow()
                    })

            elif tipo == "pago_recibido":
                exists = conn.execute(
                    text("SELECT id FROM pagos_recibidos WHERE raw_id = :rid"), {"rid": raw_id}
                ).fetchone()
                if not exists:
                    # desc debe contener referencia de factura_venta_id como primer valor
                    factura_id = int(desc.split("-", 1)[0])
                    conn.execute(text("""
                        INSERT INTO pagos_recibidos (factura_venta_id, monto, fecha, raw_id)
                        VALUES (:fv, :monto, :fecha, :rid)
                    """), {"fv": factura_id, "monto": monto, "fecha": fecha, "rid": raw_id})

            elif tipo == "pago_proveedor":
                exists = conn.execute(
                    text("SELECT id FROM pagos_proveedor WHERE raw_id = :rid"), {"rid": raw_id}
                ).fetchone()
                if not exists:
                    parts = desc.split(" - ", 1)
                    # Asumir primero factura_compra o orden_compra
                    fk = int(parts[0])
                    conn.execute(text("""
                        INSERT INTO pagos_proveedor (factura_compra_id, orden_compra_id, monto, fecha, raw_id)
                        VALUES (:fc, NULL, :monto, :fecha, :rid)
                    """), {"fc": fk, "monto": monto, "fecha": fecha, "rid": raw_id})

        # 7. Registro de log
        log_data = {
            "timestamp": now,
            "total_raw": len(rows),
            "total_cleaned": len(cleaned),
            "raw_backup": raw_file,
            "cleaned_backup": clean_file if cleaned else None,
        }
        with open(f"logs/log_{now}.json", "w", encoding="utf-8") as lf:
            json.dump(log_data, lf, indent=2)

        print(f"ETL completado: {len(cleaned)} registros procesados.")
        return log_data


if __name__ == "__main__":
    run_etl()
