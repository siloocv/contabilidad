from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, model_validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any

from sqlalchemy.exc import IntegrityError

import models
from database import SessionLocal, engine
from etl_pipeline import run_etl

from fastapi.middleware.cors import CORSMiddleware

# App y CORS
app = FastAPI(title="Pipeline contabilidad completo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción restringir
    allow_methods=["*"],
    allow_headers=["*"],
)

# Asegurar que las tablas existen (si no usás migraciones)
models.RawData.metadata.create_all(bind=engine)
models.CleanedData.metadata.create_all(bind=engine)
models.FacturaVenta.metadata.create_all(bind=engine)
models.FacturaCompra.metadata.create_all(bind=engine)
models.OrdenesCompra.metadata.create_all(bind=engine)
models.PagoRecibido.metadata.create_all(bind=engine)
models.PagoProveedor.metadata.create_all(bind=engine)
models.FacturaRecurrenteTemplate.metadata.create_all(bind=engine)
models.FacturaRecurrenteInstance.metadata.create_all(bind=engine)

# Dependencia de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas
class RawEntryIn(BaseModel):
    tipo: str
    descripcion: str
    monto: float
    fecha: date

    @field_validator("tipo")
    def tipo_valido(cls, v):
        if v.lower() not in (
            "ingreso",
            "gasto",
            "factura_recurrente",
            "pago_recibido",
            "pago_proveedor",
            "orden_compra",
        ):
            raise ValueError("tipo inválido")
        return v.lower()

class FacturaVentaIn(BaseModel):
    cliente: str
    descripcion: str
    monto: float
    fecha: date
    raw_id: Optional[int] = None

class FacturaCompraIn(BaseModel):
    proveedor: str
    descripcion: str
    monto: float
    fecha: date
    raw_id: Optional[int] = None

class RecurringTemplateIn(BaseModel):
    cliente: str
    descripcion: str
    monto: float
    frecuencia: str  # "mensual", etc.

class PagoRecibidoIn(BaseModel):
    factura_venta_id: int
    monto: float
    fecha: date

class PagoProveedorIn(BaseModel):
    factura_compra_id: Optional[int] = None
    orden_compra_id: Optional[int] = None
    monto: float
    fecha: date

    @model_validator(mode="after")
    def al_menos_uno(self):
        if not self.factura_compra_id and not self.orden_compra_id:
            raise ValueError("Se requiere al menos factura_compra_id o orden_compra_id")
        return self

# Serialización genérica
def serialize_row(obj: Any) -> dict:
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, Decimal):
            d[col.name] = float(val)
        elif isinstance(val, (datetime, date)):
            d[col.name] = val.isoformat()
        else:
            d[col.name] = val
    return d

# Endpoints

# RAW
@app.post("/api/raw/", status_code=201)
def crear_raw(entry: RawEntryIn, db: Session = Depends(get_db)):
    from crud import crear_entrada

    payload = {
        "tipo": entry.tipo,
        "descripcion": entry.descripcion,
        "monto": entry.monto,
        "fecha": entry.fecha,
    }
    try:
        nueva = crear_entrada(db, payload)
        return serialize_row(nueva)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando raw: {str(e)}")

@app.get("/api/raw/")
def listar_raw(db: Session = Depends(get_db)):
    raws = db.query(models.RawData).order_by(models.RawData.id.desc()).all()
    return [serialize_row(r) for r in raws]

# Factura de venta
@app.post("/api/facturas/venta/", status_code=201)
def crear_factura_venta(fv: FacturaVentaIn, db: Session = Depends(get_db)):
    nueva = models.FacturaVenta(
        cliente=fv.cliente,
        descripcion=fv.descripcion,
        monto=Decimal(str(fv.monto)),
        fecha=fv.fecha,
        raw_id=fv.raw_id,
    )
    try:
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return serialize_row(nueva)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Factura de venta ya existe por raw_id")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturas/venta/")
def listar_facturas_venta(db: Session = Depends(get_db)):
    fv = db.query(models.FacturaVenta).order_by(models.FacturaVenta.id.desc()).all()
    return [serialize_row(x) for x in fv]

# Factura de compra
@app.post("/api/facturas/compra/", status_code=201)
def crear_factura_compra(fc: FacturaCompraIn, db: Session = Depends(get_db)):
    nueva = models.FacturaCompra(
        proveedor=fc.proveedor,
        descripcion=fc.descripcion,
        monto=Decimal(str(fc.monto)),
        fecha=fc.fecha,
        raw_id=fc.raw_id,
    )
    try:
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return serialize_row(nueva)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Factura de compra ya existe por raw_id")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturas/compra/")
def listar_facturas_compra(db: Session = Depends(get_db)):
    fc = db.query(models.FacturaCompra).order_by(models.FacturaCompra.id.desc()).all()
    return [serialize_row(x) for x in fc]

# Facturas recurrentes
@app.post("/api/facturas/recurrentes/template/", status_code=201)
def crear_template_fr(t: RecurringTemplateIn, db: Session = Depends(get_db)):
    nueva = models.FacturaRecurrenteTemplate(
        cliente=t.cliente,
        descripcion=t.descripcion,
        monto=Decimal(str(t.monto)),
        frecuencia=t.frecuencia,
        siguiente_generacion=datetime.utcnow(),
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {
        "id": nueva.id,
        "cliente": nueva.cliente,
        "descripcion": nueva.descripcion,
        "monto": float(nueva.monto),
        "frecuencia": nueva.frecuencia,
        "siguiente_generacion": nueva.siguiente_generacion.isoformat(),
    }

@app.get("/api/facturas/recurrentes/template/")
def listar_templates_fr(db: Session = Depends(get_db)):
    temps = db.query(models.FacturaRecurrenteTemplate).order_by(models.FacturaRecurrenteTemplate.id.desc()).all()
    return [
        {
            "id": t.id,
            "cliente": t.cliente,
            "descripcion": t.descripcion,
            "monto": float(t.monto),
            "frecuencia": t.frecuencia,
            "siguiente_generacion": t.siguiente_generacion.isoformat(),
        }
        for t in temps
    ]

# Pagos recibidos
@app.post("/api/pagos/recibidos/", status_code=201)
def crear_pago_recibido(p: PagoRecibidoIn, db: Session = Depends(get_db)):
    pago = models.PagoRecibido(
        factura_venta_id=p.factura_venta_id,
        monto=Decimal(str(p.monto)),
        fecha=p.fecha,
        raw_id=None,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return {
        "id": pago.id,
        "factura_venta_id": pago.factura_venta_id,
        "monto": float(pago.monto),
        "fecha": pago.fecha.isoformat(),
    }

# Pagos a proveedor
@app.post("/api/pagos/proveedor/", status_code=201)
def crear_pago_proveedor(p: PagoProveedorIn, db: Session = Depends(get_db)):
    if not p.factura_compra_id and not p.orden_compra_id:
        raise HTTPException(status_code=422, detail="Debe proporcionar factura_compra_id o orden_compra_id")
    pago = models.PagoProveedor(
        factura_compra_id=p.factura_compra_id,
        orden_compra_id=p.orden_compra_id,
        monto=Decimal(str(p.monto)),
        fecha=p.fecha,
        raw_id=None,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return {
        "id": pago.id,
        "factura_compra_id": pago.factura_compra_id,
        "orden_compra_id": pago.orden_compra_id,
        "monto": float(pago.monto),
        "fecha": pago.fecha.isoformat(),
    }

# Pipeline y cleaned
@app.post("/api/pipeline/run")
def ejecutar_pipeline_endpoint():
    resumen = run_etl()
    return resumen

@app.get("/api/cleaned/")
def obtener_cleaned(db: Session = Depends(get_db)):
    rows = db.query(models.CleanedData).order_by(models.CleanedData.id.desc()).all()
    return [serialize_row(r) for r in rows]

# Health
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
