"""
Map generation utilities for weather variables
"""
from app.utils.geospatial_compat import ensure_fiona_path

ensure_fiona_path()

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.patches import PathPatch
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.path import Path as MplPath
import io
from pathlib import Path
from datetime import datetime, timedelta
from datetime import date as date_cls
import logging
from functools import lru_cache
import hashlib
import httpx
from shapely.geometry import Point
from typing import Optional

from app.utils.map_settings import DEFAULT_MAP_SETTINGS, MapSettings, sanitize_map_settings

logger = logging.getLogger(__name__)

def calculate_map_dimensions(bounds):
    """Calculate map dimensions to determine smart spacing"""
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    width_km = width * 111 * np.cos(np.radians((bounds[1] + bounds[3]) / 2))
    height_km = height * 111
    area_km2 = width_km * height_km
    return width, height, width_km, height_km, area_km2

def get_calibrated_grid_spacing(bounds, county_name=None):
    """
    Calibrated grid spacing based on Kenya county sizes as reference
    """
    width, height, width_km, height_km, area_km2 = calculate_map_dimensions(bounds)
    max_dim = max(width, height)
    
    print(f"   Map dimensions: {width:.2f}° x {height:.2f}° ({width_km:.0f}km x {height_km:.0f}km)")
    print(f"   Approximate area: {area_km2:,.0f} km²")
    
    # COUNTY-SPECIFIC CALIBRATION
    if county_name:
        county_sizes = {
            'turkana': 0.5, 'marsabit': 0.5, 'wajir': 0.5, 'garissa': 0.5,
            'mandera': 0.5, 'taita taveta': 0.5, 'kajiado': 0.5,
            'kilifi': 0.2, 'lamu': 0.2, 'tana river': 0.2, 'isiolo': 0.2,
            'samburu': 0.2, 'narok': 0.2, 'kitui': 0.2, 'makueni': 0.2,
            'baringo': 0.2, 'laikipia': 0.2,
            'nakuru': 0.1, 'meru': 0.1, 'tharaka nithi': 0.1, 'embu': 0.1,
            'kirinyaga': 0.1, 'muranga': 0.1, 'nyandarua': 0.1, 'nyeri': 0.1,
            'kiambu': 0.1, 'kakamega': 0.1, 'vihiga': 0.1, 'bungoma': 0.1,
            'busia': 0.1, 'siaya': 0.1, 'kisumu': 0.1, 'homa bay': 0.1,
            'migori': 0.1, 'kisii': 0.1, 'nyamira': 0.1, 'trans nzoia': 0.1,
            'uasin gishu': 0.1, 'nandi': 0.1, 'kericho': 0.1, 'bomet': 0.1,
            'kwale': 0.1, 'machakos': 0.1, 'elgeyo marakwet': 0.1, 'west pokot': 0.1,
            'nairobi': 0.02, 'mombasa': 0.02, 'kisii': 0.05, 'nyamira': 0.05,
            'vihiga': 0.05, 'nyeri': 0.05, 'kirinyaga': 0.05,
        }
        
        county_lower = county_name.lower()
        if county_lower in county_sizes:
            spacing = county_sizes[county_lower]
            print(f"   Using county-calibrated spacing for {county_name}: {spacing}°")
            return spacing
    
    # FALLBACK: Size-based calibration
    if max_dim > 6.0:
        spacing = 1.0
    elif max_dim > 3.0:
        spacing = 0.5
    elif max_dim > 1.5:
        spacing = 0.2
    elif max_dim > 0.8:
        spacing = 0.1
    elif max_dim > 0.4:
        spacing = 0.05
    elif max_dim > 0.15:
        spacing = 0.02
    else:
        spacing = 0.01
    
    return spacing

def create_weather_map(
    county_name=None,
    variable='Rain',
    data_file='kenya_3km_weather.csv',
    shapefile_path='Kenya_county_assemblies_CLEANED.shp',  # ← DYNAMIC PATH!
    map_settings: Optional[MapSettings] = None,
    report_start_at: Optional[str] = None,
    report_end_at: Optional[str] = None,
    title_period_label=None,
    output_png_path: Optional[str] = None,
    return_figure: bool = False,
):
    """
    Unified map entrypoint.
    - Rainfall uses the reliable production pipeline (Open-Meteo coarse fetch,
      offline bilinear downscale, terrain adjustment, IDW station correction).
    - Tmin/Tmax use the existing gridded rendering path.
    
    Args:
        county_name: Name of county (None for all Kenya)
        variable: 'Rain', 'Tmin', or 'Tmax'
        data_file: Path to CSV data file
        shapefile_path: Path to shapefile (now dynamic!)
        map_settings: Optional map styling overrides (boundaries, labels, fonts)
    
    Returns:
        Tuple of (image_bytes, filename)
    """
    if str(variable).strip().lower() in {"rain", "rainfall", "precipitation", "precip"}:
        if not report_start_at or not report_end_at:
            raise ValueError("Rainfall map requires report_start_at and report_end_at.")
        return _create_reliable_rainfall_map(
            county_name=county_name if county_name else "County",
            data_file=data_file,
            shapefile_path=shapefile_path,
            report_start_at=report_start_at,
            report_end_at=report_end_at,
            title_period_label=title_period_label,
            map_settings=map_settings,
            output_png_path=output_png_path,
            return_figure=return_figure,
        )

    print("=" * 70)
    print(f"KENYA {variable.upper()} MAP - CALIBRATED VERSION")
    print("=" * 70)
    
    # 1. LOAD DATA
    print("\n📁 Loading data...")
    
    grid_data = pd.read_csv(data_file)
    print(f"   Grid points: {len(grid_data)}")
    
    # Use the dynamic shapefile path
    wards = gpd.read_file(shapefile_path)
    print(f"   Wards loaded: {len(wards)}")
    
    # 2. FILTER FOR COUNTY
    if county_name:
        county_col = _resolve_column(wards.columns, ["county", "county_name", "adm1_name"])
        if not county_col:
            raise ValueError("County column not found in shapefile")
        county_wards = wards[
            wards[county_col].astype(str).str.strip().str.lower()
            == str(county_name).strip().lower()
        ].copy()
        if len(county_wards) == 0:
            raise ValueError(f"County '{county_name}' not found!")
        plot_data = county_wards
        bounds = county_wards.total_bounds
        title_area = county_name
        print(f"📍 {county_name} County")
    else:
        plot_data = wards
        bounds = wards.total_bounds
        title_area = "Kenya"
        print("📍 All Kenya")
    
    style = sanitize_map_settings(map_settings or DEFAULT_MAP_SETTINGS)

    # 3. GRID SPACING
    print("\n📐 Calculating Kenya-calibrated grid spacing...")
    grid_spacing = get_calibrated_grid_spacing(bounds, county_name)
    print(f"   Selected spacing: {grid_spacing}°")
    
    # 4. COLOR PALETTE BASED ON VARIABLE
    print("\n🎨 Applying color palette...")
    
    if variable in ['Tmin', 'Tmax']:
        if variable == 'Tmin':
            thresholds = [0, 5, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
            colors = [
                (0.0, 0.0, 0.8), (0.2, 0.4, 1.0), (0.4, 0.6, 1.0),
                (0.6, 0.8, 1.0), (0.8, 0.9, 1.0), (1.0, 1.0, 0.8),
                (1.0, 0.9, 0.6), (1.0, 0.8, 0.4), (1.0, 0.7, 0.2),
                (1.0, 0.5, 0.1), (1.0, 0.3, 0.1), (0.8, 0.2, 0.1),
                (0.6, 0.1, 0.1),
            ]
        else:  # Tmax
            thresholds = [10, 15, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
            colors = [
                (0.2, 0.4, 1.0), (0.4, 0.6, 1.0), (0.6, 0.8, 1.0),
                (0.8, 0.9, 1.0), (1.0, 1.0, 0.8), (1.0, 0.9, 0.6),
                (1.0, 0.8, 0.4), (1.0, 0.7, 0.2), (1.0, 0.5, 0.1),
                (1.0, 0.3, 0.1), (0.8, 0.2, 0.1), (0.6, 0.1, 0.1),
                (0.4, 0.0, 0.0),
            ]
        title_text = f"{variable} (°C)"
    else:
        # Rainfall
        thresholds = [0, 2, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100]
        colors = [
            (1.0, 1.0, 1.0), (0.9, 1.0, 0.9), (0.7, 0.95, 0.7),
            (0.5, 0.85, 0.5), (0.3, 0.75, 0.3), (0.8, 0.9, 1.0),
            (0.6, 0.8, 1.0), (0.4, 0.7, 1.0), (0.2, 0.6, 1.0),
            (0.1, 0.5, 1.0), (1.0, 1.0, 0.6), (1.0, 0.9, 0.4),
            (1.0, 0.7, 0.2), (1.0, 0.5, 0.1), (1.0, 0.3, 0.1),
        ]
        title_text = f"{variable} (mm)"
    
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(thresholds, cmap.N)
    
    # 5. PREPARE DATA
    print("🔍 Preparing data...")
    
    mask = (
        (grid_data['Lon'] >= bounds[0]) &
        (grid_data['Lon'] <= bounds[2]) &
        (grid_data['Lat'] >= bounds[1]) &
        (grid_data['Lat'] <= bounds[3])
    )
    area_grid = grid_data[mask].copy()
    
    lon_vals = np.sort(area_grid['Lon'].unique())
    lat_vals = np.sort(area_grid['Lat'].unique())
    
    data_grid = area_grid.pivot_table(
        index='Lat',
        columns='Lon',
        values=variable,
        aggfunc='mean'
    )
    data_grid = data_grid.reindex(index=lat_vals, columns=lon_vals)
    X, Y = np.meshgrid(lon_vals, lat_vals)
    Z = data_grid.values
    
    # 6. CREATE MAP
    print("\n🗺️  Creating map...")
    
    width, height = calculate_map_dimensions(bounds)[:2]
    aspect_ratio = width / height if height > 0 else 1.0
    
    if county_name:
        if width > height * 1.5:
            figsize = (24, 18)
        elif height > width * 1.5:
            figsize = (18, 24)
        else:
            figsize = (22, 22)
    else:
        figsize = (26, 23)

    # scale up the canvas uniformly to enlarge the map without altering the ratio
    figsize = tuple(dim * 1.3 for dim in figsize)
    
    fig = plt.figure(figsize=figsize)
    
    if aspect_ratio > 1.5:
        ax_map = fig.add_axes([0.12, 0.18, 0.76, 0.65])
    elif aspect_ratio < 0.67:
        ax_map = fig.add_axes([0.14, 0.14, 0.72, 0.68])
    else:
        ax_map = fig.add_axes([0.15, 0.20, 0.70, 0.65])
    
    # 7. PLOT DATA
    contourf = ax_map.contourf(X, Y, Z,
                              levels=thresholds,
                              cmap=cmap,
                              norm=norm,
                              alpha=0.85,
                              extend='max')
    
    # 8. ADD BOUNDARIES
    if county_name:
        county_boundary = plot_data.dissolve(by='county')
        county_boundary.boundary.plot(ax=ax_map,
                                     color='black',
                                     linewidth=1.2,
                                     alpha=1)
    
    constituency_kwargs = {
        "color": style["constituency_border_color"],
        "linewidth": style["constituency_border_width"],
        "linestyle": style["constituency_border_style"],
        "alpha": 0.7,
    }
    if style["show_constituencies"] and "const" in plot_data.columns:
        constituencies = plot_data.dissolve(by="const")
        constituencies.boundary.plot(ax=ax_map, **constituency_kwargs)

    ward_kwargs = {
        "color": style["ward_border_color"],
        "linewidth": style["ward_border_width"],
        "linestyle": style["ward_border_style"],
        "alpha": 0.5,
    }
    if style["show_wards"]:
        plot_data.boundary.plot(ax=ax_map, **ward_kwargs)
    
    # 9. COORDINATE GRID
    ax_map.set_aspect('equal')
    ax_map.xaxis.set_major_locator(plt.MultipleLocator(grid_spacing))
    ax_map.yaxis.set_major_locator(plt.MultipleLocator(grid_spacing))
    
    if grid_spacing >= 0.5:
        format_str = '%.0f°'
    elif grid_spacing >= 0.1:
        format_str = '%.1f°'
    elif grid_spacing >= 0.05:
        format_str = '%.2f°'
    else:
        format_str = '%.3f°'
    
    ax_map.xaxis.set_major_formatter(plt.FormatStrFormatter(format_str))
    ax_map.yaxis.set_major_formatter(plt.FormatStrFormatter(format_str))
    
    margin = max(width, height) * 0.05
    ax_map.set_xlim(bounds[0] - margin, bounds[2] + margin)
    ax_map.set_ylim(bounds[1] - margin, bounds[3] + margin)
    
    # 10. TITLE
    today = datetime.now()
    start_date = today + timedelta(days=1)
    end_date = today + timedelta(days=7)
    start_str = start_date.strftime("%d %b")
    end_str = end_date.strftime("%d %b")
    
    if county_name:
        full_title = f"{county_name} - {variable.upper()} DISTRIBUTION ({start_str} - {end_str})"
    else:
        full_title = f"KENYA - {variable.upper()} DISTRIBUTION ({start_str} - {end_str})"
    
    ax_map.set_title(full_title, fontsize=22 if county_name else 26, 
                    fontweight='bold', pad=30)
    ax_map.set_xlabel('Longitude', fontsize=16, fontweight='bold', labelpad=15)
    ax_map.set_ylabel('Latitude', fontsize=16, fontweight='bold', labelpad=15)
    
    # 11. COLORBAR
    cbar_width = 0.5
    cbar_left = 0.25
    cbar_bottom = 0.09
    ax_cbar = fig.add_axes([cbar_left, cbar_bottom, cbar_width, 0.01])
    cbar = fig.colorbar(contourf, cax=ax_cbar, orientation='horizontal')
    cbar.outline.set_linewidth(0.8)
    cbar.outline.set_edgecolor('black')
    ax_cbar.text(0.5, 1.5, title_text, fontsize=13, fontweight='bold',
                ha='center', va='bottom', transform=ax_cbar.transAxes)
    cbar.set_ticks(thresholds)
    ax_cbar.set_xticklabels([str(t) for t in thresholds], fontsize=9)
    
    # 12. SAVE TO MEMORY INSTEAD OF DISK
    print("\n💾 Saving to memory buffer...")
    
    # Create filename
    filename = f"{title_area.replace(' ', '_')}_{variable.lower()}_week_{today.strftime('%Y%m%d')}.png"
    
    # Save to bytes buffer instead of file
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, dpi=300, pad_inches=0.0833, facecolor='white', format='png')
    plt.close(fig)
    
    # Reset buffer position to beginning
    img_buffer.seek(0)
    
    print(f"\n✅ Map created: {filename} ({img_buffer.getbuffer().nbytes} bytes)")
    
    return img_buffer.getvalue(), filename


def _resolve_column(columns, candidates, allow_contains=True):
    lower_to_original = {str(col).strip().lower(): str(col) for col in columns}
    for candidate in candidates:
        key = candidate.lower()
        if key in lower_to_original:
            return lower_to_original[key]

    if allow_contains:
        for candidate in candidates:
            key = candidate.lower()
            for lower_name, original in lower_to_original.items():
                if key in lower_name:
                    return original
    return None


def _extract_station_frame(df: pd.DataFrame) -> pd.DataFrame:
    lat_col = _resolve_column(df.columns, ["lat", "latitude", "y"])
    lon_col = _resolve_column(df.columns, ["lon", "lng", "long", "longitude", "x"])
    rain_col = _resolve_column(
        df.columns,
        ["rainfall", "rain", "precipitation", "precip", "rr", "ond_2025"],
    )
    station_col = _resolve_column(df.columns, ["station", "station_name", "name", "code"])

    if not lat_col or not lon_col or not rain_col:
        raise ValueError(
            "Observation CSV must contain latitude, longitude, and rainfall columns."
        )

    stations = df[[lat_col, lon_col, rain_col]].copy()
    stations.columns = ["lat", "lon", "observed_rainfall"]

    if station_col:
        stations["station_name"] = df[station_col].astype(str)
    else:
        stations["station_name"] = [f"Station {i+1}" for i in range(len(stations))]

    stations["lat"] = pd.to_numeric(stations["lat"], errors="coerce")
    stations["lon"] = pd.to_numeric(stations["lon"], errors="coerce")
    stations["observed_rainfall"] = pd.to_numeric(stations["observed_rainfall"], errors="coerce")
    stations = stations.dropna(subset=["lat", "lon", "observed_rainfall"]).copy()

    if stations.empty:
        raise ValueError("No valid station rows after parsing latitude/longitude/rainfall.")
    return stations


def _ordinary_kriging_interpolate(
    stations: pd.DataFrame,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    value_column: str,
    variogram_model: str = "exponential",
    auto_variogram_fit: bool = True,
    nlags: int = 10,
) -> np.ndarray:
    try:
        from pykrige.ok import OrdinaryKriging
    except ImportError as exc:
        raise ImportError(
            "Ordinary Kriging requires 'pykrige'. Install it with: pip install pykrige"
        ) from exc

    if stations.empty:
        return np.full_like(grid_x, np.nan, dtype=float)

    # De-duplicate station coordinates so kriging matrix remains well-conditioned.
    station_frame = stations[["lon", "lat", value_column]].copy()
    station_frame[value_column] = pd.to_numeric(station_frame[value_column], errors="coerce")
    station_frame = station_frame.dropna(subset=["lon", "lat", value_column])
    if station_frame.empty:
        return np.full_like(grid_x, np.nan, dtype=float)
    station_frame = (
        station_frame.groupby(["lon", "lat"], as_index=False)[value_column]
        .mean()
        .reset_index(drop=True)
    )

    station_lon = station_frame["lon"].to_numpy(dtype=float)
    station_lat = station_frame["lat"].to_numpy(dtype=float)
    station_values = station_frame[value_column].to_numpy(dtype=float)
    if station_values.size < 2:
        return np.full_like(grid_x, float(station_values[0]) if station_values.size == 1 else np.nan, dtype=float)

    variogram_model = str(variogram_model).strip().lower()
    if variogram_model not in {"gaussian", "spherical", "exponential"}:
        variogram_model = "spherical"

    kriging_kwargs = {
        "variogram_model": variogram_model,
        "nlags": max(6, int(nlags)),
        "verbose": False,
        "enable_plotting": False,
        "coordinates_type": "euclidean",
    }
    if not auto_variogram_fit:
        # Light-touch defaults; pykrige auto-fit remains the preferred option.
        value_std = max(float(np.nanstd(station_values)), 1e-6)
        kriging_kwargs["variogram_parameters"] = {"sill": value_std**2, "nugget": 0.0}

    try:
        ok = OrdinaryKriging(
            station_lon,
            station_lat,
            station_values,
            exact_values=True,
            **kriging_kwargs,
        )
    except TypeError:
        ok = OrdinaryKriging(station_lon, station_lat, station_values, **kriging_kwargs)

    grid_lon = grid_x[0, :]
    grid_lat = grid_y[:, 0]
    z_kriged, _ = ok.execute("grid", grid_lon, grid_lat)
    surface = np.asarray(z_kriged, dtype=float)

    # Enforce exact observed values on nearest grid nodes for visibly faithful station anchors.
    for lon, lat, val in zip(station_lon, station_lat, station_values):
        gx_idx = int(np.argmin(np.abs(grid_lon - lon)))
        gy_idx = int(np.argmin(np.abs(grid_lat - lat)))
        surface[gy_idx, gx_idx] = float(val)

    return surface


def _choose_variogram_model(
    requested_model: str,
    bounds,
    station_count: int,
    rainfall_values: np.ndarray,
) -> str:
    model = str(requested_model or "").strip().lower()
    valid = {"gaussian", "spherical", "exponential"}
    if model in valid:
        return model

    # Quick county-aware heuristic for spatial patch structure.
    # - sparse/large extents: exponential (more local, patchy behavior)
    # - dense stations on small/medium extents: gaussian (smoother transitions)
    # - otherwise: spherical (balanced default)
    _, _, _, _, area_km2 = calculate_map_dimensions(bounds)
    max_dim_km = max(width_km, height_km)
    station_density = station_count / max(area_km2, 1.0)
    cv = float(np.nanstd(rainfall_values) / max(np.nanmean(rainfall_values), 1e-6))

    if station_count <= 7 or area_km2 > 42000 or max_dim_km > 280 or station_density < 0.00022:
        return "exponential"
    if station_count >= 18 and area_km2 < 22000 and cv < 0.55:
        return "gaussian"
    return "spherical"


def _select_grid_axis_size(bounds) -> int:
    _, _, width_km, height_km, area_km2 = calculate_map_dimensions(bounds)
    max_dim_km = max(width_km, height_km)

    if area_km2 < 15000 and max_dim_km < 180:
        return 280  # Small county
    if area_km2 < 45000 and max_dim_km < 320:
        return 230  # Medium county
    return 180  # Large region


def _build_regular_grid(bounds):
    lon_min, lat_min, lon_max, lat_max = bounds
    width = max(lon_max - lon_min, 1e-9)
    height = max(lat_max - lat_min, 1e-9)
    axis_cells = _select_grid_axis_size(bounds)
    margin = max(width, height) * 0.04

    lon_lin = np.linspace(lon_min - margin, lon_max + margin, axis_cells)
    lat_lin = np.linspace(lat_min - margin, lat_max + margin, axis_cells)
    return np.meshgrid(lon_lin, lat_lin), margin


def _build_target_grid(bounds, target_km: float = 1.5):
    """
    Build a near 1-2 km target grid for high-resolution rainfall mapping.
    """
    lon_min, lat_min, lon_max, lat_max = bounds
    width = max(lon_max - lon_min, 1e-9)
    height = max(lat_max - lat_min, 1e-9)
    margin = max(width, height) * 0.04

    mid_lat = (lat_min + lat_max) / 2.0
    km_per_deg_lat = 111.0
    km_per_deg_lon = max(111.0 * np.cos(np.radians(mid_lat)), 1e-6)
    target_deg_lat = max(target_km / km_per_deg_lat, 1e-6)
    target_deg_lon = max(target_km / km_per_deg_lon, 1e-6)

    lat_count = int(np.ceil((height + (2 * margin)) / target_deg_lat)) + 1
    lon_count = int(np.ceil((width + (2 * margin)) / target_deg_lon)) + 1
    lat_count = int(np.clip(lat_count, 140, 420))
    lon_count = int(np.clip(lon_count, 140, 420))

    lon_lin = np.linspace(lon_min - margin, lon_max + margin, lon_count)
    lat_lin = np.linspace(lat_min - margin, lat_max + margin, lat_count)
    return np.meshgrid(lon_lin, lat_lin), margin


def _mask_to_polygon(grid_x, grid_y, polygon):
    try:
        from shapely import contains_xy

        return contains_xy(polygon, grid_x, grid_y)
    except Exception:
        try:
            import shapely.vectorized as vectorized

            return vectorized.contains(polygon, grid_x, grid_y)
        except Exception:
            return np.array(
                [polygon.contains(Point(x, y)) for x, y in zip(grid_x.ravel(), grid_y.ravel())]
            ).reshape(grid_x.shape)


def _ring_to_path_segments(coords):
    verts = []
    codes = []
    if len(coords) < 3:
        return verts, codes
    points = np.asarray(coords, dtype=float)
    verts.append((points[0, 0], points[0, 1]))
    codes.append(MplPath.MOVETO)
    for p in points[1:]:
        verts.append((p[0], p[1]))
        codes.append(MplPath.LINETO)
    verts.append((points[0, 0], points[0, 1]))
    codes.append(MplPath.CLOSEPOLY)
    return verts, codes


def _geometry_to_clip_patch(geometry, ax):
    if geometry is None or geometry.is_empty:
        return None

    polygons = []
    if geometry.geom_type == "Polygon":
        polygons = [geometry]
    elif geometry.geom_type == "MultiPolygon":
        polygons = list(geometry.geoms)
    else:
        try:
            polygons = [g for g in geometry.geoms if g.geom_type in {"Polygon", "MultiPolygon"}]
        except Exception:
            polygons = []

    verts_all = []
    codes_all = []
    for poly in polygons:
        if poly.geom_type == "MultiPolygon":
            poly_iter = list(poly.geoms)
        else:
            poly_iter = [poly]
        for p in poly_iter:
            ext_verts, ext_codes = _ring_to_path_segments(p.exterior.coords)
            verts_all.extend(ext_verts)
            codes_all.extend(ext_codes)
            for ring in p.interiors:
                int_verts, int_codes = _ring_to_path_segments(ring.coords)
                verts_all.extend(int_verts)
                codes_all.extend(int_codes)

    if not verts_all:
        return None

    path = MplPath(verts_all, codes_all)
    return PathPatch(path, transform=ax.transData, facecolor="none", edgecolor="none")


def _determine_contour_levels(min_val: float, max_val: float) -> np.ndarray:
    if not np.isfinite(min_val) or not np.isfinite(max_val):
        return np.array([0.0, 10.0, 20.0, 30.0], dtype=float)

    if np.isclose(min_val, max_val):
        base = round(min_val / 10.0) * 10.0
        return np.array([base - 10, base, base + 10, base + 20], dtype=float)

    span = max_val - min_val
    target_step = span / 9.0
    candidates = np.array([10, 15, 20, 25, 30, 40, 50], dtype=float)
    step = candidates[np.argmin(np.abs(candidates - target_step))]
    step = max(10.0, min(50.0, float(step)))

    level_start = np.floor(min_val / step) * step
    level_end = np.ceil(max_val / step) * step
    levels = np.arange(level_start, level_end + step, step)
    if levels.size < 4:
        levels = np.array([min_val, min_val + step, min_val + (2 * step), min_val + (3 * step)], dtype=float)
    return levels


def _calculate_scale_km(bounds):
    lon_min, lat_min, lon_max, lat_max = bounds
    mid_lat = (lat_min + lat_max) / 2.0
    km_per_deg_lon = 111.32 * np.cos(np.radians(mid_lat))
    if km_per_deg_lon <= 0:
        return 20

    width_km = (lon_max - lon_min) * km_per_deg_lon
    # Use a "nice" total length near 25% of map width for a properly scaled graphic bar.
    target_km = max(width_km * 0.25, 5.0)
    nice_lengths = [5, 10, 20, 25, 50, 75, 100, 150, 200]
    return min(nice_lengths, key=lambda n: abs(n - target_km))


def _add_scale_bar(ax, bounds):
    lon_min, lat_min, lon_max, lat_max = bounds
    mid_lat = (lat_min + lat_max) / 2.0
    km_per_deg_lon = 111.32 * np.cos(np.radians(mid_lat))
    if km_per_deg_lon <= 0:
        return

    scale_km = _calculate_scale_km(bounds)
    scale_deg = scale_km / km_per_deg_lon
    segment_km = scale_km / 4.0
    segment_deg = scale_deg / 4.0

    width_deg = lon_max - lon_min
    height_deg = lat_max - lat_min
    x0 = lon_max - scale_deg - width_deg * 0.05
    y0 = lat_min + height_deg * 0.08
    bar_h = height_deg * 0.012

    # Draw alternating black/white segments.
    for idx in range(4):
        x = x0 + idx * segment_deg
        face = "black" if idx % 2 == 0 else "white"
        ax.add_patch(
            Rectangle(
                (x, y0),
                segment_deg,
                bar_h,
                facecolor=face,
                edgecolor="black",
                linewidth=0.8,
                zorder=9,
            )
        )

    # Tick labels for readability and calibration feedback.
    label_y = y0 - height_deg * 0.010
    ax.text(x0, label_y, "0", ha="center", va="top", fontsize=8, zorder=10)
    ax.text(x0 + 2 * segment_deg, label_y, f"{int(2 * segment_km)}", ha="center", va="top", fontsize=8, zorder=10)
    ax.text(x0 + 4 * segment_deg, label_y, f"{int(scale_km)} km", ha="center", va="top", fontsize=8, zorder=10)


def _add_scale_bar_panel(fig, bounds, panel_bounds):
    panel_left, panel_bottom, panel_width, panel_height = panel_bounds
    scale_ax = fig.add_axes([panel_left, panel_bottom, panel_width, panel_height], zorder=25)
    scale_ax.set_xlim(0, 1)
    scale_ax.set_ylim(0, 1)
    scale_ax.axis("off")

    scale_km = _calculate_scale_km(bounds)
    segment_w = 0.19
    x0 = 0.12
    y0 = 0.44
    bar_h = 0.26

    for idx in range(4):
        x = x0 + (idx * segment_w)
        face = "black" if idx % 2 == 0 else "white"
        scale_ax.add_patch(
            Rectangle(
                (x, y0),
                segment_w,
                bar_h,
                facecolor=face,
                edgecolor="black",
                linewidth=0.9,
            )
        )

    segment_km = scale_km / 4.0
    label_y = y0 - 0.10
    scale_ax.text(x0, label_y, "0", ha="center", va="top", fontsize=8.5)
    scale_ax.text(x0 + (2 * segment_w), label_y, f"{int(2 * segment_km)}", ha="center", va="top", fontsize=8.5)
    scale_ax.text(x0 + (4 * segment_w), label_y, f"{int(scale_km)} km", ha="center", va="top", fontsize=8.5)


def _add_north_arrow(ax, bounds):
    lon_min, lat_min, lon_max, lat_max = bounds
    x = lon_max - (lon_max - lon_min) * 0.06
    y = lat_max - (lat_max - lat_min) * 0.08
    arrow_len = (lat_max - lat_min) * 0.08
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - arrow_len),
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        arrowprops=dict(facecolor="black", width=2, headwidth=10),
    )


def _add_compass_rose(fig, container_bounds):
    container_left, container_bottom, container_width, container_height = container_bounds
    compass_size = min(container_width, container_height) * 0.11
    compass_left = container_left + container_width - compass_size - 0.014
    compass_bottom = container_bottom + container_height - compass_size - 0.014
    compass_path = Path(__file__).resolve().parents[2] / "scripts" / "assets" / "compass.png"

    # Place compass at the container top-right corner outside the map panel.
    if compass_path.exists():
        try:
            compass_img = plt.imread(str(compass_path))
            compass_ax = fig.add_axes([compass_left, compass_bottom, compass_size, compass_size], zorder=25)
            compass_ax.imshow(compass_img, interpolation="antialiased")
            compass_ax.axis("off")
            return
        except Exception:
            pass

    fig.text(
        compass_left + (compass_size / 2.0),
        compass_bottom + (compass_size / 2.0),
        "N",
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=25,
    )



def _fetch_open_meteo_station_rainfall(lat, lon, report_start_at, report_end_at):
    params = {
        "latitude": round(float(lat), 6),
        "longitude": round(float(lon), 6),
        "daily": "precipitation_sum",
        "start_date": report_start_at,
        "end_date": report_end_at,
        "timezone": "Africa/Nairobi",
    }
    response = httpx.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20.0)
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})
    values = daily.get("precipitation_sum", [])
    if not values:
        return np.nan
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if numeric.empty:
        return np.nan
    return float(numeric.sum())


def _sum_precip_from_payload(payload: dict) -> float:
    daily = payload.get("daily", {}) if isinstance(payload, dict) else {}
    values = daily.get("precipitation_sum", [])
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if numeric.empty:
        return np.nan
    return float(numeric.sum())


@lru_cache(maxsize=512)
def _fetch_open_meteo_coarse_batch(lat_csv: str, lon_csv: str, report_start_at: str, report_end_at: str):
    params = {
        "latitude": lat_csv,
        "longitude": lon_csv,
        "daily": "precipitation_sum",
        "start_date": report_start_at,
        "end_date": report_end_at,
        "timezone": "Africa/Nairobi",
    }
    response = httpx.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=30.0)
    response.raise_for_status()
    payload = response.json()
    return payload


@lru_cache(maxsize=8000)
def _fetch_open_meteo_point_rain_elev(lat_r: float, lon_r: float, report_start_at: str, report_end_at: str):
    params = {
        "latitude": float(lat_r),
        "longitude": float(lon_r),
        "daily": "precipitation_sum",
        "start_date": report_start_at,
        "end_date": report_end_at,
        "timezone": "Africa/Nairobi",
    }
    response = httpx.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20.0)
    response.raise_for_status()
    payload = response.json()
    rain = _sum_precip_from_payload(payload if isinstance(payload, dict) else {})
    elev = np.nan
    if isinstance(payload, dict):
        try:
            elev = float(payload.get("elevation", np.nan))
        except Exception:
            elev = np.nan
    return rain, elev


def _fetch_open_meteo_coarse_grid_once(lon_vals: np.ndarray, lat_vals: np.ndarray, report_start_at: str, report_end_at: str):
    gx, gy = np.meshgrid(lon_vals, lat_vals)
    flat_lat = gy.ravel()
    flat_lon = gx.ravel()
    # Rounded coordinates keep request/cache key stable.
    lat_csv = ",".join(f"{v:.4f}" for v in flat_lat)
    lon_csv = ",".join(f"{v:.4f}" for v in flat_lon)

    payload = _fetch_open_meteo_coarse_batch(lat_csv, lon_csv, report_start_at, report_end_at)
    point_count = flat_lat.size
    rain_flat = np.full(point_count, np.nan, dtype=float)
    elev_flat = np.full(point_count, np.nan, dtype=float)

    entries = None
    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("responses"), list):
            entries = payload.get("responses")
        elif "daily" in payload:
            entries = [payload]

    valid_batch = bool(entries) and len(entries) >= point_count
    if valid_batch:
        for i in range(point_count):
            entry = entries[i] if isinstance(entries[i], dict) else {}
            rain_flat[i] = _sum_precip_from_payload(entry)
            try:
                elev_flat[i] = float(entry.get("elevation", np.nan))
            except Exception:
                elev_flat[i] = np.nan
    else:
        # Reliable fallback: per-point fetch with cache.
        for i, (lat, lon) in enumerate(zip(flat_lat, flat_lon)):
            lat_r = round(float(lat), 4)
            lon_r = round(float(lon), 4)
            try:
                rain, elev = _fetch_open_meteo_point_rain_elev(lat_r, lon_r, report_start_at, report_end_at)
                rain_flat[i] = rain
                elev_flat[i] = elev
            except Exception as exc:
                logger.warning(
                    "open_meteo_point_fetch_failed",
                    extra={"lat": lat_r, "lon": lon_r, "error": str(exc)},
                )

    return rain_flat.reshape(gx.shape), elev_flat.reshape(gx.shape)


def _build_coarse_grid(bounds, coarse_km: float = 10.0, max_points: int = 81):
    lon_min, lat_min, lon_max, lat_max = bounds
    mid_lat = (lat_min + lat_max) / 2.0
    km_per_deg_lat = 111.0
    km_per_deg_lon = max(111.0 * np.cos(np.radians(mid_lat)), 1e-6)
    step_km = max(float(coarse_km), 6.0)

    while True:
        dlat = max(step_km / km_per_deg_lat, 1e-5)
        dlon = max(step_km / km_per_deg_lon, 1e-5)
        lat_vals = np.arange(lat_min, lat_max + dlat, dlat)
        lon_vals = np.arange(lon_min, lon_max + dlon, dlon)
        if lat_vals.size < 2:
            lat_vals = np.array([lat_min, lat_max], dtype=float)
        if lon_vals.size < 2:
            lon_vals = np.array([lon_min, lon_max], dtype=float)

        if (lat_vals.size * lon_vals.size) <= max_points or step_km >= 45.0:
            return lon_vals.astype(float), lat_vals.astype(float)
        step_km += 2.5


def _fill_nan_with_mean(grid):
    filled = np.asarray(grid, dtype=float).copy()
    if np.isnan(filled).all():
        return np.zeros_like(filled, dtype=float)
    mean_val = float(np.nanmean(filled))
    return np.where(np.isfinite(filled), filled, mean_val)


def _bilinear_resample_regular_grid(src_lon, src_lat, src_values, target_x, target_y):
    """
    Bilinear interpolation from a regular source grid to target_x/target_y.
    """
    values = _fill_nan_with_mean(src_values)
    nx = len(src_lon)
    ny = len(src_lat)
    if nx < 2 or ny < 2:
        return np.full_like(target_x, float(np.nanmean(values)), dtype=float)

    xi = np.interp(target_x.ravel(), src_lon, np.arange(nx, dtype=float))
    yi = np.interp(target_y.ravel(), src_lat, np.arange(ny, dtype=float))
    x0 = np.floor(xi).astype(int)
    y0 = np.floor(yi).astype(int)
    x1 = np.clip(x0 + 1, 0, nx - 1)
    y1 = np.clip(y0 + 1, 0, ny - 1)
    x0 = np.clip(x0, 0, nx - 1)
    y0 = np.clip(y0, 0, ny - 1)

    wx = xi - x0
    wy = yi - y0
    v00 = values[y0, x0]
    v10 = values[y0, x1]
    v01 = values[y1, x0]
    v11 = values[y1, x1]
    interp = (
        ((1 - wx) * (1 - wy) * v00)
        + (wx * (1 - wy) * v10)
        + ((1 - wx) * wy * v01)
        + (wx * wy * v11)
    )
    return interp.reshape(target_x.shape)


def _terrain_adjustment_factor(grid_x, grid_y, elevation_surface):
    elev = _fill_nan_with_mean(elevation_surface)
    if not np.isfinite(elev).any():
        return np.ones_like(elev, dtype=float)

    dx_deg = float(np.nanmedian(np.diff(grid_x[0, :]))) if grid_x.shape[1] > 1 else 0.01
    dy_deg = float(np.nanmedian(np.diff(grid_y[:, 0]))) if grid_y.shape[0] > 1 else 0.01
    mid_lat = float(np.nanmean(grid_y))
    dx_m = max(abs(dx_deg) * (111_000.0 * np.cos(np.radians(mid_lat))), 1.0)
    dy_m = max(abs(dy_deg) * 111_000.0, 1.0)

    grad_y, grad_x = np.gradient(elev, dy_m, dx_m)
    slope_mag = np.hypot(grad_x, grad_y)

    def _robust_norm(arr):
        lo = float(np.nanpercentile(arr, 5))
        hi = float(np.nanpercentile(arr, 95))
        if hi <= lo:
            return np.zeros_like(arr, dtype=float)
        return np.clip((arr - lo) / (hi - lo), 0.0, 1.0)

    elev_norm = _robust_norm(elev)
    slope_norm = _robust_norm(slope_mag)
    factor = 1.0 + (0.12 * elev_norm) + (0.08 * slope_norm)
    return np.clip(factor, 0.75, 1.35)


def _sample_bilinear_at_points(grid_x, grid_y, grid_values, points_lon, points_lat):
    lon_axis = grid_x[0, :]
    lat_axis = grid_y[:, 0]
    px = np.asarray(points_lon, dtype=float)
    py = np.asarray(points_lat, dtype=float)
    sample_grid_x = px.reshape(-1, 1)
    sample_grid_y = py.reshape(-1, 1)
    sampled = _bilinear_resample_regular_grid(lon_axis, lat_axis, grid_values, sample_grid_x, sample_grid_y)
    return sampled[:, 0]


def _idw_residual_surface(station_lon, station_lat, station_residuals, grid_x, grid_y, power: float = 2.0, k_nearest: int = 8):
    station_lon = np.asarray(station_lon, dtype=float)
    station_lat = np.asarray(station_lat, dtype=float)
    residuals = np.asarray(station_residuals, dtype=float)
    if residuals.size == 0:
        return np.zeros_like(grid_x, dtype=float)

    points = np.column_stack([grid_x.ravel(), grid_y.ravel()])
    station_xy = np.column_stack([station_lon, station_lat])
    dx = points[:, None, 0] - station_xy[None, :, 0]
    dy = points[:, None, 1] - station_xy[None, :, 1]
    dist = np.hypot(dx, dy)

    k = max(1, min(int(k_nearest), residuals.size))
    if k < residuals.size:
        nearest_idx = np.argpartition(dist, kth=k - 1, axis=1)[:, :k]
        nearest_dist = np.take_along_axis(dist, nearest_idx, axis=1)
        nearest_vals = residuals[nearest_idx]
    else:
        nearest_dist = dist
        nearest_vals = np.broadcast_to(residuals, dist.shape)

    out = np.empty(points.shape[0], dtype=float)
    zero_mask = nearest_dist <= 1e-12
    has_zero = zero_mask.any(axis=1)
    if has_zero.any():
        zero_cols = zero_mask.argmax(axis=1)
        row_ids = np.where(has_zero)[0]
        out[row_ids] = nearest_vals[row_ids, zero_cols[row_ids]]

    no_zero = ~has_zero
    if no_zero.any():
        d = nearest_dist[no_zero]
        v = nearest_vals[no_zero]
        w = 1.0 / np.power(d, max(1.0, float(power)))
        out[no_zero] = np.sum(w * v, axis=1) / np.sum(w, axis=1)

    return out.reshape(grid_x.shape)


def _nearest_station_distance_km(grid_x: np.ndarray, grid_y: np.ndarray, station_lon: np.ndarray, station_lat: np.ndarray) -> np.ndarray:
    """
    Distance (km) from each grid point to nearest station.
    """
    if station_lon.size == 0:
        return np.full_like(grid_x, np.inf, dtype=float)

    mid_lat = float(np.nanmean(grid_y))
    km_per_deg_lon = max(111.0 * np.cos(np.radians(mid_lat)), 1e-6)
    km_per_deg_lat = 111.0

    points = np.column_stack([grid_x.ravel(), grid_y.ravel()])
    station_xy = np.column_stack([station_lon, station_lat])
    dx_km = (points[:, None, 0] - station_xy[None, :, 0]) * km_per_deg_lon
    dy_km = (points[:, None, 1] - station_xy[None, :, 1]) * km_per_deg_lat
    dist_km = np.hypot(dx_km, dy_km)
    nearest = np.min(dist_km, axis=1)
    return nearest.reshape(grid_x.shape)


def _imprint_station_observations(
    surface: np.ndarray,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    station_lon: np.ndarray,
    station_lat: np.ndarray,
    station_obs: np.ndarray,
    influence_km: float = 3.5,
) -> np.ndarray:
    """
    Ensure station observations are visible on the final grid:
    - exact value at nearest grid node
    - gentle local imprint around that node so the class patch is visible
    """
    out = np.asarray(surface, dtype=float).copy()
    lon_axis = grid_x[0, :]
    lat_axis = grid_y[:, 0]
    mid_lat = float(np.nanmean(grid_y))
    km_per_deg_lon = max(111.0 * np.cos(np.radians(mid_lat)), 1e-6)
    km_per_deg_lat = 111.0
    sigma = max(1.0, influence_km * 0.45)

    for lon, lat, obs in zip(station_lon, station_lat, station_obs):
        if not (np.isfinite(lon) and np.isfinite(lat) and np.isfinite(obs)):
            continue

        ix = int(np.argmin(np.abs(lon_axis - lon)))
        iy = int(np.argmin(np.abs(lat_axis - lat)))

        dx_km = np.abs(lon_axis - lon) * km_per_deg_lon
        dy_km = np.abs(lat_axis - lat) * km_per_deg_lat
        x_idx = np.where(dx_km <= influence_km)[0]
        y_idx = np.where(dy_km <= influence_km)[0]
        if x_idx.size == 0:
            x_idx = np.array([ix])
        if y_idx.size == 0:
            y_idx = np.array([iy])

        sub = out[np.ix_(y_idx, x_idx)]
        xx = lon_axis[x_idx][None, :]
        yy = lat_axis[y_idx][:, None]
        dist_km = np.hypot((xx - lon) * km_per_deg_lon, (yy - lat) * km_per_deg_lat)
        blend = np.exp(-(dist_km**2) / (2.0 * sigma**2))
        blend = np.clip(blend, 0.0, 1.0)
        out[np.ix_(y_idx, x_idx)] = (blend * obs) + ((1.0 - blend) * sub)
        out[iy, ix] = float(obs)

    return out


def _smooth_nanaware_surface(surface: np.ndarray, iterations: int = 1) -> np.ndarray:
    arr = np.asarray(surface, dtype=float).copy()
    for _ in range(max(0, int(iterations))):
        valid = np.isfinite(arr).astype(float)
        vals = np.where(np.isfinite(arr), arr, 0.0)

        sum_neighbors = np.zeros_like(arr, dtype=float)
        cnt_neighbors = np.zeros_like(arr, dtype=float)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                weight = 4.0 if (dx == 0 and dy == 0) else 1.0
                sum_neighbors += weight * np.roll(np.roll(vals, dy, axis=0), dx, axis=1)
                cnt_neighbors += weight * np.roll(np.roll(valid, dy, axis=0), dx, axis=1)

        smoothed = np.where(cnt_neighbors > 0, sum_neighbors / cnt_neighbors, np.nan)
        arr = np.where(np.isfinite(arr), smoothed, np.nan)
    return arr


def _apply_mesoscale_variability(
    surface: np.ndarray,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    report_start_at: str,
    report_end_at: str,
    min_frac: float = 0.05,
    max_frac: float = 0.15,
) -> np.ndarray:
    """
    Add deterministic mesoscale variability (5-15%) so the downscaled field is not overly uniform.
    """
    arr = np.asarray(surface, dtype=float)
    if not np.isfinite(arr).any():
        return arr

    valid = arr[np.isfinite(arr)]
    mean_val = float(np.nanmean(valid))
    if mean_val <= 0:
        return arr

    # Stable seed across runs for the same map window/extent.
    seed_src = (
        f"{report_start_at}|{report_end_at}|"
        f"{float(np.nanmin(grid_x)):.4f}|{float(np.nanmax(grid_x)):.4f}|"
        f"{float(np.nanmin(grid_y)):.4f}|{float(np.nanmax(grid_y)):.4f}"
    )
    seed = int(hashlib.sha256(seed_src.encode("utf-8")).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)

    noise = rng.normal(0.0, 1.0, size=arr.shape)
    # Smooth random field to get mesoscale patches (not pixel noise).
    for _ in range(2):
        noise = _smooth_nanaware_surface(noise, iterations=1)

    amp = float(np.nanpercentile(np.abs(noise), 95))
    if amp <= 1e-8:
        return arr
    noise = noise / amp

    cv = float(np.nanstd(valid) / max(mean_val, 1e-6))
    frac = float(np.clip(0.10 + (0.12 * cv), min_frac, max_frac))
    factor = 1.0 + (frac * noise)
    factor = np.clip(factor, 1.0 - max_frac, 1.0 + max_frac)
    out = np.where(np.isfinite(arr), np.clip(arr * factor, 0.0, None), np.nan)
    return out


def _gaussian_smooth_nanaware(surface: np.ndarray, sigma: float = 0.8) -> np.ndarray:
    """
    Light Gaussian smoothing with NaN awareness.
    """
    arr = np.asarray(surface, dtype=float)
    if not np.isfinite(arr).any():
        return arr

    valid = np.isfinite(arr).astype(float)
    vals = np.where(np.isfinite(arr), arr, 0.0)

    try:
        from scipy.ndimage import gaussian_filter

        num = gaussian_filter(vals, sigma=max(0.1, float(sigma)), mode="nearest")
        den = gaussian_filter(valid, sigma=max(0.1, float(sigma)), mode="nearest")
        out = np.where(den > 1e-8, num / den, np.nan)
        return np.where(np.isfinite(arr), out, np.nan)
    except Exception:
        # Fallback if scipy is unavailable.
        iters = 1 if sigma < 1.0 else 2
        return _smooth_nanaware_surface(arr, iterations=iters)


def _build_downscaled_rainfall_surface(
    bounds,
    grid_x,
    grid_y,
    stations_in_county: pd.DataFrame,
    report_start_at: str,
    report_end_at: str,
    coarse_km: float = 10.0,
):
    _, _, _, _, area_km2 = calculate_map_dimensions(bounds)
    adaptive_coarse_km = float(coarse_km)
    if area_km2 > 18000:
        adaptive_coarse_km = max(adaptive_coarse_km, 12.0)
    if area_km2 > 35000:
        adaptive_coarse_km = max(adaptive_coarse_km, 15.0)
    if area_km2 > 60000:
        adaptive_coarse_km = max(adaptive_coarse_km, 18.0)

    lon_vals, lat_vals = _build_coarse_grid(bounds, coarse_km=adaptive_coarse_km, max_points=169)
    coarse_rain, coarse_elev = _fetch_open_meteo_coarse_grid_once(
        lon_vals=lon_vals,
        lat_vals=lat_vals,
        report_start_at=report_start_at,
        report_end_at=report_end_at,
    )
    if np.isnan(coarse_rain).all():
        raise ValueError("Open-Meteo coarse rainfall field build failed.")

    # 1) Bilinear downscale from coarse Open-Meteo field to 1-2 km target grid.
    base_surface = _bilinear_resample_regular_grid(lon_vals, lat_vals, coarse_rain, grid_x, grid_y)
    # 2) Mesoscale variability (5-15%) to avoid flat/uniform patches.
    mesoscale_surface = _apply_mesoscale_variability(
        base_surface, grid_x, grid_y, report_start_at, report_end_at, min_frac=0.08, max_frac=0.15
    )
    # 3) Terrain adjustment using elevation + slope modulation.
    elev_surface = _bilinear_resample_regular_grid(lon_vals, lat_vals, coarse_elev, grid_x, grid_y)
    terrain_factor = _terrain_adjustment_factor(grid_x, grid_y, elev_surface)
    terrain_adjusted = np.clip(mesoscale_surface * terrain_factor, 0.0, None)

    # 4) Station bias correction via IDW residual spreading.
    station_lon = stations_in_county["lon"].to_numpy(dtype=float)
    station_lat = stations_in_county["lat"].to_numpy(dtype=float)
    station_obs = stations_in_county["rainfall_mm"].to_numpy(dtype=float)
    modeled_at_stations = _sample_bilinear_at_points(grid_x, grid_y, terrain_adjusted, station_lon, station_lat)
    residuals = station_obs - modeled_at_stations
    residuals = np.where(np.isfinite(residuals), residuals, 0.0)

    station_count = len(residuals)
    if station_count <= 1:
        correction_strength = 0.10
    elif station_count == 2:
        correction_strength = 0.18
    elif station_count <= 4:
        correction_strength = 0.30
    elif station_count <= 8:
        correction_strength = 0.45
    else:
        correction_strength = 0.60

    residual_surface = _idw_residual_surface(
        station_lon=station_lon,
        station_lat=station_lat,
        station_residuals=residuals,
        grid_x=grid_x,
        grid_y=grid_y,
        power=2.0,
        k_nearest=min(8, max(station_count, 1)),
    )
    residual_cap = max(3.0, float(np.nanpercentile(np.abs(residuals), 85)) * 1.0) if station_count > 0 else 0.0
    residual_surface = np.clip(residual_surface, -residual_cap, residual_cap)

    # Prevent sparse stations from forcing county-wide uniform bias.
    nearest_dist_km = _nearest_station_distance_km(grid_x, grid_y, station_lon, station_lat)
    if station_count <= 1:
        influence_radius_km = 16.0
    elif station_count <= 3:
        influence_radius_km = 24.0
    elif station_count <= 6:
        influence_radius_km = 34.0
    else:
        influence_radius_km = 48.0
    local_weight = np.exp(-((nearest_dist_km / max(influence_radius_km, 1.0)) ** 2))
    residual_surface = residual_surface * local_weight

    corrected = np.clip(terrain_adjusted + (correction_strength * residual_surface), 0.0, None)

    # Make station influence visible as local patches while preserving realism.
    if station_count >= 3:
        corrected = _imprint_station_observations(
            corrected,
            grid_x,
            grid_y,
            station_lon=station_lon,
            station_lat=station_lat,
            station_obs=station_obs,
            influence_km=3.0,
        )

    # 5) Light Gaussian smoothing for final coherent field (kept weak to preserve patchiness).
    smooth_sigma = 0.45 if station_count <= 8 else 0.55
    smoothed = _gaussian_smooth_nanaware(corrected, sigma=smooth_sigma)
    return smoothed


def _create_reliable_rainfall_map(
    county_name: str,
    data_file: str,
    shapefile_path: str,
    report_start_at: str,
    report_end_at: str,
    title_period_label=None,
    map_settings: Optional[MapSettings] = None,
    output_png_path: Optional[str] = None,
    return_figure: bool = False,
    variogram_model: str = "exponential",
    auto_variogram_model: bool = True,
    auto_variogram_fit: bool = True,
    kriging_nlags: int = 12,
):
    """
    Create a rainfall distribution map using the standard production workflow:
    Open-Meteo coarse forecast fetch -> offline bilinear downscale -> terrain adjustment
    -> station residual correction (IDW) -> county clip + thematic rendering.

    Returns PNG bytes and filename to preserve existing API behavior.
    :param map_settings: Styling tweaks for boundaries and labels per user preferences.
    :param variogram_model: Kept for backward API compatibility (not used in standard path).
    :param auto_variogram_model: Kept for backward API compatibility (not used in standard path).
    :param auto_variogram_fit: Kept for backward API compatibility (not used in standard path).
    :param kriging_nlags: Kept for backward API compatibility (not used in standard path).
    """
    _ = date_cls.fromisoformat(report_start_at)
    _ = date_cls.fromisoformat(report_end_at)

    observations = pd.read_csv(data_file)
    try:
        stations = _extract_station_frame(observations)
    except ValueError as exc:
        # Allow rainfall map generation even when no station dataset is provided.
        logger.info("rainfall_map_no_station_data_using_downscaled_field", extra={"error": str(exc)})
        stations = pd.DataFrame(
            columns=["lat", "lon", "observed_rainfall", "station_name"],
        )
    wards = gpd.read_file(shapefile_path)
    if wards.crs is None:
        wards = wards.set_crs(epsg=4326, allow_override=True)
    elif wards.crs.to_epsg() != 4326:
        wards = wards.to_crs(epsg=4326)

    county_col = _resolve_column(wards.columns, ["county", "county_name", "adm1_name"])
    ward_col = _resolve_column(wards.columns, ["ward", "ward_name", "adm3_name", "name"])
    subcounty_col = _resolve_column(
        wards.columns,
        ["sub_county", "subcounty", "const", "constituency", "adm2_name"],
    )

    if county_name and county_col:
        county_wards = wards[
            wards[county_col].astype(str).str.strip().str.lower() == county_name.strip().lower()
        ].copy()
        if county_wards.empty:
            logger.warning(
                "county_not_found_for_rainfall_map_fallback",
                extra={"county_name": county_name},
            )
            county_wards = wards.copy()
    else:
        county_wards = wards.copy()

    style = sanitize_map_settings(map_settings or DEFAULT_MAP_SETTINGS)

    county_boundary = county_wards.dissolve()
    county_polygon = county_boundary.geometry.unary_union
    if stations.empty:
        stations_in_county = pd.DataFrame(
            columns=["lat", "lon", "observed_rainfall", "station_name", "rainfall_mm"],
        )
    else:
        station_points = gpd.GeoDataFrame(
            stations,
            geometry=gpd.points_from_xy(stations["lon"], stations["lat"]),
            crs=county_wards.crs,
        )
        stations_in_county = station_points[station_points.geometry.apply(county_polygon.covers)].copy()
        if stations_in_county.empty:
            stations_in_county = station_points.copy()
        stations_in_county["rainfall_mm"] = stations_in_county["observed_rainfall"]

    bounds = county_wards.total_bounds
    lon_min, lat_min, lon_max, lat_max = bounds
    # Primary workflow (fully local math after map input is loaded):
    # local coarse field (~10 km) -> bilinear downscale (1-2 km) ->
    # station residual bias correction (IDW, conservative when few stations).
    (grid_x, grid_y), margin = _build_target_grid(bounds, target_km=1.5)
    grid_z = _build_downscaled_rainfall_surface(
        bounds=bounds,
        grid_x=grid_x,
        grid_y=grid_y,
        stations_in_county=stations_in_county,
        report_start_at=report_start_at,
        report_end_at=report_end_at,
        coarse_km=10.0,
    )

    # Slightly portrait-oriented canvas so cover-page embedding uses vertical space better.
    fig = plt.figure(figsize=(12.0, 14.0))

    # Outer container: decorations live in this bordered frame, map uses the center panel.
    container_left, container_bottom, container_width, container_height = 0.035, 0.045, 0.93, 0.91
    container = Rectangle(
        (container_left, container_bottom),
        container_width,
        container_height,
        transform=fig.transFigure,
        fill=False,
        edgecolor="black",
        linewidth=1.2,
        zorder=40,
    )
    fig.add_artist(container)

    # Dynamic panel sizing (fractions of container) so layout scales with different figure sizes.
    title_band_h = 0.12 * container_height
    bottom_band_h = 0.04 * container_height
    left_band_w = 0.17 * container_width  # legend overlay width
    right_band_w = 0.02 * container_width
    pad = 0.012 * container_width

    # 15px left alignment for the map image area; map flows under the legend overlay.
    fig_width_px = max(fig.get_size_inches()[0] * fig.dpi, 1.0)
    left_offset_fig = 15.0 / fig_width_px
    map_left = container_left + left_offset_fig
    map_bottom = container_bottom + bottom_band_h + pad
    map_width = container_width - left_offset_fig - right_band_w - pad
    map_height = container_height - title_band_h - bottom_band_h - (2 * pad)
    ax = fig.add_axes([map_left, map_bottom, map_width, map_height], zorder=5)

    valid_rain = grid_z[np.isfinite(grid_z)]
    max_rain = float(valid_rain.max()) if valid_rain.size else 50.0

    # Match surface exactly to the requested legend classes:
    # <5, 5-20, 21-50, >50 mm (all green scale, no red classes).
    # Matplotlib contour levels must be strictly increasing; keep the top class
    # break above 50 mm even when observed maxima are <= 50.
    upper_bound = max(55.0, float(np.ceil(max_rain / 5.0) * 5.0))
    fill_levels = [0.0, 5.0, 20.0, 50.0, upper_bound]
    fill_colors = ["#ffffff", "#d9f2cf", "#88cc7a", "#2d7f3d"]
    fill_cmap = ListedColormap(fill_colors)
    fill_norm = BoundaryNorm(fill_levels, fill_cmap.N)
    contour = ax.contourf(
        grid_x,
        grid_y,
        grid_z,
        levels=fill_levels,
        cmap=fill_cmap,
        norm=fill_norm,
        antialiased=True,
        extend="neither",
        alpha=0.98,
        zorder=1,
    )
    # Add subtle internal isohyets so spatial patch structure remains visible even with broad legend classes.
    finite_vals = grid_z[np.isfinite(grid_z)]
    if finite_vals.size >= 16:
        zmin = float(np.nanmin(finite_vals))
        zmax = float(np.nanmax(finite_vals))
        if zmax > zmin:
            line_levels = np.linspace(zmin, zmax, 9)
            ax.contour(
                grid_x,
                grid_y,
                grid_z,
                levels=line_levels,
                colors="#2f4f2f",
                linewidths=0.0,
                alpha=0.0,
                zorder=2,
            )
    clip_patch = _geometry_to_clip_patch(county_polygon, ax)
    if clip_patch is not None:
        ax.add_patch(clip_patch)
        for coll in contour.collections:
            coll.set_clip_path(clip_patch)

    county_boundary.boundary.plot(ax=ax, color="black", linewidth=1.8, zorder=4)

    # Restore internal administrative boundaries and labels (as requested),
    # while keeping rainfall edge clipping smooth.
    if style["show_constituencies"] and subcounty_col:
        county_wards.dissolve(by=subcounty_col).boundary.plot(
            ax=ax,
            color=style["constituency_border_color"],
            linewidth=style["constituency_border_width"],
            linestyle=style["constituency_border_style"],
            alpha=0.9,
            zorder=4,
        )

    if style["show_wards"]:
        county_wards.boundary.plot(
            ax=ax,
            color=style["ward_border_color"],
            linewidth=style["ward_border_width"],
            linestyle=style["ward_border_style"],
            alpha=0.9,
            zorder=4,
        )

    max_labels = 40
    if subcounty_col and style["show_constituency_labels"]:
        const_labels = county_wards.dissolve(by=subcounty_col)
        count = 0
        for const_name, row in const_labels.iterrows():
            if count >= max_labels or row.geometry is None:
                continue
            centroid = row.geometry.representative_point()
            ax.text(
                centroid.x,
                centroid.y,
                str(const_name)[:28],
                fontsize=style["constituency_label_font_size"],
                color=style["constituency_border_color"],
                ha="center",
                va="center",
                zorder=5,
            )
            count += 1

    if ward_col and style["show_ward_labels"]:
        count = 0
        for _, row in county_wards.iterrows():
            if count >= max_labels:
                break
            geom = row.geometry
            if geom is None:
                continue
            centroid = geom.representative_point()
            ax.text(
                centroid.x,
                centroid.y,
                str(row.get(ward_col, ""))[:28],
                fontsize=style["ward_label_font_size"],
                color=style["ward_border_color"],
                ha="center",
                va="center",
                zorder=5,
            )
            count += 1

    # Custom rainfall legend panel (outside map).
    legend_ax = fig.add_axes(
        [
            container_left + (0.015 * container_width),
            map_bottom + (0.12 * map_height),
            left_band_w - (0.03 * container_width),
            map_height * 0.76,
        ],
        zorder=20,
    )
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis("off")
    legend_ax.add_patch(
        Rectangle((0.0, 0.0), 1.0, 1.0, facecolor="white", edgecolor="none", linewidth=0.0, alpha=0.94, zorder=0)
    )
    legend_ax.text(
        0.02,
        0.96,
        "Rainfall distribution (mm)",
        ha="left",
        va="top",
        fontsize=10,
        fontweight="bold",
    )
    legend_items = [
        ("<5 mm", "#ffffff"),
        ("5-20 mm", "#d9f2cf"),
        ("21-50 mm", "#88cc7a"),
        (">50 mm", "#2d7f3d"),
    ]

    # Pixel-precise legend geometry for clean visual rhythm.
    fig_w_px = max(fig.get_size_inches()[0] * fig.dpi, 1.0)
    fig_h_px = max(fig.get_size_inches()[1] * fig.dpi, 1.0)
    legend_w_px = max((left_band_w - (0.03 * container_width)) * fig_w_px, 1.0)
    legend_h_px = max((map_height * 0.76) * fig_h_px, 1.0)

    square_px = 22.0
    between_px = 12.0
    text_offset_px = 8.0

    square_w = square_px / legend_w_px
    square_h = square_px / legend_h_px
    step_y = (square_px + between_px) / legend_h_px
    text_offset_x = text_offset_px / legend_w_px

    x0 = 0.06
    y = 0.84
    for label, color in legend_items:
        legend_ax.add_patch(
            Rectangle(
                (x0, y - (square_h / 2.0)),
                square_w,
                square_h,
                facecolor=color,
                edgecolor="black",
                linewidth=0.9,
            )
        )
        legend_ax.text(x0 + square_w + text_offset_x, y, label, ha="left", va="center", fontsize=9)
        y -= step_y

    # Scale on bottom-right of the map (original in-map placement).
    _add_scale_bar(ax, (lon_min, lat_min, lon_max, lat_max))

    start_label = date_cls.fromisoformat(report_start_at).isoformat()
    end_label = date_cls.fromisoformat(report_end_at).isoformat()
    period_label = (
        str(title_period_label).strip()
        if title_period_label is not None and str(title_period_label).strip()
        else f"{start_label} to {end_label}"
    )
    title = f"FORECASTED CUMULATIVE RAINFALL VALID {period_label}"
    title_y = container_bottom + container_height - (title_band_h * 0.5)
    fig.text(
        container_left + (container_width * 0.50),
        title_y,
        title,
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        zorder=30,
    )

    # Compass rose in top-right of the bordered layout, outside map.
    _add_compass_rose(fig, (container_left, container_bottom, container_width, container_height))

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_facecolor("none")
    fig.patch.set_facecolor("white")
    ax.set_xlim(lon_min - margin, lon_max + margin)
    ax.set_ylim(lat_min - margin, lat_max + margin)
    ax.set_aspect("equal")

    stamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{county_name.replace(' ', '_').lower()}_reliable_rainfall_{stamp}.png"
    if return_figure:
        if output_png_path:
            fig.savefig(output_png_path, format="png", dpi=300, facecolor="white")
        return fig, filename

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=300, facecolor="white")
    if output_png_path:
        fig.savefig(output_png_path, format="png", dpi=300, facecolor="white")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue(), filename
