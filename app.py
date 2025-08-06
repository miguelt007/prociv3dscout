from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import requests

# Inicializar a aplicação Flask
app = Flask(__name__)

# Função para obter e preparar os dados
def obter_dados():
    # Exemplo: API de dados fictícios ou pode ser substituído por um CSV local
    url = "https://3pscoutsteste.abranco.pt/api/ANEPCAPI/GetPointsGetOcorrenciasActivasLista"  # ⚠️ Substitui por uma URL real se tiveres uma API
    try:
        response = requests.get(url)
        response.raise_for_status()
        dados_json = response.json()

        df = pd.DataFrame(dados_json)

        # ✅ Correções com os teus nomes de campo
        df["DataOcorrencia"] = pd.to_datetime(df["DataOcorrencia"], format="%d-%m-%Y %H:%M:%S")
        df["Latitude"] = df["Latitude"].str.replace(",", ".").astype(float)
        df["Longitude"] = df["Longitude"].str.replace(",", ".").astype(float)

        # Podes adaptar aqui o campo que vais visualizar no gráfico
        df["TotalMeios"] = (
            df["NumeroMeiosTerrestresEnvolvidos"].fillna(0)
            + df["NumeroMeiosAereosEnvolvidos"].fillna(0)
        )

        return df

    except Exception as e:
        print(f"Erro ao obter dados: {e}")
        return pd.DataFrame()

# Rota principal
@app.route("/")
def index():
    df = obter_dados()

    if df.empty:
        return "<h2>Não foi possível carregar os dados.</h2>"

    # Criar gráfico com Plotly
    grafico = px.bar(
        df,
        x="DataOcorrencia",
        y="TotalMeios",
        title="Meios Envolvidos por Ocorrência",
        color="Distrito"
    )
    grafico_html = grafico.to_html(full_html=False)

    grafico2 = px.bar(  # ou outro tipo de gráfico
    df,
    x="Distrito",
    y="TotalMeios",
    title="Total de Meios por Distrito"
   )
    grafico2_html = grafico2.to_html(full_html=False)

    # Mapa interativo
    mapa = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Natureza",
        hover_data=["EstadoOcorrencia", "Distrito", "Concelho"],
        color="Estado",
        zoom=6,
        height=400
    )
    mapa.update_layout(mapbox_style="open-street-map")
    mapa_html = mapa.to_html(full_html=False)

    return render_template("index.html", mapa=mapa_html, grafico=grafico_html, grafico2=grafico2_html)

# Executar a aplicação
if __name__ == "__main__":
    app.run(debug=True)
