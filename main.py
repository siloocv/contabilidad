from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, model_validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any, Literal

import models
from database import SessionLocal, engine
from etl_pipeline import run_etl
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

# Crear todas las tablas
models.Base.metadata.create_all(bind=engine)

# App y CORS
app = FastAPI(title="Pipeline contabilidad completo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción restringir
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Serialización genérica
def serialize_row(obj: Any) -> dict:
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, Decimal):
            d[col.name] = float(val)
        elif hasattr(val, "isoformat"):
            d[col.name] = val.isoformat()
        else:
            d[col.name] = val
    return d

# ------------------------------
# Schemas Pydantic
# ------------------------------
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
    frecuencia: str

class PagoRecibidoIn(BaseModel):
    factura_venta_id: int
    monto: float
    fecha: date

    @model_validator(mode="after")
    def verifica_factura(cls, v):
        # Puede agregar validación adicional aquí
        return v

class PagoProveedorIn(BaseModel):
    factura_compra_id: Optional[int] = None
    orden_compra_id: Optional[int] = None
    monto: float
    fecha: date

    @model_validator(mode="after")
    def al_menos_uno(cls, v):
        if not v.factura_compra_id and not v.orden_compra_id:
            raise ValueError("Se requiere factura_compra_id o orden_compra_id")
        return v

class ClienteIn(BaseModel):
    nombre: str
    identificacion: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class ProductoIn(BaseModel):
    nombre: str
    sku: Optional[str] = None
    precio_unitario: float
    descripcion: Optional[str] = None

class FacturaItemIn(BaseModel):
    factura_tipo: Literal['venta', 'compra']
    factura_venta_id: Optional[int] = None
    factura_compra_id: Optional[int] = None
    producto_id: int
    cantidad: int
    precio: float

# ------------------------------
# Endpoints: RAW
# ------------------------------
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
        raise HTTPException(status_code=500, detail=f"Error guardando raw: {e}")

@app.get("/api/raw/")
def listar_raw(db: Session = Depends(get_db)):
    raws = db.query(models.RawData).order_by(models.RawData.id.desc()).all()
    return [serialize_row(r) for r in raws]

# ------------------------------
# Endpoints: Factura de Venta
# ------------------------------
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
        db.add(nueva); db.commit(); db.refresh(nueva)
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

# ------------------------------
# Endpoints: Factura de Compra
# ------------------------------
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
        db.add(nueva); db.commit(); db.refresh(nueva)
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

# ------------------------------
# Endpoints: Facturas Recurrentes
# ------------------------------
@app.post("/api/facturas/recurrentes/template/", status_code=201)
def crear_template_fr(t: RecurringTemplateIn, db: Session = Depends(get_db)):
    nueva = models.FacturaRecurrenteTemplate(
        cliente=t.cliente,
        descripcion=t.descripcion,
        monto=Decimal(str(t.monto)),
        frecuencia=t.frecuencia,
        siguiente_generacion=datetime.utcnow(),
    )
    db.add(nueva); db.commit(); db.refresh(nueva)
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
        {"id": t.id, "cliente": t.cliente, "descripcion": t.descripcion,
         "monto": float(t.monto), "frecuencia": t.frecuencia,
         "siguiente_generacion": t.siguiente_generacion.isoformat()}
        for t in temps
    ]

# ------------------------------
# Endpoint: Pagos Recibidos
# ------------------------------
@app.post("/api/pagos/recibidos/", status_code=201)
def crear_pago_recibido(p: PagoRecibidoIn, db: Session = Depends(get_db)):
    # Validar existencia de factura_venta_id
    if not db.query(models.FacturaVenta).get(p.factura_venta_id):
        raise HTTPException(status_code=422, detail="Factura de venta no existe")
    pago = models.PagoRecibido(
        factura_venta_id=p.factura_venta_id,
        monto=Decimal(str(p.monto)),
        fecha=p.fecha,
        raw_id=None,
    )
    try:
        db.add(pago); db.commit(); db.refresh(pago)
        return serialize_row(pago)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al registrar pago recibido")

@app.get("/api/pagos/recibidos/")
def listar_pagos_recibidos(db: Session = Depends(get_db)):
    pagos = db.query(models.PagoRecibido).order_by(models.PagoRecibido.id.desc()).all()
    return [serialize_row(p) for p in pagos]

# ------------------------------
# Endpoint: Órdenes de Compra
# ------------------------------
@app.get("/api/ordenes/compra/")
def listar_ordenes_compra(db: Session = Depends(get_db)):
    ordenes = db.query(models.OrdenesCompra).order_by(models.OrdenesCompra.id.desc()).all()
    return [serialize_row(o) for o in ordenes]

# ------------------------------
# Endpoint: Pagos a Proveedor
# ------------------------------
@app.post("/api/pagos/proveedor/", status_code=201)
def crear_pago_proveedor(p: PagoProveedorIn, db: Session = Depends(get_db)):
    # Validar existencia de factura_compra_id o orden_compra_id
    if p.factura_compra_id and not db.query(models.FacturaCompra).get(p.factura_compra_id):
        raise HTTPException(status_code=422, detail="Factura de compra no existe")
    if p.orden_compra_id and not db.query(models.OrdenesCompra).get(p.orden_compra_id):
        raise HTTPException(status_code=422, detail="Orden de compra no existe")
    pago = models.PagoProveedor(
        factura_compra_id=p.factura_compra_id,
        orden_compra_id=p.orden_compra_id,
        monto=Decimal(str(p.monto)),
        fecha=p.fecha,
        raw_id=None,
    )
    try:
        db.add(pago); db.commit(); db.refresh(pago)
        return serialize_row(pago)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al registrar pago a proveedor")

@app.get("/api/pagos/proveedor/")
def listar_pagos_proveedor(db: Session = Depends(get_db)):
    pagos = db.query(models.PagoProveedor).order_by(models.PagoProveedor.id.desc()).all()
    return [serialize_row(p) for p in pagos]

# ------------------------------
# Endpoints: Clientes, Productos, Items
# ------------------------------
@app.post("/api/clientes/", status_code=201)
def crear_cliente(c: ClienteIn, db: Session = Depends(get_db)):
    nuevo = models.Cliente(**c.dict())
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    return serialize_row(nuevo)

@app.get("/api/clientes/")
def listar_clientes(db: Session = Depends(get_db)):
    return [serialize_row(x) for x in db.query(models.Cliente).all()]

@app.post("/api/productos/", status_code=201)
def crear_producto(p: ProductoIn, db: Session = Depends(get_db)):
    nuevo = models.Producto(**p.dict())
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    return serialize_row(nuevo)

@app.get("/api/productos/")
def listar_productos(db: Session = Depends(get_db)):
    return [serialize_row(x) for x in db.query(models.Producto).all()]

@app.post("/api/factura-items/", status_code=201)
def crear_item(item: FacturaItemIn, db: Session = Depends(get_db)):
    if item.factura_tipo == 'venta' and not item.factura_venta_id:
        raise HTTPException(status_code=422, detail="Se requiere factura_venta_id para tipo venta")
    if item.factura_tipo == 'compra' and not item.factura_compra_id:
        raise HTTPException(status_code=422, detail="Se requiere factura_compra_id para tipo compra")
    nuevo = models.FacturaItem(
        factura_tipo=item.factura_tipo,
        factura_venta_id=item.factura_venta_id,
        factura_compra_id=item.factura_compra_id,
        producto_id=item.producto_id,
        cantidad=item.cantidad,
        precio=Decimal(str(item.precio))
    )
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    return serialize_row(nuevo)

@app.get("/api/factura-items/")
def listar_items(db: Session = Depends(get_db)):
    return [serialize_row(x) for x in db.query(models.FacturaItem).all()]

# ------------------------------
# Endpoints: Pipeline y Health
# ------------------------------
@app.post("/api/pipeline/run")
def ejecutar_pipeline_endpoint():
    resumen = run_etl()
    return resumen

@app.get("/api/cleaned/")
def obtener_cleaned(db: Session = Depends(get_db)):
    rows = db.query(models.CleanedData).order_by(models.CleanedData.id.desc()).all()
    return [serialize_row(r) for r in rows]

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
