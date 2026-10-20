---
type: resource
tags: [RTOS, FreeRTOS, 开源仓库, 嵌入式, 内核, 仓库地图]
repo: FreeRTOS-Kernel
repo_url: https://github.com/FreeRTOS/FreeRTOS-Kernel
local_path: /home/congqiang/work/repo/FreeRTOS-Kernel
created: 2026-10-12
updated: 2026-10-12
status: active
---

# 仓库：FreeRTOS-Kernel

## 这是什么

FreeRTOS 官方**内核本体**仓库，只含内核，不含 demo 工程、板级支持和外设驱动——这正是它适合函数级精读的原因。核心 6 个源文件约 1.64 万行，就能讲清一个完整 RTOS 的调度、通信与移植；`portable/` 下另有 142 份 `port.c` 覆盖各种架构与工具链。它是理解「实时任务如何被调度、中断如何安全交给任务」的最小完整载体，和 [[MOC-Linux]] 是平行对照关系。

## 版本与状态

| 项 | 值 |
| --- | --- |
| 远程地址 | https://github.com/FreeRTOS/FreeRTOS-Kernel |
| 本地路径 | `/home/congqiang/work/repo/FreeRTOS-Kernel` |
| 分支 | `main` |
| HEAD | `7d6890e65`（Add ARM Cortex-M52 port support） |
| 内核版本 | `V11.1.0+`（见 `include/task.h:56`） |
| 核心 6 文件行数 | 16442（`tasks/queue/list/timers/event_groups/stream_buffer`） |
| 移植文件数量 | `port.c` 142 份，`portmacro.h` 155 份 |
| 内存管理 | `portable/MemMang/heap_1.c` ~ `heap_5.c` |
| 状态 | ✓ 完整源码，可立即走读 |

## 三层结构 → 实际路径映射

这是本系列组织的主线。注意本仓库是内核本体，所以「核心层」直接在根目录，而不是常见 STM32 工程里的 `FreeRTOS/Source/`。

| 层 | 常见工程里的说法 | 本仓库实际路径 | 关键文件 | 笔记 |
| --- | --- | --- | --- | --- |
| 核心层 | `FreeRTOS/Source/` | 仓库根目录 | `tasks.c`、`queue.c`、`list.c` | [[仓库-FreeRTOS-Kernel-核心层API与原理]] |
| 移植层 | `Source/portable/<工具链>/ARM_CM4F/` | `portable/GCC/ARM_CM4F/`（Keil AC5 为 `RVDS/`） | `port.c`、`portmacro.h` | [[仓库-FreeRTOS-Kernel-M4移植层解析]] |
| 配置层 | 工程根目录的 `FreeRTOSConfig.h` | `examples/template_configuration/FreeRTOSConfig.h`（仅模板） | `FreeRTOSConfig.h` | [[仓库-FreeRTOS-Kernel-FreeRTOSConfig配置详解]] |

## 目录 / 模块划分

| 路径 | 内容 | 是否精读 |
| --- | --- | --- |
| `tasks.c` | 任务管理 + 调度器（引擎） | ✓ 核心 |
| `queue.c` | 队列 / 信号量 / 互斥量（统一实现） | ✓ 核心 |
| `list.c` | 内核双向链表 | ✓ 核心 |
| `timers.c` | 软件定时器 | 用到再读 |
| `event_groups.c` | 事件组 | 用到再读 |
| `stream_buffer.c` | 流缓冲 / 消息缓冲 | 用到再读 |
| `croutine.c` | 协程（已淘汰） | 跳过 |
| `include/` | 所有对外头文件（`task.h` / `queue.h` / `list.h` / `semphr.h` …） | ✓ 读 API |
| `portable/` | 各架构/工具链移植层（142 份 `port.c`） | 只精读目标 port |
| `portable/MemMang/` | `heap_1`~`heap_5` 五种内存管理 | ✓ 选型 |
| `examples/template_configuration/` | `FreeRTOSConfig.h` 通用模板 | ✓ 配置基线 |
| `examples/cmake_example/` | 唯一可直接构建的示例（宿主 TEMPLATE port） | 验证构建流程 |

## 构建与运行

本仓库是**库**，本身不含可直接烧录的目标；`examples/cmake_example` 用宿主机的 TEMPLATE port，只能验证构建流程，**不代表能在 M4 上跑**。

| 场景 | 做法 |
| --- | --- |
| 作为库被引用 | 上游工程用 CMake `FetchContent` 拉取，再 `add_subdirectory`（见 `README.md`） |
| 跑官方示例（宿主机） | `cmake -S examples/cmake_example -B examples/cmake_example/build`，再 `cmake --build examples/cmake_example/build`，产物 `build/example` |
| 在 STM32F4 上跑 | 自建工程：加入 `tasks.c/queue.c/list.c` + `portable/GCC/ARM_CM4F/port.c` + 一个 `heap_x.c` + 自己的 `FreeRTOSConfig.h`，装好向量表 |

关键 CMake 选项：`FREERTOS_PORT`（选移植层）、`FREERTOS_HEAP`（选 heap 1~5）。

## 代码走读笔记（本系列）

| 笔记 | 内容 |
| --- | --- |
| [[仓库-FreeRTOS-Kernel-核心层API与原理]] | `list.c` / `tasks.c` / `queue.c` 的数据结构、API 与调度/通信原理 |
| [[仓库-FreeRTOS-Kernel-M4移植层解析]] | `ARM_CM4F` 的 `port.c` / `portmacro.h`：寄存器、PendSV 上下文切换、FPU、临界区 |
| [[仓库-FreeRTOS-Kernel-FreeRTOSConfig配置详解]] | 配置宏分类表 + M4 必改清单 + STM32F4 推荐值 |

## 推荐阅读顺序

| 步骤 | 读什么 | 产出 |
| --- | --- | --- |
| 1 | `list.c` / `list.h` | 理解内核链表与 `xItemValue` 排序 |
| 2 | `tasks.c` + `task.h` | 任务状态机、就绪/延时链表、调度与切换 |
| 3 | `queue.c` + `queue.h` / `semphr.h` | 队列/信号量/互斥量与阻塞唤醒 |
| 4 | `portable/GCC/ARM_CM4F/` | SVC/PendSV/SysTick、上下文切换、FPU |
| 5 | `FreeRTOSConfig.h` | 按板子裁剪出可运行配置 |

## 与标准 / 工作的对应

- 与 [[MOC-Linux]] 对照：FreeRTOS 用「ISR → `FromISR` → 队列 → 任务」，Linux 用 threaded IRQ / workqueue / 内核线程。
- 与 [[MOC-FPGA]] 交叉：Zynq / MicroBlaze 软核侧同样可跑 FreeRTOS。
- 通信主线里 RTOS 常作为协议栈/驱动的承载：见 [[领域-L2数据链路层]]。

## 疑问清单

- [ ] 选一块实际 Cortex-M 板（如 STM32F4）跑通真任务，替代纯静态走读。
- [ ] 用 `examples/cmake_example` + 调试器单步观察一次上下文切换。
- [ ] 决定综合实践题目（如某外设驱动或通信协议栈跑在 FreeRTOS 上）。

## 关联

- [[学习-RTOS-学习路线]]
- [[MOC-RTOS]]
- [[概念-ARM内核架构与FreeRTOS移植]]（ARM M/R/A 与 port 目录对应）
- [[MOC-Linux]]
- [[MOC-FPGA]]
