# -*- coding: utf-8 -*-
"""微盘样本选取 + 行情下载（腾讯接口，后复权）。

复现第一步：跑这个脚本把 cache/px_<code>_hfq.csv 造出来。
接口会变；若报错请换接口，但列名保持 date/open/high/low/close/volume/amount。
"""
import os, time, sys
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
import akshare as ak
import v5_config as C

REN = {"日期": "date", "开盘": "open", "收盘": "close", "最高": "high",
       "最低": "low", "成交量": "volume", "成交额": "amount"}

def pick_universe(n=500, lo=15e8, hi=25e8):
    spot = ak.stock_zh_a_spot_em()
    spot.columns = [str(c).strip() for c in spot.columns]
    df = spot[["代码", "名称", "总市值"]].copy()
    df["总市值"] = pd.to_numeric(df["总市值"], errors="coerce")
    df = df.dropna()
    df = df[~df["名称"].str.contains("ST|退", na=False)]
    df = df[~df["代码"].str.startswith(("4", "8", "9"))]
    df = df[(df["总市值"] >= lo) & (df["总市值"] <= hi)].sort_values("总市值")
    return df["代码"].head(n).tolist()

def fetch_one(code, start="20140101", end="20261231"):
    sym = ("sh" if code[0] in "69" else "sz") + code
    last = None
    for i in range(3):
        try:
            d = ak.stock_zh_a_hist_tx(symbol=sym, start_date=start, end_date=end, adjust="hfq")
            if d is None or len(d) < 100:
                raise ValueError("too short")
            d.columns = [REN.get(str(c), str(c).lower()) for c in d.columns]
            d = d.rename(columns={"date": "date"})
            for col in ["date", "open", "high", "low", "close", "volume", "amount"]:
                if col not in d.columns:
                    d[col] = 0.0
            d["turnover"] = 0.0
            return d[["date", "open", "high", "low", "close", "volume", "amount", "turnover"]]
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{code} 下载失败：{last}")

def main():
    codes = pick_universe()
    print(f"[universe] {len(codes)} 只")
    os.makedirs(C.OUT, exist_ok=True)
    pd.DataFrame({"code": codes}).to_csv(os.path.join(C.OUT, "micro_codes.csv"), index=False)
    ok = fail = 0
    for i, code in enumerate(codes, 1):
        p = os.path.join(C.CACHE, f"px_{code}_hfq.csv")
        if os.path.exists(p):
            ok += 1
            continue
        try:
            fetch_one(code).to_csv(p, index=False)
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  [fail] {code} {e}")
        if i % 50 == 0:
            print(f"  {i}/{len(codes)} ok={ok} fail={fail}")
    print(f"[done] ok={ok} fail={fail} -> {C.CACHE}")

if __name__ == "__main__":
    main()
