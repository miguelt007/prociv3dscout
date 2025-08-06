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
    df["dataocorrencia"] = pd.to_datetime(df["DataOcorrencia"], errors="coerce")
    df["natureza"] = df["Natureza"]
    df["distrito"] = df["Distrito"]
    df["concelho"] = df["Concelho"]
    df["estadoocorrencia"] = df["EstadoOcorrencia"]
    df["totalmeios"] = pd.to_numeric(df["NumeroMeiosTerrestresEnvolvidos"], errors="coerce").fillna(0).astype(int)
    df["totaloperacionais"] = pd.to_numeric(df["Operacionais"], errors="coerce").fillna(0).astype(int)

    # 📊 Dados para gráfico
    grafico_df = df.groupby("distrito").size().sort_values(ascending=False)
    grafico_labels = grafico_df.index.tolist()
    grafico_dados = grafico_df.values.tolist()

    # 📋 Dados para cartões
    total_ocorrencias = len(df)
    total_operacionais = df["totaloperacionais"].sum()
    total_meios = df["totalmeios"].sum()

    # 🧾 Dados para tabela
    df_filtrado = df[["dataocorrencia", "natureza", "distrito", "concelho", "estadoocorrencia", "totalmeios", "totaloperacionais"]].dropna()

    return render_template(
        "index.html",
        grafico_labels=grafico_labels,
        grafico_dados=grafico_dados,
        ocorrencias=df_filtrado.to_dict(orient="records"),
        total_ocorrencias=total_ocorrencias,
        total_operacionais=total_operacionais,
        total_meios=total_meios
    )

if __name__ == "__main__":
    app.run(debug=True)
