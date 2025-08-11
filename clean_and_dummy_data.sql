-- Script para limpiar tablas y cargar datos de prueba
-- Ejecutar con: mysql -u root -pContaEntregable04 contabilidad < clean_and_dummy_data.sql

-- Desactivar verificación de foreign keys temporalmente
SET FOREIGN_KEY_CHECKS = 0;

-- Limpiar todas las tablas
TRUNCATE TABLE factura_items;
TRUNCATE TABLE pagos_proveedor;
TRUNCATE TABLE pagos_recibidos;
TRUNCATE TABLE ordenes_compra;
TRUNCATE TABLE facturas_compra;
TRUNCATE TABLE facturas_venta;
TRUNCATE TABLE productos;
TRUNCATE TABLE proveedores;
TRUNCATE TABLE clientes;
TRUNCATE TABLE cleaned_data;
TRUNCATE TABLE raw_data;
TRUNCATE TABLE facturas_recurrentes_instance;
TRUNCATE TABLE facturas_recurrentes_template;

-- Reactivar verificación de foreign keys
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- INSERTAR DATOS DUMMY
-- =====================================================

-- 1. CLIENTES (10 clientes)
INSERT INTO clientes (nombre, identificacion, correo, telefono, direccion) VALUES
('Empresa Tech Solutions S.A.', '3-101-123456', 'contacto@techsolutions.cr', '2222-3333', 'San José, Escazú, Centro Corporativo Plaza'),
('Juan Pérez Rodríguez', '1-1234-5678', 'juan.perez@email.com', '8888-1111', 'Heredia, San Rafael, Calle 5'),
('María González López', '2-0987-6543', 'maria.gonzalez@email.com', '8777-2222', 'Alajuela, Centro, Avenida Central'),
('Comercial El Buen Precio', '3-101-789012', 'ventas@buenprecio.cr', '2444-5555', 'Cartago, Centro, Frente al parque'),
('Ana Solís Vargas', '1-1111-2222', 'ana.solis@email.com', '8999-3333', 'San José, Desamparados, Barrio San Antonio'),
('Servicios Profesionales CR', '3-101-345678', 'info@serviciospro.cr', '2555-6666', 'San José, Santa Ana, Forum II'),
('Carlos Ramírez Mora', '1-3333-4444', 'carlos.ramirez@email.com', '8666-4444', 'Puntarenas, El Roble, Casa 25'),
('Distribuidora Nacional S.A.', '3-101-567890', 'compras@distribuidora.cr', '2666-7777', 'Limón, Centro, Zona Franca'),
('Laura Jiménez Castro', '2-5555-6666', 'laura.jimenez@email.com', '8555-5555', 'Guanacaste, Liberia, Barrio Condega'),
('Consultores Asociados Ltda', '3-102-234567', 'admin@consultores.cr', '2777-8888', 'San José, Pavas, Rohrmoser');

-- 2. PROVEEDORES (12 proveedores)
INSERT INTO proveedores (nombre, identificacion, correo, telefono, direccion, contacto_nombre, contacto_telefono) VALUES
('Dell Costa Rica', '3-101-445566', 'ventas@dell.cr', '2222-9999', 'San José, Escazú, Torre Lexus', 'Carlos Mendez', '8811-2233'),
('Ingram Micro', '3-101-778899', 'info@ingrammicro.cr', '2333-4444', 'Heredia, Zona Franca America', 'Ana Vargas', '8822-3344'),
('Microsoft Costa Rica', '3-101-112233', 'partners@microsoft.cr', '2444-5555', 'San José, La Sabana, Torre Mercedes', 'Luis Rodríguez', '8833-4455'),
('APC Centroamérica', '3-101-334455', 'ventas@apc-ca.com', '2555-6666', 'San José, Curridabat', 'María Castro', '8844-5566'),
('Tecnología Global S.A.', '3-101-556677', 'compras@tecglobal.cr', '2666-7777', 'Alajuela, Zona Franca Coyol', 'Pedro Jiménez', '8855-6677'),
('Office Depot', '3-101-889900', 'empresas@officedepot.cr', '2777-8888', 'San José, Paseo Colón', 'Sofía Mora', '8866-7788'),
('HP Costa Rica', '3-101-990011', 'ventas@hp.cr', '2888-9999', 'San José, Santa Ana, Lindora', 'Roberto Sánchez', '8877-8899'),
('Logitech Distribuidores', '3-101-223344', 'info@logitech.cr', '2999-0000', 'Heredia, San Francisco', 'Carmen López', '8888-9900'),
('Cable & Wireless', '3-101-667788', 'empresas@cwpanama.cr', '2100-1111', 'San José, Sabana Norte', 'Jorge Ramírez', '8899-0011'),
('ICE Telecomunicaciones', '3-101-000001', 'corporativo@ice.go.cr', '2200-2222', 'San José, Sabana Norte, Torre ICE', 'Patricia Vargas', '8900-1122'),
('Samsung Electronics', '3-101-445577', 'b2b@samsung.cr', '2300-3333', 'San José, Escazú, Plaza Tempo', 'Daniel Rojas', '8911-2233'),
('Lenovo Costa Rica', '3-101-556688', 'ventas@lenovo.cr', '2400-4444', 'San José, Santa Ana, City Place', 'Andrea Herrera', '8922-3344');

-- 3. PRODUCTOS (15 productos de oficina y servicios)
INSERT INTO productos (nombre, sku, precio_unitario, descripcion) VALUES
('Laptop Dell Latitude', 'LAP-001', 750000.00, 'Laptop empresarial Core i5, 8GB RAM, 256GB SSD'),
('Mouse inalámbrico', 'MOU-001', 15000.00, 'Mouse óptico inalámbrico USB'),
('Teclado mecánico', 'TEC-001', 45000.00, 'Teclado mecánico retroiluminado'),
('Monitor LED 24"', 'MON-001', 185000.00, 'Monitor Full HD 24 pulgadas'),
('Servicio Consultoría TI', 'SRV-001', 75000.00, 'Hora de consultoría en tecnología'),
('Licencia Office 365', 'LIC-001', 12000.00, 'Licencia mensual Office 365 Business'),
('Router WiFi 6', 'ROU-001', 95000.00, 'Router inalámbrico WiFi 6 alta velocidad'),
('Disco Duro 1TB', 'HDD-001', 55000.00, 'Disco duro externo USB 3.0 1TB'),
('Webcam HD', 'WEB-001', 35000.00, 'Cámara web HD 1080p con micrófono'),
('Servicio Soporte Técnico', 'SRV-002', 50000.00, 'Servicio mensual de soporte técnico'),
('Impresora Láser', 'IMP-001', 225000.00, 'Impresora láser monocromática'),
('UPS 1000VA', 'UPS-001', 165000.00, 'Sistema de alimentación ininterrumpida'),
('Cable HDMI 2m', 'CAB-001', 8500.00, 'Cable HDMI 2.0 de 2 metros'),
('Audífonos Bluetooth', 'AUD-001', 65000.00, 'Audífonos inalámbricos con cancelación de ruido'),
('Silla Ergonómica', 'SIL-001', 185000.00, 'Silla de oficina ergonómica con soporte lumbar');

-- 3. FACTURAS DE VENTA (15 facturas, últimos 3 meses)
INSERT INTO facturas_venta (cliente, descripcion, monto, fecha, raw_id) VALUES
('Empresa Tech Solutions S.A.', 'Venta de equipos de cómputo', 2250000.00, '2025-05-15', NULL),
('Juan Pérez Rodríguez', 'Servicio de consultoría mensual', 450000.00, '2025-05-20', NULL),
('María González López', 'Licencias de software', 156000.00, '2025-05-25', NULL),
('Comercial El Buen Precio', 'Equipos de red y accesorios', 890000.00, '2025-06-01', NULL),
('Ana Solís Vargas', 'Laptop y accesorios', 845000.00, '2025-06-05', NULL),
('Servicios Profesionales CR', 'Servicio de soporte anual', 600000.00, '2025-06-10', NULL),
('Carlos Ramírez Mora', 'Monitor y periféricos', 258500.00, '2025-06-15', NULL),
('Distribuidora Nacional S.A.', 'Compra mayorista de equipos', 5500000.00, '2025-06-20', NULL),
('Laura Jiménez Castro', 'Audífonos y webcam', 100000.00, '2025-06-25', NULL),
('Consultores Asociados Ltda', 'Renovación de equipos', 3200000.00, '2025-07-01', NULL),
('Empresa Tech Solutions S.A.', 'Mantenimiento mensual', 350000.00, '2025-07-05', NULL),
('Juan Pérez Rodríguez', 'Actualización de software', 225000.00, '2025-07-10', NULL),
('María González López', 'Compra de impresora', 225000.00, '2025-07-15', NULL),
('Comercial El Buen Precio', 'UPS y respaldos', 385000.00, '2025-07-20', NULL),
('Ana Solís Vargas', 'Silla ergonómica', 185000.00, '2025-08-01', NULL);

-- 4. FACTURAS DE COMPRA (10 facturas de proveedores)
INSERT INTO facturas_compra (proveedor, descripcion, monto, fecha, raw_id) VALUES
('Dell Costa Rica', 'Compra de laptops para inventario', 4500000.00, '2025-05-10', NULL),
('Ingram Micro', 'Accesorios y periféricos', 850000.00, '2025-05-18', NULL),
('Microsoft Costa Rica', 'Licencias de software', 320000.00, '2025-05-28', NULL),
('APC Centroamérica', 'Sistemas UPS', 660000.00, '2025-06-08', NULL),
('Tecnología Global S.A.', 'Equipos de red', 475000.00, '2025-06-18', NULL),
('Office Depot', 'Mobiliario de oficina', 925000.00, '2025-06-28', NULL),
('HP Costa Rica', 'Impresoras y consumibles', 675000.00, '2025-07-08', NULL),
('Logitech Distribuidores', 'Accesorios de cómputo', 380000.00, '2025-07-18', NULL),
('Cable & Wireless', 'Servicios de internet', 125000.00, '2025-07-28', NULL),
('ICE Telecomunicaciones', 'Servicios telefónicos', 45000.00, '2025-08-05', NULL);

-- 5. ÓRDENES DE COMPRA (5 órdenes pendientes)
INSERT INTO ordenes_compra (proveedor, descripcion, monto, fecha) VALUES
('Samsung Electronics', 'Monitores 4K para proyectos', 2800000.00, '2025-07-25'),
('Lenovo Costa Rica', 'Servidores para datacenter', 8500000.00, '2025-07-30'),
('Cisco Systems', 'Equipos de networking', 3200000.00, '2025-08-02'),
('Adobe Systems', 'Licencias Creative Cloud', 480000.00, '2025-08-04'),
('VMware', 'Licencias de virtualización', 1200000.00, '2025-08-05');

-- 6. PAGOS RECIBIDOS (10 pagos parciales y totales)
INSERT INTO pagos_recibidos (factura_venta_id, monto, fecha, raw_id) VALUES
(1, 1500000.00, '2025-05-20', NULL),  -- Pago parcial factura 1
(1, 750000.00, '2025-05-25', NULL),   -- Pago final factura 1
(2, 450000.00, '2025-05-25', NULL),   -- Pago total factura 2
(3, 156000.00, '2025-05-30', NULL),   -- Pago total factura 3
(4, 500000.00, '2025-06-10', NULL),   -- Pago parcial factura 4
(5, 845000.00, '2025-06-15', NULL),   -- Pago total factura 5
(6, 300000.00, '2025-06-20', NULL),   -- Pago parcial factura 6
(8, 2000000.00, '2025-06-25', NULL),  -- Pago parcial factura 8
(8, 2000000.00, '2025-07-05', NULL),  -- Segundo pago factura 8
(10, 3200000.00, '2025-07-10', NULL); -- Pago total factura 10

-- 7. PAGOS A PROVEEDORES (8 pagos)
INSERT INTO pagos_proveedor (factura_compra_id, orden_compra_id, monto, fecha, raw_id) VALUES
(1, NULL, 2000000.00, '2025-05-15', NULL),  -- Pago parcial factura compra 1
(1, NULL, 2500000.00, '2025-05-25', NULL),  -- Pago final factura compra 1
(2, NULL, 850000.00, '2025-05-25', NULL),   -- Pago total factura compra 2
(3, NULL, 320000.00, '2025-06-05', NULL),   -- Pago total factura compra 3
(4, NULL, 660000.00, '2025-06-15', NULL),   -- Pago total factura compra 4
(NULL, 1, 1400000.00, '2025-08-01', NULL),  -- Pago parcial orden compra 1
(9, NULL, 125000.00, '2025-08-05', NULL),   -- Pago total factura compra 9
(10, NULL, 45000.00, '2025-08-06', NULL);   -- Pago total factura compra 10

-- 8. ITEMS DE FACTURAS (Relacionar productos con algunas facturas)
INSERT INTO factura_items (factura_tipo, factura_venta_id, factura_compra_id, producto_id, cantidad, precio) VALUES
('venta', 1, NULL, 1, 3, 750000.00),  -- 3 Laptops en factura venta 1
('venta', 5, NULL, 1, 1, 750000.00),  -- 1 Laptop en factura venta 5
('venta', 5, NULL, 2, 2, 15000.00),   -- 2 Mouse en factura venta 5
('venta', 5, NULL, 3, 1, 45000.00),   -- 1 Teclado en factura venta 5
('venta', 8, NULL, 1, 5, 750000.00),  -- 5 Laptops en factura venta 8
('venta', 8, NULL, 4, 10, 185000.00), -- 10 Monitores en factura venta 8
('venta', 10, NULL, 11, 10, 225000.00), -- 10 Impresoras en factura venta 10
('venta', 10, NULL, 12, 6, 165000.00),  -- 6 UPS en factura venta 10
('compra', NULL, 1, 1, 6, 750000.00),   -- Compra de 6 laptops
('compra', NULL, 4, 12, 4, 165000.00);  -- Compra de 4 UPS

-- Mensaje de confirmación
SELECT 'Datos de prueba cargados exitosamente!' AS mensaje;
SELECT 
    (SELECT COUNT(*) FROM clientes) as total_clientes,
    (SELECT COUNT(*) FROM proveedores) as total_proveedores,
    (SELECT COUNT(*) FROM productos) as total_productos,
    (SELECT COUNT(*) FROM facturas_venta) as total_facturas_venta,
    (SELECT COUNT(*) FROM facturas_compra) as total_facturas_compra,
    (SELECT COUNT(*) FROM pagos_recibidos) as total_pagos_recibidos,
    (SELECT COUNT(*) FROM pagos_proveedor) as total_pagos_proveedor;