"""Test script to validate tyre specification extraction from descriptions."""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.tyre_parser import extract_tyre_specs


def get_random_tyres(db_path: str, count: int = 30) -> list:
    """Get random tyres from the database."""
    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    description,
                    width,
                    profile,
                    diameter,
                    speed_rating,
                    load_index,
                    pattern,
                    oe_fitment
                FROM tyres
                WHERE description IS NOT NULL AND description != ''
                ORDER BY RANDOM()
                LIMIT {count}
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching tyres: {e}")
        return []


def normalize_value(value: str) -> str:
    """Normalize a value for comparison (strip whitespace, handle None/empty)."""
    if value is None:
        return ""
    return str(value).strip().upper()


def compare_values(extracted: str, database: str, field_name: str) -> tuple:
    """Compare extracted value with database value."""
    extracted_norm = normalize_value(extracted)
    database_norm = normalize_value(database)
    match = extracted_norm == database_norm
    return match, extracted_norm, database_norm


def generate_pattern(width: str, profile: str, diameter: str, speed_rating: str) -> str:
    """Generate pattern code from width, profile, diameter, and speed rating."""
    if width and profile and diameter and speed_rating:
        return f"{width}{profile}{diameter}{speed_rating}"
    return ""


def test_extraction(db_path: str = "data/app.db", count: int = 30):
    """Test extraction on random tyres from database."""
    print(f"Testing tyre extraction on {count} random tyres from database...")
    print("=" * 80)
    
    tyres = get_random_tyres(db_path, count)
    
    if not tyres:
        print("No tyres found in database!")
        return
    
    print(f"Found {len(tyres)} tyres to test\n")
    
    # Statistics
    total_tests = 0
    matches = {
        'width': 0,
        'profile': 0,
        'diameter': 0,
        'speed_rating': 0,
        'load_index': 0,
        'pattern': 0,
        'oe_fitment': 0
    }
    
    # Test each tyre
    for i, tyre in enumerate(tyres, 1):
        description = tyre.get('description', '')
        if not description:
            continue
        
        print(f"\n[{i}/{len(tyres)}] Testing: {description[:60]}...")
        
        # Extract specs
        extracted = extract_tyre_specs(description)
        
        if not extracted:
            print(f"  ❌ FAILED: Could not extract specs from description")
            continue
        
        width_ext, profile_ext, diameter_ext, speed_ext, load_ext, oe_ext = extracted
        pattern_ext = generate_pattern(width_ext, profile_ext, diameter_ext, speed_ext)
        
        # Compare each field
        fields_to_check = [
            ('width', width_ext, tyre.get('width')),
            ('profile', profile_ext, tyre.get('profile')),
            ('diameter', diameter_ext, tyre.get('diameter')),
            ('speed_rating', speed_ext, tyre.get('speed_rating')),
            ('load_index', load_ext, tyre.get('load_index')),
            ('pattern', pattern_ext, tyre.get('pattern')),
            ('oe_fitment', oe_ext, tyre.get('oe_fitment'))
        ]
        
        all_match = True
        for field_name, extracted_val, db_val in fields_to_check:
            total_tests += 1
            match, ext_norm, db_norm = compare_values(extracted_val, db_val, field_name)
            
            if match:
                matches[field_name] += 1
            else:
                all_match = False
                if ext_norm or db_norm:  # Only show if at least one has a value
                    print(f"  ⚠ {field_name}: extracted='{extracted_val}' vs db='{db_val}'")
        
        if all_match:
            print(f"  ✅ All fields match!")
        else:
            print(f"  ⚠ Some fields don't match")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if total_tests == 0:
        print("No tests performed!")
        return
    
    print(f"\nTotal field comparisons: {total_tests}")
    print(f"\nField-by-field accuracy:")
    for field, match_count in matches.items():
        field_tests = len(tyres)
        accuracy = (match_count / field_tests * 100) if field_tests > 0 else 0
        print(f"  {field:15s}: {match_count:2d}/{field_tests:2d} ({accuracy:5.1f}%)")
    
    overall_accuracy = sum(matches.values()) / total_tests * 100
    print(f"\nOverall accuracy: {sum(matches.values())}/{total_tests} ({overall_accuracy:.1f}%)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test tyre extraction functionality")
    parser.add_argument("--db", default="data/app.db", help="Database path")
    parser.add_argument("--count", type=int, default=30, help="Number of random tyres to test")
    
    args = parser.parse_args()
    
    test_extraction(args.db, args.count)


