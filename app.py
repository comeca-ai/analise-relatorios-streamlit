import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from docx import Document
from openai import OpenAI
import io
import re

# === VERIFICAÇÃO DE CHAVE ===
if "OPENAI_API_KEY" not in st.secrets:
    st.error("⚠️ Chave OPENAI_API_KEY não configurada. Vá em 'Manage App' > 'Secrets' no Streamlit Cloud.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# === FUNÇÕES AUXILIARES ===

def extrair_texto(docx_file):
    document = Document(io.BytesIO(docx_file.read()))
    return "\n".join([p.text for p in document.paragraphs if p.text.strip()])

def dividir_em_blocos(texto, max_palavras=2000):
    palavras = texto.split()
    return [" ".join(palavras[i:i+max_palavras]) for i in range(0, len(palavras), max_palavras)]

def solicitar_analise(texto):
    prompt = f"""
Você é um analista de dados. Com base no conteúdo abaixo, extraia dados e proponha gráficos:

{texto}

Para cada gráfico, informe:
- Título
- Tipo
- Tabela (formato markdown ou texto plano)
- Interpretação executiva
"""
    resposta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é um analista de dados experiente, especialista em visualizações."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return resposta.choices[0].message.content

def extrair_tabelas_do_texto(texto):
    padrao = re.findall(r'(\\w.+\\|.+\\n(?:[-\\w\\s%\\.]+\\|.*\\n)+)', texto)
    tabelas = []
    for bloco in padrao:
        linhas = bloco.strip().split("\\n")
        colunas = [c.strip() for c in linhas[0].split("|")]
        dados = []
        for linha in linhas[1:]:
            if "|" in linha:
                valores = [v.strip() for v in linha.split("|")]
                if len(valores) == len(colunas):
                    dados.append(valores)
        if dados:
            df = pd.DataFrame(dados, columns=colunas)
            for col in df.columns[1:]:
                try:
                    df[col] = pd.to_numeric(df[col].str.replace('%','').str.replace(',','.'), errors='coerce')
                except:
                    pass
            tabelas.append(df)
    return tabelas

def plotar_grafico(df, titulo=""):
    st.markdown(f"### 📊 {titulo or 'Gráfico'}")
    try:
        fig, ax = plt.subplots()
        df.plot(kind="bar", x=df.columns[0], y=df.columns[1], legend=False, ax=ax)
        ax.set_title(titulo)
        plt.xticks(rotation=45)
        plt.grid(True)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {e}")

# === INTERFACE ===

st.title("📄 Analisador de Relatórios com Gráficos por IA")
st.write("Faça upload de um arquivo `.docx`. Eu irei extrair os dados e gerar gráficos automaticamente.")

arquivo = st.file_uploader("📤 Envie seu arquivo Word (.docx)", type=["docx"])

if arquivo:
    with st.spinner("Lendo o conteúdo..."):
        texto = extrair_texto(arquivo)
        blocos = dividir_em_blocos(texto)

    for i, bloco in enumerate(blocos):
        st.markdown(f"## 🔍 Bloco {i+1}")
        with st.spinner("Consultando a OpenAI..."):
            resposta = solicitar_analise(bloco)

        st.markdown("#### 🧠 Resposta da IA")
        st.text_area(label=f"Resposta do GPT para bloco {i+1}", value=resposta, height=250)

        with st.spinner("Gerando gráficos..."):
            tabelas = extrair_tabelas_do_texto(resposta)
            if tabelas:
                for idx, tabela in enumerate(tabelas):
                    st.dataframe(tabela)
                    plotar_grafico(tabela, f"Gráfico {idx+1}")
            else:
                st.info("Nenhuma tabela detectada para gerar gráficos neste bloco.")

