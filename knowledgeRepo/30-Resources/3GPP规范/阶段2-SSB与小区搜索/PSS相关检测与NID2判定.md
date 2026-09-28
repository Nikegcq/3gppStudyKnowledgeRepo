---
type: resource
tags: [L1, 物理层, 3GPP, SSB, PSS, NID2, 相关检测, m序列, 小区搜索]
layer: L1
created: 2026-09-23
updated: 2026-09-23
status: active
source: 3GPP TS 38.211 §7.4.2.2；MATLAB 5G Toolbox nrPSS / hSSBurstFrequencyCorrect；见 [[3GPP-38系列-NR物理层规范]]
---

# PSS 相关检测与 N_ID^(2) 判定

## 一句话

5G NR 的 PSS 是长度 **127** 的 m 序列，用三个不同**循环移位**承载 \(N_{ID}^{(2)}\in\{0,1,2\}\)。判 ID 的核心是：接收 PSS 与本地三条候选序列分别**互相关**，取峰最大者对应的那个 ID。

## 序列怎么生成（3GPP TS 38.211 §7.4.2.2）

\[
d_{\mathrm{PSS}}(n)=1-2x(m),\qquad n=0,1,\ldots,126
\]

\[
m=(n+43\cdot N_{ID}^{(2)})\bmod 127
\]

其中 \(x(i)\) 由本原多项式递推：

\[
x(i+7)=(x(i+4)+x(i))\bmod 2
\]

三个 \(N_{ID}^{(2)}\) 对应循环移位 **0、43、86**（即 \(43\times N_{ID}^{(2)}\)）。

含义：三条 PSS **同一条 127 长 m 序列**，只是循环移位不同；移位间隔约 1/3 序列长，彼此可分，也利于抗频偏/定时误差下的歧义。

## 相关计算 → 定 \(N_{ID}^{(2)}\)

**步骤 1：本地三条候选**

本地预生成 \(\mathrm{PSS}_i\)，\(i=0,1,2\)（时域或频域均可；MATLAB 用 `nrPSS(i)`）。

**步骤 2：与接收信号互相关**

时域滑动相关（对接收序列 \(R\)、本地模板 \(p_i\)）：

\[
\mathrm{corr}_i[\tau]=\sum_{n} R[\tau+n]\cdot p_i^{*}[n]
\]

频域等价（对齐后逐子载波）：

\[
\mathrm{corr}_i=\sum_{k} R(k)\cdot \mathrm{PSS}_i^{*}(k)
\]

（MATLAB `hSSBurstFrequencyCorrect` 里是对每个候选频偏先反旋，再用 `nrTimingEstimate` 做整段时域相关，见 [[PSS检测与同步-定时频偏估计]]。）

**步骤 3：峰值最大者胜出**

\[
\widehat{N_{ID}^{(2)}}=\arg\max_{i\in\{0,1,2\}}\ \bigl|\mathrm{corr}_i\bigr|
\]

该 \(\mathrm{PSS}_{id}\) 即检测到的 \(N_{ID}^{(2)}\)。峰的位置同时是 **PSS 符号定时**。

## MATLAB 实现要点

```matlab
pss0 = nrPSS(0);  % N_ID^(2) = 0，循环移位 0
pss1 = nrPSS(1);  % 移位 43
pss2 = nrPSS(2);  % 移位 86
```

再与接收段（或参考网格里只放 PSS 的时域波形）分别相关，取峰最大者。

注意：

1. **PSS 检测通常与时间同步、频偏补偿绑在一起**——峰位给符号定时，频偏会压低相关峰幅度，故常见做法是按半子载波步进扫粗频偏（`hSSBurstFrequencyCorrect`），在每个 \(\Delta f\) 假设上对 3 条 PSS 相关，全局最大给出 \((\widehat{\Delta f},\widehat{N_{ID}^{(2)}},\hat\tau)\)。
2. 仅就 **\(N_{ID}^{(2)}\) 判定**而言，逻辑仍是三条候选互相关比峰值。
3. 先 PSS（3 选 1）再 SSS（336 选 1）是为了把相关运算量降两个数量级，见 [[小区搜索流程分步详解]]。

## 相关式一览

| 量 | 公式 | 输出 |
| --- | --- | --- |
| PSS 序列 | \(d(n)=1-2x\big((n+43 N_{ID}^{(2)})\bmod 127\big)\) | 3 条候选 |
| 互相关 | \(\mathrm{corr}_i[\tau]=\sum_n R[\tau+n]p_i^*[n]\) | 3 条相关曲线 |
| 判 ID | \(\arg\max_i\|\mathrm{corr}_i\|\) | \(N_{ID}^{(2)}\)、定时 |
| 细频偏（CP） | \(\Delta f=\angle\big(\sum y_{\mathrm{cp}}y_{\mathrm{tail}}^*\big)/(2\pi T_u)\) | 残余 CFO |

## 关联

- [[PSS检测与同步-定时频偏估计]]（滑动相关、CP/跨符号频偏、分段非相干）
- [[PSS检测与同步实现参考]]（MATLAB / srsRAN / OAI 代码位置）
- [[小区搜索流程分步详解]]（Step 1：PSS 在整条链里的位置）
- [[学习-阶段2-SSB与小区搜索]]（阶段 2 主笔记）
- [[CORESET0时频位置计算]]（MIB 之后的 SIB1 定位）
