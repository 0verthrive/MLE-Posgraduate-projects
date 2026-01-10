import pickle
from sklearn.preprocessing import MinMaxScaler


def save_scaler(scaler, path):
    with open(path, "wb") as f:
        pickle.dump(scaler, f)


def load_scaler(path):
    with open(path, "rb") as f:
        return pickle.load(f)
