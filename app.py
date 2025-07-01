
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Consulta de Empréstimos", layout="wide")

# Inicialização segura do estado
for key in ["autenticado", "arquivo_novo", "arquivo_tomb"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "autenticado" else False

def autenticar():
    senha = st.text_input("Digite a senha para acessar o sistema:", type="password")
    if senha == "tombamento":  # Substitua por senha segura
        st.session_state.autenticado = True
        st.success("Acesso autorizado.")
    elif senha:
        st.error("Senha incorreta.")

autenticar()
if not st.session_state.autenticado:
    st.stop()

def formatar_documentos(df, col, tamanho):
    return df[col].astype(str).str.replace(r'\D', '', regex=True).str.zfill(tamanho)

def carregar_bases():
    st.session_state.novo_df = pd.read_excel(st.session_state.arquivo_novo)
    st.session_state.tomb_df = pd.read_excel(st.session_state.arquivo_tomb)

    # Renomeando colunas para garantir consistência
    novo = st.session_state.novo_df.rename(columns=lambda x: x.strip())
    tomb = st.session_state.tomb_df.rename(columns=lambda x: x.strip())

    # Equalização
    novo['Número CPF/CNPJ'] = formatar_documentos(novo, 'Número CPF/CNPJ', 11)
    tomb['CPF Tomador'] = formatar_documentos(tomb, 'CPF Tomador', 11)
    if 'Número Contrato' in tomb.columns:
        tomb['Número Contrato'] = tomb['Número Contrato'].astype(str)

    st.session_state.novo_df = novo
    st.session_state.tomb_df = tomb

st.sidebar.header("Gerenciamento de Dados")

if st.session_state.arquivo_novo is None:
    st.session_state.arquivo_novo = st.sidebar.file_uploader("Base NovoEmprestimo.xlsx", type="xlsx")
if st.session_state.arquivo_tomb is None:
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
                    (tomb['CPF Tomador'] == cpf_input) &
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
                    "Consignante": consignante,
                    "Empresa Consignante": empresa
                })

            st.dataframe(pd.DataFrame(resultados))
    else:
        st.info("Insira um CPF válido com 11 dígitos.")
else:
    st.warning("⚠️ Carregue os dois arquivos para continuar.")

