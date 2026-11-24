# Auditoría de Accesos TI · Kaizen Logística

[English version](README.en.md)

Proyecto personal en desarrollo. Me interesan mucho los datos y la seguridad de la información, y quise juntar las dos cosas aprendiendo cómo se hace una auditoría de accesos TI: el tipo de revisión que hacen las áreas de riesgo y auditoría para ver quién tiene acceso a qué dentro de una empresa.

Como no puedo usar datos reales, inventé una empresa: Kaizen Logística, una empresa de despacho que contrata temporales en Cyber y Navidad. El problema que quiero mostrar es bien común: la gente se va, pero sus cuentas siguen activas, y en temporada alta se reparten permisos que después nadie quita.

## Problemática

En muchas empresas la revisión de accesos se hace a mano, en planillas Excel y una vez al año. Eso significa que una cuenta que debió cerrarse en enero puede seguir abierta hasta diciembre sin que nadie lo note. Mientras tanto, esa cuenta puede ver datos de clientes o aprobar pagos.

Me motivó pensar que esto se puede revisar de forma automática y seguido, no solo cuando llega la auditoría. Le serviría sobre todo a empresas con mucha rotación de personal, como retail y logística, y a sus equipos de TI y auditoría interna, que tienen que demostrar que controlan quién entra a sus sistemas. Y al final también protege a las personas cuyos datos guardan esas empresas, que es justamente lo que busca la nueva Ley 21.719.

## Cómo lo armé

Creé una base de datos en Oracle y un script en Python que llena la empresa con empleados, cuentas, roles y tickets de cambio. Al generar los datos dejo errores escondidos a propósito, y después los busco con consultas SQL, como lo haría un auditor.

## Controles

| Código | Qué reviso | Estado |
| --- | --- | --- |
| AC-01 | Ex trabajadores que siguen con su cuenta activa | Listo |
| AC-02 | Usuarios con permisos incompatibles (segregación de funciones) | Pendiente |
| AC-03 | Cuentas de administrador fuera de TI y cuentas genéricas | Pendiente |
| AC-04 | Cuentas sin uso por más de 90 días | Pendiente |
| CM-01 | Cambios a producción sin aprobación | Pendiente |

Tomo como referencia la ISO/IEC 27001:2022 y la Ley 21.719 de Protección de Datos Personales.

## Qué hay en el repo

```
database/          creación de las tablas
data_generator/    generador de datos ficticios
audit_tests/       una consulta SQL por control
```

Uso Oracle Database Free sobre Docker, SQL y Python (oracledb y Faker).

## Cómo probarlo

1. Levanta Oracle con la imagen `gvenzl/oracle-free` y crea el usuario `kaizen`.
2. Ejecuta `database/01_create_tables.sql`.
3. Instala `oracledb` y `faker`, y corre `data_generator/generar_datos.py`.
4. Prueba las consultas de `audit_tests/` en cualquier cliente SQL.

## Lo que viene

Terminar los controles que faltan, automatizarlos con Python, pasar los resultados a Excel, armar un dashboard y escribir un informe final con recomendaciones.

Todos los datos son inventados.

Claudio Galiano · Ingeniería en Informática, Duoc UC
