import torch.nn as nn


class LSTMPredictor(nn.Module):
    def __init__(self, input_size, hidden_size=32, num_layers=1):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,   # = 1 (Close)
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=0.3,
            batch_first=True
        )

        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out)
