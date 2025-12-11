# License Plate Detector (PlateRecognizer)

Small Streamlit app and CLI wrapper that uses the PlateRecognizer API to detect vehicle license plates in images.

Requirements
-----------
- Python 3.8+
- Install dependencies:

```powershell
pip install -r requirements.txt
```

Getting an API token
---------------------
Register for a free API token at PlateRecognizer:

https://platerecognizer.com/

Once you have a token set it in your environment (PowerShell example):

```powershell
setx PLATERECOGNIZER_TOKEN "your_real_token_here"
```

After running `setx` you may need to open a new terminal for the variable to be available. Alternatively, you can paste the token into the Streamlit sidebar when the app is running — the UI will use that token for the current session.

Run (UI)
--------
Start the Streamlit UI and upload an image:

```powershell
streamlit run app.py
```

Run (CLI)
---------
You can also run the CLI wrapper which will print detection results to terminal:

```powershell
python main.py path\to\image.jpg
```

Notes
-----
- Do NOT commit your API token into source control. This repository includes a `.gitignore` to exclude common environment files.
- The app supports region hints (e.g. `in`, `us`, `eu`) via the sidebar.
- If you want the repo to load secrets from a `.env` file, I can add `python-dotenv` and a short example.

Support / Contribution
----------------------
If you want me to add features (examples: save results, fetch plate-crop URLs automatically, or add a test image gallery), tell me which feature and I'll add it.
