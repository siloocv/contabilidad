from sqlalchemy.orm import Session
from models import RawData

def determinar_tabla_destino(tipo: str) -> str | None:
    tipo = (tipo or "").lower()
    if tipo == "ingreso":
        return "facturas_venta"
    elif tipo == "gasto":
        return "facturas_compra"
    elif tipo == "factura_recurrente":
        return "facturas_recurrentes_template"
    elif tipo == "pago_recibido":
        return "pagos_recibidos"
    elif tipo == "pago_proveedor":
        return "pagos_proveedor"
    elif tipo == "orden_compra":
        return "ordenes_compra"
    return None

def crear_entrada(db: Session, entrada_data: dict):
    entrada_data = entrada_data.copy()
    entrada_data["tipo"] = entrada_data.get("tipo", "").lower()
    entrada_data["descripcion"] = entrada_data.get("descripcion", "").strip()
    entrada_data["tabla_destino"] = determinar_tabla_destino(entrada_data.get("tipo", ""))
    nueva = RawData(**entrada_data)
    try:
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return nueva
    except Exception:
        db.rollback()
        raise
