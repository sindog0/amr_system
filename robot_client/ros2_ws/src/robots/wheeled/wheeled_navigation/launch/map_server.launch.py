import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    #获取地图路径
    map_file = os.path.join(
        get_package_share_directory('factory_simulation'),
        'maps',
        'factory_map.yaml'
    )

    #地图服务器
    map_server = Node(
        package= 'nav2_map_server',
        executable= 'map_server',
        name = 'map_server',
        output = 'screen',
        parameters=[{
            'use_sim_time': True,
            'yaml_filename': map_file 
        }]
    )

    #生命周期管理器
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='nav2_lifecycle_manager',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names':['map_server']
        }]
    )

    rviz_config = os.path.join(
        get_package_share_directory('wheeled_navigation'),
        'rviz',
        'navigation.rviz'
    )

    #启动rviz2 -d表示让rviz2加载指定的配置文件
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output ='screen',
        arguments=['-d',rviz_config]
    )

    return LaunchDescription([
        map_server,
        lifecycle_manager,
        rviz_node
    ])