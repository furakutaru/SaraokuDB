#!/bin/bash
# Check if file exists and get its size
if [ -f "$1" ]; then
    echo "File exists."
    echo "Size: $(stat -f "%z" "$1") bytes"
else
    echo "File does not exist."
fi
