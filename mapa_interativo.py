import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
import plotly.express as px
from folium import CustomIcon
import os

# === Dados ===
df_original = pd.read_excel('Pontos_Concorrencia_Curitiba.xlsx')
df_coords = pd.read_excel('lat-long.xlsx')
df_final = df_original.merge(df_coords[['enum', 'lat', 'lon']], left_on='numero', right_on='enum')

df_final.dropna(subset=['lat', 'lon'], inplace=True)

# === Cores para fallback
lista_cores = [
    "blue", "green", "red", "orange", "purple", "darkred", "darkblue",
    "cadetblue", "lightgray", "gray", "beige", "pink", "lightgreen", "black"
]
empresas_unicas = sorted(df_final['Empresa'].dropna().unique())
cores_empresa = {empresa: lista_cores[i % len(lista_cores)] for i, empresa in enumerate(empresas_unicas)}

# === Título e filtros
st.title("📌 Mapa Interativo Curitiba")

st.sidebar.title("Filtros")
nome_busca = st.sidebar.text_input("🔍 Buscar Nome do Ponto:")
empresas = st.sidebar.multiselect("🏢 Empresa:", options=empresas_unicas, default=empresas_unicas)

modo_mapa = st.sidebar.radio("👁️ Exibir no mapa:", options=["Clusters com pins/logos", "Heatmap", "Ambos"], index=2)
usar_cluster = st.sidebar.radio("📍 Agrupar pins automaticamente?", ["Sim (Cluster)", "Não (Mostrar todos)"], index=0)


categorias = st.sidebar.multiselect("📦 Categoria:", options=sorted(df_final['Categoria'].dropna().unique()), default=sorted(df_final['Categoria'].dropna().unique()))
bairros = st.sidebar.multiselect("🏘️ Bairro:", options=sorted(df_final['Bairro'].dropna().unique()), default=sorted(df_final['Bairro'].dropna().unique()))


# === Aplicação dos filtros
df_filtrado = df_final[
    (df_final['Empresa'].isin(empresas)) &
    (df_final['Categoria'].isin(categorias)) &
    (df_final['Bairro'].isin(bairros))
]
if nome_busca:
    df_filtrado = df_filtrado[df_filtrado['Nome do Ponto'].str.contains(nome_busca, case=False, na=False)]

# === Mapa base
mapa = folium.Map(location=[-25.4284, -49.2733], zoom_start=12)

# === Pins
if modo_mapa in ["Clusters com pins/logos", "Ambos"]:
    if usar_cluster == "Sim (Cluster)":
        cluster = MarkerCluster().add_to(mapa)
        target_layer = cluster
    else:
        target_layer = mapa

    for _, ponto in df_filtrado.iterrows():
        empresa = ponto['Empresa']
        nome_img = empresa.lower().strip().replace(" ", "").replace("í", "i").replace("é", "e") + ".png"
        caminho_img = f"logos/{nome_img}"

        if os.path.exists(caminho_img):
            icon = CustomIcon(caminho_img, icon_size=(30, 30))
        else:
            icon = folium.Icon(color=cores_empresa.get(empresa, 'gray'), icon='info-sign')

        folium.Marker(
            location=[ponto['lat'], ponto['lon']],
            popup=f"<b>{ponto['Nome do Ponto']}</b><br>{empresa}<br>{ponto['Categoria']}<br>{ponto['Endereço Completo']}",
            icon=icon
        ).add_to(target_layer)

# === Heatmap
if modo_mapa in ["Heatmap", "Ambos"]:
    heat_data = df_filtrado[['lat', 'lon']].dropna().values.tolist()
    if heat_data:
        HeatMap(heat_data, radius=15).add_to(mapa)

# === Exibir mapa
st.subheader("🗺️ Mapa Interativo")
st_folium(mapa, width=1000, height=600)

# === Estatísticas
st.subheader("📊 Estatísticas dos Pontos Filtrados")
col1, col2 = st.columns(2)

with col1:
    contagem_empresas = df_filtrado['Empresa'].value_counts().reset_index()
    contagem_empresas.columns = ['Empresa', 'Quantidade']
    fig_empresas = px.bar(contagem_empresas, x='Empresa', y='Quantidade', color='Empresa', title='Distribuição por Empresa')
    st.plotly_chart(fig_empresas, use_container_width=True)

with col2:
    contagem_categorias = df_filtrado['Categoria'].value_counts().reset_index()
    contagem_categorias.columns = ['Categoria', 'Quantidade']
    fig_categorias = px.pie(contagem_categorias, names='Categoria', values='Quantidade', title='Distribuição por Categoria')
    st.plotly_chart(fig_categorias, use_container_width=True)

# === Top Bairros
st.subheader("🏘️ Top Bairros com Mais Pontos")
contagem_bairros = df_filtrado['Bairro'].value_counts().reset_index()
contagem_bairros.columns = ['Bairro', 'Quantidade']
fig_bairros = px.bar(contagem_bairros.sort_values('Quantidade', ascending=False).head(15), x='Bairro', y='Quantidade', title='Top 15 Bairros com Mais Pontos', color='Quantidade', color_continuous_scale='Blues')
st.plotly_chart(fig_bairros, use_container_width=True)
