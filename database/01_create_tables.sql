-- =====================================================================
-- Kaizen Logistica S.A. - Auditoria de Accesos TI
-- 01_create_tables.sql : crea las 9 tablas de la base KAIZEN
-- Ejecutar conectado como usuario KAIZEN en FREEPDB1
-- =====================================================================

-- 1. Nomina de RR.HH. (la "verdad" de quien trabaja y quien no)
CREATE TABLE rrhh_empleados (
  empleado_id          NUMBER        PRIMARY KEY,
  rut                  VARCHAR2(12)  NOT NULL UNIQUE,
  nombre               VARCHAR2(100) NOT NULL,
  area                 VARCHAR2(50)  NOT NULL,
  cargo                VARCHAR2(80)  NOT NULL,
  tipo_contrato        VARCHAR2(10)  NOT NULL CHECK (tipo_contrato IN ('PLANTA','TEMPORAL')),
  fecha_ingreso        DATE          NOT NULL,
  fecha_desvinculacion DATE,
  estado               VARCHAR2(12)  NOT NULL CHECK (estado IN ('ACTIVO','DESVINCULADO'))
);

-- 2. Cuentas del ERP (pueden no tener dueno: cuentas genericas o de servicio)
CREATE TABLE usuarios_erp (
  usuario_id     NUMBER       PRIMARY KEY,
  username       VARCHAR2(30) NOT NULL UNIQUE,
  empleado_id    NUMBER       REFERENCES rrhh_empleados(empleado_id),
  tipo_cuenta    VARCHAR2(10) NOT NULL CHECK (tipo_cuenta IN ('NOMINAL','GENERICA','SERVICIO')),
  estado         VARCHAR2(10) NOT NULL CHECK (estado IN ('ACTIVO','BLOQUEADO')),
  fecha_creacion DATE         NOT NULL,
  ultimo_login   DATE
);

-- 3. Roles del ERP
CREATE TABLE roles (
  rol_id          NUMBER        PRIMARY KEY,
  nombre          VARCHAR2(50)  NOT NULL UNIQUE,
  descripcion     VARCHAR2(200),
  es_privilegiado CHAR(1)       DEFAULT 'N' NOT NULL CHECK (es_privilegiado IN ('S','N'))
);

-- 4. Permisos individuales (lo que se puede hacer en el sistema)
CREATE TABLE permisos (
  permiso_id  NUMBER        PRIMARY KEY,
  codigo      VARCHAR2(30)  NOT NULL UNIQUE,
  descripcion VARCHAR2(200) NOT NULL,
  modulo      VARCHAR2(30)  NOT NULL
);

-- 5. Que permisos trae cada rol
CREATE TABLE rol_permiso (
  rol_id     NUMBER NOT NULL REFERENCES roles(rol_id),
  permiso_id NUMBER NOT NULL REFERENCES permisos(permiso_id),
  CONSTRAINT pk_rol_permiso PRIMARY KEY (rol_id, permiso_id)
);

-- 6. Que roles tiene cada usuario y quien lo aprobo
CREATE TABLE usuario_rol (
  usuario_id       NUMBER NOT NULL REFERENCES usuarios_erp(usuario_id),
  rol_id           NUMBER NOT NULL REFERENCES roles(rol_id),
  fecha_asignacion DATE   NOT NULL,
  aprobado_por     NUMBER REFERENCES rrhh_empleados(empleado_id),
  ticket_ref       VARCHAR2(20),
  CONSTRAINT pk_usuario_rol PRIMARY KEY (usuario_id, rol_id)
);

-- 7. Matriz de segregacion de funciones: pares de permisos incompatibles
CREATE TABLE matriz_sod (
  conflicto_id NUMBER        PRIMARY KEY,
  permiso_a    NUMBER        NOT NULL REFERENCES permisos(permiso_id),
  permiso_b    NUMBER        NOT NULL REFERENCES permisos(permiso_id),
  riesgo       VARCHAR2(5)   NOT NULL CHECK (riesgo IN ('ALTO','MEDIO','BAJO')),
  descripcion  VARCHAR2(200) NOT NULL
);

-- 8. Tickets de cambio a produccion
CREATE TABLE tickets_cambio (
  ticket_id             NUMBER        PRIMARY KEY,
  codigo                VARCHAR2(20)  NOT NULL UNIQUE,
  descripcion           VARCHAR2(200) NOT NULL,
  sistema               VARCHAR2(30)  NOT NULL,
  solicitado_por        NUMBER        NOT NULL REFERENCES rrhh_empleados(empleado_id),
  aprobado_por          NUMBER        REFERENCES rrhh_empleados(empleado_id),
  implementado_por      NUMBER        REFERENCES rrhh_empleados(empleado_id),
  fecha_solicitud       DATE          NOT NULL,
  fecha_aprobacion      DATE,
  fecha_paso_produccion DATE,
  estado                VARCHAR2(12)  NOT NULL CHECK (estado IN ('SOLICITADO','APROBADO','EN_PRODUCCION','RECHAZADO'))
);

-- 9. Log de inicios de sesion
CREATE TABLE log_accesos (
  log_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  usuario_id NUMBER       NOT NULL REFERENCES usuarios_erp(usuario_id),
  fecha_hora TIMESTAMP    NOT NULL,
  resultado  VARCHAR2(8)  NOT NULL CHECK (resultado IN ('EXITOSO','FALLIDO')),
  ip_origen  VARCHAR2(45)
);

-- Comprobacion: deberias ver las 9 tablas
SELECT table_name FROM user_tables ORDER BY table_name;
