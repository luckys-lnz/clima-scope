#!/usr/bin/env python3
"""
Seed script for Kenya counties.

Populates the database with all 47 official Kenya counties with their KNBS codes.
This is reference data and should only be run once during initial setup.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db, Base, engine
from app.models import County
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Official 47 Kenya counties with KNBS codes
KENYA_COUNTIES = [
    {"id": "01", "name": "Mombasa", "region": "Coast"},
    {"id": "02", "name": "Kwale", "region": "Coast"},
    {"id": "03", "name": "Kilifi", "region": "Coast"},
    {"id": "04", "name": "Tana River", "region": "Coast"},
    {"id": "05", "name": "Lamu", "region": "Coast"},
    {"id": "06", "name": "Taita Taveta", "region": "Coast"},
    {"id": "07", "name": "Garissa", "region": "North Eastern"},
    {"id": "08", "name": "Wajir", "region": "North Eastern"},
    {"id": "09", "name": "Mandera", "region": "North Eastern"},
    {"id": "10", "name": "Marsabit", "region": "Eastern"},
    {"id": "11", "name": "Isiolo", "region": "Eastern"},
    {"id": "12", "name": "Meru", "region": "Eastern"},
    {"id": "13", "name": "Tharaka Nithi", "region": "Eastern"},
    {"id": "14", "name": "Embu", "region": "Eastern"},
    {"id": "15", "name": "Kitui", "region": "Eastern"},
    {"id": "16", "name": "Machakos", "region": "Eastern"},
    {"id": "17", "name": "Makueni", "region": "Eastern"},
    {"id": "18", "name": "Nyandarua", "region": "Central"},
    {"id": "19", "name": "Nyeri", "region": "Central"},
    {"id": "20", "name": "Kirinyaga", "region": "Central"},
    {"id": "21", "name": "Murang'a", "region": "Central"},
    {"id": "22", "name": "Kiambu", "region": "Central"},
    {"id": "23", "name": "Turkana", "region": "Rift Valley"},
    {"id": "24", "name": "West Pokot", "region": "Rift Valley"},
    {"id": "25", "name": "Samburu", "region": "Rift Valley"},
    {"id": "26", "name": "Trans Nzoia", "region": "Rift Valley"},
    {"id": "27", "name": "Uasin Gishu", "region": "Rift Valley"},
    {"id": "28", "name": "Elgeyo Marakwet", "region": "Rift Valley"},
    {"id": "29", "name": "Nandi", "region": "Rift Valley"},
    {"id": "30", "name": "Baringo", "region": "Rift Valley"},
    {"id": "31", "name": "Nairobi", "region": "Nairobi"},
    {"id": "32", "name": "Laikipia", "region": "Rift Valley"},
    {"id": "33", "name": "Nakuru", "region": "Rift Valley"},
    {"id": "34", "name": "Narok", "region": "Rift Valley"},
    {"id": "35", "name": "Kajiado", "region": "Rift Valley"},
    {"id": "36", "name": "Kericho", "region": "Rift Valley"},
    {"id": "37", "name": "Bomet", "region": "Rift Valley"},
    {"id": "38", "name": "Kakamega", "region": "Western"},
    {"id": "39", "name": "Vihiga", "region": "Western"},
    {"id": "40", "name": "Bungoma", "region": "Western"},
    {"id": "41", "name": "Busia", "region": "Western"},
    {"id": "42", "name": "Siaya", "region": "Nyanza"},
    {"id": "43", "name": "Kisumu", "region": "Nyanza"},
    {"id": "44", "name": "Homa Bay", "region": "Nyanza"},
    {"id": "45", "name": "Migori", "region": "Nyanza"},
    {"id": "46", "name": "Kisii", "region": "Nyanza"},
    {"id": "47", "name": "Nyamira", "region": "Nyanza"},
]


def seed_counties(force: bool = False):
    """
    Seed counties into the database.
    
    Args:
        force: If True, update existing counties. If False, skip existing ones.
    """
    # Initialize database
    init_db()
    
    db = SessionLocal()
    try:
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for county_data in KENYA_COUNTIES:
            existing = db.query(County).filter(County.id == county_data["id"]).first()
            
            if existing:
                if force:
                    # Update existing county
                    existing.name = county_data["name"]
                    existing.region = county_data["region"]
                    updated_count += 1
                    logger.info("county_updated", county_id=county_data["id"], name=county_data["name"])
                else:
                    skipped_count += 1
                    logger.debug("county_exists", county_id=county_data["id"], name=county_data["name"])
            else:
                # Create new county
                county = County(**county_data)
                db.add(county)
                created_count += 1
                logger.info("county_created", county_id=county_data["id"], name=county_data["name"])
        
        db.commit()
        
        logger.info(
            "counties_seeded",
            total=len(KENYA_COUNTIES),
            created=created_count,
            updated=updated_count,
            skipped=skipped_count,
        )
        
        print(f"\n✅ Counties seeded successfully!")
        print(f"   Total counties: {len(KENYA_COUNTIES)}")
        print(f"   Created: {created_count}")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {skipped_count}\n")
        
        return created_count, updated_count, skipped_count
        
    except Exception as e:
        db.rollback()
        logger.error("county_seeding_failed", error=str(e), exc_info=True)
        print(f"\n❌ Error seeding counties: {e}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Kenya counties into the database")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Update existing counties instead of skipping them"
    )
    
    args = parser.parse_args()
    
    seed_counties(force=args.force)
