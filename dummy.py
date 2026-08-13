"""ダミーのチェックポイントを生成するスクリプト。

本物の学習済み重みができるまでの仮置き用。
重みはランダム初期化なので予測はでたらめだが、
ファイル形式は本物と完全に同一なので、
ロード処理・API・UI の実装と動作確認はこれで進められる。

使い方 (太宰治判定器_webApp ディレクトリから、app パッケージを import できる状態で実行):
    python dummy.py
"""
from pathlib import Path

import torch

from app.model import AuthorClassifier


# ============================================================
# 設定
# ============================================================

# 重要: この順序は学習時の label_map と完全に一致させること。
# ズレてもエラーは出ず、全ての予測が違う名前で表示される。
LABELS = [
    "太宰治",
    "夏目漱石",
    "泉鏡花",
    "織田作之助",
    "坂口安吾",
    "森鴎外",
    "菊池寛",
    "夢野久作",
    "宮沢賢治",
]

INPUT_DIM = 768
HIDDEN_DIM = 128
WINDOW_SIZE = 200

OUT_PATH = Path(__file__).resolve().parent / "artifacts" / "author_classifier.pt"


# ============================================================
# 生成
# ============================================================

def main():
    # app/model.py の AuthorClassifier とコンストラクタ引数を完全に一致させること。
    model = AuthorClassifier(
        input_dim=INPUT_DIM,
        hidden_dim=HIDDEN_DIM,
        num_classes=len(LABELS),
    )

    # app/inference.py の AuthorPredictor が読むキーと完全に一致させること
    # (README.md のチェックポイント契約を参照)。
    ckpt = {
        # ---- 必須 ----
        "state_dict": model.state_dict(),
        "labels": LABELS,

        # ---- 構造の再現に必要 ----
        "input_dim": INPUT_DIM,
        "hidden_dim": HIDDEN_DIM,

        # ---- 前処理の再現に必要 ----
        "window_size": WINDOW_SIZE,

        # ---- UI 表示用の性能指標 ----
        "metrics": {
            "balanced_accuracy_mean": 0.687,
            "balanced_accuracy_std": 0.018,
            "macro_f1": 0.647,
            "per_class_f1": {
                "太宰治": 0.657,
                "夏目漱石": 0.633,
                "泉鏡花": 0.830,
                "織田作之助": 0.605,
                "坂口安吾": 0.785,
                "森鴎外": 0.634,
                "菊池寛": 0.387,
                "夢野久作": 0.779,
                "宮沢賢治": 0.515,
            },
        },

        # ---- ダミーであることの明示 ----
        "is_dummy": True,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(ckpt, OUT_PATH)

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"保存しました: {OUT_PATH} ({size_kb:.1f} KB)")
    print(f"クラス数: {len(LABELS)}")
    print("警告: これはダミーです。重みはランダム初期化されています。")


if __name__ == "__main__":
    main()