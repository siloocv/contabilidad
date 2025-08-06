#!/usr/bin/env python
"""
Script de prueba para verificar el flujo completo de ETL
"""

import requests
import json
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

def test_create_factura_venta():
    """Prueba crear una factura de venta a través del nuevo sistema ETL"""
    print("\n1. Creando factura de venta...")
    data = {
        "cliente": "Test Cliente ETL",
        "descripcion": "Factura de prueba para ETL",
        "monto": 1500.00,
        "fecha": str(date.today())
    }
    
    response = requests.post(f"{BASE_URL}/api/facturas/venta/", json=data)
    if response.status_code == 201:
        result = response.json()
        print(f"   ✓ Factura enviada a raw_data. Raw ID: {result.get('raw_id')}")
        print(f"   Status: {result.get('status')}")
        return result.get('raw_id')
    else:
        print(f"   ✗ Error: {response.text}")
        return None

def test_create_cliente():
    """Prueba crear un cliente a través del nuevo sistema ETL"""
    print("\n2. Creando cliente...")
    data = {
        "nombre": "Cliente Test ETL",
        "identificacion": "123456789",
        "correo": "test@etl.com",
        "telefono": "88888888",
        "direccion": "Dirección de prueba"
    }
    
    response = requests.post(f"{BASE_URL}/api/clientes/", json=data)
    if response.status_code == 201:
        result = response.json()
        print(f"   ✓ Cliente enviado a raw_data. Raw ID: {result.get('raw_id')}")
        print(f"   Status: {result.get('status')}")
        return result.get('raw_id')
    else:
        print(f"   ✗ Error: {response.text}")
        return None

def test_create_producto():
    """Prueba crear un producto a través del nuevo sistema ETL"""
    print("\n3. Creando producto...")
    data = {
        "nombre": "Producto Test ETL",
        "sku": "TEST-ETL-001",
        "precio_unitario": 250.50,
        "descripcion": "Producto de prueba para ETL"
    }
    
    response = requests.post(f"{BASE_URL}/api/productos/", json=data)
    if response.status_code == 201:
        result = response.json()
        print(f"   ✓ Producto enviado a raw_data. Raw ID: {result.get('raw_id')}")
        print(f"   Status: {result.get('status')}")
        return result.get('raw_id')
    else:
        print(f"   ✗ Error: {response.text}")
        return None

def check_raw_data():
    """Verificar los datos en raw_data"""
    print("\n4. Verificando datos en raw_data...")
    response = requests.get(f"{BASE_URL}/api/raw/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Total registros en raw_data: {len(data)}")
        if data:
            print("   Últimos 3 registros:")
            for item in data[:3]:
                print(f"     - ID: {item['id']}, Tipo: {item['tipo']}, Desc: {item['descripcion'][:50]}...")
    else:
        print(f"   ✗ Error al obtener raw_data: {response.text}")

def run_etl_pipeline():
    """Ejecutar el pipeline ETL"""
    print("\n5. Ejecutando pipeline ETL...")
    response = requests.post(f"{BASE_URL}/api/pipeline/run")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Pipeline ejecutado correctamente")
        print(f"   Total raw: {result.get('total_raw')}")
        print(f"   Total cleaned: {result.get('total_cleaned')}")
        return True
    else:
        print(f"   ✗ Error al ejecutar pipeline: {response.text}")
        return False

def check_final_data():
    """Verificar que los datos llegaron a las tablas finales"""
    print("\n6. Verificando datos en tablas finales...")
    
    # Verificar facturas de venta
    response = requests.get(f"{BASE_URL}/api/facturas/venta/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Facturas de venta: {len(data)} registros")
    
    # Verificar clientes
    response = requests.get(f"{BASE_URL}/api/clientes/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Clientes: {len(data)} registros")
    
    # Verificar productos
    response = requests.get(f"{BASE_URL}/api/productos/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Productos: {len(data)} registros")

def main():
    print("=" * 60)
    print("PRUEBA DEL FLUJO ETL COMPLETO")
    print("=" * 60)
    
    # Crear datos de prueba
    raw_ids = []
    
    raw_id = test_create_factura_venta()
    if raw_id:
        raw_ids.append(raw_id)
    
    raw_id = test_create_cliente()
    if raw_id:
        raw_ids.append(raw_id)
    
    raw_id = test_create_producto()
    if raw_id:
        raw_ids.append(raw_id)
    
    # Verificar raw_data
    check_raw_data()
    
    # Ejecutar ETL
    if run_etl_pipeline():
        # Verificar datos finales
        check_final_data()
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)
    print("\nNOTA: Los datos nuevos ahora siguen el flujo:")
    print("1. Se guardan primero en raw_data")
    print("2. El ETL los procesa y valida")
    print("3. Se guardan en cleaned_data")
    print("4. Finalmente se insertan en las tablas de destino")

if __name__ == "__main__":
    main()