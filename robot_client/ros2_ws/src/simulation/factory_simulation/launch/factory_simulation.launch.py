import os

from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


# def generate_launch_description():
#     package_share = get_package_share_directory('factory_simulation')

#     default_world = os.path.join(package_share, 'worlds', 'factory_map.sdf')
#     wheeled_gazebo = PathJoinSubstitution(
#         [FindPackageShare('wheeled_simulation'), 'launch', 'gazebo.launch.py'])

#     return LaunchDescription([
#         DeclareLaunchArgument(
#             'world', default_value=default_world,
#             description='SDF 世界文件；默认由 maps/factory_map.pgm 生成'),
#         DeclareLaunchArgument(
#             'headless', default_value='false',
#             description='只启动 gz server，不启动 GUI'),
#         DeclareLaunchArgument(
#             'rviz', default_value='true',
#             description='是否同时启动 RViz2'),
#         # 初始位姿（map 坐标系）。默认 (0,0) 在当前地图上离最近墙 2.15 m。
#         DeclareLaunchArgument('x', default_value='0.0'),
#         DeclareLaunchArgument('y', default_value='0.0'),
#         DeclareLaunchArgument('z', default_value='0.02'),
#         DeclareLaunchArgument('yaw', default_value='0.0'),

#         IncludeLaunchDescription(
#             PythonLaunchDescriptionSource(wheeled_gazebo),
#             launch_arguments={
#                 'world': LaunchConfiguration('world'),
#                 'headless': LaunchConfiguration('headless'),
#                 'rviz': LaunchConfiguration('rviz'),
#                 'x': LaunchConfiguration('x'),
#                 'y': LaunchConfiguration('y'),
#                 'z': LaunchConfiguration('z'),
#                 'yaw': LaunchConfiguration('yaw'),
#             }.items(),
#         ),
#     ])



def generate_launch_description():
    #1获取功能包路径
    pkg_share = get_package_share_directory('factory_simulation')

    gazebo_share = get_package_share_directory('ros_gz_sim')

    #2获取工厂世界文件
    world_file = os.path.join(
        pkg_share,
        'worlds',
        'factory_map.sdf'
    )

    #3 声明世界文件参数
    world = LaunchConfiguration('world')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value=world_file,
        description='Gazobo world file'
    )

    #4 启动gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                gazebo_share,
                'launch',
                'gz_sim.launch.py'
            )
        ),

        launch_arguments={
            'gz_args': ['-r -v 4 ', world]
        }.items()
    )

    #5 桥接gazebo 仿真时间
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ]
    )

    return LaunchDescription([
        declare_world,
        gazebo,
        clock_bridge
    ])