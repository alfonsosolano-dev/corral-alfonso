import pandas as pd

def consumo_diario_total(lotes, bajas):
    consumo = 0
    if not lotes.empty:
        for _, r in lotes.iterrows():
            b = bajas[bajas['lote']==r['id']]['cantidad'].sum() if not bajas.empty else 0
            vivas = r['cantidad'] - b
            f = 0.120 if r['especie']=="Gallinas" else 0.150 if r['especie']=="Pollos" else 0.030
            consumo += vivas*f
    return consumo

def dias_pienso_lotes(lotes, bajas, gastos):
    t_kg = gastos["kilos_pienso"].sum() if not gastos.empty else 0
    consumo = consumo_diario_total(lotes, bajas)
    return t_kg / consumo if consumo>0 else 0

def balance_total(ventas, gastos):
    t_v = ventas[ventas['tipo_venta']=='Venta Cliente']['cantidad'].sum() if not ventas.empty else 0
    t_g = gastos['cantidad'].sum() if not gastos.empty else 0
    return t_v - t_g

def huevos_por_gallina(produccion, lotes, bajas):
    total_huevos = produccion["huevos"].sum() if not produccion.empty else 0
    total_gallinas = lotes["cantidad"].sum() if not lotes.empty else 0
    total_bajas = bajas["cantidad"].sum() if not bajas.empty else 0
    vivas = total_gallinas - total_bajas
    return total_huevos/vivas if vivas>0 else 0

# ================= Predicción =================
def media_movil_produccion(produccion, dias=7):
    if produccion.empty:
        return pd.DataFrame()
    df = produccion.copy()
    df["media_movil"] = df["huevos"].rolling(dias).mean()
    return df

# ================= Ranking de Lotes =================
def ranking_lotes(produccion):
    if produccion.empty:
        return pd.DataFrame()
    return produccion.groupby("lote")["huevos"].sum().sort_values(ascending=False).reset_index()

# ================= Informe mensual =================
def informe_mensual(produccion, gastos, ventas):
    if produccion.empty and gastos.empty and ventas.empty:
        return pd.DataFrame()
    df = pd.DataFrame()
    # Producción mensual
    if not produccion.empty:
        prod_mes = produccion.copy()
        prod_mes["mes"] = pd.to_datetime(prod_mes["fecha"], format="%d/%m/%Y").dt.to_period("M")
        df["Produccion"] = prod_mes.groupby("mes")["huevos"].sum()
    # Gastos mensuales
    if not gastos.empty:
        gastos_mes = gastos.copy()
        gastos_mes["mes"] = pd.to_datetime(gastos_mes["fecha"], format="%d/%m/%Y").dt.to_period("M")
        df["Gastos"] = gastos_mes.groupby("mes")["cantidad"].sum()
    # Ventas mensuales
    if not ventas.empty:
        ventas_mes = ventas.copy()
        ventas_mes["mes"] = pd.to_datetime(ventas_mes["fecha"], format="%d/%m/%Y").dt.to_period("M")
        df["Ventas"] = ventas_mes.groupby("mes")["cantidad"].sum()
    return df.fillna(0)
