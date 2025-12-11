import streamlit as st
import main
from PIL import Image
import io

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
            
            # Call the detection function from main.py
            result = main.detect_plate_data(image_bytes=image_bytes)
            
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
                        plate = res['plate'].upper()
                        confidence = res['score'] * 100
                        vehicle_type = res.get('vehicle', {}).get('type', 'Unknown').capitalize()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Plate Number", plate)
                        with col2:
                            st.metric("Confidence", f"{confidence:.1f}%")
                        with col3:
                            st.metric("Vehicle Type", vehicle_type)
                        
                        # Show raw JSON if needed
                        with st.expander("See Raw Data"):
                            st.json(res)
