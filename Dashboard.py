import streamlit as st
import requests
import pandas as pd
import plotly.express as px


st.set_page_config(layout="wide")


def formata_numero(valor, prefixo=""):
    for unidade in ["", "mil"]:
        if valor < 1000:
            return f"{prefixo} {valor:.2f} {unidade}"
        valor /= 1000

    return f"{prefixo} {valor:.2f} milhões"


st.title("DASHBOARD DE VENDAS :shopping_trolley:")

## Filtros Regiões
regioes = ["Brasil", "Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"]
st.sidebar.title("Filtros")
regiao = st.sidebar.selectbox("Região", regioes)
if regiao == "Brasil":
    regiao = ""

## Filtros anos
todos_anos = st.sidebar.checkbox("Dados de todo o período", value=True)
if todos_anos:
    ano = ""
else:
    ano = st.sidebar.slider("Ano", 2020, 2023)

## Dados
query_string = {"regiao": regiao.lower(), "ano": ano}
url = "https://labdados.com/produtos"
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados["Data da Compra"] = pd.to_datetime(dados["Data da Compra"], format="%d/%m/%Y")

## Filtro vendedores
filtro_vendedores = st.sidebar.multiselect("Vendedores", dados["Vendedor"].unique())
if filtro_vendedores:
    dados = dados[dados["Vendedor"].isin(filtro_vendedores)]

## Tabelas Receitas
receita_estados = dados.groupby(["Local da compra", "lat", "lon"], as_index=False)[
    ["Preço"]
].sum()
receita_estados.sort_values("Preço", ascending=False, inplace=True)

receita_mensal = (
    dados.set_index("Data da Compra")
    .groupby(pd.Grouper(freq="M"))["Preço"]
    .sum()
    .reset_index()
)
receita_mensal["Ano"] = receita_mensal["Data da Compra"].dt.year
receita_mensal["Mês"] = receita_mensal["Data da Compra"].dt.month_name()

receita_categorias = (
    dados.groupby("Categoria do Produto")[["Preço"]]
    .sum()
    .sort_values("Preço", ascending=False)
)

## Tabelas Qtd Vendas
qtd_vendas = dados.groupby(["Local da compra", "lat", "lon"], as_index=False)[
    ["Produto"]
].count()
qtd_vendas.sort_values("Produto", ascending=False, inplace=True)

vendas_mensais = (
    dados.set_index("Data da Compra")
    .groupby(pd.Grouper(freq="M"))["Produto"]
    .count()
    .reset_index()
)
vendas_mensais["Ano"] = vendas_mensais["Data da Compra"].dt.year
vendas_mensais["Mês"] = vendas_mensais["Data da Compra"].dt.month_name()

vendas_produtos = (
    dados.groupby("Categoria do Produto")[["Preço"]]
    .count()
    .sort_values("Preço", ascending=False)
)

## Tabela de Vendedores
vendedores = pd.DataFrame(dados.groupby("Vendedor")["Preço"].agg(["sum", "count"]))
vendedores_receita = vendedores[["sum"]].sort_values("sum", ascending=False)
vendedores_vendas = vendedores[["count"]].sort_values("count", ascending=False)

## Gráficos Receitas
fig_mapa_receita = px.scatter_geo(
    receita_estados,
    lat="lat",
    lon="lon",
    scope="south america",
    size="Preço",
    template="seaborn",
    hover_name="Local da compra",
    hover_data={"lat": False, "lon": False},
    title="Receita por Estado",
)

fig_receita_mensal = px.line(
    receita_mensal,
    x="Mês",
    y="Preço",
    markers=True,
    range_y=(0, receita_mensal.max()),
    color="Ano",
    line_dash="Ano",
    title="Receita mensal",
)

fig_receita_mensal.update_layout(yaxis_title="Receita")

fig_receita_estados = px.bar(
    receita_estados.head(),
    x="Local da compra",
    y="Preço",
    text_auto=True,
    title="Top estados",
)
fig_receita_estados.update_layout(yaxis_title="Receita")

fig_receita_categorias = px.bar(
    receita_categorias,
    text_auto=True,
    title="Receita por categoria",
)
fig_receita_categorias.update_layout(yaxis_title="Receita")

## Gráficos qtd Vendas
fig_mapa_vendas = px.scatter_geo(
    qtd_vendas,
    lat="lat",
    lon="lon",
    scope="south america",
    size="Produto",
    template="seaborn",
    hover_name="Local da compra",
    hover_data={"lat": False, "lon": False},
    title="Quantidade de vendas por estado",
)

fig_qtd_vendas_estados = px.bar(
    qtd_vendas.head(),
    x="Local da compra",
    y="Produto",
    text_auto=True,
    title="Top estados",
)
fig_receita_estados.update_layout(yaxis_title="Qtd Vendas")

fig_vendas_mensais = px.line(
    vendas_mensais,
    x="Mês",
    y="Produto",
    markers=True,
    range_y=(0, vendas_mensais.max()),
    color="Ano",
    line_dash="Ano",
    title="Vendas mensais",
)

fig_vendas_mensais.update_layout(yaxis_title="Vendas mensais")

fig_vendas_produtos = px.bar(
    vendas_produtos,
    text_auto=True,
    title="vendas por categorias de produtos",
)
fig_vendas_produtos.update_layout(yaxis_title="Produtos")


## Visualização no Streamlit
aba1, aba2, aba3 = st.tabs(["Receita", "Quantidade de vendas", "Vendedores"])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), "R$"))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)

    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), "R$"))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_qtd_vendas_estados, use_container_width=True)

    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensais, use_container_width=True)
        st.plotly_chart(fig_vendas_produtos, use_container_width=True)

with aba3:
    qtd_vendedores = st.number_input("Quantidade de vendedores", 2, 10, 5)
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), "R$"))
        fig_vendedores_receita = px.bar(
            vendedores_receita.head(qtd_vendedores),
            x="sum",
            y=vendedores_receita.head(qtd_vendedores).index,
            text_auto=True,
            title=f"Top {qtd_vendedores} vendedores (receita)",
        )
        st.plotly_chart(fig_vendedores_receita, use_container_width=True)

    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0]))
        fig_vendedores_venda = px.bar(
            vendedores_vendas.head(qtd_vendedores),
            x="count",
            y=vendedores_vendas.head(qtd_vendedores).index,
            text_auto=True,
            title=f"Top {qtd_vendedores} vendedores (Vendas)",
        )
        st.plotly_chart(fig_vendedores_venda, use_container_width=True)
