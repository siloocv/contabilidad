from sqlalchemy.orm import Session
from models import RawData

def crear_entrada(db: Session, entrada_data: dict):
    nueva = RawData(**entrada_data)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva