import os
import torch
import mlflow
import pandas as pd
from dotenv import load_dotenv
from torch.utils.data import DataLoader
from mlflow.tracking import MlflowClient
from sklearn.preprocessing import MinMaxScaler

from prepare_data import TimeSeriesDataset
from lstm_model import LSTMPredictor
from validation_model import ValidationModel
from scaler import save_scaler

load_dotenv()

PATH_PROCESSED = os.getenv("PATH_PROCESSED")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

MODEL_PATH  = os.getenv("MODEL_PATH")
SCALER_PATH = os.getenv("SCALER_PATH")

mlflow.set_experiment("NTDOY_LSTM")


def build_loaders(X_train, y_train, X_test, y_test, seq_len, batch_size=32):
    train_ds = TimeSeriesDataset(X_train, y_train, seq_len)
    test_ds  = TimeSeriesDataset(X_test, y_test, seq_len)

    return (
        DataLoader(train_ds, batch_size=batch_size, shuffle=False),
        DataLoader(test_ds, batch_size=batch_size, shuffle=False),
    )


def train_model(
    X_train,
    y_train,
    X_test,
    y_test,
    seq_len,
    input_size=1,
    hidden_size=32,
    num_layers=1,
    epochs=50,
    lr=1e-3,
):
    train_loader, test_loader = build_loaders(
        X_train, y_train, X_test, y_test, seq_len
    )

    model = LSTMPredictor(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
    ).to(DEVICE)

    criterion = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    validator = ValidationModel(model, DEVICE)

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0

        for X, y in train_loader:
            X, y = X.to(DEVICE), y.to(DEVICE)

            optimizer.zero_grad()
            preds = model(X).squeeze()
            loss = criterion(preds, y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        validator.reset()
        val_loss = 0.0

        for X_val, y_val in test_loader:
            val_loss += validator.validate_batch(X_val, y_val, criterion)

        val_loss /= len(test_loader)
        metrics = validator.compute_metrics()

        mlflow.log_metrics(
            {
                "train_loss": train_loss,
                "val_loss": val_loss,
                "rmse": metrics["rmse"],
                "mae": metrics["mae"],
                "directional_accuracy": metrics["directional_accuracy"],
            },
            step=epoch,
        )

        if (epoch + 1) % 10 == 0:
            print(
                f"Epoch [{epoch+1}/{epochs}] | "
                f"Train Loss: {train_loss:.6f} | "
                f"Val Loss: {val_loss:.6f}"
            )

    return model, metrics


def save_model(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)


if __name__ == "__main__":

    df = pd.read_csv(PATH_PROCESSED)

    if "Close" not in df.columns:
        raise ValueError("CSV precisa conter a coluna 'Close'")

    df = df[["Close"]].dropna()

    scaler = MinMaxScaler()
    scaled_close = scaler.fit_transform(df[["Close"]].values)

    X = scaled_close.astype("float32")
    y = scaled_close.squeeze().astype("float32")

    split_idx = int(len(X) * 0.8)

    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    model_name = "NTDOY_LSTM"

    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "seq_len": 30,
                "hidden_size": 32,
                "num_layers": 1,
                "epochs": 50,
                "lr": 1e-3,
                "features": 1,
                "target": "Close",
            }
        )

        model, metrics = train_model(
            X_train, y_train, X_test, y_test,
            seq_len=30,
            input_size=1,
            epochs=50,
        )

        save_model(model, MODEL_PATH)
        save_scaler(scaler, SCALER_PATH)

        mlflow.log_artifact(MODEL_PATH)
        mlflow.log_artifact(SCALER_PATH)

        client = MlflowClient()

        if model_name not in [m.name for m in client.search_registered_models()]:
            client.create_registered_model(model_name)

        model_uri = f"runs:/{run.info.run_id}/{MODEL_PATH}"

        mv = client.create_model_version(
            name=model_name,
            source=model_uri,
            run_id=run.info.run_id,
        )

        client.transition_model_version_stage(
            name=model_name,
            version=mv.version,
            stage="Production",
            archive_existing_versions=True,
        )

        print(f"Modelo registrado como {model_name} (Production)")
        print("Métricas finais:", metrics)
