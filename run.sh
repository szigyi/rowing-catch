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

./check_in_check.sh

# 5. Launch App (Final manual check)
echo -e "\n${BLUE}Final Step: Launching App for manual verification...${NC}"
echo -e "${BLUE}(Press Ctrl+C to exit)${NC}"
streamlit run app.py