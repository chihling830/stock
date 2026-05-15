import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf


SYMBOLS = {
    # 台股上市 TW
    "2330": "2330.TW",
    "2404": "2404.TW",
    "6196": "6196.TW",
    "3680": "3680.TW",
    "1560": "1560.TW",
    "3711": "3711.TW",
    "6239": "6239.TW",
    "2449": "2449.TW",
    "3037": "3037.TW",
    "8046": "8046.TW",
    "2383": "2383.TW",
    "6213": "6213.TW",
    "2313": "2313.TW",
    "3044": "3044.TW",
    "4958": "4958.TW",
    "2368": "2368.TW",
    "8358": "8358.TW",
    "1815": "1815.TW",
    "1717": "1717.TW",
    "2327": "2327.TW",
    "2492": "2492.TW",
    "2456": "2456.TW",
    "2308": "2308.TW",
    "2301": "2301.TW",
    "3023": "3023.TW",
    "8255": "8255.TW",
    "2481": "2481.TW",
    "3017": "3017.TW",
    "3324": "3324.TW",
    "3653": "3653.TW",
    "8996": "8996.TW",
    "2421": "2421.TW",
    "2059": "2059.TW",
    "2345": "2345.TW",
    "3596": "3596.TW",
    "2408": "2408.TW",
    "2344": "2344.TW",
    "6770": "6770.TW",
    "2337": "2337.TW",
    "2451": "2451.TW",
    "4967": "4967.TW",
    "6285": "6285.TW",
    "2367": "2367.TW",
    "2485": "2485.TW",
    "3380": "3380.TW",
    "2314": "2314.TW",

    # 台股上櫃 TWO
    "3131": "3131.TWO",
    "3583": "3583.TWO",
    "3413": "3413.TWO",
    "6187": "6187.TWO",
    "6223": "6223.TWO",
    "6515": "6515.TWO",
    "7769": "7769.TWO",
    "3189": "3189.TWO",
    "6274": "6274.TWO",
    "5475": "5475.TWO",
    "5317": "5317.TWO",
    "3357": "3357.TWO",
    "3068": "3068.TWO",
    "6173": "6173.TWO",
    "3003": "3003.TWO",
    "3211": "3211.TWO",
    "3323": "3323.TWO",
    "6805": "6805.TWO",
    "6591": "6591.TWO",
    "3363": "3363.TWO",
    "3163": "3163.TWO",
    "3081": "3081.TWO",
    "4979": "4979.TWO",
    "6442": "6442.TWO",
    "3533": "3533.TWO",
    "8299": "8299.TWO",
    "5289": "5289.TWO",
    "3491": "3491.TWO",
    "3138": "3138.TWO",
    "3105": "3105.TWO",
    "6568": "6568.TWO",

    # 美股
    "ASML": "ASML",
    "AMAT": "AMAT",
    "LRCX": "LRCX",
    "KLAC": "KLAC",
    "ETN": "ETN",
    "GEV": "GEV",
    "PWR": "PWR",
    "CEG": "CEG",
    "VST": "VST",
    "LITE": "LITE",
    "COHR": "COHR",
    "AVGO": "AVGO",
    "GLW": "GLW",
    "CIEN": "CIEN",
    "ANET": "ANET",
    "MU": "MU",
    "SNDK": "SNDK",
    "ASTS": "ASTS",
    "IRDM": "IRDM",
    "RKLB": "RKLB",
    "LMT": "LMT",

    # 日股
    "6981": "6981.T",

    # 韓股
    "000660": "000660.KS",
    "005930": "005930.KS",
}


def scalar(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    return float(value)


def format_price(x):
    if x >= 100:
        return f"{x:,.0f}"
    return f"{x:,.2f}".rstrip("0").rstrip(".")


def fetch_one(code, ticker):
    df = yf.download(
        ticker,
        period="10d",
        interval="1d",
        progress=False,
        auto_adjust=False,
        threads=False,
    )

    if df is None or df.empty or len(df) < 2:
        return None

    close = scalar(df["Close"].dropna().iloc[-1])
    prev_close = scalar(df["Close"].dropna().iloc[-2])

    if prev_close == 0:
        return None

    change_pct = (close / prev_close - 1) * 100

    return {
        "ticker": ticker,
        "close": format_price(close),
        "change_pct": f"{change_pct:+.2f}%"
    }


def main():
    quotes = {
        "_updated_at": datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y/%m/%d")
    }

    failed = {}

    for code, ticker in SYMBOLS.items():
        try:
            result = fetch_one(code, ticker)
            if result:
                quotes[code] = result
                print(f"OK {code} {ticker}: {result['close']} {result['change_pct']}")
            else:
                failed[code] = ticker
                print(f"NO DATA {code} {ticker}")
        except Exception as e:
            failed[code] = f"{ticker} | {e}"
            print(f"FAILED {code} {ticker}: {e}")

        time.sleep(0.3)

    quotes["_failed"] = failed

    with open("quotes.json", "w", encoding="utf-8") as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)

    print(f"Saved quotes.json, success={len(quotes) - 2}, failed={len(failed)}")


if __name__ == "__main__":
    main()
