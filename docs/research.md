
With the growing development of domestic robots and the ever-increasing use of robots in daily life, the need for more intuitive and natural Human-Robot Interaction (HRI) also rises. It is crucial to guarantee simple, casual human-robot interactions to ensure that robots are not only useful to advanced and technical people, but also to general users.

In an effort to provide an intuitive interface for HRI, we leveraged the reasoning capabilities of Large Language Models (LLMs) via [ROSA](https://github.com/nasa-jpl/rosa) to develop a robot agent, acting as a bridge between humans and robots. Our robot agent allows users to interact with robots via **text** and **voice** -based natural language commands. For instance, a user might say "_move forward for 1 second_", and the robot agent, coupled with our underlying behaviour tree architecture, will instruct the robot to do so, while taking into account the current environment of the robot.

Our project, the `robot_suite`, is an open-source project aiming at extending the capabilities of robotic platforms through advanced behaviours and reasoning. This is achieved by integrating the power and flexibility of behaviour trees with task-specific plugins. The natural language interface provided by our robot agent enhances the usability of the `robot_suite` by making it accessible to non-technical users.

For more information, please read the [entire paper](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=11261666).

---


## Citation

To cite this work, use

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
