(() => {
  "use strict";

  // per_class_f1 がこの値を下回る作家が最上位に来た場合、
  // 「この判定は信頼度が低い」旨を表示する。
  // (作家名を直接ハードコードせず、/api/meta の実測値で動的に判定する)
  const LOW_F1_THRESHOLD = 0.55;

  const PRESETS = [
    {
      label: "太宰治『人間失格』",
      text:
        "恥の多い生涯を送って来ました。自分には、人間の生活というものが、見当つかないのです。" +
        "自分は東北の田舎に生れましたので、汽車をはじめて見たのは、よほど大きくなってからでした。",
    },
    {
      label: "夏目漱石『こころ』",
      text:
        "私はその人を常に先生と呼んでいた。だからここでもただ先生と書くだけで本名は打ち明けない。" +
        "これは世間を憚かる遠慮というよりも、その方が私にとって自然だからである。",
    },
    {
      label: "宮沢賢治『銀河鉄道の夜』",
      text:
        "「ではみなさんは、そういうふうにこれから川だと言われたり、" +
        "乳の流れたあとだと言われたりしていたこの白いものがほんとうは何かご承知ですか。」" +
        "先生は黒板に吊した大きな黒い星座の図を指しながら、みんなに問いをかけました。",
    },
    {
      label: "森鴎外『高瀬舟』",
      text:
        "高瀬舟は、京都の高瀬川を上下する小舟である。徳川時代に京都の罪人が遠島を申し渡されると、" +
        "その罪人の親類か知友かで、いわゆる情け深い者があって、" +
        "この高瀬舟の中で暇乞いをすることを許された。",
    },
  ];

  const els = {
    authorList: document.getElementById("author-list"),
    overallMetric: document.getElementById("overall-metric"),
    presets: document.getElementById("presets"),
    textInput: document.getElementById("text-input"),
    charCounter: document.getElementById("char-counter"),
    charWarning: document.getElementById("char-warning"),
    predictBtn: document.getElementById("predict-btn"),
    loading: document.getElementById("loading"),
    errorBox: document.getElementById("error"),
    resultArea: document.getElementById("result-area"),
    resultHeadline: document.getElementById("result-headline"),
    dazaiBanner: document.getElementById("dazai-banner"),
    dazaiConfetti: document.getElementById("dazai-confetti"),
    lowConfidenceWarning: document.getElementById("low-confidence-warning"),
    bars: document.getElementById("bars"),
    resultMeta: document.getElementById("result-meta"),
  };

  const MIN_LEN = 10;
  const MAX_LEN = 5000;

  let meta = null;

  // 初回訪問時、モデルのロードが完了するまでタブのタイトルで
  // 「読み込み中で止まっているわけではない」ことを伝える。
  // (Cloud Runのコールドスタート時は特に顕著に遅くなるため)
  const DEFAULT_TITLE = document.title;
  document.title = `少々お待ちください… | ${DEFAULT_TITLE}`;

  function renderPresets() {
    for (const preset of PRESETS) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "preset-btn";
      btn.textContent = preset.label;
      btn.addEventListener("click", () => {
        els.textInput.value = preset.text;
        updateCharCounter();
        els.textInput.focus();
      });
      els.presets.appendChild(btn);
    }
  }

  function updateCharCounter() {
    const len = els.textInput.value.length;
    els.charCounter.textContent = `${len} / ${MAX_LEN}文字`;

    if (len > 0 && len < MIN_LEN) {
      els.charWarning.textContent = `あと${MIN_LEN - len}文字以上入力してください`;
    } else if (len >= MAX_LEN) {
      els.charWarning.textContent = "文字数の上限に達しています";
    } else {
      els.charWarning.textContent = "";
    }

    els.predictBtn.disabled = len < MIN_LEN || len > MAX_LEN;
  }

  async function loadMeta() {
    try {
      const res = await fetch("/api/meta");
      if (!res.ok) throw new Error("meta取得に失敗しました");
      meta = await res.json();

      els.authorList.innerHTML = "";
      for (const author of meta.labels) {
        const li = document.createElement("li");
        li.textContent = author;
        els.authorList.appendChild(li);
      }

      const mean = (meta.balanced_accuracy_mean * 100).toFixed(1);
      const std = (meta.balanced_accuracy_std * 100).toFixed(1);
      els.overallMetric.textContent =
        `全体性能(5分割平均): Balanced Accuracy ${mean}% ± ${std}% / Macro F1 ${(meta.macro_f1 * 100).toFixed(1)}%`;
    } catch (err) {
      els.authorList.innerHTML = "<li>作家一覧の取得に失敗しました</li>";
    } finally {
      document.title = DEFAULT_TITLE;
    }
  }

  function showError(message) {
    els.errorBox.textContent = message;
    els.errorBox.classList.remove("hidden");
  }

  function clearError() {
    els.errorBox.textContent = "";
    els.errorBox.classList.add("hidden");
  }

  // confetti片が古い再生タイマーで新しい演出を消してしまわないようにする世代カウンタ
  let dazaiConfettiGeneration = 0;
  const DAZAI_CONFETTI_EMOJI = ["🖋️", "✒️", "📖", "🌸", "✨"];

  function spawnDazaiConfetti() {
    const generation = ++dazaiConfettiGeneration;
    els.dazaiConfetti.innerHTML = "";

    for (let i = 0; i < 26; i++) {
      const piece = document.createElement("span");
      piece.className = "confetti-piece";
      piece.textContent =
        DAZAI_CONFETTI_EMOJI[Math.floor(Math.random() * DAZAI_CONFETTI_EMOJI.length)];
      piece.style.setProperty("--x", `${Math.random() * 100}%`);
      piece.style.setProperty("--size", `${0.9 + Math.random() * 0.9}rem`);
      piece.style.setProperty("--duration", `${1.4 + Math.random() * 1.0}s`);
      piece.style.setProperty("--delay", `${Math.random() * 0.5}s`);
      piece.style.setProperty("--drift", `${(Math.random() - 0.5) * 140}px`);
      piece.style.setProperty(
        "--spin",
        `${(Math.random() < 0.5 ? -1 : 1) * (360 + Math.random() * 360)}deg`
      );
      els.dazaiConfetti.appendChild(piece);
    }

    setTimeout(() => {
      if (dazaiConfettiGeneration === generation) {
        els.dazaiConfetti.innerHTML = "";
      }
    }, 2600);
  }

  // 最上位が太宰治だった場合だけの特別演出。
  // (低信頼度警告と違い、これは「太宰治判定器」というアプリの主題そのものへの
  // 演出なので、作家名をハードコードしてよい)
  function updateDazaiEffect(isDazai) {
    els.resultHeadline.classList.remove("dazai-detected");
    els.resultArea.classList.remove("dazai-celebrate");
    els.dazaiBanner.classList.add("hidden");
    els.dazaiBanner.innerHTML = "";
    els.dazaiConfetti.innerHTML = "";

    if (!isDazai) return;

    // アニメーションを毎回頭から再生させるため、一度クラスを外してから
    // 強制リフロー(offsetWidth参照)を挟んで付け直す。
    void els.resultHeadline.offsetWidth;
    els.resultHeadline.classList.add("dazai-detected");
    els.resultArea.classList.add("dazai-celebrate");

    els.dazaiBanner.innerHTML =
      '<span class="dazai-sparkle">🖋️</span>' +
      "太宰治の文体との一致度が際立って高いです!" +
      '<span class="dazai-sparkle">🖋️</span>';
    els.dazaiBanner.classList.remove("hidden");

    spawnDazaiConfetti();
  }

  function renderResult(data) {
    els.resultArea.classList.remove("hidden");

    const top = data.results[0];
    const isDazai = top.author === "太宰治";
    const pct = (top.probability * 100).toFixed(1);
    els.resultHeadline.textContent =
      `9名の作家の中では「${top.author}」に最も近い判定結果です(${pct}%)`;

    updateDazaiEffect(isDazai);

    const topF1 = meta ? meta.per_class_f1[top.author] : undefined;
    if (typeof topF1 === "number" && topF1 < LOW_F1_THRESHOLD) {
      els.lowConfidenceWarning.textContent =
        `「${top.author}」はこのモデルの中でも判定精度が低いクラスです` +
        `(F1スコア ${(topF1 * 100).toFixed(1)}%)。この判定結果はあまり信頼できない可能性があります。`;
      els.lowConfidenceWarning.classList.remove("hidden");
    } else {
      els.lowConfidenceWarning.classList.add("hidden");
    }

    els.bars.innerHTML = "";
    for (const item of data.results) {
      const row = document.createElement("div");
      row.className = "bar-row";

      const label = document.createElement("div");
      label.className = "bar-label";
      const pctStr = (item.probability * 100).toFixed(1);
      label.innerHTML = `<span>${item.author}</span><span>${pctStr}%</span>`;

      const isTop = item === data.results[0];
      const track = document.createElement("div");
      track.className = "bar-track";
      const fill = document.createElement("div");
      fill.className =
        "bar-fill" + (isTop ? " top" : "") + (isTop && isDazai ? " dazai" : "");
      fill.style.width = `${item.probability * 100}%`;
      track.appendChild(fill);

      const std = document.createElement("div");
      std.className = "bar-std";
      std.textContent = `窓ごとの揺れ(標準偏差): ±${(item.std * 100).toFixed(1)}%`;

      row.appendChild(label);
      row.appendChild(track);
      row.appendChild(std);
      els.bars.appendChild(row);
    }

    els.resultMeta.textContent =
      `入力文字数: ${data.char_count}文字 / 分割された窓の数: ${data.num_windows}`;
  }

  async function predict() {
    const text = els.textInput.value;
    clearError();
    els.resultArea.classList.add("hidden");
    els.predictBtn.disabled = true;
    els.loading.classList.remove("hidden");

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const detail = body && body.detail ? body.detail : `エラーが発生しました (HTTP ${res.status})`;
        throw new Error(Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : detail);
      }

      const data = await res.json();
      renderResult(data);
    } catch (err) {
      showError(err.message || "判定中にエラーが発生しました。時間をおいて再度お試しください。");
    } finally {
      els.loading.classList.add("hidden");
      updateCharCounter();
    }
  }

  els.textInput.addEventListener("input", updateCharCounter);
  els.predictBtn.addEventListener("click", predict);

  renderPresets();
  updateCharCounter();
  loadMeta();
})();
