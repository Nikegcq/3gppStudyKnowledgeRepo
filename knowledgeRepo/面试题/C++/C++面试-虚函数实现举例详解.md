---
type: resource
tags: [C++, 面试题, 虚函数, 多态, vtable]
created: 2026-09-18
updated: 2026-09-18
status: active
---

# C++ 虚函数实现 — 举例详解

> 适用：面试追问「虚函数怎么实现的」时用例子讲清  
> 索引：[[C++面试-总览]]、[[C++面试-语言基础与面向对象]]

---

## 1. 先看代码现象

```cpp
#include <iostream>

struct Animal {
  virtual void speak() { std::cout << "...\n"; }
  virtual ~Animal() = default;
};

struct Dog : Animal {
  void speak() override { std::cout << "wang\n"; }
};

struct Cat : Animal {
  void speak() override { std::cout << "miao\n"; }
};

int main() {
  Dog d;
  Cat c;

  Animal* p = &d;
  p->speak();   // wang —— 不是 Animal 的 "..."

  p = &c;
  p->speak();   // miao
}
```

同一种调用 `p->speak()`，按 **p 指向的真实对象** 决定走哪个函数。这就是动态绑定；底下靠 **vptr / vtable**。

---

## 2. 对象里多了什么？

编译器给含虚函数的类插一个隐藏成员 **vptr**（通常在对象起始处，大小多为指针宽度）：

```text
Dog 对象（示意，64 位）:
+--------+------------------+
| vptr   | 其它成员（若有）  |
+--------+------------------+
   |
   v
Dog 的 vtable:
  [0] typeinfo（RTTI，若有）
  [1] Animal::~Animal()
  [2] Dog::speak()     ← 覆盖后指向 Dog 的实现
  ...
```

`Animal` 基类也有自己的 vtable，slot 里是 `Animal::speak()`。  
**换对象类型 = 换 vptr 指向的表 = 换函数地址。**

### 调用过程拆解

```text
p->speak()
  → 读对象里的 vptr
  → 按 vtable 中 speak 的槽位取函数指针
  → 间接调用该地址
```

伪代码（概念上）：

```cpp
// p->speak() 约等于
(**(p->vptr).speak)(p);  // 经 vtable 间接跳转，this 仍是 p
```

---

## 3. 手写一个「迷你 vtable」对照

用代码模拟编译器行为，面试时若被追问「你能不能说得更具体」，可画这张图：

```cpp
// —— 以下是概念模拟，不是标准 C++ 的真实 ABI ——
struct AnimalVTable {
  void (*speak)(Animal*);
  void (*dtor)(Animal*);
};

struct Animal {
  const AnimalVTable* vptr;
  // Animal() { vptr = &animal_vt; }
};

struct Dog {
  Animal base;  // 布局上先是基类（含 vptr）
};

void animal_speak(Animal* self) { /* ... */ }
void dog_speak(Animal* self)    { /* ... */ }

const AnimalVTable animal_vt{ &animal_speak, /*...*/ };
const AnimalVTable dog_vt{ &dog_speak, /*...*/ };

// Dog 构造时：base.vptr = &dog_vt;
// 调用：dog_vt.speak((Animal*)&dog);
```

要点：

| 概念 | 落地 |
|------|------|
| vptr | 对象内隐藏指针，每对象一份 |
| vtable | 每个类一份（通常只读，常在 `.rodata`） |
| 虚调用 | 两次指针跳转：对象→表→函数 |
| `this` | 仍是原始对象指针，传给具体函数 |

---

## 4. 构造期间 vptr 会变（高频追问）

```cpp
struct Base {
  Base() { hello(); }          // 注意：构造里调虚函数
  virtual void hello() { std::cout << "Base\n"; }
};

struct Derived : Base {
  void hello() override { std::cout << "Derived\n"; }
};

int main() {
  Derived d;   // 输出 Base，不是 Derived
}
```

原因：`Derived` 构造时，先跑 `Base::Base`；此刻对象动态类型仍是「Base 部分正在构造」，vptr 指向 **Base 的 vtable**，所以 `hello()` 只能绑到 `Base::hello`。等进入 `Derived` 构造体前，vptr 才改成 Derived 的表。

**结论：构造/析构中不要依赖「调到最终派生版本」。**

---

## 5. 纯虚函数 + 抽象类的例子

```cpp
struct L2Scheduler {
  virtual ~L2Scheduler() = default;
  virtual void run_slot(int slot) = 0;   // 纯虚：无默认实现
};

struct DummyScheduler : L2Scheduler {
  void run_slot(int slot) override {
    // 空实现 / 打日志
  }
};

// L2Scheduler s;           // 编译错误：抽象类不可实例化
L2Scheduler* p = new DummyScheduler;
p->run_slot(10);            // 走 DummyScheduler::run_slot
delete p;                   // 需要虚析构（见下）
```

- 纯虚 `= 0`：类不可实例化，逼子类覆盖。  
- vtable 里纯虚对应槽位可为空或占位函数；若某派生类未覆盖且尝试调用，会走占位（常 abort），所以**实例化前必须覆盖完**。

---

## 6. 为什么必须虚析构？用例子看泄漏

```cpp
struct Base {
  ~Base() { std::cout << "~Base\n"; }   // 非 virtual
  virtual void f() {}
};

struct Derived : Base {
  std::vector<int> data{1, 2, 3};
  ~Derived() { std::cout << "~Derived\n"; }
};

int main() {
  Base* p = new Derived;
  delete p;   // 只打印 ~Base —— ~Derived 没跑，data 资源未按设计释放（UB 风险）
}
```

把 `Base` 析构改成 `virtual ~Base() = default;` 后：`~Derived` → `~Base`，正确。

---

## 7. 协议栈风格示例（可替换进项目话术）

```cpp
#include <memory>
#include <vector>

struct MacEntity {
  virtual ~MacEntity() = default;
  virtual void on_slot(int slot) = 0;
  virtual const char* name() const = 0;
};

struct DummyMac : MacEntity {
  void on_slot(int slot) override { /* 统计/空跑 */ }
  const char* name() const override { return "dummy-mac"; }
};

struct CountingMac : MacEntity {
  int slots = 0;
  void on_slot(int slot) override { ++slots; }
  const char* name() const override { return "counting-mac"; }
};

void tick(const std::vector<MacEntity*>& macs, int slot) {
  for (auto* m : macs) {
    m->on_slot(slot);   // 同一行代码，不同实现
  }
}

int main() {
  DummyMac d;
  CountingMac c;
  tick({&d, &c}, 100);
  // d 空跑，c.slots == 1
}
```

面试可接：控制面组件用抽象接口 + 虚函数，便于替换实现；热路径数据面避免每消息虚调用，改模板或具体类型。

---

## 8. 成本与取舍

| 项 | 说明 |
|----|------|
| 时间 | 每次虚调用多 1～2 次指针跳转，阻碍内联 |
| 空间 | 每对象多一个 vptr；每类一张 vtable |
| 灵活 | 运行期可替换实现、接口稳定 |
| 热路径 | 协议栈数据面慎用；控制面/插件式策略常用 |
| 非虚对比 | 直接调用可内联；模板策略编译期绑定、零开销 |

---

## 9. 面试口头串讲（约 30 秒）

> 有虚函数的类，对象里会有一个隐藏的 vptr，指向该类的 vtable；vtable 里按声明顺序放函数指针。`基类指针->虚函数` 时，先读对象的 vptr，再按槽位取地址间接调用，所以看的是对象实际类型。构造过程中 vptr 先指向当前正在构造的类，因此构造里调虚函数不会走到最终派生版本。多态基类析构必须 virtual，否则 `delete` 基类指针会漏调派生析构。

---

## 10. 追问清单

1. **空类有虚函数后多大？** → 至少含 vptr（多数 64 位平台 8 字节）。  
2. **多重继承？** → 可能多个 vptr；跨基类调用可能有 this 调整（thunk）。  
3. **虚函数可以是 static 吗？** → 不行，static 无 this。  
4. **构造函数能是 virtual 吗？** → 不能。  
5. **override/final？** → `override` 编译期检查覆盖；`final` 禁止再覆盖/继承。  
6. **和函数指针接口比？** → vtable 是语言级多态；C 接口手动函数表原理类似，无类型系统自动调度。

---

## 相关

- [[C++面试-语言基础与面向对象]]（第 2～5 题）
- [[C++面试-static关键字详解]]
- [[C++面试-内存管理与智能指针]]（基类虚析构 + unique_ptr）
- [[MOC-C++与软件]]
