from setuptools import find_packages, setup

package_name = 'ros_paparazzi_core'

setup(
    name=package_name,
        version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ucmrospy',
    description='Manage the communication with the Paparazzi AP',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
                'computer = ros_paparazzi_core.computer_suscriber:main',
                'raspy = ros_paparazzi_core.raspy_publisher:main',
                'send = ros_paparazzi_core.waypoint_sender:main',
                'telemetry = ros_paparazzi_core.telemetry_receiver:main',
        ],
    },
)
