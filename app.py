from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import requests

# Inicializar a aplicação Flask
app = Flask(__name__)

# Função para obter e preparar os dados
def obter_dados():
    url = "https://3pscoutsteste.abranco.pt/api/ANEPCAPI/GetPointsGetOcorrenciasActivasLista"
    
    try:
        # 🚀 Requisição à API
        response = requests.get(url)
        response.raise_for_status()
        dados_json = response.json()

        # 📦 Converter em DataFrame
        df = pd.DataFrame(dados_json)
        print(df.columns)

        # 🔠 Normalizar nomes de colunas
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "")
        )

        # 🕒 Converter datas e coordenadas
        df["dataocorrencia"] = pd.to_datetime(df["dataocorrencia"], format="%d-%m-%Y %H:%M:%S", errors="coerce")
        df["latitude"] = df["latitude"].astype(str).str.replace(",", ".").astype(float)
        df["longitude"] = df["longitude"].astype(str).str.replace(",", ".").astype(float)

        # 🛠️ Criar campo de total de meios
        df["totalmeios"] = (
            df["numeromeiosterrestresenvolvidos"].fillna(0)
            + df["numeromeiosaereosenvolvidos"].fillna(0)
        )

        # 🧼 Padronizar nome de estado
        if "estadoocorrencia" not in df.columns and "estado" in df.columns:
            df["estadoocorrencia"] = df["estado"]

        df["estadoocorrencia"] = df["estadoocorrencia"].fillna("Desconhecido").str.title()

        # ✅ Verificações finais
        colunas_obrigatorias = ["latitude", "longitude", "natureza", "distrito", "concelho", "estadoocorrencia"]
        faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        if faltantes:
            raise ValueError(f"Colunas obrigatórias em falta: {faltantes}")

        return df

    except Exception as e:
        print(f"Erro ao obter dados: {e}")
        return pd.DataFrame()
# Rota principal
@app.route("/", methods=["GET"])
def index():
    distrito = request.args.get("distrito")
    estado = request.args.get("estado")

    # 📊 Carregar dados
    df = obter_dados()
    df_filtrado = df.copy()

    # 🔍 Filtrar por distrito e estado
    if distrito:
        df_filtrado = df_filtrado[df_filtrado["distrito"] == distrito]
    if estado:
        df_filtrado = df_filtrado[df_filtrado["estadoocorrencia"] == estado]

    # 📌 Métricas agregadas com blindagem
    total_ocorrencias = len(df_filtrado)
    total_operacionais = int(df_filtrado.get("numeromeiosterrestresenvolvidos", pd.Series([0])).sum())
    total_veiculos = int(df_filtrado.get("NumeroMeiosTerrestresEnvolvidos", pd.Series([0])).sum())
    total_aereos = int(df_filtrado.get("numeromeiosaereosenvolvidos", pd.Series([0])).sum())
    total_meios_aquaticos = int(df_filtrado.get("NumeroMeiosAquaticosEnvolvidos", pd.Series([0])).fillna(0).sum())
    total_incendios = int(df_filtrado.get("natureza", pd.Series([])).str.contains("incêndio", case=False, na=False).sum())

    # 📍 Dropdowns
    distritos = sorted(df["distrito"].dropna().unique())
    estados = sorted(df["estadoocorrencia"].dropna().unique())

    # 📊 Gráfico 1: Meios por ocorrência
    grafico = px.bar(
        df_filtrado,
        x="dataocorrencia",
        y="totalmeios",
        color="distrito",
        title="Meios Envolvidos por Ocorrência"
    )
    grafico_html = grafico.to_html(full_html=False)

    # 📊 Gráfico 2: Total por distrito
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

    # 🗺️ Mapa
    mapa = px.scatter_mapbox(
        df_filtrado,
        lat="latitude",
        lon="longitude",
        hover_name="natureza",
        hover_data=["estadoocorrencia", "distrito", "concelho"],
        color="estado",
        zoom=6,
        height=750
    )
    mapa.update_layout(mapbox_style="open-street-map")
    mapa_html = mapa.to_html(full_html=False)

    # 🧾 Renderizar template
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
