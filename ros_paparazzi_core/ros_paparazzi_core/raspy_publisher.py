# This is the node that will run on the raspberry

import threading
import time

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import NavSatFix
from ros_paparazzi_interfaces.msg import Waypoint

from ros_paparazzi_core.data import autopilot_data
from ros_paparazzi_core.paparazzi_receive import PPZI_TELEMETRY, TIME_THREAD
from ros_paparazzi_core.paparazzi_send import PPZI_DATALINK


# Variables globales
paparazzi_send = None
paparazzi_receive = None
time_thread = None


class Raspy_Publisher(Node):

    def __init__(self):
        super().__init__('Raspy_Publisher')
        self.publisher = self.create_publisher(Waypoint, 'telemetry_gps', 10)
        self.suscriber = self.create_subscription(Waypoint, 'datalink_gps', self.datalink_callback, 10)

        # Crear un hilo para monitorear cambios en telemetry_data
        self.last_telemetry_data = None
        self.last_home_data = None
        self.start_monitor_thread(autopilot_data.telemetry_data, self.telemetry_callback, self.last_telemetry_data)
        self.start_monitor_thread(autopilot_data.home_data, self.home_callback, self.last_home_data)

        # Clase para mandar datos por el puerto serie (datalink)
        port = "/dev/ttyUSB0"
        self.paparazzi_send = PPZI_DATALINK(port)
        self.paparazzi_send.run()


    # Funcion que manda los mensajes datalink por el puerto serie cuando los recibe del topic
    def datalink_callback(self, msg):

        lat = msg.position.latitude
        lon = msg.position.longitude
        alt = msg.position.altitude
        wp_id = msg.wp_id

        self.get_logger().info(f'Receiving data: [{lat*1e-07:.7f}, {lon*1e-07:.7f}]')
        autopilot_data.waypoint_data.update(lat, lon, alt, wp_id)
        self.paparazzi_send.send()
        

    # --------------------------------- FUNCIONES DE MONITOREO ---------------------------------
    # Esto se puede cambiar posiblemente

    # Funcion que publica en el topic los mensajes telemetry que recibe por el puerto serie
    def telemetry_callback(self, data):
        # data = [float(i) for i in data] # Hay que convertir los datos a Float64, que es lo que acepta NatSat
        msg = Waypoint()
        msg.position.header.stamp.sec = int(autopilot_data.tiempo)
        msg.position.header.stamp.nanosec = int(1e+9*(autopilot_data.tiempo - int(autopilot_data.tiempo)))
        msg.position.longitude = float(data.longitude*1e-07)
        msg.position.latitude = float(data.latitude*1e-07)
        msg.position.altitude = float(data.altitude/1000.0)
        msg.wp_id = 0
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing Telemetry_Data: [{msg.position.latitude:.7f}, {msg.position.longitude:.7f}, {msg.position.altitude:.2f}]')


    # Funcion que publica en el topic los mensajes home que recibe por el puerto serie
    def home_callback(self, data):
        msg = Waypoint()
        msg.position.header.stamp.sec = int(autopilot_data.tiempo)
        msg.position.header.stamp.nanosec = int(1e+9*(autopilot_data.tiempo - int(autopilot_data.tiempo)))
        msg.position.longitude = float(data.longitude*1e-07)
        msg.position.latitude = float(data.latitude*1e-07)
        msg.position.altitude = float(data.altitude/1000.0)
        msg.wp_id = 1

        self.get_logger().info(f'Home data changed: {data}')


    # Función para iniciar un hilo de monitoreo genérico
    def start_monitor_thread(self, variable, callback, last_value):
        monitor_thread = threading.Thread(
            target=self.monitor_variable, args=(variable, callback, last_value), daemon=True
        )
        monitor_thread.start()


    # Función genérica para monitorear cambios en cualquier variable
    def monitor_variable(self, variable, callback, last_value):
        
        # last_value = self.last_telemetry_data

        while True:
            current_value = variable.recover()
            
            if last_value is None:
                last_value = current_value

            if current_value != last_value:
                last_value = current_value
                callback(variable)

            time.sleep(0.1)

    


def main(args=None):

    global paparazzi_send, paparazzi_receive, time_thread
    rclpy.init(args=args)

    port = "/dev/ttyUSB0"

    # Lanza los hilos
    paparazzi_time = TIME_THREAD()
    time_thread = threading.Thread(target=paparazzi_time.run, args=(autopilot_data,))
    time_thread.start()

    paparazzi_receive = PPZI_TELEMETRY(port)
    receive_thread = threading.Thread(target=paparazzi_receive.run)
    receive_thread.start()

    # Lanza el nodo ROS
    raspy_ros_node = Raspy_Publisher()
    rclpy.spin(raspy_ros_node)

    raspy_ros_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()