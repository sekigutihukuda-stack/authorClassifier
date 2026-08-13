import torch.nn as nn


class AuthorClassifier(nn.Module):
    """768(SBERT) -> hidden -> hidden -> num_classes の MLP。

    学習に実際に使われた重みの層構成(Dropoutなし)に合わせている。
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        num_classes: int,
    ) -> None:
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x):
        return self.network(x)
