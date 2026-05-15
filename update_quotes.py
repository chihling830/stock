import json
import re
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

HTML_FILE = Path('index.html')
OUT_FILE = Path('quotes.json')

EXCHANGE_SUFFIX = {
    'TWSE': '.TW',
    'TPEX': '.TWO',
    'NASDAQ': '',
    'NYSE': '',
    'TSE': '.T',
    'KRX': '.KS',
}

FALLBACK_SUFFIXES = {
    'TWSE': ['.TW', '.TWO'],
    'TPEX': ['.TWO', '.TW'],
    'TSE': ['.T'],
    'KRX': ['.KS', '.KQ'],
    'NASDAQ': [''],
    'NYSE': [''],
}

def extract_symbols_from_html(html_path: Path) -> dict:
    """從 TradingView 連結自動抓股票代號，避免手動漏掉。"""
    html = html_path.read_text(encoding='utf-8')
    pattern = re.compile(r'https://www\.tradingview\.com/symbols/([A-Z]+)-([^/"#?]+)/')
    symbols = {}
    for exchange, symbol in pattern.findall(html):
        code = symbol.strip()
        if not code:
            continue
        suffix = EXCHANGE_SUFFIX.get(exchange, '')
        symbols[code] = {
            'exchange': exchange,
            'ticker': f'{code}{suffix}',
        }
    return symbols

def to_float(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    return float(value)

def format_price(x: float, ticker: str) -> str:
    # 台股、日股、韓股通常不用美元符號；美股保留兩位小數。
    if ticker.endswith(('.TW', '.TWO', '.T', '.KS', '.KQ')):
        if x >= 100:
            return f'{x:,.0f}'
        return f'{x:,.2f}'.rstrip('0').rstrip('.')
    return f'${x:,.2f}'

def try_download(ticker: str):
    return yf.download(
        ticker,
        period='10d',
        interval='1d',
        progress=False,
        auto_adjust=False,
        threads=False,
    )

def fetch_quote(code: str, exchange: str, primary_ticker: str):
    suffixes = FALLBACK_SUFFIXES.get(exchange, [''])
    tickers = []
    if primary_ticker not in tickers:
        tickers.append(primary_ticker)
    for suffix in suffixes:
        t = code + suffix
        if t not in tickers:
            tickers.append(t)

    last_error = None
    for ticker in tickers:
        try:
            df = try_download(ticker)
            if df is None or df.empty:
                continue

            close_series = df['Close'].dropna()
            if len(close_series) < 2:
                continue

            close = to_float(close_series.iloc[-1])
            prev_close = to_float(close_series.iloc[-2])
            if prev_close == 0:
                continue

            change_pct = (close / prev_close - 1) * 100
            return {
                'ticker': ticker,
                'close': format_price(close, ticker),
                'change_pct': f'{change_pct:+.2f}%'
            }
        except Exception as e:
            last_error = str(e)

    raise RuntimeError(last_error or 'No data')

def main():
    if not HTML_FILE.exists():
        raise FileNotFoundError('找不到 index.html。請確認 update_quotes.py 跟 index.html 在同一層。')

    symbols = extract_symbols_from_html(HTML_FILE)
    quotes = {
        '_updated_at': datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y/%m/%d'),
        '_source': 'yfinance',
    }
    failed = {}

    for i, (code, info) in enumerate(symbols.items(), start=1):
        exchange = info['exchange']
        ticker = info['ticker']
        try:
            q = fetch_quote(code, exchange, ticker)
            quotes[code] = q
            print(f'[{i}/{len(symbols)}] OK {code} {q["ticker"]}: {q["close"]} {q["change_pct"]}')
        except Exception as e:
            failed[code] = {'exchange': exchange, 'ticker': ticker, 'reason': str(e)}
            print(f'[{i}/{len(symbols)}] FAIL {code} {ticker}: {e}')
        time.sleep(0.25)

    quotes['_failed'] = failed
    OUT_FILE.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Saved {OUT_FILE}. success={len(quotes)-3}, failed={len(failed)}')

if __name__ == '__main__':
    main()
