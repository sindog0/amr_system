cmake_minimum_required(VERSION 3.8)
project(factory_simulation)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY worlds launch maps
  DESTINATION share/${PROJECT_NAME}
)

# 开发期工具：PGM/YAML -> SDF
install(
  PROGRAMS scripts/map_to_world.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
