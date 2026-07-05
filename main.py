import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Define color block coordinate ranges (x_min, x_max, name, color_bgr, thickness)
COLORS_INFO = [
    {"x_min": 23, "x_max": 159, "name": "RED", "color": (36, 27, 237), "thickness": 8},
    {"x_min": 183, "x_max": 309, "name": "BLUE", "color": (204, 71, 63), "thickness": 8},
    {"x_min": 336, "x_max": 465, "name": "GREEN", "color": (77, 177, 35), "thickness": 8},
    {"x_min": 491, "x_max": 627, "name": "YELLOW", "color": (0, 242, 254), "thickness": 8},
    {"x_min": 648, "x_max": 791, "name": "ERASER", "color": (0, 0, 0), "thickness": 50}  # Eraser draws black (0,0,0) to clear mask
]

def check_fingers_raised(landmarks):
    """
    Checks if index and middle fingers are raised.
    y-coordinate is 0 at the top, so a smaller y value means the finger tip is higher.
    """
    index_raised = landmarks[8].y < landmarks[6].y
    middle_raised = landmarks[12].y < landmarks[10].y
    return index_raised, middle_raised

def get_tool_selection(x, y, colors_info=COLORS_INFO, menu_height=145):
    """
    Returns the index of the selected tool if the coordinates are in the header region.
    """
    if y < menu_height:
        for idx, info in enumerate(colors_info):
            if info["x_min"] <= x <= info["x_max"]:
                return idx
    return None

def get_canvas_coords(x, y):
    """
    Returns the coordinates for drawing. Now allows drawing anywhere on the full screen.
    """
    return x, y

def main():

    # 1. Load the overlay image to copy the header design
    overlay_img = cv2.imread('overlay.jpg')
    if overlay_img is None:
        # Fallback if image is missing, create a blank header
        overlay_img = np.ones((648, 1152, 3), dtype=np.uint8) * 255
        # Draw placeholder boxes
        cv2.rectangle(overlay_img, (23, 23), (159, 128), (36, 27, 237), -1)
        cv2.rectangle(overlay_img, (183, 23), (309, 128), (204, 71, 63), -1)
        cv2.rectangle(overlay_img, (336, 23), (465, 128), (77, 177, 35), -1)
        cv2.rectangle(overlay_img, (491, 23), (627, 128), (0, 242, 254), -1)
        cv2.rectangle(overlay_img, (648, 23), (791, 128), (255, 255, 255), -1)
        cv2.rectangle(overlay_img, (648, 23), (791, 128), (0, 0, 0), 3)
        cv2.putText(overlay_img, "ERASER", (665, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    else:
        # Resize overlay_img to exactly 1152x648 to match our target dimensions
        overlay_img = cv2.resize(overlay_img, (1152, 648))

    # Initialize current selection (default to Red)
    current_selection_idx = 0
    
    # 2. Use OpenCV to open the webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Set webcam resolution to 1280x720 - we will resize to 1152x648
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # 3. Create a canvas of the same size as the screen to store drawings (initialized to black/empty)
    canvas = np.zeros((648, 1152, 3), dtype=np.uint8)

    # 4. Use mediapipe HandLandmarker to detect hand gestures
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        running_mode=vision.RunningMode.IMAGE
    )
    detector = vision.HandLandmarker.create_from_options(options)

    # Track drawing coordinates
    prev_x, prev_y = None, None

    print("Virtual Paint App is running. Press 'esc' to exit.")

    while cap.isOpened():
        success, raw_frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # Flip horizontally for natural mirror feel
        frame = cv2.flip(raw_frame, 1)
        # Resize to 1152x648
        frame = cv2.resize(frame, (1152, 648))

        # Detect hands on the original flipped frame (full width/height)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = detector.detect(mp_image)

        current_mode = "Standby"
        cursor_color = (128, 128, 128)

        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                
                index_raised, middle_raised = check_fingers_raised(hand_landmarks)

                # Coordinates of index tip in pixel scale
                h_img, w_img, _ = frame.shape
                x = int(hand_landmarks[8].x * w_img)
                y = int(hand_landmarks[8].y * h_img)

                # Clamp index finger coordinates within window limits
                x = max(0, min(x, w_img - 1))
                y = max(0, min(y, h_img - 1))

                # Mode selection logic
                if index_raised and middle_raised:
                    # Select Mode: Both Index and Middle fingers are raised
                    current_mode = "Select Mode"
                    cursor_color = (0, 255, 255) # Yellow cursor for selection mode
                    
                    # Reset line tracing points
                    prev_x, prev_y = None, None

                    # Middle finger tip coordinates to draw feedback between both raised fingers
                    mx = int(hand_landmarks[12].x * w_img)
                    my = int(hand_landmarks[12].y * h_img)
                    mx = max(0, min(mx, w_img - 1))
                    my = max(0, min(my, h_img - 1))
                    
                    # Draw selection indicator (circles on tips and a line connecting them)
                    # We will draw feedback directly on the output frame later
                    cv2.circle(frame, (x, y), 8, cursor_color, -1)
                    cv2.circle(frame, (mx, my), 8, cursor_color, -1)
                    cv2.line(frame, (x, y), (mx, my), cursor_color, 2)

                    # Check selection header triggers
                    sel_idx = get_tool_selection(x, y, COLORS_INFO)
                    if sel_idx is not None:
                        current_selection_idx = sel_idx

                elif index_raised:
                    # Paint Mode: Only Index finger is raised
                    current_mode = "Paint Mode"
                    cursor_color = COLORS_INFO[current_selection_idx]["color"]

                    # Draw index finger cursor feedback on the frame
                    if COLORS_INFO[current_selection_idx]["name"] == "ERASER":
                        cv2.circle(frame, (x, y), 25, (255, 255, 255), 2)
                        cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)
                    else:
                        cv2.circle(frame, (x, y), 10, cursor_color, -1)

                    # Draw on the canvas
                    canvas_coords = get_canvas_coords(x, y)
                    if canvas_coords is not None:
                        cx, cy = canvas_coords
                        if prev_x is not None:
                            prev_canvas_coords = get_canvas_coords(prev_x, prev_y)
                            if prev_canvas_coords is not None:
                                pcx, pcy = prev_canvas_coords
                                thickness = COLORS_INFO[current_selection_idx]["thickness"]
                                # Draw line on canvas
                                cv2.line(canvas, (pcx, pcy), (cx, cy), cursor_color, thickness)
                        
                        prev_x, prev_y = x, y
                else:
                    # No mode matched, reset line trace
                    prev_x, prev_y = None, None

                # draw hand landmarks manually on the camera frame
                for lm in hand_landmarks:
                    lm_x = int(lm.x * w_img)
                    lm_y = int(lm.y * h_img)
                    cv2.circle(frame, (lm_x, lm_y), 4, (255, 0, 255), -1)
        else:
            # Reset line trace when no hand is detected
            prev_x, prev_y = None, None

        # Blend drawing canvas with webcam frame
        # Find where canvas is not black (i.e. has drawing elements)
        canvas_gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(canvas_gray, 1, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        # Black out the drawing region in the camera frame
        frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        # Take drawing from the canvas
        canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask)
        # Combine them
        combined = cv2.add(frame_bg, canvas_fg)

        # Overlay the top header (up to y = 145) from overlay_img
        # We overlay it on top of the blended image
        combined[0:145, :] = overlay_img[0:145, :]

        # 9. Use OpenCV to create a green coloured border around the selected colour overlay
        selected_tool = COLORS_INFO[current_selection_idx]
        border_x_min = selected_tool["x_min"] - 4
        border_x_max = selected_tool["x_max"] + 4
        border_y_min = 23 - 4
        border_y_max = 128 + 4
        cv2.rectangle(combined, (border_x_min, border_y_min), (border_x_max, border_y_max), (0, 255, 0), 4)

        # 7. Using OpenCV, paint the current mode and active tool on the center bottom of the screen
        mode_text = f"Mode: {current_mode}"
        tool_text = f"Tool: {selected_tool['name']}"
        
        # Bottom HUD background box
        cv2.rectangle(combined, (380, 580), (770, 635), (0, 0, 0), -1)
        cv2.rectangle(combined, (380, 580), (770, 635), (255, 255, 255), 2)
        
        cv2.putText(combined, mode_text, (395, 605), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if current_mode == "Paint Mode" else (0, 255, 255), 2)
        cv2.putText(combined, tool_text, (395, 625), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(combined, "ESC to Exit", (660, 615), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Show the app window
        cv2.imshow("Virtual Paint App", combined)

        # 12. On pressing "esc" - Exit the application
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
