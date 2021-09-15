from setuptools import setup
from glob import glob

package_name = 'ntrip_client_ros'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/**')),
        ('share/' + package_name + '/params', glob('params/**')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kristoffer Bergman',
    maintainer_email='kribe606@gmail.com',
    description='NTRIP client for parsing RTCM messages to ROS2. Depends on the rtcm_msgs package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ntrip_client_node = ntrip_client_ros.ntrip_client_node:main',
        ],
    },
)
