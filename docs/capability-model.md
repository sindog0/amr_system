# 异构能力模型与派单

异构车队的前提：**派单前先能力匹配**，而不是"有车就派"。

## 机器人能力档案（注册时上报）

```json
{
  "robot_id": "amr-01",
  "type": "wheeled",                 // wheeled | quadruped
  "capabilities": {
    "max_payload_kg": 300,
    "supports_docking": true,
    "terrain": ["flat"],             // flat | ramp | stairs | rough
    "sensors": ["lidar", "rgb_cam", "thermal_cam", "gas"],
    "route_layers": ["delivery_lane"],// delivery_lane | inspection_path
    "max_speed_mps": 1.5
  },
  "battery": { "soc": 0.82, "charging": false }
}
```

四足示例：

```json
{
  "robot_id": "dog-01",
  "type": "quadruped",
  "capabilities": {
    "terrain": ["flat", "stairs", "rough"],
    "sensors": ["rgb_cam", "thermal_cam", "gas", "acoustic"],
    "route_layers": ["inspection_path"],
    "payload_kg": 5
  }
}
```

## 任务需求

```json
{
  "task_id": "T-1001",
  "kind": "delivery",
  "needs": {
    "min_payload_kg": 120,
    "requires": ["supports_docking"],
    "route_layer": "delivery_lane"
  }
}
```

## 派单流程（dispatch）

1. **过滤**：能力满足 `needs`，且 `route_layer` 兼容、当前可用。
2. **打分**：综合考虑 距离、电量余量、当前负载、道路拥堵。
3. **分配**：写资源锁，交给 `traffic` 校验路权。

## 交通分层（traffic）

同一张地图上两层路权，互不混用：

- **delivery_lane**：拓扑路网（节点/边/区域），资源锁 + 死锁规避 + 单向道 + 优先级。适合高频点对点配送。
- **inspection_path**：巡视路线（waypoints + 驻留点），按计划巡航、驻留采集。四足轨迹不可预测，**不与配送车道做统一时空避让**，只做区域级互斥（同一危险区不同时进入）。

## 为什么这样切

- 配送是"任意点到任意点走道路网"，巡检是"沿固定路线巡逻+驻留"，两者路权语义不同。
- 用能力模型而非按 type 硬编码，新增机器人类型/传感器无需改派单逻辑。
