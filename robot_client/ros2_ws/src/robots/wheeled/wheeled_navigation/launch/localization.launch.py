import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    #获取功能包路径
    simulation_dir = get_package_share_directory('factory_simulation')

    navigation_dir = get_package_share_directory('wheeled_navigation')

    map_file = os.path.join(
            get_package_share_directory('factory_simulation'),
            'maps',
            'factory_map.yaml'
        )

    amcl_config = os.path.join(
        navigation_dir, 'config', 'amcl.yaml'
        )

    rviz_config = os.path.join(
        navigation_dir, 'rviz', 'navigation.rviz'
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

    #AMCL定位节点
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output = 'screen',
        parameters=[amcl_config]
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
            'node_names':['map_server','amcl']
        }]
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
        amcl,
        lifecycle_manager,
        rviz_node
    ])