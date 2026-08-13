from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .inference import AuthorPredictor

BASE_DIR = Path(__file__).resolve().parent.parent
CHECKPOINT_PATH = BASE_DIR / "artifacts" / "author_classifier.pt"
STATIC_DIR = BASE_DIR / "static"

predictor: Optional[AuthorPredictor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global predictor
    # モデルと SBERT のロードは重いため、リクエストごとではなく
    # プロセス起動時に一度だけ行う。
    predictor = AuthorPredictor(CHECKPOINT_PATH)
    yield
    predictor = None


app = FastAPI(title="太宰治判定機", lifespan=lifespan)


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000)


class AuthorScore(BaseModel):
    author: str
    probability: float
    std: float


class PredictResponse(BaseModel):
    results: list[AuthorScore]
    top_label: str
    num_windows: int
    char_count: int


class MetaResponse(BaseModel):
    labels: list[str]
    balanced_accuracy_mean: float
    balanced_accuracy_std: float
    macro_f1: float
    per_class_f1: dict[str, float]


@app.post("/api/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    # SBERT のエンコードは重い同期処理のため async def にはしない
    # (async def にするとイベントループを塞いで他のリクエストが詰まる)。
    assert predictor is not None
    try:
        result = predictor.predict(req.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PredictResponse(**result)


@app.get("/api/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    assert predictor is not None
    metrics = predictor.metrics
    return MetaResponse(
        labels=predictor.labels,
        balanced_accuracy_mean=metrics["balanced_accuracy_mean"],
        balanced_accuracy_std=metrics["balanced_accuracy_std"],
        macro_f1=metrics["macro_f1"],
        per_class_f1=metrics["per_class_f1"],
    )


# 静的ファイルは API ルート定義の後に mount する。
# 先に mount すると "/" 配下に吸収されて /api/* に到達しなくなる。
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
