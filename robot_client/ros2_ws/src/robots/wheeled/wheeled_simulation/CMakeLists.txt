cmake_minimum_required(VERSION 3.8)
project(wheeled_simulation)

find_package(ament_cmake REQUIRED)

# launch / rviz 配置 / 可选的仿真附加 xacro 都是资源文件。
install(
  DIRECTORY launch rviz urdf config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
