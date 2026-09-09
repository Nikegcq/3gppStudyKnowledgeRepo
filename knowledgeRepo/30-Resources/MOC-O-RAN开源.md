---
type: moc
tags: [O-RAN, O-CU, O-DU, 开源]
created: 2026-09-03
updated: 2026-09-03
status: active
---

# MOC：O-RAN 开源仓库

围绕 O-RAN 架构（O-CU / O-DU / O-RU 等）学习的开源仓库地图。学习笔记统一放在 `30-Resources/开源仓库/`，命名 `仓库-仓库名-主题.md`。

## 候选仓库

- **srsRAN Project**：5G NR 的 L1/L2/L3 开源实现，C++，GitHub `srsran/srsRAN_Project` —— 适合通读协议栈代码
- **OpenAirInterface（OAI）**：RAN 与核心网开源工程，官方代码库在 Eurecom GitLab（`openairinterface5g`）—— 覆盖面广、文档多
- **O-RAN Software Community（O-RAN SC）**：O-CU-CP / O-CU-UP / O-DU 等官方工程（`gerrit.o-ran-sc.org`，GitHub 有 `o-ran-sc` 镜像组）—— 与商用 O-RAN 架构对齐
- **UERANSIM**：5G UE 与模拟 gNB，GitHub `aligungr/UERANSIM` —— 适合学习接入与移动性信令流程

## 本地代码目录

- 建议统一克隆到库外：`~/study/opensource/<仓库名>`
- 库内只放笔记，不复制源码

## 学习进度

- [x] srsRAN_Project 仓库地图：[[仓库-srsRAN_Project]]
- [x] srsRAN_Project PHY 总览：[[仓库-srsRAN_Project-PHY总览]]
- [x] 信道编码与速率匹配：[[仓库-srsRAN_Project-信道编码与速率匹配]]
- [x] 下行物理信道与 OFDM 发射：[[仓库-srsRAN_Project-下行物理信道与OFDM发射]]
- [x] 上行接收与信道估计：[[仓库-srsRAN_Project-上行接收与信道估计]]
- [ ] 待添加：其余仓库（OAI / O-RAN SC / UERANSIM）的仓库地图

## 相关

- [[领域-L1物理层]]
- [[领域-L2数据链路层]]
- [[领域-L3网络层]]
- [[MOC-C++与软件]]
