#!/bin/bash
set -e

echo "Running detection..."
python main.py

echo "Running interpolation..."
python interpolate_data.py

echo "Running visualization..."
python visualize_data.py

echo "Done! Output saved to out.mp4"
