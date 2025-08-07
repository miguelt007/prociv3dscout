from flask import Flask, render_template
import requests
import pandas as pd
import plotly.express as px

app = Flask(__name__)

@app.route("/")
def index():
    # 🔗 Endpoint da API ProCiv
    url = "https://prociv-agserver.geomai.mai.gov.pt/arcgis/rest/services/Ocorrencias_Base/FeatureServer/0/query"
    params = {
        "f": "geojson",
        "where": "0=0",
        "outFields": "*"
    }
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        geojson = response.json()
    except requests.exceptions.RequestException as e:
        print("Erro ao obter dados da API ProCiv:", e)
        geojson = {"features": []}

    # 📦 Extrair dados para DataFrame
    features = geojson.get("features", [])
    dados = [f["properties"] for f in features]
    df = pd.DataFrame(dados)

    # 🧹 Limpeza e tratamento
    df["dataocorrencia"] = pd.to_datetime(df["DataInicioOcorrencia"], errors="coerce")
    df["natureza"] = df["Natureza"]
    df["csrepc"] = df["CSREPC"]  # Substitui Distrito por Sub Região
    df["concelho"] = df["Concelho"]
    df["estadoocorrencia"] = df["EstadoOcorrencia"]
    df["totalmeios"] = pd.to_numeric(df["NumeroMeiosTerrestresEnvolvidos"], errors="coerce").fillna(0).astype(int)
    df["totaloperacionais"] = pd.to_numeric(df["Operacionais"], errors="coerce").fillna(0).astype(int)

    # 🏷️ Renomear para exibição
    df.rename(columns={"csrepc": "Sub Região"}, inplace=True)

    # 📊 Dados para gráfico
    grafico_df = df.groupby("Sub Região").size().sort_values(ascending=False)
    grafico_labels = grafico_df.index.tolist()
    grafico_dados = grafico_df.values.tolist()

    # 📋 Dados para cartões
    total_ocorrencias = len(df)
    total_operacionais = df["totaloperacionais"].sum()
    total_meios = df["totalmeios"].sum()
    total_meios_aereos = pd.to_numeric(df["NumeroMeiosAereosEnvolvidos"], errors="coerce").fillna(0).astype(int).sum()

    # 🧾 Dados para tabela
    df_filtrado = df[[
        "dataocorrencia", "natureza", "Sub Região", "concelho",
        "estadoocorrencia", "totalmeios", "totaloperacionais"
    ]].fillna("Desconhecido")

    geojson_data = geojson  # já está em formato dict

    return render_template(
        "index.html",
        grafico_labels=grafico_labels,
        grafico_dados=grafico_dados,
        geojson_data=geojson_data,
        ocorrencias=df_filtrado.to_dict(orient="records"),
        total_ocorrencias=total_ocorrencias,
        total_operacionais=total_operacionais,
        total_meios=total_meios,
        total_meios_aereos=total_meios_aereos
    )

if __name__ == "__main__":
    app.run(debug=True)
