"""Utility functions for parsing tyre descriptions and extracting specifications."""
import re
from typing import Optional, Tuple


def find_valid_speed_rating(description: str, valid_speed_ratings: list) -> str:
    """
    Find a valid speed rating in the description.
    
    Args:
        description: Tyre description text
        valid_speed_ratings: List of valid speed rating codes
    
    Returns:
        Speed rating code or empty string if not found
    """
    for rating in valid_speed_ratings:
        if rating in description:
            return rating
    return ''


def extract_oe_fitment(description: str) -> str:
    """
    Extract OE fitment from description.
    
    Common patterns: *OE*, *MO*, *AO*, (+), etc.
    
    Args:
        description: Tyre description text
    
    Returns:
        OE fitment code or empty string if not found
    """
    # Look for common OE fitment patterns
    oe_patterns = [
        r'\*([A-Z]{2,})\*',  # *MO*, *AO*, etc.
        r'\*\s*$',  # Standalone * at end of description
        r'\(([A-Z+\-]{1,})\)',   # (MO), (AO), (+), (-), etc. - single or multiple chars including + and -
        r'\b([A-Z]{2,})\s*OE',  # MO OE, AO OE, etc.
        r'OE\s*([A-Z]{2,})',  # OE MO, OE AO, etc.
    ]
    
    for i, pattern in enumerate(oe_patterns):
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            # Special case for standalone asterisk
            if i == 1:  # Standalone * pattern
                return '*'
            return match.group(1).upper()
    
    # Common OE fitment codes (2+ letters) - check if they appear at the end or before load/speed
    common_oe_codes = ['MO', 'AO', 'VO', 'RO', 'LR', 'FR', 'N0', 'N1', 'N2', 'N3', 'N4', 'N5']
    words = description.strip().split()
    if words:
        # Check last word for OE codes
        last_word = words[-1].upper().rstrip('.,;:')
        if last_word in common_oe_codes:
            return last_word
        # Check second-to-last word if last is XL/RFT/etc or load/speed rating
        if len(words) > 1:
            if last_word in ['XL', 'RFT', 'RF', 'RUNFLAT', 'ZR', 'ZRF'] or re.match(r'^\d+[A-Z]$', last_word):
                second_last = words[-2].upper().rstrip('.,;:')
                if second_last in common_oe_codes:
                    return second_last
        # Check if any OE code appears as a standalone word before the load/speed
        # Look for pattern: ... MO 110V or ... LR 113Y XL
        for i, word in enumerate(words):
            word_upper = word.upper().rstrip('.,;:')
            if word_upper in common_oe_codes and i < len(words) - 1:
                # Check if next word looks like load/speed (digits + letter)
                next_word = words[i + 1].upper()
                if re.match(r'^\d+[A-Z]$', next_word):
                    return word_upper
    
    # Look for standalone + or - at the end
    desc_stripped = description.strip()
    if desc_stripped.endswith('+'):
        return '+'
    if desc_stripped.endswith('-'):
        return '-'
    
    return ''


def extract_tyre_specs(description: str) -> Optional[Tuple[str, str, str, str, str, str]]:
    """
    Extract all tyre specifications from description.
    
    Expected format examples:
    - "225/45R17 91W"
    - "225/45RF17 91/89W"
    - "225/45Z17 91W *MO*"
    
    Args:
        description: Tyre description text
    
    Returns:
        Tuple of (width, profile, diameter, speed_rating, load_index, oe_fitment)
        Returns None if format is invalid
    """
    if not description or not description.strip():
        return None
    
    # 1. Extract width, profile, diameter
    # Pattern: digits/digits(R|RF|Z|ZRF)digits
    match = re.match(r'(\d+)/(\d+)(R|RF|Z|ZRF)(\d+)', description)
    if not match:
        return None  # Invalid format
    
    width = match.group(1)
    profile = match.group(2)
    diameter = match.group(4)
    
    # 2. Extract load index and speed rating (in priority order)
    valid_speed_ratings = ['N', 'P', 'Q', 'R', 'S', 'T', 'U', 'H', 'V', 'Z', 'W', 'Y']
    load_index = ''
    speed_rating = ''
    
    # Try Pattern 1: Dual load with speed (e.g., "91/89W")
    dual_match = re.search(r'\s+(\d+)/(\d+)([A-Z])', description)
    if dual_match and int(dual_match.group(1)) >= 65 and int(dual_match.group(2)) >= 65:
        load_index = dual_match.group(1) + '/' + dual_match.group(2)
        if dual_match.group(3) in valid_speed_ratings:
            speed_rating = dual_match.group(3)
        else:
            # Search for valid speed elsewhere
            speed_rating = find_valid_speed_rating(description, valid_speed_ratings)
    
    # Try Pattern 2: Single load with speed (e.g., "91W" or "95T")
    # This can appear after text, so search more broadly
    if not load_index:
        # First try immediately after size
        single_match = re.search(r'\s+(\d+)([A-Z])', description)
        if single_match and int(single_match.group(1)) >= 65:
            load_index = single_match.group(1)
            if single_match.group(2) in valid_speed_ratings:
                speed_rating = single_match.group(2)
            else:
                speed_rating = find_valid_speed_rating(description, valid_speed_ratings)
        else:
            # Try anywhere in description (e.g., after brand/model text)
            single_match = re.search(r'\b(\d{2,3})([NPQRSTUHVZWY])\b', description)
            if single_match and int(single_match.group(1)) >= 65 and single_match.group(2) in valid_speed_ratings:
                load_index = single_match.group(1)
                speed_rating = single_match.group(2)
    
    # Try Pattern 3 & 4: Search entire description
    if not load_index:
        # Search for dual load
        for match in re.finditer(r'\b(\d{2,3})/(\d{2,3})([NPQRSTUHVZWY])\b', description):
            if int(match.group(1)) >= 65 and int(match.group(2)) >= 65 and match.group(3) in valid_speed_ratings:
                load_index = match.group(1) + '/' + match.group(2)
                speed_rating = match.group(3)
                break
        
        # Search for single load
        if not load_index:
            for match in re.finditer(r'\b(\d{2,3})([NPQRSTUHVZWY])\b', description):
                if int(match.group(1)) >= 65 and match.group(2) in valid_speed_ratings:
                    load_index = match.group(1)
                    speed_rating = match.group(2)
                    break
    
    # 3. Extract OE fitment
    oe_fitment = extract_oe_fitment(description)
    
    return width, profile, diameter, speed_rating, load_index, oe_fitment


def validate_tyre_description(description: str) -> Tuple[bool, str]:
    """
    Validate that a tyre description is in a format that can be parsed.
    
    Args:
        description: Tyre description text to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not description or not description.strip():
        return False, "Description cannot be empty"
    
    # Check for basic size pattern (width/profileRdiameter)
    match = re.match(r'(\d+)/(\d+)(R|RF|Z|ZRF)(\d+)', description)
    if not match:
        return False, "Description must start with size format (e.g., 225/45R17)"
    
    # Check for load index and speed rating
    valid_speed_ratings = ['N', 'P', 'Q', 'R', 'S', 'T', 'U', 'H', 'V', 'Z', 'W', 'Y']
    has_load_speed = False
    
    # Check for dual load pattern
    dual_match = re.search(r'\s+(\d+)/(\d+)([A-Z])', description)
    if dual_match and int(dual_match.group(1)) >= 65 and int(dual_match.group(2)) >= 65:
        if dual_match.group(3) in valid_speed_ratings:
            has_load_speed = True
    
    # Check for single load pattern (can appear after text, e.g., "95T" after brand/model)
    if not has_load_speed:
        # First try immediately after size
        single_match = re.search(r'\s+(\d+)([A-Z])', description)
        if single_match and int(single_match.group(1)) >= 65:
            if single_match.group(2) in valid_speed_ratings:
                has_load_speed = True
    
    # Check for load/speed elsewhere in description (e.g., after brand/model text)
    if not has_load_speed:
        for match in re.finditer(r'\b(\d{2,3})(?:/(\d{2,3}))?([NPQRSTUHVZWY])\b', description):
            if match.group(2):  # Dual load
                if int(match.group(1)) >= 65 and int(match.group(2)) >= 65:
                    has_load_speed = True
                    break
            else:  # Single load
                if int(match.group(1)) >= 65:
                    has_load_speed = True
                    break
    
    if not has_load_speed:
        return False, "Description must include load index and speed rating (e.g., 91W or 91/89W)"
    
    return True, ""

