import requests
import json
import os
import sys

# Configuration
# You can get your free API Token from https://platerecognizer.com/
# Recommended: export/set the environment variable `PLATERECOGNIZER_TOKEN`.
# For local development you can set it in PowerShell:
#   setx PLATERECOGNIZER_TOKEN "your_real_token_here"
# Or paste the token into the Streamlit sidebar (app.py supports overriding at runtime).
API_TOKEN = os.environ.get("PLATERECOGNIZER_TOKEN", "ebbffa4ad08278eb093ec2cd398bc583943d5c2c")


def set_api_token(token: str):
    """Set the API token at runtime (useful from the UI).

    Example:
        import main
        main.set_api_token("mytoken")
    """
    global API_TOKEN
    API_TOKEN = str(token or "")

# API Endpoint
API_URL = "https://api.platerecognizer.com/v1/plate-reader/"


def detect_plate(image_input, regions="in"):
    """
    Detects license plates using PlateRecognizer API.

    Accepts either:
      - a path string to an image file, or
      - raw image bytes (bytes or bytearray)

    Returns a dict:
      - on success: {'results': [...], 'raw': <full api response>}
      - on error:   {'error': 'message'}
    """
    # Validate API token
    if not API_TOKEN:
        return {"error": "API Token not configured. Set PLATERECOGNIZER_TOKEN env var or provide token via the UI."}

    # Prepare files payload depending on input type
    files_payload = None
    open_fp = None

    try:
        if isinstance(image_input, (bytes, bytearray)):
            files_payload = {"upload": ("image.jpg", image_input)}
        elif isinstance(image_input, str):
            if not os.path.exists(image_input):
                return {"error": f"File not found: {image_input}"}
            open_fp = open(image_input, "rb")
            files_payload = {"upload": open_fp}
        else:
            return {"error": "Unsupported image_input type. Provide file path or bytes."}

        response = requests.post(
            API_URL,
            data={"regions": regions},
            files=files_payload,
            headers={"Authorization": f"Token {API_TOKEN}"},
            timeout=30
        )

        if open_fp:
            open_fp.close()

        if response.status_code == 403:
            return {"error": "Invalid API Token or limit reached (403)."}
        if response.status_code not in (200, 201):
            # Return the text from the API to help debugging
            return {"error": f"API returned status {response.status_code}: {response.text}"}

        result = response.json()
        return {"results": result.get("results", []), "raw": result}

    except Exception as e:
        try:
            if open_fp:
                open_fp.close()
        except Exception:
            pass
        return {"error": str(e)}


if __name__ == "__main__":
    # CLI support: path argument or default
    if len(sys.argv) > 1:
        IMAGE_PATH = sys.argv[1]
    else:
        IMAGE_PATH = "test_image.jpg"

    out = detect_plate(IMAGE_PATH)
    if "error" in out:
        print("Error:", out["error"])
    else:
        results = out.get("results", [])
        if not results:
            print("No license plate detected.")
        else:
            print("\n--- Detection Results ---")
            for idx, res in enumerate(results):
                plate = res.get("plate", "")
                confidence = res.get("score", 0)
                vehicle_type = res.get("vehicle", {}).get("type", "Unknown")
                print(f"Result {idx+1}:")
                print(f"  Plate Number: {plate.upper()}")
                print(f"  Confidence:   {confidence:.2f}")
                print(f"  Vehicle Type: {vehicle_type}")
                print("-------------------------")
