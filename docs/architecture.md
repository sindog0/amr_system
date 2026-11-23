# 架构决策与理由

## ADR-001 场景定位

- 轮式 AMR 做物料配送：成熟、走量、任务驱动、高频站点对接。
- 四足做巡检：真实但处于试点阶段，项目制、需遥操作兜底、安全标准空白。
- **同一 RMS 管异构车队**是集成与研究亮点，非常规成熟商品；作为教学/演示/论文项目成立，作为产品应先垂直做透一类。

## ADR-002 双平台成套 + 单一 HAL

每个平台是成套包（description/hardware/control/navigation/simulation），但共享 `common/robot_abstraction` 的唯一接口契约。

理由：异构平台的运动、传感、BMS 差异极大，成套化让平台代码可独立演进；HAL 保证上层与业务对具体平台零感知。

## ADR-003 应用层行为树插件化

`robot_task` 是通用执行引擎（基于 BT.CPP 或 nav2_behavior_tree），`robot_delivery` / `robot_inspection` 只提供 BT 子树与 action 节点。

理由：避免两个业务各自 fork 一套流程逻辑；新增业务 = 新增子树。

## ADR-004 导航共享底座

`navigation/robot_navigation` 提供 Nav2 通用 launch、参数与插件；`robots/<平台>/*_navigation` 只放平台差异（轮式差速 vs 四足步态/越障）。

理由：全量复制导航配置必然漂移；差异部分隔离到平台层。

## ADR-005 服务端按业务域切分

`dispatch`（派单）与 `traffic`（交通管制）分离；新增 `map` / `charging` / `api` / `observability`；`persistence` 替代 `database`。

理由：交通管制（拓扑、资源锁、死锁）是车队系统最难测的部分，不能与派单混在一起；`database` 是机制不是领域。早期允许模块化单体，但边界与依赖方向必须固定。

## ADR-006 协议单一来源

- 机器人 ↔ RMS：**MQTT 5 + JSON Schema**（沿用 VDA 5050 风格，便于调试与互操作）。
- Web ↔ RMS：REST + WebSocket。
- 所有 schema 在 `protocols/schema`，经 `protocols/codegen` 生成两侧代码；`robot_interfaces` 只承载进程内 ROS 消息。

理由：避免机器人侧 ROS msg 与服务端 DTO 双写导致协议漂移。

## ADR-007 仿真分层

- `simulation/factory_simulation`：世界与静态环境，**不引用具体机器人、不依赖 application/services**。
- `robots/<平台>/*_simulation`：平台模型与 spawn 配置，由 launch 注入世界。

理由：防止仿真包变成"依赖一切"的汇聚点。

## ADR-008 vendor 纪律

`vendor/` 存放原厂参考代码：**只读不改、单独标记 license、不进入生产构建**，需要时包装而非修改。
