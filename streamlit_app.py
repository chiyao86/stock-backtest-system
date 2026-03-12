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
    value="",
    placeholder="AAPL,TSLA,2330.TW"
)

st.sidebar.markdown("---")
st.sidebar.subheader("爬取歷史股價期間")

# 使用下拉選單選擇爬取期間
from datetime import date, timedelta

col_year, col_month, col_day = st.sidebar.columns(3)
crawl_years = col_year.selectbox("年", options=list(range(0, 11)), index=0)
crawl_months = col_month.selectbox("月", options=list(range(0, 12)), index=0)
crawl_days = col_day.selectbox("日", options=list(range(0, 366)), index=0)

# 計算爬取的開始與結束日期
end_date = date.today()
total_days = crawl_years * 365 + crawl_months * 30 + crawl_days
start_date = end_date - timedelta(days=max(total_days, 1))  # 至少1天

st.sidebar.text(f"📅 {start_date} ~ {end_date}")

st.sidebar.markdown("---")
st.sidebar.subheader("回測參數")

init_cash = st.sidebar.number_input("初始資金 (USD)", value=INIT_CASH, step=10000, min_value=1000)
fees      = st.sidebar.number_input("手續費率", value=DEFAULT_FEES, step=0.0001, format="%.6f")
slippage  = st.sidebar.number_input("滑價比率", value=DEFAULT_SLIPPAGE, step=0.0001, format="%.4f")

st.sidebar.markdown("**回測區間設定**")
bt_col1, bt_col2 = st.sidebar.columns(2)
backtest_start = bt_col1.date_input("買入日期", value=start_date, key="bt_start")
backtest_end = bt_col2.date_input("賣出日期", value=end_date, key="bt_end")

if backtest_start >= backtest_end:
    st.sidebar.warning("⚠️ 買入日期必須早於賣出日期")

st.sidebar.markdown("---")
st.sidebar.subheader("執行步驟")
do_crawl   = st.sidebar.checkbox("1. 爬取股票資料", value=True)
do_backtest = st.sidebar.checkbox("2. 回測分析（SMA 策略）", value=True)
do_predict = st.sidebar.checkbox("3. XGBoost 機器學習預測", value=True)
do_analyze = st.sidebar.checkbox("4. Groq AI 分析", value=True)
do_notify  = st.sidebar.checkbox("5. LINE 推送", value=False)

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
    
    # 回測區間
    backtest_start_str = backtest_start.strftime("%Y-%m-%d")
    backtest_end_str = backtest_end.strftime("%Y-%m-%d")

    ALL_STRATEGIES = ["sma_cross"]  # 只使用 SMA 均線交叉策略

    st.markdown(f"**股票：** {', '.join(symbols)}")
    st.markdown(f"**爬取期間：** {start_str} ~ {end_str}")
    st.markdown(f"**回測區間：** {backtest_start_str} ~ {backtest_end_str}")
    st.markdown(f"**初始資金：** ${init_cash:,.0f} | **策略：** SMA 均線交叉")

    progress = st.progress(0)
    log_area = st.empty()

    total_steps = len(symbols) * (
        (1 if do_crawl else 0) +
        (1 if do_backtest else 0) +
        (1 if do_predict else 0) +
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

        # STEP 2 — 回測（SMA 策略）
        if do_backtest:
            with st.spinner(f"📊 回測 {symbol}（SMA 均線交叉）..."):
                import matplotlib
                matplotlib.use("Agg")  # 避免 plt.show() 阻塞
                import matplotlib.pyplot as plt
                _orig_show = plt.show
                plt.show = lambda *a, **kw: None  # 攔截 plt.show()

                from services.backtest import run_all_strategies, load_data, calc_indicators
                from services.plots import (
                    plot_sma_technical, plot_rsi_technical, plot_macd_technical,
                    plot_backtest_interactive
                )
                
                results = run_all_strategies(
                    symbol, backtest_start_str, backtest_end_str,
                    init_cash=init_cash, fees=fees, slippage=slippage
                )

                plt.show = _orig_show

            if results:
                st.success(f"回測完成：{len(results)} 種策略")
                
                # 載入數據並計算指標（只計算一次）
                df_tech = load_data(symbol, start_str, end_str)
                if df_tech.empty:
                    st.error("無法載入技術分析數據")
                else:
                    df_tech = calc_indicators(df_tech)
                    
                    # ═══════════════════════════════════════
                    # 為每個策略建立獨立的完整區塊
                    # ═══════════════════════════════════════
                    
                    strategy_config = {
                        'sma_cross': {
                            'name': 'SMA 均線交叉策略',
                            'icon': '📈',
                            'plot_func': plot_sma_technical,
                            'description': '當快線(SMA20)向上穿越慢線(SMA60)時買入，向下穿越時賣出'
                        },
                        'rsi': {
                            'name': 'RSI 超買超賣策略',
                            'icon': '📊',
                            'plot_func': plot_rsi_technical,
                            'description': 'RSI低於30(超賣)時買入，高於70(超買)時賣出'
                        },
                        'macd': {
                            'name': 'MACD 趨勢動能策略',
                            'icon': '📉',
                            'plot_func': plot_macd_technical,
                            'description': 'MACD線向上穿越訊號線時買入，向下穿越時賣出'
                        }
                    }
                    
                    for strat, pf in results.items():
                        if strat not in strategy_config:
                            continue
                        
                        config = strategy_config[strat]
                        
                        # ┌─────────────────────────────────────┐
                        # │  策略區塊開始                        │
                        # └─────────────────────────────────────┘
                        st.markdown("---")
                        st.markdown(f"## {config['icon']} {config['name']}")
                        st.info(f"💡 **策略說明：** {config['description']}")
                        
                        # ─── ① 技術分析圖（只顯示該策略相關指標）───
                        st.markdown(f"### 1️⃣ 技術分析圖")
                        fig_tech = config['plot_func'](df_tech, symbol)
                        st.plotly_chart(fig_tech, use_container_width=True)
                        
                        # ─── ② 回測結果圖 ───
                        st.markdown(f"### 2️⃣ 回測結果圖")
                        fig_backtest = plot_backtest_interactive(
                            pf, symbol, strat, init_cash
                        )
                        st.plotly_chart(fig_backtest, use_container_width=True)
                        
                        # ─── ③ 損益報告 ───
                        st.markdown(f"### 3️⃣ 損益報告")
                        
                        stats = pf.stats()
                        final_value = pf.value().iloc[-1]
                        total_profit = final_value - init_cash
                        profit_pct = (total_profit / init_cash) * 100
                        
                        # 核心指標
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("初始資金", f"${init_cash:,.0f}")
                        col2.metric("最終資產", f"${final_value:,.2f}")
                        col3.metric(
                            "總損益", 
                            f"${total_profit:,.2f}",
                            delta=f"{profit_pct:+.2f}%"
                        )
                        col4.metric("總交易次數", f"{stats.get('Total Trades', 0):.0f}")
                        
                        # 交易明細
                        with st.expander("📋 查看交易明細", expanded=False):
                            trades = pf.trades.records_readable
                            if not trades.empty:
                                # 顯示交易記錄（動態選擇可用欄位）
                                available_cols = trades.columns.tolist()
                                
                                # 定義欄位對應關係
                                col_mapping = {
                                    'Entry Timestamp': '買入時間',
                                    'Entry Date': '買入時間',
                                    'Exit Timestamp': '賣出時間',
                                    'Exit Date': '賣出時間',
                                    'Entry Price': '買入價',
                                    'Avg Entry Price': '買入價',
                                    'Exit Price': '賣出價',
                                    'Avg Exit Price': '賣出價',
                                    'PnL': '損益 (USD)',
                                    'P&L': '損益 (USD)',
                                    'Return': '報酬率 (%)',
                                    'Return [%]': '報酬率 (%)'
                                }
                                
                                # 選擇存在的欄位
                                display_cols = []
                                rename_dict = {}
                                for eng, zh in col_mapping.items():
                                    if eng in available_cols and eng not in rename_dict:
                                        display_cols.append(eng)
                                        rename_dict[eng] = zh
                                
                                if display_cols:
                                    st.dataframe(
                                        trades[display_cols].rename(columns=rename_dict),
                                        use_container_width=True
                                    )
                                else:
                                    # 如果沒有匹配的欄位，顯示所有欄位
                                    st.dataframe(trades, use_container_width=True)
                            else:
                                st.info("本次回測沒有產生交易")
                        
                        # 績效指標
                        with st.expander("📊 查看詳細績效指標", expanded=False):
                            col5, col6, col7, col8 = st.columns(4)
                            col5.metric("總報酬率", f"{stats.get('Total Return [%]', 0):.2f}%")
                            col6.metric("最大回撤", f"{stats.get('Max Drawdown [%]', 0):.2f}%")
                            col7.metric("夏普比率", f"{stats.get('Sharpe Ratio', 0):.2f}")
                            col8.metric("勝率", f"{stats.get('Win Rate [%]', 0):.1f}%")
                            
                            st.info(f"""
                            📌 **指標說明：**
                            - **總損益**：基於 {config['name']} 的實際交易損益（已扣除手續費與滑價）
                            - **最大回撤**：資產從最高點跌到最低點的最大跌幅，越小越好
                            - **夏普比率**：每承擔一單位風險獲得的報酬，>1 良好，>2 優秀
                            - **勝率**：獲利交易次數佔總交易次數的比例
                            
                            💡 **圖表為互動式**：可以縮放、拖曳、懸停查看數據！
                            """)
                        
                        # ┌─────────────────────────────────────┐
                        # │  策略區塊結束                        │
                        # └─────────────────────────────────────┘
                    
            else:
                st.warning(f"⚠️ {symbol} 回測失敗")
                st.info(f"""
                **可能原因：**
                1. 回測區間內沒有資料（請確認已執行爬蟲）
                2. 回測區間與爬取期間不匹配（回測日期應在爬取範圍內）
                3. 資料量不足（建議至少爬取 60 天以上）
                4. 股票代碼錯誤
                
                **建議：**
                - 先勾選「爬取股票資料」並執行
                - 確認「回測區間」在「爬取期間」內
                - 增加爬取的時間長度
                """)

            current_step += 1
            progress.progress(current_step / max(total_steps, 1))

        # STEP 3 — XGBoost 機器學習預測
        if do_predict:
            with st.spinner(f"🤖 XGBoost 機器學習預測 {symbol} ..."):
                try:
                    from services.predictor import StockPredictor
                    
                    # 使用 2 年數據訓練模型
                    predictor = StockPredictor(symbol, years=2)
                    predictor.train(test_size=0.15, val_size=0.15)
                    
                    # 生成交易訊號
                    signal, predicted_change_pct, latest_close = predictor.predict(threshold=0.005)
                    
                    st.success(f"✅ {symbol} 機器學習預測完成")
                    
                    # ═══════════════════════════════════════
                    # 顯示預測結果
                    # ═══════════════════════════════════════
                    st.markdown("---")
                    st.markdown(f"## 🤖 XGBoost 機器學習預測")
                    st.info("💡 **模型說明：** 使用 2 年歷史數據 + 14 種技術指標訓練 XGBoost 迴歸模型，預測明日收盤價變動")
                    
                    # ─── ① 預測結果 ───
                    st.markdown(f"### 1️⃣ 交易訊號")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("最新收盤價", f"${latest_close:.2f}")
                    col2.metric(
                        "預測明日漲跌", 
                        f"{predicted_change_pct:+.2f}%",
                        delta=f"{predicted_change_pct:+.2f}%"
                    )
                    col3.metric("訊號門檻", "0.50%")
                    
                    signal_text = "🟢 買入" if signal == 1 else "⚪ 觀望"
                    signal_color = "green" if signal == 1 else "gray"
                    col4.markdown(f"**交易訊號**")
                    col4.markdown(f"<h2 style='color:{signal_color};'>{signal_text}</h2>", unsafe_allow_html=True)
                    
                    # ─── ② 模型評估 ───
                    st.markdown(f"### 2️⃣ 模型評估指標（Train / Validation / Test）")
                    
                    metrics = predictor.metrics
                    col5, col6, col7 = st.columns(3)
                    
                    with col5:
                        st.markdown("**訓練集**")
                        st.metric("RMSE", f"{metrics['train_rmse']:.6f}")
                        st.metric("MAE", f"{metrics['train_mae']:.6f}")
                    
                    with col6:
                        st.markdown("**驗證集**")
                        st.metric("RMSE", f"{metrics['val_rmse']:.6f}")
                        st.metric("MAE", f"{metrics['val_mae']:.6f}")
                    
                    with col7:
                        st.markdown("**測試集**")
                        st.metric("RMSE", f"{metrics['test_rmse']:.6f}")
                        st.metric("MAE", f"{metrics['test_mae']:.6f}")
                    
                    # ─── ③ 特徵重要性 ───
                    st.markdown(f"### 3️⃣ 特徵重要性排名")
                    
                    importance_df = predictor.get_feature_importance()
                    
                    # 使用 Streamlit 的圖表顯示
                    import plotly.graph_objects as go
                    
                    fig = go.Figure([
                        go.Bar(
                            x=importance_df['importance'],
                            y=importance_df['feature'],
                            orientation='h',
                            marker=dict(
                                color=importance_df['importance'],
                                colorscale='Viridis',
                                showscale=True
                            ),
                            text=[f"{v*100:.2f}%" for v in importance_df['importance']],
                            textposition='auto'
                        )
                    ])
                    
                    fig.update_layout(
                        title=f"{symbol} 特徵重要性排名",
                        xaxis_title="重要性分數",
                        yaxis_title="特徵",
                        height=500,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 顯示詳細數據表
                    with st.expander("📋 查看特徵重要性詳細數據", expanded=False):
                        st.dataframe(
                            importance_df.assign(
                                重要性百分比=lambda x: x['importance'].apply(lambda v: f"{v*100:.2f}%")
                            )[['feature', '重要性百分比']].rename(columns={'feature': '特徵名稱'}),
                            use_container_width=True
                        )
                    
                    # ─── ④ 技術說明 ───
                    with st.expander("📊 查看技術細節", expanded=False):
                        st.markdown(f"""
                        **訓練數據：** {len(predictor.df)} 筆（約 2 年交易日）
                        
                        **特徵工程（14 種技術指標）：**
                        - 價格指標：open, high, low, close
                        - 成交量：volume, Volume_Change
                        - 移動平均：MA5, MA20
                        - 動量指標：RSI (14日)
                        - 趨勢指標：MACD, MACD_Signal, MACD_Hist
                        - 報酬率：Daily_Return, High_Low_Pct
                        
                        **模型參數：**
                        - 演算法：XGBoost Regressor
                        - 學習率：0.05
                        - 最大深度：5
                        - 迭代次數：{metrics['best_iteration']}
                        - 正則化：L1=0.01, L2=0.5
                        
                        **數據分割：**
                        - 訓練集：70%（用於模型學習）
                        - 驗證集：15%（用於調整超參數）
                        - 測試集：15%（用於評估真實表現）
                        
                        **評估指標說明：**
                        - **RMSE** (Root Mean Square Error)：均方根誤差，越小越好
                        - **MAE** (Mean Absolute Error)：平均絕對誤差，越小越好
                        - 如果驗證集/測試集的誤差遠大於訓練集，代表可能過擬合
                        
                        **交易訊號生成：**
                        - 預測明日收盤價變動百分比
                        - 若預測漲幅 > 0.5% → 買入訊號 🟢
                        - 若預測漲幅 ≤ 0.5% → 觀望訊號 ⚪
                        """)
                    
                except Exception as e:
                    st.error(f"❌ {symbol} 機器學習預測失敗")
                    st.exception(e)
                    st.info("""
                    **可能原因：**
                    1. 資料量不足（至少需要 150 筆原始數據，推薦 500+ 筆）
                    2. 尚未爬取該股票的歷史數據
                    3. 資料庫連線問題
                    
                    **建議：**
                    - 先執行「爬取股票資料」步驟
                    - 確認爬取至少 2 年的數據（年份選 2）
                    """)
            
            current_step += 1
            progress.progress(current_step / max(total_steps, 1))

        # STEP 4 — AI 分析
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

        # STEP 5 — LINE 推送
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
