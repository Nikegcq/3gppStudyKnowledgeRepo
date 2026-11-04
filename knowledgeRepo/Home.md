---
type: moc
tags: [主页]
created: 2026-09-03
updated: 2026-10-20
status: active
---

# 首页

通信行业个人知识库：围绕 5G/6G 无线接入，收集 **L1 / L2 / L3** 协议栈知识，以及 **FPGA、射频（RF）、C++** 等实现技术；通过 **O-RAN（O-CU / O-DU）** 开源仓库学代码；用公众号好文章做持续输入。目录结构与规则见 `README.md`。

## 领域（按协议层）

- [[领域-L1物理层]]
- [[领域-L2数据链路层]]
- [[领域-L3网络层]]

## 主题地图（跨层技术）

- [[MOC-FPGA]]
- [[MOC-射频]]
- [[MOC-C++与软件]]
- [[MOC-O-RAN开源]]
- [[MOC-Linux]]（Linux：u-boot / 内核 / 驱动 / DMA）
- [[MOC-RTOS]]（RTOS：FreeRTOS 内核）

## 进行中的项目

- [[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]]（2026-09-18 ~ 11-16：O-DU/L1 协议 + RFIC 使用）
- [[计划-独立线-Linux通用内核机制]]（独立延后，不在 Q4 八周内；Q4 收口后启动）
- [[计划-FPGA学习-GAO多卡采集工程]]（2026-09-30 起：以 GAO_325T 多卡采集工程学 FPGA）

## 期望未来做的项目

- [[自研DAPLink主板]]（STM32F103CB 自研 DAPLink 主机板：硬件适配、Flash 分区与软件修改映射）

## 已完成项目

- 6449：[[简历项目-6449-SP8-多载波功率均衡与O-RAN-Cplane]]（AIR 6449 / B77D，多载波功率均衡与 O-RAN C-plane 扩展）
- ZCU670：[[luxshare-zcu670]]（Luxshare ZCU670 / RFSoC、Linux + RPU、RFDC 与 radio 软件架构）

## 面试题

- 目录：`面试题/`（库根，独立于 PARA）
- [[Linux驱动加载与匹配-面试问答]]（题号 1–11；对应内核独立线 K2）

## 素材来源

- 公众号收藏：`30-Resources/公众号收藏`
- 开源仓库笔记：`30-Resources/开源仓库`
- 3GPP 规范：`30-Resources/3GPP规范`（PDF 在 `90-Attachments/3GPP规范/`，地图见 [[3GPP-38系列-NR物理层规范]]）
- 参考网站：[[ShareTechnote-5G手册]]（ShareTechnote 5G/NR 手册，L1 图解参考）
- 今日日记：[[2026-09-10]]

## 常用操作

- 随手记：新笔记默认进入 `00-Inbox`
- 收藏公众号文章：在 Codex 里粘贴链接或正文
- 备份：终端运行 `bash scripts/backup.sh`
