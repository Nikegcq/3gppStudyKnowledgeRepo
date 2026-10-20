---
type: resource
tags: [RTOS, FreeRTOS, 内核, 任务调度, 队列, 信号量, list, 源码走读]
layer: 核心层
repo: FreeRTOS-Kernel
repo_url: https://github.com/FreeRTOS/FreeRTOS-Kernel
local_path: /home/congqiang/work/repo/FreeRTOS-Kernel
created: 2026-10-12
updated: 2026-10-12
status: active
---

# 仓库-FreeRTOS-Kernel-核心层 API 与原理

## 一句话总结

核心层是与硬件无关的 RTOS 引擎：`list.c` 提供内核链表脚手架，`tasks.c` 用「按优先级排列的就绪链表 + 延时链表」实现任务调度，`queue.c` 用「一个环形缓冲区 + 两条阻塞任务链表」同时实现队列、信号量和互斥量。三者只依赖移植层暴露的宏（`portYIELD`、`taskENTER_CRITICAL` 等），不碰任何寄存器。

## 核心层在仓库中的位置

本仓库是 FreeRTOS-Kernel **内核本体**，不是某个 STM32 工程，所以核心层文件**直接位于仓库根目录**，而不是 `FreeRTOS/Source/` 下。

| 层 | 常见工程里的说法 | 本仓库实际路径 | 关键文件 | 是否修改 |
| --- | --- | --- | --- | --- |
| 核心层 | `FreeRTOS/Source/` | 仓库根目录 | `tasks.c`、`queue.c`、`list.c` | 不改，只读 |
| 移植层 | `Source/portable/<工具链>/ARM_CM4F/` | `portable/<工具链>/ARM_CM4F/` | `port.c`、`portmacro.h` | 不改，精读 |
| 配置层 | 工程里的 `FreeRTOSConfig.h` | `examples/template_configuration/` 仅为模板 | `FreeRTOSConfig.h` | 按板子改 |

| 文件 | 行数 | 角色 |
| --- | --- | --- |
| `tasks.c` | 8861 | 调度器 + 任务管理，内核引擎 |
| `queue.c` | 3387 | 队列 / 计数信号量 / 互斥量的统一实现 |
| `list.c` | 248 | 内核双向链表，被上面两者复用 |
| `timers.c` | 1434 行头文件对应 | 软件定时器（内核之上的服务） |
| `event_groups.c` | — | 事件组 |
| `stream_buffer.c` | — | 流缓冲 / 消息缓冲 |

## 1. list.c / list.h：内核的脚手架

### 数据结构

| 结构               | 字段                                       | 说明                                           |
| ---------------- | ---------------------------------------- | -------------------------------------------- |
| `ListItem_t`     | `xItemValue`                             | 排序键。多数链表按它**升序**排列                           |
|                  | `pxNext` / `pxPrevious`                  | 双向指针，构成环形链表                                  |
|                  | `pvOwner`                                | 指回持有该结点的对象（通常是 TCB）                          |
|                  | `pxContainer`                            | 指回所属 `List_t`，单结点只属于一条链                      |
| `MiniListItem_t` | 仅 `xItemValue` / `pxNext` / `pxPrevious` | 省 RAM 的哨兵版本，`configUSE_MINI_LIST_ITEM=1` 时使用 |
| `List_t`         | `uxNumberOfItems`                        | 结点计数，O(1) 判空                                 |
|                  | `pxIndex`                                | 遍历游标，供 `listGET_OWNER_OF_NEXT_ENTRY()` 轮转    |
|                  | `xListEnd`                               | 尾哨兵，`xItemValue` 取最大值，永远排在最后                 |

### API

| API                     | 作用                      | 关键点                          |
| ----------------------- | ----------------------- | ---------------------------- |
| `vListInitialise()`     | 初始化一条空链表                | 把 `xListEnd` 的首尾指针指向自己，形成自环  |
| `vListInitialiseItem()` | 初始化结点                   | 置空 `pxContainer`             |
| `vListInsert()`         | **按 `xItemValue` 升序**插入 | 用于延时链表、阻塞链表；`list.c:139`     |
| `vListInsertEnd()`      | 插到 `pxIndex` 前（尾部）      | 用于就绪链表，保持同级轮转顺序；`list.c:105` |
| `uxListRemove()`        | 从链表中摘除                  | 返回摘除后剩余结点数；`list.c:217`      |

### 原理要点

1. **环形双向链表**：头尾相连，没有 NULL 边界判断，插删都是 O(1)（`vListInsert` 的定位是 O(n)，但内核里链表很短）。
2. **尾哨兵 `xListEnd`**：值为最大，等价于「永远排在最后的边界」，让插入逻辑无需特判空链表。
3. **两种插入语义**：`vListInsert` 有序（延时 / 阻塞列表需要按唤醒时间、优先级排序），`vListInsertEnd` 无序（就绪列表只需同级 FIFO 轮转）。
4. **`pxIndex` 与轮转**：`listGET_OWNER_OF_NEXT_ENTRY()` 每次把 `pxIndex` 前移一格，实现同优先级任务的**时间片轮转**；跳过 `xListEnd` 哨兵。
5. **结点复用**：每个 TCB 里内嵌两个结点——`xStateListItem`（挂状态链表）和 `xEventListItem`（挂事件/阻塞链表），同一任务可同时出现在两条链上。

## 2. tasks.c / task.h：任务与调度

### 任务控制块 TCB

仅列关键字段（完整定义见 `tasks.c:374`）：

| 字段                                  | 类型              | 作用                                                 |
| ----------------------------------- | --------------- | -------------------------------------------------- |
| `pxTopOfStack`                      | `StackType_t *` | **必须是 TCB 第一个成员**——移植层靠 `*pxCurrentTCB` 直接取它做上下文切换 |
| `xStateListItem`                    | `ListItem_t`    | 挂到「就绪 / 延时 / 挂起 / 等待终止」之一，表示任务状态                   |
| `xEventListItem`                    | `ListItem_t`    | 挂到队列等待链、事件组等事件链，`xItemValue` 存优先级                  |
| `uxPriority`                        | `UBaseType_t`   | 当前优先级（0 最低），可被互斥量临时提升                              |
| `uxBasePriority`                    | `UBaseType_t`   | 原始优先级，优先级继承结束后回退用（`configUSE_MUTEXES`）             |
| `pxStack` / `pxEndOfStack`          | `StackType_t *` | 栈内存范围，用于溢出检查                                       |
| `pcTaskName`                        | `char[]`        | 调试用任务名                                             |
| `ulNotifiedValue` / `ucNotifyState` | 数组              | 任务通知的值与状态                                          |
| `uxMutexesHeld`                     | `UBaseType_t`   | 持有的互斥量个数，优先级继承用                                    |

### 任务状态

FreeRTOS 对外状态（`eTaskGetState()` 返回值，见 `task.h:104`）与内部链表的对应：

| 对外状态         | 含义                     | 内部所在链表                                   |
| ------------ | ---------------------- | ---------------------------------------- |
| `eRunning`   | 正在运行（查询的是自己）           | `pxReadyTasksLists[px]` + `pxCurrentTCB` |
| `eReady`     | 就绪，等待 CPU              | `pxReadyTasksLists[px]`                  |
| `eBlocked`   | 阻塞（延时 / 等队列 / 等事件，带超时） | `pxDelayedTaskList` 或事件链表                |
| `eSuspended` | 挂起（无限期），含「无限超时阻塞」      | `xSuspendedTaskList`                     |
| `eDeleted`   | 已删除但 TCB 尚未回收          | `xTasksWaitingTermination`               |

状态迁移：Ready → Running（被调度）→ Blocked（延时/等资源）→ Ready（超时或被唤醒）；任意状态可被 `vTaskSuspend()` 打入 Suspended，被 `vTaskResume()` 拉回 Ready。

### 内核维护的关键链表

定义位置：`tasks.c:475` 起。

| 链表 | 用途 |
| --- | --- |
| `pxReadyTasksLists[configMAX_PRIORITIES]` | **按优先级分桶**的就绪任务；下标即优先级 |
| `pxDelayedTaskList` | 按唤醒 tick 升序排列的阻塞任务 |
| `pxOverflowDelayedTaskList` | tick 计数回绕时的溢出任务，tick 溢出时与上者**互换** |
| `xPendingReadyList` | 调度器挂起期间被唤醒的任务，恢复后再并入就绪链 |
| `xSuspendedTaskList` | 挂起任务 |
| `xTasksWaitingTermination` | `vTaskDelete()` 后等空闲任务回收内存的任务 |

### 调度原理

1. **优先级调度 + 就绪链表分桶**：优先级 0…`configMAX_PRIORITIES-1` 各一条就绪链，选择最高非空优先级即选任务。
2. **两种找最高优先级算法**：
   - `configUSE_PORT_OPTIMISED_TASK_SELECTION=0`：从 `uxTopReadyPriority` 向下线性找（`tasks.c:175`）。
   - `=1`：用一个 32 位位图记录哪些优先级有就绪任务，配合 ARM 的 `CLZ` 指令一次定位最高位（`tasks.c:224`、`portmacro.h:171`）。M4 上通常开启，代价是 `configMAX_PRIORITIES ≤ 32`。
3. **抢占**：`configUSE_PREEMPTION=1` 时，更高优先级任务一旦就绪，在调度点（tick、队列 Give、`taskYIELD`）立即抢占当前任务。
4. **时间片**：`configUSE_TIME_SLICING=1` 时，同优先级任务在每次 tick 轮转，靠 `listGET_OWNER_OF_NEXT_ENTRY()` 的 `pxIndex` 实现。
5. **切换入口**：内核逻辑只调用 `taskYIELD()→portYIELD()`，即给 NVIC 的 PendSV 置位；真正的寄存器保存/恢复发生在 **PendSV 异常**里，调用 `vTaskSwitchContext()` 选出 `pxCurrentTCB`。详见 [[仓库-FreeRTOS-Kernel-M4移植层解析]]。
6. **延时与唤醒**：`vTaskDelay()` 把任务按「唤醒时刻」插入 `pxDelayedTaskList`；每个 tick 由 `xTaskIncrementTick()`（`tasks.c:4725`）检查 `xNextTaskUnblockTime`，到点把任务搬回就绪链，必要时触发 PendSV。
7. **tick 回绕**：`TickType_t` 是有限位宽，用两条 delayed 链表在回绕时互换，避免比较溢出。

### 任务生命周期核心 API

| API                                          | 作用      | 关键点                                                      |
| -------------------------------------------- | ------- | -------------------------------------------------------- |
| `xTaskCreate()`                              | 动态创建任务  | 内部用 `pvPortMalloc` 分配 TCB + 栈；`tasks.c:1740`             |
| `xTaskCreateStatic()`                        | 静态创建任务  | 由调用者提供栈和 TCB 内存，无堆依赖；`tasks.c:1331`                      |
| `vTaskDelete()`                              | 删除任务    | `NULL` 表示删自己；TCB 内存由空闲任务回收；`tasks.c:2213`                |
| `vTaskDelay()`                               | 相对延时    | 单位 tick，会主动让出 CPU；`tasks.c:2458`                         |
| `vTaskDelayUntil()` / `xTaskDelayUntil()`    | 绝对周期延时  | 消除累积漂移，适合固定周期任务；`tasks.c:2366`                           |
| `vTaskSuspend()` / `vTaskResume()`           | 挂起 / 恢复 | 无限期；`xTaskResumeFromISR()` 可在中断里恢复                       |
| `vTaskPrioritySet()` / `uxTaskPriorityGet()` | 读改优先级   | 改优先级会移动就绪链桶；`tasks.c:2796`                               |
| `vTaskStartScheduler()`                      | 启动调度器   | 创建空闲任务（及定时器任务），初始化 SysTick/PendSV 后跑第一个任务；`tasks.c:3689` |
| `taskYIELD()`                                | 主动让出    | 宏，等价 `portYIELD()`，置 PendSV                              |
| `xTaskGetTickCount()`                        | 读 tick  | 32 位且 `portTICK_TYPE_IS_ATOMIC=1` 时无需临界区                 |
| `xTaskNotifyGive()` / `ulTaskNotifyTake()`   | 任务通知    | 比信号量更轻的直接通知，见 `task.h`                                   |

## 3. queue.c / semphr.h：队列与信号量

### Queue_t 结构

定义见 `queue.c:103`。**队列、信号量、互斥量共用这一个结构**，靠 `ucQueueType` 与 union 区分。

| 字段 | 作用 |
| --- | --- |
| `pcHead` / `pcWriteTo` | 环形存储区起止与写指针 |
| `u.xQueue.pcTail` / `pcReadFrom` | 队列模式下的尾部与读指针 |
| `u.xSemaphore.xMutexHolder` | 互斥量持有者 TCB |
| `u.xSemaphore.uxRecursiveCallCount` | 递归互斥量的递归计数 |
| `xTasksWaitingToSend` | 因**队列满**而阻塞的发送任务（按优先级排序） |
| `xTasksWaitingToReceive` | 因**队列空**而阻塞的接收任务 |
| `uxMessagesWaiting` | 队列=已存条目数；信号量=当前计数 |
| `uxLength` / `uxItemSize` | 容量（条目数）与单条目字节数 |
| `cRxLock` / `cTxLock` | 队列锁，调度器挂起期间延缓 ISR 侧的唤醒处理 |

### 队列 API

| API | 作用 | 关键点 |
| --- | --- | --- |
| `xQueueCreate()` | 动态创建队列 | `xQueueCreate(len, itemSize)`；`queue.c:502` |
| `xQueueCreateStatic()` | 静态创建队列 | 存储区与结构体由调用者提供；`queue.c:376` |
| `xQueueSend()` / `xQueueSendToBack()` | 尾插 | 满时按 `xTicksToWait` 阻塞 |
| `xQueueSendToFront()` | 头插 | 用于「插队」场景 |
| `xQueueOverwrite()` | 覆盖写 | 仅用于长度 1 的队列，永不阻塞 |
| `xQueueReceive()` | 取走并移除 | 空时按 `xTicksToWait` 阻塞；`queue.c:1509` |
| `xQueuePeek()` | 只读不移除 | `queue.c:1884` |
| `xQueueSendFromISR()` | ISR 版发送 | 用 `pxHigherPriorityTaskWoken` 回报是否需切换；`queue.c:1167` |
| `xQueueReceiveFromISR()` | ISR 版接收 | `queue.c:2039` |
| `uxQueueMessagesWaiting()` / `uxQueueSpacesAvailable()` | 查询计数 | 线程上下文 |
| `vQueueDelete()` | 删除队列 | 释放内存 |

### 信号量 / 互斥量 API（宏，底层都是队列）

| 上层 API | 底层实现 | 语义 |
| --- | --- | --- |
| `xSemaphoreCreateBinary()` | `xQueueGenericCreate(1,0,...)` | 二值信号量，初始为空 |
| `xSemaphoreCreateCounting(max, init)` | `xQueueCreateCountingSemaphore` | 计数信号量，初始计数可 >0 |
| `xSemaphoreCreateMutex()` | `xQueueCreateMutex` + `prvInitialiseMutex` | 互斥量，初始可用，带优先级继承 |
| `xSemaphoreCreateRecursiveMutex()` | 同上，类型不同 | 同一任务可重复 Take |
| `xSemaphoreTake()` | `xQueueSemaphoreTake`（`queue.c:1659`） | 获取 / 阻塞等待 |
| `xSemaphoreGive()` | `xQueueGenericSend` | 释放 |
| `xSemaphoreGiveFromISR()` | `xQueueGiveFromISR` | ISR 释放，回报是否需切换 |
| `xSemaphoreGiveRecursive()` / `TakeRecursive()` | 递归计数 | 归零才真正释放 |

### 原理要点

1. **值拷贝语义**：`xQueueSend/Receive` 拷贝整个 `uxItemSize` 字节，而不是传引用。大对象一般传指针。实现见 `prvCopyDataToQueue`（`queue.c:2393`）与 `prvCopyDataFromQueue`（`queue.c:2476`）。
2. **阻塞 / 唤醒机制**：队列空时接收者挂到 `xTasksWaitingToReceive`，满时发送者挂到 `xTasksWaitingToSend`；对端操作后由 `xTaskRemoveFromEventList()` 唤醒优先级最高的等待者。
3. **信号量 = 长度为 1、条目大小为 0 的队列**：`uxMessagesWaiting` 被当作计数用。Give 就是「放入一个 0 字节条目」，Take 就是「取走」。
4. **互斥量特殊之处**（`prvInitialiseMutex`，`queue.c:617`）：
   - 创建时 `uxMessagesWaiting=1`（立即可用）；
   - Take 时记录 `xMutexHolder`；
   - 若更高优先级任务来抢，持有者通过 `vTaskPriorityInherit()` **临时提升优先级**，缓解优先级反转；释放时 `vTaskPriorityDisinherit()` 回退；
   - 只能由持有者释放，ISR 不能 Take/Give 互斥量。
5. **递归互斥量**：用 `uxRecursiveCallCount` 记录同一任务的重复获取次数，计数归零才释放；中断里不可用。
6. **队列锁 `cRxLock/cTxLock`**：调度器挂起期间，ISR 对队列的操作不能直接唤醒任务，先累计锁计数，等 `prvUnlockQueue()`（`queue.c:2497`）统一处理。
7. **`FromISR` 与 `portYIELD_FROM_ISR()`**：ISR 里不能用会阻塞的 API；ISR 版本不阻塞，并通过 `pxHigherPriorityTaskWoken` 告诉调用者在 ISR 结尾是否需要一次上下文切换。

## 4. 通信机制选型对照

| 需求 | 首选机制 | 理由 |
| --- | --- | --- |
| 任务间传数据（含多生产者/消费者） | 队列 | 值拷贝、满/空阻塞、可带超时 |
| 传大块数据 | 队列传指针 / 流缓冲 / 消息缓冲 | 避免整块拷贝 |
| 只需「发个信号」 | 二值信号量 / 任务通知 | 任务通知最省资源 |
| 记录「资源数量」 | 计数信号量 | 计数即资源数 |
| 保护共享资源、防优先级反转 | 互斥量 | 带优先级继承 |
| 同一任务需嵌套获取锁 | 递归互斥量 | 带递归计数 |
| 等多条件组合满足 | 事件组 | 多位标志，可「与」可「或」 |
| ISR 通知任务 | `FromISR` 版本 + `portYIELD_FROM_ISR()` | 不阻塞、可请求切换 |

## 5. 关键代码锚点

| 主题 | 位置 |
| --- | --- |
| TCB 定义 | `tasks.c:374` |
| 就绪链表 / 延时链表 / 挂起链声明 | `tasks.c:475`–`tasks.c:491` |
| 通用版选最高优先级 | `tasks.c:175` |
| 位图 + CLZ 版选最高优先级 | `tasks.c:224`、`portmacro.h:171` |
| 任务创建 | `tasks.c:1331`（Static）、`tasks.c:1740`（Dynamic） |
| 启动调度器 | `tasks.c:3689` |
| 删除任务 | `tasks.c:2213` |
| 延时 | `tasks.c:2366`、`tasks.c:2458` |
| tick 递增与唤醒 | `tasks.c:4725` |
| 事件链插入 / 移除 | `tasks.c:5296`、`tasks.c:5394` |
| 链表 API | `list.c:49`、`list.c:105`、`list.c:139`、`list.c:217` |
| Queue_t 定义 | `queue.c:103` |
| 队列创建 | `queue.c:376`（Static）、`queue.c:502`（Dynamic） |
| 互斥量初始化 | `queue.c:617` |
| 队列发送 / 接收 | `queue.c:949`、`queue.c:1509` |
| ISR 发送 / 接收 | `queue.c:1167`、`queue.c:2039` |
| 数据拷贝实现 | `queue.c:2393`、`queue.c:2476` |

## 疑问清单 / 待深入

- [ ] 精读 `xTaskIncrementTick()` 的 tick 回绕分支，吃透双延时链表的互换时机。
- [ ] 对照 `prvSelectHighestPriorityTask()` 的 SMP 版本与单核宏版本差异。
- [ ] 跟踪一次完整的「ISR Give → 唤醒任务 → PendSV 切换」调用链。
- [ ] 结合 [[仓库-FreeRTOS-Kernel-FreeRTOSConfig配置详解]]，理解各裁剪宏如何影响这里的结构体字段与 API。

## 关联

- [[仓库-FreeRTOS-Kernel]]（仓库地图）
- [[仓库-FreeRTOS-Kernel-M4移植层解析]]
- [[仓库-FreeRTOS-Kernel-FreeRTOSConfig配置详解]]
- [[学习-RTOS-学习路线]]（阶段 1、2）
- [[MOC-RTOS]]
