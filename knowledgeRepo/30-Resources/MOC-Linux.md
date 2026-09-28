---
type: moc
tags: [Linux, 嵌入式, u-boot, 内核, 驱动开发, DMA, 学习路径]
created: 2026-09-09
updated: 2026-09-18
status: active
---

# MOC：Linux（嵌入式系统软件）

## 模块定位

学习路径块（与 [[MOC-RTOS]] 平行）。执行版为 9 阶段路径：内核地基 → 设备模型与 Pluto 启动链 → AD9361/IIO 与 DMA → 中断并发与 RAN 映射。代码载体：PlutoSDR 固件（u-boot / linux / hdl / buildroot）。

## 学习入口

| 线 | 计划 | 状态 |
| --- | --- | --- |
| 进行中（2026 Q4） | [[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]] | active |
| 独立线 | [[计划-独立线-Linux通用内核机制]] | planned |

- 面试题总目录：[[面试题-目录]]
- **启动 / U-Boot（面试题 1～22）**：[[Bootloader面试-问答]]（路径 `面试题/Linux/Bootloader/`）— BootROM、FSBL、Zynq 内存/bitstream、MicroBlaze、STM32/i.MX、DCD 等
- **驱动 / 设备模型**：[[Linux驱动加载与匹配-面试问答]]（路径 `面试题/Linux/`）
- 学习路线：[[学习-Linux-学习路线]]
- 其余 AD9361 / 阶段笔记见库内 Linux 学习条目

**面试题目录布局：**

```text
面试题/
├── 面试题-目录.md
├── Linux/
│   ├── Linux驱动加载与匹配-面试问答.md
│   └── Bootloader/
│       └── Bootloader面试-问答.md
└── C++/
    └── （C++ 面试题系列）
```

## 主题地图

- **u-boot / Bootloader**：[[Bootloader面试-问答]]
- **Linux 驱动模型**：[[Linux驱动加载与匹配-面试问答]]
- **DMA / IIO / 中断**：见学习路线与阶段笔记

## 关联

- [[MOC-RTOS]] · [[MOC-FPGA]] · [[MOC-射频]] · [[MOC-C++与软件]] · [[MOC-O-RAN开源]]
- [[领域-L1物理层]]
- [[面试题-目录]]
