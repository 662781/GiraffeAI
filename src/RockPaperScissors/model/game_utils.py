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


# This function takes an integer n as input and returns n+1 if n is not equal to 3, otherwise, it returns 1.
def beats(n):
    if int(n) == 3:
        return int(1)
    else:
        return int(n)+1


#This function overlays the imgFront image on top of the imgBack image at the specified position pos.
# It handles transparency by using an alpha channel in the imgFront image.
# The resulting image is returned.
def overlayPNG(imgBack, imgFront, pos=[0, 0]):
    hf, wf, cf = imgFront.shape
    hb, wb, cb = imgBack.shape
    if (pos[0] > wb or pos[1] > hb):  # prevent out of bounds overlays
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


#This function retrieves training data from a CSV file (CVAssets.CSV_ROCK_PAPER_SCISSORS) for a specific player (player_name).
# It reads the CSV file, skips the header row, and collects the player's moves from the CSV file.
# It returns the last 7 moves of the player as a list.
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


#This function retrieves the training data for a player using get_training_data(player_name).
# If the length of the training data is 7, it preprocesses the data, creates a model (MLPClassifier), and fits the model to the data.
# It returns the trained model and the scaler used for preprocessing.
# If the length of the training data is not 7, it returns None for both the model and scaler.
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


#This function obtains the model and scaler for player1 using get_model(player1).
# If the model is available, it retrieves the last moves of player1 and predicts the next move using the model.
# If the model is not available (insufficient data), it generates a random move.
# It prints the received data and the predicted move.
# It returns the randomly generated move and the predicted move as a tuple.
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
    print("AI move = ", randomNumber)
    return randomNumber, predicted_move  # Return both the random number and predicted move as a tuple


#This function determines the move made by player1 based on the positions of the fingers detected by the hand detector (detectorLeft).
# It assigns a move code (1, 2, or 3) based on the finger configuration.
# It returns the move code and the corresponding move name.
def get_player_move(handLeft, detectorLeft, player1):
    playerLeftMove = None
    playerLeftMoveName = ""
    fingersLeft = detectorLeft.fingersUp(handLeft[0])
    if fingersLeft == [0, 0, 0, 0, 0]:
        playerLeftMoveName = "Rock"
        playerLeftMove = 1
    elif fingersLeft == [1, 1, 1, 1, 1]:
        playerLeftMoveName = "Paper"
        playerLeftMove = 2
    elif fingersLeft == [0, 1, 1, 0, 0]:
        playerLeftMoveName = "Scissors"
        playerLeftMove = 3
    else:
        playerLeftMoveName = "Wrong selection!"
    print(f"Player '{player1}' move = ", playerLeftMoveName)
    return playerLeftMove, playerLeftMoveName


#This function calculates the result of the game between the player (playerLeftMove) and the AI (randomNumber).
# It updates the scores and win streaks based on the result.
# It returns the result, updated scores, and win streaks.
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

#This function draws the UI for the game against the AI.
# It overlays the AI move image on the left frame and combines it with the right frame.
# It displays player names, scores, and a dividing line on the combined frame.
# The resulting frame is returned.
def draw_ui_against_AI(player1, player2, scores, randomNumber, left_frame, right_frame, half_width, height, handText, display_fps):
    imgAI = cv2.imread(f'RockPaperScissors/assets/{randomNumber}.png', cv2.IMREAD_UNCHANGED)
    x_offset = int((right_frame.shape[1] - imgAI.shape[1]) / 2)
    y_offset = int((right_frame.shape[0] - imgAI.shape[0]) / 2)
    left_frame = overlayPNG(left_frame, imgAI, [x_offset, y_offset])

    # Concatenate the left and right frames horizontally
    combined_frame = cv2.hconcat([left_frame, right_frame])

    # Display FPS
    # cv2.putText(combined_frame, "FPS:" + str(display_fps), (460, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2,cv2.LINE_AA)

    # Display player names on the frames
    #image, text, position, font_path, font_size, font_color, outline_color = (255, 255, 255), outline_width=2)
    combined_frame = Generics.put_text_with_custom_font(combined_frame, player2, (10,50), CVAssets.FONT_FRUIT_NINJA, 20 ,(255, 255, 255), outline_color=(0,0,0))
    combined_frame = Generics.put_text_with_custom_font(combined_frame, player1, (half_width+10, 50),CVAssets.FONT_FRUIT_NINJA, 20 , (255, 255, 255), outline_color=(0,0,0))
    combined_frame = Generics.put_text_with_custom_font(combined_frame, "Points: " + str(scores[0]), (10,100), CVAssets.FONT_FRUIT_NINJA, 20 ,(255, 255, 255), outline_color=(0,0,0))
    combined_frame = Generics.put_text_with_custom_font(combined_frame, "Points: " + str(scores[1]), (half_width+10, 100), CVAssets.FONT_FRUIT_NINJA, 20 ,(255, 255, 255), outline_color=(0,0,0))

    # Display detected hand
    if handText == "None":
        combined_frame = Generics.put_text_with_custom_font(combined_frame, "Hand: " + handText,(half_width + 150, 100), CVAssets.FONT_FRUIT_NINJA, 20,(0, 0, 255), outline_color=(0, 0, 0))
    else:
        combined_frame = Generics.put_text_with_custom_font(combined_frame, "Hand: " + handText,(half_width + 150, 100), CVAssets.FONT_FRUIT_NINJA, 20,(0, 255, 0), outline_color=(0, 0, 0))

    cv2.line(combined_frame, (half_width, 0), (half_width, height), (255,255,255), 1)

    return combined_frame

#This function saves game data (player name, move, win streak, prediction, and AI move) to a CSV file (CVAssets.CSV_ROCK_PAPER_SCISSORS).
# If the file doesn't exist, it creates a new file with a header row.
# If the player's training data exceeds 7 moves, it updates the model for that player.
def save_to_csv(player_name, player_move, player_win_streak, prediction, AIMove):
    if player_move in [1, 2, 3]:
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



#This function determines the moves made by both players based on the positions of their fingers detected by the respective hand detectors.
# It assigns move codes (1, 2, or 3) based on the finger configurations of both players.
# It returns the move codes and corresponding move names for both players.
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
    print(f"Player '{player1}' move = ", playerLeftMoveName)

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
    print(f"Player '{player2}' move = ", playerRightMoveName)
    return playerLeftMove, playerLeftMoveName, playerRightMove, playerRightMoveName

#This function draws the UI for the game between two players.
# It combines the left and right frames, displays the scores, and adds a dividing line.
# The resulting combined frame is returned.
def draw_ui_against_players(scores, left_frame, right_frame, half_width, height, handLeftText, handRightText, display_fps):
    # Concatenate the left and right frames horizontally
    combined_frame = cv2.hconcat([left_frame, right_frame])

    # Display FPS
    #cv2.putText(combined_frame, "FPS:" + str(display_fps), (460, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2,cv2.LINE_AA)

    # Display player names on the frames
    combined_frame = Generics.put_text_with_custom_font(combined_frame, "Points: " + str(scores[1]), (10, 50),CVAssets.FONT_FRUIT_NINJA, 20, (255, 255, 255),outline_color=(0, 0, 0))
    combined_frame = Generics.put_text_with_custom_font(combined_frame, "Points: " + str(scores[0]),(half_width + 10, 50), CVAssets.FONT_FRUIT_NINJA, 20,(255, 255, 255), outline_color=(0, 0, 0))

    # Display detected hands
    if handLeftText == "None":
        combined_frame = Generics.put_text_with_custom_font(combined_frame, "Hand: " + handLeftText,(150, 50), CVAssets.FONT_FRUIT_NINJA, 20,(0, 0, 255), outline_color=(0, 0, 0))
    else:
        combined_frame = Generics.put_text_with_custom_font(combined_frame, "Hand: " + handLeftText,(150, 50), CVAssets.FONT_FRUIT_NINJA, 20,(0, 255, 0), outline_color=(0, 0, 0))
    if handRightText == "None":
        combined_frame = Generics.put_text_with_custom_font(combined_frame, "Hand: " + handRightText,(half_width + 150, 50), CVAssets.FONT_FRUIT_NINJA, 20,(0, 0, 255), outline_color=(0, 0, 0))
    else:
        combined_frame = Generics.put_text_with_custom_font(combined_frame, "Hand: " + handRightText,(half_width + 150, 50), CVAssets.FONT_FRUIT_NINJA, 20,(0, 255, 0), outline_color=(0, 0, 0))




    cv2.line(combined_frame, (half_width, 0), (half_width, height), (255,255,255), 1)

    return combined_frame

#This function calculates the result of the game between two players (player1 and player2) based on their moves (playerLeftMove and playerRightMove).
# It updates the scores based on the result.
# It returns the updated scores.
def calculate_results_against_players(playerLeftMove, playerRightMove, scores, player2, player1):
    # Player Right Wins
    if (playerLeftMove == 1 and playerRightMove == 3) or \
            (playerLeftMove == 2 and playerRightMove == 1) or \
            (playerLeftMove == 3 and playerRightMove == 2):
        scores[1] += 1
        print(f"Player '{player1}' Wins, Score = ", scores[1])

    # Player Left Wins
    elif (playerLeftMove == 3 and playerRightMove == 1) or \
            (playerLeftMove == 1 and playerRightMove == 2) or \
            (playerLeftMove == 2 and playerRightMove == 3):
        scores[0] += 1
        print(f"Player '{player2}' Wins, Score = ", scores[0])
    else:
        print("Bust, try again..")

    return scores

#------------------------------------------------------------------------ Used in both



def mirror_hands(hand):
    if str(hand[0]['type']) == "Left":
        handtext = "Right"
    elif str(hand[0]['type']) == "Right":
        handtext = "Left"
    else:
        handtext = "None"

    return handtext