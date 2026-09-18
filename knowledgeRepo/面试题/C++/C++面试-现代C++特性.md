---
type: resource
tags: [C++, 面试题, 现代C++]
created: 2026-09-18
updated: 2026-09-18
status: active
---

# C++ 面试 — 现代 C++ 特性

> 适用：C++11/14/17/20 岗位，尤其 srsRAN 等 C++17 协议栈  
> 结构：每题 **口头答案** + **关键点** + **易被追问**  
> 索引：[[C++面试-总览]]

---

## 速记总览

| 题号 | 题目 | 一句话结论 |
|------|------|------------|
| 1 | 左值与右值 | 左值有身份可寻址；右值多是临时的、可被移动 |
| 2 | 移动语义 | 转移资源所有权，避免深拷贝；移动后源对象可析构 |
| 3 | std::move 与转发 | move 是无条件右值转型；完美转发保左右值属性 |
| 4 | auto / decltype | auto 丢引用与顶层 const（需 auto&）；decltype 按表达式推导 |
| 5 | lambda | 可调用对象，捕获列表决定环境；可转 std::function 或模板参数 |
| 6 | nullptr vs 0/NULL | 类型安全空指针，避免重载决议歧义 |
| 7 | constexpr / consteval | 编译期求值能力，常量传播与配置表 |
| 8 | enum class | 强类型枚举，不隐式转 int，作用域隔离 |
| 9 | C++17 实用特性 | structured bindings、if constexpr、optional/string_view 等 |
| 10 | 右值引用成员函数 | ref-qualifier，区分对象是左值还是临时量 |

---

## 1. 左值和右值有什么区别？

### 口头答案

能取地址、有名字的通常是左值（具名变量、解引用等）；右值多是临时对象、字面量，表达式结束后消亡，适合被移动。右值引用 `T&&`（C++11）用于绑定右值，是移动构造/移动赋值的基础。注意：`std::move(x)` 后 `x` 仍是左值，只是被当作右值来源。

### 关键点

| 类别 | 例子 | 可否被 move |
|------|------|-------------|
| 左值 | `int a; foo(a);` | 需显式 move |
| 纯右值 | `foo(42)`、`T()` | 可直接绑定 `T&&` |
| 将亡值 | `std::move(a)` 结果 | 是移动语义主要来源 |

### 易被追问

- 移动后还能用吗？→ 可析构、可赋值，内容未指明（常见“空”）。  
- 函数返回局部对象？→ RVO/移动，通常不额外拷贝。

---

## 2. 什么是移动语义？解决什么问题？

### 口头答案

移动语义允许把资源（堆内存、缓冲区）的**所有权/内部指针**从一个对象“搬”到另一个，避免深拷贝。表现为移动构造函数与移动赋值运算符，参数是 `T&&`。容器扩容、函数返回大 `vector`、协议消息从队列取出时都能受益。

### 关键点

```cpp
Buffer(Buffer&& other) noexcept
  : data_(other.data_), size_(other.size_) {
  other.data_ = nullptr;
  other.size_ = 0;
}
```

- 应 `noexcept`，利于容器扩容走移动而非拷贝  
- 移动后源对象保持有效可析构状态  
- 资源类：Rule of Five 或只移  

### 易被追问

- 何时该写移动？→ 类管理堆/大缓冲时。  
- 何时移动不划算？→ 小对象（几个 int）拷贝更快。  
- 协议栈 PDU？→ 大块 buffer 移动进队列，避免复制载荷。

---

## 3. std::move 和完美转发有什么区别？

### 口头答案

`std::move(x)` 无条件把 `x` 转型为右值引用，表示“可以偷资源”，不做移动本身。完美转发用于模板：`std::forward<T>(x)` 按 `T` 推导结果保留实参是左值还是右值，常用于包装函数/工厂/`emplace` 参数。

### 关键点

```cpp
template <class T>
void wrapper(T&& arg) {
  target(std::forward<T>(arg));  // 保真转发
}
```

`T&&` + 模板推导 = **万能引用**（转发引用）；成员函数的 `T&&` 只是右值引用，不是万能引用。

### 易被追问

- move 后原变量？→ 仍可析构/再赋值，值通常被掏空。  
- `forward` 一定要 `static_cast` 语义？→ 是 `static_cast` 到 `T&&`，带推导信息。  
- 为何 emplace 优于 push？→ 原地构造，少一次临时对象+移动。

---

## 4. auto 和 decltype 怎么用？易错点？

### 口头答案

`auto` 按初始化表达式推导类型，省冗长模板代码，但会**去掉引用和顶层 const**，需要保留时写 `auto&` / `const auto&`。`decltype(expr)` 按表达式**精确**推导，包括引用属性，适合泛型返回类型（C++14 还可 `decltype(auto)`）。

### 关键点

```cpp
std::vector<int> v;
for (const auto& x : v) { /* 避免拷贝 */ }
auto  a = v[0];   // int
auto& b = v[0];   // int&
decltype(v[0]) c = v[0];  // int&（表达式是左值）
```

### 易被追问

- `auto` 收窄？→ 列表初始化可能拒绝收窄。  
- 可读性？→ 类型不明显时手写更清晰；循环与复杂迭代器别名用 auto 更好。

---

## 5. lambda 表达式由哪些部分组成？捕获有哪些方式？

### 口头答案

形式：`[捕获](参数) -> 返回类型 { 函数体 }`。捕获可按值 `[x]`、按引用 `[&x]`、this、`=`/`&` 全捕获，以及 C++14 初始化捕获 `[p = std::move(up)]`。常用在算法谓词、异步回调、局部小函数。注意：引用捕获悬空、mutable、与 std::function 开销。

### 关键点

```cpp
auto add = [](int a, int b) { return a + b; };
int n = 10;
auto f = [n](int x) { return x + n; };      // 按值
auto g = [&n](int x) { return x + n; };     // 按引用
```

- 无捕获 lambda 可转函数指针  
- 有捕获用 `std::function` 或模板转发可调用，注意 type erasure 分配  
- 热路径可用模板参数接受任意 callable，零开销  

### 易被追问

- 按引用捕获局部后异步执行？→ 悬空，UB；应按值或 shared_ptr。  
- `[=]` 捕获 this？→ 拷贝的是 this 指针，对象仍需存活。

---

## 6. 为什么要用 nullptr 而不是 0 / NULL？

### 口头答案

`0`/`NULL` 在重载场景会当整型，导致调用错误的重载；`nullptr` 是 `std::nullptr_t`，类型安全，语义就是空指针。现代代码一律用 `nullptr`。

### 关键点

```cpp
void f(int);
void f(char*);
f(NULL);     // 危险：常被解析为 f(int)
f(nullptr);  // OK
```

### 易被追问

- `bool` 转换？→ `nullptr` 可转 false，符合习惯。  
- 与 C 接口？→ 仍传 `nullptr`，ABI 兼容空指针。

---

## 7. constexpr 与 const 的区别？

### 口头答案

`const` 表示运行期不可改；`constexpr` 要求编译期可求值，可用于数组大小、模板参数、编译期查表。函数标 `constexpr` 则参数合适时可在编译期执行，否则也能在运行期调用（C++11 起逐步放松）。C++20 `consteval` 强制编译期。

### 关键点

| 关键字 | 侧重点 |
|--------|--------|
| const | 不可修改 |
| constexpr | 尽量/必须编译期求值 |
| consteval | 必须编译期 |
| constinit | 动态初始化前先常量初始化（C++20） |

协议栈：采样率、FFT 长度、查表初值、状态机转移表可 constexpr。

### 易被追问

- constexpr 函数能有循环？→ C++14 起可以。  
- 与宏？→ 优先 constexpr，类型安全可调试。

---

## 8. 为什么要用 enum class？

### 口头答案

普通 `enum` 会把枚举子泄漏到外层作用域，且能隐式转整型，易与整数接口混淆。`enum class` 强类型、作用域限定，必须显式转换，协议消息类型、状态机状态用它更安全清晰。

### 关键点

```cpp
enum class State { Idle, Active };
// State::Idle 必须带作用域
// int x = State::Idle; // 错误
```

可指定底层类型：`enum class Msg : uint8_t`，便于序列化。

### 易被追问

- 位标志？→ 需手写或用 bit flag 辅助；不能隐式或运算除非重载。  
- 与 C 枚举对接？→ `static_cast` 到底层类型。

---

## 9. C++17 有哪些常用特性？（结合 srsRAN）

### 口头答案

工程上常用：**结构化绑定**（`auto [key, val]`）、**if constexpr**（按分支实例化模板）、**std::optional**（可能失败/无值返回）、**string_view**（只读视图避免拷贝）、**std::filesystem**、并行算法、`std::variant`/`any`、内联变量。srsRAN Project 以 C++17 为主，optional 与 string_view 在配置与消息接口上很常见。

### 关键点

```cpp
if constexpr (sizeof(T) == 4) { /* SIMD/标量分支 */ }
std::optional<Grant> g = try_allocate();
auto [it, ok] = map.emplace(key, value);
```

- `string_view` 不拥有内存，注意生命周期  
- `optional` 不要当异常替代滥用；表达“可能没有”  

### 易被追问

- C++20 亮点？→ concepts、ranges、coroutine、`std::span`、`<=>`。  
- 协议栈更想用 span？→ 视图表达缓冲区，避免裸指针+长度散落。

---

## 10. 什么是引用限定成员函数？

### 口头答案

可在成员函数后加 `&` / `&&`，限制只对左值或右值对象调用。典型：移动后 `return *this` 的链式接口，或 `get() &&` 返回内部资源给临时对象。可避免对临时对象误用接口。

### 关键点

```cpp
std::vector<int> data() && { return std::move(data_); }
std::vector<int> data() const& { return data_; }
```

### 易被追问

- 重载同时有 & 与 &&？→ 按对象值类别选择。  
- 何时写？→ 库作者；业务代码了解概念即可。

---

## 面试答法示例

> 移动语义减少大缓冲拷贝，std::move 只是转型，真正搬资源靠移动构造。模板包装用 forward 完美转发。我们项目用 C++17：optional 表示可失败分配，string_view/视图读配置，if constexpr 做类型/位宽分支，热路径对象尽量 noexcept 移动。

---

## 相关

- [[C++面试-总览]]
- [[C++面试-内存管理与智能指针]]
- [[C++面试-STL与模板]]
- [[MOC-C++与软件]]
