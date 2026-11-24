"""
Kaizen Logistica S.A. - Generador de datos ficticios para la auditoria de accesos.

Que hace:
  1. Crea empleados (planta y temporales de peak), cuentas del ERP, roles,
     permisos, matriz SoD, tickets de cambio y log de accesos.
  2. Siembra errores A PROPOSITO (los "hallazgos" que la auditoria debe encontrar).
  3. Guarda la "lista de respuestas" en respuestas_esperadas.csv para validar
     despues que nuestras pruebas encuentran el 100%.
  4. Carga todo en Oracle (usuario KAIZEN, base FREEPDB1).

Uso:
  python3 generar_datos.py            -> carga en Oracle
  python3 generar_datos.py --dry-run  -> solo genera CSV en ./salida (sin Oracle)

Siempre genera los mismos datos (semilla fija), asi el resultado es repetible.
"""
import csv
import os
import random
import sys
import unicodedata
from datetime import date, datetime, timedelta

from faker import Faker

# ---------------------------------------------------------------- configuracion
SEMILLA = 42
FECHA_CORTE = date(2026, 11, 30)          # dia en que "hacemos" la auditoria
N_PLANTA = 250
N_TEMPORALES = 80                         # contratados para Cyber/Navidad 2025

DB_USER = os.getenv("KAIZEN_USER", "kaizen")
DB_PASS = os.getenv("KAIZEN_PASS", "ClaveKaizen123")
DB_DSN = os.getenv("KAIZEN_DSN", "localhost:1521/FREEPDB1")

random.seed(SEMILLA)
fake = Faker("es_CL")
Faker.seed(SEMILLA)

respuestas = []   # (control, tipo, id_registro, detalle)


def anotar(control, tipo, id_registro, detalle):
    respuestas.append((control, tipo, id_registro, detalle))


def rut_ficticio(numero):
    """Calcula el digito verificador (modulo 11) para que el RUT sea valido."""
    suma, factor = 0, 2
    for d in reversed(str(numero)):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    dv = 11 - suma % 11
    dv = {11: "0", 10: "K"}.get(dv, str(dv))
    return f"{numero}-{dv}"


def fecha_entre(desde, hasta):
    return desde + timedelta(days=random.randint(0, (hasta - desde).days))


# ---------------------------------------------------------------- permisos y roles
PERMISOS = [
    # id, codigo, descripcion, modulo
    (1, "REGISTRAR_ENVIO", "Registrar y despachar envios", "OPERACIONES"),
    (2, "GESTIONAR_BODEGA", "Mover stock entre bodegas", "OPERACIONES"),
    (3, "VER_DATOS_CLIENTES", "Ver nombre, RUT y direccion de destinatarios", "CLIENTES"),
    (4, "EXPORTAR_DATOS_CLIENTES", "Exportar base de destinatarios a Excel", "CLIENTES"),
    (5, "CREAR_PROVEEDOR", "Crear o modificar proveedores", "COMPRAS"),
    (6, "CREAR_OC", "Crear ordenes de compra", "COMPRAS"),
    (7, "APROBAR_OC", "Aprobar ordenes de compra", "COMPRAS"),
    (8, "EMITIR_PAGO", "Preparar pagos a proveedores", "FINANZAS"),
    (9, "APROBAR_PAGO", "Aprobar y liberar pagos", "FINANZAS"),
    (10, "MODIFICAR_TARIFAS", "Cambiar tarifas de envio", "COMERCIAL"),
    (11, "VER_REPORTES", "Ver reportes de gestion", "GESTION"),
    (12, "ADMIN_USUARIOS", "Crear usuarios y asignar roles", "TI"),
    (13, "ADMIN_SISTEMA", "Configurar el ERP y la base de datos", "TI"),
]

ROLES = [
    # id, nombre, descripcion, privilegiado, permisos
    (1, "OPERADOR_BODEGA", "Personal de bodega", "N", [1, 2]),
    (2, "REPARTIDOR", "Personal de reparto", "N", [1, 3]),
    (3, "ATENCION_CLIENTE", "Ejecutivo de atencion", "N", [3]),
    (4, "ANALISTA_COMPRAS", "Gestiona proveedores y OC", "N", [5, 6]),
    (5, "JEFE_COMPRAS", "Aprueba ordenes de compra", "N", [7, 11]),
    (6, "ANALISTA_TESORERIA", "Prepara pagos", "N", [8]),
    (7, "JEFE_FINANZAS", "Aprueba pagos", "N", [9, 11]),
    (8, "COMERCIAL", "Gestiona tarifas", "N", [10, 11]),
    (9, "GERENCIA", "Consulta reportes", "N", [11]),
    (10, "SOPORTE_TI", "Mesa de ayuda", "N", [11]),
    (11, "ADMIN_TI", "Administrador del ERP", "S", [12, 13]),
    (12, "ANALISTA_DATOS", "Reportes de clientes", "N", [3, 4, 11]),
    (13, "JEFE_RRHH", "Gestion de personas", "N", [11]),
]

MATRIZ_SOD = [
    # id, permiso_a, permiso_b, riesgo, descripcion
    (1, 5, 9, "ALTO", "Crear proveedor y aprobar pagos: puede pagarse a un proveedor falso"),
    (2, 6, 7, "ALTO", "Crear y aprobar la misma orden de compra"),
    (3, 8, 9, "ALTO", "Preparar y aprobar el mismo pago"),
    (4, 12, 9, "ALTO", "Darse permisos a si mismo y aprobar pagos"),
    (5, 4, 12, "MEDIO", "Exportar datos de clientes y borrar rastros de usuarios"),
]

# area -> (cargo jefe, [(cargo, rol_id)], cuantos de planta)
AREAS = {
    "Operaciones": ("Jefe de Operaciones", [("Operador de bodega", 1)], 70),
    "Reparto": ("Jefe de Reparto", [("Conductor repartidor", 2)], 70),
    "Atencion al Cliente": ("Jefe de Atencion", [("Ejecutivo de atencion", 3)], 30),
    "Compras": ("Jefe de Compras", [("Analista de compras", 4)], 10),
    "Finanzas": ("Jefe de Finanzas", [("Analista de tesoreria", 6)], 12),
    "Comercial": ("Jefe Comercial", [("Ejecutivo comercial", 8), ("Analista de datos", 12)], 20),
    "TI": ("Jefe de TI", [("Soporte TI", 10), ("Administrador ERP", 11)], 12),
    "RRHH": ("Jefe de RR.HH.", [("Analista de RR.HH.", 9)], 6),
    "Gerencia": ("Gerente General", [("Gerente de area", 9)], 20),
}
ROL_JEFE = {"Operaciones": 1, "Reparto": 2, "Atencion al Cliente": 3, "Compras": 5,
            "Finanzas": 7, "Comercial": 8, "TI": 11, "RRHH": 13, "Gerencia": 9}

# ---------------------------------------------------------------- empleados
empleados, jefes = [], {}
ruts_usados = set()


def nuevo_empleado(area, cargo, tipo, ingreso, salida=None):
    emp_id = len(empleados) + 1
    while True:
        num = random.randint(10_000_000, 24_999_999)
        if num not in ruts_usados:
            ruts_usados.add(num)
            break
    empleados.append({
        "empleado_id": emp_id, "rut": rut_ficticio(num),
        "nombre": f"{fake.first_name()} {fake.last_name()} {fake.last_name()}",
        "area": area, "cargo": cargo, "tipo_contrato": tipo,
        "fecha_ingreso": ingreso, "fecha_desvinculacion": salida,
        "estado": "DESVINCULADO" if salida else "ACTIVO",
    })
    return emp_id


rol_de_empleado = {}
for area, (cargo_jefe, cargos, n) in AREAS.items():
    jefe = nuevo_empleado(area, cargo_jefe, "PLANTA", fecha_entre(date(2015, 1, 1), date(2021, 12, 31)))
    jefes[area] = jefe
    rol_de_empleado[jefe] = ROL_JEFE[area]
    for i in range(n - 1):
        cargo, rol = cargos[i % len(cargos)]
        if rol == 11 and i > 5:          # solo 3 administradores ERP
            cargo, rol = cargos[0]
        e = nuevo_empleado(area, cargo, "PLANTA", fecha_entre(date(2016, 1, 1), date(2025, 12, 31)))
        rol_de_empleado[e] = rol

ids_planta = [e["empleado_id"] for e in empleados]

# 15 empleados de planta que renunciaron durante 2026
renuncias = random.sample([i for i in ids_planta if i not in jefes.values()], 15)
for i in renuncias:
    emp = empleados[i - 1]
    emp["fecha_desvinculacion"] = fecha_entre(date(2026, 2, 1), date(2026, 10, 31))
    emp["estado"] = "DESVINCULADO"

# Temporales del peak Cyber/Navidad 2025: entran oct-dic 2025, salen en enero 2026
ids_temporales = []
for _ in range(N_TEMPORALES):
    area, cargo, rol = random.choice([("Operaciones", "Operador de bodega temporal", 1),
                                       ("Reparto", "Repartidor temporal", 2),
                                       ("Atencion al Cliente", "Ejecutivo temporal", 3)])
    e = nuevo_empleado(area, cargo, "TEMPORAL", fecha_entre(date(2025, 10, 15), date(2025, 12, 1)),
                       fecha_entre(date(2026, 1, 5), date(2026, 1, 31)))
    rol_de_empleado[e] = rol
    ids_temporales.append(e)

# ---------------------------------------------------------------- cuentas ERP y roles
usuarios, usuario_rol, logs = [], [], []
usuario_de_empleado = {}


def nuevo_usuario(username, empleado_id, tipo, estado, creacion):
    uid = len(usuarios) + 1
    usuarios.append({"usuario_id": uid, "username": username, "empleado_id": empleado_id,
                     "tipo_cuenta": tipo, "estado": estado, "fecha_creacion": creacion,
                     "ultimo_login": None})
    return uid


def asignar_rol(uid, rol, fecha, aprobador, ticket=True):
    usuario_rol.append({"usuario_id": uid, "rol_id": rol, "fecha_asignacion": fecha,
                        "aprobado_por": aprobador,
                        "ticket_ref": f"ACC-{len(usuario_rol) + 1:05d}" if ticket else None})


usernames = set()
for emp in empleados:
    base = (emp["nombre"].split()[0][0] + emp["nombre"].split()[1]).lower()
    base = unicodedata.normalize("NFKD", base)                     # quita tildes: Guzman
    base = "".join(c for c in base if c.isalnum() and ord(c) < 128)
    username, n = base, 1
    while username in usernames:
        n += 1
        username = f"{base}{n}"
    usernames.add(username)
    estado = "BLOQUEADO" if emp["estado"] == "DESVINCULADO" else "ACTIVO"
    uid = nuevo_usuario(username, emp["empleado_id"], "NOMINAL", estado, emp["fecha_ingreso"])
    usuario_de_empleado[emp["empleado_id"]] = uid
    rol = rol_de_empleado[emp["empleado_id"]]
    # el jefe del area aprueba; los jefes los aprueba el Gerente General
    aprobador = jefes[emp["area"]] if jefes[emp["area"]] != emp["empleado_id"] else jefes["Gerencia"]
    if emp["empleado_id"] == jefes["Gerencia"]:
        aprobador = jefes["RRHH"]
    asignar_rol(uid, rol, emp["fecha_ingreso"], aprobador)

# cuenta de servicio legitima (sin dueno, pero documentada y sin privilegios)
svc = nuevo_usuario("svc_tracking", None, "SERVICIO", "ACTIVO", date(2022, 3, 1))
asignar_rol(svc, 10, date(2022, 3, 1), jefes["TI"])

# ================================================================= ERRORES SEMBRADOS
def emp(i):
    return empleados[i - 1]


activos_planta = [i for i in ids_planta if emp(i)["estado"] == "ACTIVO" and i not in jefes.values()]

# --- AC-01: desvinculados con cuenta ACTIVA (12 temporales + 4 de planta)
ac01 = random.sample(ids_temporales, 12) + random.sample(renuncias, 4)
for e in ac01:
    usuarios[usuario_de_empleado[e] - 1]["estado"] = "ACTIVO"
    anotar("AC-01", "DESVINCULADO_ACTIVO", usuarios[usuario_de_empleado[e] - 1]["username"],
           f"{emp(e)['tipo_contrato']} desvinculado el {emp(e)['fecha_desvinculacion']}")
# 5 de ellos incluso iniciaron sesion despues de irse (lo mas grave)
login_post_salida = ac01[:5]

# --- AC-02: conflictos de segregacion de funciones (6 usuarios)
# a cada uno le dan un segundo rol "para salir del paso" en el peak de diciembre 2025
PARES_SOD = [(4, 7), (4, 7), (4, 5), (6, 7), (11, 7), (12, 11)]   # (rol que tenia, rol extra)
candidatos = []
for rol_base, rol_extra in PARES_SOD:
    e = random.choice([i for i in activos_planta if rol_de_empleado[i] == rol_base and i not in candidatos])
    candidatos.append(e)
    asignar_rol(usuario_de_empleado[e], rol_extra, fecha_entre(date(2025, 11, 20), date(2025, 12, 20)),
                jefes[emp(e)["area"]])
    if rol_extra == 11 and emp(e)["area"] != "TI":
        anotar("AC-03", "ADMIN_FUERA_DE_TI", usuarios[usuario_de_empleado[e] - 1]["username"],
               f"{emp(e)['cargo']} de {emp(e)['area']} con rol ADMIN_TI")
# las respuestas de AC-02 se calculan al final (ver validar_sod)

# --- AC-03: accesos privilegiados indebidos
no_ti = random.sample([i for i in activos_planta if emp(i)["area"] not in ("TI",) and i not in candidatos], 3)
for e in no_ti:
    asignar_rol(usuario_de_empleado[e], 11, fecha_entre(date(2025, 6, 1), date(2026, 9, 30)), jefes["TI"])
    anotar("AC-03", "ADMIN_FUERA_DE_TI", usuarios[usuario_de_empleado[e] - 1]["username"],
           f"{emp(e)['cargo']} de {emp(e)['area']} con rol ADMIN_TI")
for nombre in ("admin", "soporte01"):
    uid = nuevo_usuario(nombre, None, "GENERICA", "ACTIVO", date(2021, 5, 10))
    asignar_rol(uid, 11, date(2021, 5, 10), None, ticket=False)
    anotar("AC-03", "GENERICA_PRIVILEGIADA", nombre, "Cuenta generica sin dueno con rol ADMIN_TI y sin aprobacion")
ti_sin_aprob = [i for i in activos_planta if rol_de_empleado.get(i) == 11 and i not in candidatos][:1]
for e in ti_sin_aprob:
    for ur in usuario_rol:
        if ur["usuario_id"] == usuario_de_empleado[e] and ur["rol_id"] == 11:
            ur["aprobado_por"], ur["ticket_ref"] = None, None
            anotar("AC-03", "PRIVILEGIO_SIN_APROBACION", usuarios[usuario_de_empleado[e] - 1]["username"],
                   "Rol ADMIN_TI asignado sin aprobador ni ticket")

# --- AC-04: cuentas activas sin login hace mas de 90 dias (8)
excluir = set(ac01) | set(candidatos) | set(no_ti) | set(ti_sin_aprob)
inactivos = random.sample([i for i in activos_planta if i not in excluir], 8)

# ---------------------------------------------------------------- log de accesos
def registrar_logins(uid, desde, hasta, n):
    ult = None
    for _ in range(n):
        d = fecha_entre(desde, hasta)
        ts = datetime(d.year, d.month, d.day, random.randint(7, 20), random.randint(0, 59))
        logs.append({"usuario_id": uid, "fecha_hora": ts,
                     "resultado": "EXITOSO" if random.random() > 0.05 else "FALLIDO",
                     "ip_origen": f"10.20.{random.randint(1, 30)}.{random.randint(2, 250)}"})
        if logs[-1]["resultado"] == "EXITOSO" and (ult is None or ts > ult):
            ult = ts
    usuarios[uid - 1]["ultimo_login"] = ult


for u in usuarios:
    uid, e = u["usuario_id"], u["empleado_id"]
    if e is None:
        registrar_logins(uid, FECHA_CORTE - timedelta(days=30), FECHA_CORTE, 6)
        continue
    em = emp(e)
    if e in inactivos:
        registrar_logins(uid, date(2026, 3, 1), FECHA_CORTE - timedelta(days=120), 4)
        dias = (FECHA_CORTE - usuarios[uid - 1]["ultimo_login"].date()).days
        anotar("AC-04", "SIN_LOGIN_90_DIAS", u["username"], f"Ultimo login hace {dias} dias")
    elif em["estado"] == "DESVINCULADO":
        salida = em["fecha_desvinculacion"]
        registrar_logins(uid, max(em["fecha_ingreso"], salida - timedelta(days=60)), salida - timedelta(days=1), 5)
        if e in login_post_salida:
            antes = usuarios[uid - 1]["ultimo_login"]
            registrar_logins(uid, salida + timedelta(days=3), FECHA_CORTE - timedelta(days=5), 2)
            if usuarios[uid - 1]["ultimo_login"] is None or (antes and usuarios[uid - 1]["ultimo_login"] < antes):
                usuarios[uid - 1]["ultimo_login"] = antes
            anotar("AC-01", "LOGIN_POST_SALIDA", u["username"], "Inicio sesion despues de su desvinculacion")
    else:
        registrar_logins(uid, FECHA_CORTE - timedelta(days=60), FECHA_CORTE, 5)
    # garantiza al menos un login exitoso para cuentas activas normales
    if u["ultimo_login"] is None and e not in inactivos:
        hasta = FECHA_CORTE if em["estado"] == "ACTIVO" else em["fecha_desvinculacion"] - timedelta(days=1)
        ts = datetime.combine(hasta - timedelta(days=2), datetime.min.time()).replace(hour=9)
        logs.append({"usuario_id": uid, "fecha_hora": ts, "resultado": "EXITOSO", "ip_origen": "10.20.1.10"})
        u["ultimo_login"] = ts

# ---------------------------------------------------------------- tickets de cambio
tickets = []
ti_staff = [i for i in ids_planta if emp(i)["area"] == "TI" and emp(i)["estado"] == "ACTIVO" and i != jefes["TI"]]
solicitantes = [i for i in ids_planta if emp(i)["area"] in ("Operaciones", "Comercial", "Finanzas", "Reparto")]
SISTEMAS = ["ERP", "WMS Bodega", "Portal Tracking", "App Repartidor"]
CAMBIOS = ["Ajuste de reporte", "Nuevo campo en formulario", "Correccion de calculo de tarifa",
           "Actualizacion de version", "Cambio de regla de despacho", "Parche de seguridad",
           "Nueva integracion con courier", "Mejora de rendimiento"]
for t in range(1, 61):
    sol = fecha_entre(date(2026, 1, 5), date(2026, 11, 10))
    apr = sol + timedelta(days=random.randint(1, 5))
    prod = apr + timedelta(days=random.randint(1, 7))
    estado = random.choices(["EN_PRODUCCION", "SOLICITADO", "RECHAZADO"], [0.8, 0.1, 0.1])[0]
    tk = {"ticket_id": t, "codigo": f"CHG-2026-{t:03d}",
          "descripcion": f"{random.choice(CAMBIOS)} en {random.choice(SISTEMAS)}",
          "sistema": random.choice(SISTEMAS), "solicitado_por": random.choice(solicitantes),
          "aprobado_por": jefes["TI"], "implementado_por": random.choice(ti_staff),
          "fecha_solicitud": sol, "fecha_aprobacion": apr, "fecha_paso_produccion": prod,
          "estado": estado}
    if estado == "SOLICITADO":
        tk.update(aprobado_por=None, implementado_por=None, fecha_aprobacion=None, fecha_paso_produccion=None)
    elif estado == "RECHAZADO":
        tk.update(implementado_por=None, fecha_paso_produccion=None)
    tickets.append(tk)

en_prod = [t for t in tickets if t["estado"] == "EN_PRODUCCION"]
sembrados = random.sample(en_prod, 12)
for t in sembrados[:5]:       # en produccion sin aprobacion
    t.update(aprobado_por=None, fecha_aprobacion=None)
    anotar("CM-01", "SIN_APROBACION", t["codigo"], "Paso a produccion sin aprobacion")
for t in sembrados[5:9]:      # autoaprobados
    t["aprobado_por"] = t["implementado_por"]
    anotar("CM-01", "AUTOAPROBADO", t["codigo"], "El mismo que implemento lo aprobo")
for t in sembrados[9:12]:     # aprobado despues de subir a produccion
    t["fecha_aprobacion"] = t["fecha_paso_produccion"] + timedelta(days=random.randint(1, 4))
    anotar("CM-01", "APROBACION_POSTERIOR", t["codigo"], "Se aprobo despues de pasar a produccion")


# ---------------------------------------------------------------- respuestas AC-02
def validar_sod():
    """Calcula los conflictos SoD reales para la lista de respuestas."""
    permisos_rol = {r[0]: set(r[4]) for r in ROLES}
    nombre_permiso = {p[0]: p[1] for p in PERMISOS}
    por_usuario = {}
    for ur in usuario_rol:
        u = usuarios[ur["usuario_id"] - 1]
        if u["estado"] == "ACTIVO":
            por_usuario.setdefault(u["username"], set()).update(permisos_rol[ur["rol_id"]])
    for username, perms in sorted(por_usuario.items()):
        for c in MATRIZ_SOD:
            if c[1] in perms and c[2] in perms:
                anotar("AC-02", "CONFLICTO_SOD", username,
                       f"{nombre_permiso[c[1]]} + {nombre_permiso[c[2]]} (riesgo {c[3]})")


validar_sod()

# ================================================================= salida
TABLAS = [
    ("rrhh_empleados", empleados),
    ("usuarios_erp", usuarios),
    ("roles", [{"rol_id": r[0], "nombre": r[1], "descripcion": r[2], "es_privilegiado": r[3]} for r in ROLES]),
    ("permisos", [{"permiso_id": p[0], "codigo": p[1], "descripcion": p[2], "modulo": p[3]} for p in PERMISOS]),
    ("rol_permiso", [{"rol_id": r[0], "permiso_id": p} for r in ROLES for p in r[4]]),
    ("usuario_rol", usuario_rol),
    ("matriz_sod", [{"conflicto_id": c[0], "permiso_a": c[1], "permiso_b": c[2], "riesgo": c[3],
                     "descripcion": c[4]} for c in MATRIZ_SOD]),
    ("tickets_cambio", tickets),
    ("log_accesos", logs),
]

carpeta = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(carpeta, "respuestas_esperadas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["control", "tipo", "registro", "detalle"])
    w.writerows(sorted(respuestas))


def resumen():
    print(f"Empleados: {len(empleados)} ({N_TEMPORALES} temporales) | Cuentas: {len(usuarios)} | "
          f"Asignaciones de rol: {len(usuario_rol)} | Tickets: {len(tickets)} | Logins: {len(logs)}")
    print("Errores sembrados (respuestas_esperadas.csv):")
    for control in ("AC-01", "AC-02", "AC-03", "AC-04", "CM-01"):
        print(f"  {control}: {sum(1 for r in respuestas if r[0] == control)}")


if "--dry-run" in sys.argv:
    os.makedirs(os.path.join(carpeta, "salida"), exist_ok=True)
    for nombre, filas in TABLAS:
        with open(os.path.join(carpeta, "salida", f"{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
            w.writeheader()
            w.writerows(filas)
    resumen()
    sys.exit(0)

import oracledb  # noqa: E402  (solo se necesita para cargar en Oracle)

with oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN) as con:
    cur = con.cursor()
    # borra en orden inverso para poder correr el script varias veces
    for nombre, _ in reversed(TABLAS):
        cur.execute(f"DELETE FROM {nombre}")
    for nombre, filas in TABLAS:
        columnas = list(filas[0].keys())
        sql = f"INSERT INTO {nombre} ({', '.join(columnas)}) VALUES ({', '.join(':' + c for c in columnas)})"
        # le dice a Oracle el tipo de cada columna (por si la primera fila trae vacios)
        tipos = {}
        for c in columnas:
            v = next((f[c] for f in filas if f[c] is not None), None)
            if isinstance(v, datetime):
                tipos[c] = oracledb.DB_TYPE_TIMESTAMP
            elif isinstance(v, date):
                tipos[c] = oracledb.DB_TYPE_DATE
            elif isinstance(v, int) or v is None:
                tipos[c] = oracledb.DB_TYPE_NUMBER
            else:
                tipos[c] = max(len(str(f[c] or "")) for f in filas) or 1
        cur.setinputsizes(**tipos)
        cur.executemany(sql, filas)
        print(f"  {nombre}: {len(filas)} filas")
    con.commit()
resumen()
print("Listo: datos cargados en Oracle.")
