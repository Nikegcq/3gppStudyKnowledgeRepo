---
type: resource
tags: [C++, 面试题, vptr, vtable, 虚函数, 多态]
created: 2026-09-18
updated: 2026-09-18
status: active
---

# C++ vptr 与 vtable 详解

> 适用：面试追问「虚函数表怎么组织、对象里有什么」  
> 前置：[[C++面试-虚函数实现举例详解]]（现象与最小代码）  
> 索引：[[C++面试-总览]]、[[C++面试-语言基础与面向对象]]

---

## 速记总览

| 概念 | 是什么 | 份数 | 位置 |
|------|--------|------|------|
| **vptr** | 对象内隐藏指针，指向该对象动态类型对应的 vtable | 每对象 1 个（多继承可能多个） | 对象布局内，常为首成员 |
| **vtable** | 该类的虚函数指针表（还可含 typeinfo、offset 等） | 每（多态）类 1 张 | 静态只读区（`.rodata` 等） |
| **虚调用** | `obj->vf()` → 读 vptr → 表中槽位 → 间接 call | — | 运行期 |

**硬结论：**  
1. vptr 跟**对象**走，vtable 跟**类**走。  
2. 覆盖（override）不改基类 vtable，而是派生类拥有**自己的 vtable**，槽位换成派生函数地址。  
3. 构造/析构过程中 vptr 会切换，因此不能在基类构造里调用「最终派生版」虚函数。

---

## 1. 名词拆开看

### vptr（virtual pointer）

- 编译器插入对象中的**隐藏指针**，程序员写代码时看不见。  
- 标准**不规定**布局细节（这是 ABI 问题）；主流实现（GCC/Clang 的 Itanium C++ ABI、MSVC 类似思想）都用 vptr + vtable。  
- 有虚函数的类 → 对象通常 `sizeof` 变大（64 位平台上常 +8 字节）。  
- 同一动态类型的对象，vptr **指向同一张表**（值相同）。

### vtable（virtual table / vftable）

- 每个含虚函数的**类**对应一张（静态）表。  
- 表项典型包括：各虚函数地址；析构相关槽位；`typeinfo*`（支持 `dynamic_cast`/`typeid`，若开启 RTTI）；多重继承下可能还有 **offset-to-top**、this 调整 thunk。  
- 创建对象时，构造函数把本类 vtable 的地址写入对象的 vptr。

---

## 2. 单继承下的布局（最常见）

```cpp
struct Base {
  int x;
  virtual void f() {}
  virtual void g() {}
  virtual ~Base() = default;
};

struct Derived : Base {
  int y;
  void f() override {}
  void g() override {}
};
```

### 对象布局示意

```text
Derived d;
+------------------+
| vptr  ───────────┼──→  Derived::vtable
+------------------+         [0] ~Derived / deleting dtor
| Base::x          |         [1] Derived::f
+------------------+         [2] Derived::g
| Derived::y       |         [... typeinfo ...]
+------------------+
```

```text
Base b;
+------------------+
| vptr  ───────────┼──→  Base::vtable
+------------------+         [0] ~Base / deleting dtor
| Base::x          |         [1] Base::f
+------------------+         [2] Base::g
```

要点：

- 派生对象**共用**基类子对象布局约定，再追加自己的数据成员。  
- `Derived::vtable` 是**另一张表**，不是改写 `Base::vtable`。  
- 覆盖只是「派生类表里同槽位放了新地址」。

---

## 3. 一次虚调用的时间线

```cpp
Base* p = new Derived;
p->f();
```

```text
1) 读 p 指向对象起始处的 vptr          → 得到 Derived::vtable
2) 按 f 在类层次中的槽位 index 取表项 → Derived::f 的地址
3) call 该地址，this = p（必要时 thunk 调整）
```

伪代码：

```cpp
// 概念模拟
using Fn = void(*)(Base*);
Fn fn = p->vptr->slot_f;
fn(p);
```

| 步骤 | 成本 |
|------|------|
| 读 vptr | 一次内存读 |
| 读函数地址 | 第二次读（表在只读段） |
| 间接跳转 | 可能阻碍分支预测与内联 |

对比非虚：直接 `call Base::f` 或内联后变成直线代码。

---

## 4. 槽位顺序谁定？覆盖如何「写入」？

- 槽位顺序由**声明顺序**与 ABI 约定决定（常见：析构相关槽 + 按声明序的虚函数）。  
- 编译器为每个类生成一张表；派生类**复制基类槽位布局**，再把覆盖函数的地址填进去；未覆盖的槽位沿用基类实现地址。  
- `final` 覆盖或 `devirtualized` 调用时，编译器可能优化成直接调用（静态可知类型）。

```text
Base::vtable          Derived::vtable
[0] ~Base        →    [0] ~Derived
[1] Base::f      →    [1] Derived::f   // override
[2] Base::g      →    [2] Derived::g   // override
[3] Base::h      →    [3] Base::h      // 未覆盖则保留
```

---

## 5. 构造 / 析构时 vptr 如何变？

```cpp
struct Base {
  Base() { /* 此刻 vptr → Base::vtable */ }
  virtual void hello() {}
  virtual ~Base() {}
};

struct Derived : Base {
  Derived() { /* 先 Base()，再把 vptr → Derived::vtable */ }
  void hello() override {}
  ~Derived() override { /* 派生析构体结束后 vptr 回到 Base */ }
};
```

```text
new Derived
  分配内存
  → Base::Base()      内 vptr = Base::vtable
  → 写 Derived 成员前/中  vptr 改为 Derived::vtable
  → Derived::Derived() 体
delete
  → ~Derived() 体     （已是 Derived 表）
  → 恢复为 Base 表 → ~Base()
  → operator delete
```

因此：

- 基类构造函数里调 `hello()` → 走 `Base::hello`（vptr 还指向 Base）。  
- 同理基类析构里也不应假设派生状态仍有效。

---

## 6. 纯虚函数在 vtable 里是什么？

```cpp
struct Iface {
  virtual void run() = 0;
  virtual ~Iface() = default;
};
```

- 抽象类仍有 vtable（供派生复制槽位）。  
- 纯虚槽位常见实现：指向编译器提供的**占位函数**（如 `__cxa_pure_virtual`），调用会终止程序。  
- 派生类必须覆盖后，该槽位才是有用地址；否则对象本就不可合法实例化。

---

## 7. 多重继承：多个 vptr

```cpp
struct A { virtual void a(); int x; };
struct B { virtual void b(); int y; };
struct D : A, B {
  void a() override;
  void b() override;
};
```

示意：

```text
D 对象
+------------------+
| vptrA ──────────┼──→ D-as-A 的表（含 A 槽 + 可能 D 特有）
| A::x             |
+------------------+
| vptrB ──────────┼──→ D-as-B 的表（B 槽；this-thunk 调整）
| B::y             |
+------------------+
```

- `A* pa = d` 与 `B* pb = d` 的**指针值可能不同**（`pb` 可能有偏移）。  
- 经 `B*` 调用时，若 `this` 需要调整回 D/A 子对象，vtable 槽里可能是 **thunk**：先修正 `this`，再跳到真正函数。  
- 表中还可能有 **offset-to-top**、指向 **typeinfo** 的指针，用于 `dynamic_cast`/RTTI。

---

## 8. 虚析构与 deleting destructor

多态删除：

```cpp
Base* p = new Derived;
delete p;  // 需要「先跑派生析构，再释放整块内存」
```

主流 ABI 会在 vtable 里放：

| 槽位类型 | 作用 |
|----------|------|
| complete object destructor | 只析构对象 |
| deleting destructor | 析构 + 调用 `operator delete` |

`delete p` 经 vptr 调到 **deleting dtor**，才能把「派生析构」和「按 Base* 释放」一起做完。这也是**基类析构必须 virtual** 的实现层原因之一。

---

## 9. sizeof / 拷贝 / 移动 与 vptr

| 问题 | 结论 |
|------|------|
| 空类无虚函数 | 常 1 字节 |
| 空类有虚函数 | 至少一个 vptr（8 字节，64 位） |
| 对象拷贝 | 拷的是数据 + 当前类型的 vptr（按静态类型拷贝构造） |
| `Base b = derived_obj` | **对象切片**：按 Base 布局拷贝，vptr 变成 Base 的，多态丢失 |
| 移动 | 移动数据成员；vptr 由目标对象构造/赋值语义决定，不是「搬走源的表」 |

切片示例：

```cpp
Derived d;
Base b = d;   // b.vptr → Base::vtable，b 不是 Derived
```

---

## 10. 与「手写函数表」的对照（C 接口）

vtable 的工程本质：**每类一张函数指针表 + 每对象一个表指针**。

```c
struct Ops {
  void (*speak)(void* self);
};

struct Animal {
  const struct Ops* ops;
};

void animal_speak(struct Animal* a) { a->ops->speak(a); }
```

| | C++ vtable | 手写 Ops |
|--|------------|----------|
| 生成 | 编译器自动 | 程序员维护 |
| 槽位 | 声明序/ABI 固定 | 自定义 |
| 类型安全 | 语言保证 | 靠约定 |
| 覆盖检查 | `override` | 无 |
| RTTI/虚析构 | 可选自带 | 手写 |

协议栈 C 辅接口、驱动 `file_operations` 都是同一思想。

---

## 11. 工程取舍（结合 O-DU / srsRAN）

| 场景 | 建议 |
|------|------|
| 控制面、策略可替换、模块边界 | 抽象类 + 虚函数清晰，vtable 开销可接受 |
| 数据面、每 slot/每 PDU 热路径 | 避免虚调用；具体类型、模板、函数指针批量 |
| 对象数量巨大 | 注意每对象 vptr 的 cache 占用 |
| 需要 devirtualize | 局部使用具体类型，或 `final` |
| 序列化/跨模块 ABI | 不要依赖 vtable 内存布局跨 so 混用；接口版本要显式 |

---

## 12. 面试高频追问

1. **vptr 在对象的哪个位置？** → 标准未规定；主流常在起始处，方便 `Base*`/`Derived*` 共享前缀。  
2. **vtable 有几个？** → 通常每个含虚函数的类一张；多继承下按「基类子对象视角」可能有多张/多组槽。  
3. **覆盖会修改基类的 vtable 吗？** → 不会；派生类生成自己的表。  
4. **没有虚函数的类有 vptr 吗？** → 一般没有。  
5. **虚函数可以 inline 吗？** → 经指针调用通常不能内联；类型在调用点可见时编译器可去虚化后内联。  
6. **线程安全？** → vtable 只读，虚调用本身安全；对象数据仍需自行同步。  
7. **`dynamic_cast` 怎么实现？** → 沿 vtable 中 typeinfo/RTTI 结构查继承图（代价较高）。  
8. **构造函数为什么不能是 virtual？** → 构造时动态类型尚未完成，语言直接禁止。

---

## 13. 口头串讲（约 35 秒）

> vptr 是对象里编译器插入的隐藏指针，指向该对象动态类型对应的 vtable；vtable 是每个类一张的静态函数指针表，槽位按 ABI/声明顺序放析构和各虚函数。调用 `基类指针->虚函数` 时先读对象 vptr，再按槽位取地址间接 call。覆盖不会改基类的表，而是派生类有自己的 vtable，同槽位换成派生函数。构造过程中 vptr 先指向当前正在构造的基类表，所以构造里调虚函数不会走到最终派生版本；多态基类还要虚析构，表里 deleting destructor 负责「析构 + 按基类指针释放」。

---

## 相关

- [[C++面试-虚函数实现举例详解]]（现象、迷你 vtable 代码）
- [[C++面试-语言基础与面向对象]]（第 2～5 题）
- [[C++面试-内存管理与智能指针]]（`unique_ptr<Base>` + 虚析构）
- [[C++面试-static关键字详解]]（static 函数无 vptr、不可 virtual）
- [[面试题-目录]]
- [[MOC-C++与软件]]
