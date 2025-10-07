import streamlit as st
import pandas as pd
import numpy as np
import joblib
import datetime
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
load_dotenv()
path_training= os.getenv('TRAINING_DATA_PATH')
path_model = os.getenv('MODEL_PATH')

# -----------------------------
# 🔧 Configurações iniciais
# -----------------------------
st.set_page_config(
    page_title="Predição Semanal - Cepea",
    page_icon="📈",
    layout="wide"
)

# -----------------------------
# 📦 Carregar modelo e dados
# -----------------------------
def get_file(path, tipo):
    print(path, tipo)
    return [f for f in os.listdir(path) if tipo in f.lower()][0]

@st.cache_resource
def load_model():
    return joblib.load(f"{path_model}/{get_file(path_model, '.pkl')}")

@st.cache_data
def load_data():
    dados_agrupados = pd.read_csv(f"{path_training}/{get_file(path_training, '.csv')}", sep=';', decimal='.')
    return dados_agrupados

model = load_model()
dados_agrupados = load_data()

# -----------------------------
# 🗂️ Criar abas
# -----------------------------
aba_predicao, aba_agrupado = st.tabs(["📊 Predição", "🧩 Dados Agrupados"])

# -----------------------------
# 🧮 Aba 1 - Predição
# -----------------------------
with aba_predicao:
    st.header("📈 Predição de Preços - Próxima Semana")

    # Campo de data: usuário escolhe dentro de 7 dias a partir de hoje
    hoje = datetime.date.today()
    data_inicial = st.date_input(
        "Selecione a data de início da previsão:",
        min_value=hoje,
        max_value=hoje + datetime.timedelta(days=7),
        value=hoje
    )

    st.subheader("🌦️ Parâmetros climáticos médios")
    col1, col2, col3 = st.columns(3)
    temperature_2m_max = col1.number_input("Temperatura Máxima (°C)", value=30.0)
    temperature_2m_min = col2.number_input("Temperatura Mínima (°C)", value=20.0)
    wind_speed_10m_max = col3.number_input("Velocidade Máx. do Vento (m/s)", value=5.0)

    col4, col5, col6, col7 = st.columns(4)
    rain_sum = col4.number_input("Chuva acumulada (mm)", value=15.0)
    precipitation_hours = col5.number_input("Horas de precipitação", value=3.0)
    rain = col6.number_input("Probabilidade de chuva (%)", value=70.0)
    dias_previsao = col7.slider("Dias para prever", min_value=3, max_value=14, value=7)

    # Botão de previsão
    if st.button("🚀 Gerar previsão"):
        datas = pd.date_range(data_inicial, periods=dias_previsao, freq='D')

        # Monta DataFrame com as features climáticas
        X_novo = pd.DataFrame({
            'date': datas,
            'temperature_2m_max': np.random.normal(temperature_2m_max, 1.5, len(datas)),
            'temperature_2m_min': np.random.normal(temperature_2m_min, 1.5, len(datas)),
            'wind_speed_10m_max': np.random.normal(wind_speed_10m_max, 1.0, len(datas)),
            'rain_sum': np.random.normal(rain_sum, 2.0, len(datas)),
            'rain': np.random.normal(rain, 5.0, len(datas)),
            'precipitation_hours': np.random.normal(precipitation_hours, 1.0, len(datas)),
        })

        # 🔧 Adiciona features derivadas da data
        X_novo['month'] = X_novo['date'].dt.month
        X_novo['day_of_week'] = X_novo['date'].dt.dayofweek
        X_novo['year'] = X_novo['date'].dt.year

        # 🧠 Ordena as colunas exatamente como no fit
        feature_order = [
            'temperature_2m_max',
            'temperature_2m_min',
            'wind_speed_10m_max',
            'rain_sum',
            'rain',
            'precipitation_hours',
            'month',
            'day_of_week',
            'year'
        ]

        X_model = X_novo[feature_order]

        # 🔮 Fazer a previsão (duas saídas)
        previsoes = model.predict(X_model)

        # O modelo retorna dois preços — BR e US
        resultados = X_novo.copy()
        resultados['price_br_pred'] = previsoes[:, 0]
        resultados['price_us_pred'] = previsoes[:, 1]

        st.success("✅ Previsões geradas com sucesso!")

        # Slider para exibir registros
        n = st.slider("Quantidade de registros a exibir:", min_value=5, max_value=len(resultados), value=10)

        # 📋 Mostrar tabela
        st.subheader("📋 Tabela de Previsões")
        st.dataframe(resultados[['date', 'price_br_pred', 'price_us_pred']].head(n), use_container_width=True)

        # 📊 Gráficos
        st.subheader("📊 Gráfico da Previsão de Preços")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(resultados['date'], resultados['price_br_pred'], marker='o', label="Preço BR (R$)")
        ax.plot(resultados['date'], resultados['price_us_pred'], marker='s', label="Preço US ($)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Preço Previsto")
        ax.set_title("Tendência prevista de preços - próximos dias")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)


# -----------------------------
# 🧩 Aba 3 - Dados agrupados
# -----------------------------
with aba_agrupado:
    st.header("🧩 Dados Agrupados - Visualização Interativa")

    # Garantir que a coluna de data está no formato correto
    if 'date' in dados_agrupados.columns:
        dados_agrupados['date'] = pd.to_datetime(dados_agrupados['date'], errors='coerce')

    # Filtros de ano e mês
    anos = sorted(dados_agrupados['date'].dt.year.dropna().unique())
    ano_selecionado = st.selectbox("📅 Selecione o ano:", anos, index=len(anos)-1)

    meses = sorted(dados_agrupados[dados_agrupados['date'].dt.year == ano_selecionado]['date'].dt.month.unique())
    nome_meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                  7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

    mes_selecionado_num = st.selectbox("📆 Selecione o mês:", meses, format_func=lambda x: nome_meses[x])

    # Filtrar o DataFrame
    df_filtrado = dados_agrupados[
        (dados_agrupados['date'].dt.year == ano_selecionado) &
        (dados_agrupados['date'].dt.month == mes_selecionado_num)
    ].sort_values('date')

    # Slider para limitar a quantidade de registros mostrados
    qtd = st.slider("Quantidade de registros a exibir:", min_value=5, max_value=len(df_filtrado), value=min(10, len(df_filtrado)))

    # Tabela com os dados filtrados
    st.subheader("📋 Tabela de Dados Agrupados")
    st.dataframe(df_filtrado.head(qtd), use_container_width=True)

    # Gráfico de preços por data
    st.subheader("📊 Gráfico de Preço por Data")
    if {'price_br', 'price_us'}.issubset(df_filtrado.columns):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(df_filtrado['date'], df_filtrado['price_br'], marker='o', label="Preço BR (R$)")
        ax.plot(df_filtrado['date'], df_filtrado['price_us'], marker='s', label="Preço US ($)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Preço")
        ax.set_title(f"Preços - {nome_meses[mes_selecionado_num]} / {ano_selecionado}")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
    else:
        st.warning("As colunas 'price_br' e 'price_us' não foram encontradas no arquivo.")

