# Boundary Source Documentation

## Supabase table

- The shapefile components for Kenya county/ward boundaries are stored in the `shared_files` table (column `file_type = 'shapefile'`). Workflow routines (see `backend/app/api/v1/workflow.py:1328-1416`) query `supabase.table("shared_files")` to get `file_name` and `file_path`, then download each component (`.shp`, `.dbf`, `.shx`, etc.) from the bucket named by `settings.SUPABASE_STORAGE_BUCKET`.

## Download and local path

- Each component is streamed from `supabase.storage.from_(bucket).download(file_path)` into a temporary directory (lines 1363-1398). The `.shp` path is tracked so downstream code (e.g., `map_generator.create_weather_map`) can pass it to GeoPandas.
- After use, the temp directory is removed so no artifacts remain on disk (see the cleanup logic around lines 1399-1411).

## Loader reuse

- The new historical loader (`backend/scripts/load_historical_weather_data.py`) now reuses that same table and bucket. It downloads the shapefile components, reads the county geometries via GeoPandas, computes centroids, and then fetches Open-Meteo data using those centroids. Because the loader uses the exact same Supabase records, it always aligns with the maps that the API displays.

## Future considerations

- If the shapefile changes, update the `shared_files` entry so both the map generator and the loader pick up the latest boundaries automatically.
- You can also point the loader at a pre-prepared centroid JSON via `--centroids-path` for faster runs.
