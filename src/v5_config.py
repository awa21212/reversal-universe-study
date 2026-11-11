# -*- coding: utf-8 -*-
"""v5_config.py —— 路径与网络参数（只保留复现所需的目录约定）。

策略层的参数（持仓数、单票上限、调仓频率等）不在开源范围内。
"""
from __future__ import annotations

import os

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "cache")
META = os.path.join(BASE, "meta")
OUT = os.path.join(BASE, "out")
for _d in (CACHE, META, OUT):
    os.makedirs(_d, exist_ok=True)

# 网络
RETRIES = 3
RETRY_WAIT = 2.0
