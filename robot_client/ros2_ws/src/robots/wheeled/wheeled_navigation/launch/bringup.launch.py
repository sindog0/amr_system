import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    simulation_dir = get_package_share_directory('factory_simulation')
    navigation_dir = get_package_share_directory('wheeled_navigation')

    #启动仿真
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(simulation_dir,'launch','factory_simulation.launch.py')
        )
    )

    #启动定位
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(navigation_dir, 'launch', 'localization.launch.py')
        )
    )

    # 启动导航
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(navigation_dir, 'launch', 'navigatoin.launch.py')
        )
    )

    return LaunchDescription([
        simulation,
        TimerAction(period=5.0, actions=[localization]),
        TimerAction(period=10.0, actions=[navigation])
    ])
    #等待5s后启动localization 10s后启动navigation 但是机器不同性能不同，下一步优化为事件驱动