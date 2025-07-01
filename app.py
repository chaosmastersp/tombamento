
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Consulta de Empréstimos", layout="wide")

# Inicialização do estado
for key in ["autenticado", "arquivo_novo", "arquivo_tomb"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "autenticado" else False

DATA_DIR = "data"
NOVO_PATH = os.path.join(DATA_DIR, "novoemprestimo.xlsx")
TOMB_PATH = os.path.join(DATA_DIR, "tombamento.xlsx")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def autenticar():
    senha = st.text_input("Digite a senha para acessar o sistema:", type="password")
    if senha == "tombamento":
        st.session_state.autenticado = True
        st.success("Acesso autorizado.")
    elif senha:
        st.error("Senha incorreta.")

autenticar()
if not st.session_state.autenticado:
    st.stop()

def formatar_documentos(df, col, tamanho):
    return df[col].astype(str).str.replace(r'\D', '', regex=True).str.zfill(tamanho)

def carregar_bases_do_disco():
    st.session_state.novo_df = pd.read_excel(NOVO_PATH)
    st.session_state.tomb_df = pd.read_excel(TOMB_PATH)

    st.session_state.novo_df['Número CPF/CNPJ'] = formatar_documentos(st.session_state.novo_df, 'Número CPF/CNPJ', 11)
    st.session_state.tomb_df['CPF Tomador'] = formatar_documentos(st.session_state.tomb_df, 'CPF Tomador', 11)
    if 'Número Contrato' in st.session_state.tomb_df.columns:
        st.session_state.tomb_df['Número Contrato'] = st.session_state.tomb_df['Número Contrato'].astype(str)

def salvar_arquivos(upload_novo, upload_tomb):
    with open(NOVO_PATH, "wb") as f:
        f.write(upload_novo.read())
    with open(TOMB_PATH, "wb") as f:
        f.write(upload_tomb.read())
    carregar_bases_do_disco()

st.sidebar.header("Gerenciamento de Dados")

# Atualizar base
if st.sidebar.button("Atualizar Bases"):
    st.session_state.arquivo_novo = st.sidebar.file_uploader("Nova Base NovoEmprestimo.xlsx", type="xlsx")
    st.session_state.arquivo_tomb = st.sidebar.file_uploader("Nova Base Tombamento.xlsx", type="xlsx")
    if st.session_state.arquivo_novo and st.session_state.arquivo_tomb:
        salvar_arquivos(st.session_state.arquivo_novo, st.session_state.arquivo_tomb)
        st.rerun()
    else:
        st.warning("Envie os dois arquivos para atualizar.")
    st.stop()

# Carregamento inicial: se arquivos não existem, obriga upload
if not os.path.exists(NOVO_PATH) or not os.path.exists(TOMB_PATH):
    st.info("Faça o upload das bases para iniciar o sistema.")
    arquivo_novo = st.file_uploader("Base NovoEmprestimo.xlsx", type="xlsx", key="upload_novo")
    arquivo_tomb = st.file_uploader("Base Tombamento.xlsx", type="xlsx", key="upload_tomb")
    if arquivo_novo and arquivo_tomb:
        salvar_arquivos(arquivo_novo, arquivo_tomb)
        st.success("Bases carregadas com sucesso.")
        st.rerun()
    else:
        st.stop()
else:
    carregar_bases_do_disco()

# Interface principal
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


