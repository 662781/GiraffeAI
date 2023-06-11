# Giraffe AI

Python Mini-Games Collection

## Description

This project is a collection of four AI-related mini-games implemented in Python. Each game showcases different aspects of artificial intelligence and utilizes popular AI libraries such as Mediapipe, YOLO, and hand tracking. The games included in this collection are:

1. Punch Simulator with Mediapipe: This game uses the Mediapipe library to track hand movements and arm angles. It provides a fun and interactive way to test your punching skills.

2. AI Fruit Ninja with YOLO: In this game, the YOLO (You Only Look Once) object detection algorithm is employed to detect the player on the screen. Objects are then thrown at the player, and the player must use their hands or feet to slice the objects in half. This game is inspired by the popular mobile game Fruit Ninja.

3. Rock Paper Scissors Game with Hand Tracking: This game utilizes hand tracking to recognize and classify hand gestures as rock, paper, or scissors. You can play against the computer or against a friend.

4. Warmup Game with Push-Up Counter: The warmup game is designed to get your body moving. It includes a push-up counter that uses computer vision techniques to count your push-ups accurately. It's a great way to incorporate physical exercise into your coding routine if you spend a lot of time sitting at a desk.

## Installation

Clone the repository:

```bash
git clone https://github.com/662781/GiraffeAI
```


## Prerequisites

Before running the games in this collection, ensure that you have the following:

- A camera capable of 60 Frames per second and a fielf of view of at least 100 degrees.
- 4GB of free RAM
- Nvidia gtx 1050m or higher
- [Cuda 11.7](https://developer.nvidia.com/cuda-11-7-0-download-archive)
- [Pytorch for Cuda 11.7](https://pytorch.org/get-started/locally/)

### Game-Specific Requirements

1. Punch Simulator with Mediapipe:
   - Position the camera: Ensure that your camera is positioned to capture your left side and is not too far away from you. This will provide optimal tracking for the punch simulation.

2. Rock Paper Scissors Game with Hand Tracking:
   - Hand positioning: Place your hands in front of the camera and make sure they are not too far away. This will help the hand tracking algorithm accurately recognize your gestures.

3. AI Fruit Ninja with YOLO:
   - Camera placement: Position the camera directly in front of you, facing the game area. Wide field of view is especially important for multiplayer.  

4. Warmup Game with Push-Up Counter:
   - No specific requirements.

Note: These requirements are general guidelines to achieve the best experience while playing the games. Adjustments may be needed based on your specific setup and environment.



