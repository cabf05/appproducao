# app.py

import streamlit as st
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Resumo de Produção", layout="wide")
st.title("Resumo de Produção por Local")

# Entrada da data de produção
data_producao = st.date_input("Data de Produção")

# Upload das planilhas
uploaded_dados = st.file_uploader("Faça upload da planilha Dados_Produtos.xlsx", type=["xlsx"])
uploaded_cadastro = st.file_uploader("Faça upload da planilha CadastroTotal.xlsx", type=["xlsx"])

if uploaded_dados and uploaded_cadastro:
    try:
        # Leitura das planilhas
        dados = pd.read_excel(uploaded_dados)
        cadastro = pd.read_excel(uploaded_cadastro)

        # Padronizar nomes de colunas: strip e lowercase
        dados.columns = dados.columns.str.strip().str.lower()
        cadastro.columns = cadastro.columns.str.strip().str.lower()

        # Definição de colunas esperadas
        required_dados = ['produto', 'quantidade']
        required_cadastro = ['produto', 'local', 'fator calculo producao']

        # Verificação de colunas faltantes
        missing_d = [col for col in required_dados if col not in dados.columns]
        missing_c = [col for col in required_cadastro if col not in cadastro.columns]
        if missing_d or missing_c:
            st.error(
                f"Colunas faltando:\nDados_Produtos.xlsx: {missing_d}\nCadastroTotal.xlsx: {missing_c}\n" +
                f"Colunas em Dados: {', '.join(dados.columns)}\n" +
                f"Colunas em Cadastro: {', '.join(cadastro.columns)}"
            )
            st.stop()

        # Renomear colunas para uso interno
        dados = dados.rename(columns={'produto': 'produto', 'quantidade': 'quantidade'})
        cadastro = cadastro.rename(columns={
            'produto': 'produto',
            'local': 'local',
            'fator calculo producao': 'fator'
        })

        # Junção: traz local e fator para cada produto
        df = pd.merge(dados, cadastro[['produto', 'local', 'fator']], on='produto', how='left')

        # Tratar registros sem cadastro
        if df[['local', 'fator']].isna().any().any():
            missing_info = df[df['local'].isna() | df['fator'].isna()]['produto'].unique()
            st.warning(
                f"Produtos sem cadastro completo (local ou fator faltando): {list(missing_info)}. "
                + "Usando local='Desconhecido' e fator=1 onde faltarem."
            )
            df['local'] = df['local'].fillna('Desconhecido')
            df['fator'] = df['fator'].fillna(1)

        # Cálculo da quantidade a preparar
        df['quantidade_preparar'] = df['quantidade'] * df['fator']

        # Resumo por local e produto
        summary = (
            df.groupby(['local', 'produto'], as_index=False)
              .agg({'quantidade_preparar': 'sum'})
        )

        # Formata data
        data_str = data_producao.strftime("%d-%m-%Y")

        # Geração do PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Para cada local, exibe e adiciona página
        for loc in summary['local'].unique():
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
            # Cabeçalho com data e local
            pdf.cell(0, 10, f"Data de Produção: {data_str}", ln=True)
            pdf.cell(0, 10, f"Local: {loc}", ln=True)
            pdf.ln(5)

            # Tabela com cores alternadas
            pdf.set_font("Arial", size=10)
            # Cabeçalho da tabela
            col_widths = [90, 90]
            headers = ['Produto', 'Quantidade a Preparar']
            # Desenha cabeçalho
            for i, header in enumerate(headers):
                pdf.set_fill_color(200, 200, 200)
                pdf.cell(col_widths[i], 8, header, border=1, align='C', fill=True)
            pdf.ln()
            # Linhas de dados
            for idx, row in df_loc.iterrows():
                fill = idx % 2 == 1
                if fill:
                    pdf.set_fill_color(230, 230, 230)
                else:
                    pdf.set_fill_color(255, 255, 255)
                pdf.cell(col_widths[0], 6, str(row['Produto']), border=1, fill=fill)
                pdf.cell(col_widths[1], 6, str(row['Quantidade a Preparar']), border=1, fill=fill)
                pdf.ln()

        # Download do PDF
        pdf_buffer = pdf.output(dest='S')  # retorna bytearray
        pdf_bytes = bytes(pdf_buffer)
        st.download_button(
            label="Download do resumo em PDF",
            data=pdf_bytes,
            file_name="resumo_producao.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Erro ao processar as planilhas: {e}")
        st.stop()
