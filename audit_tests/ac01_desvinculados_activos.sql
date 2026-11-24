-- AC-01: desvinculados en RR.HH. con cuenta activa en el ERP
SELECT e.nombre, e.tipo_contrato, e.fecha_desvinculacion,
       u.username, u.estado
FROM rrhh_empleados e
JOIN usuarios_erp u ON e.empleado_id = u.empleado_id
WHERE e.estado = 'DESVINCULADO'
  AND u.estado = 'ACTIVO';
