import streamlit as st
import main
from PIL import Image
import io
import requests
import traceback

# Page Config
st.set_page_config(
    page_title="License Plate Detector",
    page_icon="🚗",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
    }
    .reportview-container .markdown-text-container {
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚗 License Plate Detector")
st.write("Upload an image of a vehicle to detect the license plate number.")

# File Uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Sidebar: allow providing an API token and region override
st.sidebar.header("Settings")
user_token = st.sidebar.text_input("PlateRecognizer API Token (optional)", type="password")
region_option = st.sidebar.selectbox("Region", options=["in", "us", "eu", "*"], index=0)

if user_token:
    # Override the token in main module at runtime
    try:
        main.API_TOKEN = user_token
    except Exception:
        # If for some reason the attribute doesn't exist, ignore — main will handle missing token
        pass

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image', use_column_width=True)
    
    st.write("")
    if st.button('Detect License Plate', type="primary"):
        with st.spinner('Processing image...'):
            # Reset file pointer to beginning for API call
            uploaded_file.seek(0)
            image_bytes = uploaded_file.read()

            # Call the detection function from main.py with selected region
            try:
                result = main.detect_plate(image_bytes, regions=region_option)
            except Exception as e:
                result = {"error": f"Internal error calling detection: {e}\n{traceback.format_exc()}"}
            
            if "error" in result:
                st.error(result["error"])
            else:
                results = result.get('results', [])
                if not results:
                    st.warning("No license plate detected.")
                else:
                    st.success("License Plate Detected!")

                    # Display results
                    for idx, res in enumerate(results):
                        plate = res.get('plate', '').upper()
                        score = res.get('score', res.get('confidence', 0))
                        try:
                            confidence = float(score) * 100
                        except Exception:
                            confidence = 0.0
                        vehicle_type = res.get('vehicle', {}).get('type', 'Unknown').capitalize()

                        # Layout: plate crop (if available) + metrics
                        left, right = st.columns([1, 2])
                        with left:
                            # Try to show a cropped plate image if bounding box exists
                            box = res.get('box') or res.get('bbox') or res.get('vehicle', {}).get('box')
                            cropped_shown = False
                            if box and image is not None:
                                try:
                                    # Support multiple box formats
                                    if all(k in box for k in ("xmin", "ymin", "xmax", "ymax")):
                                        xmin = int(box['xmin']); ymin = int(box['ymin'])
                                        xmax = int(box['xmax']); ymax = int(box['ymax'])
                                    elif all(k in box for k in ("x", "y", "w", "h")):
                                        xmin = int(box['x']); ymin = int(box['y'])
                                        xmax = xmin + int(box['w']); ymax = ymin + int(box['h'])
                                    else:
                                        xmin = ymin = xmax = ymax = None

                                    if xmin is not None and ymin is not None and xmax is not None and ymax is not None:
                                        # Ensure coordinates inside image bounds
                                        img_w, img_h = image.size
                                        xmin = max(0, min(xmin, img_w - 1))
                                        xmax = max(0, min(xmax, img_w))
                                        ymin = max(0, min(ymin, img_h - 1))
                                        ymax = max(0, min(ymax, img_h))

                                        if xmax > xmin and ymax > ymin:
                                            plate_crop = image.crop((xmin, ymin, xmax, ymax))
                                            st.image(plate_crop, caption="Plate crop", use_column_width=True)
                                            cropped_shown = True
                                except Exception:
                                    cropped_shown = False

                            if not cropped_shown:
                                # Fallback: show small thumbnail of full image
                                try:
                                    thumb = image.copy()
                                    thumb.thumbnail((300, 200))
                                    st.image(thumb, caption="Vehicle (thumbnail)", use_column_width=True)
                                except Exception:
                                    st.write("(No image preview)")

                        with right:
                            st.metric("Plate Number", plate or "-")
                            st.metric("Confidence", f"{confidence:.1f}%")
                            st.metric("Vehicle Type", vehicle_type)

                            # Show candidate list if present
                            candidates = res.get('candidates') or []
                            if candidates:
                                st.write("**Candidates:**")
                                for cand in candidates:
                                    p = cand.get('plate', '').upper()
                                    s = cand.get('score', cand.get('confidence', 0))
                                    try:
                                        s_pct = float(s) * 100
                                    except Exception:
                                        s_pct = 0.0
                                    st.write(f"- {p} — {s_pct:.1f}%")

                        # Show raw JSON if needed
                        with st.expander("See Raw Data"):
                            st.json(res)
