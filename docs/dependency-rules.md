# 依赖规则

ROS 2 中任意包都能 include 别人，分层靠规则与评审维持。以下为**唯一允许的依赖边**。

## 机器人端 DAG

| 包 | 允许依赖 |
|---|---|
| `common/robot_interfaces` | 无（纯 msg/srv/action） |
| `common/robot_utils` | 无 |
| `common/robot_abstraction` | robot_interfaces |
| `navigation/robot_navigation` | robot_interfaces, robot_utils |
| `robots/<平台>/<平台>_description` | 无（xacro/mesh） |
| `robots/<平台>/<平台>_hardware` | robot_abstraction, robot_interfaces |
| `robots/<平台>/<平台>_control` | robot_abstraction, robot_interfaces |
| `robots/<平台>/<平台>_docking`（仅轮式） | robot_abstraction, robot_interfaces, *_navigation |
| `robots/<平台>/<平台>_navigation` | navigation/robot_navigation, robot_interfaces, robot_abstraction |
| `robots/<平台>/<平台>_simulation` | *_description |
| `application/*` | robot_abstraction, robot_interfaces, robot_utils, robot_task |
| `services/*` | robot_interfaces, robot_utils（robot_agent 可经 robot_abstraction 读能力） |
| `simulation/factory_simulation` | *_description, *_simulation |
| `robot_bringup` | 全部（组合根，唯一例外） |

## 禁止边（评审红线）

- ❌ `robots/*` → `application/*` / `services/*`
- ❌ `common/*` → 任何上层包
- ❌ `application/*` → `robots/*`（必须经 `robot_abstraction`）
- ❌ `services/*` → `application/*` / `robots/*`（能力读取除外，经 abstraction）
- ❌ `simulation/factory_simulation` → `application/*` / `services/*`

## 服务端模块依赖

```
api        → 各域服务
scheduler  → dispatch, traffic, task, charging, fleet
dispatch   → fleet, task, map
traffic    → map, fleet
charging   → fleet, task
device     → fleet, communication
*fleet/map/task/... → persistence, common
observability ← 所有（只读）
```

- 域模块之间**不得循环依赖**；跨域只经公开接口，不直接读对方表。
- `persistence` 只提供仓储接口，域模块不直接写 SQL。

## 校验建议

- CI 中对每个 `package.xml` / `CMakeLists.txt` 的 `depend` 做白名单校验。
- 用 `ros2 pkg` / `colcon graph` 检查循环依赖。
