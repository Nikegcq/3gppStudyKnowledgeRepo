---
type: note
tags: [RF, 射频, PLL, VCO, 时钟, AD9361, BBPLL, 硬件]
created: 2026-09-15
updated: 2026-09-15
status: active
source: 原理通识 + AD9361 UG-570 / Linux ad9361.c 对照
---

# 概念：锁相环 PLL 与 VCO（含 AD9361 BBPLL）

## 一句话总结

PLL 用「鉴相 + 环路滤波 + VCO + 反馈分频」的负反馈，把不稳的高频 VCO **锁**到晶振参考的 \(N_{\text{eff}}\) 倍上；AD9361 的 BBPLL 再经环外 `REG_BBPLL` 分频，才变成 ADC/DAC 时钟，**不是**直接等于采样率。

---

## 1. 为什么需要 PLL

| 来源 | 特点 |
| --- | --- |
| 晶振 REF | 准、稳，但频率固定且偏低（如 40 MHz） |
| 系统需求 | 几十 MHz～GHz 的 LO / ADC 钟，且要可调 |
| 自由 VCO | 能出高频，但温度/电源/噪声下会漂 |

PLL = **用准的低频，驯服不稳的高频**。

---

## 2. 经典五块电路

```text
f_ref ──► PFD ──► CP ──► LF ──► VCO ──┬──► f_out
         ▲                            │
         │         ┌──────┐           │
         └─────────│  ÷N  │◄──────────┘
                   └──────┘
```

| 模块 | 全称 | 作用 |
| --- | --- | --- |
| PFD | Phase-Frequency Detector | 比较 REF 与反馈的相位/频率，输出 UP/DN |
| CP | Charge Pump | UP/DN → 充放电电流 |
| LF | Loop Filter | 电流积分成 \(V_{\text{tune}}\)，决定带宽与稳定性 |
| VCO | Voltage-Controlled Oscillator | 电压 → 频率，真正产生高频 |
| ÷N | Feedback Divider | 把 \(f_{\text{out}}\) 分到与 REF 同频以便比相 |

锁定后：

\[
f_{\text{out}} = N \cdot f_{\text{ref}}
\]

「倍频」来自反馈 ÷N + 鉴相，不是把 REF 直接放大。

---

## 3. VCO：硬件与压控原理

### 3.1 射频主流：LC 振荡器

\[
f_0 = \frac{1}{2\pi\sqrt{LC}}
\]

结构：**LC 谐振腔（tank）+ 变容管 + 负阻放大器**（抵消损耗、维持振幅）。片内集成电感/电容与 varactor。

### 3.2 电压如何控频（变容管）

变容二极管反偏时，结电容 \(C_j\) 随反压变化：

```text
V_tune ↑  →  耗尽层 ↑  →  Cj ↓  →  f0 ↑
```

故 \(K_{\text{VCO}} > 0\)（常见极性）：

\[
f_{\text{out}} \approx f_0 + K_{\text{VCO}} \cdot V_{\text{tune}}
\]

数字/SoC 内另有环形振荡器（电流控延迟），射频 LO 一般不用。

### 3.3 自由振荡为何不稳

| 原因 | 机制 |
| --- | --- |
| 温度 | L/C/gm/\(C_j\) 温漂 |
| 电源 | 偏置点移动 → 推频 |
| 器件容差 | 流片差异，中心频率偏 |
| 1/f、热噪声 | 相位噪声、抖动 |
| 负载牵引 pulling | 后级阻抗变化 |
| \(V_{\text{tune}}\) 噪声 | \(K_{\text{VCO}}\cdot n(t)\) 变成调频 |

无环路时相位误差累积，长稳短稳都不够 ADC/LO 用。PLL 持续比相微调 \(V_{\text{tune}}\) 才稳住。

---

## 4. 整数 N vs 小数 N

| 类型 | 公式 | 特点 |
| --- | --- | --- |
| Integer-N | \(f=N\cdot f_{\text{ref}}\) | 杂散少，步进 = \(f_{\text{ref}}\) |
| Fractional-N | \(f=f_{\text{ref}}(N+F/M)\) | 细步进；SDM 把量化噪声推高频 |

AD9361 BBPLL 为小数 N：

\[
M = 2088960,\quad
f_{\text{BBPLL}} = f_{\text{ref}}\left(N + \frac{F}{M}\right)
\]

---

## 5. AD9361 BBPLL 对照

### 5.1 在时钟链中的位置（易混）

```text
40 MHz REF (ad9364_ext_refclk)
        │
        ▼
   ┌──────── BBPLL（小数 N PLL，VCO 715–1430 MHz）──┐
   │  PFD → CP → LF → VCO → 反馈 ÷(N+F/M)          │
   └────────────────────┬───────────────────────────┘
                        │  f_BBPLL ≈ 数百 MHz–1 GHz+
                        ▼
                 REG_BBPLL ÷d (2–64)     ← 环外数字分频
                        │
                        ▼
                   ADC_CLK / DAC_CLK
                        │
                        ▼  半带 / FIR / 抽取插值
                   采样率 Fs（如 30.72 Msps）
```

**要点**：`ad9361_bbpll_set_rate()` 算的是 **VCO 频率**，不是采样率；Fs 还要再除抽取比。

### 5.2 寄存器地图

| 地址 | 宏 | 作用 |
| --- | --- | --- |
| `0x009[0]` | `BBPLL_ENABLE` | BBPLL 使能 |
| `0x00A` | `REG_BBPLL` | **环外**分频到 ADC/DAC |
| `0x03F` | `REG_SDM_CTRL_1` | 启动校准 / `BBPLL_RESET_BAR` |
| `0x041–0x043` | `REG_FRACT_BB_FREQ_WORD_*` | 小数频字 \(F\)（24-bit） |
| `0x044` | `REG_INTEGER_BB_FREQ_WORD` | 整数 \(N\) |
| `0x046` | `REG_CP_CURRENT` | 电荷泵电流 ICP |
| `0x048–0x04A` | `REG_LOOP_FILTER_*` | 环路滤波（默认 `{0x35,0x5B,0xE8}`） |
| `0x04B` | `REG_VCO_CTRL` | VCO 频率校准使能/计数 |
| `0x04C/0x04D` | `REG_VCO_PROGRAM_*` | KV / 相位裕度微调 |
| `0x04E` | `REG_SDM_CTRL` | SDM 时钟（校准用 REF/4） |
| `0x05E[7]` | `BBPLL_LOCK` | 锁定标志 |

频率常数：VCO **715–1430 MHz**；`MIN/MAX_BBPLL_FREF`、分频 2–64。

### 5.3 频字计算（Linux `ad9361_bbpll_set_rate`）

```text
N = rate / parent_rate
r = rate % parent_rate
F = round( r * M / parent_rate )    # + parent_rate/2 四舍五入

写: 0x044=N, 0x043=F[7:0], 0x042=F[15:8], 0x041=F[23:16]
```

配套：

- ICP ≈ 随 \(f_{\text{BBPLL}}/f_{\text{ref}}\) 缩放，写 `0x046`
- 环路滤波默认三字节写 `0x048–0x04A`
- `0x03F` 启动/清校准 → 轮询 `0x05E[7]`

### 5.4 符号速查

| 符号 | 含义 |
| --- | --- |
| \(f_{\text{ref}}\) / `parent_rate` | 参考钟（Pluto 40 MHz） |
| \(f_{\text{BBPLL}}\) / `rate` | 目标 VCO 频率 |
| \(N\) / `integer` | 整数分频字 |
| \(F\) / `fract` | 小数频字 |
| \(M\) | 模数 2088960 |
| `do_div(n,base)` | n←商，返回余数 |
| \(d\) | `REG_BBPLL` 环外分频 |
| \(K_{\text{VCO}}\) | 压控灵敏度 MHz/V |

---

## 6. 环路带宽折中

| 窄带宽 | 宽带宽 |
| --- | --- |
| 锁定慢 | 锁定快 |
| 压 SDM 杂散更好 | 杂散易漏 |
| 对 REF 噪声抑制较好 | 对 VCO 近端噪声抑制较差 |

改频序列：调 ICP/环滤 → 写频字 → 启动校准 → 等 LOCK。

---

## 7. PLL vs 纯分频

| | PLL | 纯分频（`REG_BBPLL`） |
| --- | --- | --- |
| 频率方向 | 可高于 REF | 只低于输入 |
| 噪声 | 引入环内噪声/杂散 | 不产生新噪声 |
| 复杂度 | PFD+CP+LF+VCO | 计数器 |

---

## 8. 相关笔记

- [[资源-AD9361-寄存器文档]]
- [[学习-Linux-驱动开发-AD9361-从零到通]]
- [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]
- [[MOC-射频]]
- [[MOC-FPGA]]（数字侧时钟与数据接口）
