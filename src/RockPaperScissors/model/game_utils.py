import random
import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import time
import csv
import os
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from shared.utils import CVAssets, Generics

#------------------------------------------------------------------------ Used in AI



def beats(n):
    if int(n) == 3:
        return int(1)
    else:
        return int(n)+1


def overlayPNG(imgBack, imgFront, pos=[0, 0]):
    hf, wf, cf = imgFront.shape
    hb, wb, cb = imgBack.shape
    if (pos[0] > wb or pos[1] > hb):  # prevent out of bounds overlays
        # print("Image not in view")
        return imgBack
    *_, mask = cv2.split(imgFront)
    maskBGRA = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGRA)
    maskBGR = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    imgRGBA = cv2.bitwise_and(imgFront, maskBGRA)
    imgRGB = cv2.cvtColor(imgRGBA, cv2.COLOR_BGRA2BGR)

    y1, y2 = max(0, pos[1]), min(hf + pos[1], hb)
    x1, x2 = max(0, pos[0]), min(wf + pos[0], wb)
    imgMaskFull = np.zeros((hb, wb, cb), np.uint8)
    # Adjusted MaskFull and MaskFull2 to function even if image is partially out of bounds
    imgMaskFull[y1:y2, x1:x2, :] = imgRGB[(y1 - pos[1]):(y2 - pos[1]), (x1 - pos[0]):(x2 - pos[0]), :]
    imgMaskFull2 = np.ones((hb, wb, cb), np.uint8) * 255
    maskBGRInv = cv2.bitwise_not(maskBGR)
    imgMaskFull2[y1:y2, x1:x2, :] = maskBGRInv[(y1 - pos[1]):(y2 - pos[1]), (x1 - pos[0]):(x2 - pos[0]), :]

    imgBack = cv2.bitwise_and(imgBack, imgMaskFull2)
    imgBack = cv2.bitwise_or(imgBack, imgMaskFull)
    return imgBack


def get_training_data(player_name):
    with open(CVAssets.CSV_ROCK_PAPER_SCISSORS, 'a+') as _:
        pass

    with open(CVAssets.CSV_ROCK_PAPER_SCISSORS, mode='r') as file:
        reader = csv.reader(file)
        try:
            next(reader)  # Skip header row
            moves = []
            for row in reader:
                if row[0] == player_name:
                    try:
                        player_move = int(row[1])  # Convert player's move to an integer
                        moves.append(player_move)
                    except Exception as e:
                        print(f"Skipped row due to invalid data: {e}")
            return moves[-7:]
        except StopIteration:
            return []


def get_model(player_name):
    last_moves = get_training_data(player_name)
    if len(last_moves) == 7:  # Only train if we have 7 moves
        X = np.array(last_moves[:-1]).reshape(1, -1)  # the features are the first 6 moves
        y = np.array(last_moves[-1]).reshape(1, )  # the target is the last move
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=2000)
        model.fit(X, y)
        return model, scaler
    else:
        return None, None


def get_ai_move(player1):
    model, scaler = get_model(player1)
    if model is not None:
        last_moves = get_training_data(player1)
        X = np.array(last_moves[:-1]).reshape(1, -1)
        X = scaler.transform(X)
        predicted_move = str(model.predict(X)[0])  # Store the predicted move as a string
        randomNumber = beats(model.predict(X)[0])
        print("Data received: " + str(get_training_data(player1)))
        print("Predicted: " + predicted_move)
    else:
        randomNumber = random.randint(1, 3)
        print("Model is not being used because of insufficient data.")
        predicted_move = str(randomNumber)  # Use the random number as the predicted move
    print("AI move =", randomNumber)
    return randomNumber, predicted_move  # Return both the random number and predicted move as a tuple


def get_player_move(handLeft, detectorLeft, player1):
    playerLeftMove = None
    playerLeftMoveName = ""
    fingersLeft = detectorLeft.fingersUp(handLeft[0])
    if fingersLeft == [0, 0, 0, 0, 0]:
        playerLeftMoveName = "Rock"
        playerLeftMove = 1
    if fingersLeft == [1, 1, 1, 1, 1]:
        playerLeftMoveName = "Paper"
        playerLeftMove = 2
    if fingersLeft == [0, 1, 1, 0, 0]:
        playerLeftMoveName = "Scissors"
        playerLeftMove = 3
    print(f"{player1} move = ", playerLeftMoveName)
    return playerLeftMove, playerLeftMoveName


def calculate_result_against_AI(playerLeftMove, randomNumber, scores, winStreak):
    # Player1 Wins
    if (playerLeftMove == 1 and randomNumber == 3) or \
            (playerLeftMove == 2 and randomNumber == 1) or \
            (playerLeftMove == 3 and randomNumber == 2):
        scores[1] += 1
        winStreak[1] += 1
        winStreak[0] = 0
        result = 1
    # Player2 (AI) Wins
    elif (playerLeftMove == 1 and randomNumber == 2) or \
            (playerLeftMove == 2 and randomNumber == 3) or \
            (playerLeftMove == 3 and randomNumber == 1):
        scores[0] += 1
        winStreak[0] += 1
        winStreak[1] = 0
        result = -1
    # Draw
    else:
        result = 0

    return result, scores, winStreak


def draw_ui_against_AI(player1, player2, scores, randomNumber, left_frame, right_frame, half_width, height):
    imgAI = cv2.imread(f'RockPaperScissors/assets/{randomNumber}.png', cv2.IMREAD_UNCHANGED)
    imgAI = cv2.flip(imgAI,1)
    x_offset = int((right_frame.shape[1] - imgAI.shape[1]) / 2)
    y_offset = int((right_frame.shape[0] - imgAI.shape[0]) / 2)
    left_frame = overlayPNG(left_frame, imgAI, [x_offset, y_offset])
    # Concatenate the left and right frames horizontally
    combined_frame = cv2.hconcat([left_frame, right_frame])

    # Flip the resulting image horizontally
    combined_frame = cv2.flip(combined_frame, 1)

    # Display player names on the frames
    #image, text, position, font_path, font_size, font_color, outline_color = (255, 255, 255), outline_width=2)
    combined_frame = Generics.put_text_with_custom_font(combined_frame, player1, (10,50), CVAssets.FONT_FRUIT_NINJA, 20 ,(255, 255, 255), outline_color=(0,0,0))
    combined_frame = Generics.put_text_with_custom_font(combined_frame, player2, (half_width+10, 50),CVAssets.FONT_FRUIT_NINJA, 20 , (255, 255, 255), outline_color=(0,0,0))
    combined_frame = Generics.put_text_with_custom_font(combined_frame, "Points: " + str(scores[1]), (10,100), CVAssets.FONT_FRUIT_NINJA, 20 ,(255, 255, 255), outline_color=(0,0,0))
    combined_frame = Generics.put_text_with_custom_font(combined_frame, "Points: " + str(scores[0]), (half_width+10, 100), CVAssets.FONT_FRUIT_NINJA, 20 ,(255, 255, 255), outline_color=(0,0,0))
    # cv2.putText(combined_frame, player1, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    # cv2.putText(combined_frame, player2, (half_width+10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    # cv2.putText(combined_frame, "Points: " + str(scores[1]), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    # cv2.putText(combined_frame, "Points: " + str(scores[0]), (half_width+10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.line(combined_frame, (half_width, 0), (half_width, height), (255,255,255), 1)

    return combined_frame

def save_to_csv(player_name, player_move, player_win_streak, prediction, AIMove):
    file_exists = os.path.isfile(CVAssets.CSV_ROCK_PAPER_SCISSORS)
    with open(CVAssets.CSV_ROCK_PAPER_SCISSORS, mode='a', newline='') as file:
        fieldnames = ['playerName', 'playerMove', 'playerWinStreak', 'prediction', 'AIMove']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  # Write header row only if the file doesn't exist
        writer.writerow({'playerName': player_name,
                         'playerMove': player_move,
                         'playerWinStreak': player_win_streak,
                         'prediction': prediction,
                         'AIMove': AIMove})
    if len(get_training_data(player_name)) > 7:
        get_model(player_name)



#------------------------------------------------------------------------ Used in players



def get_players_move(handLeft, detectorLeft, player1, handRight, detectorRight, player2):
    # Player left is actually player right but inverted
    playerLeftMove = None
    playerLeftMoveName = ""
    fingersLeft = detectorLeft.fingersUp(handLeft[0])
    if fingersLeft == [0, 0, 0, 0, 0]:
        playerLeftMoveName = "Rock"
        playerLeftMove = 1
    if fingersLeft == [1, 1, 1, 1, 1]:
        playerLeftMoveName = "Paper"
        playerLeftMove = 2
    if fingersLeft == [0, 1, 1, 0, 0]:
        playerLeftMoveName = "Scissors"
        playerLeftMove = 3
    print(f"{player1} move = ", playerLeftMoveName)

    # Player right is actually player left but inverted
    fingersRight = detectorRight.fingersUp(handRight[0])
    playerRightMove = None
    playerRightMoveName = ""
    if fingersRight == [0, 0, 0, 0, 0]:
        playerRightMoveName = "Rock"
        playerRightMove = 1
    if fingersRight == [1, 1, 1, 1, 1]:
        playerRightMoveName = "Paper"
        playerRightMove = 2
    if fingersRight == [0, 1, 1, 0, 0]:
        playerRightMoveName = "Scissors"
        playerRightMove = 3
    print(f"{player2} move = ", playerRightMoveName)
    return playerLeftMove, playerLeftMoveName, playerRightMove, playerRightMoveName

def draw_ui_against_players(scores, left_frame, right_frame, half_width, height):
    # Concatenate the left and right frames horizontally
    combined_frame = cv2.hconcat([left_frame, right_frame])

    # Flip the resulting image horizontally
    combined_frame = cv2.flip(combined_frame, 1)

    # Display player names on the frames
    cv2.putText(combined_frame, "Points: " + str(scores[0]), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(combined_frame, "Points: " + str(scores[1]), (half_width+10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.line(combined_frame, (half_width, 0), (half_width, height), (255,255,255), 1)

    return combined_frame

def calculate_results_against_players(playerLeftMove, playerRightMove, scores, player2, player1):
    # Player Right Wins
    if (playerLeftMove == 1 and playerRightMove == 3) or \
            (playerLeftMove == 2 and playerRightMove == 1) or \
            (playerLeftMove == 3 and playerRightMove == 2):
        scores[1] += 1
        print(f"{player2} Wins, Score = ", scores[1])

    # Player Left Wins
    elif (playerLeftMove == 3 and playerRightMove == 1) or \
            (playerLeftMove == 1 and playerRightMove == 2) or \
            (playerLeftMove == 2 and playerRightMove == 3):
        scores[0] += 1
        print(f"{player1} Wins, Score = ", scores[0])
    else:
        print("Bust, try again..")

    return scores

#------------------------------------------------------------------------ Used in both