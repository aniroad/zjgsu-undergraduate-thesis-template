#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成论文图 1 的双面板序列图（模拟数据，可一键复跑）。

运行（在本目录 `大论文模板/` 下）：
    python3 图1/make_fig1.py

产物：
    图1/fig1_data.csv   —— 模拟日度数据（date, ivs, fb, to）
    图1/fig1_a.png      —— 面板 (a) 隐含波动率偏差与基差
    图1/fig1_b.png      —— 面板 (b) 隐含波动率偏差与 ETF 换手率

说明：
- 两面板共享同一时间轴（2017-01-03 至 2020-02-28，工作日），
  分别用左右双纵轴，避免两条量纲不同的序列互相压扁。
- 数据为随机模拟，仅用于模板演示；真实论文请把
  `simulate()` 换成读取 Wind 数据的代码，其余绘图部分不用改。
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
TEXTWIDTH_IN = 415.14 / 72.0   # 版心宽 415.14pt，按 1:1 出图，插入时不缩放

# ---------- 中文字体：按系统可用性降级 ----------
CJK_CANDIDATES = [
    "SimSun", "NSimSun", "Songti SC", "Noto Serif CJK SC",
    "Source Han Serif SC", "WenQuanYi Zen Hei", "DejaVu Sans",
]
installed = {f.name for f in font_manager.fontManager.ttflist}
CJK = next((n for n in CJK_CANDIDATES if n in installed), "DejaVu Sans")

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [CJK],
    "axes.unicode_minus": False,
    "font.size": 7,
    "axes.linewidth": 0.6,
    "xtick.direction": "in",
    "ytick.direction": "in",
})


def simulate(seed: int = 20261107) -> pd.DataFrame:
    """模拟三条日度序列：隐含波动率偏差 IVS、基差 FB、ETF 换手率 TO。"""
    dates = pd.bdate_range("2017-01-03", "2020-02-28")
    rng = np.random.default_rng(seed)
    n = len(dates)

    eps = rng.standard_normal(n)
    ivs = np.zeros(n)
    fb = np.zeros(n)
    to = np.zeros(n)
    ivs[0] = 0.0226
    fb[0] = 0.0038
    to[0] = 0.0147
    for t in range(1, n):
        ivs[t] = 0.92 * ivs[t - 1] + 0.025 * eps[t] + 0.0019
        fb[t] = 0.85 * fb[t - 1] + 0.0012 * ivs[t] + 0.0068 * eps[t]
        # 换手率恒为正：均值回复到 0.0147，标准差约 0.008，负值截断到 0.0005
        to[t] = max(0.0005, 0.80 * to[t - 1] + 0.20 * 0.0147
                    + 0.0045 * rng.standard_normal())

    return pd.DataFrame({"date": dates, "ivs": ivs, "fb": fb, "to": to})


def _style(ax_left, ax_right, df: pd.DataFrame, ylabel_right: str):
    """两面板共用的坐标轴样式：同一时间轴、同一刻度、内向刻度。"""
    ax_left.set_xlim(pd.Timestamp("2017-01-01"), df["date"].iloc[-1])
    ax_left.xaxis.set_major_locator(mdates.YearLocator())
    ax_left.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax_left.set_ylabel("隐含波动率偏差（IVS）")
    ax_right.set_ylabel(ylabel_right)
    ax_right.set_ylim(df["fb"].min(), df["fb"].max())
    for ax in (ax_left, ax_right):
        ax.tick_params(labelsize=7, length=2.5, width=0.6)


def panel(df: pd.DataFrame, other: str, ylabel_right: str, ylabel_left: str,
          outfile: Path):
    fig, ax1 = plt.subplots(figsize=(TEXTWIDTH_IN, 2.05))
    ax2 = ax1.twinx()

    ax1.plot(df["date"], df["ivs"], color="black", linewidth=0.8, label="IVS")
    ax2.plot(df["date"], df[other], color="0.45", linewidth=0.8,
             linestyle=(0, (4, 2)), label=other.upper())

    _style(ax1, ax2, df, ylabel_right)
    ax1.set_ylabel(ylabel_left)

    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines],
               loc="upper right", fontsize=6.5, ncol=2, frameon=True,
               facecolor="white", edgecolor="none", framealpha=0.85,
               handlelength=2.2, columnspacing=1.2)
    fig.subplots_adjust(left=0.115, right=0.885, top=0.96, bottom=0.19)
    fig.savefig(outfile, dpi=300)
    plt.close(fig)


def main():
    df = simulate()
    csv = HERE / "fig1_data.csv"
    df.to_csv(csv, index=False, float_format="%.6f")

    panel(df, "fb", "基差（FB）", "隐含波动率偏差（IVS）", HERE / "fig1_a.png")
    panel(df, "to", "ETF 换手率（TO）", "隐含波动率偏差（IVS）", HERE / "fig1_b.png")

    print(f"中文字体：{CJK}")
    print(f"样本：{len(df)} 个交易日，{df['date'].iloc[0]:%Y-%m-%d} 至 "
          f"{df['date'].iloc[-1]:%Y-%m-%d}")
    print(f"已写出：{csv.name}、fig1_a.png、fig1_b.png（300 dpi，"
          f"宽 {TEXTWIDTH_IN:.2f} in = 版心宽）")


if __name__ == "__main__":
    main()
