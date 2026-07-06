# Virtual Paint App Documentation

## Feature Overview

### 1. Multilingual Settings (English / Bengali)
- **Settings Trigger**: A "SETTINGS" box is drawn in the top-right header coordinates (`x: 900-1100`, `y: 23-128`).
- **Interactive Modal**: Hovering over the Settings button in **Select Mode** opens a central dialog box offering options to switch UI languages.
- **Language Options**:
  - **English**: Translates UI labels to English.
  - **Bengali (বাংলা)**: Translates UI labels to Bengali (e.g. modes, active tools, exit messages) with proper rendering support.
- **Done Button**: Closes the dialog box, returning the canvas interaction to active.

### 2. Pause Mode via Multi-Finger Gesture
- **Gesture Control**: Raising the **index, middle, and ring fingers** simultaneously triggers **Pause Mode**, stopping the painting state.
- **Resuming**: To stop the pause mode and turn on **Paint Mode**, raise **only the index finger**.
- **Visual Feedback**:
  - When drawing is paused, the HUD mode indicator displays **Pause Mode** (in orange).
  - The cursor changes to a protective orange circle outline, indicating that moving your finger will not write on the canvas.

## Code Design

- Language choices are dynamically mapped via a `TRANSLATIONS` dictionary.
- Non-ASCII/Bengali scripts are rendered cleanly onto the OpenCV frames using the `Pillow` library via a helper function `render_bengali_text` mapping to the system's `Nirmala.ttc` font.
- Ring finger gestures are detected using the `check_ring_raised` helper function mapping landmark 16 (tip) relative to landmark 14 (PIP joint).
- Mode transitions and painting constraints are regulated using the state variable `is_paused`.

## Version Control Info
Changes have been implemented on the branch `feature` and merged to `main`.


