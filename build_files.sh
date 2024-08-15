#!/bin/bash

set -e  # Exit on any error

echo "BUILD START"

# Activate the virtual environment (make sure the path is correct)
source /path/to/your/venv/bin/activate

# Navigate to the Django project directory if not already in it
cd /path/to/your/project

# Upgrade pip
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Create the static directory if it doesn't exist
mkdir -p static

# Collect static files
# python manage.py collectstatic --noinput --clear

echo "BUILD END"
