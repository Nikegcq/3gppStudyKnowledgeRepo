---
type: note
tags: [RF, 射频, ADC, Delta-Sigma, ΔΣ, AD9361, 过采样, 硬件, 入门]
created: 2026-09-15
updated: 2026-09-15
status: active
source: 通识 + AD9361 UG-570 / Linux ad9361_rx_adc_setup 对照
---

# 概念：ADC 与 Delta-Sigma 入门（含 AD9361）

## 一句话总结

ADC 把连续电压变成数字码；AD9361 片内 Rx ADC 是**三阶连续时间 ΔΣ**，靠**高倍过采样 + 噪声整形**换精度；`sampling_frequency` 只是抽取后的数据率，和片内 ADC_CLK 不是一回事。寄存器 `0x200`–`0x227` 是该调制器的**模拟偏置表**，必须随钟/带宽由驱动重算。

---

## 1. ADC 是什么

- **输入**：连续电压 \(v(t)\)
- **输出**：每隔 \(1/F_s\) 一个数字码

常见类型：

| 类型 | 特点 | 场景 |
| --- | --- | --- |
| Flash | 一堆比较器，极快、位数低 | ΔΣ 内部粗量化 |
| SAR | 逐次逼近，中速 | MCU 等 |
| **ΔΣ** | 极高过采样 + 噪声整形 | 通信基带（AD9361） |

---

## 2. 为什么 ΔΣ 采样率要很高

### 过采样（OSR）

\[
\mathrm{OSR}=\frac{F_{s,\text{ADC}}}{F_s},\quad
\text{SQNR}\approx 6.02N+1.76+10\log_{10}(\mathrm{OSR})
\]

OSR 翻 4 倍 ≈ 多约 6 dB（约 1 bit）。

### 噪声整形

环路把量化噪声推到信号带外，带内更干净。

### 模拟抗混叠更好做

\(F_{s,\text{ADC}}\gg B\) 时过渡带宽，模拟滤波可以「软」；锐截止交给数字抽取。

### 数字抽取

高速比特流 → 数字低通 → 降采样 → **对外 sampling frequency**。

---

## 3. ΔΣ 环路（小白结构）

```text
输入 ──►(+)──► 积分器1 ──► 积分器2 ──► 积分器3 ──► 量化(Flash) ──► 数字
        ▲                                                        │
        └──────────────── 反馈 DAC ◄─────────────────────────────┘
```

误差 = 输入 − 反馈，不断积分，逼输出平均值跟上输入。

### 部件词典

| 术语 | 小白解释 |
| --- | --- |
| 积分器 | 攒误差；R 定「进水快慢」，C 定「桶多大」 |
| 电阻 R / 电容 C | 时间常数 \(RC\)，决定跟随速度 |
| 反馈 DAC | 数字结果转回模拟，从输入减掉 |
| 电流源 | 尽量恒流的电路 |
| NMOS / PMOS | 两种 MOS 管 |
| Cascode | 叠管提高阻抗，电流更稳更线性 |
| 偏置电流 | 给运放/比较器工作点 |
| Flash | 一堆比较器，粗量化 |
| 三阶 | 三个积分器，整形更强 |
| Clk Delay | 环内时钟对齐 |
| Cc | 运放补偿，防自激 |

---

## 4. 时钟：三层不要混

```text
REF (40 MHz) → BBPLL → REG_BBPLL ÷d → ADC_CLK（ΔΣ 转换率）
                                              │
                                              ▼ 数字抽取
                                    sampling_frequency（IQ 数据率）
信道带宽 B：模拟 LPF + 数字滤波决定的「窗」
```

| 量 | 典型 | 约束 |
| --- | --- | --- |
| 信道带宽 B | 如 20 MHz | 与 Fs 匹配，留过渡带 |
| sampling frequency | 如 30.72 Msps | **I/Q 复采样** \(F_s\gtrsim B\)（实采样才是 \(2B\)） |
| ADC_CLK | 数十～数百 MHz | AD9361：**25–640 MHz** |
| BBPLL VCO | ~0.7–1.4 GHz | 见 [[概念-锁相环PLL与VCO]] |

工程上 \(F_s\gtrsim B/0.8\)；20 MHz 常用 25～30.72 Msps。

---

## 5. AD9361 的 ADC（UG-570）

- 架构：**third-order continuous time delta-sigma modulator**，高度可编程  
- 寄存器**随 ADC 采样钟变化**，初值必须正确  
- Linux：`ad9361_rx_adc_setup()` 一次写 **40 字节**，地址 **`0x200`–`0x227`**（`data[i] → 0x200+i`）  
- 输入：`bbpll_freq`、`adc_sampl_freq_Hz`、已校准 BBF（C3/R2346 等）

```text
ADC_CLK < 80 MHz  → scale_snr ≈ 1.0
ADC_CLK ≥ 80 MHz  → scale_snr ≈ 1.585
BBBW clamp 到 200 kHz–28 MHz
```

---

## 6. `0x200`–`0x227` 分组（模拟偏置表）

```text
0x200–0x206  时钟延迟 / 测试 MUX     ← 固定（Flash 延迟 0x24）
0x207–0x20E  INT1/2/3 的 R、C、Amp Cc ← 随 ADC_CLK、BBBW 计算
0x20F–0x218  FB DAC 电流（3 级 + 总偏置 0x2E）
0x219–0x221  运放 1st/cascode/2nd 电流 ← 随 ADC_CLK
0x222–0x225  Flash 偏置（部分固定 ladder）
0x226–0x227  复位 / 保留 = 0
```

| 地址 | 宏（摘） | 作用 |
| --- | --- | --- |
| 0x207/0x208 | INT1 R/C | 第 1 级积分器 |
| 0x20A/0x20B | INT2 R/C | 第 2 级 |
| 0x20C/0x20D | INT3 R/C | 第 3 级 |
| 0x20F–0x217 | FB DAC NMOS/cascode/PMOS | 三级反馈电流 |
| 0x218 | FB_DAC_BIAS | 总偏置 |
| 0x219–0x221 | INT 各级运放电流 | 带宽/功耗 |
| 0x222–0x225 | FLASH_* | 量化器偏置 |

**不能手写死**：钟或带宽变了，RC/电流不匹配会不稳或噪声变差。

---

## 7. 和模拟前端的衔接

| 模块 | 约关系（UG-570） |
| --- | --- |
| Rx TIA | 混频后，0/−6 dB，极点约 **2.5×** 基带带宽 |
| Rx 基带模拟滤波 | 需校准；BBBW 进 ADC setup 公式 |
| Tx secondary filter | 约 **5×** 基带带宽，压带外噪声 |
| 最大模拟信道带宽 | **56 MHz** |
| LVDS DATA_CLK 最大 | **245.76 MHz**（接口钟，≠ ADC_CLK） |

---

## 8. 读代码时怎么用

1. 看到 `sampling_frequency` → 想 **数据率**，不是 ADC 钟  
2. 看到 `0x200` 写一大串 → **ΔΣ 模拟偏置**，跟 `ad9361_rx_adc_setup` 走  
3. 看到 BBPLL / `REG_BBPLL` → 产生 ADC_CLK 的上游，见 PLL 笔记  
4. 看到带宽校准 / TIA → 进 ADC setup 之前的 BBBW 来源  

---

## 9. 相关笔记

- [[概念-ADC采样量化与SAR]]（采样+量化；SAR 二分 vs Flash）
- [[概念-锁相环PLL与VCO]]（BBPLL → ADC_CLK）
- [[资源-AD9361-寄存器文档]]
- [[学习-Linux-驱动开发-AD9361-从零到通]]
- [[MOC-射频]]
- [[MOC-FPGA]]（抽取后的 IQ 如何进 FPGA/DMA）
