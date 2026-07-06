# Virtual Paint App Documentation (Multilingual Settings)

## Feature Overview

We added interactive **multilingual settings** (English / Bengali) to the Virtual Paint App.

- **Settings Trigger**: A "SETTINGS" box is drawn in the top-right header coordinates (`x: 900-1100`, `y: 23-128`).
- **Interactive Modal**: Hovering over the Settings button in **Select Mode** opens a central dialog box offering options to switch UI languages.
- **Language Options**:
  - **English**: Translates UI labels to English.
  - **Bengali (বাংলা)**: Translates UI labels to Bengali (e.g. modes, active tools, exit messages) with proper rendering support.
- **Done Button**: Closes the dialog box, returning the canvas interaction to active.

## Code Design

- Language choices are dynamically mapped via a `TRANSLATIONS` dictionary.
- Non-ASCII/Bengali scripts are rendered cleanly onto the OpenCV frames using the `Pillow` library via a helper function `render_bengali_text` mapping to the system's `Nirmala.ttc` font.

## Version Control Info
Changes have been implemented on the new branch `feature` ready to be committed and merged.
