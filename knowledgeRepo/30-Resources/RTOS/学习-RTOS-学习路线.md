---
type: resource
tags: [RTOS, FreeRTOS, 嵌入式, 学习计划, 任务调度, 队列, 中断, 移植]
created: 2026-09-09
updated: 2026-09-09
status: active
---

# RTOS 学习路线（FreeRTOS-Kernel）

## 一句话总结

参照通信知识（L1）的学习结构：**阶段化学习计划 + 「主读材料」映射表 + 概念 / 学习笔记 + 进度勾选**。通信学习里「规范章节」的位置，这里换成 **RTOS 内核源码文件**；FreeRTOS 是「最小可读的完整 RTOS 实现」，目标：能独立讲清任务切换、任务间通信与中断集成，并完成一次移植 / 运行验证。

## 本地代码与状态（截至 2026-09-09）

| 载体 | 本地路径 | 状态 |
| --- | --- | --- |
| FreeRTOS-Kernel | `/home/congqiang/work/repo/FreeRTOS-Kernel` | ✓ 完整（HEAD `7d6890e65`，git describe `V10.4.3-741-…`，README 关联 V11.1.0 / 202406 LTS）；核心 `tasks.c` / `queue.c` / `timers.c` 等约 1.7 万行；`portable/` 142 个 port.c；`portable/MemMang/` 提供 heap_1~5 |

## 阶段学习清单

| 阶段 | 主题与核心问题 | 主读：代码 / 文件 | 配套资料 | 练习 / 产出 |
| --- | --- | --- | --- | --- |
| 0 | 全景与「最小阅读集」：内核源码怎么组织、先读哪几个文件 | `README.md`、`include/`（FreeRTOS.h / task.h / queue.h / list.h 等头文件分工）、`tasks.c` / `queue.c` 行数体量、`examples/template_configuration/FreeRTOSConfig.h`、`examples/cmake_example/main.c` | FreeRTOS Developer Docs / 官方文档 | 仓库地图笔记；画「内核文件地图」（对应通信学习里的总体架构一步） |
| 1 | 任务与调度：RTOS 的「多任务」到底是什么，怎么切换 | `tasks.c`（TCB 结构、`xTaskCreateStatic` / `xTaskCreate`、就绪 / 延时链表、`vTaskStartScheduler`、调度点与任务切换入口）、`list.c` / `list.h`（内核链表）、空闲任务与 Idle Hook | FreeRTOS 文档 Tasks & Scheduler | 笔记「学习-RTOS-任务与调度」；画任务状态迁移图（Running / Ready / Blocked / Suspended） |
| 2 | 任务间通信：任务之间怎么安全传数据、怎么互斥 | `queue.c` + `semphr.h`（队列 / 信号量 / 互斥 / 递归互斥）、`event_groups.c`、`stream_buffer.c`、`message_buffer.h`；优先级反转场景 | FreeRTOS 文档（Queue / Semaphore / Mutex） | 笔记「学习-RTOS-任务间通信」；做一张「什么时候选队列 / 信号量 / 事件组 / 流缓冲」的对照表 |
| 3 | 时间与软件定时器：tick 怎么驱动延时与调度 | `timers.c`、`FreeRTOS.h` 里的 tick 配置、`vTaskDelay` vs `vTaskDelayUntil`、tickless idle（`configUSE_TICKLESS_IDLE`） | FreeRTOS 文档（Software Timers） | 笔记「概念-RTOS-时间与定时器」；弄清 tick 精度 / 漂移问题 |
| 4 | 内存管理：动态创建的内存从哪来，heap 怎么选 | `portable/MemMang/heap_1.c` ~ `heap_5.c`（差异：碎片 / 线程安全 / 支持跨堆）；`xTaskCreateStatic` 与静态分配（对照 `examples/cmake_example/main.c`） | FreeRTOS 文档（Memory Management） | 笔记「概念-FreeRTOS-内存管理」；给出选型表 |
| 5 | 中断集成与移植：ISR 里怎么安全地「唤醒任务」，RTOS 怎么上硬件 | `portable/GCC/ARM_CM4F/port.c`（SysTick / PendSV / 临界区 / 上下文切换）、`portmacro.h`；`FromISR` 结尾 API：`xQueueSendFromISR`、`xSemaphoreGiveFromISR`、`taskYIELD_FROM_ISR`；`configMAX_SYSCALL_INTERRUPT_PRIORITY` | FreeRTOS 文档（Interrupts / Porting） | 笔记「学习-RTOS-中断与临界区」；画「中断 → 队列 → 任务唤醒」路径 |
| 6 | 综合实践：跑一个最小应用，并和 Linux 块对照 | 开发板或模拟环境：2 个任务 + 1 个队列 + 1 个定时器；精读所选 port 的移植差异；对照 [[MOC-Linux]]（同样的事件，Linux 用 threaded IRQ / workqueue，RTOS 用 ISR → 队列 → 任务） | 所选 MCU 手册 / 移植指南 | 端到端运行一次；产出「Linux vs RTOS 数据通路分工」对照图 |

## 每个阶段的收尾动作（沿用通信学习习惯）

1. 建「学习-<主题>」笔记并勾选进度；
2. 关键概念沉淀为「概念-<主题>」笔记并互链；
3. 代码锚点记录到文件 / 函数 / 行；
4. 复盘写入当日 `50-Journal`；
5. 更新本清单与 [[MOC-RTOS]]。

## 学习进度

- [ ] 阶段 0：全景与最小阅读集
- [ ] 阶段 1：任务与调度
- [ ] 阶段 2：任务间通信
- [ ] 阶段 3：时间与软件定时器
- [ ] 阶段 4：内存管理
- [ ] 阶段 5：中断集成与移植
- [ ] 阶段 6：综合实践与 Linux 对照

## 待办 / 疑问

- [ ] RTOS 实践载体：先用 `examples/cmake_example`（模板 port 下只验证流程），还是定一块 Cortex-M 板（如 STM32）跑真任务
- [ ] 精读哪个 port 作为主线：建议先 ARM Cortex-M4F（资料最多），若有实际 MCU 再按芯片选
- [ ] 是否需要与后续工程结合（如某外设驱动、通信协议栈跑在 RTOS 上），决定综合实践题目

## 关联

- [[MOC-RTOS]]（模块主页）
- [[MOC-Linux]]（平行对照块）
- [[MOC-FPGA]]、[[MOC-C++与软件]]
- [[领域-L1物理层]]、[[领域-L2数据链路层]]
- [[Home]]
