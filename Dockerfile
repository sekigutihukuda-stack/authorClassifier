# Hugging Face Spaces (Docker SDK) 用。
# コンテナは非rootユーザー(UID 1000)で動かす必要があるため、
# それに合わせてユーザーを作成してから作業する。
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# 1. 依存関係のインストール(requirements.txt が変わらない限りキャッシュされる)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 2. SBERT (multilingual-e5-base, 約1.1GB) をビルド時にダウンロードして
#    イメージに焼き込む。実行時ダウンロードにすると、Spaceがスリープから
#    復帰するたびに毎回ダウンロードが走り、初回応答が非常に遅くなるため。
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-base')"

# 3. アプリ本体・静的ファイル・学習済みモデルは最後にCOPYする。
#    ここより上のレイヤー(pip install・SBERTダウンロード)は
#    requirements.txt を変えない限りキャッシュが効くため、
#    author_classifier.pt だけを差し替えた際の再ビルドが速くなる。
COPY --chown=user app/ app/
COPY --chown=user static/ static/
COPY --chown=user artifacts/ artifacts/

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
