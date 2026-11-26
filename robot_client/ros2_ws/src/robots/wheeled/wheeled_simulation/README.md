# wheeled_simulation

轮式 AMR 的仿真/可视化启动包。模型几何与惯性来自 `wheeled_description`；
本包只描述「在 Gazebo 里怎么被驱动、怎么被感知」。

依赖方向（[docs/dependency-rules.md](../../../../../../docs/dependency-rules.md)）：
`wheeled_simulation → wheeled_description`。

## 文件各自负责什么

```
wheeled_simulation/
├── urdf/wheeled_robot.sim.urdf.xacro       # 入口：include 下面三个
├── urdf/wheeled_robot.ros2_control.xacro   # 4 个轮子的 command/state interface
├── urdf/wheeled_robot.gazebo_sensors.xacro # gz-sim 的 lidar/camera/imu
├── config/controllers.yaml                 # controller_manager + 控制器参数
├── launch/display.launch.py                # 只开 RViz
├── launch/gazebo.launch.py                 # gz sim + spawn + 控制器 + 桥接
└── rviz/wheeled.rviz
```

`wheeled_description` 完全不知道 ros2_control / Gazebo 的存在，这是刻意的：
换真机时只替换 hardware 插件，模型不用动。

## 差速控制是怎么接起来的

这是一条 6 段链路，缺任何一段轮子都不转：

1. **URDF 声明接口**（[wheeled_robot.ros2_control.xacro](urdf/wheeled_robot.ros2_control.xacro)）

   ```xml
   <ros2_control name="WheeledSimSystem" type="system">
     <hardware>
       <plugin>gz_ros2_control/GazeboSimSystem</plugin>
     </hardware>
     <joint name="joint_left_w">
       <command_interface name="velocity">...</command_interface>
       <state_interface name="position"/>
       <state_interface name="velocity"/>
     </joint>
     ...
   </ros2_control>
   ```

   `command_interface` 是控制器能写的量，`state_interface` 是能读的量。
   joint 名必须和模型里的 `<joint name>` 一字不差。

2. **Gazebo 内起 controller_manager**
   （同一个 xacro 里的 `<gazebo><plugin filename="gz_ros2_control-system">`）
   插件在 gz 进程内创建 `/controller_manager`，并读取 `config/controllers.yaml`。

3. **controllers.yaml 声明加载哪些控制器**

   ```yaml
   controller_manager:
     ros__parameters:
       joint_state_broadcaster: {type: joint_state_broadcaster/JointStateBroadcaster}
       diff_drive_controller:   {type: diff_drive_controller/DiffDriveController}
   ```

4. **spawner 激活控制器**（launch 中 6 s / 8 s 的两个 `controller_manager spawner`）
   控制器分 `unconfigured → inactive → active`，spawner 负责推进到 active。

5. **diff_drive_controller 把几何参数变成轮速**
   输入 `~/cmd_vel`（Jazzy 是 `geometry_msgs/msg/TwistStamped`，不是 Twist），
   按 `wheel_separation`、`wheel_radius` 算出左右轮角速度，写入 velocity 接口。

6. **反馈回里程计**
   轮子 position/velocity 接口 → `~/odom` + `odom → base_footprint` TF；
   `joint_state_broadcaster` → `/joint_states` → `robot_state_publisher` 补全其余 TF。

## 传感器是怎么接起来的

同样三段，缺一不响：

1. **world 里加载系统插件**（不在本包，见
   [factory_simulation/worlds/sim_demo.sdf](../../../simulation/factory_simulation/worlds/sim_demo.sdf)）：

   ```xml
   <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
     <render_engine>ogre2</render_engine>
   </plugin>
   <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
   ```

   Gz 自带的 `empty.sdf` 没有这两个插件，所以用 `empty.sdf` 时传感器永远没数据。

2. **URDF 的 `<gazebo reference="link">` 里定义 sensor**
   （[wheeled_robot.gazebo_sensors.xacro](urdf/wheeled_robot.gazebo_sensors.xacro)）
   关键是 `<topic>`（gz 主题名）和 `<gz_frame_id>`（桥接后 ROS 消息的 frame_id）。

3. **ros_gz_bridge 把 gz 主题桥成 ROS 主题**：

   | gz 主题 | ROS 主题 | 类型 |
   |---|---|---|
   | `/scan` | `/scan` | `sensor_msgs/msg/LaserScan` |
   | `/camera/image` | `/camera/image` | `sensor_msgs/msg/Image` |
   | `/camera/camera_info` | `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` |
   | `/imu` | `/imu` | `sensor_msgs/msg/Imu` |
   | `/clock` | `/clock` | `rosgraph_msgs/msg/Clock` |

   注意相机内参的主题是 `<topic>/camera_info`；写 `/camera_info` 是收不到数据的。

## 启动与验证

```bash
cd robot_client/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-up-to factory_simulation
source install/setup.bash

# 带传感器世界的完整仿真（推荐）
ros2 launch factory_simulation factory_simulation.launch.py

# 或不用 factory 世界（此时传感器不会出数据）
ros2 launch wheeled_simulation gazebo.launch.py world:=empty.sdf
```

验证：

```bash
ros2 control list_controllers          # 两个控制器应为 active
ros2 topic echo /scan --once           # frame_id: laser_link
ros2 topic echo /camera/image --once   # frame_id: camera_link
ros2 topic echo /imu --once            # frame_id: base_imu
ros2 run tf2_ros tf2_echo odom base_footprint

# 让机器人前进（TwistStamped！-s 表示用仿真时间填 header.stamp）
ros2 topic pub -s -r 20 /diff_drive_controller/cmd_vel \
  geometry_msgs/msg/TwistStamped \
  "{header: {frame_id: base_link}, twist: {linear: {x: 0.3}}}"
```

### 键盘遥控

`teleop_twist_keyboard` 发的是 `geometry_msgs/Twist` 到 `/cmd_vel`，而 Jazzy 的
`diff_drive_controller` 只收 `TwistStamped`。launch 默认会启动
[cmd_vel_relay.py](scripts/cmd_vel_relay.py) 做转换，所以直接开遥控即可：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
# i 前进 / , 后退 / j l 转向 / k 停
```

不想用 relay 时 launch 加 `cmd_vel_relay:=false`，但那样就必须自己发 TwistStamped。

## 实测踩过的坑（模型/配置层面）

1. **原厂 `velocity="0"`**：四个轮子的 joint limit 速度是 0，Gazebo 里关节不动。
   已在 description 中改为 20 rad/s。
2. **`base_footprint` 与 `base_link` 重合**：轮子半径 0.0435、轮心 z=0.0283，
   原模型轮子陷地 1.5 cm。已把 footprint joint 抬高 0.0152 m。
3. **`package://` 在 Gz 里变成 `model://`**：description 的 `package.xml` 需要
   `<gazebo_ros gazebo_model_path="${prefix}/.."/>`，否则 Gazebo 找不到 mesh。
4. **相机内参主题**：`<topic>/camera/image</topic>` 的内参在 `/camera/camera_info`。
5. **固定关节被 SDF 合并**：`camera_link/laser_link/base_imu` 在 Gazebo 里会被
   合并进父 link，这是正常行为；`gz_frame_id` 仍保证 ROS 消息 frame_id 正确。

## 当前限制

- 没有真机 hardware 插件、没有 Nav2 接入；控制器参数是仿真值。
- 轮子用 velocity 接口 + 位置反馈；如果换成真实编码器差速底盘，只需换
  `<hardware><plugin>`，controllers.yaml 可复用。
- `cmd_vel_timeout: 0.5` 会在空闲时周期性打印 "Velocity command timed out. Braking."，
  属正常保护行为。
