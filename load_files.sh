#!/bin/bash

directory="./files_to_load"
port="/dev/cu.wchusbserial1410"

for file in "$directory"/*; do
  ampy --port $port put "$file"
done

