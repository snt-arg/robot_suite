from setuptools import find_packages, setup

package_name = 'robot_capabilities'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Pedro Soares',
    maintainer_email='pedro.bastos@uni.lu',
    description='TODO: Package description',
    license='GPL-3.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'robot_capabilities = robot_capabilities.robot_capabilities:main'
        ],
    },
)
