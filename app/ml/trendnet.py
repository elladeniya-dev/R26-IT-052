"""TrendNet architecture. Do not change without retraining — weights are fit to this exact shape.
See docs/trend-engine-guide.html."""
import torch
import torch.nn as nn


class TrendNet(nn.Module):
    def __init__(self, hid: int = 64, n_type: int = 8, emb: int = 8):
        super().__init__()
        self.emb = nn.Embedding(n_type, emb)
        self.gru = nn.GRU(1, hid, batch_first=True)
        self.fuse = nn.Sequential(
            nn.Linear(hid + emb + 1, 48), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(48, 24), nn.ReLU(),
            nn.Linear(24, 1),
        )

    def forward(self, x: torch.Tensor, tid: torch.Tensor, logscale: torch.Tensor) -> torch.Tensor:
        o, _ = self.gru(x.unsqueeze(-1))
        h = torch.cat([o[:, -1], self.emb(tid), logscale.unsqueeze(-1)], dim=1)
        return self.fuse(h).squeeze(-1)


def load_trendnet(path: str) -> tuple[TrendNet, dict]:
    """Returns (model, checkpoint_meta)."""
    ck = torch.load(path, map_location="cpu", weights_only=False)
    model = TrendNet()
    model.load_state_dict(ck["state_dict"])
    model.eval()
    return model, ck
