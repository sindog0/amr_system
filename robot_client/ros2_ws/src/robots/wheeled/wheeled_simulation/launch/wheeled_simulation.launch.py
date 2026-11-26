import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    RegisterEventHandler,
    EmitEvent
)

from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import(
    LaunchConfiguration,
    Command,
    FindExecutable
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    #1 获取机器人描述包路径
    simulation_share = get_package_share_directory(
        'wheeled_simulation'
    )

    #2 默认文件路径
    default_model = os.path.join(
        simulation_share,
        'urdf',
        'wheeled_robot.sim.urdf.xacro'
    )

    bridge_config = os.path.join(
        simulation_share,
        'config',
        'bridge.yaml'
    )

    model = LaunchConfiguration('model')
    world_name = LaunchConfiguration('world_name')

    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    spawn_z = LaunchConfiguration('spawn_z')
    spawn_yaw = LaunchConfiguration('spawn_yaw')

    #3 声明启动参数
    declare_model = DeclareLaunchArgument(
        'model',
        default_value=default_model,
        description='robot URDF/Xacro file'
    )

    declare_model_name = DeclareLaunchArgument(
        'model_name',
        default_value= 'default',
        description='gazebo world name'
    )

    declare_spawn_x = DeclareLaunchArgument(
        'spawn_x',
        default_value='0.0'
    )

    declare_spawn_y = DeclareLaunchArgument(
        'spawn_y',
        default_value='0.0'
    )

    declare_spawn_z = DeclareLaunchArgument(
        'spawn_z',
        default_value='0.02'
    )

    declare_spawn_yaw = DeclareLaunchArgument(
        'spawn_yaw',
        default_value='0.0'
    )




    #4 解析机器人描述
    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'),
            ' ',
            model
        ]),
        value_type=str
    )


    #5 启动robot_state_publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }]
        
    )

    #6 启动传感器桥接
    sensor_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='sensor_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_config
        }]
    )


    #7 将机器人生成到gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_robot',
        output='screen',
        arguments=[
            '-topic', '/robot_description',
            '-name', 'wheeled_robot',
            '-x', spawn_x,
            '-y', spawn_y,
            '-z', spawn_z,
            '-Y', spawn_yaw
        ]
    )

    #8 关节状态广播器
    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        name='joint_state_broadcaster_spawner',
        output='screen',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager',
            '/controller_manager',
            '--controller-manager-timeout',
            '120'
        ]
    )

    #9 差速驱动控制器
    diff_drive_controller =Node(
        package='controller_manager',
        executable='spawner',
        name='diff_drive_controller_spawner',
        output='screen',
        arguments=[
            'diff_drive_controller',
            '--controller-manager',
            '/controller_manager',
            '--controller-manager-timeout',
            '120'
        ]
    )

    #10 控制器启动事件

    def after_spawn(event, context):
        if event.returncode == 0:
            print('Robot spawned successfully.')
            return [joint_state_broadcaster]
        return [
            EmitEvent(
                event=Shutdown(
                    reason='Failed to spawn robot.'
                )
            )
        ]

    def after_joint_state(event, context):
        if event.returncode == 0:
            print('Joint state broadcaster activated.')
            return [diff_drive_controller]
        return [
            EmitEvent(
                event=Shutdown(
                    reason='Failed to start joint_state_broadcaster.'
                )
            )
        ]     

    spawn_event = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=after_spawn
        )
    )

    joint_state_event = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=after_joint_state
        )
    )

    return LaunchDescription([
        declare_model,
        declare_model_name,
        declare_spawn_x,
        declare_spawn_y,
        declare_spawn_z,
        declare_spawn_yaw,

        robot_state_publisher,

        sensor_bridge,

        spawn_event,
        joint_state_event,

        spawn_robot
    ])