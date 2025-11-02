#!/usr/bin/env python3
"""
Reset and Setup MongoDB TimeSeries Databases
Safely deletes existing workshop databases and recreates them with TimeSeries configuration
"""

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure
from datetime import datetime
import sys
import time

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Admin connection string
MONGODB_ADMIN_URI = "mongodb+srv://patrikas:FMVOBSwdqFsu4iCF@cluster0.inpz4xy.mongodb.net/?appName=Cluster0"

# Team configuration
TEAMS = [
    "team01",
    "team02",
    "team03",
    "team04",
    "team05",
    "team06",
    "team07",
    "team08",
    "team09",
    "team10",
]

# Collection configuration
COLLECTION_NAME = "sensor_data"
TIME_FIELD = "timestamp"
META_FIELD = "team"

# Safety settings
REQUIRE_CONFIRMATION = True  # Set to False to skip confirmation prompt

# ============================================================================
# FUNCTIONS
# ============================================================================


def list_existing_databases(client):
    """
    List all existing workshop databases

    Args:
        client: MongoClient instance

    Returns:
        list: Workshop database names
    """
    all_dbs = client.list_database_names()
    workshop_dbs = [db for db in all_dbs if db.startswith("workshop_")]
    return workshop_dbs


def get_database_info(client, db_name):
    """
    Get information about a database

    Args:
        client: MongoClient instance
        db_name: Database name

    Returns:
        dict: Database information
    """
    try:
        db = client[db_name]
        stats = db.command("dbStats")
        collections = db.list_collection_names()

        # Get document count
        doc_count = 0
        if COLLECTION_NAME in collections:
            doc_count = db[COLLECTION_NAME].count_documents({})

        # Check if TimeSeries
        is_timeseries = False
        if COLLECTION_NAME in collections:
            coll_info = list(db.list_collections(filter={"name": COLLECTION_NAME}))[0]
            is_timeseries = coll_info.get("type") == "timeseries"

        return {
            "name": db_name,
            "size_bytes": stats.get("dataSize", 0),
            "size_mb": stats.get("dataSize", 0) / (1024 * 1024),
            "collections": collections,
            "doc_count": doc_count,
            "is_timeseries": is_timeseries,
        }
    except Exception as e:
        return {"name": db_name, "error": str(e)}


def delete_database(client, db_name):
    """
    Delete a database

    Args:
        client: MongoClient instance
        db_name: Database name to delete

    Returns:
        bool: True if successful
    """
    try:
        client.drop_database(db_name)
        print(f"  ✓ Deleted: {db_name}")
        return True
    except Exception as e:
        print(f"  ✗ Error deleting {db_name}: {e}")
        return False


def create_timeseries_collection(client, team_name):
    """
    Create a TimeSeries collection for a team

    Args:
        client: MongoClient instance
        team_name: Team identifier

    Returns:
        bool: True if successful
    """
    db_name = f"workshop_{team_name}"

    try:
        db = client[db_name]

        # Create TimeSeries collection
        db.create_collection(
            COLLECTION_NAME,
            timeseries={
                "timeField": TIME_FIELD,
                "metaField": META_FIELD,
                "granularity": "seconds",
            },
        )

        # Insert welcome document with proper Date object
        collection = db[COLLECTION_NAME]
        welcome_doc = {
            TIME_FIELD: datetime.utcnow(),  # BSON Date object
            META_FIELD: team_name,
            "message": f"Welcome {team_name}! Your TimeSeries database is ready.",
            "sensor_type": "system",
            "setup_time": datetime.utcnow(),
        }

        collection.insert_one(welcome_doc)
        print(f"  ✓ Created: {db_name} (TimeSeries)")
        return True

    except Exception as e:
        print(f"  ✗ Error creating {db_name}: {e}")
        return False


def print_summary(existing_dbs):
    """Print summary of existing databases"""
    print(f"\n{'='*70}")
    print("EXISTING DATABASES FOUND")
    print(f"{'='*70}")

    if not existing_dbs:
        print("No workshop databases found.")
        return

    total_size = 0
    total_docs = 0

    print(f"\n{'Database':<30} {'Type':<15} {'Docs':<10} {'Size':<10}")
    print("-" * 70)

    for db_info in existing_dbs:
        if "error" in db_info:
            print(f"{db_info['name']:<30} ERROR: {db_info['error']}")
            continue

        db_type = "TimeSeries" if db_info["is_timeseries"] else "Regular"
        size_str = f"{db_info['size_mb']:.2f} MB"

        print(
            f"{db_info['name']:<30} {db_type:<15} {db_info['doc_count']:<10} {size_str:<10}"
        )

        total_size += db_info["size_mb"]
        total_docs += db_info["doc_count"]

    print("-" * 70)
    print(f"{'TOTAL':<30} {'':<15} {total_docs:<10} {total_size:.2f} MB")
    print()


def confirm_deletion():
    """Ask user to confirm deletion"""
    print(f"\n{'='*70}")
    print("⚠️  WARNING: DESTRUCTIVE OPERATION")
    print(f"{'='*70}")
    print("This will DELETE all existing workshop databases and recreate them.")
    print("All existing data will be PERMANENTLY LOST.")
    print()

    response = input("Are you sure you want to continue? Type 'DELETE' to confirm: ")

    return response.strip() == "DELETE"


def main():
    """Main function"""
    print("=" * 70)
    print("Reset and Setup MongoDB TimeSeries Databases")
    print("=" * 70)
    print(f"Teams to configure: {len(TEAMS)}")
    print(f"Teams: {', '.join(TEAMS)}")
    print("=" * 70)
    print()

    # Validate configuration
    if "YOUR_PASSWORD" in MONGODB_ADMIN_URI or "xxxxx" in MONGODB_ADMIN_URI:
        print("✗ ERROR: Please update MONGODB_ADMIN_URI with your actual credentials!")
        sys.exit(1)

    # Connect to MongoDB
    print("Connecting to MongoDB Atlas...")
    try:
        client = MongoClient(MONGODB_ADMIN_URI, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        print("✓ Connected successfully!")

        # Check MongoDB version
        server_info = client.server_info()
        version = server_info.get("version", "unknown")
        print(f"  MongoDB version: {version}")

        version_parts = version.split(".")
        major_version = int(version_parts[0]) if version_parts else 0

        if major_version < 5:
            print(f"\n⚠  WARNING: TimeSeries requires MongoDB 5.0+")
            print(f"   Your version: {version}")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    # List existing databases
    print("\nScanning for existing workshop databases...")
    existing_db_names = list_existing_databases(client)

    if not existing_db_names:
        print("No existing workshop databases found.")
        print("\nProceeding with fresh setup...")
    else:
        print(f"Found {len(existing_db_names)} existing workshop databases.")

        # Get detailed info about each database
        existing_db_info = []
        for db_name in existing_db_names:
            print(f"  Analyzing {db_name}...", end="\r")
            info = get_database_info(client, db_name)
            existing_db_info.append(info)

        print(" " * 50, end="\r")  # Clear the line

        # Print summary
        print_summary(existing_db_info)

        # Confirm deletion
        if REQUIRE_CONFIRMATION:
            if not confirm_deletion():
                print("\n❌ Operation cancelled by user.")
                client.close()
                sys.exit(0)

        # Delete existing databases
        print(f"\n{'='*70}")
        print("DELETING EXISTING DATABASES")
        print(f"{'='*70}")

        delete_count = 0
        for db_name in existing_db_names:
            if delete_database(client, db_name):
                delete_count += 1
            time.sleep(0.1)  # Small delay to avoid overwhelming MongoDB

        print(f"\n✓ Deleted {delete_count}/{len(existing_db_names)} databases")

    # Create new TimeSeries databases
    print(f"\n{'='*70}")
    print("CREATING NEW TIMESERIES DATABASES")
    print(f"{'='*70}")
    print()

    success_count = 0
    failed_teams = []

    for team in TEAMS:
        if create_timeseries_collection(client, team):
            success_count += 1
        else:
            failed_teams.append(team)
        time.sleep(0.1)  # Small delay between creations

    # Verify new databases
    print(f"\n{'='*70}")
    print("VERIFICATION")
    print(f"{'='*70}")
    print()

    new_db_names = list_existing_databases(client)
    new_db_info = []

    for db_name in new_db_names:
        info = get_database_info(client, db_name)
        new_db_info.append(info)

    verified_count = 0
    print(f"{'Database':<30} {'Type':<15} {'Status':<10}")
    print("-" * 70)

    for info in new_db_info:
        if "error" in info:
            print(f"{info['name']:<30} ERROR           ✗ Failed")
            continue

        db_type = "TimeSeries" if info["is_timeseries"] else "Regular"
        status = "✓ OK" if info["is_timeseries"] else "✗ Wrong type"

        print(f"{info['name']:<30} {db_type:<15} {status:<10}")

        if info["is_timeseries"]:
            verified_count += 1

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Successfully created: {success_count}/{len(TEAMS)} databases")
    print(f"Successfully verified: {verified_count}/{len(TEAMS)} databases")

    if failed_teams:
        print(f"\n⚠️  Failed teams: {', '.join(failed_teams)}")

    if verified_count == len(TEAMS):
        print("\n✅ All TimeSeries databases are ready!")
        print("\nNext steps:")
        print("  1. Update your MQTT bridge (ensure it uses new Date())")
        print("  2. Restart the bridge")
        print("  3. Test with: node test_mqtt_bridge.js")
        print()
        print("Bridge timestamp code should be:")
        print("  data.timestamp = new Date();  // Date object, not string!")
    else:
        print("\n⚠️  Some databases need attention. Check errors above.")

    # Close connection
    client.close()
    print("\n✓ Connection closed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
