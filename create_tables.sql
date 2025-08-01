-- 1. Borrar y recrear la base limpia
DROP DATABASE IF EXISTS contabilidad;
CREATE DATABASE contabilidad CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Crear/asegurar usuario y permisos (local)
CREATE USER IF NOT EXISTS 'sebas'@'localhost' IDENTIFIED BY 'YES';
GRANT ALL PRIVILEGES ON contabilidad.* TO 'sebas'@'localhost';
FLUSH PRIVILEGES;

-- 3. Usar la base
USE contabilidad;

-- 4. Tablas principales (en el orden correcto)

-- Raw y cleaned
CREATE TABLE IF NOT EXISTS raw_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(50),
    descripcion TEXT,
    monto DECIMAL(10,2),
    fecha DATETIME,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tabla_destino VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cleaned_data (
    id INT PRIMARY KEY,  -- reutiliza el id de raw_data
    tipo VARCHAR(50),
    descripcion TEXT,
    monto DECIMAL(10,2),
    fecha DATETIME,
    creado_en DATETIME,
    validado_por VARCHAR(100),
    tabla_destino VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Facturas recurrentes: plantilla primero
CREATE TABLE IF NOT EXISTS facturas_recurrentes_template (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente VARCHAR(100),
    descripcion TEXT,
    monto DECIMAL(10,2),
    frecuencia VARCHAR(50),
    siguiente_generacion DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS facturas_recurrentes_instance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT,
    cliente VARCHAR(100),
    descripcion TEXT,
    monto DECIMAL(10,2),
    fecha DATE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_id INT,
    CONSTRAINT fk_instance_template FOREIGN KEY (template_id)
        REFERENCES facturas_recurrentes_template(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Facturas de venta y compra
CREATE TABLE IF NOT EXISTS facturas_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente VARCHAR(100),
    descripcion TEXT,
    monto DECIMAL(10,2),
    fecha DATE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_id INT,
    CONSTRAINT uq_factura_venta_raw UNIQUE (raw_id),
    CONSTRAINT fk_factura_venta_raw FOREIGN KEY (raw_id) REFERENCES raw_data(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS facturas_compra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor VARCHAR(100),
    descripcion TEXT,
    monto DECIMAL(10,2),
    fecha DATE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_id INT,
    CONSTRAINT uq_factura_compra_raw UNIQUE (raw_id),
    CONSTRAINT fk_factura_compra_raw FOREIGN KEY (raw_id) REFERENCES raw_data(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Órdenes de compra
CREATE TABLE IF NOT EXISTS ordenes_compra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor VARCHAR(100),
    descripcion TEXT,
    monto DECIMAL(10,2),
    fecha DATE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pagos recibidos (cliente paga factura de venta)
CREATE TABLE IF NOT EXISTS pagos_recibidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    factura_venta_id INT,
    monto DECIMAL(10,2),
    fecha DATE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_id INT,
    CONSTRAINT fk_pago_recibido_factura FOREIGN KEY (factura_venta_id) REFERENCES facturas_venta(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pagos a proveedores (por factura de compra u orden)
CREATE TABLE IF NOT EXISTS pagos_proveedor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    factura_compra_id INT NULL,
    orden_compra_id INT NULL,
    monto DECIMAL(10,2),
    fecha DATE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_id INT,
    CONSTRAINT fk_pago_proveedor_factura FOREIGN KEY (factura_compra_id) REFERENCES facturas_compra(id) ON DELETE SET NULL,
    CONSTRAINT fk_pago_proveedor_orden FOREIGN KEY (orden_compra_id) REFERENCES ordenes_compra(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
