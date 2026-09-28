---
type: moc
tags: [Linux, 嵌入式, u-boot, 内核, 驱动开发, DMA, 学习路径]
created: 2026-09-09
updated: 2026-09-15
status: active
---

# MOC：Linux（嵌入式系统软件）

## 模块定位

学习路径块（与 [[MOC-RTOS]] 平行，同属实现技术类，不替代 5G/6G 协议主线）。执行版为 **9 阶段单一路径**：阶段 0–2 打通用内核地基（源码地图 → 最小驱动 → QEMU+GDB），阶段 3–4 过渡到设备模型与 Pluto 启动链，阶段 5–6 进入控制面（ad9361/IIO）与数据面（cf_axi_adc/DMA/libiio），阶段 7–8 收口中断并发与 RAN 映射。代码载体是 PlutoSDR 固件工程，正好是一条真实数据链：AD9361（RF）→ FPGA（hdl）→ AXI DMA → Linux 驱动 → 用户态（libiio）。

## 学习入口

**两条计划线，勿混进度**：

| 线 | 计划 | 状态 |
| --- | --- | --- |
| 进行中（2026 Q4 八周） | [[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]] —— 主线 B 为 **RFIC（AD9361）使用** | active |
| 独立、不在八周内 | [[计划-独立线-Linux通用内核机制]] —— 模块/VFS/QEMU+GDB/设备模型/DMA/中断（K1–K6） | planned，Q4 收口后或按需启动 |

- 面试题（库根 `面试题/`）：[[Linux驱动加载与匹配-面试问答]]（1–11，对应 K2 设备模型）
- 优化整合版执行路线（9 阶段长期全文，含 Pluto P 线；**不是** Q4 进度表）：[[学习-Linux-学习路线]]
- 阶段 0 成果（QEMU+GDB 环境、源码地图、产物链）：[[学习-Linux-阶段0-源码地图与调试环境]]
- T 线方法与环境：[[学习-Linux-内核源码阅读与驱动学习法]]（源码地图 / 最小模块 / QEMU+GDB / 设备模型 / 资源）
- 概念书：[[书籍-Linux内核设计与实现（LKD）]]（Robert Love，第 3 版；子系统导览）
- 驱动全景：[[概念-物理层射频驱动全景]]（RFIC 驱动 / 数据面 / 用户态 / L1 功能四层）
- AD9361 零基础教学（结合实板 dump）：[[学习-Linux-驱动开发-AD9361-从零到通]]
- 阶段 3 深读：[[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]（dtsi → SPI/platform 匹配 → ad9361_probe → cf_axi_adc → IIO DMA buffer）
- AD9361 寄存器文档（UG-570 / Datasheet / 驱动头文件）：[[资源-AD9361-寄存器文档]]

## 代码载体

| 仓库 | 本地路径 | 学什么 | 可用状态 |
| --- | --- | --- | --- |
| plutosdr-fw（ADI PlutoSDR 固件） | `/home/congqiang/work/repo/plutosdr-fw` | u-boot / Linux 内核 / 设备树 / 驱动（IIO）/ DMA 全链 | 顶层 Makefile / scripts ✓；四个子模块已按锁定 commit 初始化（2026-09-09 经 ghfast.top 镜像）：`buildroot @ e783aadc`、`hdl @ 065c8f18`、`linux @ f3da30df`、`u-boot-xlnx @ 90401ce9` |

## 主题地图

- **通用内核地基（T 线）**：源码树地图、最小模块 / 字符设备、QEMU+GDB、bus-device-driver 设备模型、子系统选型
- **u-boot**：启动流程、环境变量、FIT 镜像（先加载 FPGA bitstream 再启动内核）
- **Linux 内核**：启动过程、设备树、bus/device/driver 驱动模型
- **驱动开发**：模块 / 字符设备骨架、IIO 框架（ad9361、cf_axi_adc / cf_axi_dds）
- **DMA**：axi_dmac 数据通路、dmaengine、mmap / libiio 用户态
- **中断与并发**：threaded IRQ、workqueue、自旋锁 / 互斥锁

## 关联

- 平行对照：[[MOC-RTOS]]（同样的数据到达事件在 RTOS 里怎么做）
- 交叉主题：[[MOC-FPGA]]（hdl / AXI DMA）、[[MOC-射频]]（AD9361 前端）、[[MOC-O-RAN开源]]、[[MOC-C++与软件]]
- 通信主线：[[领域-L1物理层]]
- 待补：仓库地图笔记「仓库-plutosdr-fw」（建好后加入关联）
