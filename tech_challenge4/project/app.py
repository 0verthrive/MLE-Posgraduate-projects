import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from source.inference import load_model, predict_next_days
from source.scaler import load_scaler

# ------------------------------------------------------------------
# Configurações iniciais
# ------------------------------------------------------------------
load_dotenv()
st.set_page_config(page_title="NTDOY Forecast", layout="wide")

SEQ_LEN = 30
N_DAYS = 5

# ------------------------------------------------------------------
# Carregamento do modelo e scaler (SEM MLflow)
# ------------------------------------------------------------------
@st.cache_resource
def load_production_assets():
    model_path = os.getenv("MODEL_PATH")
    scaler_path = os.getenv("SCALER_PATH")

    if not model_path or not scaler_path:
        st.error("Variáveis de ambiente MODEL_PATH e SCALER_PATH não definidas.")
        st.stop()

    model = load_model(model_path)
    scaler = load_scaler(scaler_path)

    return model, scaler


# ------------------------------------------------------------------
# Carregamento dos dados processados
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    path_processed = os.getenv("PATH_PROCESSED")

    if not path_processed:
        st.error("Variável de ambiente PATH_PROCESSED não definida.")
        st.stop()

    df = pd.read_csv(path_processed)
    df["Date"] = pd.to_datetime(df["Date"])
    return df[["Date", "Close"]].dropna()


# ------------------------------------------------------------------
# Inicialização
# ------------------------------------------------------------------
model, scaler = load_production_assets()
df = load_data()

# ------------------------------------------------------------------
# Layout principal
# ------------------------------------------------------------------
st.title("📈 NTDOY - LSTM Forecast Dashboard")

tab1, tab2, tab3 = st.tabs(
    ["📈 Histórico de Preços", "📊 Treino & Volatilidade", "🔮 Previsão 5 dias"]
)

# ------------------------------------------------------------------
# TAB 1 — Histórico de preços
# ------------------------------------------------------------------
with tab1:
    st.subheader("📈 Histórico de Preços – Fechamento (Close)")

    st.markdown(
        """
        **Visão Geral**  
        Evolução histórica do preço de fechamento (**Close**) do ativo,
        com uma curva suavizada por média móvel para destacar tendências.
        """
    )

    window_smooth = 7
    close_smooth = df["Close"].rolling(window_smooth).mean()

    fig, ax = plt.subplots(figsize=(11, 4))

    ax.plot(
        df["Date"],
        df["Close"],
        label="Close (valor observado)",
        alpha=0.25,
        linewidth=1,
    )

    ax.plot(
        df["Date"],
        close_smooth,
        label=f"Tendência (Média Móvel {window_smooth})",
        linewidth=2.5,
    )

    ax.set_xlabel("Data")
    ax.set_ylabel("Preço de Fechamento")
    ax.set_title("Evolução Histórica do Preço de Fechamento")
    ax.legend()
    ax.grid(alpha=0.25)

    st.pyplot(fig)


# ------------------------------------------------------------------
# TAB 2 — Treino & Volatilidade
# ------------------------------------------------------------------
with tab2:
    st.subheader("📊 Dados de Treino & Volatilidade Histórica")

    st.markdown(
        """
        Esta aba apresenta os dados utilizados no treinamento do modelo
        e a volatilidade histórica do ativo.
        """
    )

    # Série usada no treino
    window_smooth = 7
    close_smooth = df["Close"].rolling(window_smooth).mean()

    fig_train, ax_train = plt.subplots(figsize=(11, 4))

    ax_train.plot(
        df["Date"],
        df["Close"],
        label="Close (valor observado)",
        alpha=0.25,
        linewidth=1,
    )

    ax_train.plot(
        df["Date"],
        close_smooth,
        label=f"Tendência (Média Móvel {window_smooth})",
        linewidth=2.5,
    )

    ax_train.set_xlabel("Data")
    ax_train.set_ylabel("Preço de Fechamento")
    ax_train.set_title("Dados Utilizados no Treinamento do Modelo")
    ax_train.legend()
    ax_train.grid(alpha=0.25)

    st.pyplot(fig_train)

    # Volatilidade
    vol_window = 10
    volatility = df["Close"].rolling(vol_window).std()

    fig_vol, ax_vol = plt.subplots(figsize=(11, 3))

    ax_vol.plot(
        df["Date"],
        volatility,
        label=f"Volatilidade (Std móvel {vol_window})",
        linewidth=2,
        color="orange",
    )

    ax_vol.set_xlabel("Data")
    ax_vol.set_ylabel("Volatilidade")
    ax_vol.set_title("Volatilidade Histórica")
    ax_vol.legend()
    ax_vol.grid(alpha=0.25)

    st.pyplot(fig_vol)

    st.markdown("### 🔍 Amostra dos dados utilizados pelo modelo")
    st.dataframe(
        df.tail(10).rename(columns={"Close": "Preço de Fechamento"}),
        use_container_width=True,
    )


# ------------------------------------------------------------------
# TAB 3 — Previsão 5 dias
# ------------------------------------------------------------------
with tab3:
    st.subheader("🔮 Previsão de Preços – Próximos 5 Dias")

    st.markdown(
        """
        O usuário pode **enviar dados históricos de preços**
        para obter previsões futuras geradas pelo modelo LSTM.

        - Utiliza apenas a coluna **Close**
        - Previsão **autoregressiva**
        - Horizonte de **5 dias**
        """
    )

    uploaded_file = st.file_uploader(
        "📤 Envie um arquivo CSV com histórico de preços",
        type=["csv"],
    )

    if uploaded_file is not None:
        user_df = pd.read_csv(uploaded_file)

        if "Close" not in user_df.columns:
            st.error("O arquivo precisa conter a coluna 'Close'.")
        else:
            st.success("Arquivo carregado com sucesso!")

            user_df = user_df[["Close"]].dropna()

            st.markdown("**Amostra dos dados fornecidos:**")
            st.dataframe(user_df.tail(10), use_container_width=True)

            if len(user_df) < SEQ_LEN:
                st.warning(
                    f"O modelo precisa de pelo menos {SEQ_LEN} registros para gerar previsão."
                )
            else:
                close_values = user_df["Close"].values.reshape(-1, 1)
                close_scaled = scaler.transform(close_values)

                last_window = close_scaled[-SEQ_LEN:]

                preds = predict_next_days(
                    model=model,
                    window=last_window,
                    scaler=scaler,
                    n_days=N_DAYS,
                )

                future_days = [f"Dia +{i+1}" for i in range(N_DAYS)]

                fig, ax = plt.subplots(figsize=(8, 4))

                ax.plot(
                    future_days,
                    preds,
                    marker="o",
                    linewidth=2,
                    label="Previsão LSTM",
                )

                ax.fill_between(
                    future_days,
                    preds * 0.98,
                    preds * 1.02,
                    alpha=0.2,
                    label="Faixa estimada (±2%)",
                )

                ax.set_xlabel("Horizonte de Previsão")
                ax.set_ylabel("Preço Previsto (Close)")
                ax.set_title("Previsão dos Próximos 5 Dias")
                ax.legend()
                ax.grid(alpha=0.3)

                st.pyplot(fig)

                st.metric(
                    "Último preço informado",
                    f"{user_df['Close'].iloc[-1]:.2f}",
                )
