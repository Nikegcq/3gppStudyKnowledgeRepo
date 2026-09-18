---
type: resource
tags: [C++, 面试题, static, 语言基础]
created: 2026-09-18
updated: 2026-09-18
status: active
---

# C++ static 关键字详解

> 适用：C++ 面试 + 协议栈/嵌入式工程  
> 结构：分场景语义 → 硬结论 → 代码对照 → 易被追问  
> 索引：[[C++面试-总览]]、[[C++面试-语言基础与面向对象]]

---

## 速记总览

| 场景 | static 的含义 | 一句话 |
|------|---------------|--------|
| 函数内局部变量 | 静态存储期 | 作用域还在函数内，寿命跟程序一样长 |
| 文件作用域变量/函数 | 内部链接 | 只对本翻译单元可见，不进全局符号表 |
| 类内静态数据成员 | 类共享数据 | 一份拷贝，所有对象共用，无 `this` |
| 类内静态成员函数 | 类作用域函数 | 不依赖对象，可 `类名::func()` 调用 |
| 与 const/constexpr 连用 | 常量 + 静态 | 类内编译期常量或共享只读配置 |

**硬结论三条：**  
1. 局部 `static` 管的是**存储期**（活多久），不是“全局变量”。  
2. 文件作用域 `static` 管的是**链接属性**（谁能看到），现代 C++ 更推荐匿名命名空间。  
3. 类 `static` 成员**属于类**，不随对象创建/销毁；静态函数**没有 this**。

---

## 1. 函数内的静态局部变量

### 口头答案

写在函数体内的 `static` 变量：第一次执行到该行时初始化，之后即使函数返回，对象仍然存在，再次进入时沿用旧值。它的**作用域**仍在函数内，**存储期**却是静态的。C++11 起局部静态初始化是线程安全的（编译器插入 guard）。

### 关键点

```cpp
void log_hit() {
  static int hits = 0;  // 只初始化一次
  ++hits;
  // hits 在多次调用间保持
}
```

| 维度 | 普通局部 | static 局部 |
|------|----------|-------------|
| 存储 | 栈 | 静态区（数据/BSS 或 guard 延迟） |
| 初始化 | 每次进入 | 首次执行到时一次 |
| 生命期 | 作用域结束 | 程序结束 |
| 作用域 | 函数内 | 函数内 |
| 线程 | 每线程栈一份 | 多线程共享一份（需自同步） |

**适用：** 调用计数、懒初始化缓存、只建一次的查找表、局部单例。  
**慎用：** 可测试性变差（跨调用隐藏状态）；多线程写仍要锁；析构顺序在退出时不确定。

### 易被追问

- 和全局变量区别？→ 全局无函数作用域保护；static 局部封装更好，且可延迟初始化。  
- 线程安全吗？→ **初始化**是线程安全的；之后的**读写**不是。  
- 协议栈里能用吗？→ 启动阶段建表可以；实时热路径上的全局可变 static 易成隐蔽共享状态。

---

## 2. 文件作用域：static 变量与 static 函数

### 口头答案

在 `.cpp` 顶层、类外写 `static int n;` 或 `static void f()`，表示**内部链接（internal linkage）**：只在当前翻译单元可见，其它 `.cpp` 用 `extern` 也链不到。用于隐藏模块私有符号，避免命名冲突和误用。

### 关键点

```cpp
// file_a.cpp
static int g_counter = 0;   // 仅 file_a.cpp 可见
static void helper() {}     // 仅 file_a.cpp 可见

// 现代替代
namespace {
  int g_counter = 0;  // 匿名命名空间：同样内部链接
  void helper() {}
}
```

| 写法 | 链接 | 备注 |
|------|------|------|
| `int n;`（全局） | 外部链接 | 其它 TU 可 `extern int n` |
| `static int n;` | 内部链接 | 旧式隐藏 |
| 匿名命名空间 `int n;` | 内部链接 | 现代首选 |
| `static void f();` | 内部链接 | 等价匿名命名空间函数 |

### 易被追问

- 头文件里写 `static` 变量？→ 每个包含该头的 `.cpp` 各有一份，易重复、易误以为是“一份全局”。应 `extern` + 单一定义，或 C++17 `inline` 变量。  
- `static` 全局对象构造顺序？→ 同 TU 内按定义序；**跨 TU 顺序未定义**（static initialization order fiasco）。  
- 驱动/库边界？→ 对外 API 用非 static；实现细节用匿名命名空间。

---

## 3. 类的静态数据成员

### 口头答案

`static` 数据成员属于**类**，不属于某个对象：无论生成多少实例，只有一份；不随对象构造/析构。适合：所有实例共享的配置、计数、工厂注册表。访问写 `Class::member` 或经实例访问（仍是一份）。

### 关键点

```cpp
class MacCell {
 public:
  static int cell_count;           // 声明
  static inline int live_ue = 0;   // C++17：类内直接定义
  static constexpr int max_harq = 8; // 编译期常量
};

// C++14 及以前：类外定义（.cpp）
int MacCell::cell_count = 0;
```

| 特性 | 说明 |
|------|------|
| 所有权 | 类共享一份 |
| 生命期 | 程序运行期（加载即存在，或 inline） |
| 初始化 | 优先常量初始化/inline；动态初始化顺序跨 TU 要小心 |
| 与 const | `static const`/`constexpr` 常用；非 const static 可变共享 |
| 模板类 | 每个实例化类型各一份 static 成员 |

### 易被追问

- 为什么不能类内写 `static int x = 0;`（C++17 前）？→ 非 const 静态数据成员只声明不定义；C++17 用 `inline static` 解决。  
- `sizeof` 含 static 吗？→ **不含**；static 不在对象布局里。  
- 单例？→ Meyer’s singleton：函数内 `static` 局部对象 + 返回引用。

---

## 4. 类的静态成员函数

### 口头答案

静态成员函数是**类作用域下的普通函数**：没有 `this`，不能直接访问非静态成员，也不能是 `virtual`（没有对象动态类型可查）。可直接 `Class::func()` 调用；仍是类成员，可访问 `private static` 成员。

### 关键点

```cpp
class BufferPool {
 public:
  static BufferPool& instance() {   // 经典单例入口
    static BufferPool pool;
    return pool;
  }
  static int allocated() { return n_alloc_; }
 private:
  static int n_alloc_;
  BufferPool() = default;
};
```

| 能力 | static 成员函数 | 非 static 成员函数 |
|------|-----------------|---------------------|
| this | 无 | 有 |
| 访问非 static 成员 | 否 | 是 |
| 访问 static 成员 | 是 | 是 |
| 虚函数 | 否 | 可以 |
| 调用方式 | `C::f()` / `obj.f()` | 一般经对象/指针 |

### 易被追问

- 和普通自由函数区别？→ 在类作用域内、可访问私有 static、受访问控制、是类接口的一部分。  
- 回调函数指针？→ 无捕获 lambda 或 static 成员可转 C 风格函数指针（`void(*)(void*)` 场景常配合用户数据指针）。  
- 单例线程安全？→ C++11 局部 static 初始化线程安全；双检锁旧写法不必再用。

---

## 5. static 与 const / constexpr

### 口头答案

- `const`：不可修改（承诺）  
- `static`：存储期/链接/类共享（归属与可见性）  
- `constexpr`：尽量编译期求值  

组合常见：

| 写法 | 含义 |
|------|------|
| `static const int n = 10;` | 静态常量；类内整型常量可类内初始化（C++17 前） |
| `static constexpr int n = 10;` | 编译期常量，推荐 |
| `const static` | 与 `static const` 同义（修饰顺序不影响语义） |
| `mutable static` | 无意义（static 成员与对象 const 无关） |
| `static` 成员函数 + `const`？ | 不能写 `static const` 成员函数；const 修饰的是 this |

协议场景：FFT 长度、带宽、最大 HARQ 进程数等用 `static constexpr`。

### 易被追问

- `const` 成员函数里的 static 局部？→ 仍可改（static 不属对象）；但破坏逻辑 const，要慎用。  
- `thread_local static`？→ C++11，每线程一份静态存储，适合线程本地缓存。

---

## 6. 三个概念别混：存储期 · 链接 · 作用域

### 口头答案

面试官爱考“static 到底管什么”。分层记：

```text
作用域 Scope      → 名字在哪里可见（块/类/文件）
存储期 Storage    → 对象活多久（自动/静态/线程/动态）
链接 Linkage      → 跨翻译单元如何解析符号（内部/外部/无）
```

| 位置 | 主要效果 |
|------|----------|
| 函数内 `static` 变量 | 静态存储期 + 块作用域 |
| 文件内 `static` 变量/函数 | 内部链接 + 文件作用域 |
| 类 `static` 数据成员 | 类作用域 + 静态存储期 + 一份共享 |
| 类 `static` 成员函数 | 类作用域函数 + 无 this |

### 易被追问

- `extern` 和 `static`？→ 外部链接 vs 内部链接，相对概念。  
- 寄存器/局部普通变量？→ 自动存储期，函数退出即结束。

---

## 7. 线程与初始化（工程要点）

### 口头答案

C++11 规定：局部静态变量的**动态初始化线程安全**——并发首次进入时只有一个线程初始化，其余等待。但初始化后的普通读写仍可能数据竞争。跨翻译单元的全局/静态对象初始化顺序未定义，库作者要用函数内 static、`constinit`（C++20）或显式 init 函数。

### 关键点

```text
安全：首次 lazy init（magic statics）
不安全：多线程 ++static int；无同步的 static 容器写
实时：避免在关键路径上首次触发复杂 static 构造
```

### 易被追问

- 为何嵌入式讨厌静态构造？→ 启动顺序、无堆环境、确定性要求；倾向显式 `init()`。  
- `thread_local` 用途？→ 每核统计、TLS 缓存、避免 false sharing（配合对齐）。

---

## 8. 与协议栈/项目相关的用法示例

```cpp
// 编译期配置
class OduConfig {
 public:
  static constexpr size_t nof_slots_ahead = 2;
  static constexpr int    max_ue          = 128;
};

// 模块私有状态（.cpp 内）
namespace {
  std::atomic<uint64_t> slot_counter{0};
}

// 懒初始化表（注意线程写）
const Lut& pss_lut() {
  static const Lut table = build_lut();  // 构造一次
  return table;
}

// 工厂/单例式入口
SrsranLog& log() {
  static SrsranLog instance;
  return instance;
}
```

工程取舍：

| 场景 | 建议 |
|------|------|
| 编译期常量 | `static constexpr` |
| .cpp 内符号 | 匿名命名空间（少用文件 static 变量） |
| 只读懒表 | 函数内 `static const` + 返回引用 |
| 可变共享状态 | 尽量改为显式成员 + 依赖注入；再考虑 static |
| 每线程数据 | `thread_local` 或 per-core 结构 |
| 硬件/驱动注册 | 类 static 或显式 register 函数 |

---

## 9. 面试高频追问清单

1. **局部 static 和全局变量差在哪？** → 作用域封装 + 可延迟初始化 + 可避免符号污染。  
2. **类 static 成员在对象里吗？** → 不在；`sizeof` 不含；对象拷贝不复制它。  
3. **static 函数能是虚函数吗？** → 不能，无 this、无动态绑定基础。  
4. **C++17 `inline static` 解决什么？** → 头文件里直接定义类静态成员，避免类外 .cpp 定义。  
5. **文件 static vs 匿名命名空间？** → 语义同为内部链接；匿名空间对类型更友好，现代代码优先。  
6. **多线程下 static 局部安全吗？** → 初始化安全；使用仍可能要锁/原子。  
7. **构造顺序崩溃？** → 跨 TU static 初始化顺序未定义，改函数内 static 或显式初始化。

---

## 面试答法示例（30 秒）

> C++ 里 static 要分场景看：函数内是静态存储期，首次初始化后跨调用保持，C++11 初始化线程安全；文件作用域是内部链接，只在本编译单元可见，现在更推荐匿名命名空间；类内 static 数据成员和成员函数属于类，不属于对象，静态函数没有 this，不能虚函数。我们项目里编译期常量用 static constexpr，模块私有符号放匿名命名空间，只读查找表用函数内 static const 懒初始化。

---

## 相关

- [[C++面试-总览]]
- [[C++面试-语言基础与面向对象]]
- [[C++面试-内存管理与智能指针]]
- [[C++面试-多线程与并发]]
- [[MOC-C++与软件]]
