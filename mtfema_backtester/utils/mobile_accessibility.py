"""
Mobile Accessibility Utilities for MT 9 EMA Backtester.

This module provides utilities for enhancing the mobile experience
of the MT 9 EMA Backtester application, ensuring proper responsive design,
touch optimization, and offline capabilities.
"""

import os
import json
import logging
import re
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Callable, Tuple
from dataclasses import dataclass
from functools import wraps

# Setup logger
logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """Types of devices for responsive design."""
    DESKTOP = "desktop"
    TABLET = "tablet"
    PHONE = "phone"
    UNKNOWN = "unknown"


class Orientation(Enum):
    """Device orientation."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class DeviceInfo:
    """Information about the user's device."""
    
    # Type of device
    device_type: DeviceType
    
    # Device orientation
    orientation: Orientation
    
    # Screen width in pixels
    screen_width: int
    
    # Screen height in pixels
    screen_height: int
    
    # Pixel ratio for high-DPI displays
    pixel_ratio: float
    
    # Is this a touch-enabled device
    is_touch: bool
    
    # Network connection type (wifi, cellular, offline)
    connection_type: str
    
    # Browser user agent
    user_agent: str
    
    # Whether the app is running in standalone mode (PWA)
    is_standalone: bool = False


class MobileAccessibilityManager:
    """
    Manages mobile accessibility features for the application.
    
    This class provides utilities for:
    1. Detecting device types and capabilities
    2. Providing responsive layout recommendations
    3. Optimizing touch interactions
    4. Managing offline capabilities
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MobileAccessibilityManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the mobile accessibility manager.
        
        Args:
            config_file: Path to configuration file
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return
            
        self._initialized = True
        
        # Configuration
        self._config_file = config_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "mobile_config.json"
        )
        
        # Default configuration
        self._config = {
            # Breakpoints for responsive design in pixels
            "breakpoints": {
                "phone_max": 767,
                "tablet_min": 768,
                "tablet_max": 1023,
                "desktop_min": 1024
            },
            
            # Touch target sizes in pixels
            "touch": {
                "min_target_size": 44,
                "min_spacing": 8
            },
            
            # Storage limits for offline mode in KB
            "offline": {
                "max_storage": 50000,  # 50MB
                "max_items": 1000
            },
            
            # Performance thresholds
            "performance": {
                "max_main_thread_work": 4000,  # ms
                "target_fps": 60,
                "max_bundle_size": 500,  # KB
                "max_image_size": 200   # KB
            }
        }
        
        # Load configuration
        self._load_config()
        
        # Current device info
        self._current_device = DeviceInfo(
            device_type=DeviceType.DESKTOP,
            orientation=Orientation.LANDSCAPE,
            screen_width=1920,
            screen_height=1080,
            pixel_ratio=1.0,
            is_touch=False,
            connection_type="wifi",
            user_agent="",
            is_standalone=False
        )
        
        logger.info("Mobile accessibility manager initialized")
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r') as f:
                    config = json.load(f)
                    
                # Update config with loaded values
                self._update_nested_dict(self._config, config)
                    
                logger.info(f"Loaded mobile accessibility configuration from {self._config_file}")
            except Exception as e:
                logger.error(f"Error loading mobile accessibility configuration: {str(e)}")
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """Update a nested dictionary with values from another dictionary."""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def set_device_info(self, device_info: DeviceInfo) -> None:
        """
        Set current device information.
        
        Args:
            device_info: Device information
        """
        self._current_device = device_info
        logger.debug(f"Device info updated: {device_info.device_type.value}, {device_info.screen_width}x{device_info.screen_height}")
    
    def detect_device_type(self, 
                        screen_width: int, 
                        screen_height: int,
                        user_agent: str = "") -> DeviceType:
        """
        Detect device type based on screen size and user agent.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            user_agent: Browser user agent string
            
        Returns:
            DeviceType enum value
        """
        # Check for common mobile identifiers in user agent
        is_mobile_ua = any(keyword in user_agent.lower() for keyword in 
                          ['android', 'iphone', 'ipad', 'mobile', 'smartphone'])
        
        # Get breakpoints from config
        breakpoints = self._config["breakpoints"]
        
        # Use the smaller dimension for detection (handles orientation)
        smaller_dimension = min(screen_width, screen_height)
        
        if smaller_dimension <= breakpoints["phone_max"] or is_mobile_ua:
            return DeviceType.PHONE
        elif smaller_dimension <= breakpoints["tablet_max"]:
            return DeviceType.TABLET
        else:
            return DeviceType.DESKTOP
    
    def detect_orientation(self, screen_width: int, screen_height: int) -> Orientation:
        """
        Detect device orientation based on screen dimensions.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            
        Returns:
            Orientation enum value
        """
        return Orientation.LANDSCAPE if screen_width >= screen_height else Orientation.PORTRAIT
    
    def get_layout_recommendations(self) -> Dict[str, Any]:
        """
        Get layout recommendations based on current device.
        
        Returns:
            Dictionary of layout recommendations
        """
        device = self._current_device
        
        # Base recommendations
        recommendations = {
            "container_width": "100%",
            "font_size_base": "16px",
            "line_height": 1.5,
            "column_count": 1,
            "show_sidebar": False,
            "touch_optimized": device.is_touch,
            "use_condensed_header": True,
            "use_bottom_navigation": True,
            "image_quality": "medium"
        }
        
        # Adjust based on device type
        if device.device_type == DeviceType.DESKTOP:
            recommendations.update({
                "container_width": "1200px",
                "column_count": 3,
                "show_sidebar": True,
                "use_condensed_header": False,
                "use_bottom_navigation": False,
                "image_quality": "high"
            })
        elif device.device_type == DeviceType.TABLET:
            recommendations.update({
                "container_width": "90%",
                "column_count": 2,
                "show_sidebar": device.orientation == Orientation.LANDSCAPE,
                "use_condensed_header": False,
                "use_bottom_navigation": device.orientation == Orientation.PORTRAIT,
                "image_quality": "high"
            })
        
        # Further adjustments based on orientation
        if device.orientation == Orientation.LANDSCAPE and device.device_type != DeviceType.DESKTOP:
            recommendations["column_count"] += 1
        
        # Adjust for high DPI displays
        if device.pixel_ratio > 1.5:
            recommendations["image_quality"] = "high"
        
        # Adjust for connection type
        if device.connection_type == "cellular":
            recommendations["image_quality"] = "low"
        elif device.connection_type == "offline":
            recommendations["image_quality"] = "low"
        
        return recommendations
    
    def get_touch_guidelines(self) -> Dict[str, Any]:
        """
        Get guidelines for touch targets based on current device.
        
        Returns:
            Dictionary of touch target guidelines
        """
        touch_config = self._config["touch"]
        
        # Base guidelines
        guidelines = {
            "min_target_size": touch_config["min_target_size"],
            "min_spacing": touch_config["min_spacing"],
            "use_touch_feedback": True,
            "increase_form_controls": True,
            "show_active_states": True
        }
        
        # Only return touch guidelines for touch devices
        if not self._current_device.is_touch:
            guidelines["use_touch_feedback"] = False
            guidelines["increase_form_controls"] = False
        
        return guidelines
    
    def get_offline_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for offline capabilities.
        
        Returns:
            Dictionary of offline capability recommendations
        """
        offline_config = self._config["offline"]
        
        # Base recommendations
        recommendations = {
            "use_service_worker": True,
            "cache_strategy": "stale-while-revalidate",
            "max_cache_size": offline_config["max_storage"],
            "sync_priority_items": [
                "user_settings",
                "active_backtests",
                "recent_results"
            ],
            "show_offline_indicator": True,
            "support_offline_edits": True
        }
        
        # Adjust based on device type
        if self._current_device.device_type == DeviceType.PHONE:
            # More conservative with storage on phones
            recommendations["max_cache_size"] = offline_config["max_storage"] // 2
            
        # Adjust for connection type
        if self._current_device.connection_type == "offline":
            recommendations["show_offline_indicator"] = True
        else:
            recommendations["show_offline_indicator"] = False
        
        return recommendations
    
    def get_performance_guidelines(self) -> Dict[str, Any]:
        """
        Get performance guidelines based on current device.
        
        Returns:
            Dictionary of performance guidelines
        """
        perf_config = self._config["performance"]
        
        # Base guidelines
        guidelines = {
            "target_fps": perf_config["target_fps"],
            "max_main_thread_work": perf_config["max_main_thread_work"],
            "max_bundle_size": perf_config["max_bundle_size"],
            "max_image_size": perf_config["max_image_size"],
            "use_code_splitting": True,
            "lazy_load_images": True,
            "use_web_workers": True,
            "minimize_animations": False
        }
        
        # Adjust based on device type
        if self._current_device.device_type == DeviceType.PHONE:
            guidelines.update({
                "target_fps": 30,
                "max_main_thread_work": perf_config["max_main_thread_work"] // 2,
                "max_bundle_size": perf_config["max_bundle_size"] // 2,
                "max_image_size": perf_config["max_image_size"] // 2,
                "minimize_animations": True
            })
        elif self._current_device.device_type == DeviceType.TABLET:
            guidelines.update({
                "max_main_thread_work": int(perf_config["max_main_thread_work"] * 0.75),
                "max_bundle_size": int(perf_config["max_bundle_size"] * 0.75),
                "max_image_size": int(perf_config["max_image_size"] * 0.75)
            })
        
        # Adjust for connection type
        if self._current_device.connection_type == "cellular":
            guidelines.update({
                "max_bundle_size": guidelines["max_bundle_size"] // 2,
                "max_image_size": guidelines["max_image_size"] // 2,
                "minimize_animations": True
            })
        
        return guidelines
    
    def get_pwa_manifest(self) -> Dict[str, Any]:
        """
        Get Progressive Web App manifest recommendations.
        
        Returns:
            Dictionary with PWA manifest recommendations
        """
        # Base PWA manifest
        manifest = {
            "name": "MT 9 EMA Backtester",
            "short_name": "MT9EMA",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#5b21b6",
            "orientation": "any",
            "icons": [
                {
                    "src": "icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            "screenshots": [
                {
                    "src": "screenshots/desktop.png",
                    "sizes": "1280x800",
                    "type": "image/png",
                    "form_factor": "wide"
                },
                {
                    "src": "screenshots/mobile.png",
                    "sizes": "750x1334",
                    "type": "image/png",
                    "form_factor": "narrow"
                }
            ],
            "shortcuts": [
                {
                    "name": "Run Backtest",
                    "short_name": "Backtest",
                    "description": "Start a new backtest",
                    "url": "/backtest",
                    "icons": [{"src": "icons/backtest.png", "sizes": "192x192"}]
                },
                {
                    "name": "View Results",
                    "short_name": "Results",
                    "description": "View backtest results",
                    "url": "/results",
                    "icons": [{"src": "icons/results.png", "sizes": "192x192"}]
                }
            ]
        }
        
        # Adjust based on device
        if self._current_device.device_type == DeviceType.PHONE:
            manifest["orientation"] = "portrait"
        
        return manifest
    
    def get_service_worker_config(self) -> Dict[str, Any]:
        """
        Get service worker configuration for offline capabilities.
        
        Returns:
            Dictionary with service worker configuration
        """
        # Base configuration
        config = {
            "cache_name": "mt9ema-cache-v1",
            "precache_urls": [
                "/",
                "/index.html",
                "/styles.css",
                "/main.js",
                "/favicon.ico"
            ],
            "cacheable_extensions": [
                "html", "css", "js", "json", "png", "jpg", "jpeg", 
                "svg", "woff", "woff2", "ttf", "eot"
            ],
            "network_first_routes": [
                "/api/market-data/",
                "/api/auth/"
            ],
            "cache_first_routes": [
                "/icons/",
                "/assets/",
                "/fonts/"
            ],
            "stale_while_revalidate_routes": [
                "/api/static-data/",
                "/api/user-config/"
            ]
        }
        
        return config


# Global instance
mobile_accessibility_manager = MobileAccessibilityManager()

def get_mobile_accessibility_manager() -> MobileAccessibilityManager:
    """
    Get the global mobile accessibility manager instance.
    
    Returns:
        MobileAccessibilityManager instance
    """
    return mobile_accessibility_manager

def get_device_info(user_agent: str = "", 
                   screen_width: int = 1920, 
                   screen_height: int = 1080,
                   pixel_ratio: float = 1.0,
                   is_touch: bool = False,
                   connection_type: str = "wifi",
                   is_standalone: bool = False) -> DeviceInfo:
    """
    Create a DeviceInfo object based on parameters.
    
    Args:
        user_agent: Browser user agent string
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        pixel_ratio: Pixel ratio (for high-DPI displays)
        is_touch: Whether the device has touch capability
        connection_type: Network connection type
        is_standalone: Whether the app is running in standalone mode
        
    Returns:
        DeviceInfo object
    """
    manager = get_mobile_accessibility_manager()
    
    device_type = manager.detect_device_type(screen_width, screen_height, user_agent)
    orientation = manager.detect_orientation(screen_width, screen_height)
    
    return DeviceInfo(
        device_type=device_type,
        orientation=orientation,
        screen_width=screen_width,
        screen_height=screen_height,
        pixel_ratio=pixel_ratio,
        is_touch=is_touch,
        connection_type=connection_type,
        user_agent=user_agent,
        is_standalone=is_standalone
    )

def is_mobile(user_agent: str = "") -> bool:
    """
    Check if a user agent string appears to be from a mobile device.
    
    Args:
        user_agent: Browser user agent string
        
    Returns:
        True if mobile, False otherwise
    """
    # Simple regex patterns for mobile detection
    mobile_patterns = [
        r'Android',
        r'iPhone',
        r'iPad',
        r'Windows Phone',
        r'Mobile',
        r'Tablet',
        r'BlackBerry',
        r'Opera Mini'
    ]
    
    return any(re.search(pattern, user_agent, re.IGNORECASE) for pattern in mobile_patterns)

def optimize_for_mobile(func: Callable):
    """
    Decorator to optimize a function's output for mobile devices.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the original output
        output = func(*args, **kwargs)
        
        # Check if we should optimize
        device_info = kwargs.get('device_info')
        if device_info and device_info.device_type != DeviceType.DESKTOP:
            # If the output is a dictionary, modify it for mobile
            if isinstance(output, dict):
                # Simplify output for mobile devices
                if 'detailed_metrics' in output and device_info.device_type == DeviceType.PHONE:
                    # Keep only essential metrics for phones
                    essential_keys = ['win_rate', 'profit_factor', 'avg_trade', 'total_trades']
                    output['detailed_metrics'] = {
                        k: v for k, v in output['detailed_metrics'].items() if k in essential_keys
                    }
                
                # Reduce image quality for mobile
                if 'images' in output and isinstance(output['images'], list):
                    for i, img in enumerate(output['images']):
                        if isinstance(img, dict) and 'url' in img:
                            # Add mobile-optimized image URL
                            output['images'][i]['url'] = img['url'].replace('.png', '-mobile.png')
                
                # Add mobile flag
                output['is_mobile_optimized'] = True
        
        return output
    return wrapper 