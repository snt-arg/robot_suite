from setuptools import find_packages, setup
import os
from glob import glob

package_name = "sign_filter_plugin"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.py")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="maeri",
    maintainer_email="maevachekma@gmail.com",
    description="Package to filter out sign that do not come from the target person",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "sign_filter_node = sign_filter_plugin.sign_filter:main",
            "tello_sign_interpreter_node = sign_filter_plugin.tello_sign_interpreter:main",
        ],
    },
)
