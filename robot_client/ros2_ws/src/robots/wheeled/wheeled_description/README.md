# wheeled_description

轮式 AMR 的机器人描述包（xacro + mesh），遵循
[docs/dependency-rules.md](../../../../../../docs/dependency-rules.md)：
**本包只允许包含 xacro/mesh，不依赖任何其他包**。

## 来源与改动

模型复制自原厂参考代码（vendor 只读，未修改原件）：

- 源 URDF：`vendor/src/abot_base/abot_model/urdf/abot_model.urdf`
- 源 mesh：`vendor/src/abot_base/abot_model/meshes/*.STL`

复制时做了三处修正（其余内容，包括机器人名 `abot_model`、尺寸与惯性，保持原样）：

1. mesh 引用 `package://abot_model/meshes/...` → `package://wheeled_description/meshes/...`
2. `base_footprint_joint` 的 z 从 0 改为 0.0152：轮子半径 0.0435 m、轮心 z=0.0283 m，
   原模型 footprint 与 base_link 重合会让轮子陷地约 1.5 cm。
3. 四个轮子 joint limit 的 `velocity` 从 0 改为 20 rad/s：原厂导出值会让
   Gazebo 关节无法转动（差速控制器激活但不走）。

`use_gazebo_classic` 参数默认 false，用于屏蔽原厂 Gazebo Classic 插件。

## 结构

```
wheeled_description/
├── urdf/wheeled_robot.urdf.xacro   # 差速底盘：base_footprint → base_link → 4 轮 + camera + laser + imu
└── meshes/*.STL                     # 7 个 SolidWorks 导出网格
```

TF 树：

```
base_footprint
└── base_link
    ├── base_imu
    ├── camera_link
    ├── laser_link
    ├── link_left_w   (continuous)
    ├── link_left_s   (continuous)
    ├── link_right_w  (continuous)
    └── link_right_s  (continuous)
```

## 尚未迁移的部分（有意不做）

1. **launch 不放在本包**：按依赖规则，显示/仿真的 launch 应放在 `wheeled_simulation`
   （允许依赖 `*_description`）或 `robot_bringup`。
2. **Gazebo Classic 插件已用 xacro 参数隔离**：`libgazebo_ros_laser.so`、
   `libgazebo_ros_camera.so` 只在 `use_gazebo_classic:=true` 时展开（默认 false），
   避免 Jazzy + Gz Sim 加载时报找不到插件。真正的 gz-sim 传感器/控制器配置
   应在 `wheeled_simulation` 里补，而不是改本包。
3. **`camera_link` 质量为 0、惯量全 0**：RViz 可用，物理仿真会告警，仿真迁移时需补。
4. **原厂 world 文件**（`abot_square.world`、`mbxh.world`）属于仿真资产，
   未复制；将来放 `simulation/factory_simulation` 或 `wheeled_simulation`。
5. **`joint_names_abot_model.yaml`**（ros_control 关节名）未复制，接 controller 时再引入。

## License

原厂 `abot_model` 的 `package.xml` 中 license 为 `TODO`，本包暂沿用 `TODO`。
在对外分发或进入生产构建前，需要确认原厂授权。
