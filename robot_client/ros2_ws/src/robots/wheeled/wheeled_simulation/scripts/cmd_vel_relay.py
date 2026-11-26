#!/usr/bin/env python3
"""把 /cmd_vel (geometry_msgs/Twist) 转成差速控制器要的 TwistStamped。

为什么需要它：
  Jazzy 的 diff_drive_controller 只订阅 geometry_msgs/msg/TwistStamped
  （话题 /diff_drive_controller/cmd_vel），而 teleop_twist_keyboard、Nav2
  早期插件、很多教程发布的是 geometry_msgs/msg/Twist 到 /cmd_vel。
  话题名和消息类型都不匹配，所以轮子不动。本节点做协议转换：

      /cmd_vel (Twist)  ->  /diff_drive_controller/cmd_vel (TwistStamped)

  header.stamp 用节点时钟（launch 里 use_sim_time=true，所以是仿真时间），
  否则控制器的 cmd_vel_timeout 会认为指令过期并刹车。
"""

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node


class CmdVelRelay(Node):

    def __init__(self):
        super().__init__('cmd_vel_relay')
        self.declare_parameter('frame_id', 'base_link')
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic', '/diff_drive_controller/cmd_vel')

        in_topic = self.get_parameter('input_topic').value
        out_topic = self.get_parameter('output_topic').value

        self.publisher = self.create_publisher(TwistStamped, out_topic, 10)
        self.subscription = self.create_subscription(
            Twist, in_topic, self.callback, 10)

        self.get_logger().info(f'relay: {in_topic} (Twist) -> '
                               f'{out_topic} (TwistStamped)')

    def callback(self, msg):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.get_parameter('frame_id').value
        out.twist = msg
        self.publisher.publish(out)


def main():
    rclpy.init()
    node = CmdVelRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
