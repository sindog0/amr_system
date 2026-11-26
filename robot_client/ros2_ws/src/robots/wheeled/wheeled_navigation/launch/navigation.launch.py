import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory('wheeled_navigation'),
        'config',
        'nav2_params.yaml'
    )

    #1.全局路径规划
    planner = Node(
        package='nav2_planner',
        executable='planner_server',
        name = 'planner_server',
        output = 'screen',
        parameters=[params_file]
    )

    #2.路径跟踪控制
    controller = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file]
    )

    #3.路径平滑
    smoother = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[params_file]
    )

    #4.行为服务器
    behavior = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[params_file]
    )

    #5.行为树导航
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[params_file]
    )

    #6生命周期管理
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names':[
                'planner_server',
                'controller_server',
                'smoother_server',
                'behavior_server',
                'bt_navigator'
            ]
        }]

    )

    return LaunchDescription([
        planner,
        controller,
        smoother,
        behavior,
        bt_navigator,
        lifecycle_manager
    ])
    