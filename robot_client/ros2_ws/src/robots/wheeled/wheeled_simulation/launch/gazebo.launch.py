import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, FindExecutable
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    simulation_share = FindPackageShare('wheeled_simulation')

    # 注意：这里用 sim 入口 xacro，不是 description 里那个。
    sim_xacro = PathJoinSubstitution(
        [simulation_share, 'urdf', 'wheeled_robot.sim.urdf.xacro'])
    rviz_config = PathJoinSubstitution(
        [simulation_share, 'rviz', 'wheeled.rviz'])
    gz_sim_launch = PathJoinSubstitution(
        [FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])

    robot_description = ParameterValue(
        Command(['xacro ', sim_xacro]), value_type=str)

    world = LaunchConfiguration('world')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('rviz')

    gz_with_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={'gz_args': ['-r ', world]}.items(),
        condition=UnlessCondition(headless),
    )
    # --headless-rendering：没有窗口也要跑 camera/lidar 的渲染管线
    gz_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={
            'gz_args': ['-r -s --headless-rendering ', world]}.items(),
        condition=IfCondition(headless),
    )

    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-name', 'wheeled_robot',
                    '-topic', 'robot_description',
                    '-x', LaunchConfiguration('x'),
                    '-y', LaunchConfiguration('y'),
                    '-z', LaunchConfiguration('z'),
                    '-Y', LaunchConfiguration('yaw'),
                ],
                output='screen',
            ),
        ],
    )

    # spawner 会等 /controller_manager 服务出现；先激活状态广播，再激活差速控制。
    load_joint_state_broadcaster = TimerAction(
        period=6.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'joint_state_broadcaster',
                    '--controller-manager', '/controller_manager',
                    '--controller-manager-timeout', '60',
                ],
                output='screen',
            ),
        ],
    )
    load_diff_drive = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'diff_drive_controller',
                    '--controller-manager', '/controller_manager',
                    '--controller-manager-timeout', '60',
                ],
                output='screen',
            ),
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world', default_value='empty.sdf',
            description='Gz Sim 世界文件（名称或绝对路径）。带传感器的 world 见 factory_simulation'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='只启动 gz server（附 headless 渲染），不启动 GUI'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='是否同时启动 RViz2'),
        DeclareLaunchArgument('x', default_value='0.0',
                              description='spawn 位姿 x（m）'),
        DeclareLaunchArgument('y', default_value='0.0',
                              description='spawn 位姿 y（m）'),
        DeclareLaunchArgument('z', default_value='0.02',
                              description='spawn 位姿 z（m）'),
        DeclareLaunchArgument('yaw', default_value='0.0',
                              description='spawn 朝向（rad）'),
        DeclareLaunchArgument(
            'cmd_vel_relay', default_value='true',
            description='启动 /cmd_vel(Twist) -> 控制器 TwistStamped 的转换节点'),

        gz_with_gui,
        gz_headless,

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': True,
            }],
            output='screen',
        ),
        # teleop / Nav2 常发 geometry_msgs/Twist 到 /cmd_vel，
        # 而 Jazzy 的 diff_drive_controller 只收 TwistStamped。
        Node(
            package='wheeled_simulation',
            executable='cmd_vel_relay.py',
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('cmd_vel_relay')),
            output='screen',
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
                # gz 相机传感器把内参发在 <topic>/camera_info，即 /camera/camera_info
                '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
                '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            ],
            parameters=[{'use_sim_time': True}],
            output='screen',
        ),
        spawn_robot,
        load_joint_state_broadcaster,
        load_diff_drive,
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(use_rviz),
            output='screen',
        ),
    ])


