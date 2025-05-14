import streamlit as st
from docx import Document
import io
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI

# Configurar API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Interface
st.title("📊 Análise Automática de Relatórios com IA")
st.write("Faça upload de um arquivo `.docx`. Eu irei analisar os dados, gerar gráficos e apresentar insights estratégicos.")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha um arquivo DOCX", type=["docx"])

def extrair_texto(docx_file):
    document = Document(io.BytesIO(docx_file.read()))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())

def dividir_texto(texto, max_palavras=2000):
    palavras = texto.split()
    blocos = [" ".join(palavras[i:i+max_palavras]) for i in range(0, len(palavras), max_palavras)]
    return blocos

def solicitar_analise(texto):
    prompt = f"""Você é um analista de mercado. Com base no texto abaixo, identifique dados quantitativos e proponha gráficos:

{texto}

Para cada gráfico, informe:
- Título
- Tipo de gráfico
- Dados em formato de tabela
- Fonte
- Interpretação executiva
"""
    resposta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é um analista de dados com foco em visualizações."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return resposta.choices[0].message.content

def gerar_grafico_exemplo():
    data = {"Plataforma": ["iFood", "Rappi", "99Food"], "Participação (%)": [78, 12, 10]}
    df = pd.DataFrame(data)
    fig, ax = plt.subplots()
    df.plot(kind="bar", x="Plataforma", y="Participação (%)", legend=False, ax=ax)
    ax.set_title("Market Share Estimado - 2024")
    plt.grid(True)
    st.pyplot(fig)
    st.caption("Fonte: Seção 3.2 do relatório")

# Processamento
if uploaded_file:
    with st.spinner("🔍 Extraindo texto..."):
        texto = extrair_texto(uploaded_file)
        blocos = dividir_texto(texto)

    for i, bloco in enumerate(blocos):
        st.subheader(f"🔹 Bloco {i + 1}")
        with st.spinner("Analisando com IA..."):
            resposta = solicitar_analise(bloco)
        st.text_area("📄 Análise", resposta, height=300)

    st.subheader("📈 Gráfico Exemplo")
    gerar_grafico_exemplo()
