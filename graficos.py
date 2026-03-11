import streamlit as st
import pandas as pd
import plotly.express as px

def grafico_produccion(produccion):
    if not produccion.empty:
        df = produccion.groupby("fecha")["huevos"].sum().reset_index()
        fig = px.line(df, x="fecha", y="huevos", title="Producción diaria de huevos")
        st.plotly_chart(fig, use_container_width=True)

def grafico_gastos_categoria(gastos):
    if not gastos.empty:
        df = gastos.groupby("categoria")["cantidad"].sum().reset_index()
        fig = px.bar(df, x="categoria", y="cantidad", title="Gastos por categoría")
        st.plotly_chart(fig, use_container_width=True)
