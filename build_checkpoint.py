"""Downloadsに保存された学習済み重み・ラベルと、手元の評価結果から
artifacts/author_classifier.pt (本番用チェックポイント) を組み立てるスクリプト。

前提:
  - PTH_PATH: state_dict/labels/input_dim/hidden_dim を含む辞書として
    torch.save されたファイル(Dropout(0.3)込みのアーキテクチャで学習済み)
  - LABELS_JSON_PATH: 出力インデックス順の作家名リスト(PTH内のlabelsと一致するはずだが、
    念のため突き合わせて検証する)
  - METRICS: balanced_accuracy_mean/std は5回実験(different splits)の平均・標準偏差、
    macro_f1/per_class_f1 は実際にデプロイする最終モデル1回分の classification report から。
    (この重みを学習した回とは別の回の評価結果を流用している。ユーザー了承済み)

使い方 (太宰治判定器_webApp ディレクトリから):
    python build_checkpoint.py
"""
import json
from pathlib import Path

import torch

from app.model import AuthorClassifier

PTH_PATH = Path(__file__).resolve().parent / "author_classifier_9authors (2).pth"
LABELS_JSON_PATH = Path("/Users/fukudataketo/Downloads/author_classifier_9authors_labels.json")
OUT_PATH = Path(__file__).resolve().parent / "artifacts" / "author_classifier.pt"

WINDOW_SIZE = 200

# 5回実験(異なるtrain/test分割)のBalanced Accuracy平均・標準偏差
BALANCED_ACCURACY_MEAN = 0.6829754293164976
BALANCED_ACCURACY_STD = 0.015012229459588905

# 実際にデプロイする最終モデル1回分の classification report より
MACRO_F1 = 0.6285804640787831
PER_CLASS_F1 = {
    "太宰治": 0.630,
    "夏目漱石": 0.536,
    "泉鏡花": 0.843,
    "織田作之助": 0.596,
    "坂口安吾": 0.754,
    "森鴎外": 0.644,
    "菊池寛": 0.353,
    "夢野久作": 0.757,
    "宮沢賢治": 0.544,
}


def main():
    raw = torch.load(PTH_PATH, map_location="cpu")

    with open(LABELS_JSON_PATH, encoding="utf-8") as f:
        labels_from_json = json.load(f)

    assert raw["labels"] == labels_from_json, (
        f".pth内のlabelsと.jsonのlabelsが一致しません: {raw['labels']} != {labels_from_json}"
    )
    assert set(raw["labels"]) == set(PER_CLASS_F1.keys()), (
        "labelsとPER_CLASS_F1のキーが一致しません。"
    )

    # 実際に app/model.py の現在の構造でロードできるか検証する
    # (strictモードなのでキーが1つでもズレていればここで例外になる)
    model = AuthorClassifier(
        input_dim=raw["input_dim"],
        hidden_dim=raw["hidden_dim"],
        num_classes=len(raw["labels"]),
    )
    model.load_state_dict(raw["state_dict"], strict=True)

    checkpoint = {
        "state_dict": raw["state_dict"],
        "labels": raw["labels"],
        "input_dim": raw["input_dim"],
        "hidden_dim": raw["hidden_dim"],
        "window_size": WINDOW_SIZE,
        "metrics": {
            "balanced_accuracy_mean": BALANCED_ACCURACY_MEAN,
            "balanced_accuracy_std": BALANCED_ACCURACY_STD,
            "macro_f1": MACRO_F1,
            "per_class_f1": PER_CLASS_F1,
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, OUT_PATH)

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"保存しました: {OUT_PATH} ({size_kb:.1f} KB)")
    print(f"クラス数: {len(raw['labels'])}")
    print("load_state_dict(strict=True) 検証: OK")


if __name__ == "__main__":
    main()
