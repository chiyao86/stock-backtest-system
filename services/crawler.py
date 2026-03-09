"""股票爬蟲 — yfinance → PostgreSQL（批次寫入）"""

import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_CONFIG


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def ensure_table():
    """確保 stock_prices 資料表存在"""
    sql = """
    CREATE TABLE IF NOT EXISTS stock_prices (
        id          SERIAL PRIMARY KEY,
        symbol      VARCHAR(20)  NOT NULL,
        trade_date  DATE         NOT NULL,
        open_price  NUMERIC(12,2),
        high_price  NUMERIC(12,2),
        low_price   NUMERIC(12,2),
        close_price NUMERIC(12,2),
        volume      BIGINT,
        created_at  TIMESTAMP DEFAULT NOW(),
        UNIQUE (symbol, trade_date)
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("✅ stock_prices 資料表已就緒")


def crawl_stock(symbol: str, start: str, end: str) -> int:
    """用 yfinance 爬取股票資料並批次寫入 PostgreSQL"""
    print(f"\n📡 爬取 {symbol} ({start} ~ {end}) ...")

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)

    if df.empty:
        print(f"⚠️  {symbol} 無資料")
        return 0

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = df.index.tz_localize(None)
    print(f"✅ 共取得 {len(df)} 筆資料")

    # 組裝寫入用的 tuple list
    rows = [
        (
            symbol,
            idx.date(),
            round(row.Open,  2),
            round(row.High,  2),
            round(row.Low,   2),
            round(row.Close, 2),
            int(row.Volume),
        )
        for idx, row in df.iterrows()
    ]

    ensure_table()

    sql = """
        INSERT INTO stock_prices
            (symbol, trade_date, open_price, high_price, low_price, close_price, volume)
        VALUES %s
        ON CONFLICT (symbol, trade_date) DO UPDATE SET
            open_price  = EXCLUDED.open_price,
            high_price  = EXCLUDED.high_price,
            low_price   = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume      = EXCLUDED.volume;
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)
        conn.commit()

    print(f"💾 {symbol}：已寫入 {len(rows)} 筆至 PostgreSQL")
    return len(rows)


def list_db_symbols() -> list:
    """列出 DB 中所有可用的股票代碼"""
    sql = "SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol;"
    with get_conn() as conn:
        df = pd.read_sql(sql, conn)
    return df["symbol"].tolist()
