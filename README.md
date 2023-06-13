# Computer Vision Dojo by Team Giraffe

Python Mini-Games Collection based on computer vision.

## Description

This project is a collection of four computer vision related mini-games implemented in Python 3.10. Each game showcases different aspects of artificial intelligence and utilizes popular AI libraries such as Mediapipe & YOLO. The games included in this collection are:

1. Fight Simulator with Mediapipe: This game uses the Mediapipe library to track hand movements and arm angles. It provides a fun and interactive way to test your punching skills.

2. AI Fruit Ninja with YOLOv8: In this game, the YOLO (You Only Look Once) object detection algorithm is employed to detect the player on the screen. Objects are then thrown at the player, and the player must use their hands or feet to slice the objects in half. This game is inspired by the popular mobile game Fruit Ninja.

![CVNinja Gif](https://i.imgur.com/WgdcTpN.gif)

3. Rock Paper Scissors Game: This game utilizes hand tracking to recognize and classify hand gestures as rock, paper, or scissors. You can play against a person or against an AI which is retrained after every round taking into account the last 7 moves of the certain player by name. After retraining, the model tries to predict the next move of the user which is then used by the artificial intelligence to try defeating its opponent (the player).

4. Warming Up Game: The warming up game is a game that can detect multiple players doing certain exercises. It includes a push-up counter that uses computer vision techniques to count push-ups semi-accurately. It has a rudimentary user interface.

## Prerequisites

Before running the games in this collection, ensure that you have the following:

- A camera capable of 60 Frames per second and a field of view of at least 100 degrees.
- 4GB of **free** RAM
- Windows 10 or 11 running on your machine (verified compatibilty ✔️)
- Nvidia GTX1050m GPU or higher
- [CUDA Toolkit 11.7](https://developer.nvidia.com/cuda-11-7-0-download-archive)
- [PyTorch for CUDA 11.7](https://pytorch.org/get-started/locally/)

## Installation

Clone the repository:

```bash
git clone https://github.com/662781/GiraffeAI
```
After cloning, navigate to the src directory using
```
cd GiraffeAI/src
```
**IMPORTANT:** Make sure to run the PyTorch install command from the provided link **BEFORE** you install the requirements.txt!     
Install the requirements:
```
pip install -r ./requirements.txt
```
Run the GameManager script from the src directory to start the application!
```
python ./GameManager.py
```

### Game-Specific Requirements

1. Fight Simulator with Mediapipe:
   - Position the camera: Ensure that your camera is positioned to capture your left side and is not too far away from you. This will provide optimal tracking for the punch simulation.

2. Rock Paper Scissors Game:
   - Hand positioning: Place your hands in front of the camera and make sure they are not too far away. This will help the hand tracking algorithm accurately recognize your gestures.

3. AI Fruit Ninja with YOLOv8:
   - Camera placement: Position the camera directly in front of you, facing the game area. A wide field of view is especially important for multiplayer, so that every player as enough room to kick and punch.  

4. Warming Up Game:
   - Position the camera so that all players are in view and no other people can disturb the detection of the AI model.

Note: These requirements are general guidelines to achieve the best experience while playing the games. Adjustments may be needed based on your specific setup and environment.
