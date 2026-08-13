# 太宰治判定機

Sentence-BERT (`intfloat/multilingual-e5-base`) + MLP による、近代日本文学9作家の文体分類 Web アプリ。

対象作家: 太宰治 / 夏目漱石 / 泉鏡花 / 坂口安吾 / 織田作之助 / 森鴎外 / 菊池寛 / 夢野久作 / 宮沢賢治

## モデルの制約(重要)

このモデルは **上記9名に限定した閉じたソフトマックス分類器** です。9名以外の作者の文章
(現代の文章など)を入力しても、必ず9名のうち誰かが最上位の結果として返ります。
出力される数値は「その作家である確率」ではなく、**「9名の中での相対的な近さ」** として
解釈してください。UI側でもこの点を常時表示しています。

全体性能: Balanced Accuracy 0.687 ± 0.018(5分割平均)、Macro F1 0.647。
クラス別 F1 が低い作家(菊池寛 0.387、宮沢賢治 0.515 など)が最上位に来た場合は、
UI 上で判定の信頼度が低い旨を警告表示します(しきい値は `/api/meta` の `per_class_f1` を
見て動的に判断しており、フロント側に作家名をハードコードしていません)。

## セットアップ

```bash
cd dazai-app  # このディレクトリ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## `artifacts/author_classifier.pt` の配置

このリポジトリには学習済み重みを含めません。以下のいずれかの方法で配置してください。

1. 既に学習済みのチェックポイントファイルがある場合は、`artifacts/author_classifier.pt`
   としてコピーする。
2. まだ無い場合は、下記「学習側での保存コード例」を使って学習スクリプト側で
   `artifacts/author_classifier.pt` を出力する。

チェックポイントは以下のキーを持つ辞書として保存されている必要があります。

| キー | 内容 |
|---|---|
| `state_dict` | `AuthorClassifier` の `state_dict()` |
| `labels` | 出力インデックス順の作家名リスト(長さ = クラス数) |
| `input_dim` | SBERT の埋め込み次元(768) |
| `hidden_dim` | MLP の隠れ層次元(128) |
| `window_size` | 学習時のスライディングウィンドウ文字数(200) |
| `metrics` | `balanced_accuracy_mean` / `balanced_accuracy_std` / `macro_f1` / `per_class_f1`(dict) |

`app/inference.py` はこの形式を前提に `len(ckpt["labels"])` からクラス数を決定するため、
作家を増減させる場合もコード変更は不要です。

### 学習側での保存コード例

```python
import torch
from sklearn.metrics import balanced_accuracy_score, f1_score

LABELS = [
    "太宰治", "夏目漱石", "泉鏡花", "坂口安吾", "織田作之助",
    "森鴎外", "菊池寛", "夢野久作", "宮沢賢治",
]

# 5分割の実験結果から算出した値をここに集計しておく想定
balanced_accuracy_mean = 0.687
balanced_accuracy_std = 0.018
macro_f1 = 0.647
per_class_f1 = {
    "泉鏡花": 0.830,
    "坂口安吾": 0.785,
    "夢野久作": 0.779,
    "太宰治": 0.657,
    "森鴎外": 0.634,
    "夏目漱石": 0.633,
    "織田作之助": 0.605,
    "宮沢賢治": 0.515,
    "菊池寛": 0.387,
}

checkpoint = {
    "state_dict": model.state_dict(),
    "labels": LABELS,
    "input_dim": 768,
    "hidden_dim": 128,
    "window_size": 200,
    "metrics": {
        "balanced_accuracy_mean": balanced_accuracy_mean,
        "balanced_accuracy_std": balanced_accuracy_std,
        "macro_f1": macro_f1,
        "per_class_f1": per_class_f1,
    },
}

torch.save(checkpoint, "artifacts/author_classifier.pt")
```

`AuthorClassifier` は `app/model.py` のものと同一構造(768→128→128→9、各隠れ層の後にReLU、
Dropoutなし)で学習してください。構造が一致しないと `load_state_dict` が失敗します。

## 起動

```bash
uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/` にアクセスすると UI が表示されます。
初回起動時は SBERT モデル(約1.1GB)のダウンロード・ロードが走るため、起動と最初の判定に
時間がかかります。

## Google Cloud Run へのデプロイ

`Dockerfile` はそのまま Cloud Run で使える(コード変更不要)。ローカルで `docker build` して
動作確認したイメージと同じものが、Cloud Build 経由でビルドされてデプロイされる。

### 初回のみのセットアップ

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成し、
   課金を有効化する(支払い方法の登録は本人確認目的。無料枠(月間リクエスト数・
   コンピュート時間など)の範囲内であれば実際の課金は発生しない。誤って有料の
   ハードウェア/リージョン設定をしないよう、後述の `--memory`・`--cpu` の値を守ること)
2. ログインとプロジェクト設定:
   ```bash
   gcloud auth login
   gcloud config set project <あなたのプロジェクトID>
   ```
3. 必要な API を有効化:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
   ```

### デプロイ

```bash
GCP_PROJECT_ID=<あなたのプロジェクトID> ./deploy.sh
```

`deploy.sh` は `gcloud run deploy --source .` を実行する。Cloud Build が `Dockerfile` を
ビルドし、Artifact Registry に push した上で Cloud Run サービスとして起動する。
`--memory 2Gi --cpu 2` を指定しているのは、SBERT + MLP の推論に Cloud Run のデフォルト
(512MiB)では不足するため。リクエストが無い間はゼロスケールし、課金されない。

`author_classifier.pt` を差し替えた後の再デプロイも、同じコマンドを再実行するだけでよい。

### リージョン・サービス名の変更

デフォルトはリージョン `asia-northeast1`(東京)、サービス名 `dazai-classifier`。
変更する場合は環境変数で上書きできる:

```bash
GCP_PROJECT_ID=<プロジェクトID> GCP_REGION=us-central1 GCP_SERVICE_NAME=my-service ./deploy.sh
```

## API

- `POST /api/predict` — `{"text": "..."}` (10〜5000文字) を受け取り、各作家の確率・
  窓ごとの標準偏差・最上位ラベル・窓数・文字数を返す。
- `GET /api/meta` — ラベル一覧とクラス別性能指標を返す(フロントはこれを見て
  ラベルや閾値判定を行い、値をハードコードしない)。

## ディレクトリ構成

```
dazai-app/
├── app/
│   ├── main.py        # FastAPI アプリ本体
│   ├── model.py        # AuthorClassifier の定義
│   ├── preprocess.py   # 青空文庫テキストのクリーニング・窓分割
│   └── inference.py    # モデルロードと predict()
├── static/              # 素の HTML/CSS/JS フロントエンド
├── artifacts/
│   └── author_classifier.pt  # 学習済み重み(別途配置)
├── requirements.txt
└── README.md
```
