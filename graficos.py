import streamlit as st
import pandas as pd

def grafico_produccion(produccion):
    if not produccion.empty:
        df = produccion.groupby("fecha")["huevos"].sum().reset_index()
        st.line_chart(df.set_index("fecha"))

def grafico_gastos_categoria(gastos):
    if not gastos.empty:
        df = gastos.groupby("categoria")["cantidad"].sum()
        st.bar_chart(df)
