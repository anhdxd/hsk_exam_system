#!/bin/bash
# Pre-deployment test script

echo "Testing Heroku deployment configuration..."

# Set Heroku environment simulation
export DYNO=web.1

# Test Django configuration
echo "1. Checking Django configuration..."
python manage.py check --settings=config.settings_heroku

# Test static files collection
echo "2. Testing static files collection..."
python manage.py collectstatic --noinput --settings=config.settings_heroku

# Test migrations (dry-run)
echo "3. Checking migrations..."
python manage.py showmigrations --settings=config.settings_heroku

echo "Pre-deployment test completed!"
