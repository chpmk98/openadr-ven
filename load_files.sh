#!/bin/bash

directory="./files_to_load"
port=""

for file in "$directory"/*; do
  ampy --port $port put file
done

