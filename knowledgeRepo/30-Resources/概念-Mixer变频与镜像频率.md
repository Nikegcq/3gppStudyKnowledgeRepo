---
type: note
tags: [RF, 射频, Mixer, 混频器, 镜像频率, 零中频, I/Q, 正交混频, AD9361, 硬件]
created: 2026-09-17
updated: 2026-09-17
status: active
source: 原理通识 + AD9361 UG-570 对照
---

# 概念：Mixer 变频与镜像频率（含 AD9361）

> 若觉得本篇公式偏多，请先读图解版：[[概念-Mixer与IQ-图解步骤]]（含零中频 I/Q 框图 ![[图-零中频接收机-IQ框图.png]]）；本篇作推导与 AD9361 细节。

## 一句话总结

混频器用**乘法**把频谱搬到 LO 两侧（和频、差频）；下变频时若只保留差频，则存在另一个射频 $f_{\mathrm{image}}=2f_{\mathrm{LO}}-f_{\mathrm{RF}}$ 也会落到**同一个 IF**——这就是镜像。超外差用 RF BPF 压镜像 + IF BPF 选差频；**AD9361 是零中频**，靠片内 **I/Q 正交混频** 区分正负频（消镜像），混频后是 **基带 LPF**。天线只有**一路实信号**；I/Q 是用相差 90° 的两路 LO **下变频后拆出来的**，不是信号自带的。

---

## 0. 符号约定

| 符号 | 全称 / 含义 |
| --- | --- |
| **RF** | Radio Frequency，射频（天线口） |
| **IF** | Intermediate Frequency，中频 |
| **LO** | Local Oscillator，本振 |
| $f_{\mathrm{RF}}$ | 有用射频频率 |
| $f_{\mathrm{LO}}$ | 本振频率 |
| $f_{\mathrm{IF}}$ | 中频 $=\lvert f_{\mathrm{RF}}-f_{\mathrm{LO}}\rvert$ |
| $f_{\mathrm{image}}$ | 镜像 $=2f_{\mathrm{LO}}-f_{\mathrm{RF}}$ |
| $I(t),Q(t)$ | 同相 / 正交基带，$z_{BB}=I+jQ$ |

---

## 1. 为什么需要 Mixer

| 侧 | 问题 |
| --- | --- |
| 天线 / 空口 | 信号在 RF（70 MHz–6 GHz） |
| ADC / DAC / 数字 | 适合在基带或较低中频 |
| Mixer | 收 = 下变频，发 = 上变频 |

---

## 2. 原理：时域相乘 → 频域两个边带

理想混频器是乘法器：

$$
y(t)=x(t)\cdot\cos(\omega_{\mathrm{LO}}t)
$$

单音输入 $\cos(\omega_{\mathrm{RF}}t)$ 时，积化和差：

$$
\cos(\omega_{\mathrm{RF}}t)\cos(\omega_{\mathrm{LO}}t)
=\frac{1}{2}\cos(\omega_{\mathrm{RF}}-\omega_{\mathrm{LO}})t
+\frac{1}{2}\cos(\omega_{\mathrm{RF}}+\omega_{\mathrm{LO}})t
$$

| 分量 | 频率 | 典型用途 |
| --- | --- | --- |
| 差频 | $\lvert f_{\mathrm{RF}}-f_{\mathrm{LO}}\rvert$ | 下变频要的 |
| 和频 | $f_{\mathrm{RF}}+f_{\mathrm{LO}}$ | 通常滤掉 |

---

## 3. 镜像频率

定义：

$$
f_{\mathrm{IF}}=\lvert f_{\mathrm{in}}-f_{\mathrm{LO}}\rvert
$$

**绝对值**导致两个不同的 $f_{\mathrm{in}}$ 得到同一个 $f_{\mathrm{IF}}$。设 $f_{\mathrm{RF}}=f_{\mathrm{LO}}-f_{\mathrm{IF}}$，另一个解为 $f_{\mathrm{LO}}+f_{\mathrm{IF}}$，代入得：

$$
f_{\mathrm{image}}=2f_{\mathrm{LO}}-f_{\mathrm{RF}}
$$

$$
f_{\mathrm{RF}}+f_{\mathrm{image}}=2f_{\mathrm{LO}}
$$

**数值例（LO=100 MHz）**：117 MHz 与 83 MHz 都差出 17 MHz，互为镜像。

---

## 4. 超外差 vs 零中频（简表）

| | 超外差 | 零中频（AD9361） |
| --- | --- | --- |
| IF | 固定中频 | ≈0 |
| 和频 | IF BPF | 基带 LPF 甩开 |
| 镜像 | RF BPF 压 $2f_{LO}-f_{RF}$ | **I/Q** 分正负频 |
| 带外阻塞 | RF BPF | 片外预选/双工 |

---

## 5. AD9361 中的 Mixer 与 LO

```text
RX: 天线 → LNA → [Mixer↓ + Rx LO] → TIA(+LPF) → Rx BB LPF → ADC → I/Q
TX: I/Q → 内插 → DAC → BB LPF → [Mixer↑ + Tx LO] → 衰减 → Buffer
```

配置：`ad9361_set_rx/tx_lo_freq`（Hz）；FDD/TDD/External LO；Quad Cal、RF DC Cal。

### 5.4 Mixer 后 / Mixer 前的两级 LPF（滤什么）

**RX（混频后）**

| 级 | 角点（约） | 滤掉什么 |
|----|------------|----------|
| TIA LPF（单极点） | 2.5×BBBW | 和频 $f_{RF}+f_{LO}$、远端杂散、带外宽带噪声 |
| Rx BB LPF（三阶 Butterworth） | 1.4×BBBW | 邻道/带外干扰、带外噪声、**ADC 抗混叠** |

**TX（混频前，对偶）**

| 级 | 角点（约） | 滤掉什么 |
|----|------------|----------|
| Tx BB LPF（三阶） | 1.6×BBBW | DAC 镜像与重建毛刺 |
| Tx Secondary LPF（单极点） | 5×BBBW | 带外噪声（改善 ACLR） |

**分工记忆**：一阶先滤「又远又大」（和频等）；三阶再「贴近通道收干净 + 抗混叠」。  
**镜像与 DC 不靠 LPF**：镜像靠 I/Q + Quad Cal；LO 泄漏/直流失调靠 RF DC Cal、BB DC Cal。

见图解版 [[概念-Mixer与IQ-图解步骤]] 步骤 5。

---

## 6. 常见误解：「LO = 接收频率就没有镜像了？」

**不对。** $f_{\mathrm{LO}}=f_{\mathrm{RF}}$ 时 $f_{\mathrm{image}}=f_{\mathrm{RF}}$，镜像贴到信号上；实信号 ±f 对称，单路混频会**折叠**。零中频必须 I/Q；不完美则有残余镜像 → Quad Cal。

---

## 7. I/Q 从哪来？——详细公式推导

### 7.1 天线上只有一路实信号

接收时，天线口电压是**实函数**：

$$
x(t)=A(t)\cos\bigl(\omega_{\mathrm{RF}}t+\phi(t)\bigr)\in\mathbb{R}
$$

用欧拉公式：

$$
\cos\theta=\frac{e^{j\theta}+e^{-j\theta}}{2}
$$

可写成：

$$
x(t)=\frac{1}{2}A(t)\Bigl[
e^{\,j(\omega_{\mathrm{RF}}t+\phi)}
+e^{-j(\omega_{\mathrm{RF}}t+\phi)}
\Bigr]
$$

含义：

- 频谱在 $+f_{\mathrm{RF}}$ 与 $-f_{\mathrm{RF}}$ **各有一份**（幅度关系由实信号约束）
- 这不是两路天线信号，而是**同一实信号的完整描述**
- **I/Q 不在射频上，而是后面用正交本振「拆」出来的**

### 7.2 单路实混频：为什么 +f 与 −f 会叠

只乘 $\cos(\omega_{\mathrm{LO}}t)$。对复指数分量 $e^{\pm j\omega_{\mathrm{RF}}t}$：

$$
e^{\,j\omega_{\mathrm{RF}}t}\cos(\omega_{\mathrm{LO}}t)
=\frac{1}{2}e^{\,j(\omega_{\mathrm{RF}}-\omega_{\mathrm{LO}})t}
+\frac{1}{2}e^{\,j(\omega_{\mathrm{RF}}+\omega_{\mathrm{LO}})t}
$$

$$
e^{-j\omega_{\mathrm{RF}}t}\cos(\omega_{\mathrm{LO}}t)
=\frac{1}{2}e^{-j(\omega_{\mathrm{RF}}+\omega_{\mathrm{LO}})t}
+\frac{1}{2}e^{-j(\omega_{\mathrm{RF}}-\omega_{\mathrm{LO}})t}
$$

低通只留差频项后，$+f_{\mathrm{RF}}$ 贡献 $e^{+j\omega_{\mathrm{IF}}t}$，$-f_{\mathrm{RF}}$ 贡献 $e^{-j\omega_{\mathrm{IF}}t}$。  
在**实基带**里这两项共轭对称，观察到的实信号无法区分「谁来自上边带、谁来自下边带」→ **镜像折叠**。

### 7.3 正交本振：I 与 Q 的定义

片内生成相位差 90° 的两路 LO：

$$
\mathrm{LO_I}(t)=\cos(\omega_{\mathrm{LO}}t),\qquad
\mathrm{LO_Q}(t)=\sin(\omega_{\mathrm{LO}}t)
$$

下变频（乘法 + 基带 LPF，略去和频）后近似：

$$
I(t)\approx \frac{1}{2}A(t)\cos\bigl(\omega_{\mathrm{IF}}t+\phi\bigr)
$$

$$
Q(t)\approx \frac{1}{2}A(t)\sin\bigl(\omega_{\mathrm{IF}}t+\phi\bigr)
$$

（符号约定可能差一个整体相位/符号，不影响「两路正交」这一本质。）

合成复基带：

$$
z_{BB}(t)=I(t)+jQ(t)
$$

### 7.4 与复指数下变频等价

因为

$$
e^{-j\omega_{\mathrm{LO}}t}=\cos(\omega_{\mathrm{LO}}t)-j\sin(\omega_{\mathrm{LO}}t)
$$

所以

$$
z_{BB}(t)=\bigl(I_{\mathrm{RF}}(t)+jQ_{\mathrm{RF}}(t)\bigr)\cdot e^{-j\omega_{\mathrm{LO}}t}
$$

的实现方式就是：**实部与 cos 混、虚部与 sin 混**（接收时实信号可看作解析信号的实部）。

更完整地，把实信号 $x(t)$ 的频谱 $X(f)$（满足 $X(-f)=X^*(f)$）乘以 $e^{-j\omega_{\mathrm{LO}}t}$，频域是**平移**：

$$
Z_{BB}(f)=X(f+f_{\mathrm{LO}})
$$

- 原来在 $+f_{\mathrm{RF}}$ 的那瓣 → 移到 $f_{\mathrm{RF}}-f_{\mathrm{LO}}=+f_{\mathrm{IF}}$
- 原来在 $-f_{\mathrm{RF}}$ 的那瓣 → 移到 $-f_{\mathrm{RF}}-f_{\mathrm{LO}}$（和频侧）或经共轭对称关系落到 $-f_{\mathrm{IF}}$

理想解析化 / 正交接收后，**上边带与下边带不再落在同一实频率**，镜像与信号分离。

### 7.5 直接算：上边带与下边带分别落到哪

设两个单音（简化，幅度 1）：

$$
x(t)=\cos(\omega_{U}t)+\cos(\omega_{L}t)
$$

其中 $\omega_{U}>\omega_{\mathrm{LO}}>\omega_{L}$，且关于 LO 对称：

$$
\omega_{U}=\omega_{\mathrm{LO}}+\omega_{m},\qquad
\omega_{L}=\omega_{\mathrm{LO}}-\omega_{m}
$$

**I 路**（乘 cos，LPF）：

$$
I(t)=\frac{1}{2}\cos(\omega_{m}t)+\frac{1}{2}\cos(\omega_{m}t)=\cos(\omega_{m}t)
$$

上下边带在 I 上**同相相加**，分不开。

**Q 路**（乘 sin，LPF）利用
$\cos\omega t\cdot\sin\omega_{\mathrm{LO}}t$ 的差频：

- 上边带 $\cos(\omega_{\mathrm{LO}}+\omega_m)t$ → Q 含 $-\frac{1}{2}\sin(\omega_{m}t)$
- 下边带 $\cos(\omega_{\mathrm{LO}}-\omega_m)t$ → Q 含 $+\frac{1}{2}\sin(\omega_{m}t)$

于是对称双音时

$$
Q(t)=-\frac{1}{2}\sin(\omega_{m}t)+\frac{1}{2}\sin(\omega_{m}t)=0
$$

只看 I 仍是 $\cos(\omega_m t)$，**分不清上下边带**；但 I 与 Q 的**相对符号**不同：

- 只存在上边带：$I\propto\cos\omega_m t$，$Q\propto-\sin\omega_m t$，即 $z_{BB}\propto e^{-j\omega_m t}$
- 只存在下边带：$I\propto\cos\omega_m t$，$Q\propto+\sin\omega_m t$，即 $z_{BB}\propto e^{+j\omega_m t}$

（若 Q 混频用 $-\sin$ 或整体再旋转 180°，符号会对调，但「正负频可区分」不变。）

**结论**：只看 I 分不清；**I 与 Q 的相对符号/相位**能区分上、下边带 → 消镜像。

### 7.6 用解析信号一句话概括

对实信号取解析信号（希尔伯特变换）得到只有 $+f$ 的 $z_{RF}(t)$，再乘 $e^{-j\omega_{\mathrm{LO}}t}$ 平移到基带，镜像在理想数学下被去掉。  
硬件上用 **cos/sin 两路混频近似**这一操作；幅相误差 → 残余镜像。

### 7.7 幅相误差时的残余镜像（定性）

设

$$
\tilde{I}=(1+\epsilon)I,\qquad
\tilde{Q}=Q\ \text{相位偏了}\ \Delta\phi
$$

则镜像抑制比（IRR）有限，大致

$$
\mathrm{IRR}\propto \frac{1}{\epsilon^{2}+(\Delta\phi)^{2}}
$$

这就是 AD9361 需要 **Rx Quad Tracking / Tx Quad Cal** 的原因：把 $\epsilon,\Delta\phi$ 修小。

### 7.8 发射端对偶

$$
s_{\mathrm{RF}}(t)=I(t)\cos(\omega_{\mathrm{LO}}t)-Q(t)\sin(\omega_{\mathrm{LO}}t)
$$

等价于 $\mathrm{Re}\{z_{BB}(t)\,e^{j\omega_{\mathrm{LO}}t}\}$，只产生一个有用边带（理想）。

---

## 8. 与 AD9361 对照

| 概念 | 芯片实现 |
| --- | --- |
| 实信号入口 | Rx1A/B/C 等，仍是单路（差分对）RF |
| 正交 LO | RFPLL → 分频/分相 → LOI/LOQ |
| I/Q 下变频 | 片内 Mixer |
| I/Q 数字输出 | ADC 后 12-bit I/Q 给 BBP |
| 校准 | Rx Quad Tracking、Tx Quad Cal、RF DC Cal |

---

## 9. 和「TX Power」的边界

| 模块 | 管什么 |
| --- | --- |
| Mixer + LO + I/Q | 频率搬移、镜像/边带 |
| Tx 衰减器 | 相对功率 |
| 板级标定 | 绝对 dBm |

---

## 10. 易混点自检

1. 和频 ≠ 镜像；镜像是另一个 RF。
2. LO=100 MHz 时，117 与 83 单路混频都到 17 MHz。
3. **I/Q 是下变频拆出来的**，不是天线自带两路。
4. **LO=RF ≠ 无镜像**，变成 ±f 折叠，仍要 I/Q。
5. 零中频混频后有基带 LPF，不是没有滤波。

---

## 相关

- [[概念-锁相环PLL与VCO]]：LO 从哪来
- [[概念-ADC与Delta-Sigma入门]]：混频后进 ADC
- [[概念-物理层射频驱动全景]]
- [[资源-AD9361-寄存器文档]]
- [[学习-Linux-驱动开发-AD9361-从零到通]]
- 图：[[图-AD9361-TX-RX路径硬件模块.excalidraw]]
- 入口：[[MOC-射频]]
