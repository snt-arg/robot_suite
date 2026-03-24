# Robot Suite

> [!IMPORTANT]
> This project is still a work in progress, so expect some bugs! If you encounter any, please open an issue or submit a PR with a fix.
> This suite has been ported from the `tello_suite` project, so some names may not have been fully updated to reflect the new `robot_...` naming convention.

Robot Suite is a collection of ROS2 packages designed to enhance the capabilities of robots,
making them more innovative and more versatile. The suite utilizes a series of plugins—ROS2 packages with
specialized features—to extend the robot's functionality. While each plugin can operate independently,
the primary goal of the suite is to integrate with the robot_bt package, which enables complex
behaviors by orchestrating the execution of multiple plugins.

A key principle of this project is robot agnosticism. This means that the combination
of these plugin packages is designed to work across any robot platform, including both
ground and aerial robots. As such, there is no robot-specific package, such as a dedicated robot driver.
Instead, we leverage ROS' standard interfaces, using middleware and configuration files to ensure compatibility.
For instance, these configuration files allow plugins to subscribe to the appropriate topics for the robot in use.

The suite also includes a Dockerfile for easy setup, eliminating the need to install dependencies
on your computer and simplifying the process of switching between different robot platforms.
For more information, refer to the Docker page.

## Documentation

**Documentation can be found [here](https://snt-arg.github.io/robot_suite).**

Additionally, the documentation can be viewed locally using the following options:

1.  With docker: `docker run --rm -it -p 8000:8000 -v ${PWD}:/docs squidfunk/mkdocs-material`.
2.  With python: First install material mkdocs with `pip install mkdocs-material`. Then, to preview the documentation run `mkdocs serve`.

> [!NOTE]
> The documentation should become available on [http://localhost:8000](http://localhost:8000)


## 📚 Citation
- **Explore the research behind this repository -->** [Link to the paper](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=11261666)
- **Cite this work:**  
```bibtex
@article{robotsuite2025,
  title={Interpretable Robot Control via Structured Behavior Trees and Large Language Models},
  author={Chekam, Ingrid Maéva and Pastor-Martinez, Ines and Tourani, Ali and Millan-Romera, Jose Andres and Ribeiro, Laura and Soares, Pedro Miguel Bastos and Voos, Holger and Sanchez-Lopez, Jose Luis},
  journal={IEEE Access},
  year={2025},
  volume={13},
  pages={200905-200916},
  doi={10.1109/ACCESS.2025.3635471},
  link={https://doi.org/10.1109/ACCESS.2025.3635471}
}
```
