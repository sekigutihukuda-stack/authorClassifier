import re

# 推論時の窓分割ストライド。訓練時(stride=50)とは別に、
# ユーザー入力を欠落なくカバーしつつ窓数を抑えるため 100 を使う。
INFERENCE_STRIDE = 100

_HEADER_SEP = "-------------------------------------------------------"


def clean_aozora_text(text: str) -> str:
    """青空文庫テキストからルビ・注記・ヘッダ/フッタ・改行を除去する。

    学習データ生成時と同一のロジック(青空文庫の記法に対応)。
    """
    if _HEADER_SEP in text:
        parts = text.split(_HEADER_SEP)
        if len(parts) >= 3:
            text = parts[2]

    if "底本：" in text:
        text = text.split("底本：")[0]

    # ルビ除去
    text = re.sub(r"《.*?》", "", text)

    # 注記除去
    text = re.sub(r"［＃.*?］", "", text)

    # 縦棒除去
    text = text.replace("｜", "")

    # 改行整理
    text = re.sub(r"\n+", "\n", text)

    # 改行コード除去
    text = text.replace("\r", "")
    text = text.replace("\n", "")

    return text.strip()


def make_windows(
    text: str,
    window_size: int,
    stride: int = INFERENCE_STRIDE,
) -> list[str]:
    """テキストを window_size 文字の窓に分割する。

    window_size 未満の入力はそのまま1件として扱う。
    末尾が stride で割り切れず取りこぼされる場合は、末尾に届く窓を1つ追加する。
    """
    n = len(text)

    if n <= window_size:
        return [text]

    windows = []
    i = 0
    while i + window_size <= n:
        windows.append(text[i : i + window_size])
        i += stride

    last_start = n - window_size
    if not windows or windows[-1] != text[last_start:n]:
        windows.append(text[last_start:n])

    return windows
