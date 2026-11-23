# robot_system — 工业移动机器人调度管理与自主作业系统

异构车队：**轮式 AMR 负责物料配送**，**四足机器人负责巡检**，由统一 RMS 调度管理。

- 机器人端：ROS 2（Jazzy/Humble）+ 嵌入式 Linux
- 管理服务端：RMS（设备/车队/任务/调度/交通/地图/充电/通信）
- Web 平台：监控与运维
- 通信协议单一来源，两侧代码生成

## 架构总览

```
robot_client ──MQTT──▶ rms_server ──HTTP/WS──▶ rms_web
     ▲                     │
     └──── protocols ──────┴── (单一 schema 来源)
```

## 目录结构

```
robot_system/
├── robot_client/ros2_ws/src/
│   ├── common/                     # 依赖最底层，平台无关
│   │   ├── robot_interfaces/       # 只放 msg/srv/action
│   │   ├── robot_abstraction/      # C++ 纯虚 HAL 接口契约
│   │   └── robot_utils/            # 数学/配置/日志
│   ├── navigation/
│   │   └── robot_navigation/       # 共享 Nav2 底座：launch/通用参数/插件
│   ├── robots/                     # 平台成套实现
│   │   ├── wheeled/
│   │   │   ├── wheeled_description/
│   │   │   ├── wheeled_hardware/   # HAL 实现：驱动
│   │   │   ├── wheeled_control/    # 差速控制
│   │   │   ├── wheeled_docking/    # 充电桩/产线对接
│   │   │   ├── wheeled_navigation/ # 平台导航参数/插件
│   │   │   └── wheeled_simulation/
│   │   └── quadruped/
│   │       ├── quadruped_description/
│   │       ├── quadruped_hardware/
│   │       ├── quadruped_control/  # 步态/MPC
│   │       ├── quadruped_navigation/
│   │       └── quadruped_simulation/
│   ├── application/                # 业务（行为树插件）
│   │   ├── robot_task/             # 通用 BT/状态机执行引擎
│   │   ├── robot_delivery/         # 配送 BT 子树
│   │   └── robot_inspection/       # 巡检 BT 子树
│   ├── services/                   # 系统服务
│   │   ├── robot_agent/            # 身份/注册/心跳/能力上报
│   │   ├── robot_communication/    # 传输 MQTT/gRPC
│   │   ├── robot_safety/           # 急停/安全降级
│   │   ├── robot_diagnostics/
│   │   └── robot_storage/
│   ├── simulation/
│   │   └── factory_simulation/     # 世界/环境，机器人由 launch 注入
│   └── robot_bringup/              # 组合根，唯一允许依赖全部
│
├── rms_server/                     # 服务端按业务域切分
│   ├── api/                        # REST/WS 网关
│   ├── device/                     # 注册/心跳/连接生命周期
│   ├── fleet/                      # 车队注册表/能力/状态聚合
│   ├── task/                       # 任务生命周期/模板
│   ├── dispatch/                   # 能力匹配派单
│   ├── traffic/                    # 路网/资源锁/死锁规避
│   ├── map/                        # 地图版本/区域/拓扑
│   ├── charging/                   # 电量策略/充电调度
│   ├── scheduler/                  # 顶层编排
│   ├── communication/              # 与机器人传输
│   ├── persistence/                # 仓储 + 迁移
│   ├── common/                     # 配置/日志/错误码
│   └── observability/              # 指标/告警/审计
│
├── rms_web/src/                    # api/views/components/stores/router
├── protocols/                      # schema(单一来源)/codegen/VERSION
├── deploy/                         # robot(systemd/OTA)/server/monitoring/provisioning
├── scripts/
├── tests/                          # integration/e2e/hil/fleet_sim/perf
├── vendor/                         # 原厂参考代码：只读不改
└── docs/                           # architecture/dependency-rules/capability-model/adr
```

## 三条铁律

1. **依赖方向单一**：`common` 最底层；`robots/*` 永不依赖 `application/*` 与 `services/*`；跨层只能经 `robot_abstraction`。详见 [docs/dependency-rules.md](docs/dependency-rules.md)。
2. **协议单一来源**：所有跨进程/跨机器通信从 `protocols/schema` 生成，`robot_interfaces` 只放进程内 ROS 消息。
3. **应用即插件**：业务差异以行为树子树表达，不 fork 执行引擎。

## 文档

- [架构决策与理由](docs/architecture.md)
- [依赖规则](docs/dependency-rules.md)
- [异构能力模型与派单](docs/capability-model.md)

## 下一步

```bash
cd robot_client/ros2_ws/src
ros2 pkg create --build-type ament_cmake robot_interfaces ...
# 先打通：robot_interfaces → robot_abstraction → 一个平台 hardware → robot_communication → rms_server
```
