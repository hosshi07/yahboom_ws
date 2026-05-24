from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'gui_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ts',
    maintainer_email='tosshi1229@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'arm_gui_node = gui_pkg.arm_gui_node:main',
            'voice_gui_node = gui_pkg.voice_gui_node:main',
            'yahboom_commander = gui_pkg.yahboom_commander:main',
        ],
    },
)
