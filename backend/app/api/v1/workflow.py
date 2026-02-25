from fastapi import APIRouter, HTTPException, Depends
import pandas as pd
import io
import logging
from datetime import datetime

from app.core.supabase import get_supabase_anon
from app.api.v1.auth import get_current_user
from app.schemas.workflow import ValidationRequest, ValidationResponse, ReportPeriod
from app.core.config import settings

router = APIRouter(tags=["Workflow"])
logger = logging.getLogger(__name__)

# Get bucket name from settings
BUCKET_NAME = settings.SUPABASE_STORAGE_BUCKET


@router.post("/validate-inputs", response_model=ValidationResponse)
async def validate_inputs(
    request: ValidationRequest,
    user=Depends(get_current_user)
):
    """
    Step 1: Validate observation + shapefile for the SPECIFIED reporting period
    """
    print("\n" + "="*60)
    print("🔍 WORKFLOW VALIDATION STARTED")
    print("="*60)
    
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")
    
    print(f"👤 User ID: {user_id}")
    print(f"🪣 Using bucket: {BUCKET_NAME}")
    print(f"📊 Validating for week: {request.report_week}, year: {request.report_year}")
    print(f"📅 Period: {request.report_start_at} to {request.report_end_at}")
    
    # =========================
    # DEBUG: Check ALL user uploads first
    # =========================
    print("\n" + "-"*40)
    print("📋 CHECKING ALL USER UPLOADS")
    print("-"*40)
    
    try:
        all_uploads = supabase.table("uploads")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        print(f"📊 Total uploads for user: {len(all_uploads.data)}")
        
        if all_uploads.data:
            print("\n📁 ALL UPLOADS:")
            for i, upload in enumerate(all_uploads.data):
                print(f"  {i+1}. File: {upload.get('file_name')}")
                print(f"     Type: {upload.get('file_type')}")
                print(f"     Week: {upload.get('report_week')}")
                print(f"     Year: {upload.get('report_year')}")
                print(f"     Start: {upload.get('report_start_at')}")
                print(f"     End: {upload.get('report_end_at')}")
                print(f"     ID: {upload.get('id')}")
                print(f"     Path: {upload.get('file_path')}")
                print("     ---")
        else:
            print("❌ No uploads found for this user!")
            
    except Exception as e:
        print(f"❌ Error fetching all uploads: {e}")
    
    # =========================
    # DEBUG: Check observation files only
    # =========================
    print("\n" + "-"*40)
    print("📋 CHECKING OBSERVATION FILES ONLY")
    print("-"*40)
    
    try:
        obs_files = supabase.table("uploads")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("file_type", "observations")\
            .execute()
        
        print(f"📊 Total observation files: {len(obs_files.data)}")
        
        if obs_files.data:
            print("\n📁 OBSERVATION FILES:")
            for i, obs in enumerate(obs_files.data):
                print(f"  {i+1}. File: {obs.get('file_name')}")
                print(f"     Week: {obs.get('report_week')}")
                print(f"     Year: {obs.get('report_year')}")
                print(f"     Start: {obs.get('report_start_at')}")
                print(f"     End: {obs.get('report_end_at')}")
                print("     ---")
        else:
            print("❌ No observation files found!")
            
    except Exception as e:
        print(f"❌ Error fetching observation files: {e}")
    
    # =========================
    # 1️⃣ FIND OBSERVATION FILE for SPECIFIED report week/year
    # =========================
    print("\n" + "-"*40)
    print(f"🔍 LOOKING FOR WEEK {request.report_week} OBSERVATION FILE")
    print("-"*40)
    
    print(f"🔍 Query filters:")
    print(f"   - user_id: {user_id}")
    print(f"   - file_type: observations")  # ✅ FIXED: plural
    print(f"   - report_week: {request.report_week}")
    print(f"   - report_year: {request.report_year}")
    
    try:
        uploads_response = supabase.table("uploads")\
            .select("id,file_name,file_path,uploaded_at,report_week,report_year,report_start_at,report_end_at")\
            .eq("user_id", user_id)\
            .eq("file_type", "observations")\
            .eq("report_week", request.report_week)\
            .eq("report_year", request.report_year)\
            .order("uploaded_at", desc=True)\
            .limit(1)\
            .execute()
        
        uploads = uploads_response.data or []
        print(f"📊 Query returned {len(uploads)} results")
        
        if uploads:
            print(f"✅ Found: {uploads[0].get('file_name')}")
        else:
            print(f"❌ No file found for week {request.report_week}")
            
    except Exception as e:
        print(f"❌ Error in query: {e}")
        uploads = []

    if not uploads:
        print("\n❌ VALIDATION FAILED: No observation file found")
        raise HTTPException(
            status_code=404, 
            detail=f"No observation file found for week {request.report_week}, {request.report_year}. Please upload the observation file for this reporting period."
        )

    obs = uploads[0]
    print(f"\n✅ Using observation file: {obs['file_name']}")
    print(f"   Week: {obs['report_week']}")
    print(f"   Path: {obs['file_path']}")

    # =========================
    # 2️⃣ FIND SHAPEFILE
    # =========================
    print("\n" + "-"*40)
    print("🗺️ LOOKING FOR SHAPEFILE")
    print("-"*40)
    
    try:
        shapes_response = supabase.table("shared_files")\
            .select("id,file_name,file_path,upload_date")\
            .eq("file_type", "shapefile")\
            .order("upload_date", desc=True)\
            .limit(1)\
            .execute()
        
        shapes = shapes_response.data or []
        print(f"📊 Found {len(shapes)} shapefiles")
        
        if shapes:
            print(f"✅ Using shapefile: {shapes[0].get('file_name')}")
        else:
            print("❌ No shapefile found")
            
    except Exception as e:
        print(f"❌ Error fetching shapefiles: {e}")
        shapes = []

    if not shapes:
        raise HTTPException(status_code=404, detail="No shapefile uploaded. Please contact administrator.")

    shp = shapes[0]

    # =========================
    # 3️⃣ DOWNLOAD OBSERVATION FILE
    # =========================
    print("\n" + "-"*40)
    print("⬇️ DOWNLOADING OBSERVATION FILE")
    print("-"*40)
    
    try:
        file_path = obs["file_path"]
        print(f"📁 File path: {file_path}")
        print(f"🪣 Using bucket: {BUCKET_NAME}")
        
        # Download file from storage using the configured bucket
        file_data = supabase.storage.from_(BUCKET_NAME).download(file_path)
        print(f"✅ Download successful: {len(file_data)} bytes")
        
        # Read CSV from bytes
        df = pd.read_csv(io.BytesIO(file_data))
        print(f"📊 CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"📋 Columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Failed to read observation file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read observation file: {str(e)}")

    # =========================
    # 4️⃣ DETECT VARIABLES
    # =========================
    print("\n" + "-"*40)
    print("🔎 DETECTING VARIABLES")
    print("-"*40)
    
    possible_vars = {
        "rainfall": ["rain", "rainfall", "precip", "precipitation", "rr"],
        "tmin": ["tmin", "min_temp", "minimum_temperature", "tn"],
        "tmax": ["tmax", "max_temp", "maximum_temperature", "tx"],
        "wind": ["wind", "wind_speed", "windspeed", "ff"],
        "humidity": ["humidity", "rh", "relative_humidity"],
        "pressure": ["pressure", "pres", "atmospheric_pressure"],
    }

    cols = [str(c).lower().strip() for c in df.columns]
    print(f"📋 Lowercase columns: {cols}")
    
    found = []

    for var, aliases in possible_vars.items():
        for alias in aliases:
            if any(alias in col for col in cols):
                found.append(var)
                print(f"✅ Found {var} (matched alias: {alias})")
                break

    print(f"📊 Detected variables: {found}")

    # =========================
    # 5️⃣ UPDATE WORKFLOW STATUS
    # =========================
    print("\n" + "-"*40)
    print("💾 UPDATING WORKFLOW STATUS")
    print("-"*40)
    
    try:
        workflow_check = supabase.table("workflow_status")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("report_week", request.report_week)\
            .eq("report_year", request.report_year)\
            .execute()
        
        workflow_data = {
            "validated": True,
            "variables_found": found,
            "observation_file_id": obs["id"],
            "shapefile_id": shp["id"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if workflow_check.data:
            print("🔄 Updating existing workflow record")
            supabase.table("workflow_status")\
                .update(workflow_data)\
                .eq("user_id", user_id)\
                .eq("report_week", request.report_week)\
                .eq("report_year", request.report_year)\
                .execute()
        else:
            print("➕ Creating new workflow record")
            workflow_data.update({
                "user_id": user_id,
                "report_week": request.report_week,
                "report_year": request.report_year,
                "report_start_at": request.report_start_at,
                "report_end_at": request.report_end_at,
                "uploaded": True,
                "created_at": datetime.utcnow().isoformat()
            })
            supabase.table("workflow_status")\
                .insert(workflow_data)\
                .execute()
        
        print("✅ Workflow status updated")
                
    except Exception as e:
        print(f"⚠️ Failed to update workflow status: {e}")

    # =========================
    # 6️⃣ RETURN RESPONSE
    # =========================
    print("\n" + "-"*40)
    print("✅ VALIDATION COMPLETE")
    print("-"*40)
    print(f"📊 Response: {len(found)} variables, {len(df)} rows")
    print("="*60 + "\n")
    
    return ValidationResponse(
        observation_found=True,
        shapefile_found=True,
        variables=found,
        observation_file=obs["file_name"],
        shapefile=shp["file_name"],
        report_week=request.report_week,
        report_year=request.report_year,
        report_period=ReportPeriod(
            start=request.report_start_at,
            end=request.report_end_at
        ),
        column_count=len(df.columns),
        row_count=len(df)
    )
