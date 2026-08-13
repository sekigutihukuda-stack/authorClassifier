import torch.nn as nn


class AuthorClassifier(nn.Module):
    """768(SBERT) -> hidden -> hidden -> num_classes の MLP。"""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        num_classes: int,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x):
        return self.network(x)
