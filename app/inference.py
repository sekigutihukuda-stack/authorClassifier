from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from .model import AuthorClassifier
from .preprocess import clean_aozora_text, make_windows

SBERT_MODEL_NAME = "intfloat/multilingual-e5-base"


class AuthorPredictor:
    """チェックポイントと SBERT を保持し、テキストから作家を推論する。

    起動時(FastAPI lifespan)に一度だけインスタンス化される想定。
    """

    def __init__(self, checkpoint_path: Path) -> None:
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"モデルファイルが見つかりません: {checkpoint_path}\n"
                "README.md の手順に従って artifacts/author_classifier.pt を配置してください。"
            )

        ckpt = torch.load(checkpoint_path, map_location="cpu")

        self.labels: list[str] = ckpt["labels"]
        self.input_dim: int = ckpt["input_dim"]
        self.hidden_dim: int = ckpt["hidden_dim"]
        self.window_size: int = ckpt["window_size"]
        self.metrics: dict[str, Any] = ckpt["metrics"]

        self.model = AuthorClassifier(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            num_classes=len(self.labels),
        )
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.eval()

        self.sbert = SentenceTransformer(SBERT_MODEL_NAME, device="cpu")

    def predict(self, raw_text: str) -> dict[str, Any]:
        text = clean_aozora_text(raw_text)
        if not text:
            raise ValueError("入力テキストから有効な本文を抽出できませんでした。")

        windows = make_windows(text, window_size=self.window_size)

        embeddings = self.sbert.encode(windows, convert_to_numpy=True)
        x = torch.tensor(embeddings, dtype=torch.float32)

        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1).numpy()

        mean_probs = probs.mean(axis=0)
        std_probs = probs.std(axis=0)

        order = np.argsort(-mean_probs)

        results = [
            {
                "author": self.labels[i],
                "probability": float(mean_probs[i]),
                "std": float(std_probs[i]),
            }
            for i in order
        ]

        return {
            "results": results,
            "top_label": self.labels[int(order[0])],
            "num_windows": len(windows),
            "char_count": len(text),
        }
