import streamlit as st
from datetime import datetime
from database import get_conn, cargar, eliminar_reg
from calculos import dias_pienso_lotes, balance_total, huevos_por_gallina, media_movil_produccion, ranking_lotes, informe_mensual
from graficos import grafico_produccion, grafico_gastos_categoria
from utils import alertas_pienso, alertas_produccion, alertas_lote
import plotly.express as px

# =================== CONFIGURACIÓN ===================
st.set_page_config(page_title="Corral Maestro PRO PLUS", page_icon="🐓", layout="wide")
st.title("🐔 Corral Maestro PRO PLUS")

# =================== CARGA DE DATOS ===================
lotes = cargar("lotes")
produccion = cargar("produccion")
gastos = cargar("gastos")
ventas = cargar("ventas")
bajas = cargar("bajas")
salud = cargar("salud")

# =================== CÁLCULOS ===================
dias_pienso = dias_pienso_lotes(lotes, bajas, gastos)
balance = balance_total(ventas, gastos)
t_huevos = produccion["huevos"].sum() if not produccion.empty else 0
huevos_gallina = huevos_por_gallina(produccion, lotes, bajas)

# =================== ALERTAS ===================
alertas_pienso(dias_pienso)
alertas_produccion(produccion)
alertas_lote(produccion, lotes, bajas)

# =================== MENÚ ===================
menu = st.sidebar.selectbox("MENÚ PRINCIPAL", [
    "🏠 Dashboard",
    "🐣 Alta de Lotes",
    "📊 Ranking Lotes",
    "📈 Predicción Huevos",
    "📜 Histórico",
    "💾 Backup",
    "🧾 Informe Mensual"
])

# =================== DASHBOARD ===================
if menu == "🏠 Dashboard":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stock Pienso", f"{dias_pienso:.1f} días")
    c2.metric("Balance", f"{balance:.2f} €")
    c3.metric("Huevos Totales", t_huevos)
    c4.metric("Huevos por Gallina", round(huevos_gallina, 2))

    st.subheader("📊 Producción Últimos 30 días")
    grafico_produccion(produccion)

    st.subheader("💸 Gastos por Categoría")
    grafico_gastos_categoria(gastos)

# =================== RANKING LOTES ===================
elif menu == "📊 Ranking Lotes":
    st.subheader("🏆 Ranking de Lotes por Producción")
    df_rank = ranking_lotes(produccion)
    st.dataframe(df_rank)

# =================== PREDICCIÓN ===================
elif menu == "📈 Predicción Huevos":
    st.subheader("🔮 Predicción de Huevos (Media Móvil)")
    df_pred = media_movil_produccion(produccion)
    if not df_pred.empty:
        fig = px.line(df_pred, x="fecha", y=["huevos", "media_movil"], labels={"value":"Huevos","fecha":"Fecha"})
        st.plotly_chart(fig, use_container_width=True)

# =================== INFORME MENSUAL ===================
elif menu == "🧾 Informe Mensual":
    st.subheader("🧾 Informe Mensual")
    df_informe = informe_mensual(produccion, gastos, ventas)
    st.dataframe(df_informe)
    if not df_informe.empty:
        df_informe.to_excel("informe_mensual.xlsx")
        with open("informe_mensual.xlsx","rb") as f:
            st.download_button("📥 Descargar Informe", f, file_name="informe_mensual.xlsx")

# =================== ALTA DE LOTES ===================
elif menu == "🐣 Alta de Lotes":
    st.subheader("🐣 Registrar Lote")
    with st.form("f_lote"):
        fecha = st.date_input("Fecha")
        especie = st.selectbox("Especie", ["Gallinas","Pollos","Codornices"])
        razas = {"Gallinas":["Roja","Blanca","Chocolate"],
                 "Pollos":["Blanco Engorde","Campero"],
                 "Codornices":["Codorniz"]}
        raza = st.selectbox("Raza", razas[especie])
        cantidad = st.number_input("Cantidad", min_value=1, value=10)
        edad_inicial = st.number_input("Edad inicial", min_value=0)
        if st.form_submit_button("✅ Guardar"):
            conn = get_conn()
            conn.execute(
                "INSERT INTO lotes (fecha, especie, raza, cantidad, edad_inicial, estado) VALUES (?,?,?,?,?,'Activo')",
                (fecha.strftime("%d/%m/%Y"), especie, raza, cantidad, edad_inicial)
            )
            conn.commit(); conn.close()
            st.success("✔️ Lote registrado")
            st.experimental_rerun()

# =================== HISTÓRICO ===================
elif menu == "📜 Histórico":
    st.subheader("📜 Histórico de Datos")
    tabla = st.selectbox("Tabla", ["produccion","gastos","ventas","salud","bajas","lotes"])
    df_h = cargar(tabla)
    
    # --- FILTRO POR FECHA ---
    if not df_h.empty and "fecha" in df_h.columns:
        fecha_inicio = st.date_input("Fecha inicio", value=datetime(2023,1,1))
        fecha_fin = st.date_input("Fecha fin", value=datetime.now())
        df_h["fecha_dt"] = pd.to_datetime(df_h["fecha"], format="%d/%m/%Y")
        df_h = df_h[(df_h["fecha_dt"] >= pd.to_datetime(fecha_inicio)) & 
                    (df_h["fecha_dt"] <= pd.to_datetime(fecha_fin))]
        df_h = df_h.drop(columns=["fecha_dt"])
    
    st.dataframe(df_h, use_container_width=True)
    id_borrar = st.number_input("ID a borrar", min_value=1, step=1)
    if st.button("❌ Borrar Registro"):
        if id_borrar in df_h["id"].values:
            eliminar_reg(tabla, id_borrar)
            st.success("Registro eliminado")
            st.experimental_rerun()

# =================== BACKUP ===================
elif menu == "💾 Backup":
    st.subheader("💾 Backup Base de Datos")
    from pathlib import Path
    DB_PATH = Path("corral_maestro_pro.db")
    if DB_PATH.exists():
        with open(DB_PATH, "rb") as f:
            st.download_button("📥 Descargar .db", f, file_name="corral_maestro_pro.db")
    up = st.file_uploader("📤 Restaurar .db", type="db")
    if up:
        with open(DB_PATH, "wb") as f:
            f.write(up.getbuffer())
        st.success("Base de datos restaurada")
        st.experimental_rerun()
