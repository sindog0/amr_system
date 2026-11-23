"""世界 + 机器人的组合根：由 factory_simulation 注入 world，再 include 平台仿真 launch。

依赖方向（docs/architecture.md ADR-007）：
  factory_simulation → wheeled_simulation → wheeled_description
机器人 launch 不反向依赖世界。

world 的坐标系约定与 ROS map 坐标系完全一致（见 scripts/map_to_world.py），
因此机器人在 Gazebo 里的初始位姿 (x, y, yaw) 就是 map 坐标系下的位姿。
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = get_package_share_directory('factory_simulation')

    default_world = os.path.join(package_share, 'worlds', 'factory_map.sdf')
    wheeled_gazebo = PathJoinSubstitution(
        [FindPackageShare('wheeled_simulation'), 'launch', 'gazebo.launch.py'])

    return LaunchDescription([
        DeclareLaunchArgument(
            'world', default_value=default_world,
            description='SDF 世界文件；默认由 maps/factory_map.pgm 生成'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='只启动 gz server，不启动 GUI'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='是否同时启动 RViz2'),
        # 初始位姿（map 坐标系）。默认 (0,0) 在当前地图上离最近墙 2.15 m。
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.02'),
        DeclareLaunchArgument('yaw', default_value='0.0'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(wheeled_gazebo),
            launch_arguments={
                'world': LaunchConfiguration('world'),
                'headless': LaunchConfiguration('headless'),
                'rviz': LaunchConfiguration('rviz'),
                'x': LaunchConfiguration('x'),
                'y': LaunchConfiguration('y'),
                'z': LaunchConfiguration('z'),
                'yaw': LaunchConfiguration('yaw'),
            }.items(),
        ),
    ])
