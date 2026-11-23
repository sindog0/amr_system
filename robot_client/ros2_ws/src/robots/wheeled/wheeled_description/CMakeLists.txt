cmake_minimum_required(VERSION 3.8)
project(wheeled_description)

find_package(ament_cmake REQUIRED)

# 纯资源包：只安装 xacro 与 mesh，不编译代码、不引入其他包依赖。
install(
  DIRECTORY urdf meshes
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
