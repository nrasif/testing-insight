# utils/helpers.py for utility functions used across the app.
# This file contains functions for SVG conversion, string truncation, duration parsing, and formatting.
import pandas as pd
import numpy as np
import re
import urllib.parse

def svg_to_img(icon_svg: str) -> str:
    """Converts a raw SVG string to a data URI for use in <img> tags."""
    encoded_svg = urllib.parse.quote("".join(line.strip() for line in icon_svg.split("\n")))
    return f"data:image/svg+xml;charset=utf-8,{encoded_svg}"

def truncate_feature_name(name, max_words=2):
    """Truncates a string to a maximum number of words, adding '...' if longer."""
    if not isinstance(name, str):
        return ""
    words = name.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + ' ...'
    return name

def duration_to_hours(duration_str):
    """Converts a duration string (e.g., '2 hari 3 jam') to total hours."""
    if not isinstance(duration_str, str) or duration_str.strip() == '':
        return np.nan
    total_hours = 0
    hari_match = re.search(r'(\d+)\s*hari', duration_str)
    if hari_match:
        total_hours += int(hari_match.group(1)) * 24
    jam_match = re.search(r'(\d+)\s*jam', duration_str)
    if jam_match:
        total_hours += int(jam_match.group(1))
    menit_match = re.search(r'(\d+)\s*menit', duration_str)
    if menit_match:
        total_hours += int(menit_match.group(1)) / 60
    return total_hours if total_hours > 0 else np.nan

def format_hours_to_days_hours(total_hours):
    """Formats total hours into a human-readable string (e.g., '2 hari 3 jam')."""
    if pd.isna(total_hours) or total_hours < 0:
        return "N/A"
    if total_hours < 1:
        minutes = round(total_hours * 60)
        return "Kurang dari 1 menit" if minutes == 0 and total_hours > 0 else f"{minutes} menit"
    
    days = int(total_hours // 24)
    remaining_hours = int(total_hours % 24)
    parts = []
    if days > 0:
        parts.append(f"{days} hari")
    if remaining_hours > 0:
        parts.append(f"{remaining_hours} jam")
        
    return " ".join(parts) if parts else "0 jam"
