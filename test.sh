#!/bin/bash

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run the Python script and capture output
echo "Running test.py..."
python test.py > acutal_departure_arrival_output.txt

# Compare outputs
echo "Comparing departure arrival output..."
if diff -q acutal_departure_arrival_output.txt expected_departure_arrival_output.txt > /dev/null; then
    echo "✅ Output matches expected output."
else
    echo "❌ Output differs from expected output. See differences below:"
    diff acutal_departure_arrival_output.txt expected_departure_arrival_output.txt
fi
