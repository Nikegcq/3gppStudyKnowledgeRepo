---
type: resource
tags: [FPGA, GAO_325T, 软件架构, 远程升级, drawio]
layer: L1
created: 2026-10-19
updated: 2026-10-19
status: active
source: prj_colotrum/*.dio
---

# 图：GAO_325T 工程结构、模块状态与远程升级流程

以下三张图来自 `C:\Users\Admin\work\prj_colotrum` 中的 draw.io XML 源文件。SVG 用于 Obsidian 直接预览，`.drawio` 保留为可编辑源文件。

## 1. 系统详细结构与数据通路

![[new_struct.svg]]

可编辑源文件：[[new_struct.drawio]]

## 2. 软件与 FPGA 模块实现状态

![[开发模块.svg]]

可编辑源文件：[[开发模块.drawio]]

## 3. Flash 分区与远程升级流程

![[远程升级.svg]]

可编辑源文件：[[远程升级.drawio]]

## 读图提醒

- 图中“从收到第一个 card 数据开始 3us 定时”与现有笔记中的“3 s 超时”不一致；代码 `pkg_data_to_eth.v` 使用 `r_wait_cnt == 12'd1000`，按 100 MHz 约 10 us。三处数值需要以板上时钟和实测为准。
- `.drawio` 文件本身不能由 Obsidian 原生渲染；需要 draw.io Desktop 或 diagrams.net 打开。SVG 是由本地脚本转换的预览版，布局和文字基本保留，精确样式以 `.drawio` 为准。

## 关联

- [[仓库-GAO_325T-工程总览]]
- [[仓库-GAO_325T-系统架构与数据通路]]
- [[计划-FPGA学习-GAO多卡采集工程]]
- [[MOC-FPGA]]
