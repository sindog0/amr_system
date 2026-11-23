# factory_simulation

仿真「世界」与组合 launch。按 ADR-007：

- 这里放静态环境（地面、墙、箱子、灯光、world 级插件）；
- 不引用 application/services，也不复制机器人模型；
- 通过 launch 把 world 注入 `wheeled_simulation`。

## 目录

```
factory_simulation/
├── maps/factory_map.pgm|yaml     # ROS 2D 占据栅格（Nav2 用）
├── worlds/factory_map.sdf        # 由上面的地图自动生成的 Gazebo 世界
├── worlds/sim_demo.sdf           # 手工搭的演示世界（四面墙 + 箱子）
├── scripts/map_to_world.py       # PGM/YAML -> SDF 转换器
└── launch/factory_simulation.launch.py
```

## 为什么不能把 .pgm 直接丢给 Gazebo

`.pgm + .yaml` 是 **Nav2 / AMCL 用的二维占据栅格**，Gazebo 不认识这种格式。
要让 Gazebo 里也有同一张地图，需要把它变成三维几何。本包的做法：

```
occupied 像素 → 0.05 m × 0.05 m 的墙体盒子（高度 1.5 m）
```

同时保留 PGM/YAML 给 Nav2 的 `map_server` 使用。两边共用同一个 `origin`、
`resolution`，所以 **Gazebo 世界坐标 = ROS map 坐标**，AMCL 定位和仿真不会错位。

> 备选方案：把地图当贴图铺在地面（只能看、不能撞），或用 heightmap
> （墙会变成 5 cm 宽斜坡）。做导航仿真建议用这里的盒子方案。

## 生成 / 更新 Gazebo 世界

地图变了就重新生成：

```bash
cd robot_client/ros2_ws/src/simulation/factory_simulation
python3 scripts/map_to_world.py
# 可选参数：
#   --map-yaml maps/xxx.yaml
#   --output worlds/xxx.sdf
#   --wall-height 2.0
#   --unknown free|wall      # 未知区域（PGM 灰度 205）当空地还是墙
```

当前地图（403×286 px @ 0.05 m/px = 20.15×14.30 m，origin `[-10.049, -7.160]`）
生成了 **508 个墙体盒子**。脚本会先把每行占据像素做游程编码，再把上下相邻
且区间相同的游程合并，避免生成几万个盒子把 Gazebo 拖死。

## 启动

```bash
cd robot_client/ros2_ws
colcon build --symlink-install --packages-up-to factory_simulation
source install/setup.bash

# 默认就是 maps/factory_map.pgm 生成的世界
ros2 launch factory_simulation factory_simulation.launch.py

# 换回手工演示世界
ros2 launch factory_simulation factory_simulation.launch.py \
  world:=$(ros2 pkg prefix factory_simulation)/share/factory_simulation/worlds/sim_demo.sdf

# 指定初始位姿（map 坐标系；默认 (0,0) 离最近墙 2.15 m）
ros2 launch factory_simulation factory_simulation.launch.py x:=2.0 y:=-1.0 yaw:=1.57
```

## world 里必须有的插件

```xml
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
```

没有这两个插件，URDF 里的 lidar/camera/IMU 不会产生任何数据。生成脚本
和 `sim_demo.sdf` 都包含它们。

## 已知边界

- 地图是二维的：墙体只有一层盒子，没有门框高度、货架分层等三维细节。
- 未知区域默认当空地；如果地图边缘有未建图区域，机器人可能开出去。
- 目前假设 YAML 的 `origin` 只有平移（yaw=0）；当前地图满足。若以后
  yaw≠0，脚本会告警，需要先扩展坐标变换。
- 地图与 Nav2 的 `map_server` 用同一份 yaml；接 Nav2 时把
  `maps/factory_map.yaml` 传给 map_server 即可。
