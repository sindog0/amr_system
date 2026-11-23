#!/usr/bin/env python3
"""把 ROS 2D 占据栅格地图（PGM + YAML）转成 Gz Sim 世界。

为什么需要转换：
  .pgm/.yaml 是 Nav2/AMCL 用的二维占据栅格，Gazebo 不认识这种文件；
  Gazebo 需要的是三维几何（SDF）。这里把“占据”像素变成 3D 墙体盒子，
  于是 Gazebo 的碰撞、激光、相机和 Nav2 的地图在同一个坐标系里对齐。

坐标约定（很重要）：
  ROS 地图 YAML 的 origin 是「左下角像素在地图坐标系中的位姿」；
  PGM 第 0 行是图像顶部（y 最大）。本脚本按此把像素换算到地图坐标系，
  生成的 Gazebo 世界坐标 x/y 与 ROS 的 map 坐标系完全一致。

用法：
  python3 scripts/map_to_world.py \
      --map-yaml maps/factory_map.yaml \
      --output worlds/factory_map.sdf \
      --wall-height 1.5

  # 未知区域（YAML 里 205 灰度）默认当空地；如果希望未知也当墙：
  #   --unknown wall
"""

import argparse
import os
import sys

import yaml


def read_pgm(path):
    """读 P5 二进制 PGM，返回 (width, height, maxval, bytes)。"""
    with open(path, 'rb') as f:
        data = f.read()

    tokens = []
    i = 0
    while len(tokens) < 4:
        while i < len(data) and data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b'#':
            while i < len(data) and data[i:i + 1] not in b'\r\n':
                i += 1
            continue
        j = i
        while j < len(data) and not data[j:j + 1].isspace():
            j += 1
        tokens.append(data[i:j])
        i = j

    magic = tokens[0]
    if magic != b'P5':
        raise ValueError(f'只支持 P5 二进制 PGM，实际是 {magic!r}')
    width, height, maxval = int(tokens[1]), int(tokens[2]), int(tokens[3])
    i += 1  # 跳过 maxval 后的单个空白
    pixels = data[i:i + width * height]
    if len(pixels) != width * height:
        raise ValueError('PGM 像素数据长度不符')
    return width, height, maxval, pixels


def classify(value, maxval, negate, occupied_thresh, free_thresh):
    """按 ROS map_server 规则返回 'occupied' / 'free' / 'unknown'。"""
    v = value * 255.0 / maxval
    occ_prob = (255.0 - v) / 255.0 if not negate else v / 255.0
    if occ_prob > occupied_thresh:
        return 'occupied'
    if occ_prob < free_thresh:
        return 'free'
    return 'unknown'


def occupied_grid(pixels, width, height, maxval, negate,
                  occupied_thresh, free_thresh, unknown_as_wall):
    grid = []
    for r in range(height):
        row = []
        base = r * width
        for c in range(width):
            kind = classify(pixels[base + c], maxval, negate,
                            occupied_thresh, free_thresh)
            if kind == 'occupied':
                row.append(True)
            elif kind == 'unknown':
                row.append(unknown_as_wall)
            else:
                row.append(False)
        grid.append(row)
    return grid


def merge_rectangles(grid, width, height):
    """逐行做游程编码，再把上下相邻且区间完全相同的游程合并成矩形。

    返回 [(row_start, row_end, col_start, col_end), ...]（闭区间）。
    这样几万个像素变成几百个盒子，Gazebo 才跑得动。
    """
    rectangles = []
    active = {}  # (col_start, col_end) -> row_start

    for r in range(height):
        current = set()
        c = 0
        row = grid[r]
        while c < width:
            if row[c]:
                start = c
                while c < width and row[c]:
                    c += 1
                current.add((start, c - 1))
            else:
                c += 1

        for interval in list(active):
            if interval not in current:
                rectangles.append((active.pop(interval), r - 1,
                                   interval[0], interval[1]))
        for interval in current:
            active.setdefault(interval, r)

    for interval, row_start in active.items():
        rectangles.append((row_start, height - 1, interval[0], interval[1]))
    return rectangles


def rect_to_pose(rect, width, height, resolution, origin):
    """把像素矩形换算成世界坐标中心与尺寸。"""
    r0, r1, c0, c1 = rect
    ncols = c1 - c0 + 1
    nrows = r1 - r0 + 1

    x = origin[0] + (c0 + ncols / 2.0) * resolution
    # 第 r 行像素中心的 y：origin_y + (height - 0.5 - r) * resolution
    y = origin[1] + (height - 0.5 - (r0 + r1) / 2.0) * resolution
    return x, y, ncols * resolution, nrows * resolution


def render_world(world_name, rectangles, width, height, resolution, origin,
                 wall_height, map_yaml, source_rel):
    lines = []
    add = lines.append

    add('<?xml version="1.0" ?>')
    add('<!--')
    add('  由 factory_simulation/scripts/map_to_world.py 自动生成，请勿手工编辑。')
    add(f'  来源地图: {source_rel}')
    add(f'  分辨率: {resolution} m/px, 尺寸: {width} x {height} px')
    add(f'  origin: [{origin[0]}, {origin[1]}, {origin[2]}]')
    add(f'  墙体: {len(rectangles)} 个盒子, 高度 {wall_height} m')
    add('  坐标系与 ROS map 坐标系一致（x/y 直接对应）。')
    add('-->')
    add('<sdf version="1.9">')
    add(f'  <world name="{world_name}">')
    add('')
    add('    <physics name="1ms" type="ignored">')
    add('      <max_step_size>0.001</max_step_size>')
    add('      <real_time_factor>1.0</real_time_factor>')
    add('    </physics>')
    add('')
    add('    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>')
    add('    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>')
    add('    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>')
    add('    <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>')
    add('')
    add('    <!-- 渲染类传感器（lidar/camera）必需 -->')
    add('    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">')
    add('      <render_engine>ogre2</render_engine>')
    add('    </plugin>')
    add('    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>')
    add('')
    add('    <light type="directional" name="sun">')
    add('      <cast_shadows>true</cast_shadows>')
    add('      <pose>0 0 10 0 0 0</pose>')
    add('      <diffuse>0.8 0.8 0.8 1</diffuse>')
    add('      <specular>0.2 0.2 0.2 1</specular>')
    add('      <attenuation>')
    add('        <range>1000</range><constant>0.9</constant>')
    add('        <linear>0.01</linear><quadratic>0.001</quadratic>')
    add('      </attenuation>')
    add('      <direction>-0.5 0.1 -0.9</direction>')
    add('    </light>')
    add('')
    add('    <model name="ground_plane">')
    add('      <static>true</static>')
    add('      <link name="link">')
    add('        <collision name="collision">')
    add('          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>')
    add('        </collision>')
    add('        <visual name="visual">')
    add('          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>')
    add('          <material><ambient>0.8 0.8 0.8 1</ambient>'
        '<diffuse>0.8 0.8 0.8 1</diffuse><specular>0.8 0.8 0.8 1</specular></material>')
    add('        </visual>')
    add('      </link>')
    add('    </model>')
    add('')
    add('    <!-- 地图墙体：一个静态 link 下挂所有 collision/visual -->')
    add('    <model name="map_walls">')
    add('      <static>true</static>')
    add('      <link name="walls">')

    for i, rect in enumerate(rectangles):
        x, y, sx, sy = rect_to_pose(rect, width, height, resolution, origin)
        z = wall_height / 2.0
        add(f'        <collision name="wall_col_{i}">')
        add(f'          <pose>{x:.4f} {y:.4f} {z:.4f} 0 0 0</pose>')
        add(f'          <geometry><box><size>{sx:.4f} {sy:.4f} {wall_height:.4f}</size></box></geometry>')
        add('        </collision>')
        add(f'        <visual name="wall_vis_{i}">')
        add(f'          <pose>{x:.4f} {y:.4f} {z:.4f} 0 0 0</pose>')
        add(f'          <geometry><box><size>{sx:.4f} {sy:.4f} {wall_height:.4f}</size></box></geometry>')
        add('          <material>')
        add('            <ambient>0.6 0.6 0.6 1</ambient>')
        add('            <diffuse>0.6 0.6 0.6 1</diffuse>')
        add('          </material>')
        add('        </visual>')

    add('      </link>')
    add('    </model>')
    add('')
    add('  </world>')
    add('</sdf>')
    return '\n'.join(lines) + '\n'


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pkg_dir = os.path.dirname(here)
    if not os.path.isdir(os.path.join(pkg_dir, 'maps')):
        # 安装后运行时（share/factory_simulation），从 ament 索引取包目录
        from ament_index_python.packages import get_package_share_directory
        pkg_dir = get_package_share_directory('factory_simulation')

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--map-yaml',
                        default=os.path.join(pkg_dir, 'maps', 'factory_map.yaml'))
    parser.add_argument('--output',
                        default=os.path.join(pkg_dir, 'worlds', 'factory_map.sdf'))
    parser.add_argument('--world-name', default='factory_map')
    parser.add_argument('--wall-height', type=float, default=1.5,
                        help='墙体高度（米）')
    parser.add_argument('--unknown', choices=['free', 'wall'], default='free',
                        help='未知区域按空地还是墙处理')
    args = parser.parse_args()

    with open(args.map_yaml) as f:
        meta = yaml.safe_load(f)

    image_path = meta['image']
    if not os.path.isabs(image_path):
        image_path = os.path.join(os.path.dirname(args.map_yaml), image_path)

    resolution = float(meta.get('resolution', 0.05))
    origin = list(meta.get('origin', [0.0, 0.0, 0.0]))
    if len(origin) > 2 and abs(float(origin[2])) > 1e-6:
        print(f'警告: map origin yaw={origin[2]} 未处理，按 0 生成墙体；'
              '如需支持请先旋转地图或扩展本脚本', file=sys.stderr)
    negate = int(meta.get('negate', 0))
    occupied_thresh = float(meta.get('occupied_thresh', 0.65))
    free_thresh = float(meta.get('free_thresh', 0.196))

    width, height, maxval, pixels = read_pgm(image_path)
    grid = occupied_grid(pixels, width, height, maxval, negate,
                         occupied_thresh, free_thresh,
                         unknown_as_wall=(args.unknown == 'wall'))
    occupied_count = sum(sum(row) for row in grid)
    rectangles = merge_rectangles(grid, width, height)

    source_rel = os.path.relpath(args.map_yaml, pkg_dir)
    text = render_world(args.world_name, rectangles, width, height,
                        resolution, origin, args.wall_height,
                        args.map_yaml, source_rel)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(text)

    print(f'地图: {width}x{height} px @ {resolution} m/px '
          f'-> {width * resolution:.2f} x {height * resolution:.2f} m')
    print(f'占据像素: {occupied_count}，合并为 {len(rectangles)} 个墙体盒子')
    print(f'已生成: {args.output}')


if __name__ == '__main__':
    sys.exit(main())
