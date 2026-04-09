#!/bin/bash

# Pre-commit check script for Rowing Catch
# This script runs linting, formatting, type-checking, and tests.

# Exit immediately if a command exits with a non-zero status.
set -e

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Pre-Commit Pipeline ===${NC}"
echo -e "${BLUE}Tip: To auto-fix issues, run:${NC}"
echo -e "${BLUE}  ruff check . --fix && ruff format .  # Fix linting and formatting issues${NC}"
echo ""

# Source virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}Error: .venv not found. Please create it first.${NC}"
    exit 1
fi

# 1. Linting with Ruff
echo -e "\n${BLUE}Step 1: Linting (Ruff)${NC}"
ruff check .

# 2. Formatting Check with Ruff
echo -e "\n${BLUE}Step 2: Formatting Check (Ruff)${NC}"
ruff format --check .

# 3. Type Checking with Mypy
echo -e "\n${BLUE}Step 3: Type Checking (Mypy)${NC}"
mypy .

# 4. Testing with Pytest
echo -e "\n${BLUE}Step 4: Running Tests (Pytest)${NC}"
pytest

echo -e "\n${GREEN}✔ All checks passed successfully!${NC}"
