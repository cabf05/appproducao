import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

st.set_page_config(page_title="Resumo de Produção", layout="wide")
st.title("Resumo de Produção por Local")

# Upload das planilhas
uploaded_dados = st.file_uploader("Faça upload da planilha Dados_Produtos.xlsx", type=["xlsx"] )
uploaded_cadastro = st.file_uploader("Faça upload da planilha CadastroTotal.xlsx", type=["xlsx"] )

if uploaded_dados and uploaded_cadastro:
    # Leitura das planilhas
    dados = pd.read_excel(uploaded_dados)
    cadastro = pd.read_excel(uploaded_cadastro)

    # Junção dos dados pelo campo Produto
    df = pd.merge(
        dados,
        cadastro[['Produto', 'FATOR CALCULO PRODUCAO']],
        on='Produto',
        how='left'
    )

    # Cálculo da Quantidade a Preparar
    df['Quantidade a Preparar'] = df['Quantidade'] * df['FATOR CALCULO PRODUCAO']

    # Resumo por Local e Produto
    summary = (
        df
        .groupby(['Local', 'Produto'])['Quantidade a Preparar']
        .sum()
        .reset_index()
    )

    # Criação do PDF
    pdf = FPDF()

    # Exibição no app e geração do PDF
    locais = summary['Local'].unique()
    for loc in locais:
        st.subheader(f"Local: {loc}")
        df_loc = summary[summary['Local'] == loc][['Produto', 'Quantidade a Preparar']]
        st.table(df_loc)

        # Nova página no PDF
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Local: {loc}", ln=True)
        pdf.ln(5)
        for _, row in df_loc.iterrows():
            pdf.cell(0, 8, f"{row['Produto']}: {row['Quantidade a Preparar']}", ln=True)

    # Botão de download do PDF
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    st.download_button(
        "Download do resumo em PDF",
        data=pdf_bytes,
        file_name="resumo_producao.pdf",
        mime="application/pdf"
    )

