from fastapi import APIRouter, HTTPException, Depends
import pandas as pd
import io
import logging
import os
from datetime import datetime
from typing import List
from pydantic import BaseModel

from app.core.supabase import get_supabase_anon, get_supabase_admin
from app.api.v1.auth import get_current_user
from app.schemas.workflow import ValidationRequest, ValidationResponse, ReportPeriod
from app.core.config import settings
from app.utils.map_generator import create_weather_map

router = APIRouter(tags=["Workflow"])
logger = logging.getLogger(__name__)

# Get bucket name from settings
BUCKET_NAME = settings.SUPABASE_STORAGE_BUCKET

# ===== Map Generation Schemas =====
class MapGenerationRequest(BaseModel):
    county: str
    variables: List[str]
    report_week: int
    report_year: int
    report_start_at: str
    report_end_at: str

class MapOutput(BaseModel):
    variable: str
    map_url: str

class MapGenerationResponse(BaseModel):
    outputs: List[MapOutput]


# ============================================================================
# STEP 1: VALIDATE INPUTS
# ============================================================================
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
    print(f"   - file_type: observations")
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


# ============================================================================
# STEP 3: GENERATE MAPS
# ============================================================================
@router.post("/generate-maps", response_model=MapGenerationResponse)
async def generate_maps(
    request: MapGenerationRequest,
    user=Depends(get_current_user)
):
    """
    Step 3: Generate maps for each selected variable
    """
    print("\n" + "="*60)
    print("🗺️ MAP GENERATION STARTED")
    print("="*60)
    
    supabase = get_supabase_anon()
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")
    
    print(f"👤 User ID: {user_id}")
    print(f"📍 County: {request.county}")
    print(f"📊 Variables: {request.variables}")
    print(f"📅 Week: {request.report_week}, Year: {request.report_year}")
    print(f"📅 Period: {request.report_start_at} to {request.report_end_at}")
    
    # =========================
    # 1. GET OBSERVATION FILE
    # =========================
    try:
        upload = supabase.table("uploads")\
            .select("id, file_name, file_path")\
            .eq("user_id", user_id)\
            .eq("file_type", "observations")\
            .eq("report_week", request.report_week)\
            .eq("report_year", request.report_year)\
            .order("uploaded_at", desc=True)\
            .limit(1)\
            .execute()
        
        if not upload.data:
            raise HTTPException(
                status_code=404, 
                detail=f"No observation file found for week {request.report_week}"
            )
        
        obs = upload.data[0]
        print(f"✅ Observation file: {obs['file_name']}")
        
    except Exception as e:
        print(f"❌ Error fetching observation file: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch observation file")
    
    # =========================
    # 2. GET ALL SHAPEFILE COMPONENTS FROM shared_files
    # =========================
    try:
        shapefile_records = supabase.table("shared_files")\
            .select("file_name, file_path")\
            .eq("file_type", "shapefile")\
            .execute()
        
        if not shapefile_records.data:
            raise HTTPException(
                status_code=404, 
                detail="No shapefile found. Please contact administrator."
            )
        
        print(f"\n📁 Found {len(shapefile_records.data)} shapefile components:")
        for comp in shapefile_records.data:
            print(f"   - {comp['file_name']}")
        
    except Exception as e:
        print(f"❌ Error fetching shapefiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch shapefiles")
    
    # =========================
    # 3. DOWNLOAD OBSERVATION FILE
    # =========================
    temp_csv = None
    try:
        file_data = supabase.storage.from_(BUCKET_NAME).download(obs["file_path"])
        print(f"\n✅ Downloaded observation: {len(file_data)} bytes")
        
        temp_csv = f"/tmp/weather_data_{user_id}_{request.report_week}.csv"
        with open(temp_csv, 'wb') as f:
            f.write(file_data)
        print(f"✅ Saved temp file: {temp_csv}")
        
    except Exception as e:
        print(f"❌ Error downloading observation file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download observation file")
    
    # =========================
    # 4. DOWNLOAD ALL SHAPEFILE COMPONENTS
    # =========================
    temp_shapefile_dir = None
    local_shapefile_path = None
    
    try:
        import os
        import tempfile
        
        # Create temp directory for all shapefile components
        temp_shapefile_dir = tempfile.mkdtemp(prefix=f"shapefiles_{user_id}_{request.report_week}_")
        print(f"\n✅ Created temp directory: {temp_shapefile_dir}")
        
        # Download each shapefile component
        for component in shapefile_records.data:
            try:
                file_data = supabase.storage.from_(BUCKET_NAME).download(component["file_path"])
                
                # Save to temp directory with original filename
                local_path = os.path.join(temp_shapefile_dir, component["file_name"])
                with open(local_path, 'wb') as f:
                    f.write(file_data)
                
                print(f"✅ Downloaded: {component['file_name']}")
                
                # Store path to .shp file for map generation
                if component["file_name"].endswith('.shp'):
                    local_shapefile_path = local_path
                    
            except Exception as e:
                print(f"⚠️ Failed to download {component['file_name']}: {e}")
                continue
        
        if not local_shapefile_path:
            raise Exception("No .shp file found in downloaded components")
        
        print(f"\n✅ Main shapefile: {os.path.basename(local_shapefile_path)}")
        print(f"✅ All shapefile components downloaded to temp directory")
        
    except Exception as e:
        print(f"❌ Error downloading shapefile components: {e}")
        # Clean up if error occurs
        if temp_shapefile_dir and os.path.exists(temp_shapefile_dir):
            import shutil
            shutil.rmtree(temp_shapefile_dir)
        raise HTTPException(status_code=500, detail=f"Failed to download shapefile: {str(e)}")
    
    # =========================
    # 5. VARIABLE MAPPING
    # =========================
    var_map = {
        "rainfall": "Rain",
        "tmin": "Tmin", 
        "tmax": "Tmax"
    }
    
    # =========================
    # 6. GENERATE MAPS FOR EACH VARIABLE
    # =========================
    outputs = []
    
    for variable in request.variables:
        col_name = var_map.get(variable)
        if not col_name:
            print(f"⚠️ Unknown variable: {variable}, skipping")
            continue
        
        print(f"\n{'='*50}")
        print(f"🔄 Generating {variable} map...")
        print(f"{'='*50}")
        
        try:
            # Generate map with downloaded files
            image_bytes, filename = create_weather_map(
                county_name=request.county if request.county != "—" else None,
                variable=col_name,
                data_file=temp_csv,
                shapefile_path=local_shapefile_path  # Path to .shp file
            )
            
            print(f"✅ Map generated: {filename} ({len(image_bytes)} bytes)")
            
            # Create storage path
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            storage_path = f"users/{user_id}/maps/week_{request.report_week}_{request.report_year}/{variable}_{timestamp}.png"
            
            # Upload to Supabase Storage
            supabase_admin.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=image_bytes,
                file_options={"content-type": "image/png"}
            )
            print(f"✅ Uploaded to storage: {storage_path}")
            
            # ========== FIXED URL GENERATION ==========
            # Try multiple methods to get a working URL
            map_url = None
            
            # Method 1: Signed URL (works for both public and private buckets)
            try:
                signed_result = supabase_admin.storage.from_(BUCKET_NAME).create_signed_url(
                    storage_path, 
                    expires_in=604800  # 1 week in seconds
                )
                map_url = signed_result['signedURL']
                print(f"✅ Generated signed URL (expires in 1 week)")
            except Exception as e:
                print(f"⚠️ Signed URL failed: {e}")
                
                # Method 2: Public URL
                try:
                    map_url = supabase_admin.storage.from_(BUCKET_NAME).get_public_url(storage_path)
                    print(f"✅ Generated public URL")
                except Exception as e2:
                    print(f"⚠️ Public URL failed: {e2}")
                    
                    # Method 3: Manual construction as last resort
                    try:
                        # Extract project ID from Supabase URL
                        project_id = settings.SUPABASE_URL.replace('https://', '').split('.')[0]
                        map_url = f"https://{project_id}.supabase.co/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
                        print(f"✅ Manually constructed URL")
                    except Exception as e3:
                        print(f"❌ All URL methods failed: {e3}")
                        raise Exception("Could not generate accessible URL for map")
            # ===========================================
            
            # Save record to generated_maps table
            map_record = {
                "user_id": user_id,
                "variable": variable,
                "map_url": map_url,
                "storage_path": storage_path,
                "report_week": request.report_week,
                "report_year": request.report_year,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("generated_maps").insert(map_record).execute()
            print(f"✅ Database record saved")
            
            outputs.append(MapOutput(
                variable=variable,
                map_url=map_url
            ))
            
        except Exception as e:
            print(f"❌ Error generating {variable} map: {e}")
            # Continue with other variables
            pass
    
    # =========================
    # 7. CLEAN UP TEMP FILES
    # =========================
    import shutil
    
    # Remove temp CSV
    if temp_csv and os.path.exists(temp_csv):
        os.remove(temp_csv)
        print(f"\n✅ Temp CSV cleaned up")
    
    # Remove shapefile temp directory
    if temp_shapefile_dir and os.path.exists(temp_shapefile_dir):
        shutil.rmtree(temp_shapefile_dir)
        print(f"✅ Shapefile temp directory cleaned up")
    
    print(f"\n{'='*60}")
    print(f"✅ MAP GENERATION COMPLETE: {len(outputs)} maps created")
    print(f"{'='*60}\n")
    
    if not outputs:
        raise HTTPException(status_code=500, detail="No maps were generated successfully")
    
    return MapGenerationResponse(outputs=outputs)
