"""
Map generation utilities for weather variables
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.lines import Line2D
import io
from datetime import datetime, timedelta
from datetime import date as date_cls
import logging
import httpx
from shapely.geometry import Point

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
    shapefile_path='Kenya_county_assemblies_CLEANED.shp'  # ← DYNAMIC PATH!
):
    """
    Create weather map for specified variable and return as bytes
    
    Args:
        county_name: Name of county (None for all Kenya)
        variable: 'Rain', 'Tmin', or 'Tmax'
        data_file: Path to CSV data file
        shapefile_path: Path to shapefile (now dynamic!)
    
    Returns:
        Tuple of (image_bytes, filename)
    """
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
        county_wards = wards[wards['county'] == county_name].copy()
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
    
    if 'const' in plot_data.columns:
        constituencies = plot_data.dissolve(by='const')
        constituencies.boundary.plot(ax=ax_map,
                                    color='black',
                                    linewidth=0.8,
                                    alpha=0.7)
    
    plot_data.boundary.plot(ax=ax_map,
                           color='blue',
                           linewidth=0.8,
                           linestyle=':',
                           alpha=0.5)
    
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


def _idw_interpolate(stations: pd.DataFrame, grid_x: np.ndarray, grid_y: np.ndarray) -> np.ndarray:
    station_lon = stations["lon"].to_numpy()
    station_lat = stations["lat"].to_numpy()
    station_values = stations["blended_rainfall"].to_numpy()

    interpolated = np.zeros_like(grid_x, dtype=float)
    for i in range(grid_x.shape[0]):
        gx = grid_x[i, :]
        gy = grid_y[i, :]
        dx = gx[:, None] - station_lon[None, :]
        dy = gy[:, None] - station_lat[None, :]
        dist2 = dx * dx + dy * dy
        dist2 = np.where(dist2 < 1e-12, 1e-12, dist2)
        weights = 1.0 / dist2
        interpolated[i, :] = (weights * station_values[None, :]).sum(axis=1) / weights.sum(axis=1)
    return interpolated


def _add_scale_bar(ax, bounds):
    lon_min, lat_min, lon_max, lat_max = bounds
    mid_lat = (lat_min + lat_max) / 2.0
    km_per_deg_lon = 111.32 * np.cos(np.radians(mid_lat))
    if km_per_deg_lon <= 0:
        return

    width_km = (lon_max - lon_min) * km_per_deg_lon
    scale_km = 20 if width_km > 70 else 10
    scale_deg = scale_km / km_per_deg_lon

    x0 = lon_min + (lon_max - lon_min) * 0.06
    y0 = lat_min + (lat_max - lat_min) * 0.05
    ax.plot([x0, x0 + scale_deg], [y0, y0], color="black", linewidth=3, solid_capstyle="butt")
    ax.text(x0 + scale_deg / 2, y0 + (lat_max - lat_min) * 0.02, f"{scale_km} km", ha="center", fontsize=9)


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


def create_reliable_rainfall_map(
    county_name: str,
    data_file: str,
    shapefile_path: str,
    report_start_at: str,
    report_end_at: str,
    title_period_label: str = "OND 2025",
):
    """
    Create a rainfall map that blends station observations with Open-Meteo forecast totals.
    Includes county/sub-county/ward boundaries, ward labels, station points, interpolated
    rainfall surface, legend, scale bar, north arrow, and map title.
    """
    _ = date_cls.fromisoformat(report_start_at)
    _ = date_cls.fromisoformat(report_end_at)

    observations = pd.read_csv(data_file)
    stations = _extract_station_frame(observations)
    wards = gpd.read_file(shapefile_path)

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
    else:
        county_wards = wards.copy()

    if county_wards.empty:
        raise ValueError(f"County '{county_name}' not found in shapefile")

    county_boundary = county_wards.dissolve()
    county_polygon = county_boundary.geometry.unary_union
    station_points = gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy(stations["lon"], stations["lat"]),
        crs=county_wards.crs,
    )
    stations_in_county = station_points[station_points.geometry.within(county_polygon)].copy()
    if stations_in_county.empty:
        stations_in_county = station_points.copy()

    forecast_values = []
    for _, row in stations_in_county.iterrows():
        try:
            forecast_values.append(
                _fetch_open_meteo_station_rainfall(
                    lat=row["lat"],
                    lon=row["lon"],
                    report_start_at=report_start_at,
                    report_end_at=report_end_at,
                )
            )
        except Exception as exc:
            logger.warning("station_open_meteo_fetch_failed", extra={"error": str(exc)})
            forecast_values.append(np.nan)

    stations_in_county["forecast_rainfall"] = forecast_values
    forecast_available = stations_in_county["forecast_rainfall"].notna().any()
    if forecast_available:
        obs_median = float(stations_in_county["observed_rainfall"].median())
        forecast_median = float(stations_in_county["forecast_rainfall"].median(skipna=True))
        ratio = (obs_median / forecast_median) if forecast_median > 0 else 999.0
        forecast_weight = 0.2 if ratio > 3.0 else 0.35
        stations_in_county["blended_rainfall"] = (
            stations_in_county["observed_rainfall"] * (1.0 - forecast_weight)
            + stations_in_county["forecast_rainfall"].fillna(stations_in_county["observed_rainfall"])
            * forecast_weight
        )
    else:
        stations_in_county["blended_rainfall"] = stations_in_county["observed_rainfall"]

    bounds = county_wards.total_bounds
    lon_min, lat_min, lon_max, lat_max = bounds
    width = lon_max - lon_min
    height = lat_max - lat_min
    margin = max(width, height) * 0.05
    lon_lin = np.linspace(lon_min - margin, lon_max + margin, 220)
    lat_lin = np.linspace(lat_min - margin, lat_max + margin, 220)
    grid_x, grid_y = np.meshgrid(lon_lin, lat_lin)
    grid_z = _idw_interpolate(stations_in_county, grid_x, grid_y)

    inside_mask = np.array(
        [county_polygon.contains(Point(x, y)) for x, y in zip(grid_x.ravel(), grid_y.ravel())]
    ).reshape(grid_x.shape)
    grid_z = np.where(inside_mask, grid_z, np.nan)

    fig, ax = plt.subplots(figsize=(14, 14))
    thresholds = [0, 10, 20, 30, 40, 60, 80, 100, 130, 160, 200, 260]
    cmap = ListedColormap(
        [
            "#edf8fb", "#ccece6", "#99d8c9", "#66c2a4", "#41ae76",
            "#238b45", "#006d2c", "#fef0d9", "#fdcc8a", "#fc8d59", "#d7301f",
        ]
    )
    norm = BoundaryNorm(thresholds, cmap.N)

    contour = ax.contourf(
        grid_x,
        grid_y,
        grid_z,
        levels=thresholds,
        cmap=cmap,
        norm=norm,
        alpha=0.9,
        extend="max",
    )

    county_boundary.boundary.plot(ax=ax, color="black", linewidth=1.8, zorder=4)
    if subcounty_col:
        county_wards.dissolve(by=subcounty_col).boundary.plot(
            ax=ax, color="#303030", linewidth=1.1, zorder=4
        )
    county_wards.boundary.plot(ax=ax, color="#0b5ed7", linewidth=0.6, linestyle=":", zorder=4)

    max_labels = 40
    if ward_col:
        for _, row in county_wards.head(max_labels).iterrows():
            centroid = row.geometry.representative_point()
            label = str(row[ward_col])[:28]
            ax.text(centroid.x, centroid.y, label, fontsize=6, color="#0b1f33", ha="center", zorder=5)

    ax.scatter(
        stations_in_county["lon"],
        stations_in_county["lat"],
        s=36,
        color="black",
        edgecolor="white",
        linewidth=0.5,
        zorder=6,
        label="Rainfall station",
    )

    station_legend = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="black",
            label="Rainfall station",
            markerfacecolor="black",
            markersize=7,
            linestyle="None",
        )
    ]
    ax.legend(handles=station_legend, loc="lower left", frameon=True, fontsize=9)

    cbar = fig.colorbar(contour, ax=ax, orientation="horizontal", fraction=0.045, pad=0.04)
    cbar.set_label("Rainfall (mm)", fontsize=10, fontweight="bold")

    _add_scale_bar(ax, (lon_min, lat_min, lon_max, lat_max))
    _add_north_arrow(ax, (lon_min, lat_min, lon_max, lat_max))

    title = (
        f"{county_name} County Rainfall Map\n"
        f"Interpolated Rainfall Surface ({title_period_label})"
    )
    ax.set_title(title, fontsize=14, fontweight="bold", pad=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(lon_min - margin, lon_max + margin)
    ax.set_ylim(lat_min - margin, lat_max + margin)
    ax.set_aspect("equal")

    fig.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, facecolor="white")
    plt.close(fig)
    buffer.seek(0)

    stamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{county_name.replace(' ', '_').lower()}_reliable_rainfall_{stamp}.png"
    return buffer.getvalue(), filename
