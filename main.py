import requests
import json
import os
import sys

# Configuration
# You can get your free API Token from https://platerecognizer.com/
# Set it here or export it as an environment variable: export PLATERECOGNIZER_TOKEN="your_token"
API_TOKEN = os.environ.get("PLATERECOGNIZER_TOKEN", "ebbffa4ad08278eb093ec2cd398bc583943d5c2c")

# API Endpoint
API_URL = "https://api.platerecognizer.com/v1/plate-reader/"

def detect_plate(image_path):
    """
    Detects license plate in the given image using PlateRecognizer API.
    Prints the detected plate number to terminal.
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found at {image_path}")
        return

    if API_TOKEN == "YOUR_API_TOKEN_HERE":
        print("Error: API Token not configured.")
        print("Please set the API_TOKEN variable in the script or use 'export PLATERECOGNIZER_TOKEN=...'")
        return

    print(f"Processing image: {image_path}...")

    try:
        with open(image_path, 'rb') as fp:
            response = requests.post(
                API_URL,
                data=dict(regions='in'),  # Optional: 'in' for India, 'us' for USA, etc.
                files=dict(upload=fp),
                headers={'Authorization': f'Token {API_TOKEN}'}
            )
        
        # Check response status
        if response.status_code == 403:
             print("Error: Invalid API Token or Limit Reached.")
             return
        elif response.status_code != 200 and response.status_code != 201:
             print(f"Error: API returned status code {response.status_code}")
             print(response.text)
             return

        result = response.json()
        
        # Parse results
        results = result.get('results', [])
        
        if not results:
            print("No license plate detected.")
        else:
            print(f"\n--- Detection Results ---")
            for idx, res in enumerate(results):
                plate = res['plate']
                confidence = res['score']
                vehicle_type = res.get('vehicle', {}).get('type', 'Unknown')
                print(f"Result {idx+1}:")
                print(f"  Plate Number: {plate.upper()}")
                print(f"  Confidence:   {confidence:.2f}")
                print(f"  Vehicle Type: {vehicle_type}")
                print("-------------------------")
                
                # If you just want the raw string for the first match:
                # print(plate.upper())

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # You can hardcode the path here as requested
    # Example: IMAGE_PATH = "/path/to/your/image.jpg"
    
    # Using command line argument for flexibility, but falling back to a default if provided
    if len(sys.argv) > 1:
        IMAGE_PATH = sys.argv[1]
    else:
        # REPLACE THIS WITH YOUR HARDCODED PATH
        IMAGE_PATH = "test_image.jpg" 
        
    detect_plate(IMAGE_PATH)
