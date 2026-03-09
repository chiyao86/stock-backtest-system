"""
股票回測分析系統 — Streamlit 前端
啟動：streamlit run streamlit_app.py
"""

import streamlit as st
import time
from pathlib import Path
from config import REPORT_DIR, INIT_CASH, DEFAULT_FEES, DEFAULT_SLIPPAGE

st.set_page_config(page_title="📈 股票回測分析系統", layout="wide")

# ═══════════════════════════════════════════════════════
# 側邊欄：使用者輸入
# ═══════════════════════════════════════════════════════
st.sidebar.title("📈 股票回測分析系統")
st.sidebar.markdown("---")

# 股票代碼
symbols_input = st.sidebar.text_input(
    "股票代碼（多支用逗號分隔）",
    value="AAPL,TSLA",
    placeholder="AAPL,TSLA,2330.TW"
)

# 日期
col1, col2 = st.sidebar.columns(2)
from datetime import date, timedelta
start_date = col1.date_input("開始日期", value=date.today() - timedelta(days=365))
end_date   = col2.date_input("結束日期", value=date.today())

st.sidebar.markdown("---")
st.sidebar.subheader("回測參數")

init_cash = st.sidebar.number_input("初始資金 (USD)", value=INIT_CASH, step=10000, min_value=1000)
fees      = st.sidebar.number_input("手續費率", value=DEFAULT_FEES, step=0.0001, format="%.6f")
slippage  = st.sidebar.number_input("滑價比率", value=DEFAULT_SLIPPAGE, step=0.0001, format="%.4f")

st.sidebar.markdown("---")
st.sidebar.subheader("執行步驟")
do_crawl   = st.sidebar.checkbox("1. 爬取股票資料", value=True)
do_backtest = st.sidebar.checkbox("2. 回測分析（全策略）", value=True)
do_analyze = st.sidebar.checkbox("3. Groq AI 分析", value=True)
do_notify  = st.sidebar.checkbox("4. LINE 推送", value=False)

run_btn = st.sidebar.button("🚀 開始執行", type="primary", use_container_width=True)


# ═══════════════════════════════════════════════════════
# 主畫面
# ═══════════════════════════════════════════════════════
st.title("📈 股票回測分析系統")

# 顯示現有報告
tab_run, tab_reports = st.tabs(["🔄 執行分析", "📁 歷史報告"])


with tab_reports:
    report_files = sorted(REPORT_DIR.glob("*.html"))
    if report_files:
        st.success(f"共有 {len(report_files)} 份報告")
        for f in report_files:
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"📄 {f.name}")
            with open(f, "r", encoding="utf-8") as fh:
                col_b.download_button("下載", fh.read(), file_name=f.name, mime="text/html",
                                      key=f"dl_{f.name}")

    # 顯示圖片
    image_files = sorted(REPORT_DIR.glob("*.png"))
    if image_files:
        st.markdown("---")
        st.subheader("📊 圖表")
        for img in image_files:
            st.image(str(img), caption=img.name, use_container_width=True)
    elif not report_files:
        st.info("尚無任何報告，請先執行分析")


with tab_run:
    if not run_btn:
        st.info("👈 在左側設定參數後按「開始執行」")
        st.stop()

    # 解析股票代碼
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    if not symbols:
        st.error("請輸入至少一支股票代碼")
        st.stop()

    start_str = start_date.strftime("%Y-%m-%d")
    end_str   = end_date.strftime("%Y-%m-%d")

    ALL_STRATEGIES = ["sma_cross", "rsi", "macd"]

    st.markdown(f"**股票：** {', '.join(symbols)} &nbsp;|&nbsp; "
                f"**期間：** {start_str} ~ {end_str} &nbsp;|&nbsp; "
                f"**資金：** ${init_cash:,.0f}")

    progress = st.progress(0)
    log_area = st.empty()

    total_steps = len(symbols) * (
        (1 if do_crawl else 0) +
        (1 if do_backtest else 0) +
        (len(ALL_STRATEGIES) if do_analyze else 0) +
        (1 if do_notify else 0)
    )
    current_step = 0

    for idx, symbol in enumerate(symbols):
        st.markdown(f"### 🔄 [{idx+1}/{len(symbols)}] {symbol}")

        # STEP 1 — 爬蟲
        if do_crawl:
            with st.spinner(f"📡 爬取 {symbol} ..."):
                from services.crawler import crawl_stock
                count = crawl_stock(symbol, start_str, end_str)
                st.success(f"爬取完成：{count} 筆")
                current_step += 1
                progress.progress(current_step / max(total_steps, 1))

        # STEP 2 — 回測（全策略）
        if do_backtest:
            with st.spinner(f"📊 回測 {symbol}（全策略）..."):
                import matplotlib
                matplotlib.use("Agg")  # 避免 plt.show() 阻塞
                import matplotlib.pyplot as plt
                _orig_show = plt.show
                plt.show = lambda *a, **kw: None  # 攔截 plt.show()

                from services.backtest import run_all_strategies
                results = run_all_strategies(
                    symbol, start_str, end_str,
                    init_cash=init_cash, fees=fees, slippage=slippage
                )

                plt.show = _orig_show

            if results:
                st.success(f"回測完成：{len(results)} 種策略")

                # 顯示回測圖片
                for strat in ALL_STRATEGIES:
                    img_path = REPORT_DIR / f"{symbol}_{strat}_回測結果.png"
                    if img_path.exists():
                        st.image(str(img_path), caption=f"{symbol} - {strat}", use_container_width=True)

                tech_img = REPORT_DIR / f"{symbol}_技術分析.png"
                if tech_img.exists():
                    st.image(str(tech_img), caption=f"{symbol} 技術分析", use_container_width=True)

                # 顯示績效摘要
                for strat, pf in results.items():
                    stats = pf.stats()
                    with st.expander(f"📋 {strat} 績效摘要"):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("總報酬率", f"{stats.get('Total Return [%]', 0):.2f}%")
                        col2.metric("最大回撤", f"{stats.get('Max Drawdown [%]', 0):.2f}%")
                        col3.metric("夏普比率", f"{stats.get('Sharpe Ratio', 0):.2f}")
                        col4.metric("勝率", f"{stats.get('Win Rate [%]', 0):.1f}%")

            current_step += 1
            progress.progress(current_step / max(total_steps, 1))

        # STEP 3 — AI 分析
        if do_analyze:
            from services.analyzer import analyze_report
            for strat in ALL_STRATEGIES:
                report_file = REPORT_DIR / f"{symbol}_{strat}_report.html"
                if not report_file.exists():
                    current_step += 1
                    progress.progress(current_step / max(total_steps, 1))
                    continue

                with st.spinner(f"🤖 AI 分析 {symbol} [{strat}] ..."):
                    analysis = analyze_report(symbol, report_file=report_file)

                if analysis:
                    with st.expander(f"🤖 AI 分析：{symbol} [{strat}]", expanded=(idx == 0)):
                        st.markdown(analysis)

                    # 暫存分析結果供 LINE 推送
                    if "analyses" not in st.session_state:
                        st.session_state.analyses = []
                    st.session_state.analyses.append((symbol, strat, analysis))

                current_step += 1
                progress.progress(current_step / max(total_steps, 1))
                time.sleep(2)

        # STEP 4 — LINE 推送
        if do_notify and "analyses" in st.session_state:
            with st.spinner(f"📤 LINE 推送 {symbol} ..."):
                from services.notifier import send_analysis_report
                for sym, strat, analysis in st.session_state.analyses:
                    if sym == symbol:
                        header = f"📊 {sym} [{strat}] 回測分析\n{'='*30}\n\n"
                        send_analysis_report(sym, header + analysis)
                        time.sleep(1)
                st.success(f"{symbol} LINE 推送完成")
            current_step += 1
            progress.progress(current_step / max(total_steps, 1))

    progress.progress(1.0)
    st.balloons()
    st.success(f"🎉 全部完成！共處理 {len(symbols)} 支股票 × {len(ALL_STRATEGIES)} 種策略")
