# -*- coding: utf-8 -*-
"""JT 式 J×K 组合排序：检验「短期反转 / 中长期动量」在 2016-2026 的中证800 上是否成立。
方法：Jegadeesh & Titman (1993) 的标准框架——按过去 J 个月收益分十组，持有 K 个月，等权。
用途：复现《A股个股回报率的惯性与反转》（潘莉、徐建国，金融研究 2011）的核心设计，
      把样本换成 2016-2026 的中证800，看原结论是否还成立。
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import v5_factors as F

def monthly_prices():
    panel = F.load_panel(start="2015-06-01", end="2026-11-10")
    adj = panel["adj_close"].copy()
    adj.index = pd.to_datetime(adj.index)
    m = adj.resample("ME").last()
    return m

def run(m, J, K):
    ret = m.pct_change()
    form = m.shift(1) / m.shift(1 + J) - 1          # 过去 J 个月（不含当月）
    wml = []
    win, lose = [], []
    for i in range(J + 1, len(m) - K):
        t = m.index[i]
        s = form.loc[t]
        ok = s.notna() & m.loc[t].notna()
        s = s[ok]
        if len(s) < 100: continue
        r = s.rank(pct=True)
        hi = s.index[r > 0.9]; lo = s.index[r <= 0.1]
        for k in range(1, K + 1):
            if i + k >= len(m): break
            rr = ret.loc[m.index[i + k], hi].mean()
            rl = ret.loc[m.index[i + k], lo].mean()
            if np.isfinite(rr) and np.isfinite(rl):
                wml.append(rr - rl); win.append(rr); lose.append(rl)
    if len(wml) < 20: return None
    w = np.array(wml); w2 = np.array(win); l2 = np.array(lose)
    t = w.mean() / (w.std(ddof=1) / np.sqrt(len(w)))
    wb = w[::K]
    t_nb = wb.mean() / (wb.std(ddof=1) / np.sqrt(len(wb))) if len(wb) > 5 else np.nan
    return dict(J=J, K=K, W=w2.mean()*100, L=l2.mean()*100, WML=w.mean()*100,
                t=t, t_nb=t_nb, n=len(w), n_nb=len(w[::K]), win_rate=(w > 0).mean()*100)

m = monthly_prices()
print(f"[data] 月频 {m.shape[1]} 只 × {len(m)} 个月：{m.index[0].date()} ~ {m.index[-1].date()}")
rows = []
for J in (1, 3, 6, 12):
    for K in (1, 3, 6, 12):
        r = run(m, J, K)
        if r: rows.append(r)
df = pd.DataFrame(rows)
print("\n列：J=形成期(月)，K=持有期(月)，W/L=赢家/输家组合月均收益(%)，WML=多空(%)，t=WML的t值")
print(df.to_string(index=False, float_format=lambda x: f"{x:7.2f}"))
df.to_csv("out/replication_jt.csv", index=False)
print("\n[write] out/replication_jt.csv")
