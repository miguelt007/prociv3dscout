from flask import Flask, render_template
import requests
import pandas as pd
import plotly.express as px

app = Flask(__name__)

def obter_dados():
    url = "https://3pscoutsteste.abranco.pt/api/ANEPCAPI/GetPointsGetOcorrenciasActivasLista"
    resposta = requests.get(url)
    if resposta.status_code == 200:
        return resposta.json()
    return []

@app.route('/')
def index():
    dados = obter_dados()
    df = pd.DataFrame(dados)

    grafico_html = "<p>Nenhum dado disponível para gráfico.</p>"
    mapa_html = "<p>Nenhum dado de localização disponível.</p>"

    if not df.empty:
        if 'Tipo' in df.columns:
            fig = px.histogram(df, x='Tipo', title='Tipos de Ocorrência')
            grafico_html = fig.to_html(full_html=False)

        if {'Latitude', 'Longitude'}.issubset(df.columns):
            mapa = px.scatter_mapbox(df,
                                     lat="Latitude",
                                     lon="Longitude",
                                     hover_name="Localidade",
                                     zoom=6,
                                     height=500)
            mapa.update_layout(mapbox_style="open-street-map")
            mapa_html = mapa.to_html(full_html=False)

    return render_template("index.html", grafico=grafico_html, mapa=mapa_html)
