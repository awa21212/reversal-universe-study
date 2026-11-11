# -*- coding: utf-8 -*-
"""微盘股 J×K 检验：用腾讯行情补数据（东财已限流），6 线程。"""
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
import v5_config as C

codes = pd.read_csv(os.path.join(C.OUT, "micro_codes.csv"), dtype={"code": str})["code"].tolist()

def sym(c):
    return ("sh" if c[0] in "69" else "sz") + c

def one(c):
    p = os.path.join(C.CACHE, f"px_{c}_hfq.csv")
    if os.path.exists(p) and os.path.getsize(p) > 200: return True
    for _ in range(2):
        try:
            df = ak.stock_zh_a_hist_tx(symbol=sym(c), start_date="20150101", end_date="20261110", adjust="hfq")
            if df is None or len(df) < 200: return False
            for col in ("amount", "turnover"):
                if col not in df.columns: df[col] = np.nan
            df[["date","open","high","low","close","volume","amount","turnover"]].to_csv(p, index=False)
            return True
        except Exception:
            time.sleep(1.0)
    return False

t0 = time.time(); ok = bad = 0
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(one, c): c for c in codes}
    for i, f in enumerate(as_completed(futs), 1):
        if f.result(): ok += 1
        else: bad += 1
        if i % 50 == 0:
            print(f"[dl] {i}/{len(codes)} ok={ok} bad={bad} {time.time()-t0:.0f}s", flush=True)
print(f"[dl] 完成 ok={ok} bad={bad} 用时 {time.time()-t0:.0f}s")

buf = {}
for c in codes:
    p = os.path.join(C.CACHE, f"px_{c}_hfq.csv")
    if not os.path.exists(p): continue
    d = pd.read_csv(p)
    if len(d) < 200: continue
    buf[c] = d.set_index("date")["close"].astype(float)
adj = pd.DataFrame(buf); adj.index = pd.to_datetime(adj.index)
m = adj.resample("ME").last()
print(f"[panel] 微盘 {adj.shape[1]} 只 × {len(m)} 个月：{m.index[0].date()} ~ {m.index[-1].date()}")

def run(J, K):
    ret = m.pct_change(); form = m.shift(1)/m.shift(1+J) - 1
    w = []
    for i in range(J+1, len(m)-K):
        t = m.index[i]; s = form.loc[t].dropna()
        if len(s) < 100: continue
        r = s.rank(pct=True)
        hi = s.index[r > 0.9]; lo = s.index[r <= 0.1]
        for k in range(1, K+1):
            if i+k >= len(m): break
            a = ret.loc[m.index[i+k], hi].mean(); b = ret.loc[m.index[i+k], lo].mean()
            if np.isfinite(a) and np.isfinite(b): w.append(a-b)
    if len(w) < 20: return None
    w = np.array(w); wb = w[::K]
    t = w.mean()/(w.std(ddof=1)/np.sqrt(len(w)))
    tn = wb.mean()/(wb.std(ddof=1)/np.sqrt(len(wb))) if len(wb) > 5 else np.nan
    return (J, K, w.mean()*100, t, tn, len(w))

print("\n微盘股（市值 15–25 亿）：J×K 多空（正=惯性，负=反转）")
print("J  K   多空%/月     t重叠   t非重叠   n")
for J, K in [(1,1),(1,3),(1,6),(3,3),(6,6),(12,12)]:
    r = run(J, K)
    if r: print(f"{r[0]:>2} {r[1]:>2}   {r[2]:+8.3f}   {r[3]:+6.2f}   {r[4]:+6.2f}  {r[5]}")
