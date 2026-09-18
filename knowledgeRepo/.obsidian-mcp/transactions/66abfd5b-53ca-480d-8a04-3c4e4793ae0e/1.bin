---
type: resource
tags: [C++, 面试题, 多线程, 并发]
created: 2026-09-18
updated: 2026-09-18
status: active
---

# C++ 面试 — 多线程与并发

> 适用：协议栈 / 后端 / 实时软件 C++ 岗  
> 结构：每题 **口头答案** + **关键点** + **易被追问**  
> 索引：[[C++面试-总览]]

---

## 速记总览

| 题号 | 题目 | 一句话结论 |
|------|------|------------|
| 1 | 线程创建与结束 | `std::thread`，结束前必须 join 或 detach |
| 2 | mutex 与 lock_guard | 互斥保护共享数据；RAII 加解锁 |
| 3 | unique_lock 与条件变量 | 需要中途解锁/配合 wait 时用 unique_lock |
| 4 | 条件变量用法 | wait 防虚假唤醒必须带谓词；先改条件再 notify |
| 5 | atomic | 单操作原子性；不能替代锁保护复合不变式 |
| 6 | 死锁四条件与避免 | 互斥、持有并等待、不可剥夺、循环等待；固定加锁顺序 |
| 7 | 数据竞争 | 无同步地并发读写同一内存=UB；需锁/原子/不可变 |
| 8 | 线程安全容器？ | STL 容器本身不是线程安全的 |
| 9 | 协议栈并发模型 | 分核/分任务、SPSC 队列、避免锁在实时路径 |
| 10 | memory_order | 默认 seq_cst 最安全；acquire/release 用于生产者-消费者旗标 |

---

## 1. C++11 如何创建线程？线程函数要注意什么？

### 口头答案

`#include <thread>`，`std::thread t(func, args...);`。线程函数按值拷贝参数，要传引用用 `std::ref`。析构 `std::thread` 前必须 `join()`（等待结束）或 `detach()`，否则 `std::terminate`。建议用 RAII 线程池或明确 join 作用域。

### 关键点

```cpp
std::thread t([&]{ worker(); });
// ...
t.join();
```

- `std::this_thread::sleep_for` / `get_id`  
- 异常抛出线程函数外未捕获 → 进程终止  
- 优先 `jthread`（C++20）自动 join  

### 易被追问

- lambda 捕获局部后 detach？→ 悬空风险。  
- 线程数怎么定？→ CPU 密集 ≈ 核数；IO 密集可更多；实时系统按核绑定。

---

## 2. 互斥量怎么用？lock_guard 是什么？

### 口头答案

`std::mutex` 保护临界区，`lock()`/`unlock()` 必须成对。现代 C++ 用 `std::lock_guard` 或 `std::scoped_lock`（C++17）RAII 管理：构造加锁、析构解锁，异常安全。多个锁时 `scoped_lock` 一次锁多个，内部避免死锁算法。

### 关键点

```cpp
{
  std::scoped_lock lk(m1, m2);
  // 临界区
}
```

- 不要手动 lock 后复杂逻辑中途 return 忘 unlock  
- 不要在锁内做可能阻塞很久的 IO（协议栈慎用）  
- 递归锁 `recursive_mutex` 仅特殊场景，优先重构  

### 易被追问

- 性能？→ 锁竞争是瓶颈；减少临界区、分段锁、SPSC。  
- 共享读？→ `shared_mutex` 读写锁（C++17）。

---

## 3. unique_lock 和 lock_guard 有何区别？

### 口头答案

`lock_guard` 更轻，作用域内一直持锁。`unique_lock` 更灵活：可延迟加锁、中途 `unlock`/`lock`、转移所有权，是 `condition_variable::wait` 的标配（wait 内部要解锁等待再重新加锁）。

### 关键点

| 类型 | 特点 | 典型用途 |
|------|------|----------|
| lock_guard / scoped_lock | 简单 RAII | 普通临界区 |
| unique_lock | 可移动、可解锁 | 条件变量、复杂控制流 |

### 易被追问

- 偏向性能？→ 无额外需求用 scoped_lock。  
- C++17 shared_lock？→ 配合 `shared_mutex` 做读多写少。

---

## 4. 条件变量的标准用法？虚假唤醒是什么？

### 口头答案

生产者修改共享状态后 `notify_one/all`；消费者：

```cpp
std::unique_lock lk(m);
cv.wait(lk, [&]{ return ready; });  // 谓词防虚假唤醒
// 处理
```

`wait` 可能虚假返回，**必须用谓词循环判断条件**。应在持有锁时修改条件，再通知；避免丢通知。

### 关键点

```text
lock
→ while (!pred) wait(lock)   // wait(lk, pred) 已封装
→ 临界区处理
unlock
```

- `notify_all` vs `notify_one`：多消费者同质用 all，单任务用 one  
- 只保护条件标志，真正数据可按策略移出锁外处理  

### 易被追问

- 丢失唤醒？→ 条件在锁内检查与修改。  
- 超时？→ `wait_for` / `wait_until`。

---

## 5. std::atomic 解决什么问题？不能解决什么？

### 口头答案

保证单个原子操作（读/写/读改写）不可分割，避免数据竞争；适合计数器、标志位、简单共享状态。**不能**自动保证多操作复合逻辑的原子性（check-then-act），也不能给对象任意成员上“事务”。复杂不变式仍要 mutex 或无锁数据结构。

### 关键点

```cpp
std::atomic<int> cnt{0};
cnt.fetch_add(1, std::memory_order_relaxed);
std::atomic<bool> stop{false};
// 等待: while (!stop.load(std::memory_order_acquire)) ...
```

- `atomic` 对象不可拷贝  
- `memory_order` 默认 `seq_cst`，先正确再调序  

### 易被追问

- `atomic` 指针？→ 指针本身原子，所指数据不管。  
- 无锁队列？→ 可讲 MPSC/SPSC 思路；不要假装自己实现了正确 lock-free 而不谈内存序。

---

## 6. 死锁的条件与如何避免？

### 口头答案

四条件同时成立才死锁：互斥、持有并等待、不可剥夺、循环等待。避免：全局固定加锁顺序；`std::scoped_lock`/`std::lock` 同时锁多把；减少锁粒度与嵌套；超时 `try_lock`；用无锁或单线程分核模型。

### 关键点

```text
线程1: lock(A) → 想 lock(B)
线程2: lock(B) → 想 lock(A)
→ 循环等待
```

### 易被追问

- 如何排查？→ 先画锁顺序图；`gdb`/日志打印持锁；ThreadSanitizer。  
- 活锁/饥饿？→ 长时间 `try_lock` 失败、优先级反转；实时系统关注优先级继承（OS 层）。

---

## 7. 什么是数据竞争？如何消灭？

### 口头答案

两个线程并发访问同一内存，至少一个是写，且没有 happens-before 同步，则是数据竞争，**未定义行为**（不仅是“偶发错值”）。消灭方式：mutex；atomic + 正确内存序；分区所有权（每线程独占一片）；消息传递不可变数据。

### 关键点

| 策略 | 例子 |
|------|------|
| 互斥 | 共享 map + mutex |
| 原子 | 统计计数、停止标志 |
| 分核 | 每 worker 自己的队列与缓冲池 |
| 消息 | 线程间传值/传 unique_ptr |

### 易被追问

- 只读共享？→ 初始化后只读安全；写必须同步。  
- TSan？→ 编译 `-fsanitize=thread` 检测。

---

## 8. STL 容器是线程安全的吗？

### 口头答案

**不是。** 标准只要求：不同容器对象可并行；同一容器多线程写、或一写多读（读到的是同一对象且无同步）都可能数据竞争。需要外部 mutex，或每线程私有副本 + 合并，或用专用并发容器。

### 关键点

```text
并发策略：
外部锁保护整个容器
分片锁 / 细粒度锁
SPSC/MPSC 队列
每线程 local + 定期 reduce
```

### 易被追问

- 只遍历加锁够吗？→ 遍历期间任何写都会失效迭代器，必须互斥。  
- `vector` 一边 push 一边读？→ 必须同步，否则 UB + 迭代器失效。

---

## 9. 协议栈/实时系统里并发怎么做更合理？

### 口头答案

结合实时约束：① **任务分区**：按协议层或 UE 流水线分核，减少共享；② 低延迟用 **SPSC 无锁环形队列** 传消息/缓冲；③ 启动时预分配，避免热路径锁内分配；④ 控制面可用 mutex+条件变量，数据面优先无阻塞；⑤ 绑定 CPU、注意 false sharing、日志异步化。

### 关键点

```text
控制面：清晰锁 + 状态机
数据面：分核流水线 + SPSC/批量
共享统计：atomic 或 per-core 再汇总
缓冲：池化 + 对齐 + 所有权随消息移动
```

srsRAN 等实现常见 worker 线程池与高层接口线程分离。

### 易被追问

- 锁在实时路径？→ 抖动与优先级反转；尽量无锁或短临界区。  
- 跨线程释放缓冲？→ 池回收或消息携带所有权，避免跨线程 delete 竞态。

---

## 10. memory_order 了解多少？实际怎么选？

### 口头答案

编译器/CPU 可重排指令；原子操作带内存序约束线程间可见性。默认 `seq_cst` 全局顺序最强最安全。`acquire`/`release` 配对：写 release、读 acquire，保证释放前的写对后续读可见（发布-获取）。`relaxed` 只要原子性，无跨变量顺序，仅适合独立计数。

### 关键点

```text
生产者: data = ...; flag.store(true, release);
消费者: if (flag.load(acquire)) { 使用 data; }
```

业务代码：**先用默认 seq_cst**；性能分析后再用 acq/rel；不要随意 relaxed。

### 易被追问

- 错误用 relaxed 会怎样？→ 可能看到 flag=true 但 data 未写完。  
- 与 mutex？→ mutex 解锁/加锁自带 release/acquire 效果。

---

## 面试答法示例

> 我区分控制面和数据面：控制面用 mutex + condition_variable 和 RAII 锁；数据面尽量按 UE/流水线分核，用 SPSC 队列传缓冲所有权，避免在实时路径上做复杂加锁和堆分配。共享统计用 atomic，复合不变式仍用锁。排查数据竞争用 TSan，并固定加锁顺序避免死锁。

---

## 相关

- [[C++面试-总览]]
- [[C++面试-内存管理与智能指针]]
- [[C++面试-STL与模板]]
- [[MOC-C++与软件]]
- [[MOC-RTOS]]
