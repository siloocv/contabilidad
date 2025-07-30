from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, crud
import subprocess

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint: leer tabla cleaned_data
@app.get("/api/cleaned/")
def leer_datos_limpios(db: Session = Depends(get_db)):
    return db.query(models.CleanedData).all()

# Endpoint: crear datos en raw_data
@app.post("/api/raw/")
def crear_dato(data: dict, db: Session = Depends(get_db)):
    return crud.crear_entrada(db, data)

# Endpoint: ejecutar pipeline ETL
@app.post("/api/pipeline/run")
def ejecutar_pipeline():
    try:
        result = subprocess.run(["python", "etl_pipeline.py"], capture_output=True, text=True)
        return {
            "status": "ok",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# NUEVO: endpoint para guardar factura de venta (ingresos)
@app.post("/api/ingresos")
def guardar_factura_venta(data: dict, db: Session = Depends(get_db)):
    nueva = models.FacturaVenta(
        cliente=data["cliente"],
        descripcion=data["descripcion"],
        monto=data["monto"],
        fecha=data["fecha"]
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

# NUEVO: endpoint para guardar factura de compra (gastos)
@app.post("/api/gastos")
def guardar_factura_compra(data: dict, db: Session = Depends(get_db)):
    nueva = models.FacturaCompra(
        proveedor=data["proveedor"],
        descripcion=data["descripcion"],
        monto=data["monto"],
        fecha=data["fecha"]
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva
