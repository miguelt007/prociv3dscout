from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import requests

# Inicializar a aplicação Flask
app = Flask(__name__)

def coluna_segura(df, coluna, default=0):
"""Retorna uma série segura para colunas que podem não existir."""
return df[coluna] if coluna in df.columns else pd.Series([default] * len(df))

# 🔄 Nova função para obter dados da API ProCiv
def obter_dados_prociv():
url = "https://prociv-agserver.geomai.mai.gov.pt/arcgis/rest/services/Ocorrencias_Base/FeatureServer/0/query"
params = {
    "f": "geojson",
    "where": "0=0",
    "outFields": "*"
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    geojson = response.json()
    features = geojson.get("features", [])
    dados = [f["properties"] for f in features]

    df = pd.DataFrame(dados)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "")
    )

    if "dataocorrencia" in df.columns:
        df["dataocorrencia"] = pd.to_datetime(df["dataocorrencia"], errors="coerce")

    if "latitude" in df.columns and "longitude" in df.columns:
        df["latitude"] = df["latitude"].astype(str).str.replace(",", ".").astype(float)
        df["longitude"] = df["longitude"].astype(str).str.replace(",", ".").astype(float)

    meios = [
        "meiosterrestres", "meiosaereos", "meiosaquaticos",
        "operacionalesterrestres", "operacionaisaereos", "operacionaisaquaticos"
    ]
    for campo in meios:
        if campo in df.columns:
            df[campo] = pd.to_numeric(df[campo], errors="coerce").fillna(0)

    df["totalmeios"] = df.get("meiosterrestres", 0) + df.get("meiosaereos", 0) + df.get("meiosaquaticos", 0)
    df["totaloperacionais"] = df.get("operacionalesterrestres", 0) + df.get("operacionaisaereos", 0) + df.get("operacionaisaquaticos", 0)

    return df

except Exception as e:
    print(f"Erro ao obter dados da API ProCiv: {e}")
    return pd.DataFrame()        
# Rota principal
@app.route("/", methods=["GET", "POST"])
def index():
df = obter_dados_prociv()

# Filtros
distrito = request.form.get("distrito", "Todos")
estado = request.form.get("estado", "Todos")

# Verificação de dados
if df.empty:
    df_filtrado = pd.DataFrame()
    distritos = []
    estados = []
else:
    df_filtrado = df.copy()
    if distrito != "Todos" and "distrito" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["distrito"] == distrito]
    if estado != "Todos" and "estadoocorrencia" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["estadoocorrencia"] == estado]

    distritos = sorted(df["distrito"].dropna().unique()) if "distrito" in df.columns else []
    estados = sorted(df["estadoocorrencia"].dropna().unique()) if "estadoocorrencia" in df.columns else []

# Funções defensivas
def get_safe_sum(df, col):
    return int(df[col].sum()) if col in df.columns else 0

def get_safe_count(df, col, value):
    return df[df[col] == value].shape[0] if col in df.columns else 0

# Métricas
total_ocorrencias = len(df_filtrado)
total_operacionais = get_safe_sum(df_filtrado, "operacionais")
total_veiculos = (
    get_safe_sum(df_filtrado, "numeromeiosterrestresenvolvidos") +
    get_safe_sum(df_filtrado, "numeromeiosaereosenvolvidos") +
    get_safe_sum(df_filtrado, "numeromeiosaquaticos")
)
total_aereos = get_safe_sum(df_filtrado, "numeromeiosaereosenvolvidos")
total_meios_aquaticos = get_safe_sum(df_filtrado, "numeromeiosaquaticos")
total_incendios = get_safe_count(df_filtrado, "natureza", "Incêndio")

# Gráfico 1: Meios por ocorrência
if "dataocorrencia" in df_filtrado.columns and "totalmeios" in df_filtrado.columns:
    grafico = px.bar(
        df_filtrado,
        x="dataocorrencia",
        y="totalmeios",
        color="distrito" if "distrito" in df_filtrado.columns else None,
        title="Meios Envolvidos por Ocorrência"
    )
    grafico_html = grafico.to_html(full_html=False)
else:
    grafico_html = "<div>Gráfico 1 indisponível</div>"

# Gráfico 2: Total por distrito
if "distrito" in df_filtrado.columns and "totalmeios" in df_filtrado.columns:
    df_barras = df_filtrado.groupby("distrito", as_index=False)["totalmeios"].sum()
    df_barras = df_barras[df_barras["totalmeios"] > 0]

    grafico2 = px.bar(
        df_barras,
        x="distrito",
        y="totalmeios",
        title="Total de Meios por Distrito",
        text="totalmeios"
    )
    grafico2.update_traces(textposition="outside")
    grafico2.update_layout(yaxis=dict(range=[0, df_barras["totalmeios"].max() * 1.2]))
    grafico2_html = grafico2.to_html(full_html=False)
else:
    grafico2_html = "<div>Gráfico 2 indisponível</div>"

# Mapa
if {"latitude", "longitude", "natureza"}.issubset(df_filtrado.columns):
    mapa = px.scatter_mapbox(
        df_filtrado,
        lat="latitude",
        lon="longitude",
        hover_name="natureza",
        hover_data=["estadoocorrencia", "distrito", "concelho"],
        color="estadoocorrencia" if "estadoocorrencia" in df_filtrado.columns else None,
        zoom=6,
        height=750
    )
    mapa.update_layout(mapbox_style="open-street-map")
    mapa_html = mapa.to_html(full_html=False)
else:
    mapa_html = "<div>Mapa indisponível</div>"

# Renderizar template
return render_template(
    "index.html",
    mapa=mapa_html,
    grafico=grafico_html,
    grafico2=grafico2_html,
    distritos=distritos,
    estados=estados,
    distrito_selecionado=distrito,
    estado_selecionado=estado,
    total_ocorrencias=total_ocorrencias,
    total_operacionais=total_operacionais,
    total_veiculos=total_veiculos,
    total_aereos=total_aereos,
    total_meios_aquaticos=total_meios_aquaticos,
    total_incendios=total_incendios
)
# 🚀 Executar a aplicação
if __name__ == "__main__":
  app.run(debug=True)
