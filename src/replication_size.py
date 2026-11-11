# -*- coding: utf-8 -*-
"""反转是否只存在于小市值端？——按规模三分组重跑 J=1,K=1 的月度反转。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import v5_factors as F

panel = F.load_panel(start="2015-06-01", end="2026-11-10")
adj = panel["adj_close"].copy(); adj.index = pd.to_datetime(adj.index)
amt = panel["amount"].copy(); amt.index = adj.index
m = adj.resample("ME").last(); mt = amt.resample("ME").mean()
ret = m.pct_change(); form = m.shift(1)/m.shift(2) - 1

for label, mask_fn in [("全部", lambda s, sz: s.index),
                       ("小市值 1/3", lambda s, sz: sz[sz<=sz.quantile(1/3)].index),
                       ("中 1/3", lambda s, sz: sz[(sz>sz.quantile(1/3))&(sz<=sz.quantile(2/3))].index),
                       ("大市值 1/3", lambda s, sz: sz[sz>sz.quantile(2/3)].index)]:
    w=[]
    for i in range(3, len(m)-1):
        t=m.index[i]
        s=form.loc[t].dropna(); sz=mt.loc[t].reindex(s.index)
        if len(s)<90: continue
        idx=mask_fn(s, sz.dropna())
        s2=s.reindex(idx).dropna()
        if len(s2)<30: continue
        r=s2.rank(pct=True)
        hi=s2.index[r>0.9]; lo=s2.index[r<=0.1]
        rr=ret.loc[m.index[i+1], hi].mean(); rl=ret.loc[m.index[i+1], lo].mean()
        if np.isfinite(rr) and np.isfinite(rl): w.append(rr-rl)
    w=np.array(w); t=w.mean()/(w.std(ddof=1)/np.sqrt(len(w)))
    print(f"{label:10s} 反转多空(买跌卖涨) = {w.mean()*100:+.3f}%/月  t = {t:+.2f}  n = {len(w)}")
