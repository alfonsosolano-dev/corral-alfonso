import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import plotly.express as px
import os

# =================== CONFIGURACIÓN ===================
st.set_page_config(page_title="Corral Maestro PRO PLUS", page_icon="🐓", layout="wide")
st.title("🐔 Corral Maestro PRO PLUS")

# =================== BASE DE DATOS ===================
DB_PATH = Path("corral_maestro_pro.db")

# Crear base de datos si no existe
if not DB_PATH.exists():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS lotes(
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, especie TEXT, raza TEXT,
        cantidad INTEGER, edad_inicial INTEGER, precio_ud REAL, estado TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS produccion(
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, lote INTEGER, huevos INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS gastos(
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, categoria TEXT, concepto TEXT,
        cantidad REAL, kilos_pienso REAL DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS ventas(
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, tipo_venta TEXT,
        concepto TEXT, cantidad REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS salud(
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, lote INTEGER, descripcion TEXT,
        proxima_fecha TEXT, estado TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bajas(
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, lote INTEGER, cantidad INTEGER,
        motivo TEXT)""")
    conn.commit()
    conn.close()
    st.success("✔ Base de datos creada automáticamente")

# =================== FUNCIONES ===================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def cargar(tabla):
    conn = get_conn()
    try: return pd.read_sql(f"SELECT * FROM {tabla}", conn)
    except: return pd.DataFrame()
    finally: conn.close()

def eliminar_reg(tabla, id_reg):
    conn = get_conn()
    conn.execute(f"DELETE FROM {tabla} WHERE id = ?", (id_reg,))
    conn.commit()
    conn.close()

# =================== CARGA DE DATOS ===================
lotes = cargar("lotes")
produccion = cargar("produccion")
gastos = cargar("gastos")
ventas = cargar("ventas")
bajas = cargar("bajas")
salud = cargar("salud")

# =================== CÁLCULOS ===================
def consumo_diario_total():
    consumo = 0
    if not lotes.empty:
        for _, r in lotes.iterrows():
            b = bajas[bajas['lote']==r['id']]['cantidad'].sum() if not bajas.empty else 0
            vivas = r['cantidad'] - b
            f = 0.120 if r['especie']=="Gallinas" else 0.150 if r['especie']=="Pollos" else 0.030
            consumo += vivas*f
    return consumo

t_kg = gastos["kilos_pienso"].sum() if not gastos.empty else 0
consumo = consumo_diario_total()
dias_pienso = t_kg / consumo if consumo>0 else 0

t_v = ventas[ventas['tipo_venta']=='Venta Cliente']['cantidad'].sum() if not ventas.empty else 0
t_g = gastos['cantidad'].sum() if not gastos.empty else 0
balance = t_v - t_g

t_huevos = produccion["huevos"].sum() if not produccion.empty else 0
total_gallinas = lotes["cantidad"].sum() if not lotes.empty else 0
total_bajas = bajas["cantidad"].sum() if not bajas.empty else 0
vivas = total_gallinas - total_bajas
huevos_gallina = t_huevos / vivas if vivas>0 else 0

# =================== ALERTAS ===================
if dias_pienso < 3: st.error("⚠️ Queda pienso para menos de 3 días")
elif dias_pienso < 7: st.warning("⚠️ Pienso para menos de una semana")
else: st.info("✅ Pienso suficiente")

if not produccion.empty:
    media = produccion["huevos"].mean()
    ultimo = produccion.iloc[-1]["huevos"]
    if ultimo < media*0.7: st.warning(f"🥚 Producción baja: {ultimo} huevos vs media {media:.1f}")

ranking = produccion.groupby("lote")["huevos"].sum() if not produccion.empty else pd.Series()
for lote, total in ranking.items():
    info = lotes[lotes["id"]==lote]
    nombre = f"{info['raza'].values[0]} ({lote})" if not info.empty else str(lote)
    if total < 50: st.warning(f"⚠️ Lote {nombre} con baja producción ({total} huevos)")

# =================== MENÚ ===================
menu = st.sidebar.selectbox("MENÚ PRINCIPAL", [
    "🏠 Dashboard","🐣 Alta de Lotes","📊 Ranking Lotes",
    "📈 Predicción Huevos","📜 Histórico","💾 Backup"
])

# =================== DASHBOARD ===================
if menu=="🏠 Dashboard":
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Stock Pienso", f"{dias_pienso:.1f} días")
    c2.metric("Balance", f"{balance:.2f} €")
    c3.metric("Huevos Totales", t_huevos)
    c4.metric("Huevos por Gallina", round(huevos_gallina,2))

    if not produccion.empty:
        df = produccion.groupby("fecha")["huevos"].sum().reset_index()
        fig = px.line(df, x="fecha", y="huevos", title="Producción diaria de huevos")
        st.plotly_chart(fig, use_container_width=True)

    if not gastos.empty:
        df = gastos.groupby("categoria")["cantidad"].sum().reset_index()
        fig = px.bar(df, x="categoria", y="cantidad", title="Gastos por categoría")
        st.plotly_chart(fig, use_container_width=True)

# =================== ALTA DE LOTES ===================
elif menu=="🐣 Alta de Lotes":
    st.header("🐣 Registrar Nuevo Lote")
    with st.form("alta_lote"):
        f = st.date_input("Fecha de ingreso")
        esp = st.selectbox("Especie", ["Gallinas","Pollos","Codornices"])
        razas = {"Gallinas":["Roja","Blanca","Chocolate"],
                 "Pollos":["Blanco Engorde","Campero"],
                 "Codornices":["Codorniz"]}
        rz = st.selectbox("Raza", razas[esp])
        cant = st.number_input("Cantidad", min_value=1, step=1)
        edad_i = st.number_input("Edad inicial", min_value=0, step=1)
        if st.form_submit_button("Guardar"):
            conn = get_conn()
            conn.execute("""INSERT INTO lotes (fecha, especie, raza, cantidad, edad_inicial, estado)
                            VALUES (?,?,?,?,?, 'Activo')""",
                         (f.strftime("%d/%m/%Y"), esp, rz, cant, edad_i))
            conn.commit(); conn.close()
            st.success("✔ Lote registrado correctamente")
            st.experimental_rerun()

# =================== RANKING DE LOTES ===================
elif menu=="📊 Ranking Lotes":
    st.header("📊 Lotes con más huevos")
    if not produccion.empty:
        rank = produccion.groupby("lote")["huevos"].sum().sort_values(ascending=False).reset_index()
        st.dataframe(rank)
    else:
        st.info("No hay datos de producción.")

# =================== PREDICCIÓN HUEVOS ===================
elif menu=="📈 Predicción Huevos":
    st.header("📈 Predicción simple (media móvil 7 días)")
    if not produccion.empty:
        df = produccion.copy()
        df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
        df = df.groupby("fecha_dt")["huevos"].sum().reset_index()
        df["media_movil"] = df["huevos"].rolling(7).mean()
        st.line_chart(df.set_index("fecha_dt")[["huevos","media_movil"]])
    else:
        st.info("No hay datos de producción.")

# =================== HISTÓRICO ===================
elif menu=="📜 Histórico":
    st.header("📜 Histórico de registros")
    tabla = st.selectbox("Selecciona tabla", ["lotes","produccion","gastos","ventas","bajas","salud"])
    df = cargar(tabla)
    st.dataframe(df)
    id_b = st.number_input("ID a borrar", min_value=1, step=1)
    if st.button("Borrar registro"):
        if id_b in df["id"].values:
            eliminar_reg(tabla, id_b)
            st.success("Registro eliminado")
            st.experimental_rerun()

# =================== BACKUP ===================
elif menu=="💾 Backup":
    st.header("💾 Copia de seguridad")
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            st.download_button("📥 Descargar Base de Datos", f, file_name="corral_maestro_pro.db")
    up = st.file_uploader("📤 Restaurar Base de Datos", type="db")
    if up:
        with open(DB_PATH, "wb") as f:
            f.write(up.getbuffer())
        st.success("Base de datos restaurada correctamente")
        st.experimental_rerun()
