from setuptools import find_packages, setup

package_name = "robot_agent"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Ines Pastor",
    maintainer_email="ines.pastor.001@student.uni.lu",
    description="An LLM Agent for robot_suite built on ROSA",
    license="GPL-3.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "robot_agent_node = robot_agent.llm_agent:main",
        ],
    },
)
