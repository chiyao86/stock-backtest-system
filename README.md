<<<<<<< HEAD
# stock-backtest-system
=======
# 📈 股票回測分析系統

自動化股票量化回測平台 — 從資料爬取到 AI 投資分析，一條龍完成。

## 功能特色

| 模組 | 功能 |
|------|------|
| **爬蟲** | 用 yfinance 爬取美股 / 台股歷史資料，存入 PostgreSQL |
| **回測** | 三種策略（SMA 交叉、RSI、MACD）× VectorBT 回測引擎 |
| **圖表** | K 線 + 布林通道 + MACD + RSI 技術分析圖、回測結果圖 |
| **AI 分析** | Groq AI（Llama 3.3 70B）生成專業投資分析報告 |
| **通知** | LINE Push 推送分析結果 |
| **前端** | Streamlit 互動式 Web 介面 |

## 專案結構

```
├── app.py                  # CLI 主入口（python app.py）
├── streamlit_app.py        # Streamlit Web 前端（streamlit run streamlit_app.py）
├── config.py               # 統一設定（DB / API Key / 路徑）
├── services/
│   ├── __init__.py
│   ├── crawler.py          # 股票爬蟲（yfinance → PostgreSQL）
│   ├── backtest.py         # 回測引擎（指標 / 訊號 / VectorBT）
│   ├── analyzer.py         # Groq AI 分析
│   └── notifier.py         # LINE Push 推送
├── 回測報告/               # 輸出資料夾（HTML 報告 / PNG 圖表）
├── .env                    # 環境變數（API Key 等）
└── requirements.txt        # Python 依賴
```

## 技術棧

- **語言**：Python 3.11
- **資料庫**：PostgreSQL
- **回測引擎**：VectorBT + Numba JIT 加速
- **技術指標**：Pandas 原生計算（SMA / EMA / MACD / RSI / 布林通道 / ATR）
- **報告**：QuantStats HTML 報告
- **AI**：Groq API（Llama 3.3 70B）
- **通知**：LINE Bot SDK（Push Message）
- **前端**：Streamlit
- **視覺化**：Matplotlib

## 快速開始

### 1. 環境設定

```bash
# 建立 conda 環境
conda create -n stock_py311 python=3.11 -y
conda activate stock_py311

# 安裝依賴
pip install -r requirements.txt
```

### 2. 設定 `.env`

```env
LINE_CHANNEL_ACCESS_TOKEN=你的LINE_TOKEN
LINE_CHANNEL_SECRET=你的LINE_SECRET
LINE_USER_ID=你的LINE_USER_ID

GROQ_API_KEY=你的GROQ_API_KEY

# 資料庫（選填，預設值已寫在 config.py）
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=stock_db
# DB_USER=postgres
# DB_PASSWORD=5432
```

### 3. 確認 PostgreSQL

確保 PostgreSQL 已啟動，資料表會在首次爬取時自動建立。

### 4. 執行

**CLI 模式**（終端互動）：
```bash
python app.py
```

**Web 模式**（Streamlit）：
```bash
streamlit run streamlit_app.py
```

## 回測策略

| 策略 | 邏輯 |
|------|------|
| **SMA Cross** | SMA20 與 SMA60 黃金交叉買入、死亡交叉賣出 |
| **RSI** | RSI14 跌破 30 後回升買入、突破 70 後回落賣出 |
| **MACD** | MACD 線上穿訊號線買入、下穿賣出 |

三種策略會在每次執行時全部跑完，方便比較。

## 流程圖

```
使用者輸入股票代碼 + 日期範圍
        ↓
  STEP 1：yfinance 爬取 → PostgreSQL
        ↓
  STEP 2：計算技術指標 → 三種策略回測
        ↓  產出：技術分析圖 / 回測結果圖 / HTML 報告
  STEP 3：Groq AI 分析每份報告
        ↓
  STEP 4：LINE Push 推送結果
```

## API Key 取得

| 服務 | 取得方式 |
|------|---------|
| **Groq API** | [Groq Console](https://console.groq.com/) → 免費註冊 → API Keys |
| **LINE Bot** | [LINE Developers](https://developers.line.biz/) → 建立 Provider + Channel |
>>>>>>> 8b5cef9 (Initial commit)
