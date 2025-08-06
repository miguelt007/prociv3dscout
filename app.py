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

        # Converter em DataFrame
        df = pd.DataFrame(dados_json)

        # Exemplos de tratamento (modifica conforme necessário)
        df["data"] = pd.to_datetime(df["data"])
        df["valor"] = df["valor"].astype(float)
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
    grafico = px.line(df, x="data", y="valor", title="Evolução dos Valores")
    grafico_html = grafico.to_html(full_html=False)

    return render_template("index.html", grafico=grafico_html)

# Executar a aplicação
if __name__ == "__main__":
    app.run(debug=True)
