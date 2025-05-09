# app.py

import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

st.set_page_config(page_title="Resumo de Produção", layout="wide")
st.title("Resumo de Produção por Local")

# Upload das planilhas
uploaded_dados = st.file_uploader("Faça upload da planilha Dados_Produtos.xlsx", type=["xlsx"])
uploaded_cadastro = st.file_uploader("Faça upload da planilha CadastroTotal.xlsx", type=["xlsx"])

if uploaded_dados and uploaded_cadastro:
    try:
        # Leitura das planilhas
        dados = pd.read_excel(uploaded_dados)
        cadastro = pd.read_excel(uploaded_cadastro)

        # Limpeza e padronização de nomes de colunas para lowercase
        dados.columns = dados.columns.str.strip().str.lower()
        cadastro.columns = cadastro.columns.str.strip().str.lower()

        # Definição de colunas esperadas
        required_dados = ['local', 'produto', 'quantidade']
        required_cadastro = ['produto', 'fator calculo producao']

        # Verificação de colunas faltantes
        missing_d = [col for col in required_dados if col not in dados.columns]
        missing_c = [col for col in required_cadastro if col not in cadastro.columns]
        if missing_d or missing_c:
            st.error(
                f"Colunas faltando:\nDados_Produtos.xlsx: {missing_d}\nCadastroTotal.xlsx: {missing_c}\n" +
                "Colunas em Dados: " + ", ".join(dados.columns) + "\n" +
                "Colunas em Cadastro: " + ", ".join(cadastro.columns)
            )
            st.stop()

        # Renomear colunas internamente para facilitar uso
        dados = dados.rename(columns={
            'local': 'local',
            'produto': 'produto',
            'quantidade': 'quantidade'
        })
        cadastro = cadastro.rename(columns={
            'produto': 'produto',
            'fator calculo producao': 'fator'
        })

        # Junção dos dados pelo campo produto
        df = pd.merge(
            dados,
            cadastro[['produto', 'fator']],
            on='produto',
            how='left'
        )

        # Tratar possíveis NaNs no fator
        if df['fator'].isna().any():
            missing_prod = df[df['fator'].isna()]['produto'].unique()
            st.warning(f"Fator de cálculo não encontrado para os produtos: {list(missing_prod)}. Utilizando fator = 1.")
            df['fator'] = df['fator'].fillna(1)

        # Cálculo da quantidade a preparar
        df['quantidade_preparar'] = df['quantidade'] * df['fator']

        # Resumo por local e produto
        summary = (
            df
            .groupby(['local', 'produto'], as_index=False)[['quantidade_preparar']]
            .sum()
        )

        # Criação do PDF
        pdf = FPDF()

        # Exibição no app e geração do PDF
        locais = summary['local'].unique()
        for loc in locais:
            st.subheader(f"Local: {loc}")
            df_loc = summary[summary['local'] == loc][['produto', 'quantidade_preparar']]
            df_loc = df_loc.rename(columns={
                'produto': 'Produto',
                'quantidade_preparar': 'Quantidade a Preparar'
            })
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

    except Exception as e:
        st.error(f"Erro ao processar as planilhas: {e}")
        st.stop()
