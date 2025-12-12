#!/bin/bash
# =============================================================================
# Download Sample Video for ANPR Dashboard
# =============================================================================

echo "================================================"
echo "  ANPR Dashboard - Sample Video Download"
echo "================================================"
echo ""

# Check if video already exists
if [ -f "1.mp4" ]; then
    echo "Video file '1.mp4' already exists."
    echo "Delete it first if you want to download a new one."
    exit 0
fi

echo "Note: You need to provide your own traffic video file."
echo ""
echo "Instructions:"
echo "1. Obtain a traffic surveillance video (MP4 format)"
echo "2. Rename it to '1.mp4'"
echo "3. Place it in this directory"
echo ""
echo "Video Requirements:"
echo "- Resolution: 1920x1080 or higher recommended"
echo "- Frame rate: 30 FPS recommended"
echo "- Content: Traffic with visible vehicles and license plates"
echo ""
echo "Example sources:"
echo "- Your own traffic camera footage"
echo "- Dashcam recordings"
echo "- Public traffic datasets"
echo ""
echo "================================================"
