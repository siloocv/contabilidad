from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    DECIMAL,
    Date,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(DateTime)
    creado_en = Column(DateTime, default=datetime.utcnow)
    tabla_destino = Column(String(100))


class CleanedData(Base):
    __tablename__ = "cleaned_data"

    id = Column(Integer, primary_key=True, index=True)  # reutiliza id de raw
    tipo = Column(String(50))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(DateTime)
    creado_en = Column(DateTime)
    validado_por = Column(String(100))
    tabla_destino = Column(String(100))


class FacturaVenta(Base):
    __tablename__ = "facturas_venta"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String(100))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)
    raw_id = Column(Integer)
    __table_args__ = (UniqueConstraint("raw_id", name="uq_factura_venta_raw"),)


class FacturaCompra(Base):
    __tablename__ = "facturas_compra"

    id = Column(Integer, primary_key=True, index=True)
    proveedor = Column(String(100))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)
    raw_id = Column(Integer)
    __table_args__ = (UniqueConstraint("raw_id", name="uq_factura_compra_raw"),)


class OrdenesCompra(Base):
    __tablename__ = "ordenes_compra"

    id = Column(Integer, primary_key=True, index=True)
    proveedor = Column(String(100))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)


class PagoRecibido(Base):
    __tablename__ = "pagos_recibidos"

    id = Column(Integer, primary_key=True, index=True)
    factura_venta_id = Column(Integer, ForeignKey("facturas_venta.id"))
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)
    raw_id = Column(Integer)
    factura_venta = relationship("FacturaVenta")


class PagoProveedor(Base):
    __tablename__ = "pagos_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    factura_compra_id = Column(Integer, ForeignKey("facturas_compra.id"), nullable=True)
    orden_compra_id = Column(Integer, ForeignKey("ordenes_compra.id"), nullable=True)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)
    raw_id = Column(Integer)
    factura_compra = relationship("FacturaCompra")
    orden_compra = relationship("OrdenesCompra")


class FacturaRecurrenteTemplate(Base):
    __tablename__ = "facturas_recurrentes_template"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String(100))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    frecuencia = Column(String(50))
    siguiente_generacion = Column(DateTime)


class FacturaRecurrenteInstance(Base):
    __tablename__ = "facturas_recurrentes_instance"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("facturas_recurrentes_template.id"))
    cliente = Column(String(100))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)
    raw_id = Column(Integer)
    template = relationship("FacturaRecurrenteTemplate")
