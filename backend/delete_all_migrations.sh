#!/bin/bash
# Script to delete all migration files except __init__.py in each app's migrations directory

set -e

APPS=(accounts core products sales finance reports)

for app in "${APPS[@]}"; do
    MIGRATIONS_DIR="backend/$app/migrations"
    if [ -d "$MIGRATIONS_DIR" ]; then
        find "$MIGRATIONS_DIR" -type f ! -name "__init__.py" -name "*.py" -delete
        find "$MIGRATIONS_DIR" -type f -name "*.pyc" -delete
        echo "Cleaned migrations in $MIGRATIONS_DIR"
    fi
done

echo "All migration files (except __init__.py) deleted." 