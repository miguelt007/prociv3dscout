@app.route('/')
def index():
    dados = obter_dados()
    df = pd.DataFrame(dados)

    grafico_html = "<p>Nenhum dado disponível para gráfico.</p>"
    mapa_html = "<p>Nenhum dado de localização disponível.</p>"

    if not df.empty:
        # ➤ Limpar valores nulos na coluna Tipo
        if 'Tipo' in df.columns and not df['Tipo'].isna().all():
            df_tipo = df[df['Tipo'].notna()]
            fig = px.histogram(df_tipo, x='Tipo', title='Tipos de Ocorrência')
            grafico_html = fig.to_html(full_html=False)

        # ➤ Limpar e converter coordenadas
        if {'Latitude', 'Longitude'}.issubset(df.columns):
            df["Latitude"] = pd.to_numeric(df["Latitude"].str.replace(",", ".", regex=False), errors="coerce")
            df["Longitude"] = pd.to_numeric(df["Longitude"].str.replace(",", ".", regex=False), errors="coerce")
            df.dropna(subset=["Latitude", "Longitude"], inplace=True)

            # ➤ Confirmar colunas para hover e cor
            hover_col = "Localidade" if "Localidade" in df.columns else None
            hover_data = ["Distrito", "Concelho", "Freguesia", "Tipo", "Estado"] if hover_col else None
            cor = "Tipo" if "Tipo" in df.columns and not df['Tipo'].isna().all() else None

            # ➤ Construir o mapa
            mapa = px.scatter_mapbox(
                df,
                lat="Latitude",
                lon="Longitude",
                hover_name=hover_col,
                hover_data=hover_data,
                color=cor,
                zoom=5,
                height=500,
                title=f"{len(df)} ocorrências ativas"
            )
            mapa.update_layout(mapbox_style="open-street-map")
            mapa_html = mapa.to_html(full_html=False)

    return render_template("index.html", grafico=grafico_html, mapa=mapa_html)
