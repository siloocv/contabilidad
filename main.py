from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, model_validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any, Literal
import json

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

class ProveedorIn(BaseModel):
    nombre: str
    identificacion: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_telefono: Optional[str] = None

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

@app.get("/api/raw/{id}/")
def obtener_raw(id: int, db: Session = Depends(get_db)):
    item = db.query(models.RawData).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/raw/{id}/")
def actualizar_raw(id: int, entry: RawEntryIn, db: Session = Depends(get_db)):
    item = db.query(models.RawData).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.tipo = entry.tipo
    item.descripcion = entry.descripcion
    item.monto = entry.monto
    item.fecha = entry.fecha
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/raw/{id}/")
def eliminar_raw(id: int, db: Session = Depends(get_db)):
    item = db.query(models.RawData).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

# ------------------------------
# Endpoints: Factura de Venta
# ------------------------------
@app.post("/api/facturas/venta/", status_code=201)
def crear_factura_venta(fv: FacturaVentaIn, db: Session = Depends(get_db)):
    # Primero guardar en raw_data
    raw_entry = models.RawData(
        tipo="ingreso",
        descripcion=f"{fv.cliente} - {fv.descripcion}",
        monto=Decimal(str(fv.monto)),
        fecha=fv.fecha,
        tabla_destino="facturas_venta"
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Datos registrados en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "factura_venta"
    }

@app.get("/api/facturas/venta/")
def listar_facturas_venta(db: Session = Depends(get_db)):
    fv = db.query(models.FacturaVenta).order_by(models.FacturaVenta.id.desc()).all()
    return [serialize_row(x) for x in fv]

@app.get("/api/facturas/venta/{id}/")
def obtener_factura_venta(id: int, db: Session = Depends(get_db)):
    item = db.query(models.FacturaVenta).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/facturas/venta/{id}/")
def actualizar_factura_venta(id: int, fv: FacturaVentaIn, db: Session = Depends(get_db)):
    item = db.query(models.FacturaVenta).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.cliente = fv.cliente
    item.descripcion = fv.descripcion
    item.monto = Decimal(str(fv.monto))
    item.fecha = fv.fecha
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/facturas/venta/{id}/")
def eliminar_factura_venta(id: int, db: Session = Depends(get_db)):
    item = db.query(models.FacturaVenta).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

# ------------------------------
# Endpoints: Factura de Compra
# ------------------------------
@app.post("/api/facturas/compra/", status_code=201)
def crear_factura_compra(fc: FacturaCompraIn, db: Session = Depends(get_db)):
    # Primero guardar en raw_data
    raw_entry = models.RawData(
        tipo="gasto",
        descripcion=f"{fc.proveedor} - {fc.descripcion}",
        monto=Decimal(str(fc.monto)),
        fecha=fc.fecha,
        tabla_destino="facturas_compra"
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Datos registrados en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "factura_compra"
    }

@app.get("/api/facturas/compra/")
def listar_facturas_compra(db: Session = Depends(get_db)):
    fc = db.query(models.FacturaCompra).order_by(models.FacturaCompra.id.desc()).all()
    return [serialize_row(x) for x in fc]

@app.get("/api/facturas/compra/{id}/")
def obtener_factura_compra(id: int, db: Session = Depends(get_db)):
    item = db.query(models.FacturaCompra).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/facturas/compra/{id}/")
def actualizar_factura_compra(id: int, fc: FacturaCompraIn, db: Session = Depends(get_db)):
    item = db.query(models.FacturaCompra).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.proveedor = fc.proveedor
    item.descripcion = fc.descripcion
    item.monto = Decimal(str(fc.monto))
    item.fecha = fc.fecha
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/facturas/compra/{id}/")
def eliminar_factura_compra(id: int, db: Session = Depends(get_db)):
    item = db.query(models.FacturaCompra).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

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

@app.get("/api/facturas/recurrentes/template/{id}/")
def obtener_template_fr(id: int, db: Session = Depends(get_db)):
    item = db.query(models.FacturaRecurrenteTemplate).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return {
        "id": item.id, "cliente": item.cliente, "descripcion": item.descripcion,
        "monto": float(item.monto), "frecuencia": item.frecuencia,
        "siguiente_generacion": item.siguiente_generacion.isoformat()
    }

@app.put("/api/facturas/recurrentes/template/{id}/")
def actualizar_template_fr(id: int, t: RecurringTemplateIn, db: Session = Depends(get_db)):
    item = db.query(models.FacturaRecurrenteTemplate).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.cliente = t.cliente
    item.descripcion = t.descripcion
    item.monto = Decimal(str(t.monto))
    item.frecuencia = t.frecuencia
    db.commit()
    db.refresh(item)
    return {
        "id": item.id, "cliente": item.cliente, "descripcion": item.descripcion,
        "monto": float(item.monto), "frecuencia": item.frecuencia,
        "siguiente_generacion": item.siguiente_generacion.isoformat()
    }

@app.delete("/api/facturas/recurrentes/template/{id}/")
def eliminar_template_fr(id: int, db: Session = Depends(get_db)):
    item = db.query(models.FacturaRecurrenteTemplate).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

# ------------------------------
# Endpoint: Pagos Recibidos
# ------------------------------
@app.post("/api/pagos/recibidos/", status_code=201)
def crear_pago_recibido(p: PagoRecibidoIn, db: Session = Depends(get_db)):
    # Validar existencia de factura_venta_id
    if not db.query(models.FacturaVenta).get(p.factura_venta_id):
        raise HTTPException(status_code=422, detail="Factura de venta no existe")
    
    # Primero guardar en raw_data
    raw_entry = models.RawData(
        tipo="pago_recibido",
        descripcion=f"{p.factura_venta_id} - Pago recibido",
        monto=Decimal(str(p.monto)),
        fecha=p.fecha,
        tabla_destino="pagos_recibidos"
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Datos registrados en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "pago_recibido"
    }

@app.get("/api/pagos/recibidos/")
def listar_pagos_recibidos(db: Session = Depends(get_db)):
    pagos = db.query(models.PagoRecibido).order_by(models.PagoRecibido.id.desc()).all()
    return [serialize_row(p) for p in pagos]

@app.get("/api/pagos/recibidos/{id}/")
def obtener_pago_recibido(id: int, db: Session = Depends(get_db)):
    item = db.query(models.PagoRecibido).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/pagos/recibidos/{id}/")
def actualizar_pago_recibido(id: int, p: PagoRecibidoIn, db: Session = Depends(get_db)):
    item = db.query(models.PagoRecibido).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    if not db.query(models.FacturaVenta).get(p.factura_venta_id):
        raise HTTPException(status_code=422, detail="Factura de venta no existe")
    item.factura_venta_id = p.factura_venta_id
    item.monto = Decimal(str(p.monto))
    item.fecha = p.fecha
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/pagos/recibidos/{id}/")
def eliminar_pago_recibido(id: int, db: Session = Depends(get_db)):
    item = db.query(models.PagoRecibido).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

# ------------------------------
# Endpoint: Órdenes de Compra
# ------------------------------
@app.get("/api/ordenes/compra/")
def listar_ordenes_compra(db: Session = Depends(get_db)):
    ordenes = db.query(models.OrdenesCompra).order_by(models.OrdenesCompra.id.desc()).all()
    return [serialize_row(o) for o in ordenes]

@app.post("/api/ordenes/compra/", status_code=201)
def crear_orden_compra(oc: FacturaCompraIn, db: Session = Depends(get_db)):
    # Primero guardar en raw_data
    raw_entry = models.RawData(
        tipo="orden_compra",
        descripcion=f"{oc.proveedor} - {oc.descripcion}",
        monto=Decimal(str(oc.monto)),
        fecha=oc.fecha,
        tabla_destino="ordenes_compra"
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Datos registrados en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "orden_compra"
    }

@app.get("/api/ordenes/compra/{id}/")
def obtener_orden_compra(id: int, db: Session = Depends(get_db)):
    item = db.query(models.OrdenesCompra).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/ordenes/compra/{id}/")
def actualizar_orden_compra(id: int, oc: FacturaCompraIn, db: Session = Depends(get_db)):
    item = db.query(models.OrdenesCompra).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.proveedor = oc.proveedor
    item.descripcion = oc.descripcion
    item.monto = Decimal(str(oc.monto))
    item.fecha = oc.fecha
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/ordenes/compra/{id}/")
def eliminar_orden_compra(id: int, db: Session = Depends(get_db)):
    item = db.query(models.OrdenesCompra).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

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
    
    # Primero guardar en raw_data
    ref_id = p.factura_compra_id if p.factura_compra_id else p.orden_compra_id
    ref_type = "FC" if p.factura_compra_id else "OC"
    raw_entry = models.RawData(
        tipo="pago_proveedor",
        descripcion=f"{ref_type}-{ref_id} - Pago a proveedor",
        monto=Decimal(str(p.monto)),
        fecha=p.fecha,
        tabla_destino="pagos_proveedor"
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Datos registrados en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "pago_proveedor"
    }

@app.get("/api/pagos/proveedor/")
def listar_pagos_proveedor(db: Session = Depends(get_db)):
    pagos = db.query(models.PagoProveedor).order_by(models.PagoProveedor.id.desc()).all()
    return [serialize_row(p) for p in pagos]

@app.get("/api/pagos/proveedor/{id}/")
def obtener_pago_proveedor(id: int, db: Session = Depends(get_db)):
    item = db.query(models.PagoProveedor).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/pagos/proveedor/{id}/")
def actualizar_pago_proveedor(id: int, p: PagoProveedorIn, db: Session = Depends(get_db)):
    item = db.query(models.PagoProveedor).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    if p.factura_compra_id and not db.query(models.FacturaCompra).get(p.factura_compra_id):
        raise HTTPException(status_code=422, detail="Factura de compra no existe")
    if p.orden_compra_id and not db.query(models.OrdenesCompra).get(p.orden_compra_id):
        raise HTTPException(status_code=422, detail="Orden de compra no existe")
    item.factura_compra_id = p.factura_compra_id
    item.orden_compra_id = p.orden_compra_id
    item.monto = Decimal(str(p.monto))
    item.fecha = p.fecha
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/pagos/proveedor/{id}/")
def eliminar_pago_proveedor(id: int, db: Session = Depends(get_db)):
    item = db.query(models.PagoProveedor).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

# ------------------------------
# Endpoints: Clientes, Productos, Items
# ------------------------------
@app.post("/api/clientes/", status_code=201)
def crear_cliente(c: ClienteIn, db: Session = Depends(get_db)):
    # Primero guardar en raw_data
    raw_entry = models.RawData(
        tipo="cliente",
        descripcion=f"Cliente: {c.nombre}",
        monto=0,  # Los clientes no tienen monto asociado
        fecha=datetime.now().date(),
        tabla_destino="clientes",
        metadata_json=json.dumps(c.dict())
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Cliente registrado en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "cliente",
        "nombre": c.nombre
    }

@app.get("/api/clientes/")
def listar_clientes(db: Session = Depends(get_db)):
    return [serialize_row(x) for x in db.query(models.Cliente).all()]

@app.get("/api/clientes/{id}/")
def obtener_cliente(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Cliente).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/clientes/{id}/")
def actualizar_cliente(id: int, c: ClienteIn, db: Session = Depends(get_db)):
    item = db.query(models.Cliente).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.nombre = c.nombre
    item.identificacion = c.identificacion
    item.correo = c.correo
    item.telefono = c.telefono
    item.direccion = c.direccion
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/clientes/{id}/")
def eliminar_cliente(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Cliente).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

@app.post("/api/proveedores/", status_code=201)
def crear_proveedor(p: ProveedorIn, db: Session = Depends(get_db)):
    # Primero guardar en raw_data
    raw_entry = models.RawData(
        tipo="proveedor",
        descripcion=f"Proveedor: {p.nombre}",
        monto=0,  # Los proveedores no tienen monto asociado
        fecha=datetime.now().date(),
        tabla_destino="proveedores",
        metadata_json=json.dumps(p.dict())
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Proveedor registrado en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "proveedor",
        "nombre": p.nombre
    }

@app.get("/api/proveedores/")
def listar_proveedores(db: Session = Depends(get_db)):
    return [serialize_row(x) for x in db.query(models.Proveedor).all()]

@app.get("/api/proveedores/{id}/")
def obtener_proveedor(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Proveedor).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/proveedores/{id}/")
def actualizar_proveedor(id: int, p: ProveedorIn, db: Session = Depends(get_db)):
    item = db.query(models.Proveedor).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.nombre = p.nombre
    item.identificacion = p.identificacion
    item.correo = p.correo
    item.telefono = p.telefono
    item.direccion = p.direccion
    item.contacto_nombre = p.contacto_nombre
    item.contacto_telefono = p.contacto_telefono
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/proveedores/{id}/")
def eliminar_proveedor(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Proveedor).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

@app.post("/api/productos/", status_code=201)
def crear_producto(p: ProductoIn, db: Session = Depends(get_db)):
    # Primero guardar en raw_data
    raw_entry = models.RawData(
        tipo="producto",
        descripcion=f"Producto: {p.nombre} - SKU: {p.sku or 'N/A'}",
        monto=Decimal(str(p.precio_unitario)),
        fecha=datetime.now().date(),
        tabla_destino="productos",
        metadata_json=json.dumps({k: str(v) if v is not None else None for k, v in p.dict().items()})
    )
    db.add(raw_entry)
    db.commit()
    db.refresh(raw_entry)
    
    return {
        "message": "Producto registrado en cola de procesamiento",
        "raw_id": raw_entry.id,
        "status": "pending_etl",
        "tipo": "producto",
        "nombre": p.nombre
    }

@app.get("/api/productos/")
def listar_productos(db: Session = Depends(get_db)):
    return [serialize_row(x) for x in db.query(models.Producto).all()]

@app.get("/api/productos/{id}/")
def obtener_producto(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Producto).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    return serialize_row(item)

@app.put("/api/productos/{id}/")
def actualizar_producto(id: int, p: ProductoIn, db: Session = Depends(get_db)):
    item = db.query(models.Producto).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    item.nombre = p.nombre
    item.sku = p.sku
    item.precio_unitario = p.precio_unitario
    item.descripcion = p.descripcion
    db.commit()
    db.refresh(item)
    return serialize_row(item)

@app.delete("/api/productos/{id}/")
def eliminar_producto(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Producto).get(id)
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}

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

# ------------------------------
# Endpoints: Reportes
# ------------------------------
@app.get("/api/reportes/resumen/")
def obtener_resumen_financiero(db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    # Total ingresos (facturas de venta)
    total_ingresos = db.query(func.sum(models.FacturaVenta.monto)).scalar() or 0
    
    # Total gastos (facturas de compra + órdenes de compra)
    total_gastos_fc = db.query(func.sum(models.FacturaCompra.monto)).scalar() or 0
    total_gastos_oc = db.query(func.sum(models.OrdenesCompra.monto)).scalar() or 0
    total_gastos = total_gastos_fc + total_gastos_oc
    
    # Total pagos recibidos
    total_pagos_recibidos = db.query(func.sum(models.PagoRecibido.monto)).scalar() or 0
    
    # Total pagos a proveedores
    total_pagos_proveedor = db.query(func.sum(models.PagoProveedor.monto)).scalar() or 0
    
    # Cuentas por cobrar (facturas de venta - pagos recibidos)
    cuentas_por_cobrar = total_ingresos - total_pagos_recibidos
    
    # Cuentas por pagar (gastos - pagos a proveedores)
    cuentas_por_pagar = total_gastos - total_pagos_proveedor
    
    # Balance
    balance = total_ingresos - total_gastos
    
    return {
        "total_ingresos": float(total_ingresos),
        "total_gastos": float(total_gastos),
        "total_pagos_recibidos": float(total_pagos_recibidos),
        "total_pagos_proveedor": float(total_pagos_proveedor),
        "cuentas_por_cobrar": float(cuentas_por_cobrar),
        "cuentas_por_pagar": float(cuentas_por_pagar),
        "balance": float(balance),
        "fecha_reporte": datetime.utcnow().isoformat()
    }

@app.get("/api/reportes/facturas-pendientes/")
def obtener_facturas_pendientes(db: Session = Depends(get_db)):
    from sqlalchemy import func, and_
    
    # Facturas de venta con pagos pendientes
    subquery = db.query(
        models.PagoRecibido.factura_venta_id,
        func.sum(models.PagoRecibido.monto).label("total_pagado")
    ).group_by(models.PagoRecibido.factura_venta_id).subquery()
    
    facturas_venta_pendientes = db.query(
        models.FacturaVenta.id,
        models.FacturaVenta.cliente,
        models.FacturaVenta.monto,
        models.FacturaVenta.fecha,
        func.coalesce(subquery.c.total_pagado, 0).label("pagado")
    ).outerjoin(
        subquery, models.FacturaVenta.id == subquery.c.factura_venta_id
    ).filter(
        models.FacturaVenta.monto > func.coalesce(subquery.c.total_pagado, 0)
    ).all()
    
    # Facturas de compra con pagos pendientes
    subquery2 = db.query(
        models.PagoProveedor.factura_compra_id,
        func.sum(models.PagoProveedor.monto).label("total_pagado")
    ).group_by(models.PagoProveedor.factura_compra_id).subquery()
    
    facturas_compra_pendientes = db.query(
        models.FacturaCompra.id,
        models.FacturaCompra.proveedor,
        models.FacturaCompra.monto,
        models.FacturaCompra.fecha,
        func.coalesce(subquery2.c.total_pagado, 0).label("pagado")
    ).outerjoin(
        subquery2, models.FacturaCompra.id == subquery2.c.factura_compra_id
    ).filter(
        models.FacturaCompra.monto > func.coalesce(subquery2.c.total_pagado, 0)
    ).all()
    
    return {
        "facturas_venta_pendientes": [
            {
                "id": f.id,
                "cliente": f.cliente,
                "monto": float(f.monto),
                "pagado": float(f.pagado),
                "pendiente": float(f.monto - f.pagado),
                "fecha": f.fecha.isoformat() if hasattr(f.fecha, 'isoformat') else str(f.fecha)
            }
            for f in facturas_venta_pendientes
        ],
        "facturas_compra_pendientes": [
            {
                "id": f.id,
                "proveedor": f.proveedor,
                "monto": float(f.monto),
                "pagado": float(f.pagado),
                "pendiente": float(f.monto - f.pagado),
                "fecha": f.fecha.isoformat() if hasattr(f.fecha, 'isoformat') else str(f.fecha)
            }
            for f in facturas_compra_pendientes
        ]
    }

@app.get("/")
def root():
    return {
        "message": "Sistema de Contabilidad Web API",
        "docs": "http://127.0.0.1:8000/docs",
        "frontend": "Abrir frontend/index.html en el navegador",
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
