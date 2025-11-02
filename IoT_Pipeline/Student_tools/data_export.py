#!/usr/bin/env python3
"""
Student Data Export Tool
Exports your team's sensor data from MongoDB for analysis
"""

import json
import csv
from datetime import datetime, timedelta
from pymongo import MongoClient
import sys

# ============================================================================
# CONFIGURATION - STUDENTS UPDATE THIS
# ============================================================================

# Your team's MongoDB connection string (get from instructor)
MONGODB_URI = "mongodb+srv://patrikas:FMVOBSwdqFsu4iCF@cluster0.inpz4xy.mongodb.net/?appName=Cluster0"

# Your team's database name
DATABASE_NAME = "workshop_team01"

# Collection name (usually "sensor_data")
COLLECTION_NAME = "sensor_data"

# Export format: "json", "csv", or "both"
EXPORT_FORMAT = "both"

# Export filename (without extension)
OUTPUT_FILENAME = "team01_sensor_data"

# ============================================================================
# FILTER OPTIONS (Optional)
# ============================================================================

# Time range filter (set to None to get all data)
# Examples:
#   HOURS_TO_EXPORT = 24      # Last 24 hours only
#   HOURS_TO_EXPORT = None    # All data
HOURS_TO_EXPORT = None

# Limit number of documents (set to None for all)
# Examples:
#   MAX_DOCUMENTS = 1000      # Only get 1000 most recent
#   MAX_DOCUMENTS = None      # Get all documents
MAX_DOCUMENTS = None

# ============================================================================
# FUNCTIONS
# ============================================================================


def connect_to_database():
    """Connect to MongoDB and return collection"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")

        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        print(f"✓ Connected to MongoDB")
        print(f"  Database: {DATABASE_NAME}")
        print(f"  Collection: {COLLECTION_NAME}")

        return client, collection

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPlease check:")
        print("  1. MongoDB URI is correct")
        print("  2. Password is correct")
        print("  3. You have internet connection")
        sys.exit(1)


def build_query():
    """Build MongoDB query based on filters"""
    query = {}

    # Add time range filter if specified
    if HOURS_TO_EXPORT is not None:
        cutoff_time = datetime.utcnow() - timedelta(hours=HOURS_TO_EXPORT)
        query["timestamp"] = {"$gte": cutoff_time}
        print(f"  Filtering: Last {HOURS_TO_EXPORT} hours")

    return query


def export_to_json(data, filename):
    """Export data to JSON file"""
    try:
        # Convert datetime objects to ISO strings for JSON compatibility
        json_data = []
        for doc in data:
            doc_copy = doc.copy()

            # Convert ObjectId to string
            if "_id" in doc_copy:
                doc_copy["_id"] = str(doc_copy["_id"])

            # Convert datetime objects to ISO strings
            for key, value in doc_copy.items():
                if isinstance(value, datetime):
                    doc_copy[key] = value.isoformat() + "Z"

            json_data.append(doc_copy)

        # Write to file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported to JSON: {filename}")
        print(f"  Documents: {len(json_data)}")

    except Exception as e:
        print(f"✗ JSON export failed: {e}")


def export_to_csv(data, filename):
    """Export data to CSV file"""
    try:
        if not data:
            print("✗ No data to export to CSV")
            return

        # Get all unique field names from all documents
        fieldnames = set()
        for doc in data:
            fieldnames.update(doc.keys())

        # Remove _id from fieldnames (not useful in CSV)
        fieldnames.discard("_id")

        # Convert to sorted list
        fieldnames = sorted(list(fieldnames))

        # Write CSV
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")

            # Write header
            writer.writeheader()

            # Write data rows
            for doc in data:
                # Convert datetime objects to strings
                row = {}
                for key, value in doc.items():
                    if key == "_id":
                        continue
                    elif isinstance(value, datetime):
                        row[key] = value.isoformat() + "Z"
                    else:
                        row[key] = value

                writer.writerow(row)

        print(f"✓ Exported to CSV: {filename}")
        print(f"  Documents: {len(data)}")
        print(f"  Columns: {len(fieldnames)}")

    except Exception as e:
        print(f"✗ CSV export failed: {e}")


def print_summary(data):
    """Print summary statistics about the data"""
    if not data:
        print("\n⚠ No data found!")
        return

    print(f"\n{'='*60}")
    print("DATA SUMMARY")
    print(f"{'='*60}")

    # Count documents
    print(f"Total documents: {len(data)}")

    # Get all unique fields
    all_fields = set()
    for doc in data:
        all_fields.update(doc.keys())

    all_fields.discard("_id")
    all_fields.discard("timestamp")
    all_fields.discard("timestamp_readable")
    all_fields.discard("team")
    all_fields.discard("topic")

    print(f"Sensor fields found: {', '.join(sorted(all_fields))}")

    # Time range
    if data:
        timestamps = [doc.get("timestamp") for doc in data if "timestamp" in doc]
        timestamps = [ts for ts in timestamps if ts is not None]

        if timestamps:
            oldest = min(timestamps)
            newest = max(timestamps)
            duration = newest - oldest

            print(f"\nTime range:")
            print(f"  Oldest: {oldest.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Newest: {newest.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Duration: {duration}")

    # Sample data (first document)
    print(f"\nSample document:")
    sample = data[0].copy()
    sample.pop("_id", None)
    for key, value in list(sample.items())[:5]:  # Show first 5 fields
        if isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {key}: {value}")

    if len(sample) > 5:
        print(f"  ... and {len(sample) - 5} more fields")


def main():
    """Main export function"""
    print("=" * 60)
    print("Student Data Export Tool")
    print("=" * 60)
    print()

    # Connect to database
    client, collection = connect_to_database()

    # Build query
    query = build_query()

    # Fetch data
    print(f"\nFetching data...")
    try:
        cursor = collection.find(query).sort("timestamp", -1)

        # Apply limit if specified
        if MAX_DOCUMENTS is not None:
            cursor = cursor.limit(MAX_DOCUMENTS)
            print(f"  Limiting to {MAX_DOCUMENTS} documents")

        # Convert cursor to list
        data = list(cursor)

        if not data:
            print("\n⚠ No data found with current filters!")
            print("\nTroubleshooting:")
            print("  1. Check if ESP32 is sending data")
            print("  2. Check bridge is running")
            print("  3. Try removing time filter (set HOURS_TO_EXPORT = None)")
            client.close()
            sys.exit(0)

        print(f"✓ Retrieved {len(data)} documents")

    except Exception as e:
        print(f"✗ Data fetch failed: {e}")
        client.close()
        sys.exit(1)

    # Print summary
    print_summary(data)

    # Export based on format
    print(f"\n{'='*60}")
    print("EXPORTING DATA")
    print(f"{'='*60}")

    if EXPORT_FORMAT in ["json", "both"]:
        json_filename = f"{OUTPUT_FILENAME}.json"
        export_to_json(data, json_filename)

    if EXPORT_FORMAT in ["csv", "both"]:
        csv_filename = f"{OUTPUT_FILENAME}.csv"
        export_to_csv(data, csv_filename)

    # Close connection
    client.close()

    print(f"\n{'='*60}")
    print("✓ EXPORT COMPLETE!")
    print(f"{'='*60}")

    if EXPORT_FORMAT == "both":
        print(f"\nYour data has been exported to:")
        print(f"  • {OUTPUT_FILENAME}.json (for Python/JavaScript)")
        print(f"  • {OUTPUT_FILENAME}.csv (for Excel/Pandas)")
    else:
        print(f"\nYour data has been exported to:")
        print(f"  • {OUTPUT_FILENAME}.{EXPORT_FORMAT}")

    print("\nNext steps:")
    print("  • Open CSV in Excel for charts")
    print("  • Use Python/Pandas for analysis")
    print("  • Import JSON into visualization tools")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Export cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
