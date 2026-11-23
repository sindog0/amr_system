"""RViz2 显示：只启动 robot_state_publisher + joint_state_publisher + rviz2。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description_share = FindPackageShare('wheeled_description')
    simulation_share = FindPackageShare('wheeled_simulation')

    xacro_file = PathJoinSubstitution(
        [description_share, 'urdf', 'wheeled_robot.urdf.xacro'])
    rviz_config = PathJoinSubstitution(
        [simulation_share, 'rviz', 'wheeled.rviz'])

    # 注意：不加 use_gazebo_classic:=true 时，Gazebo Classic 插件不会展开，
    # RViz 只使用纯 URDF 几何/惯性。
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]), value_type=str)

    jsp_gui = LaunchConfiguration('jsp_gui')
    use_rviz = LaunchConfiguration('rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'jsp_gui', default_value='false',
            description='用 joint_state_publisher_gui 拖动关节（需已安装该包）'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='是否启动 RViz2'),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen',
        ),
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            condition=UnlessCondition(jsp_gui),
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            condition=IfCondition(jsp_gui),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            condition=IfCondition(use_rviz),
            output='screen',
        ),
    ])
