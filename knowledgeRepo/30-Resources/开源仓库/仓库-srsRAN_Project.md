---
type: resource
tags: [开源, srsRAN, O-RAN, PHY]
repo: srsRAN_Project
repo_url: https://github.com/srsran/srsRAN_Project
local_path: /home/nick/work/repo/srsRAN_Project
created: 2026-09-03
updated: 2026-09-03
status: active
---

# srsRAN_Project 仓库地图

## 这是什么

srsRAN Project 是一套完整的 5G RAN 开源实现（O-RAN 原生 CU/DU），包含 L1/L2/L3 全栈，代码以 C++17 为主，面向 x86 与 ARM 优化，外部依赖很少（FFTW、mbedTLS、yaml-cpp、lksctp 等）。本仓库已包含从 CU-CP/CU-UP、DU 到 PHY、调度器的完整 gNB 功能。

## 版本与项目状态（重要）

- 本地分支：`main`；描述：`release_25_10-192-g4bf1543936`；HEAD：`4bf1543936`（2026-02 “readme: add OCUDU notice”）
- 上游：`origin → https://github.com/srsran/srsRAN_Project.git`
- 项目迁移：README 顶部声明，**srsRAN Project 已于 2025-12 迁移到 OCUDU**（[ocudu.org](https://ocudu.org)，新仓库 `gitlab.com/ocudu/ocudu`），本仓库将归档、不再维护。因此：学习 25.10 前后的代码用本仓库没问题；要看后续新特性需切换到 OCUDU 仓库。
- 本地工作区有**未提交的定制/文档**（`git status` 可见）：`docs/l1c_flow.md`、`docs/pdsch_codeword_layer_port_explanation.md`、`docs/mac_to_ofh_*`、`lib/phy/upper/upper_phy_rx_dci_extractor_decorator.*`、`configs/gnb_zmq.yaml`、`AGENTS.md`、`build/` 等。阅读时注意区分上游代码与本地改动。

## 顶层结构

| 目录 | 内容 |
| --- | --- |
| `apps/` | 可执行程序：`gnb`（gnb.cpp）、`du`（du.cpp）、`du_low`（du_low.cpp）、`cu`/`cu_cp`/`cu_up`、`examples`、`helpers`、`units` |
| `lib/` | 37+ 功能库（phy、scheduler、mac、rlc、pdcp、sdap、rrc、f1ap、e1ap、ngap、gtpu、fapi、fapi_adaptor、ofh、ru、hal、radio、srsvec、support、ran、asn1……） |
| `include/srsran/` | 对外公共头文件（接口定义，学习 PHY 从这里看接口最清晰） |
| `tests/` | `unittests`、`integrationtests`、`e2e`（PHY 单测在 `tests/unittests/phy/`） |
| `docs/` | 代码文档；**本机新增的团队文档也在这里**（见下） |
| `configs/`、`docker/`、`external/` | 示例配置、容器、第三方依赖 |

## 与 3GPP / O-RAN 分层的关系

- 3GPP 5G 架构：gNB 分为 CU（再拆 CU-CP / CU-UP）与 DU，接口 F1/E1；PHY 属于 DU 侧，向上通过 MAC（调度器 `lib/scheduler`）衔接。
- O-RAN：本仓库支持 Split-8（`lib/radio` + UHD/ZMQ，射频直连）与 Split-7.2x（`lib/ru` + `lib/ofh` 前传接口 + 外部 RU）；`du_low` 应用面向 7.2x 场景。PHY 内部又分上 PHY（upper PHY，处理 PDU/资源网格）与下 PHY（lower PHY，OFDM/采样域），对应 O-RAN 的 DU-Low 分工。
- MAC↔PHY 之间走 FAPI（`lib/fapi` + `lib/fapi_adaptor`，适配器在 `include/srsran/fapi_adaptor/`）。

## 构建与测试

```bash
cd /home/nick/work/repo/srsRAN_Project
mkdir -p build && cd build
cmake ../ -DBUILD_TESTING=On
make -j$(nproc)
ctest -R pdsch        # 只跑 PDSCH 相关测试
```

常用 CMake 选项：`-DENABLE_ZEROMQ=ON`、`-DENABLE_DPDK=True`、`-DCMAKE_BUILD_TYPE=Release`、`-DASSERT_LEVEL=PARANOID`。要求 FFTW、mbedTLS、yaml-cpp、lksctp（仓库自带 AGENTS.md 有记录）。

## 本机 docs/ 里已有的团队学习文档

先读这些再进代码，事半功倍：

- `docs/l1c_flow.md`：lib/phy 与 lib/scheduler 的每帧/子帧流程梳理（RX→调度→TX→HARQ 闭环），并给出插桩/调试建议
- `docs/pdsch_codeword_layer_port_explanation.md`：PDSCH 从 TB 到空口的完整链路 + 码字/层/天线端口概念辨析
- `docs/mac_to_ofh_sequence.md/.puml`：MAC 调度到 Open Fronthaul（Split 7.2）的调用时序

## 本系列学习笔记

- [[仓库-srsRAN_Project-PHY总览]]：PHY 代码地图、上/下 PHY 与 TX/RX 全链路
- [[仓库-srsRAN_Project-信道编码与速率匹配]]：CRC/LDPC/Polar/短块编码与 3GPP 对照
- [[仓库-srsRAN_Project-下行物理信道与OFDM发射]]：PDSCH/PDCCH/SSB 发射链与资源映射
- [[仓库-srsRAN_Project-上行接收与信道估计]]：PUSCH/PUCCH/PRACH/SRS 接收链

## 待办

- [ ] 对照 OCUDU 新仓库，确认本仓库之后的关键 PHY 变更
- [ ] 逐个模块跑 `ctest` 并用日志 decorator 观察行为

