#!/usr/bin/env python

"""
Project-level overrides for prompts and temperatures.

Only define keys you want to override; missing keys fall back to built-in
defaults in `src/showroom_tool/prompts.py`.

Keys supported (refactored names):
- SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT
- SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT
- SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT
- SHOWROOM_SUMMARY_TEMPERATURE
- SHOWROOM_REVIEW_TEMPERATURE
- SHOWROOM_DESCRIPTION_TEMPERATURE
"""

# Example prompt overrides (uncomment and customize):
# SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT = """
# Your customized summary system prompt...
# """

# SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT = """
# Your customized review system prompt...
# """

# SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT = """
# Your customized description system prompt...
# """

# Per-action temperatures (optional; floats)
# SHOWROOM_SUMMARY_TEMPERATURE = 0.1
# SHOWROOM_REVIEW_TEMPERATURE = 0.1
# SHOWROOM_DESCRIPTION_TEMPERATURE = 0.1


