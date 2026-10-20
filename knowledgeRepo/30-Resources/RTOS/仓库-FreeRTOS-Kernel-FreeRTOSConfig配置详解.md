---
type: resource
tags: [RTOS, FreeRTOS, FreeRTOSConfig, 配置, 裁剪, Cortex-M4, STM32]
layer: 配置层
repo: FreeRTOS-Kernel
repo_url: https://github.com/FreeRTOS/FreeRTOS-Kernel
local_path: /home/congqiang/work/repo/FreeRTOS-Kernel
created: 2026-10-12
updated: 2026-10-12
status: active
---

# 仓库-FreeRTOS-Kernel-FreeRTOSConfig 配置详解

## 一句话总结

`FreeRTOSConfig.h` 是你工程自己的文件，决定内核**怎么裁剪、怎么跑**。模板 `examples/template_configuration/FreeRTOSConfig.h` 里大量安全值是**演示占位**（20MHz、100Hz、64 位 tick、系统调用优先级 0），直接照搬 STM32F4 会在调度器启动时断言。下面按类别给出全部宏的作用与取值建议。

> ⚠️ 模板里 `configMAX_SYSCALL_INTERRUPT_PRIORITY = 0`、`configKERNEL_INTERRUPT_PRIORITY = 0` 在 Cortex-M4 上**不可用**：`0` 是最高优先级，且 `BASEPRI=0` 表示不屏蔽任何中断，`port.c` 会直接 `configASSERT` 失败。

## 1. 硬件描述

| 宏 | 模板值 | 作用 | M4 / STM32 建议 |
| --- | --- | --- | --- |
| `configCPU_CLOCK_HZ` | `20000000` | 驱动 tick 的时钟频率（通常=系统主频） | 按板子改，如 F407 跑 168MHz 就填 `168000000` |
| `configSYSTICK_CLOCK_HZ` | 未定义 | 仅 Cortex-M 用；SysTick 时钟≠内核时钟时定义 | 默认不定义；若 SysTick 走别的时钟源，填实际频率 |

## 2. 调度行为

| 宏                                         | 模板值                       | 作用                     | M4 建议                                                  |
| ----------------------------------------- | ------------------------- | ---------------------- | ------------------------------------------------------ |
| `configTICK_RATE_HZ`                      | `100`                     | tick 中断频率（Hz）          | 常用 `1000`（1ms）；`100`→10ms 太粗                           |
| `configUSE_PREEMPTION`                    | `1`                       | `1`=抢占式；`0`=协作式        | 一般 `1`                                                 |
| `configUSE_TIME_SLICING`                  | `0`                       | `1`=同优先级任务按 tick 轮转    | 需要公平轮转就设 `1`；硬实时希望确定性强可设 `0`                           |
| `configUSE_PORT_OPTIMISED_TASK_SELECTION` | `0`                       | `1`=用 CLZ 选最高优先级       | M4 建议 `1`（port 层缺省也是 1），要求 `configMAX_PRIORITIES ≤ 32` |
| `configUSE_TICKLESS_IDLE`                 | `0`                       | `1`=低功耗 tickless       | 需要低功耗再开；有 `vPortSuppressTicksAndSleep` 支持              |
| `configMAX_PRIORITIES`                    | `5`                       | 优先级总数（0 ~ N-1，0 最低）    | `5`~`7` 通常够；开了位图选优先级须 ≤ 32                             |
| `configMINIMAL_STACK_SIZE`                | `128`                     | **空闲任务**栈深度（单位：字，不是字节） | `128` 字=512 字节，一般够；用 HAL 打印可加大                         |
| `configMAX_TASK_NAME_LEN`                 | `16`                      | 任务名最大长度（含结尾 `\0`）      | `8`~`16`                                               |
| `configTICK_TYPE_WIDTH_IN_BITS`           | `TICK_TYPE_WIDTH_64_BITS` | tick 计数位宽（16/32/64）    | M4 **推荐 `TICK_TYPE_WIDTH_32_BITS`**；64 位慢且占空间          |
| `configIDLE_SHOULD_YIELD`                 | `1`                       | 空闲任务是否让位于同级应用任务        | `1`                                                    |
| `configTASK_NOTIFICATION_ARRAY_ENTRIES`   | `1`                       | 每任务通知数组长度              | `1` 最省；需要多路通知再加大                                       |
| `configQUEUE_REGISTRY_SIZE`               | `0`                       | 队列/信号量注册表大小（内核感知调试用）   | 不用 IDE 调试队列就 `0`                                       |
| `configENABLE_BACKWARD_COMPATIBILITY`     | `0`                       | `1`=映射旧版本函数名/类型        | 新工程 `0`                                                |
| `configNUM_THREAD_LOCAL_STORAGE_POINTERS` | `0`                       | 每任务 TLS 指针槽数量          | 不用 TLS 就 `0`                                           |
| `configUSE_MINI_LIST_ITEM`                | `1`                       | `1`=用省 RAM 的迷你哨兵       | 保留 `1`（除非编译器严格别名优化出问题）                                 |
| `configSTACK_DEPTH_TYPE`                  | `size_t`                  | 栈深度参数类型                | 保留 `size_t`，或改 `uint16_t` 省空间                          |
| `configMESSAGE_BUFFER_LENGTH_TYPE`        | `size_t`                  | 消息缓冲长度字段类型             | 消息都很短可改 `uint8_t`/`uint16_t` 省 RAM                     |
| `configHEAP_CLEAR_MEMORY_ON_FREE`         | `1`                       | 释放时清零（安全，但费时间）         | 安全优先保留 `1`；性能优先 `0`                                    |
| `configSTATS_BUFFER_MAX_LENGTH`           | `0xFFFF`                  | 旧版 `vTaskList` 缓冲长度假设  | 新工程改用带长度的 API，保留默认即可                                   |
| `configUSE_NEWLIB_REENTRANT`              | `0`                       | 每任务 newlib 重入结构（栈空间）   | 不用 newlib 就 `0`                                        |

## 3. 软件定时器

只有 `configUSE_TIMERS = 1` 时才需要并生效；同时工程必须加入 `timers.c`。

| 宏 | 模板值 | 作用 | 建议 |
| --- | --- | --- | --- |
| `configUSE_TIMERS` | `1` | 是否编译软件定时器功能 | 用就 `1` |
| `configTIMER_TASK_PRIORITY` | `configMAX_PRIORITIES - 1` | 定时器服务任务优先级 | 一般取最高 |
| `configTIMER_TASK_STACK_DEPTH` | `configMINIMAL_STACK_SIZE` | 定时器任务栈（字） | 回调复杂时加大 |
| `configTIMER_QUEUE_LENGTH` | `10` | 定时器命令队列长度 | 并发定时器多时加大 |

## 4. 事件组 / 流缓冲

| 宏 | 模板值 | 作用 | 建议 |
| --- | --- | --- | --- |
| `configUSE_EVENT_GROUPS` | `1` | 编译事件组（需 `event_groups.c`） | 用就 `1` |
| `configUSE_STREAM_BUFFERS` | `1` | 编译流/消息缓冲（需 `stream_buffer.c`） | 用就 `1` |

## 5. 内存管理

| 宏 | 模板值 | 作用 | 建议 |
| --- | --- | --- | --- |
| `configSUPPORT_STATIC_ALLOCATION` | `1` | 允许静态创建对象 | 车规/安全场景优先静态 |
| `configSUPPORT_DYNAMIC_ALLOCATION` | `1` | 允许动态创建对象（需 heap_x.c） | 一般 `1`；纯静态工程可 `0` |
| `configTOTAL_HEAP_SIZE` | `4096` | FreeRTOS 堆大小（字节，heap_1/2/4） | **必改**；按任务数放大，如 `15360`~`40960` |
| `configAPPLICATION_ALLOCATED_HEAP` | `0` | `1`=应用自己定义堆数组 | 需把堆放指定内存段时设 `1` |
| `configSTACK_ALLOCATION_FROM_SEPARATE_HEAP` | `0` | `1`=任务栈走独立堆 | 需要把栈放快速 RAM 时开，并实现 `pvPortMallocStack` |
| `configENABLE_HEAP_PROTECTOR` | `0` | heap_4/5 指针越界与混淆保护 | 调试期建议 `1` |

## 6. 中断嵌套配置（M4 最关键）

| 宏 | 模板值 | 作用 | M4 建议 |
| --- | --- | --- | --- |
| `configKERNEL_INTERRUPT_PRIORITY` | `0` | tick / 切换中断的优先级 | **ARM_CM4F 移植层不读取此宏**（它硬编码 PendSV/SysTick 为最低 255）；保留默认即可，别依赖它 |
| `configMAX_SYSCALL_INTERRUPT_PRIORITY` | `0` | 可调用 `FromISR` API 的优先级阈值 | **必改**；如 4 位优先级、取抢占 5 → `5 << (8-4)` = `0x50`。必须非 0 且是有效优先级值 |
| `configMAX_API_CALL_INTERRUPT_PRIORITY` | `0` | 上者的别名（因 port 而异） | 不用；CM4F port 用 `configMAX_SYSCALL_INTERRUPT_PRIORITY` |

**规则**：优先级数值越大越低。调用 FreeRTOS API 的中断，其 NVIC 优先级数值必须 **≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY`**；数值更小的紧急中断不会被 RTOS 屏蔽，但**绝不能调用任何 `FromISR` API**。见 [[仓库-FreeRTOS-Kernel-M4移植层解析]]。

## 7. Hook 与回调

| 宏 | 模板值 | 作用 | 建议 |
| --- | --- | --- | --- |
| `configUSE_IDLE_HOOK` | `0` | 空闲任务钩子 | 用则 `1` 并实现 `vApplicationIdleHook()` |
| `configUSE_TICK_HOOK` | `0` | 每 tick 钩子 | 慎用（在 tick 上下文，要极快） |
| `configUSE_MALLOC_FAILED_HOOK` | `0` | 堆分配失败钩子 | 建议 `1`，便于排查堆不足 |
| `configUSE_DAEMON_TASK_STARTUP_HOOK` | `0` | 定时器守护任务启动钩子 | 按需 |
| `configUSE_SB_COMPLETED_CALLBACK` | `0` | 流/消息缓冲收发完成回调 | 按需 |
| `configCHECK_FOR_STACK_OVERFLOW` | `2` | 栈溢出检查：`1` 检查 SP 越界，`2` 检查栈尾魔数 | 调试期保留 `2`；量产可关以提速 |

## 8. 运行时统计

| 宏 | 模板值 | 作用 | 建议 |
| --- | --- | --- | --- |
| `configGENERATE_RUN_TIME_STATS` | `0` | 统计各任务占用时间 | 需要性能分析才开，并配计时源 |
| `configUSE_TRACE_FACILITY` | `0` | 增加跟踪/可视化所需的 TCB 字段 | 用 Tracealyzer / `vTaskList` 时开 |
| `configUSE_STATS_FORMATTING_FUNCTIONS` | `0` | 编译 `vTaskList` / `vTaskGetRunTimeStats` | 需要打印任务表时开 |

## 9. 协程（基本淘汰）

| 宏 | 模板值 | 作用 | 建议 |
| --- | --- | --- | --- |
| `configUSE_CO_ROUTINES` | `0` | 编译协程（需 `croutine.c`） | 直接用任务，保持 `0` |
| `configMAX_CO_ROUTINE_PRIORITIES` | `1` | 协程优先级数 | 不用协程时无意义 |

## 10. 调试辅助

| 宏 | 模板值 | 作用 |
| --- | --- | --- |
| `configASSERT(x)` | 关中断 + 死循环 | 断言失败时停机便于定位；是栈溢出、中断优先级等校验的前提，**调试期务必定义** |
| `configASSERT_DEFINED` | 由上面是否定义自动推出 | 移植层据此启用 `vPortValidateInterruptPriority()` |

## 11. MPU 相关（普通 M4 不用）

仅 Cortex-M **MPU 版** port 使用（如 `portable/GCC/ARM_CM4_MPU`），普通 ARM_CM4F 不读取。

| 宏 | 模板值 | 作用 |
| --- | --- | --- |
| `configINCLUDE_APPLICATION_DEFINED_PRIVILEGED_FUNCTIONS` | `0` | 允许应用自定义特权函数 |
| `configTOTAL_MPU_REGIONS` | `8` | 硬件 MPU 区域数 |
| `configTEX_S_C_B_FLASH` / `_SRAM` | `0x07UL` | Flash / RAM 区域 TEX/S/C/B 属性 |
| `configENFORCE_SYSTEM_CALLS_FROM_KERNEL_ONLY` | `1` | 是否只允许内核发起特权提升 |
| `configALLOW_UNPRIVILEGED_CRITICAL_SECTIONS` | `0` | 非特权任务能否进临界区 |
| `configUSE_MPU_WRAPPERS_V1` | `0` | 用 v1 还是 v2 MPU wrapper |
| `configPROTECTED_KERNEL_OBJECT_POOL_SIZE` | `10` | v2 wrapper 下内核对象池上限 |
| `configSYSTEM_CALL_STACK_SIZE` | `128` | 每任务系统调用栈（字） |
| `configENABLE_ACCESS_CONTROL_LIST` | `1` | 是否启用对象访问控制列表 |

## 12. SMP 相关（M4 单核不用）

| 宏 | 模板值 | 作用 | M4 建议 |
| --- | --- | --- | --- |
| `configNUMBER_OF_CORES` | 未定义（默认 1） | 核数 | 单核保持默认 |
| `configRUN_MULTIPLE_PRIORITIES` | `0` | 多核是否允许不同优先级并行 | 不适用 |
| `configUSE_CORE_AFFINITY` | `0` | 核亲和 | 不适用 |
| `configTASK_DEFAULT_CORE_AFFINITY` | `tskNO_AFFINITY` | 默认核亲和掩码 | 不适用 |
| `configUSE_TASK_PREEMPTION_DISABLE` | `0` | 单任务可关抢占（SMP） | 不适用 |
| `configUSE_PASSIVE_IDLE_HOOK` | `0` | 被动空闲钩子（SMP） | 不适用 |
| `configTIMER_SERVICE_TASK_CORE_AFFINITY` | `tskNO_AFFINITY` | 定时器任务核亲和 | 不适用 |

## 13. ARMv8-M 专用（M4 不用）

M4 属 ARMv7-M，以下宏**对 ARM_CM4F 无效**，保留模板值即可，不要据此判断 M4 功能。

| 宏 | 模板值 | 适用 |
| --- | --- | --- |
| `secureconfigMAX_SECURE_CONTEXTS` | `5` | ARMv8-M 安全侧 |
| `configKERNEL_PROVIDED_STATIC_MEMORY` | `1` | ARMv8-M |
| `configENABLE_TRUSTZONE` | `1` | ARMv8-M TrustZone |
| `configRUN_FREERTOS_SECURE_ONLY` | `1` | ARMv8-M |
| `configENABLE_MPU` | `1` | ARMv8-M port |
| `configENABLE_FPU` | `1` | ARMv8-M port（**M4 的 FPU 靠编译器 `__ARM_FP`，不看这个宏**） |
| `configENABLE_MVE` | `1` | Cortex-M52/M55/M85 |

## 14. ARMv7-M / ARMv8-M 通用

| 宏 | 模板值 | 作用 | M4 建议 |
| --- | --- | --- | --- |
| `configCHECK_HANDLER_INSTALLATION` | `1` | 校验 SVC/PendSV 是否正确装到向量表 | 保留 `1`（走间接路由时设 `0`） |

## 15. 功能开关（configUSE_*）

| 宏 | 模板值 | 作用 |
| --- | --- | --- |
| `configUSE_TASK_NOTIFICATIONS` | `1` | 任务通知（轻量同步） |
| `configUSE_MUTEXES` | `1` | 互斥量 + 优先级继承 |
| `configUSE_RECURSIVE_MUTEXES` | `1` | 递归互斥量 |
| `configUSE_COUNTING_SEMAPHORES` | `1` | 计数信号量 |
| `configUSE_QUEUE_SETS` | `0` | 队列集 |
| `configUSE_APPLICATION_TASK_TAG` | `0` | 任务标签，供应用挂私有数据 |
| `configUSE_POSIX_ERRNO` | `0` | 每任务 `FreeRTOS_errno` |

## 16. API 裁剪（INCLUDE_*）

`1`=编译该 API，`0`=不编译。多数链接器会自动去掉未用函数，但显式裁剪能加快编译、减小体积。

| 宏 | 模板值 | 对应 API |
| --- | --- | --- |
| `INCLUDE_vTaskPrioritySet` | `1` | `vTaskPrioritySet()` |
| `INCLUDE_uxTaskPriorityGet` | `1` | `uxTaskPriorityGet()` |
| `INCLUDE_vTaskDelete` | `1` | `vTaskDelete()` |
| `INCLUDE_vTaskSuspend` | `1` | `vTaskSuspend()` / `vTaskResume()` |
| `INCLUDE_xTaskDelayUntil` | `1` | `xTaskDelayUntil()` |
| `INCLUDE_vTaskDelay` | `1` | `vTaskDelay()` |
| `INCLUDE_xTaskGetSchedulerState` | `1` | `xTaskGetSchedulerState()` |
| `INCLUDE_xTaskGetCurrentTaskHandle` | `1` | `xTaskGetCurrentTaskHandle()` |
| `INCLUDE_uxTaskGetStackHighWaterMark` | `0` | `uxTaskGetStackHighWaterMark()` |
| `INCLUDE_xTaskGetIdleTaskHandle` | `0` | `xTaskGetIdleTaskHandle()` |
| `INCLUDE_eTaskGetState` | `0` | `eTaskGetState()` |
| `INCLUDE_xTimerPendFunctionCall` | `0` | `xTimerPendFunctionCall()` |
| `INCLUDE_xTaskAbortDelay` | `0` | `xTaskAbortDelay()` |
| `INCLUDE_xTaskGetHandle` | `0` | `xTaskGetHandle()` |
| `INCLUDE_xTaskResumeFromISR` | `1` | `xTaskResumeFromISR()` |

## 17. STM32F4 必改清单 + 推荐起始值

模板值→可跑值的对照（以 F407 @168MHz、4 位 NVIC 抢占优先级为例）：

| 宏 | 模板值 | STM32F4 建议 | 理由 |
| --- | --- | --- | --- |
| `configCPU_CLOCK_HZ` | `20000000` | `168000000` | 必须等于真实主频 |
| `configTICK_RATE_HZ` | `100` | `1000` | 1ms 时基 |
| `configTICK_TYPE_WIDTH_IN_BITS` | `TICK_TYPE_WIDTH_64_BITS` | `TICK_TYPE_WIDTH_32_BITS` | M4 上 32 位更高效 |
| `configMAX_SYSCALL_INTERRUPT_PRIORITY` | `0` | `0x50`（= `5 << 4`） | 非 0 且有效；只用 4 位优先级 |
| `configUSE_PORT_OPTIMISED_TASK_SELECTION` | `0` | `1` | 用 CLZ 加速选任务 |
| `configUSE_TIME_SLICING` | `0` | `1` | 同优先级公平轮转 |
| `configTOTAL_HEAP_SIZE` | `4096` | `15360`~`40960` | 按任务/队列数量放大 |
| `configMAX_PRIORITIES` | `5` | `5`~`7` | 够用即可 |
| `configCHECK_FOR_STACK_OVERFLOW` | `2` | `2` | 调试期强烈建议 |
| `NVIC_SetPriorityGrouping(0)` | — | 启动调度器前调用 | 全部位作抢占优先级 |

## 18. 生效关系速查

| 配置宏 | 影响的内核模块 |
| --- | --- |
| `configMAX_PRIORITIES` | `tasks.c` 就绪链数组、TCB 结构 |
| `configUSE_PREEMPTION` / `configUSE_TIME_SLICING` | `tasks.c` 调度策略 |
| `configUSE_MUTEXES` | TCB 增 `uxBasePriority`、`uxMutexesHeld`；`queue.c` 优先级继承 |
| `configUSE_TASK_NOTIFICATIONS` | TCB 增通知数组 |
| `configUSE_TIMERS` | 需 `timers.c`、定时器任务与队列 |
| `configSUPPORT_STATIC/DYNAMIC_ALLOCATION` | 决定静态/动态 API 与结构体字段 |
| `configMAX_SYSCALL_INTERRUPT_PRIORITY` | `portmacro.h` 的 BASEPRI、`port.c` 断言 |
| `configUSE_PORT_OPTIMISED_TASK_SELECTION` | `portmacro.h` 位图 + CLZ |
| `configUSE_TICKLESS_IDLE` | `port.c` 的 `vPortSuppressTicksAndSleep` |
| `configCHECK_FOR_STACK_OVERFLOW` | `tasks.c` 切换时栈检查 |
| `INCLUDE_*` | 对应 API 是否编译 |

## 疑问清单

- [ ] 在 STM32F407 上实测 `configMAX_SYSCALL_INTERRUPT_PRIORITY=0x50` 与 HAL 的优先级分组配合是否通过断言。
- [ ] 用 `uxTaskGetStackHighWaterMark()` 反推各任务实际需要的栈，替换拍脑袋的 `configMINIMAL_STACK_SIZE`。
- [ ] 对比 `configUSE_TIME_SLICING` 开/关时同优先级任务的时序。

## 关联

- [[仓库-FreeRTOS-Kernel]]（仓库地图）
- [[仓库-FreeRTOS-Kernel-核心层API与原理]]
- [[仓库-FreeRTOS-Kernel-M4移植层解析]]
- [[学习-RTOS-学习路线]]（阶段 0、5）
- [[MOC-RTOS]]
