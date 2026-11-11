
# -*- coding: utf-8 -*-
"""退市预警因子：用「股价逼近面值」做死亡风险代理，检验两件事
1) 低价股是否真的更差（因子有效性）
2) 把濒死股剔除后，微盘反转是否复活（生存偏差的另一种修法）
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import v5_config as C

live = pd.read_csv(os.path.join(C.OUT, "micro_codes.csv"), dtype={"code": str})["code"].tolist()
dead = pd.read_csv(os.path.join(C.OUT, "delist_codes.csv"), dtype={"code": str})["code"].tolist()

def load(codes):
    buf = {}
    for c in codes:
        p = os.path.join(C.CACHE, f"px_{c}_hfq.csv")
        if not os.path.exists(p): continue
        d = pd.read_csv(p)
        if len(d) < 200: continue
        buf[c] = d.set_index(pd.to_datetime(d["date"]))["close"].astype(float)
    df = pd.DataFrame(buf)
    return df

# 注意：判面值要用未复权价；这里用 hfq 的绝对值不成立，改用「相对 1 元」不可得，
# 所以用「后复权价格 / 该股上市以来最高后复权价」做归一化代理：低于 10% 分位 = 长期崩塌
px = load(live + dead)
m = px.resample("ME").last()
ratio = m / m.cummax()          # 距历史最高点的比例
print(f"[panel] {px.shape[1]} 只（活 {len(live)} + 死 {len(dead)}）")

fwd6 = m.shift(-6) / m - 1
bins = [(0, 0.1, "距高点 <10%（崩塌档）"), (0.1, 0.3, "10%–30%"), (0.3, 0.6, "30%–60%"), (0.6, 1.01, "60%–100%（接近高点）")]
print("\n一、按「距历史高点比例」分组，未来 6 个月收益（月频、等权、剔极端）")
for lo, hi, name in bins:
    mask = (ratio >= lo) & (ratio < hi)
    vals = fwd6.where(mask).stack().dropna()
    print(f"  {name:<18} 样本 {len(vals):>7}  未来6月均值 {vals.mean()*100:>+7.2f}%  中位 {vals.median()*100:>+7.2f}%  为负占比 {(vals<0).mean()*100:>4.0f}%")

def jk(panel_df, J, K, filt=None):
    mm = panel_df.resample("ME").last()
    ret = mm.pct_change(); form = mm.shift(1) / mm.shift(1 + J) - 1
    w = []
    for i in range(J + 1, len(mm) - K):
        t = mm.index[i]
        s = form.loc[t].dropna()
        if filt is not None:
            keep = filt.loc[t].reindex(s.index).fillna(False)
            s = s[keep]
        if len(s) < 50: continue
        r = s.rank(pct=True)
        hi = s.index[r > 0.9]; lo = s.index[r <= 0.1]
        for k in range(1, K + 1):
            if i + k >= len(mm): break
            a = ret.loc[mm.index[i + k], hi].mean(); b = ret.loc[mm.index[i + k], lo].mean()
            if np.isfinite(a) and np.isfinite(b): w.append(a - b)
    w = np.array(w)
    if len(w) < 20: return None
    wb = w[::K]
    t = w.mean() / (w.std(ddof=1) / np.sqrt(len(w)))
    tn = wb.mean() / (wb.std(ddof=1) / np.sqrt(len(wb))) if len(wb) > 5 else np.nan
    return w.mean() * 100, t, tn

print("\n二、剔除「长期崩塌股」后的反转（距高点 <10% 时不买）")
alive = ratio >= 0.10
for J, K in [(1,1), (3,3), (6,6)]:
    a = jk(px, J, K); b = jk(px, J, K, filt=alive)
    if a and b:
        print(f"  J={J} K={K}  全样本 {a[0]:+.3f}% (t {a[1]:+.2f} / t_nb {a[2]:+.2f})   剔除崩塌 {b[0]:+.3f}% (t {b[1]:+.2f} / t_nb {b[2]:+.2f})")

print("\n三、更严：距高点 <30% 不买")
alive30 = ratio >= 0.30
for J, K in [(1,1), (3,3), (6,6)]:
    a = jk(px, J, K); b = jk(px, J, K, filt=alive30)
    if a and b:
        print(f"  J={J} K={K}  全样本 {a[0]:+.3f}% (t {a[1]:+.2f} / t_nb {a[2]:+.2f})   剔除30% {b[0]:+.3f}% (t {b[1]:+.2f} / t_nb {b[2]:+.2f})")
