"""Script to import tyre data from CSV into the database."""
import os
import sys
import csv
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.tyre import Tyre


def import_tyres_from_csv(csv_path: str = "tyres/tyre_db.csv", db_path: str = "data/app.db", clear_existing: bool = True):
    """
    Import tyres from CSV file into the database.
    
    Args:
        csv_path: Path to the CSV file
        db_path: Path to the database file
        clear_existing: If True, clear existing tyres before importing (default: True)
    """
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False
    
    # Initialize tyre model
    tyre_model = Tyre(db_path)
    
    # Check if data already exists and clear if needed
    existing_count = tyre_model.get_count()
    if existing_count > 0:
        if clear_existing:
            print(f"Clearing {existing_count} existing tyre records...")
            success, message = tyre_model.clear_all()
            if not success:
                print(f"Error clearing existing data: {message}")
                return False
            print("Existing records cleared successfully.")
        else:
            response = input(f"Database already contains {existing_count} tyres. Clear and reimport? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                print("Clearing existing tyre records...")
                success, message = tyre_model.clear_all()
                if not success:
                    print(f"Error clearing existing data: {message}")
                    return False
                print("Existing records cleared successfully.")
            else:
                print("Import cancelled.")
                return False
    
    # Read and import CSV
    print(f"Reading CSV file: {csv_path}")
    imported_count = 0
    error_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            # Try to detect delimiter, default to comma if detection fails
            sample = csvfile.read(4096)  # Read more for better detection
            csvfile.seek(0)
            delimiter = ','  # Default to comma
            try:
                sniffer = csv.Sniffer()
                detected = sniffer.sniff(sample)
                delimiter = detected.delimiter
            except (csv.Error, Exception):
                # If detection fails, use comma as default
                delimiter = ','
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Process each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Import the row
                success, message = tyre_model.import_from_csv_row(row)
                if success:
                    imported_count += 1
                    if imported_count % 1000 == 0:
                        print(f"  Imported {imported_count} tyres...")
                else:
                    error_count += 1
                    if error_count <= 10:  # Only show first 10 errors
                        print(f"  Error on row {row_num}: {message}")
            
            print(f"\nImport complete!")
            print(f"  Successfully imported: {imported_count} tyres")
            if error_count > 0:
                print(f"  Errors: {error_count} rows")
            
            return True
    
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to import tyres."""
    print("=" * 60)
    print("Tyre Import Script")
    print("=" * 60)
    
    csv_path = "tyres/tyre_db.csv"
    db_path = "data/app.db"
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"\nError: CSV file not found at '{csv_path}'")
        print("Please ensure the CSV file exists in the tyres directory.")
        return
    
    # Ask about clearing existing data
    print(f"\nCSV file: {csv_path}")
    print(f"Database: {db_path}")
    print("\nNote: This will clear all existing tyre records and import new data from the CSV.")
    
    # Import tyres (default: clear existing data)
    success = import_tyres_from_csv(csv_path, db_path, clear_existing=True)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Tyre import completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Tyre import failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

