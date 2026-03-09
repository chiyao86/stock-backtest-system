"""
股票回測分析系統 — 主程式入口
一條龍：爬蟲 → 全策略回測 → AI 分析 → LINE 推送
"""

import time
from config import REPORT_DIR, INIT_CASH, DEFAULT_FEES, DEFAULT_SLIPPAGE


BANNER = """
╔══════════════════════════════════════════════╗
║         📈 股票回測分析系統                  ║
║   爬蟲 → 回測(全策略) → AI 分析 → LINE 推送 ║
╚══════════════════════════════════════════════╝
"""

ALL_STRATEGIES = ["sma_cross", "rsi", "macd"]


def main():
    print(BANNER)

    # ─── 使用者輸入 ───
    symbols_raw = input("股票代碼（多支用逗號分隔，如 AAPL,TSLA,2330.TW）：").strip()
    if not symbols_raw:
        print("❌ 未輸入股票代碼，結束")
        return
    symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()]

    start = input("開始日期（如 2025-03-10）：").strip()
    end   = input("結束日期（如 2026-03-08）：").strip()
    if not (start and end):
        print("❌ 日期不完整，結束")
        return

    # 回測參數（有預設值，按 Enter 跳過即可）
    print(f"\n── 回測參數（按 Enter 使用預設值）──")
    init_cash_str = input(f"  初始資金（預設 {INIT_CASH:,.0f}）：").strip()
    fees_str      = input(f"  手續費率（預設 {DEFAULT_FEES}）：").strip()
    slippage_str  = input(f"  滑價比率（預設 {DEFAULT_SLIPPAGE}）：").strip()

    init_cash = float(init_cash_str) if init_cash_str else INIT_CASH
    fees      = float(fees_str)      if fees_str      else DEFAULT_FEES
    slippage  = float(slippage_str)  if slippage_str  else DEFAULT_SLIPPAGE

    print(f"\n📋 即將處理 {len(symbols)} 支股票：{', '.join(symbols)}")
    print(f"   期間：{start} ~ {end}")
    print(f"   資金：${init_cash:,.0f}  手續費：{fees}  滑價：{slippage}")
    print(f"   策略：{', '.join(ALL_STRATEGIES)}（全部執行）\n")

    # ═══════════════════════════════════════════════════
    # 逐支股票跑完整流程
    # ═══════════════════════════════════════════════════
    from services.crawler import crawl_stock
    from services.backtest import run_all_strategies
    from services.analyzer import analyze_report
    from services.notifier import send_analysis_report

    total = len(symbols)
    for idx, symbol in enumerate(symbols, 1):
        print(f"\n{'═'*60}")
        print(f"  🔄 [{idx}/{total}] {symbol}")
        print(f"{'═'*60}")

        # STEP 1 — 爬蟲
        print(f"\n  ── STEP 1／4 — 爬取 {symbol} 股票資料 ──")
        crawl_stock(symbol, start, end)

        # STEP 2 — 全策略回測
        print(f"\n  ── STEP 2／4 — 執行回測（sma_cross / rsi / macd）──")
        run_all_strategies(symbol, start, end,
                           init_cash=init_cash, fees=fees, slippage=slippage)

        # STEP 3 — AI 分析（分析每個策略的報告）
        print(f"\n  ── STEP 3／4 — Groq AI 分析 ──")
        analyses = []
        for strat in ALL_STRATEGIES:
            report_file = REPORT_DIR / f"{symbol}_{strat}_report.html"
            if report_file.exists():
                print(f"\n  🤖 分析 {symbol} [{strat}] ...")
                analysis = analyze_report(symbol, report_file=report_file)
                if analysis:
                    analyses.append((strat, analysis))
                time.sleep(2)

        # STEP 4 — LINE 推送
        print(f"\n  ── STEP 4／4 — LINE 推送 ──")
        for strat, analysis in analyses:
            header = f"📊 {symbol} [{strat}] 回測分析\n{'='*30}\n\n"
            send_analysis_report(symbol, header + analysis)
            time.sleep(1)

        print(f"\n  ✅ {symbol} 全流程完成！")

        if idx < total:
            print("  ⏳ 等待 3 秒...")
            time.sleep(3)

    # ═══════════════════════════════════════════════════
    print(f"\n{'═'*60}")
    print(f"  🎉 全部完成！共處理 {total} 支股票 × {len(ALL_STRATEGIES)} 種策略")
    print(f"  📁 報告資料夾：{REPORT_DIR}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 使用者中斷程式")
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")
        import traceback
        traceback.print_exc()
