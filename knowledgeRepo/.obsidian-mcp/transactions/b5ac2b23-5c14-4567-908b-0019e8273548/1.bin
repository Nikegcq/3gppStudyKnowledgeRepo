---
type: resource
tags: [C++, 面试题, STL, 模板]
created: 2026-09-18
updated: 2026-09-18
status: active
---

# C++ 面试 — STL 与模板

> 适用：通用 C++ + 协议栈（消息、容器、策略模板化）  
> 结构：每题 **口头答案** + **关键点** + **易被追问**  
> 索引：[[C++面试-总览]]

---

## 速记总览

| 题号 | 题目 | 一句话结论 |
|------|------|------------|
| 1 | vector/list/deque | 连续内存随机访问；list 节点任意增删；deque 两端效率高 |
| 2 | vector 扩容机制 | 空间不足时重新分配并搬移，容量可 > size |
| 3 | map vs unordered_map | 有序 O(log n) vs 哈希平均 O(1) |
| 4 | 迭代器失效 | 删除/扩容后旧迭代器不可再用，规则因容器而异 |
| 5 | 拷贝与移动进容器 | `push_back` 拷/移；`emplace` 原地构造 |
| 6 | 模板是什么 | 编译期代码生成；具现化、特化、偏特化 |
| 7 | 函数模板与模板函数 | 泛型接口 vs 具体实例化函数 |
| 8 | std::function 与函数对象 | 类型擦除有开销；模板 callable 零开销 |
| 9 | span/string_view | 非拥有视图，避免拷贝，注意生命周期 |
| 10 | 算法复杂度习惯 | 大 O + 实测；缓存局部性常比理论复杂度更关键 |

---

## 1. vector、list、deque 如何选型？

### 口头答案

`vector`：连续内存，随机访问 O(1)，尾部均摊 O(1)，cache 友好，**默认首选**。`list`：双向链表，任意位置增删 O(1)（已有迭代器），但无随机访问、额外指针、cache 差。`deque`：分块连续，两端 push/pop 效率好，随机访问仍可但比 vector 常数大。协议栈消息、配置数组优先 vector；稳定节点指针且频繁中部删除才考虑 list（或改为索引）。

### 关键点

| 容器 | 访问 | 头尾 | 中部插入删除 | 内存 |
|------|------|------|--------------|------|
| vector | O(1) | 尾 O(1) 均摊 | O(n) | 紧凑 |
| list | O(n) | O(1) | O(1) | 每节点开销大 |
| deque | O(1) | 两端 O(1) | O(n) | 分块 |

### 易被追问

- 为何少用 list？→ 指针追踪差、分配碎片；现代硬件上 vector 常更快。  
- map 节点指针稳定？→ `std::map`/`list` 迭代器在非删除时稳定；vector 扩容不稳定。

---

## 2. vector 的扩容机制？capacity 与 size？

### 口头答案

`size()` 是元素个数，`capacity()` 是已分配可容纳个数。`push_back` 在 size==capacity 时扩容：新分配更大缓冲（常见 2 倍，实现相关），**移动/拷贝**旧元素，释放旧缓冲，因此迭代器/指针/引用失效。可用 `reserve` 预留减少重分配。

### 关键点

```cpp
v.reserve(n);           // 预留
v.shrink_to_fit();      // 请缩小（非强制）
```

- 扩容复杂度均摊 O(1)，单次最坏 O(n)  
- 移动元素若 noexcept 更可靠走移动  
- `resize` 改 size，可能改 capacity  

### 易被追问

- 扩容因子？→ 实现定义，libstdc++ 多为 2 倍。  
- 如何保迭代器？→ `reserve` 足够；或 `list`/`deque`；或存索引。

---

## 3. map 与 unordered_map 区别？怎么选？

### 口头答案

`map` 是红黑树，有序，操作 O(log n)，键需弱序比较。`unordered_map` 哈希表，平均 O(1)，无序，需哈希与相等。要排序遍历、范围查询用 map；只求查找快、键可哈希用 unordered_map。注意最坏哈希退化与 rehash 抖动。

### 关键点

| | map | unordered_map |
|--|-----|---------------|
| 结构 | 树 | 哈希桶 |
| 有序 | 是 | 否 |
| 查找 | O(log n) | 平均 O(1) 最坏 O(n) |
| 键要求 | 严格弱序 | Hash + == |
| 迭代器 | 稳定（除删除） | rehash 后失效 |

### 易被追问

- UE_id 小整数？→ 小范围可用 `vector` 当 map，O(1) 更快。  
- 热路径避免 unordered_map？→ 预分配、开放寻址自定义表、避免 rehash。

---

## 4. 什么是迭代器失效？常见规则？

### 口头答案

迭代器/引用/指针在容器结构变更后不能再安全使用。典型：`vector` 插入可能全失效（扩容）；删除点及其后失效。`map/unordered_map` 删除仅被删节点失效；`unordered_map` rehash 使迭代器失效（引用视实现/标准细节，业务上 rehash 后勿旧迭代器遍历）。删除元素用 `it = vec.erase(it)` 模式。

### 关键点

```cpp
for (auto it = v.begin(); it != v.end(); ) {
  if (pred(*it)) it = v.erase(it);
  else ++it;
}
```

- C++11 `vector::erase` 返回下一迭代器  
- 边遍历边 push 要小心扩容失效  

### 易被追问

- 为何现场常崩？→ use-after-free 式访问已失效迭代器。  
- 如何降风险？→ 索引+版本、值拷贝待删表、选稳定容器。

---

## 5. push_back、emplace_back 怎么选？

### 口头答案

`push_back(obj)` 拷贝/移动；`push_back(T(...))` 先临时再移。`emplace_back(args...)` 在容器内直接构造，少一次中间对象。大对象或构造昂贵时 emplace 更优。语义要表达“已有一个对象拷/移进去”时用 push_back 更清晰。

### 关键点

```cpp
v.emplace_back(1, 2, 3);   // 直接 T(1,2,3)
v.push_back(std::move(t)); // 已有对象移动
```

- `reserve` + emplace 减少重分配与拷贝  
- 异常安全依赖元素移动/拷贝行为  

### 易被追问

- emplace 一定更快？→ 简单 `int` 差异可忽略。  
- 返回值？→ C++17 `emplace_back` 返回引用。

---

## 6. C++ 模板是做什么的？实例化发生在何时？

### 口头答案

模板是编译期泛型工具：用类型/非类型参数生成代码，调用时**实例化**出具体函数或类。好处是零开销抽象、可内联；代价是编译时间、错误信息长、代码膨胀。策略模式、缓冲区实现、协议编解码常用模板参数化类型/位宽。

### 关键点

```cpp
template <class T>
T max3(T a, T b) { return a > b ? a : b; }

// 实例化: max3<int>, max3<double>
```

- 类型参数：`template<class T>`  
- 非类型：`template<size_t N>`，编译期常量  
- 头文件定义：一般定义放在 h/hpp  

### 易被追问

- 与虚函数？→ 模板编译期绑定，虚函数运行期多态。  
- 代码膨胀？→ 显式实例化、公共非模板实现抽取。

---

## 7. 全特化与偏特化是什么？

### 口头答案

全特化：为某一具体类型提供专门实现 `template<> class Vec<bool>`。偏特化（类模板）：对某类参数模式仍留参数 `template<class T> class X<T*>`。函数模板主要靠重载/全特化（偏特化规则不同）。协议里对 `uint8_t`/`float` 等特殊路径很常见。

### 关键点

```cpp
template <class T> struct Codec { static void write(T); };
template <> struct Codec<bool> { /* 全特化 */ };
template <class T> struct Codec<T*> { /* 偏特化指针 */ };
```

### 易被追问

- 何时选重载何时特化？→ 函数优先重载；类按类型族特化。  
- 概念/concepts？→ C++20 约束模板，替代部分 enable_if 黑魔法。

---

## 8. std::function 和直接模板传入函数对象有何差别？

### 口头答案

`std::function` 做类型擦除，可存储任意可调用，接口统一，可能堆分配、虚调用，有运行期开销。模板参数接受 callable 在实例化时展开，可内联、零开销，但每个不同 lambda 类型都是新类型。热路径用模板；需要运行期配置/回调注册用 `std::function`。

### 关键点

```cpp
template <class F>
void run(F&& f) { f(); }              // 零开销

std::function<void()> cb = []{};      // 类型擦除，灵活
```

### 易被追问

- 小 lambda 优化？→ 部分实现 SBO，仍可能有间接开销。  
- 信号槽框架？→ 多用 type erasure；性能敏感处改直接调用。

---

## 9. std::span / string_view 解决什么问题？风险？

### 口头答案

它们是**非拥有**的连续内存视图：`span<T>` 指针+长度（C++20），`string_view` 适合只读字符串（C++17）。API 传“一段缓冲”不必拷贝也不必裸 `data/size` 双参。风险：不延长底层生命周期，悬空使用是 UB；修改权限与所有权要靠约定。

### 关键点

```cpp
void crc(std::span<const uint8_t> pkt);
crc(std::span(buf));  // 或 C++20 span 构造
```

- 协议 PDU、解析器接口很适合  
- 不要从临时 `vector` 返回 span  
- C++23 更有 `mdspan` 等；项目以 17 为主时可用自研 view  

### 易被追问

- 与 vector 关系？→ vector 是拥有者，span 是窗口。  
- 能否可写 span？→ `span<T>` 可写，`span<const T>` 只读。

---

## 10. 如何评估容器/算法性能？

### 口头答案

先分析操作频率与数据规模，给复杂度模型；再看**常数与局部性**：连续内存遍历常打败理论更优但节点分散的结构。用 benchmark（项目测试、perf）验证；关注分配次数、cache miss、锁。协议栈还看最坏延迟而不仅是吞吐。

### 关键点

```text
理论：O(n)/O(log n)/O(1)
实际：cache line、分支预测、分配器、锁竞争
实时：最坏耗时、抖动、优先级
```

### 易被追问

- 1e6 次查找？→ 小键整数 vector/数组常优于 unordered_map。  
- 如何测？→ 固定数据集、关闭无关日志、多次统计 p50/p99。

---

## 面试答法示例

> 容器默认 vector，预留容量；需要有序再 map，小整数键直接数组。删除用 erase 返回值，避免迭代器失效。泛型算法用模板热路径零开销，注册回调才用 std::function。PDU 接口用 string_view/span 传只读缓冲，所有权留在缓冲池，用完归还。

---

## 相关

- [[C++面试-总览]]
- [[C++面试-现代C++特性]]
- [[C++面试-内存管理与智能指针]]
- [[C++面试-多线程与并发]]
- [[MOC-C++与软件]]
