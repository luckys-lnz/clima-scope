from fastapi import APIRouter, HTTPException, Depends
import pandas as pd
import io
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.core.supabase import get_supabase_anon, get_supabase_admin
from app.api.v1.auth import get_current_user
from app.schemas.workflow import (
    ValidationRequest,
    ValidationResponse,
    ReportPeriod,
    ReportGenerationRequest,
    ReportGenerationResponse,
)
from app.core.config import settings
from app.utils.map_generator import create_weather_map
from app.utils.report_generator import generate_weekly_forecast_pdf
from app.services.narration_service import (
    generate_report_narration,
    summarize_observation_data,
)

router = APIRouter(tags=["Workflow"])
logger = logging.getLogger(__name__)

# Get bucket name from settings
BUCKET_NAME = settings.SUPABASE_STORAGE_BUCKET


def get_or_create_workflow_status(
    supabase_admin,
    user_id: str,
    report_week: int,
    report_year: int,
    observation_file_id: Optional[str] = None,
) -> Optional[int]:
    """Get existing workflow row for period or create a new one."""
    try:
        existing = (
            supabase_admin.table("workflow_status")
            .select("id")
            .eq("user_id", user_id)
            .eq("report_week", report_week)
            .eq("report_year", report_year)
            .limit(1)
            .execute()
        )
        if existing.data:
            return existing.data[0]["id"]

        insert_payload: Dict[str, Any] = {
            "user_id": user_id,
            "report_week": report_week,
            "report_year": report_year,
            "uploaded": False,
            "aggregated": False,
            "mapped": False,
            "generated": False,
            "completed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        if observation_file_id:
            insert_payload["observation_file_id"] = observation_file_id

        created = supabase_admin.table("workflow_status").insert(insert_payload).execute()
        rows = created.data or []
        if rows:
            return rows[0]["id"]
    except Exception as exc:
        print(f"⚠️ Failed to get/create workflow_status: {exc}")
    return None


def update_workflow_status_flags(
    supabase_admin,
    workflow_status_id: int,
    flags: Dict[str, Any],
) -> None:
    """Update workflow_status with known schema flags only."""
    allowed_keys = {
        "uploaded",
        "aggregated",
        "mapped",
        "generated",
        "completed",
        "observation_file_id",
        "generated_report_id",
    }
    update_payload = {k: v for k, v in flags.items() if k in allowed_keys}
    if not update_payload:
        return
    update_payload["updated_at"] = datetime.utcnow().isoformat()
    try:
        (
            supabase_admin.table("workflow_status")
            .update(update_payload)
            .eq("id", workflow_status_id)
            .execute()
        )
    except Exception as exc:
        print(f"⚠️ Failed to update workflow_status flags: {exc}")


def append_workflow_log(
    supabase_admin,
    workflow_status_id: Optional[int],
    stage: str,
    status: str,
    message: str,
) -> None:
    """Append a workflow log row; non-blocking on failure."""
    if workflow_status_id is None:
        return
    try:
        supabase_admin.table("workflow_logs").insert(
            {
                "workflow_status_id": workflow_status_id,
                "stage": stage,
                "status": status,
                "message": message,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as exc:
        print(f"⚠️ Failed to append workflow log: {exc}")

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
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")
    workflow_status_id: Optional[int] = None
    
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
        workflow_status_id = get_or_create_workflow_status(
            supabase_admin=supabase_admin,
            user_id=user_id,
            report_week=request.report_week,
            report_year=request.report_year,
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="error",
            message="Validation failed: observation file not found",
        )
        raise HTTPException(
            status_code=404, 
            detail=f"No observation file found for week {request.report_week}, {request.report_year}. Please upload the observation file for this reporting period."
        )

    obs = uploads[0]
    workflow_status_id = get_or_create_workflow_status(
        supabase_admin=supabase_admin,
        user_id=user_id,
        report_week=request.report_week,
        report_year=request.report_year,
        observation_file_id=obs["id"],
    )
    append_workflow_log(
        supabase_admin,
        workflow_status_id,
        stage="validate_inputs",
        status="info",
        message="Starting validation for observation and shapefile inputs",
    )
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
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="error",
            message="Validation failed: shapefile not found",
        )
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
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="error",
            message="Validation failed: could not read observation file",
        )
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
    if workflow_status_id is None:
        workflow_status_id = get_or_create_workflow_status(
            supabase_admin=supabase_admin,
            user_id=user_id,
            report_week=request.report_week,
            report_year=request.report_year,
            observation_file_id=obs["id"],
        )
    if workflow_status_id is not None:
        update_workflow_status_flags(
            supabase_admin=supabase_admin,
            workflow_status_id=workflow_status_id,
            flags={
                "uploaded": True,
                "aggregated": True,
                "observation_file_id": obs["id"],
            },
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="success",
            message=f"Validation completed: {len(found)} variables detected",
        )
        print("✅ Workflow status updated")

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
    user=Depends(get_current_user),
):
    """
    Step 3: Generate maps for each selected variable
    """
    print("\n" + "=" * 60)
    print("🗺️ MAP GENERATION STARTED")
    print("=" * 60)

    supabase = get_supabase_anon()
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")
    workflow_status_id: Optional[int] = get_or_create_workflow_status(
        supabase_admin=supabase_admin,
        user_id=user_id,
        report_week=request.report_week,
        report_year=request.report_year,
    )
    append_workflow_log(
        supabase_admin,
        workflow_status_id,
        stage="generate_maps",
        status="info",
        message=f"Starting map generation for {len(request.variables)} variable(s)",
    )

    print(f"👤 User ID: {user_id}")
    print(f"📍 County: {request.county}")
    print(f"📊 Variables: {request.variables}")
    print(f"📅 Week: {request.report_week}, Year: {request.report_year}")
    print(f"📅 Period: {request.report_start_at} to {request.report_end_at}")

    # =========================
    # 1. GET OBSERVATION FILE
    # =========================
    try:
        upload = (
            supabase.table("uploads")
            .select("id, file_name, file_path")
            .eq("user_id", user_id)
            .eq("file_type", "observations")
            .eq("report_week", request.report_week)
            .eq("report_year", request.report_year)
            .order("uploaded_at", desc=True)
            .limit(1)
            .execute()
        )

        if not upload.data:
            raise HTTPException(
                status_code=404,
                detail=f"No observation file found for week {request.report_week}",
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
        shapefile_records = (
            supabase.table("shared_files")
            .select("file_name, file_path")
            .eq("file_type", "shapefile")
            .execute()
        )

        if not shapefile_records.data:
            raise HTTPException(
                status_code=404,
                detail="No shapefile found. Please contact administrator.",
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
        with open(temp_csv, "wb") as f:
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
        # Create temp directory for all shapefile components
        temp_shapefile_dir = tempfile.mkdtemp(
            prefix=f"shapefiles_{user_id}_{request.report_week}_"
        )
        print(f"\n✅ Created temp directory: {temp_shapefile_dir}")

        # Download each shapefile component
        for component in shapefile_records.data:
            try:
                file_data = supabase.storage.from_(BUCKET_NAME).download(
                    component["file_path"]
                )

                # Save to temp directory with original filename
                local_path = os.path.join(temp_shapefile_dir, component["file_name"])
                with open(local_path, "wb") as f:
                    f.write(file_data)

                print(f"✅ Downloaded: {component['file_name']}")

                # Store path to .shp file for map generation
                if component["file_name"].endswith(".shp"):
                    local_shapefile_path = local_path

            except Exception as e:
                print(f"⚠️ Failed to download {component['file_name']}: {e}")
                continue

        if not local_shapefile_path:
            raise Exception("No .shp file found in downloaded components")

        print(f"\n✅ Main shapefile: {os.path.basename(local_shapefile_path)}")
        print("✅ All shapefile components downloaded to temp directory")

    except Exception as e:
        print(f"❌ Error downloading shapefile components: {e}")
        # Clean up if error occurs
        if temp_shapefile_dir and os.path.exists(temp_shapefile_dir):
            import shutil

            shutil.rmtree(temp_shapefile_dir)
        raise HTTPException(
            status_code=500, detail=f"Failed to download shapefile: {str(e)}"
        )

    # =========================
    # 5. VARIABLE MAPPING
    # =========================
    var_map = {
        "rainfall": "Rain",
        "tmin": "Tmin",
        "tmax": "Tmax",
    }

    # =========================
    # 6. GENERATE MAPS FOR EACH VARIABLE
    # =========================
    outputs: List[MapOutput] = []

    for variable in request.variables:
        col_name = var_map.get(variable)
        if not col_name:
            print(f"⚠️ Unknown variable: {variable}, skipping")
            continue

        print(f"\n{'=' * 50}")
        print(f"🔄 Generating {variable} map...")
        print(f"{'=' * 50}")

        try:
            # Generate map with downloaded files
            image_bytes, filename = create_weather_map(
                county_name=request.county if request.county != "—" else None,
                variable=col_name,
                data_file=temp_csv,
                shapefile_path=local_shapefile_path,  # Path to .shp file
            )

            print(f"✅ Map generated: {filename} ({len(image_bytes)} bytes)")

            # Create storage path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            storage_path = (
                f"users/{user_id}/maps/"
                f"week_{request.report_week}_{request.report_year}/{variable}_{timestamp}.png"
            )

            # Upload to Supabase Storage
            supabase_admin.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=image_bytes,
                file_options={"content-type": "image/png"},
            )
            print(f"✅ Uploaded to storage: {storage_path}")

            # ========== URL GENERATION ==========
            map_url = None

            # Method 1: Signed URL
            try:
                signed_result = supabase_admin.storage.from_(BUCKET_NAME).create_signed_url(
                    storage_path,
                    expires_in=604800,  # 1 week in seconds
                )
                map_url = signed_result["signedURL"]
                print("✅ Generated signed URL (expires in 1 week)")
            except Exception as e:
                print(f"⚠️ Signed URL failed: {e}")

                # Method 2: Public URL
                try:
                    map_url = supabase_admin.storage.from_(BUCKET_NAME).get_public_url(
                        storage_path
                    )
                    print("✅ Generated public URL")
                except Exception as e2:
                    print(f"⚠️ Public URL failed: {e2}")

                    # Method 3: Manual construction as last resort
                    try:
                        project_id = (
                            settings.SUPABASE_URL.replace("https://", "").split(".")[0]
                        )
                        map_url = (
                            f"https://{project_id}.supabase.co/storage/v1/"
                            f"object/public/{BUCKET_NAME}/{storage_path}"
                        )
                        print("✅ Manually constructed URL")
                    except Exception as e3:
                        print(f"❌ All URL methods failed: {e3}")
                        raise Exception(
                            "Could not generate accessible URL for map"
                        )

            # Save record to generated_maps table
            map_record = {
                "user_id": user_id,
                "workflow_status_id": workflow_status_id,
                "variable": variable,
                "map_url": map_url,
                "storage_path": storage_path,
                "report_week": request.report_week,
                "report_year": request.report_year,
                "created_at": datetime.utcnow().isoformat(),
            }

            supabase.table("generated_maps").insert(map_record).execute()
            print("✅ Database record saved")

            outputs.append(MapOutput(variable=variable, map_url=map_url))

        except Exception as e:
            print(f"❌ Error generating {variable} map: {e}")
            append_workflow_log(
                supabase_admin,
                workflow_status_id,
                stage="generate_maps",
                status="error",
                message=f"Failed generating map for variable: {variable}",
            )
            # Continue with other variables
            continue

    # =========================
    # 7. CLEAN UP TEMP FILES
    # =========================
    import shutil

    # Remove temp CSV
    if temp_csv and os.path.exists(temp_csv):
        os.remove(temp_csv)
        print("\n✅ Temp CSV cleaned up")

    # Remove shapefile temp directory
    if temp_shapefile_dir and os.path.exists(temp_shapefile_dir):
        shutil.rmtree(temp_shapefile_dir)
        print("✅ Shapefile temp directory cleaned up")

    print(f"\n{'=' * 60}")
    print(f"✅ MAP GENERATION COMPLETE: {len(outputs)} maps created")
    print(f"{'=' * 60}\n")

    if not outputs:
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="generate_maps",
            status="error",
            message="Map generation failed: no map outputs created",
        )
        raise HTTPException(status_code=500, detail="No maps were generated successfully")

    if workflow_status_id is not None:
        update_workflow_status_flags(
            supabase_admin=supabase_admin,
            workflow_status_id=workflow_status_id,
            flags={"mapped": True},
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="generate_maps",
            status="success",
            message=f"Map generation complete: {len(outputs)} map(s) created",
        )

    return MapGenerationResponse(outputs=outputs)


# ============================================================================
# STEP 4: GENERATE FINAL PDF REPORT
# ============================================================================
@router.post("/generate-report", response_model=ReportGenerationResponse)
async def generate_report(
    request: ReportGenerationRequest,
    user=Depends(get_current_user),
):
    """
    Step 4: Generate the final weekly PDF report and store it in Supabase.

    Step 4 workflow:
    1) Gather latest observation file for the selected report window
    2) Gather generated maps for the same window
    3) Generate AI narration from those inputs
    4) Build the PDF with existing helper and store it in Supabase
    """
    print("\n" + "=" * 60)
    print("📄 REPORT GENERATION STARTED")
    print("=" * 60)

    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    print(f"👤 User ID: {user_id}")
    print(f"📍 County: {request.county_name}")
    print(
        f"📅 Week: {request.week_number}, Year: {request.year}, "
        f"Period: {request.report_start_at} to {request.report_end_at}"
    )

    stage_statuses = []

    def add_stage(stage: str, status: str, message: str):
        stage_statuses.append(
            {
                "stage": stage,
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )

    add_stage("report_generation", "in_progress", "Step 4 started")
    workflow_status_id: Optional[int] = get_or_create_workflow_status(
        supabase_admin=supabase_admin,
        user_id=user_id,
        report_week=request.week_number,
        report_year=request.year,
    )

    # ------------------------------------------------------------------
    # 1. Gather observation + map context for AI narration
    # ------------------------------------------------------------------
    try:
        add_stage(
            "observation_context",
            "in_progress",
            "Loading observation file for selected report window",
        )
        upload = (
            supabase_admin.table("uploads")
            .select("id,file_name,file_path")
            .eq("user_id", user_id)
            .eq("file_type", "observations")
            .eq("report_week", request.week_number)
            .eq("report_year", request.year)
            .order("uploaded_at", desc=True)
            .limit(1)
            .execute()
        )
        if not upload.data:
            add_stage(
                "observation_context",
                "failed",
                "No observation file found for selected window",
            )
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No observation file found for week {request.week_number}, "
                    f"{request.year}. Generate maps/validate for this window first."
                ),
            )

        obs = upload.data[0]
        if workflow_status_id is not None:
            update_workflow_status_flags(
                supabase_admin=supabase_admin,
                workflow_status_id=workflow_status_id,
                flags={"observation_file_id": obs["id"], "uploaded": True},
            )
        observation_bytes = supabase_admin.storage.from_(BUCKET_NAME).download(
            obs["file_path"]
        )
        observation_summary = summarize_observation_data(
            csv_bytes=observation_bytes,
            requested_variables=request.variables,
        )
        add_stage(
            "observation_context",
            "completed",
            f"Observation data prepared from {obs['file_name']}",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to prepare observation context: {e}")
        add_stage(
            "observation_context",
            "failed",
            "Failed to read observation data",
        )
        raise HTTPException(status_code=500, detail="Failed to read observation data")

    rainfall_map_storage_path = None
    try:
        add_stage(
            "map_context",
            "in_progress",
            "Loading generated maps for selected variables",
        )
        maps_response = (
            supabase_admin.table("generated_maps")
            .select("variable,map_url,storage_path,created_at")
            .eq("user_id", user_id)
            .eq("report_week", request.week_number)
            .eq("report_year", request.year)
            .order("created_at", desc=True)
            .execute()
        )
        rows = maps_response.data or []

        latest_maps_by_var = {}
        for row in rows:
            variable = row.get("variable")
            if variable and variable not in latest_maps_by_var:
                latest_maps_by_var[variable] = row

        map_context = []
        for variable in request.variables:
            row = latest_maps_by_var.get(variable)
            if row:
                map_context.append(
                    {
                        "variable": variable,
                        "map_url": row.get("map_url", ""),
                        "storage_path": row.get("storage_path", ""),
                    }
                )

        # Prefer rainfall map for the PDF cover page map slot.
        rainfall_row = latest_maps_by_var.get("rainfall") or latest_maps_by_var.get("rain")
        if rainfall_row:
            rainfall_map_storage_path = rainfall_row.get("storage_path")
        add_stage(
            "map_context",
            "completed",
            f"Map context prepared for {len(map_context)} variable(s)",
        )
    except Exception as e:
        print(f"⚠️ Failed to fetch generated maps context: {e}")
        map_context = []
        add_stage(
            "map_context",
            "failed",
            "Failed to load map context; continuing without map metadata",
        )

    # ------------------------------------------------------------------
    # 2. Generate AI narration from maps + observation summary
    # ------------------------------------------------------------------
    append_workflow_log(
        supabase_admin,
        workflow_status_id,
        stage="generate_narration",
        status="info",
        message="Generating AI narration from map and observation context",
    )
    add_stage(
        "ai_narration",
        "in_progress",
        "Generating weekly narration from observation and map context",
    )
    narration = await generate_report_narration(
        county_name=request.county_name,
        week_number=request.week_number,
        year=request.year,
        report_start_at=request.report_start_at,
        report_end_at=request.report_end_at,
        selected_variables=request.variables,
        observation_summary=observation_summary,
        map_context=map_context,
    )
    narration_source = narration.get("source", "unknown")
    if narration_source == "fallback":
        add_stage(
            "ai_narration",
            "completed",
            "AI narration unavailable; fallback narration applied",
        )
    else:
        add_stage(
            "ai_narration",
            "completed",
            f"AI narration generated via {narration_source}",
        )
    append_workflow_log(
        supabase_admin,
        workflow_status_id,
        stage="generate_narration",
        status="success",
        message=f"Narration generated via {narration_source}",
    )

    # ------------------------------------------------------------------
    # 3. Build structured data payload for the PDF helper
    # ------------------------------------------------------------------
    profile = {}
    try:
        profile_response = (
            supabase_admin.table("profiles")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if profile_response.data:
            profile = profile_response.data[0]
    except Exception as e:
        print(f"⚠️ Failed to fetch profile for sign-off details: {e}")

    signoff_name = profile.get("full_name") or "N/A"
    county_for_title = profile.get("county") or request.county_name
    signoff_title = (
        profile.get("job_title")
        or profile.get("title")
        or f"County Director of Meteorological Services, {county_for_title} County."
    )
    signoff_mobile = profile.get("phone") or "N/A"
    signoff_email = profile.get("email") or getattr(user, "email", None)
    if not signoff_email and isinstance(user, dict):
        signoff_email = user.get("email")
    if not signoff_email:
        signoff_email = "N/A"

    signoff = {
        "name": signoff_name,
        "job_title": signoff_title,
        "mobile": signoff_mobile,
        "email": signoff_email,
    }

    issue_date = datetime.utcnow().strftime("%Y-%m-%d")
    period_str = f"{request.report_start_at} to {request.report_end_at}"

    data = {
        "meta": {
            "station": request.county_name,
            "county": request.county_name,
            "issue_date": issue_date,
            "period": period_str,
        },
        # A single generic "County" section with placeholder content
        "sub_counties": [
            {
                "title": request.county_name,
                "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "forecast": {
                    day: {
                        "Morning": "No detailed forecast available.",
                        "Afternoon": "No detailed forecast available.",
                        "Night": "No detailed forecast available.",
                        "Rainfall distribution": "Refer to generated maps where available.",
                        "Maximum temperature": "Data not yet synthesized.",
                        "Minimum temperature": "Data not yet synthesized.",
                        "Winds": "Data not yet synthesized.",
                    }
                    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                },
            }
        ],
        "marine": {
            "daily_wind": {
                "Day 1": "N/A",
                "Day 2": "N/A",
                "Day 3": "N/A",
                "Day 4": "N/A",
                "Day 5": "N/A",
                "Day 6": "N/A",
                "Day 7": "N/A",
            }
        },
    }

    # ------------------------------------------------------------------
    # 4. Generate PDF to a temporary file
    # ------------------------------------------------------------------
    filename = (
        f"{request.county_name.replace(' ', '_').lower()}_week_"
        f"{request.week_number}_{request.year}.pdf"
    )

    temp_dir = tempfile.mkdtemp(prefix="weekly_report_")
    output_path = os.path.join(temp_dir, filename)
    map_path = None

    # Try to attach rainfall distribution map below issue/period on cover page.
    if rainfall_map_storage_path:
        try:
            add_stage(
                "map_attachment",
                "in_progress",
                "Fetching rainfall distribution map for report cover",
            )
            map_bytes = supabase_admin.storage.from_(BUCKET_NAME).download(
                rainfall_map_storage_path
            )
            map_path = os.path.join(temp_dir, "rainfall_distribution_map.png")
            with open(map_path, "wb") as map_file:
                map_file.write(map_bytes)
            add_stage(
                "map_attachment",
                "completed",
                "Rainfall distribution map attached to report cover",
            )
        except Exception as e:
            print(f"⚠️ Failed to attach rainfall map: {e}")
            map_path = None
            add_stage(
                "map_attachment",
                "failed",
                "Could not attach rainfall map; continuing without cover map",
            )
    else:
        add_stage(
            "map_attachment",
            "completed",
            "No rainfall map found for this window; report generated without cover map",
        )

    try:
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="generate_pdf",
            status="info",
            message="Generating PDF document",
        )
        add_stage("pdf_generation", "in_progress", "Generating PDF document")
        print(f"📝 Generating PDF at: {output_path}")
        generate_weekly_forecast_pdf(
            data=data,
            narration=narration,
            map_path=map_path,
            output_path=output_path,
            signoff=signoff,
        )
        print("✅ PDF generation complete")
        add_stage("pdf_generation", "completed", "PDF document generated")
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="generate_pdf",
            status="success",
            message="PDF document generated",
        )
    except Exception as e:
        print(f"❌ Failed to generate PDF: {e}")
        add_stage("pdf_generation", "failed", "Failed to generate report PDF")
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="generate_pdf",
            status="error",
            message="Failed to generate PDF document",
        )
        raise HTTPException(status_code=500, detail="Failed to generate report PDF")

    # ------------------------------------------------------------------
    # 5. Upload PDF to Supabase Storage and create DB record
    # ------------------------------------------------------------------
    try:
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="store_report",
            status="info",
            message="Uploading generated report and saving metadata",
        )
        add_stage("storage_upload", "in_progress", "Uploading generated PDF to storage")
        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        storage_path = (
            f"users/{user_id}/reports/"
            f"week_{request.week_number}_{request.year}/report_{timestamp}.pdf"
        )

        print(f"⬆️ Uploading PDF to storage: {storage_path}")
        supabase_admin.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf"},
        )

        # Store as "<bucket>/<path>" so existing download route can split it
        file_path = f"{BUCKET_NAME}/{storage_path}"

        report_record = {
            "user_id": user_id,
            "observation_file_id": obs.get("id"),
            "template_file_id": None,
            "status": "success",
            "file_path": file_path,
            "generated_at": datetime.utcnow().isoformat(),
        }

        print("💾 Saving generated_reports record")
        insert_result = (
            supabase_admin.table("generated_reports")
            .insert(report_record)
            .execute()
        )

        rows = insert_result.data or []
        if not rows:
            raise Exception("Insert into generated_reports returned no rows")

        report_id = rows[0]["id"]
        pdf_url = f"/api/v1/reports/download/{report_id}"

        print("✅ Report record created")
        add_stage(
            "storage_upload",
            "completed",
            "PDF uploaded and report record created",
        )
        if workflow_status_id is not None:
            update_workflow_status_flags(
                supabase_admin=supabase_admin,
                workflow_status_id=workflow_status_id,
                flags={
                    "generated": True,
                    "completed": True,
                    "generated_report_id": report_id,
                },
            )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="store_report",
            status="success",
            message="Report metadata saved successfully",
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="workflow_complete",
            status="success",
            message="Workflow completed successfully",
        )

    except Exception as e:
        print(f"❌ Failed to upload or save report record: {e}")
        add_stage(
            "storage_upload",
            "failed",
            "Failed to store generated report",
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="store_report",
            status="error",
            message="Failed to store report metadata",
        )
        raise HTTPException(status_code=500, detail="Failed to store generated report")
    finally:
        # Clean up temp directory
        try:
            import shutil

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print("🧹 Temp report directory cleaned up")
        except Exception as cleanup_err:
            print(f"⚠️ Failed to clean up temp directory: {cleanup_err}")

    print("\n" + "=" * 60)
    print("✅ REPORT GENERATION COMPLETE")
    print("=" * 60 + "\n")
    add_stage("report_generation", "completed", "Step 4 completed successfully")

    return ReportGenerationResponse(
        pdf_url=pdf_url,
        filename=filename,
        report_week=request.week_number,
        report_year=request.year,
        stage_statuses=stage_statuses,
    )
