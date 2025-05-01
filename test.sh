#!/bin/bash

echo "Installing requirements..."
pip install -r requirements.txt

all_passed=true

echo "Running test.py..."
python test.py > acutal_departure_arrival_output.txt

echo "Comparing departure arrival output..."
if diff -q acutal_departure_arrival_output.txt expected_departure_arrival_output.txt > /dev/null; then
    echo "SUCCESS: Actual output matches expected output."
else
    echo "FAILURE: Output differs from expected output. See differences below:"
    diff acutal_departure_arrival_output.txt expected_departure_arrival_output.txt
    all_passed=false
fi

echo "Running survey_data.py..."
python survey_data.py > acutal_survey_analysis_output.txt

echo "Comparing survey data output..."
if diff -q acutal_survey_analysis_output.txt expected_survey_analysis_output.txt > /dev/null; then
    echo "SUCCESS: Actual output matches expected output."
else
    echo "FAILURE: Output differs from expected output. See differences below:"
    diff acutal_survey_analysis_output.txt expected_survey_analysis_output.txt
    all_passed=false
fi

echo "Running RidershipTest.py..."
python RidershipTest.py > acutal_ridership_output.txt

echo "Comparing ridership data output..."
if diff -q acutal_ridership_output.txt expected_ridership_output.txt > /dev/null; then
    echo "SUCCESS: Actual output matches expected output."
else
    echo "FAILURE: Output differs from expected output. See differences below:"
    diff acutal_ridership_output.txt expected_ridership_output.txt
    all_passed=false
fi

if $all_passed; then
    echo "ALL TEST CASES PASSED!"
else
    echo "SOME TEST CASES FAILED."
fi
