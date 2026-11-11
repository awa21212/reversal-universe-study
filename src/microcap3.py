
# -*- coding: utf-8 -*-
"""从 500 只微盘股里每次随机抽 200 只，重复 10 次，检验 J×K 反转结论是否依赖特定样本。"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import v5_config as C

codes = pd.read_csv(os.path.join(C.OUT, "micro_codes.csv"), dtype={"code": str})["code"].tolist()
buf = {}
for code in codes:
    p = os.path.join(C.CACHE, f"px_{code}_hfq.csv")
    if not os.path.exists(p): continue
    df = pd.read_csv(p)
    if len(df) < 200: continue
    buf[code] = df.set_index("date")["close"].astype(float)
adj = pd.DataFrame(buf); adj.index = pd.to_datetime(adj.index)
print(f"[panel] 可用 {adj.shape[1]} 只 × {len(adj)} 天")

def jk(panel, J, K):
    m = panel.resample("ME").last()
    ret = m.pct_change(); form = m.shift(1) / m.shift(1 + J) - 1
    w = []
    for i in range(J + 1, len(m) - K):
        s = form.loc[m.index[i]].dropna()
        if len(s) < 40: continue
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

cols = list(adj.columns)
print("\n每次随机抽 200 只（不放回），10 次独立抽样：")
print(f"{'序':>2} {'J1K1 收益':>11} {'t_nb':>7} {'J3K3 收益':>11} {'t_nb':>7} {'J6K6 收益':>11} {'t_nb':>7}")
rows = []
for seed in range(10):
    rng = np.random.default_rng(seed)
    pick = rng.choice(cols, size=200, replace=False)
    sub = adj[pick]
    a = jk(sub, 1, 1); b = jk(sub, 3, 3); c = jk(sub, 6, 6)
    rows.append((a[0], a[2], b[0], b[2], c[0], c[2]))
    print(f"{seed:>2} {a[0]:>+10.3f}% {a[2]:>7.2f} {b[0]:>+10.3f}% {b[2]:>7.2f} {c[0]:>+10.3f}% {c[2]:>7.2f}")

r = np.array(rows)
print("\n汇总（10 次抽样的均值 ± 标准差）：")
for i, name in enumerate(["J1K1 收益%", "J1K1 t_nb", "J3K3 收益%", "J3K3 t_nb", "J6K6 收益%", "J6K6 t_nb"]):
    print(f"  {name:<10} {r[:,i].mean():+7.3f} ± {r[:,i].std(ddof=1):5.3f}   最小 {r[:,i].min():+7.3f}  最大 {r[:,i].max():+7.3f}")
for i, name in [("J1K1", ""), ("J3K3", ""), ("J6K6", "")]:
    pass
neg1 = (r[:,0] < 0).sum(); sig1 = (r[:,1] < -1.96).sum()
neg3 = (r[:,2] < 0).sum(); sig3 = (r[:,3] < -1.96).sum()
neg6 = (r[:,4] < 0).sum(); sig6 = (r[:,5] < -1.96).sum()
print(f"\n方向为负的次数：J1K1 {neg1}/10，J3K3 {neg3}/10，J6K6 {neg6}/10")
print(f"非重叠 t < -1.96 的次数：J1K1 {sig1}/10，J3K3 {sig3}/10，J6K6 {sig6}/10")
