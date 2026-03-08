import os
import requests
import pandas as pd
import streamlit as st

UPLOAD_API_URL = os.environ.get("UPLOAD_API_URL", "")
PREDICT_API_URL = os.environ.get("PREDICT_API_URL", "")

st.set_page_config(page_title="Passos Mágicos Dashboard", layout="wide")
st.title("Dashboard - Passos Mágicos")


@st.cache_data(ttl=60)
def load_students():
    response = requests.get(f"{PREDICT_API_URL}dashboard/students", timeout=120)
    response.raise_for_status()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=30)
def load_status():
    response = requests.get(f"{PREDICT_API_URL}dashboard/status", timeout=60)
    response.raise_for_status()
    return response.json()


tab1, tab2, tab3 = st.tabs(["Visão Geral", "Upload de Arquivo", "Predição"])

with tab1:
    st.subheader("Acompanhamento dos alunos")

    try:
        status = load_status()
        students_df = load_students()
    except Exception as e:
        st.error(f"Erro ao carregar dashboard: {e}")
        students_df = pd.DataFrame()
        status = {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Arquivos raw/parquet", status.get("raw_parquet_files", 0))
    c2.metric("Total de alunos", status.get("total_students", 0))
    c3.metric("Modelo disponível", "Sim" if status.get("model_available") else "Não")
    c4.metric("Último processamento", str(status.get("last_processed_at")))

    if not students_df.empty:
        for col in [
            "student_id",
            "nome",
            "turma",
            "fase",
            "faixa_etaria",
            "risk_category",
            "media_notas",
            "faltas",
        ]:
            if col not in students_df.columns:
                students_df[col] = ""

        with st.sidebar:
            st.header("Filtros")

            turma_opts = ["Todos"] + sorted(
                [str(x) for x in students_df["turma"].dropna().unique() if str(x) != ""]
            )
            fase_opts = ["Todos"] + sorted(
                [str(x) for x in students_df["fase"].dropna().unique() if str(x) != ""]
            )
            faixa_opts = ["Todos"] + sorted(
                [str(x) for x in students_df["faixa_etaria"].dropna().unique() if str(x) != ""]
            )

            turma_sel = st.selectbox("Turma", turma_opts)
            fase_sel = st.selectbox("Fase", fase_opts)
            faixa_sel = st.selectbox("Faixa etária", faixa_opts)

        filtered_df = students_df.copy()

        if turma_sel != "Todos":
            filtered_df = filtered_df[filtered_df["turma"].astype(str) == turma_sel]

        if fase_sel != "Todos":
            filtered_df = filtered_df[filtered_df["fase"].astype(str) == fase_sel]

        if faixa_sel != "Todos":
            filtered_df = filtered_df[filtered_df["faixa_etaria"].astype(str) == faixa_sel]

        st.subheader("Distribuição de categorias")
        category_counts = (
            filtered_df["risk_category"]
            .fillna("Nao informado")
            .value_counts()
            .rename_axis("risk_category")
            .reset_index(name="quantidade")
        )
        st.bar_chart(category_counts.set_index("risk_category"))

        st.subheader("Alunos em risco")
        risk_df = filtered_df[
            filtered_df["risk_category"].isin(["Perigo", "Suporte"])
        ].copy()

        risk_columns = [
            "student_id",
            "nome",
            "turma",
            "fase",
            "faixa_etaria",
            "media_notas",
            "faltas",
            "risk_category",
        ]

        for col in risk_columns:
            if col not in risk_df.columns:
                risk_df[col] = ""

        st.dataframe(
            risk_df[risk_columns].sort_values(
                by=["risk_category", "faltas"],
                ascending=[True, False]
            ),
            use_container_width=True,
        )

        st.subheader("Base filtrada")
        st.dataframe(filtered_df, use_container_width=True)

with tab2:
    st.subheader("Enviar XLSX para processamento")
    uploaded_file = st.file_uploader("Selecione um arquivo XLSX", type=["xlsx"])

    if uploaded_file is not None:
        st.write(f"Arquivo selecionado: {uploaded_file.name}")

        if st.button("Enviar arquivo"):
            url = f"{UPLOAD_API_URL}files/{uploaded_file.name}"
            response = requests.put(
                url,
                data=uploaded_file.getvalue(),
                headers={
                    "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                },
                timeout=120,
            )

            st.write("Status:", response.status_code)
            try:
                st.json(response.json())
            except Exception:
                st.text(response.text)

with tab3:
    st.subheader("Predição individual")

    student_id = st.text_input("Student ID", "RA-1")
    nota_portugues = st.number_input("Nota Português", 0.0, 10.0, 6.5)
    nota_matematica = st.number_input("Nota Matemática", 0.0, 10.0, 5.0)
    nota_ciencias = st.number_input("Nota Inglês", 0.0, 10.0, 6.0)
    faltas = st.number_input("Nº Av", 0, 50, 4)
    idade = st.number_input("Idade", 5, 30, 17)
    participacao = st.number_input("IPS", 0.0, 10.0, 5.0)

    if st.button("Prever risco"):
        payload = {
            "student_id": student_id,
            "nota_portugues": nota_portugues,
            "nota_matematica": nota_matematica,
            "nota_ciencias": nota_ciencias,
            "faltas": faltas,
            "idade": idade,
            "participacao": participacao,
        }

        response = requests.post(
            f"{PREDICT_API_URL}predict",
            json=payload,
            timeout=120,
        )

        st.write("Status:", response.status_code)
        try:
            result = response.json()
            st.json(result)
            if "risk_score" in result:
                st.metric("Risk Score", result["risk_score"])
            if "risk_category" in result:
                st.metric("Categoria", result["risk_category"])
        except Exception:
            st.text(response.text)