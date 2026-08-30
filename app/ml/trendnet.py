"""
TrendNet — ported verbatim from research/trendnet_training.ipynb (cell 8) and
research/trend_engine_original.py. Do not change the architecture without
retraining: the weights in weights/outfitiq_trendnet.pt were fit to this
exact shape (embedding(8,8) -> single-layer GRU(1,64) -> Linear(73,48) ->
ReLU -> Dropout(0.2) -> Linear(48,24) -> ReLU -> Linear(24,1)).

H&M-trained at a 4-observation window: IC +0.428 (t=+16.51, n=95 overlapping
cutoffs; +0.345, t=+5.37 on 14 non-overlapping cutoffs). 17,681 params —
outperforms both zero-shot Chronos-2 (IC +0.385) and H&M LoRA-fine-tuned
Chronos-2 (IC +0.406) at ~11,600x fewer parameters. See
research/trendnet_training.ipynb for the full methodology (window-size
ablation, overfitting check, baseline comparison).

This module has no imports from the rest of app/ — see architecture spec §7.1.
"""
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
    """Returns (model, checkpoint_meta). checkpoint_meta has tmap/window/
    horizon/arch/ic/t_stat/n_cutoffs — see trend_snapshots.model_ic, which
    stores ic from here for provenance on every computed snapshot."""
    ck = torch.load(path, map_location="cpu", weights_only=False)
    model = TrendNet()
    model.load_state_dict(ck["state_dict"])
    model.eval()
    return model, ck
