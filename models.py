from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, Date
from database import Base
from datetime import datetime

# Datos en bruto para el ETL
class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(DateTime)
    creado_en = Column(DateTime, default=datetime.utcnow)

# Datos limpios del ETL
class CleanedData(Base):
    __tablename__ = "cleaned_data"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(DateTime)
    creado_en = Column(DateTime)
    validado_por = Column(String(100))

# Facturas de venta (ingresos)
class FacturaVenta(Base):
    __tablename__ = "facturas_venta"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String(100))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)

# Facturas de compra (gastos)
class FacturaCompra(Base):
    __tablename__ = "facturas_compra"

    id = Column(Integer, primary_key=True, index=True)
    proveedor = Column(String(100))
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    creado_en = Column(DateTime, default=datetime.utcnow)