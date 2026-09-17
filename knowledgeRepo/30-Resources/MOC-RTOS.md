---
type: moc
tags: [RTOS, FreeRTOS, 嵌入式, 实时系统, 学习路径]
created: 2026-09-09
updated: 2026-09-09
status: active
---

# MOC：RTOS（FreeRTOS 内核）

## 模块定位

学习路径块（与 [[MOC-Linux]] 平行，同属实现技术类，不替代 5G/6G 协议主线）。主线：用 FreeRTOS-Kernel 官方内核源码学 RTOS 核心机制——**任务与调度、任务间通信、时间与定时器、内存管理、中断集成、移植**。FreeRTOS 内核源码短而完整（无 demo / board 层），适合函数级精读，是理解「实时任务怎么被调度、中断怎么安全地交给任务」的最小载体。

## 学习入口

- 2026 Q4 双主线项目（RTOS 阶段 0–2 排入第 1/6 周）：[[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]]
- 阶段化学习清单（含代码锚点与产出要求）：[[学习-RTOS-学习路线]]

## 代码载体

| 仓库 | 本地路径 | 学什么 | 可用状态 |
| --- | --- | --- | --- |
| FreeRTOS-Kernel | `/home/congqiang/work/repo/FreeRTOS-Kernel` | 调度核心（tasks.c / list.c）、队列与信号量（queue.c / semphr.h）、事件组 / 流缓冲、软件定时器、heap_1~5、portable 移植（142 个 port.c） | ✓ 完整源码，可立即走读 |

## 主题地图

- **任务与调度**：TCB、就绪 / 阻塞 / 挂起链表、调度器启动、时间片与优先级
- **任务间通信**：队列 / 信号量 / 互斥量 / 递归互斥、事件组、流与消息缓冲
- **时间**：tick、软件定时器、`vTaskDelay` vs `vTaskDelayUntil`
- **内存管理**：`heap_1`~`heap_5` 差异与选型、静态 vs 动态创建
- **中断与移植**：`FromISR` API、临界区、Cortex-M 移植（PendSV / SysTick）

## 关联

- 平行对照：[[MOC-Linux]]（同样的事件，Linux 用 threaded IRQ / workqueue / 内核线程）
- 交叉主题：[[MOC-FPGA]]（Zynq / MicroBlaze 裸机与软核侧）、[[MOC-C++与软件]]
- 通信主线：[[领域-L1物理层]]、[[领域-L2数据链路层]]
- 待补：仓库地图笔记「仓库-FreeRTOS-Kernel」（建好后加入关联）
