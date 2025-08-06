from flask import Flask, render_template, request
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
@app.route("/", methods=["GET"])
def index():
    distrito = request.args.get("distrito")
    estado = request.args.get("estado")

    # Aplica os filtros
    df = obter_dados()
    df_filtrado = df.copy()
    if distrito:
        df_filtrado = df_filtrado[df_filtrado["Distrito"] == distrito]
    if estado:
        df_filtrado = df_filtrado[df_filtrado["EstadoOcorrencia"] == estado]

    # Lista única para preencher o dropdown
    distritos = sorted(df["Distrito"].unique())
    estados = sorted(df["EstadoOcorrencia"].unique())

    # Recriar gráficos com df_filtrado
    grafico = px.bar(df_filtrado, x="DataOcorrencia", y="TotalMeios", color="Distrito", title="Meios Envolvidos por Ocorrência")
    grafico_html = grafico.to_html(full_html=False)

    grafico2 = px.bar(df_filtrado, x="Distrito", y="TotalMeios", title="Total de Meios por Distrito")
    grafico2_html = grafico2.to_html(full_html=False)

    mapa = px.scatter_mapbox(
        df_filtrado,
        lat="Latitude",
        lon="Longitude",
        hover_name="Natureza",
        hover_data=["EstadoOcorrencia", "Distrito", "Concelho"],
        color="Estado",
        zoom=6,
        height=900
    )
    mapa.update_layout(mapbox_style="open-street-map")
    mapa_html = mapa.to_html(full_html=False)

    return render_template(
        "index.html",
        mapa=mapa_html,
        grafico=grafico_html,
        grafico2=grafico2_html,
        distritos=distritos,
        estados=estados,
        distrito_selecionado=distrito,
        estado_selecionado=estado
    )

# Executar a aplicação
if __name__ == "__main__":
    app.run(debug=True)
