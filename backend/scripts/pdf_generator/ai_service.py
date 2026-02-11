"""
AI Service for Generating Narrative Content

Uses OpenAI or Anthropic API to generate professional narrative text
from raw weather data.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from pdf_generator directory or current directory
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try current directory
        load_dotenv()
except ImportError:
    # python-dotenv not installed, will use environment variables only
    pass


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIService:
    """Service for generating narrative content using AI."""
    
    def __init__(self, provider: AIProvider = AIProvider.OPENAI, api_key: Optional[str] = None):
        """
        Initialize AI service.
        
        Args:
            provider: AI provider to use (openai or anthropic)
            api_key: API key (if None, reads from environment variable)
        """
        self.provider = provider
        self.api_key = api_key or self._get_api_key()
        self._client = None
        
    def _get_api_key(self) -> str:
        """Get API key from environment variable."""
        if self.provider == AIProvider.OPENAI:
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable not set. "
                    "Please set it or pass api_key parameter. "
                    "See pdf_generator/docs/API_KEY_SETUP.md for instructions."
                )
            return key
        elif self.provider == AIProvider.ANTHROPIC:
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Please set it or pass api_key parameter. "
                    "See pdf_generator/docs/API_KEY_SETUP.md for instructions."
                )
            return key
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _get_client(self):
        """Get or create AI client."""
        if self._client is None:
            if self.provider == AIProvider.OPENAI:
                try:
                    from openai import OpenAI
                    self._client = OpenAI(api_key=self.api_key)
                except ImportError:
                    raise ImportError(
                        "openai package not installed. "
                        "Run: pip install openai>=1.0.0"
                    )
            elif self.provider == AIProvider.ANTHROPIC:
                try:
                    from anthropic import Anthropic
                    self._client = Anthropic(api_key=self.api_key)
                except ImportError:
                    raise ImportError(
                        "anthropic package not installed. "
                        "Run: pip install anthropic>=0.18.0"
                    )
        return self._client
    
    def generate_executive_summary(
        self, 
        weather_data: Dict[str, Any],
        county_name: str
    ) -> Dict[str, Any]:
        """
        Generate executive summary section.
        
        Args:
            weather_data: Raw weather data dictionary
            county_name: Name of the county
            
        Returns:
            Dictionary with summary_statistics, key_highlights, and weather_pattern_summary
        """
        prompt = self._build_executive_summary_prompt(weather_data, county_name)
        response = self._call_ai(prompt, response_format="json")
        return json.loads(response)
    
    def generate_weekly_narrative(
        self,
        weather_data: Dict[str, Any],
        county_name: str
    ) -> Dict[str, Any]:
        """
        Generate weekly narrative section.
        
        Args:
            weather_data: Raw weather data dictionary
            county_name: Name of the county
            
        Returns:
            Dictionary with narrative content
        """
        prompt = self._build_narrative_prompt(weather_data, county_name)
        response = self._call_ai(prompt, response_format="json")
        return json.loads(response)
    
    def generate_rainfall_narrative(
        self,
        rainfall_data: Dict[str, Any],
        county_name: str
    ) -> str:
        """Generate narrative description for rainfall outlook."""
        prompt = self._build_rainfall_narrative_prompt(rainfall_data, county_name)
        return self._call_ai(prompt)
    
    def generate_temperature_narrative(
        self,
        temperature_data: Dict[str, Any],
        county_name: str
    ) -> str:
        """Generate narrative description for temperature outlook."""
        prompt = self._build_temperature_narrative_prompt(temperature_data, county_name)
        return self._call_ai(prompt)
    
    def generate_wind_narrative(
        self,
        wind_data: Dict[str, Any],
        county_name: str
    ) -> str:
        """Generate narrative description for wind outlook."""
        prompt = self._build_wind_narrative_prompt(wind_data, county_name)
        return self._call_ai(prompt)
    
    def generate_impacts_advisories(
        self,
        weather_data: Dict[str, Any],
        county_name: str
    ) -> Dict[str, Any]:
        """Generate impacts and advisories section."""
        prompt = self._build_impacts_prompt(weather_data, county_name)
        response = self._call_ai(prompt, response_format="json")
        return json.loads(response)
    
    def _call_ai(self, prompt: str, response_format: str = "text") -> str:
        """
        Call AI API with prompt.
        
        Args:
            prompt: The prompt to send
            response_format: "text" or "json"
            
        Returns:
            AI response text
        """
        client = self._get_client()
        
        if self.provider == AIProvider.OPENAI:
            model = "gpt-4o"  # or "gpt-4-turbo" for better performance
            messages = [{"role": "user", "content": prompt}]
            
            response_format_param = {"type": "json_object"} if response_format == "json" else None
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format_param,
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
            
        elif self.provider == AIProvider.ANTHROPIC:
            model = "claude-3-5-sonnet-20241022"  # or "claude-3-opus-20240229"
            
            if response_format == "json":
                prompt += "\n\nRespond with valid JSON only, no additional text."
            
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
    
    def _build_executive_summary_prompt(self, data: Dict, county: str) -> str:
        """Build prompt for executive summary generation."""
        return f"""You are a professional meteorologist writing a weekly weather outlook report for {county} County, Kenya.

Based on the following weather data, generate a comprehensive executive summary in JSON format with these exact keys:
- summary_statistics: {{"total_rainfall": number, "mean_temperature": number, "temperature_range": {{"min": number, "max": number}}, "max_wind_speed": number, "dominant_wind_direction": string}}
- key_highlights: array of 3-5 bullet point strings
- weather_pattern_summary: string (3-4 sentence paragraph)

Weather Data:
{json.dumps(data, indent=2)}

Generate a professional, accurate executive summary suitable for government officials and agricultural planners. Focus on actionable insights."""
    
    def _build_narrative_prompt(self, data: Dict, county: str) -> str:
        """Build prompt for weekly narrative generation."""
        return f"""You are a professional meteorologist writing a weekly weather narrative for {county} County, Kenya.

Based on the weather data, generate a comprehensive weekly narrative in JSON format with these exact keys:
- opening_paragraph: string
- temporal_breakdown: {{"early_week": string, "mid_week": string, "late_week": string}}
- variable_specific_details: {{"rainfall": string, "temperature": string, "wind": string, "humidity": string (optional)}}
- spatial_variations: string

Weather Data:
{json.dumps(data, indent=2)}

Write in a clear, professional style suitable for public weather reports."""
    
    def _build_rainfall_narrative_prompt(self, data: Dict, county: str) -> str:
        """Build prompt for rainfall narrative."""
        return f"""Write a 2-3 paragraph narrative description of the rainfall outlook for {county} County, Kenya.

Data: {json.dumps(data, indent=2)}

Focus on:
- Total weekly rainfall and distribution
- Peak rainfall days
- Spatial variations across wards
- Flood risk areas
- Agricultural implications

Write in professional meteorological language."""
    
    def _build_temperature_narrative_prompt(self, data: Dict, county: str) -> str:
        """Build prompt for temperature narrative."""
        return f"""Write a 2-3 paragraph narrative description of the temperature outlook for {county} County, Kenya.

Data: {json.dumps(data, indent=2)}

Focus on:
- Mean temperatures and ranges
- Diurnal patterns
- Spatial variations
- Heat stress considerations

Write in professional meteorological language."""
    
    def _build_wind_narrative_prompt(self, data: Dict, county: str) -> str:
        """Build prompt for wind narrative."""
        return f"""Write a 2-3 paragraph narrative description of the wind outlook for {county} County, Kenya.

Data: {json.dumps(data, indent=2)}

Focus on:
- Mean wind speeds and gusts
- Dominant directions
- Spatial patterns
- Safety implications

Write in professional meteorological language."""
    
    def _build_impacts_prompt(self, data: Dict, county: str) -> str:
        """Build prompt for impacts and advisories."""
        return f"""You are a professional meteorologist generating sector-specific advisories for {county} County, Kenya.

Based on the weather data, generate advisories in JSON format with these exact keys:
- agricultural_advisories: {{"rainfall_impact": string, "temperature_effects": string, "optimal_timing": string}}
- water_resources: {{"rainfall_contribution": string, "reservoir_implications": string (optional)}}
- health_advisories: {{"heat_related_warnings": array of strings (optional), "vector_borne_disease_risk": string (optional)}}
- general_public_advisories: {{"travel_conditions": string, "outdoor_activity_recommendations": string, "safety_precautions": string}}
- sector_specific_guidance: {{"energy": string (optional), "construction": string (optional), "tourism": string (optional)}}

Weather Data:
{json.dumps(data, indent=2)}

Provide practical, actionable guidance for each sector."""
