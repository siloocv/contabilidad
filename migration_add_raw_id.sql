-- Agregar columna raw_id a las tablas que la necesitan

-- Facturas de venta
ALTER TABLE facturas_venta ADD COLUMN IF NOT EXISTS raw_id INT NULL;

-- Facturas de compra  
ALTER TABLE facturas_compra ADD COLUMN IF NOT EXISTS raw_id INT NULL;

-- Pagos recibidos
ALTER TABLE pagos_recibidos ADD COLUMN IF NOT EXISTS raw_id INT NULL;

-- Pagos a proveedores
ALTER TABLE pagos_proveedor ADD COLUMN IF NOT EXISTS raw_id INT NULL;

-- Facturas recurrentes instance
ALTER TABLE facturas_recurrentes_instance ADD COLUMN IF NOT EXISTS raw_id INT NULL;