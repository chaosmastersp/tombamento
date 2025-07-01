
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Consulta de Empréstimos", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def autenticar():
    senha = st.text_input("Digite a senha para acessar o sistema:", type="password")
    if senha == "tombamento":  # Substitua por senha segura
        st.session_state.autenticado = True
        st.success("Acesso autorizado.")
    else:
        st.error("Senha incorreta.")

if not st.session_state.autenticado:
    autenticar()
    st.stop()

def formatar_documentos(df, col, tamanho):
    return df[col].astype(str).str.replace(r'\D', '', regex=True).str.zfill(tamanho)

def carregar_bases():
    st.session_state.novo_df = pd.read_excel(st.session_state.arquivo_novo)
    st.session_state.tomb_df = pd.read_excel(st.session_state.arquivo_tomb)
    st.session_state.novo_df['Número CPF/CNPJ'] = formatar_documentos(st.session_state.novo_df, 'Número CPF/CNPJ', 11)
    st.session_state.novo_df['CNPJ Empresa'] = formatar_documentos(st.session_state.novo_df, 'CNPJ Empresa', 14)
    st.session_state.tomb_df['Número CPF'] = formatar_documentos(st.session_state.tomb_df, 'Número CPF', 11)
    st.session_state.tomb_df['Número Contrato'] = st.session_state.tomb_df['Número Contrato'].astype(str)

st.sidebar.header("Gerenciamento de Dados")

if "arquivo_novo" not in st.session_state or st.session_state.arquivo_novo is None:
    st.session_state.arquivo_novo = st.sidebar.file_uploader("Base NovoEmprestimo.xlsx", type="xlsx")
if "arquivo_tomb" not in st.session_state or st.session_state.arquivo_tomb is None:
    st.session_state.arquivo_tomb = st.sidebar.file_uploader("Base Tombamento.xlsx", type="xlsx")

if st.session_state.arquivo_novo and st.session_state.arquivo_tomb:
    carregar_bases()

    if st.sidebar.button("Atualizar Bases"):
        st.session_state.arquivo_novo = None
        st.session_state.arquivo_tomb = None
        st.experimental_rerun()

    st.title("🔍 Consulta de Empréstimos por CPF")
    cpf_input = st.text_input("Digite o CPF (apenas números):").strip()

    if cpf_input and len(cpf_input) == 11 and cpf_input.isdigit():
        df = st.session_state.novo_df
        tomb = st.session_state.tomb_df

        filtrado = df[
            (df['Número CPF/CNPJ'] == cpf_input) &
            (df['Submodalidade Bacen'] == 'CRÉDITO PESSOAL - COM CONSIGNAÇÃO EM FOLHA DE PAGAM.') &
            (df['Critério Débito'] == 'FOLHA DE PAGAMENTO') &
            (~df['Código Linha Crédito'].isin([140073, 138358, 141011]))
        ]

        if filtrado.empty:
            st.warning("Nenhum contrato encontrado com os filtros aplicados.")
        else:
            resultados = []
            for _, row in filtrado.iterrows():
                contrato = str(row['Número Contrato Crédito'])
                match = tomb[
                    (tomb['Número CPF'] == cpf_input) &
                    (tomb['Número Contrato'] == contrato)
                ]

                consignante = match['CNPJ Empresa Consignante'].iloc[0] if not match.empty else "CONSULTE SISBR"
                empresa = match['Empresa Consignante'].iloc[0] if not match.empty else "CONSULTE SISBR"

                resultados.append({
                    "Número CPF/CNPJ": row['Número CPF/CNPJ'],
                    "Nome Cliente": row['Nome Cliente'],
                    "Número Contrato Crédito": contrato,
                    "Quantidade Parcelas Abertas": row['Quantidade Parcelas Abertas'],
                    "% Taxa Operação": row['% Taxa Operação'],
                    "Código Linha Crédito": row['Código Linha Crédito'],
                    "Nome Comercial": row['Nome Comercial'],
                    "CNPJ Empresa": row['CNPJ Empresa'],
                    "Consignante": consignante,
                    "Empresa Consignante": empresa
                })

            st.dataframe(pd.DataFrame(resultados))
    else:
        st.info("Insira um CPF válido com 11 dígitos.")
else:
    st.warning("⚠️ Carregue os dois arquivos para continuar.")

