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
    """
    Returns the next number in a sequence based on the given number.

    Parameters:
        n (int): The input number.

    Returns:
        int: The next number in the sequence.

    Example:
        >>> beats(3)
        1
        >>> beats(2)
        3
    """
    if int(n) == 3:
        return int(1)
    else:
        return int(n)+1


def overlayPNG(imgBack, imgFront, pos=[0, 0]):
    """
    Overlays the `imgFront` image on top of the `imgBack` image at the specified position `pos`.
    Handles transparency by using an alpha channel in the `imgFront` image.

    Parameters:
        imgBack (numpy.ndarray): The background image.
        imgFront (numpy.ndarray): The foreground image to be overlaid.
        pos (list[int, int]): The position at which the `imgFront` image should be placed on `imgBack`. Default is [0, 0].

    Returns:
        numpy.ndarray: The resulting image after overlaying `imgFront` on `imgBack`.

    Note:
        The `imgBack` and `imgFront` images should have the same number of channels (e.g., RGB or BGR).

    Example:
        >>> imgBack = cv2.imread('background.png')
        >>> imgFront = cv2.imread('foreground.png', cv2.IMREAD_UNCHANGED)
        >>> result = overlayPNG(imgBack, imgFront, pos=[100, 200])
    """
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

def get_training_data(player_name):
    """
    Retrieves training data from a CSV file for a specific player.

    The function reads the CSV file, skips the header row, and collects the player's moves from the CSV file.
    It returns the last 7 moves of the player as a list.

    Parameters:
        player_name (str): The name of the player to retrieve training data for.

    Returns:
        list: The last 7 moves of the player as a list of integers.

    Example:
        >>> player_name = "John"
        >>> moves = get_training_data(player_name)
        >>> print(moves)
        [2, 1, 3, 2, 1, 3, 1]
    """
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
    """
    Retrieves the training data for a player and trains a model if the data has a length of 7.

    If the length of the training data is 7, the function preprocesses the data, creates a model (MLPClassifier),
    and fits the model to the data. It returns the trained model and the scaler used for preprocessing.

    If the length of the training data is not 7, it returns None for both the model and scaler.

    Parameters:
        player_name (str): The name of the player to retrieve training data for.

    Returns:
        tuple: A tuple containing the trained model and the scaler used for preprocessing if the length of training data is 7.
               If the length of training data is not 7, returns (None, None).

    Example:
        >>> player_name = "John"
        >>> model, scaler = get_model(player_name)
        >>> if model is not None:
        ...     print("Model trained successfully!")
        ... else:
        ...     print("Insufficient training data.")
    """
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
    """
     Obtains the model and scaler for player1 and predicts the next move using the model if available.

     If the model is available, the function retrieves the last moves of player1 and predicts the next move using the model.
     If the model is not available (insufficient data), it generates a random move.
     It prints the received data and the predicted move.
     It returns the randomly generated move and the predicted move as a tuple.

     Parameters:
         player1 (str): The name of player1.

     Returns:
         tuple: A tuple containing the randomly generated move and the predicted move as strings.

     Example:
         >>> player1 = "John"
         >>> random_move, predicted_move = get_ai_move(player1)
         >>> print("Random move:", random_move)
         >>> print("Predicted move:", predicted_move)
     """
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

def get_player_move(handLeft, detectorLeft, player1):
    """
    Determines the move made by player1 based on the positions of the fingers detected by the hand detector (detectorLeft).

    The function assigns a move code (1, 2, or 3) based on the finger configuration.
    It returns the move code and the corresponding move name.

    Parameters:
        handLeft (list): The positions of the fingers detected by the hand detector for player1's left hand.
        detectorLeft: The hand detector used for detecting finger positions.
        player1 (str): The name of player1.

    Returns:
        tuple: A tuple containing the move code and the corresponding move name as strings.

    Example:
        >>> handLeft = [0, 1, 1, 0, 0]
        >>> detectorLeft = HandDetector()
        >>> player1 = "John"
        >>> move_code, move_name = get_player_move(handLeft, detectorLeft, player1)
        >>> print("Move code:", move_code)
        >>> print("Move name:", move_name)
    """
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

def calculate_result_against_AI(playerLeftMove, randomNumber, scores, winStreak):
    """
    Calculates the result of the game between the player and the AI.

    The function updates the scores and win streaks based on the result.
    It returns the result, updated scores, and win streaks.

    Parameters:
        playerLeftMove (int): The move code made by the player.
        randomNumber (int): The randomly generated move code by the AI.
        scores (list): A list containing the scores of the player and the AI.
        winStreak (list): A list containing the win streaks of the player and the AI.

    Returns:
        tuple: A tuple containing the result code (-1 for AI wins, 0 for draw, 1 for player wins),
               updated scores (list), and updated win streaks (list).

    Example:
        >>> playerLeftMove = 1
        >>> randomNumber = 3
        >>> scores = [0, 0]
        >>> winStreak = [0, 0]
        >>> result, updated_scores, updated_win_streaks = calculate_result_against_AI(playerLeftMove, randomNumber, scores, winStreak)
        >>> print("Result:", result)
        >>> print("Updated Scores:", updated_scores)
        >>> print("Updated Win Streaks:", updated_win_streaks)
    """
    # Player1 Wins
    if (playerLeftMove == 1 and randomNumber == 3) or \
            (playerLeftMove == 2 and randomNumber == 1) or \
            (playerLeftMove == 3 and randomNumber == 2):
        scores[1] += 1
        winStreak[1] += 1
        winStreak[0] = 0
        winner = 1
        new_round = True

    # Player2 (AI) Wins
    elif (playerLeftMove == 1 and randomNumber == 2) or \
            (playerLeftMove == 2 and randomNumber == 3) or \
            (playerLeftMove == 3 and randomNumber == 1):
        scores[0] += 1
        winStreak[0] += 1
        winner = 2
        new_round = True
    # Draw
    else:
        winner = 0
        new_round = True

    return scores, winStreak, winner, new_round

def draw_ui_against_AI(player1, player2, scores, randomNumber, left_frame, right_frame, half_width, height, handText, display_fps, winner, new_round):
    """
    Draws the UI for the game against the AI.

    The function overlays the AI move image on the left frame and combines it with the right frame.
    It displays player names, scores, and a dividing line on the combined frame.
    The resulting frame is returned.

    Parameters:
        player1 (str): The name of player1.
        player2 (str): The name of player2 (AI).
        scores (list): A list containing the scores of player1 and player2 (AI).
        randomNumber (int): The randomly generated move code by the AI.
        left_frame (numpy.ndarray): The left frame.
        right_frame (numpy.ndarray): The right frame.
        half_width (int): The half width of the frame.
        height (int): The height of the frame.
        handText (str): The text describing the detected hand.
        display_fps: The FPS value for display purposes.

    Returns:
        numpy.ndarray: The combined frame with the UI elements.

    Example:
        >>> player1 = "John"
        >>> player2 = "AI"
        >>> scores = [0, 0]
        >>> randomNumber = 2
        >>> left_frame = cv2.imread('left_frame.png')
        >>> right_frame = cv2.imread('right_frame.png')
        >>> half_width = 640
        >>> height = 480
        >>> handText = "Detected"
        >>> display_fps = 30
        >>> combined_frame = draw_ui_against_AI(player1, player2, scores, randomNumber, left_frame, right_frame, half_width, height, handText, display_fps)
    """
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

    cv2.line(combined_frame, (half_width, 50), (half_width, height), (255,255,255), 1)

    if(new_round):
        if(winner == 1):
            timer = 0
            if timer < 3:
                combined_frame = Generics.put_text_with_custom_font(combined_frame, "A.I. wins!",
                                                                    (270, 10), CVAssets.FONT_FRUIT_NINJA, 20,
                                                                    (0, 255, 0), outline_color=(0, 0, 0))
        elif(winner == 2):
            timer = 0
            if timer < 3:
                combined_frame = Generics.put_text_with_custom_font(combined_frame, "Player wins!",
                                                                    (270, 10), CVAssets.FONT_FRUIT_NINJA, 20,
                                                                    (0, 255, 0), outline_color=(0, 0, 0))
        elif(winner == 0):
            timer = 0
            if timer < 3:
                combined_frame = Generics.put_text_with_custom_font(combined_frame, "Bust, Try Again!",
                                                                    (250, 10), CVAssets.FONT_FRUIT_NINJA, 20,
                                                                    (0, 0, 255), outline_color=(0, 0, 0))
    return combined_frame

def save_to_csv(player_name, player_move, player_win_streak, prediction, AIMove):
    """
    Saves game data (player name, move, win streak, prediction, and AI move) to a CSV file.

    If the file doesn't exist, it creates a new file with a header row.
    If the player's training data exceeds 7 moves, it updates the model for that player.

    Parameters:
        player_name (str): The name of the player.
        player_move (int): The move made by the player.
        player_win_streak (int): The win streak of the player.
        prediction (str): The predicted move.
        AIMove (int): The move made by the AI.

    Returns:
        None

    Example:
        >>> player_name = "John"
        >>> player_move = 2
        >>> player_win_streak = 3
        >>> prediction = "Paper"
        >>> AIMove = 1
        >>> save_to_csv(player_name, player_move, player_win_streak, prediction, AIMove)
    """
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


def get_players_move(handLeft, detectorLeft, player1, handRight, detectorRight, player2):
    """
    Determines the moves made by both players based on the positions of their fingers detected by the respective hand detectors.

    The function assigns move codes (1, 2, or 3) based on the finger configurations of both players.
    It returns the move codes and corresponding move names for both players.

    Parameters:
        handLeft (list): The positions of the fingers detected by the hand detector for player1's left hand.
        detectorLeft: The hand detector used for detecting finger positions for player1's left hand.
        player1 (str): The name of player1.
        handRight (list): The positions of the fingers detected by the hand detector for player2's right hand.
        detectorRight: The hand detector used for detecting finger positions for player2's right hand.
        player2 (str): The name of player2.

    Returns:
        tuple: A tuple containing the move code and corresponding move name for player1, and the move code and corresponding move name for player2.

    Example:
        >>> handLeft = [0, 1, 1, 0, 0]
        >>> detectorLeft = HandDetector()
        >>> player1 = "John"
        >>> handRight = [1, 1, 1, 0, 0]
        >>> detectorRight = HandDetector()
        >>> player2 = "Mary"
        >>> move_code_player1, move_name_player1, move_code_player2, move_name_player2 = get_players_move(handLeft, detectorLeft, player1, handRight, detectorRight, player2)
        >>> print("Player 1 Move Code:", move_code_player1)
        >>> print("Player 1 Move Name:", move_name_player1)
        >>> print("Player 2 Move Code:", move_code_player2)
        >>> print("Player 2 Move Name:", move_name_player2)
    """
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

def draw_ui_against_players(scores, left_frame, right_frame, half_width, height, handLeftText, handRightText, display_fps, winner, new_round):
    """
    Draws the UI for the game between two players.

    The function combines the left and right frames, displays the scores, and adds a dividing line.
    The resulting combined frame is returned.

    Parameters:
        scores (list): A list containing the scores of both players.
        left_frame (numpy.ndarray): The left frame.
        right_frame (numpy.ndarray): The right frame.
        half_width (int): The half width of the frame.
        height (int): The height of the frame.
        handLeftText (str): The text describing the detected hand for player1.
        handRightText (str): The text describing the detected hand for player2.
        display_fps: The FPS value for display purposes.

    Returns:
        numpy.ndarray: The combined frame with the UI elements.

    Example:
        >>> scores = [0, 0]
        >>> left_frame = cv2.imread('left_frame.png')
        >>> right_frame = cv2.imread('right_frame.png')
        >>> half_width = 640
        >>> height = 480
        >>> handLeftText = "Detected"
        >>> handRightText = "Not Detected"
        >>> display_fps = 30
        >>> combined_frame = draw_ui_against_players(scores, left_frame, right_frame, half_width, height, handLeftText, handRightText, display_fps)
    """
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

    cv2.line(combined_frame, (half_width, 50), (half_width, height), (255,255,255), 1)
    if(new_round):
        if(winner == 1):
            timer = 0
            if timer < 3:
                combined_frame = Generics.put_text_with_custom_font(combined_frame, "Player left wins!",
                                                                    (250, 10), CVAssets.FONT_FRUIT_NINJA, 20,
                                                                    (0, 255, 0), outline_color=(0, 0, 0))
        elif(winner == 2):
            timer = 0
            if timer < 3:
                combined_frame = Generics.put_text_with_custom_font(combined_frame, "Player right wins!",
                                                                    (250, 10), CVAssets.FONT_FRUIT_NINJA, 20,
                                                                    (0, 255, 0), outline_color=(0, 0, 0))
        elif(winner == 0):
            timer = 0
            if timer < 3:
                combined_frame = Generics.put_text_with_custom_font(combined_frame, "Bust, Try Again!",
                                                                    (250, 10), CVAssets.FONT_FRUIT_NINJA, 20,
                                                                    (0, 0, 255), outline_color=(0, 0, 0))

    return combined_frame

def calculate_results_against_players(playerLeftMove, playerRightMove, scores, player2, player1):
    """
    Calculates the result of the game between two players based on their moves.

    The function updates the scores based on the result.
    It returns the updated scores.

    Parameters:
        playerLeftMove (int): The move made by player1.
        playerRightMove (int): The move made by player2.
        scores (list): A list containing the scores of player1 and player2.
        player2 (str): The name of player2.
        player1 (str): The name of player1.

    Returns:
        list: A list containing the updated scores of player1 and player2.

    Example:
        >>> playerLeftMove = 2
        >>> playerRightMove = 3
        >>> scores = [0, 0]
        >>> player2 = "John"
        >>> player1 = "Mary"
        >>> updated_scores = calculate_results_against_players(playerLeftMove, playerRightMove, scores, player2, player1)
        >>> print("Updated Scores:", updated_scores)
    """
    # Player Right Wins
    if (playerLeftMove == 1 and playerRightMove == 3) or \
            (playerLeftMove == 2 and playerRightMove == 1) or \
            (playerLeftMove == 3 and playerRightMove == 2):
        scores[1] += 1
        print(f"Player '{player1}' Wins, Score = ", scores[1])
        winner = 1
        new_round = True

    # Player Left Wins
    elif (playerLeftMove == 3 and playerRightMove == 1) or \
            (playerLeftMove == 1 and playerRightMove == 2) or \
            (playerLeftMove == 2 and playerRightMove == 3):
        scores[0] += 1
        print(f"Player '{player2}' Wins, Score = ", scores[0])
        winner = 2
        new_round = True
    else:
        print("Bust, try again..")
        winner = 0
        new_round = True

    return scores, winner, new_round

#------------------------------------------------------------------------ Used in both
def mirror_hands(hand):
    """
    Mirrors the hand type from left to right or right to left.

    The function determines the type of hand based on the provided hand data and returns the mirrored hand type.

    Parameters:
        hand (list): A list containing hand data.

    Returns:
        str: The mirrored hand type. Possible values are "Left", "Right", or "None".

    Example:
        >>> hand = [{'type': 'Left', 'confidence': 0.9}]
        >>> mirrored_hand = mirror_hands(hand)
        >>> print("Mirrored Hand:", mirrored_hand)
    """
    if str(hand[0]['type']) == "Left":
        handtext = "Right"
    elif str(hand[0]['type']) == "Right":
        handtext = "Left"
    else:
        handtext = "None"

    return handtext