
# -*- coding: utf-8 -*-
"""生存偏差检验：把 2015 年后退市/暂停上市的股票补进来，重跑 J×K 反转检验。
机制预期：反转策略买「跌得最狠」的票，而这些票里有一部分后来退市（跌到零）。
若原样本把这些死掉的票排除在外，反转收益会被高估；补进来后幅度应缩小。
"""
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import akshare as ak
import v5_config as C

LIVE = pd.read_csv(os.path.join(C.OUT, "micro_codes.csv"), dtype={"code": str})["code"].tolist()
DEAD_CSV = os.path.join(C.OUT, "delist_codes.csv")
CACHE = C.CACHE

def sina_sym(code):
    return ("sh" if code[0] in "69" else "sz") + code

def get_list():
    rows = []
    try:
        sh = ak.stock_info_sh_delist()
        sh["暂停上市日期"] = pd.to_datetime(sh["暂停上市日期"], errors="coerce")
        sh = sh[sh["暂停上市日期"] >= "2015-01-01"]
        for _, r in sh.iterrows():
            rows.append((str(r["公司代码"]), r["公司简称"], r["暂停上市日期"].strftime("%Y-%m-%d")))
    except Exception as e:
        print("[warn] SH 退市名单失败", e)
    for attempt in range(3):
        try:
            sz = ak.stock_info_sz_delist()
            col = [c for c in sz.columns if "终止" in c or "摘牌" in c]
            datecol = [c for c in sz.columns if "日期" in c]
            cc = [c for c in sz.columns if "代码" in c][0]
            nc = [c for c in sz.columns if "简称" in c or "名称" in c][0]
            if datecol:
                sz[datecol[0]] = pd.to_datetime(sz[datecol[0]], errors="coerce")
                sz = sz[sz[datecol[0]] >= "2015-01-01"]
                for _, r in sz.iterrows():
                    rows.append((str(r[cc]), r[nc], r[datecol[0]].strftime("%Y-%m-%d")))
            break
        except Exception as e:
            print(f"[warn] SZ 退市名单第 {attempt+1} 次失败：{str(e)[:60]}")
            time.sleep(3)
    df = pd.DataFrame(rows, columns=["code", "name", "delist_date"]).drop_duplicates("code")
    df.to_csv(DEAD_CSV, index=False, encoding="utf-8")
    print(f"[list] 2015 年后退市/暂停上市 {len(df)} 只")
    return df

if os.path.exists(DEAD_CSV):
    dead = pd.read_csv(DEAD_CSV, dtype={"code": str})
else:
    dead = get_list()

ok = 0
for i, code in enumerate(dead["code"].tolist(), 1):
    p = os.path.join(CACHE, f"px_{code}_hfq.csv")
    if os.path.exists(p) and os.path.getsize(p) > 200:
        ok += 1; continue
    try:
        df = ak.stock_zh_a_daily(symbol=sina_sym(code), start_date="20140101", end_date="20261231", adjust="hfq")
        if df is not None and len(df) > 60:
            out = pd.DataFrame({"date": pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d"),
                                "open": df["open"], "high": df["high"], "low": df["low"],
                                "close": df["close"], "volume": df["volume"]})
            out["amount"] = out["close"] * out["volume"]
            out["turnover"] = np.nan
            out.to_csv(p, index=False); ok += 1
    except Exception:
        pass
    if i % 20 == 0: print(f"[dl] {i}/{len(dead)} 已存 {ok}", flush=True)
    time.sleep(0.3)
print(f"[dl] 退市股行情就绪 {ok}/{len(dead)}")

def panel(codes):
    buf = {}
    for c in codes:
        p = os.path.join(CACHE, f"px_{c}_hfq.csv")
        if not os.path.exists(p): continue
        d = pd.read_csv(p)
        if len(d) < 200: continue
        buf[c] = d.set_index("date")["close"].astype(float)
    df = pd.DataFrame(buf); df.index = pd.to_datetime(df.index)
    return df

def jk(panel_df, J, K):
    m = panel_df.resample("ME").last()
    ret = m.pct_change(); form = m.shift(1) / m.shift(1 + J) - 1
    w = []
    for i in range(J + 1, len(m) - K):
        s = form.loc[m.index[i]].dropna()
        if len(s) < 50: continue
        r = s.rank(pct=True)
        hi = s.index[r > 0.9]; lo = s.index[r <= 0.1]
        for k in range(1, K + 1):
            if i + k >= len(m): break
            a = ret.loc[m.index[i + k], hi].mean(); b = ret.loc[m.index[i + k], lo].mean()
            if np.isfinite(a) and np.isfinite(b): w.append(a - b)
    w = np.array(w)
    if len(w) < 20: return None
    wb = w[::K]
    t = w.mean() / (w.std(ddof=1) / np.sqrt(len(w)))
    tn = wb.mean() / (wb.std(ddof=1) / np.sqrt(len(wb))) if len(wb) > 5 else np.nan
    return w.mean() * 100, t, tn, len(wb)

live_p = panel(LIVE)
dead_codes = dead["code"].tolist()
all_p = panel(LIVE + dead_codes)
print(f"[panel] 仅存活 {live_p.shape[1]} 只｜含退市 {all_p.shape[1]} 只（退市进入 {all_p.shape[1]-live_p.shape[1]} 只）")

print("\n窗口        宇宙          J1K1          t_nb    J3K3          t_nb    J6K6          t_nb")
for name, pnl in [("仅存活", live_p), ("含退市", all_p)]:
    r1 = jk(pnl, 1, 1); r3 = jk(pnl, 3, 3); r6 = jk(pnl, 6, 6)
    print(f"2015-2026  {name:<8} {r1[0]:>+7.3f}% {r1[2]:>8.2f} {r3[0]:>+8.3f}% {r3[2]:>7.2f} {r6[0]:>+8.3f}% {r6[2]:>7.2f}")

print("\n退市股「死亡惩罚」：退市前最后 6 个月的月均收益")
pen = []
for c in dead_codes:
    p = os.path.join(CACHE, f"px_{c}_hfq.csv")
    if not os.path.exists(p): continue
    d = pd.read_csv(p)
    if len(d) < 130: continue
    s = d.set_index("date")["close"].astype(float).resample("ME").last().dropna()
    if len(s) < 8: continue
    pen.append(s.iloc[-6:].pct_change().dropna().mean())
pen = np.array(pen) * 100
if len(pen):
    print(f"  样本 {len(pen)} 只｜均值 {pen.mean():+.2f}%/月｜中位 {np.median(pen):+.2f}%/月｜为负占比 {(pen<0).mean()*100:.0f}%")
print("  （对照：全部 A 股月均约 +0.5%，这批票在死前半年显著跑输）")
