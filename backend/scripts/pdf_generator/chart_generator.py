"""
Chart Generation Service

Matplotlib wrapper for generating weather-related charts with consistent styling
for embedding in PDF reports.

All charts are exported as high-DPI PNG images suitable for print quality PDFs.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta


# WMO-compliant color palette
COLORS = {
    'rainfall': '#3b82f6',  # Blue
    'temperature': '#ef4444',  # Red
    'wind': '#10b981',  # Green
    'background': '#ffffff',
    'grid': '#e5e7eb',
    'text': '#1f2937',
    'text_light': '#6b7280'
}


class ChartGenerator:
    """Generates weather charts with consistent styling."""
    
    def __init__(self, dpi: int = 300, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize chart generator.
        
        Args:
            dpi: Output DPI for charts
            style: Matplotlib style to use
        """
        self.dpi = dpi
        self.style = style
        
        # Set default style
        try:
            plt.style.use(style)
        except:
            # Fallback to default if style not available
            pass
    
    def generate_rainfall_bar_chart(
        self,
        daily_values: List[float],
        day_labels: List[str],
        output_path: Path,
        title: str = "Daily Rainfall",
        width: float = 10,
        height: float = 6
    ) -> Path:
        """
        Generate a bar chart for daily rainfall accumulation.
        
        Args:
            daily_values: List of 7 daily rainfall values (mm)
            day_labels: List of day labels (Mon, Tue, Wed, etc.)
            output_path: Where to save the chart
            title: Chart title
            width: Figure width in inches
            height: Figure height in inches
            
        Returns:
            Path to generated chart
        """
        fig, ax = plt.subplots(figsize=(width, height), dpi=self.dpi)
        
        # Create bars
        bars = ax.bar(day_labels, daily_values, color=COLORS['rainfall'], alpha=0.8)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{height:.1f}',
                ha='center',
                va='bottom',
                fontsize=9
            )
        
        # Styling
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Day of Week', fontsize=11)
        ax.set_ylabel('Rainfall (mm)', fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Set y-axis to start at 0
        ax.set_ylim(bottom=0)
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        return output_path
    
    def generate_temperature_line_chart(
        self,
        daily_max: List[float],
        daily_min: List[float],
        day_labels: List[str],
        output_path: Path,
        title: str = "Daily Temperature Range",
        width: float = 10,
        height: float = 6
    ) -> Path:
        """
        Generate a line chart for daily temperature ranges.
        
        Args:
            daily_max: List of 7 daily maximum temperatures (°C)
            daily_min: List of 7 daily minimum temperatures (°C)
            day_labels: List of day labels
            output_path: Where to save the chart
            title: Chart title
            width: Figure width in inches
            height: Figure height in inches
            
        Returns:
            Path to generated chart
        """
        fig, ax = plt.subplots(figsize=(width, height), dpi=self.dpi)
        
        x = np.arange(len(day_labels))
        
        # Plot lines
        ax.plot(x, daily_max, marker='o', linewidth=2.5, markersize=8,
                color='#ef4444', label='Max Temperature')
        ax.plot(x, daily_min, marker='o', linewidth=2.5, markersize=8,
                color='#3b82f6', label='Min Temperature')
        
        # Fill area between lines
        ax.fill_between(x, daily_min, daily_max, alpha=0.2, color='#fbbf24')
        
        # Add value labels
        for i, (max_val, min_val) in enumerate(zip(daily_max, daily_min)):
            ax.text(i, max_val, f'{max_val:.1f}°', ha='center', va='bottom', fontsize=8)
            ax.text(i, min_val, f'{min_val:.1f}°', ha='center', va='top', fontsize=8)
        
        # Styling
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Day of Week', fontsize=11)
        ax.set_ylabel('Temperature (°C)', fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(day_labels)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        return output_path
    
    def generate_wind_speed_chart(
        self,
        daily_peak: List[float],
        day_labels: List[str],
        directions: Optional[List[str]] = None,
        output_path: Optional[Path] = None,
        title: str = "Daily Peak Wind Speed",
        width: float = 10,
        height: float = 6
    ) -> Path:
        """
        Generate a chart for daily peak wind speeds.
        
        Args:
            daily_peak: List of 7 daily peak wind speeds (km/h)
            day_labels: List of day labels
            directions: Optional list of wind directions
            output_path: Where to save the chart
            title: Chart title
            width: Figure width in inches
            height: Figure height in inches
            
        Returns:
            Path to generated chart
        """
        fig, ax = plt.subplots(figsize=(width, height), dpi=self.dpi)
        
        x = np.arange(len(day_labels))
        
        # Create bars
        bars = ax.bar(x, daily_peak, color=COLORS['wind'], alpha=0.7, width=0.6)
        
        # Add wind direction labels if provided
        if directions:
            for i, (bar, direction) in enumerate(zip(bars, directions)):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{height:.1f}\n{direction}',
                    ha='center',
                    va='bottom',
                    fontsize=8
                )
        else:
            # Just show values
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontsize=9
                )
        
        # Add threshold line for strong winds (30 km/h)
        ax.axhline(y=30, color='#f97316', linestyle='--', linewidth=1.5, alpha=0.6, label='Strong Wind Threshold (30 km/h)')
        
        # Styling
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Day of Week', fontsize=11)
        ax.set_ylabel('Wind Speed (km/h)', fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(day_labels)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        ax.set_ylim(bottom=0)
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        return output_path
    
    def generate_weekly_summary_chart(
        self,
        rainfall_total: float,
        temp_mean: float,
        temp_max: float,
        temp_min: float,
        wind_mean: float,
        wind_max: float,
        output_path: Path,
        title: str = "Weekly Summary",
        width: float = 10,
        height: float = 6
    ) -> Path:
        """
        Generate a summary chart showing weekly statistics.
        
        Args:
            rainfall_total: Total weekly rainfall (mm)
            temp_mean: Mean weekly temperature (°C)
            temp_max: Maximum temperature (°C)
            temp_min: Minimum temperature (°C)
            wind_mean: Mean wind speed (km/h)
            wind_max: Maximum wind gust (km/h)
            output_path: Where to save the chart
            title: Chart title
            width: Figure width in inches
            height: Figure height in inches
            
        Returns:
            Path to generated chart
        """
        fig = plt.figure(figsize=(width, height), dpi=self.dpi)
        
        # Create 3 subplots
        gs = fig.add_gridspec(1, 3, hspace=0.3, wspace=0.3)
        
        # Rainfall
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.bar(['Total'], [rainfall_total], color=COLORS['rainfall'], alpha=0.8, width=0.5)
        ax1.set_title('Rainfall', fontweight='bold', fontsize=12)
        ax1.set_ylabel('mm', fontsize=10)
        ax1.text(0, rainfall_total, f'{rainfall_total:.1f}mm', ha='center', va='bottom', fontsize=11)
        ax1.set_ylim(bottom=0, top=rainfall_total * 1.2)
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.set_axisbelow(True)
        
        # Temperature
        ax2 = fig.add_subplot(gs[0, 1])
        temps = [temp_min, temp_mean, temp_max]
        labels = ['Min', 'Mean', 'Max']
        colors = ['#3b82f6', '#fbbf24', '#ef4444']
        bars = ax2.bar(labels, temps, color=colors, alpha=0.8)
        ax2.set_title('Temperature', fontweight='bold', fontsize=12)
        ax2.set_ylabel('°C', fontsize=10)
        for bar, temp in zip(bars, temps):
            ax2.text(bar.get_x() + bar.get_width()/2, temp, f'{temp:.1f}°',
                    ha='center', va='bottom', fontsize=9)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_axisbelow(True)
        
        # Wind
        ax3 = fig.add_subplot(gs[0, 2])
        winds = [wind_mean, wind_max]
        labels = ['Mean', 'Max Gust']
        bars = ax3.bar(labels, winds, color=COLORS['wind'], alpha=0.8)
        ax3.set_title('Wind Speed', fontweight='bold', fontsize=12)
        ax3.set_ylabel('km/h', fontsize=10)
        for bar, wind in zip(bars, winds):
            ax3.text(bar.get_x() + bar.get_width()/2, wind, f'{wind:.1f}',
                    ha='center', va='bottom', fontsize=9)
        ax3.set_ylim(bottom=0)
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.set_axisbelow(True)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        return output_path
    
    def generate_trend_indicators(
        self,
        current_value: float,
        previous_value: float,
        variable: str = "value",
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate trend indicator (↑↓→).
        
        Args:
            current_value: Current period value
            previous_value: Previous period value
            variable: Variable name for context
            output_path: Optional path to save indicator image
            
        Returns:
            Unicode trend arrow (↑↓→)
        """
        diff = current_value - previous_value
        percent_change = (diff / previous_value * 100) if previous_value != 0 else 0
        
        if abs(percent_change) < 5:
            return "→"  # Stable (< 5% change)
        elif diff > 0:
            return "↑"  # Increasing
        else:
            return "↓"  # Decreasing


def generate_sample_charts(output_dir: Path):
    """Generate sample charts for testing."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = ChartGenerator()
    
    # Sample data
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    rainfall = [6.2, 8.5, 12.3, 10.7, 4.8, 2.1, 0.8]
    temp_max = [25.3, 26.1, 26.8, 25.9, 24.7, 23.8, 24.2]
    temp_min = [14.2, 15.1, 15.8, 15.3, 14.9, 14.5, 14.7]
    wind_peak = [18.2, 21.5, 28.3, 24.1, 19.7, 16.3, 15.8]
    wind_directions = ['NE', 'NE', 'E', 'NE', 'NE', 'N', 'NE']
    
    # Generate charts
    print("Generating sample charts...")
    
    generator.generate_rainfall_bar_chart(
        rainfall, days,
        output_dir / "sample_rainfall_chart.png",
        title="Nairobi - Daily Rainfall"
    )
    print("✓ Rainfall chart")
    
    generator.generate_temperature_line_chart(
        temp_max, temp_min, days,
        output_dir / "sample_temperature_chart.png",
        title="Nairobi - Temperature Range"
    )
    print("✓ Temperature chart")
    
    generator.generate_wind_speed_chart(
        wind_peak, days, wind_directions,
        output_dir / "sample_wind_chart.png",
        title="Nairobi - Wind Speed"
    )
    print("✓ Wind chart")
    
    generator.generate_weekly_summary_chart(
        rainfall_total=sum(rainfall),
        temp_mean=21.5,
        temp_max=max(temp_max),
        temp_min=min(temp_min),
        wind_mean=13.5,
        wind_max=max(wind_peak),
        output_path=output_dir / "sample_summary_chart.png",
        title="Nairobi County - Weekly Weather Summary"
    )
    print("✓ Summary chart")
    
    print(f"\nCharts saved to: {output_dir}")


if __name__ == "__main__":
    # Generate sample charts when run directly
    output_dir = Path(__file__).parent / "sample_charts"
    generate_sample_charts(output_dir)
