import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from PIL import Image, ImageDraw, ImageFont
import os

# Define color block coordinate ranges (x_min, x_max, name, color_bgr, thickness)
COLORS_INFO = [
    {"x_min": 23, "x_max": 159, "name": "RED", "color": (36, 27, 237), "thickness": 8},
    {"x_min": 183, "x_max": 309, "name": "BLUE", "color": (204, 71, 63), "thickness": 8},
    {"x_min": 336, "x_max": 465, "name": "GREEN", "color": (77, 177, 35), "thickness": 8},
    {"x_min": 491, "x_max": 627, "name": "YELLOW", "color": (0, 242, 254), "thickness": 8},
    {"x_min": 648, "x_max": 791, "name": "ERASER", "color": (0, 0, 0), "thickness": 50}  # Eraser draws black (0,0,0) to clear mask
]

# Multilingual Translations
TRANSLATIONS = {
    "English": {
        "RED": "RED",
        "BLUE": "BLUE",
        "GREEN": "GREEN",
        "YELLOW": "YELLOW",
        "ERASER": "ERASER",
        "SETTINGS": "SETTINGS",
        "SELECT_LANGUAGE": "SELECT LANGUAGE",
        "ENGLISH_BTN": "ENGLISH",
        "BENGALI_BTN": "BENGALI",
        "DONE_BTN": "DONE",
        "MODE_LABEL": "Mode: ",
        "TOOL_LABEL": "Tool: ",
        "EXIT_LABEL": "ESC to Exit",
        "STANDBY": "Standby",
        "SELECT_MODE": "Select Mode",
        "PAINT_MODE": "Paint Mode"
    },
    "Bengali": {
        "RED": "লাল",
        "BLUE": "নীল",
        "GREEN": "সবুজ",
        "YELLOW": "হলুদ",
        "ERASER": "মুছনি",
        "SETTINGS": "সেটিংস",
        "SELECT_LANGUAGE": "ভাষা নির্বাচন করুন",
        "ENGLISH_BTN": "English",
        "BENGALI_BTN": "বাংলা",
        "DONE_BTN": "সম্পন্ন",
        "MODE_LABEL": "মোড: ",
        "TOOL_LABEL": "টুল: ",
        "EXIT_LABEL": "বাহির হতে ESC চাপুন",
        "STANDBY": "অপেক্ষমান",
        "SELECT_MODE": "নির্বাচন মোড",
        "PAINT_MODE": "আঁকার মোড"
    }
}

# Settings Button coordinates (top-right header)
SETTINGS_BTN = {"x_min": 900, "x_max": 1100, "y_min": 23, "y_max": 128}

# Settings Modal layout coordinates
MODAL_BOX = {"x_min": 320, "x_max": 832, "y_min": 150, "y_max": 550}
ENGLISH_OPT_BTN = {"x_min": 400, "x_max": 600, "y_min": 260, "y_max": 330}
BENGALI_OPT_BTN = {"x_min": 400, "x_max": 600, "y_min": 370, "y_max": 440}
DONE_OPT_BTN = {"x_min": 660, "x_max": 780, "y_min": 440, "y_max": 500}

# Font paths for rendering
FONT_PATH_DEFAULT = "C:\\Windows\\Fonts\\Nirmala.ttc"
if not os.path.exists(FONT_PATH_DEFAULT):
    FONT_PATH_DEFAULT = "arial.ttf"

def render_bengali_text(img, text, position, font_size=20, font_color=(255, 255, 255)):
    """
    Renders Bengali or English text using PIL library onto the OpenCV frame.
    Supports complex scripts.
    """
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try:
        font = ImageFont.truetype(FONT_PATH_DEFAULT, font_size)
    except IOError:
        font = ImageFont.load_default()
    draw.text(position, text, font=font, fill=font_color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

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

def check_settings_trigger(x, y, menu_height=145):
    """
    Checks if selection coordinates hover over the Settings button.
    """
    if y < menu_height:
        if SETTINGS_BTN["x_min"] <= x <= SETTINGS_BTN["x_max"]:
            return True
    return False

def check_modal_options(x, y):
    """
    Returns the hovered option in settings modal: "ENGLISH", "BENGALI", "DONE", or None.
    """
    if ENGLISH_OPT_BTN["x_min"] <= x <= ENGLISH_OPT_BTN["x_max"] and ENGLISH_OPT_BTN["y_min"] <= y <= ENGLISH_OPT_BTN["y_max"]:
        return "ENGLISH"
    elif BENGALI_OPT_BTN["x_min"] <= x <= BENGALI_OPT_BTN["x_max"] and BENGALI_OPT_BTN["y_min"] <= y <= BENGALI_OPT_BTN["y_max"]:
        return "BENGALI"
    elif DONE_OPT_BTN["x_min"] <= x <= DONE_OPT_BTN["x_max"] and DONE_OPT_BTN["y_min"] <= y <= DONE_OPT_BTN["y_max"]:
        return "DONE"
    return None

def get_canvas_coords(x, y):
    """
    Returns the coordinates for drawing. Now allows drawing anywhere on the full screen.
    """
    return x, y

def main():
    current_language = "English"
    settings_active = False

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

        current_mode = "STANDBY"
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
                    current_mode = "SELECT_MODE"
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

                    if settings_active:
                        # Interact with settings modal
                        opt = check_modal_options(x, y)
                        if opt == "ENGLISH":
                            current_language = "English"
                        elif opt == "BENGALI":
                            current_language = "Bengali"
                        elif opt == "DONE":
                            settings_active = False
                    else:
                        # Check selection header triggers
                        sel_idx = get_tool_selection(x, y, COLORS_INFO)
                        if sel_idx is not None:
                            current_selection_idx = sel_idx
                        elif check_settings_trigger(x, y):
                            settings_active = True

                elif index_raised:
                    # Paint Mode: Only Index finger is raised
                    current_mode = "PAINT_MODE"
                    cursor_color = COLORS_INFO[current_selection_idx]["color"]

                    # Draw index finger cursor feedback on the frame
                    if COLORS_INFO[current_selection_idx]["name"] == "ERASER":
                        cv2.circle(frame, (x, y), 25, (255, 255, 255), 2)
                        cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)
                    else:
                        cv2.circle(frame, (x, y), 10, cursor_color, -1)

                    # Draw on the canvas (only if settings menu is not open)
                    if not settings_active:
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

        # Draw Settings Button on header
        cv2.rectangle(combined, (SETTINGS_BTN["x_min"], SETTINGS_BTN["y_min"]), (SETTINGS_BTN["x_max"], SETTINGS_BTN["y_max"]), (255, 255, 255), -1)
        cv2.rectangle(combined, (SETTINGS_BTN["x_min"], SETTINGS_BTN["y_min"]), (SETTINGS_BTN["x_max"], SETTINGS_BTN["y_max"]), (0, 0, 0), 3)
        combined = render_bengali_text(
            combined, 
            TRANSLATIONS[current_language]["SETTINGS"], 
            (SETTINGS_BTN["x_min"] + 20, SETTINGS_BTN["y_min"] + 30), 
            font_size=24, 
            font_color=(0, 0, 0)
        )

        # 9. Use OpenCV to create a green coloured border around the selected colour overlay
        selected_tool = COLORS_INFO[current_selection_idx]
        border_x_min = selected_tool["x_min"] - 4
        border_x_max = selected_tool["x_max"] + 4
        border_y_min = 23 - 4
        border_y_max = 128 + 4
        cv2.rectangle(combined, (border_x_min, border_y_min), (border_x_max, border_y_max), (0, 255, 0), 4)

        # Draw Settings Dialog Modal if active
        if settings_active:
            # Semi-transparent overlay backdrop
            overlay_bg = combined.copy()
            cv2.rectangle(overlay_bg, (0, 0), (1152, 648), (0, 0, 0), -1)
            cv2.addWeighted(overlay_bg, 0.4, combined, 0.6, 0, combined)

            # Draw Dialog Box
            cv2.rectangle(combined, (MODAL_BOX["x_min"], MODAL_BOX["y_min"]), (MODAL_BOX["x_max"], MODAL_BOX["y_max"]), (255, 255, 255), -1)
            cv2.rectangle(combined, (MODAL_BOX["x_min"], MODAL_BOX["y_min"]), (MODAL_BOX["x_max"], MODAL_BOX["y_max"]), (36, 114, 237), 5) # Orange/blue border

            # Title
            combined = render_bengali_text(
                combined,
                TRANSLATIONS[current_language]["SETTINGS"],
                (MODAL_BOX["x_min"] + 180, MODAL_BOX["y_min"] + 20),
                font_size=32,
                font_color=(180, 0, 0)
            )

            # Prompt label
            combined = render_bengali_text(
                combined,
                TRANSLATIONS[current_language]["SELECT_LANGUAGE"],
                (MODAL_BOX["x_min"] + 40, MODAL_BOX["y_min"] + 70),
                font_size=20,
                font_color=(180, 0, 0)
            )

            # Draw English option button
            eng_border_color = (0, 255, 0) if current_language == "English" else (0, 0, 0)
            cv2.rectangle(combined, (ENGLISH_OPT_BTN["x_min"], ENGLISH_OPT_BTN["y_min"]), (ENGLISH_OPT_BTN["x_max"], ENGLISH_OPT_BTN["y_max"]), (240, 240, 240), -1)
            cv2.rectangle(combined, (ENGLISH_OPT_BTN["x_min"], ENGLISH_OPT_BTN["y_min"]), (ENGLISH_OPT_BTN["x_max"], ENGLISH_OPT_BTN["y_max"]), eng_border_color, 3)
            combined = render_bengali_text(
                combined,
                TRANSLATIONS[current_language]["ENGLISH_BTN"],
                (ENGLISH_OPT_BTN["x_min"] + 50, ENGLISH_OPT_BTN["y_min"] + 20),
                font_size=22,
                font_color=(0, 0, 0)
            )

            # Draw Bengali option button
            beng_border_color = (0, 255, 0) if current_language == "Bengali" else (0, 0, 0)
            cv2.rectangle(combined, (BENGALI_OPT_BTN["x_min"], BENGALI_OPT_BTN["y_min"]), (BENGALI_OPT_BTN["x_max"], BENGALI_OPT_BTN["y_max"]), (240, 240, 240), -1)
            cv2.rectangle(combined, (BENGALI_OPT_BTN["x_min"], BENGALI_OPT_BTN["y_min"]), (BENGALI_OPT_BTN["x_max"], BENGALI_OPT_BTN["y_max"]), beng_border_color, 3)
            combined = render_bengali_text(
                combined,
                TRANSLATIONS[current_language]["BENGALI_BTN"],
                (BENGALI_OPT_BTN["x_min"] + 50, BENGALI_OPT_BTN["y_min"] + 20),
                font_size=22,
                font_color=(0, 0, 0)
            )

            # Draw Done button
            cv2.rectangle(combined, (DONE_OPT_BTN["x_min"], DONE_OPT_BTN["y_min"]), (DONE_OPT_BTN["x_max"], DONE_OPT_BTN["y_max"]), (240, 240, 240), -1)
            cv2.rectangle(combined, (DONE_OPT_BTN["x_min"], DONE_OPT_BTN["y_min"]), (DONE_OPT_BTN["x_max"], DONE_OPT_BTN["y_max"]), (0, 0, 255), 3)
            combined = render_bengali_text(
                combined,
                TRANSLATIONS[current_language]["DONE_BTN"],
                (DONE_OPT_BTN["x_min"] + 20, DONE_OPT_BTN["y_min"] + 15),
                font_size=20,
                font_color=(180, 0, 0)
            )

        # 7. Using OpenCV, paint the current mode and active tool on the center bottom of the screen
        mode_key = current_mode
        mode_text_val = TRANSLATIONS[current_language][mode_key]
        mode_text = f"{TRANSLATIONS[current_language]['MODE_LABEL']}{mode_text_val}"
        
        tool_name_key = selected_tool["name"]
        tool_text_val = TRANSLATIONS[current_language][tool_name_key]
        tool_text = f"{TRANSLATIONS[current_language]['TOOL_LABEL']}{tool_text_val}"

        exit_text = TRANSLATIONS[current_language]["EXIT_LABEL"]
        
        # Bottom HUD background box
        cv2.rectangle(combined, (340, 580), (810, 635), (0, 0, 0), -1)
        cv2.rectangle(combined, (340, 580), (810, 635), (255, 255, 255), 2)
        
        combined = render_bengali_text(
            combined,
            mode_text,
            (355, 585),
            font_size=18,
            font_color=(0, 255, 0) if current_mode == "PAINT_MODE" else (0, 255, 255)
        )
        combined = render_bengali_text(
            combined,
            tool_text,
            (355, 610),
            font_size=18,
            font_color=(255, 255, 255)
        )
        combined = render_bengali_text(
            combined,
            exit_text,
            (640, 595),
            font_size=18,
            font_color=(0, 0, 255)
        )

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
