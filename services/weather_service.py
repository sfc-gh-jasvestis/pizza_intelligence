"""
Pizza Operations Pipeline - Weather Service
Real-time weather integration for delivery optimization
Uses OpenWeatherMap API (free tier)
"""

import requests
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

# =============================================================================
# WEATHER DATA STRUCTURES
# =============================================================================

@dataclass
class WeatherData:
    """Current weather conditions"""
    temperature_f: float
    feels_like_f: float
    humidity: int
    wind_speed_mph: float
    description: str
    icon_code: str
    condition: str  # Maps to our internal conditions (Sunny, Rainy, Snowy, etc.)
    delivery_multiplier: float
    alert: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def icon_emoji(self) -> str:
        """Get emoji for weather condition"""
        # First check condition-based emoji (more accurate for Cold/Hot)
        condition_emoji = {
            "Cold": "❄️",
            "Hot": "🌡️",
            "Snowy": "🌨️",
            "Rainy": "🌧️",
            "Stormy": "⛈️",
            "Cloudy": "☁️",
            "Sunny": "☀️",
        }
        if self.condition in condition_emoji:
            return condition_emoji[self.condition]
        
        # Fall back to icon code mapping
        emoji_map = {
            "01d": "☀️", "01n": "🌙",  # Clear
            "02d": "⛅", "02n": "☁️",  # Few clouds
            "03d": "☁️", "03n": "☁️",  # Scattered clouds
            "04d": "☁️", "04n": "☁️",  # Broken clouds
            "09d": "🌧️", "09n": "🌧️",  # Shower rain
            "10d": "🌦️", "10n": "🌧️",  # Rain
            "11d": "⛈️", "11n": "⛈️",  # Thunderstorm
            "13d": "🌨️", "13n": "🌨️",  # Snow
            "50d": "🌫️", "50n": "🌫️",  # Mist
        }
        return emoji_map.get(self.icon_code, "🌤️")
    
    @property
    def impact_level(self) -> str:
        """Get impact level for deliveries"""
        if self.delivery_multiplier >= 1.5:
            return "severe"
        elif self.delivery_multiplier >= 1.25:
            return "moderate"
        elif self.delivery_multiplier >= 1.1:
            return "low"
        return "none"


# =============================================================================
# WEATHER SERVICE
# =============================================================================

class WeatherService:
    """
    Real-time weather service using OpenWeatherMap API.
    Falls back to simulated weather if API unavailable.
    """
    
    # OpenWeatherMap free tier: 1000 calls/day
    # Cache weather for 10 minutes to stay within limits
    CACHE_DURATION_SEC = 600
    
    # Chicago coordinates
    CHICAGO_LAT = 41.8781
    CHICAGO_LON = -87.6298
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather service.
        
        Args:
            api_key: OpenWeatherMap API key. If None, uses simulated weather.
        """
        self.api_key = api_key
        self._cache: Optional[WeatherData] = None
        self._cache_time: float = 0
        self._use_simulation = api_key is None
    
    def get_current_weather(self, force_refresh: bool = False) -> WeatherData:
        """
        Get current weather conditions for Chicago.
        Uses cached data if available and not expired.
        
        Args:
            force_refresh: Force API call even if cache is valid
            
        Returns:
            WeatherData with current conditions
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            return self._cache
        
        # Try API call if we have a key
        if not self._use_simulation:
            weather = self._fetch_from_api()
            if weather:
                self._cache = weather
                self._cache_time = time.time()
                return weather
            # Fall back to simulation if API fails
        
        # Use simulated weather
        weather = self._simulate_weather()
        self._cache = weather
        self._cache_time = time.time()
        return weather
    
    def _is_cache_valid(self) -> bool:
        """Check if cached weather data is still valid"""
        if self._cache is None:
            return False
        return (time.time() - self._cache_time) < self.CACHE_DURATION_SEC
    
    def _fetch_from_api(self) -> Optional[WeatherData]:
        """Fetch weather from OpenWeatherMap API"""
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": self.CHICAGO_LAT,
                "lon": self.CHICAGO_LON,
                "appid": self.api_key,
                "units": "imperial"  # Fahrenheit
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_api_response(data)
            else:
                print(f"Weather API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Weather API exception: {e}")
            return None
    
    def _parse_api_response(self, data: Dict) -> WeatherData:
        """Parse OpenWeatherMap API response into WeatherData"""
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        
        # Get basic weather info
        temp_f = main.get("temp", 70)
        feels_like = main.get("feels_like", temp_f)
        humidity = main.get("humidity", 50)
        wind_speed = wind.get("speed", 0)
        description = weather.get("description", "clear sky").title()
        icon_code = weather.get("icon", "01d")
        weather_main = weather.get("main", "Clear")
        
        # Map to our internal condition and get delivery multiplier
        condition, multiplier = self._map_weather_condition(
            weather_main, temp_f, wind_speed
        )
        
        # Check for alerts
        alert = None
        if multiplier >= 1.5:
            alert = f"Severe weather alert: {description}. Expect delivery delays."
        elif multiplier >= 1.25:
            alert = f"Weather advisory: {description}. Some delays possible."
        
        return WeatherData(
            temperature_f=temp_f,
            feels_like_f=feels_like,
            humidity=humidity,
            wind_speed_mph=wind_speed,
            description=description,
            icon_code=icon_code,
            condition=condition,
            delivery_multiplier=multiplier,
            alert=alert
        )
    
    def _map_weather_condition(
        self, 
        weather_main: str, 
        temp_f: float, 
        wind_speed: float
    ) -> Tuple[str, float]:
        """
        Map OpenWeatherMap condition to internal condition and delivery multiplier.
        
        Returns:
            Tuple of (condition_name, delivery_multiplier)
        """
        # Base conditions from API
        condition_map = {
            "Clear": ("Sunny", 1.0),
            "Clouds": ("Cloudy", 1.0),
            "Drizzle": ("Rainy", 1.15),
            "Rain": ("Rainy", 1.25),
            "Thunderstorm": ("Stormy", 1.75),
            "Snow": ("Snowy", 1.5),
            "Mist": ("Cloudy", 1.1),
            "Fog": ("Cloudy", 1.15),
            "Haze": ("Cloudy", 1.05),
        }
        
        condition, multiplier = condition_map.get(weather_main, ("Cloudy", 1.0))
        
        # Adjust for temperature extremes
        if temp_f < 20:
            condition = "Cold"
            multiplier = max(multiplier, 1.2)
        elif temp_f > 95:
            condition = "Hot"
            multiplier = max(multiplier, 1.1)
        
        # Adjust for high winds
        if wind_speed > 25:
            multiplier *= 1.15
        elif wind_speed > 15:
            multiplier *= 1.05
        
        return condition, round(multiplier, 2)
    
    def _simulate_weather(self) -> WeatherData:
        """Generate simulated weather - consistent 'Cold' for Chicago winter demo"""
        import random
        
        # For demo consistency, use Cold weather (matches historical Snowflake data)
        # Chicago in February is typically cold
        condition = "Cold"
        icon = "01d"  # Clear sky icon
        multiplier = 1.2  # Cold weather adds 20% to delivery times
        
        # Temperature range for cold Chicago winter (15-28°F)
        temp_f = random.uniform(15, 28)
        
        # Generate other values
        humidity = random.randint(40, 65)
        wind_speed = random.uniform(8, 18)  # Chicago is windy
        
        # Wind chill effect
        feels_like = temp_f - (wind_speed * 0.7)
        
        return WeatherData(
            temperature_f=round(temp_f, 1),
            feels_like_f=round(feels_like, 1),
            humidity=humidity,
            wind_speed_mph=round(wind_speed, 1),
            description="Cold and windy",
            icon_code=icon,
            condition=condition,
            delivery_multiplier=multiplier,
            alert=None  # Cold but manageable
        )
    
    def get_weather_impact_summary(self) -> str:
        """Get a summary of weather impact on deliveries"""
        weather = self.get_current_weather()
        
        if weather.impact_level == "severe":
            return f"🚨 {weather.icon_emoji} Severe weather ({weather.description}) - Expect 50%+ longer delivery times"
        elif weather.impact_level == "moderate":
            return f"⚠️ {weather.icon_emoji} {weather.description} - Deliveries may take 20-30% longer"
        elif weather.impact_level == "low":
            return f"📝 {weather.icon_emoji} {weather.description} - Minor impact on delivery times"
        else:
            return f"✅ {weather.icon_emoji} {weather.description} - Good conditions for deliveries"


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_weather_service: Optional[WeatherService] = None

def get_weather_service(api_key: Optional[str] = None) -> WeatherService:
    """Get the singleton weather service instance"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService(api_key)
    return _weather_service


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Test with simulated weather
    service = WeatherService()
    weather = service.get_current_weather()
    
    print(f"\nCurrent Weather in Chicago:")
    print(f"  {weather.icon_emoji} {weather.description}")
    print(f"  Temperature: {weather.temperature_f}°F (feels like {weather.feels_like_f}°F)")
    print(f"  Humidity: {weather.humidity}%")
    print(f"  Wind: {weather.wind_speed_mph} mph")
    print(f"  Condition: {weather.condition}")
    print(f"  Delivery Impact: {weather.impact_level} ({weather.delivery_multiplier}x)")
    if weather.alert:
        print(f"  ⚠️ Alert: {weather.alert}")
    print(f"\n{service.get_weather_impact_summary()}")
