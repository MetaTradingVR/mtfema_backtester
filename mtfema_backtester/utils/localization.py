"""
Localization Framework for MT 9 EMA Backtester.

This module provides internationalization (i18n) support for multiple languages,
enabling the application to be used by traders worldwide.
"""

import os
import json
import locale
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Setup logger
logger = logging.getLogger(__name__)

class Direction(Enum):
    """Text direction for languages."""
    LTR = "ltr"  # Left-to-right (e.g., English, Spanish)
    RTL = "rtl"  # Right-to-left (e.g., Arabic, Hebrew)


@dataclass
class Language:
    """Represents a language supported by the application."""
    
    # Language code (e.g., 'en', 'es', 'zh')
    code: str
    
    # Native name of the language (e.g., 'English', 'Español', '中文')
    name: str
    
    # Text direction
    direction: Direction
    
    # Flag emoji or code
    flag: str
    
    # Whether the language is fully supported
    is_complete: bool = False


class LocalizationManager:
    """Manages language translations and localization."""
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LocalizationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, translations_dir: Optional[str] = None, default_language: str = "en"):
        """
        Initialize the localization manager.
        
        Args:
            translations_dir: Directory containing translation files
            default_language: Default language code
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return
            
        self._initialized = True
        
        # Set translations directory
        self._translations_dir = translations_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "translations"
        )
        
        # Ensure translations directory exists
        os.makedirs(self._translations_dir, exist_ok=True)
        
        # Define supported languages
        self._languages: Dict[str, Language] = {
            "en": Language(code="en", name="English", direction=Direction.LTR, flag="🇺🇸", is_complete=True),
            "es": Language(code="es", name="Español", direction=Direction.LTR, flag="🇪🇸"),
            "fr": Language(code="fr", name="Français", direction=Direction.LTR, flag="🇫🇷"),
            "de": Language(code="de", name="Deutsch", direction=Direction.LTR, flag="🇩🇪"),
            "zh": Language(code="zh", name="中文", direction=Direction.LTR, flag="🇨🇳"),
            "ja": Language(code="ja", name="日本語", direction=Direction.LTR, flag="🇯🇵"),
            "ru": Language(code="ru", name="Русский", direction=Direction.LTR, flag="🇷🇺"),
            "ar": Language(code="ar", name="العربية", direction=Direction.RTL, flag="🇸🇦"),
            "hi": Language(code="hi", name="हिन्दी", direction=Direction.LTR, flag="🇮🇳"),
            "pt": Language(code="pt", name="Português", direction=Direction.LTR, flag="🇧🇷")
        }
        
        # Set default language
        self._default_language = default_language if default_language in self._languages else "en"
        
        # Current language
        self._current_language = self._detect_language()
        
        # Load translations
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()
        
        logger.info(f"Localization initialized with language: {self._current_language}")
    
    def _detect_language(self) -> str:
        """
        Detect the user's preferred language.
        
        Returns:
            Language code for the detected language
        """
        # Check if language is set in environment variable
        env_lang = os.environ.get("MTFEMA_LANGUAGE")
        if env_lang and env_lang in self._languages:
            return env_lang
            
        # Check if there's a stored preference
        config_path = os.path.join(os.path.dirname(self._translations_dir), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    lang = config.get("language")
                    if lang and lang in self._languages:
                        return lang
            except Exception as e:
                logger.error(f"Error loading language preference: {str(e)}")
        
        # Fall back to system locale
        try:
            system_locale, _ = locale.getdefaultlocale()
            if system_locale:
                lang_code = system_locale.split('_')[0]
                if lang_code in self._languages:
                    return lang_code
        except Exception as e:
            logger.error(f"Error detecting system locale: {str(e)}")
        
        # Default to English if all else fails
        return self._default_language
    
    def _load_translations(self) -> None:
        """Load translations for all languages."""
        for lang_code in self._languages:
            self._load_language_translations(lang_code)
    
    def _load_language_translations(self, lang_code: str) -> None:
        """
        Load translations for a specific language.
        
        Args:
            lang_code: Language code to load
        """
        # Skip loading English as it's the base language
        if lang_code == "en":
            return
            
        translation_file = os.path.join(self._translations_dir, f"{lang_code}.json")
        
        if not os.path.exists(translation_file):
            logger.warning(f"Translation file not found for {lang_code}, creating template")
            self._create_translation_template(lang_code)
            return
            
        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                self._translations[lang_code] = json.load(f)
                
            # Check if all translations are present
            is_complete = self._check_translation_completeness(lang_code)
            self._languages[lang_code].is_complete = is_complete
                
            logger.info(f"Loaded {len(self._translations[lang_code])} translations for {lang_code}")
        except Exception as e:
            logger.error(f"Error loading translations for {lang_code}: {str(e)}")
            self._translations[lang_code] = {}
    
    def _create_translation_template(self, lang_code: str) -> None:
        """
        Create a template translation file for a language.
        
        Args:
            lang_code: Language code for the template
        """
        # Load English strings as a basis for translation
        english_strings = self._get_base_strings()
        
        # Create empty translation template
        template = {key: "" for key in english_strings}
        
        # Save template
        translation_file = os.path.join(self._translations_dir, f"{lang_code}.json")
        try:
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Created translation template for {lang_code}")
        except Exception as e:
            logger.error(f"Error creating translation template for {lang_code}: {str(e)}")
    
    def _get_base_strings(self) -> Dict[str, str]:
        """
        Get the base set of strings for translation.
        
        This serves as the master list of all translatable strings.
        
        Returns:
            Dictionary of string keys and English values
        """
        # Default set of strings in English
        # In a real implementation, these would be extracted from the codebase
        return {
            "app.name": "MT 9 EMA Backtester",
            "app.description": "A comprehensive backtesting system for the Multi-Timeframe 9 EMA Extension trading strategy",
            
            # General UI terms
            "ui.save": "Save",
            "ui.cancel": "Cancel",
            "ui.ok": "OK",
            "ui.back": "Back",
            "ui.next": "Next",
            "ui.close": "Close",
            "ui.loading": "Loading...",
            "ui.search": "Search",
            "ui.settings": "Settings",
            "ui.theme": "Theme",
            "ui.language": "Language",
            
            # Navigation
            "nav.home": "Home",
            "nav.backtest": "Backtest",
            "nav.results": "Results",
            "nav.strategy": "Strategy",
            "nav.community": "Community",
            "nav.settings": "Settings",
            
            # Backtest
            "backtest.title": "Run Backtest",
            "backtest.symbol": "Symbol",
            "backtest.start_date": "Start Date",
            "backtest.end_date": "End Date",
            "backtest.timeframes": "Timeframes",
            "backtest.run": "Run Backtest",
            "backtest.stop": "Stop",
            "backtest.progress": "Progress",
            "backtest.error": "Error in Backtest",
            
            # Strategy
            "strategy.ema_period": "EMA Period",
            "strategy.extension_threshold": "Extension Threshold",
            "strategy.reclamation_threshold": "Reclamation Threshold",
            "strategy.pullback_threshold": "Pullback Threshold",
            "strategy.risk_per_trade": "Risk Per Trade",
            "strategy.target_multiplier": "Target Multiplier",
            
            # Results
            "results.total_trades": "Total Trades",
            "results.win_rate": "Win Rate",
            "results.profit_factor": "Profit Factor",
            "results.max_drawdown": "Max Drawdown",
            "results.avg_trade": "Average Trade",
            "results.sharpe_ratio": "Sharpe Ratio",
            
            # Community
            "community.forums": "Forums",
            "community.signals": "Trading Signals",
            "community.sharing": "Share Setup",
            "community.profile": "Profile",
            "community.leaderboard": "Leaderboard",
            
            # Errors
            "error.data_load": "Failed to load data",
            "error.invalid_input": "Invalid input",
            "error.connection": "Connection error",
            "error.permission": "Permission denied",
            "error.unknown": "Unknown error occurred"
        }
    
    def _check_translation_completeness(self, lang_code: str) -> bool:
        """
        Check if a language translation is complete.
        
        Args:
            lang_code: Language code to check
            
        Returns:
            True if all strings are translated, False otherwise
        """
        if lang_code not in self._translations:
            return False
            
        base_strings = self._get_base_strings()
        translations = self._translations[lang_code]
        
        # Check if all keys are present and have non-empty values
        for key in base_strings:
            if key not in translations or not translations[key]:
                return False
                
        return True
    
    def set_language(self, lang_code: str) -> bool:
        """
        Set the current language.
        
        Args:
            lang_code: Language code to set
            
        Returns:
            True if successful, False otherwise
        """
        if lang_code not in self._languages:
            logger.warning(f"Language {lang_code} not supported")
            return False
            
        self._current_language = lang_code
        
        # Save language preference
        config_path = os.path.join(os.path.dirname(self._translations_dir), "config.json")
        try:
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            config["language"] = lang_code
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving language preference: {str(e)}")
        
        logger.info(f"Language set to {lang_code}")
        return True
    
    def get_current_language(self) -> str:
        """
        Get the current language code.
        
        Returns:
            Current language code
        """
        return self._current_language
    
    def get_language_direction(self) -> Direction:
        """
        Get the text direction for the current language.
        
        Returns:
            Text direction (LTR or RTL)
        """
        return self._languages[self._current_language].direction
    
    def get_supported_languages(self) -> List[Language]:
        """
        Get a list of all supported languages.
        
        Returns:
            List of Language objects
        """
        return list(self._languages.values())
    
    @lru_cache(maxsize=1024)
    def translate(self, key: str, default: Optional[str] = None) -> str:
        """
        Translate a string key to the current language.
        
        Args:
            key: String key to translate
            default: Default value if key is not found
            
        Returns:
            Translated string
        """
        if self._current_language == "en":
            # For English, use the base strings
            base_strings = self._get_base_strings()
            return base_strings.get(key, default or key)
            
        # For other languages, look up in translations
        if self._current_language in self._translations:
            translations = self._translations[self._current_language]
            if key in translations and translations[key]:
                return translations[key]
                
        # Fall back to English if translation not found
        base_strings = self._get_base_strings()
        return base_strings.get(key, default or key)
    
    def format_number(self, number: float, decimal_places: int = 2) -> str:
        """
        Format a number according to the current locale.
        
        Args:
            number: Number to format
            decimal_places: Number of decimal places
            
        Returns:
            Formatted number string
        """
        try:
            # Set locale based on current language
            locale_map = {
                "en": "en_US",
                "es": "es_ES",
                "fr": "fr_FR",
                "de": "de_DE",
                "zh": "zh_CN",
                "ja": "ja_JP",
                "ru": "ru_RU",
                "ar": "ar_SA",
                "hi": "hi_IN",
                "pt": "pt_BR"
            }
            
            loc = locale_map.get(self._current_language, "en_US")
            
            # Save current locale
            current_locale = locale.getlocale(locale.LC_NUMERIC)
            
            try:
                # Set temporary locale
                locale.setlocale(locale.LC_NUMERIC, loc)
                
                # Format number
                return locale.format_string(f"%.{decimal_places}f", number, grouping=True)
            finally:
                # Restore original locale
                locale.setlocale(locale.LC_NUMERIC, current_locale)
        except Exception as e:
            logger.error(f"Error formatting number: {str(e)}")
            return f"{number:.{decimal_places}f}"
    
    def format_date(self, date_obj, format_str: Optional[str] = None) -> str:
        """
        Format a date according to the current locale.
        
        Args:
            date_obj: Date object to format
            format_str: Optional format string
            
        Returns:
            Formatted date string
        """
        try:
            # Set locale based on current language
            locale_map = {
                "en": "en_US",
                "es": "es_ES",
                "fr": "fr_FR",
                "de": "de_DE",
                "zh": "zh_CN",
                "ja": "ja_JP",
                "ru": "ru_RU",
                "ar": "ar_SA",
                "hi": "hi_IN",
                "pt": "pt_BR"
            }
            
            loc = locale_map.get(self._current_language, "en_US")
            
            # Save current locale
            current_locale = locale.getlocale(locale.LC_TIME)
            
            try:
                # Set temporary locale
                locale.setlocale(locale.LC_TIME, loc)
                
                # Use appropriate format for the locale
                if not format_str:
                    format_str = "%x"  # Locale's appropriate date representation
                
                # Format date
                return date_obj.strftime(format_str)
            finally:
                # Restore original locale
                locale.setlocale(locale.LC_TIME, current_locale)
        except Exception as e:
            logger.error(f"Error formatting date: {str(e)}")
            return str(date_obj)


# Global instance
localization_manager = LocalizationManager()

def get_localization_manager() -> LocalizationManager:
    """
    Get the global localization manager instance.
    
    Returns:
        LocalizationManager instance
    """
    return localization_manager

def translate(key: str, default: Optional[str] = None) -> str:
    """
    Translate a string key to the current language.
    
    Args:
        key: String key to translate
        default: Default value if key is not found
        
    Returns:
        Translated string
    """
    return localization_manager.translate(key, default)

def set_language(lang_code: str) -> bool:
    """
    Set the current language.
    
    Args:
        lang_code: Language code to set
        
    Returns:
        True if successful, False otherwise
    """
    return localization_manager.set_language(lang_code)

def get_current_language() -> str:
    """
    Get the current language code.
    
    Returns:
        Current language code
    """
    return localization_manager.get_current_language()

def format_number(number: float, decimal_places: int = 2) -> str:
    """
    Format a number according to the current locale.
    
    Args:
        number: Number to format
        decimal_places: Number of decimal places
        
    Returns:
        Formatted number string
    """
    return localization_manager.format_number(number, decimal_places)

def format_date(date_obj, format_str: Optional[str] = None) -> str:
    """
    Format a date according to the current locale.
    
    Args:
        date_obj: Date object to format
        format_str: Optional format string
        
    Returns:
        Formatted date string
    """
    return localization_manager.format_date(date_obj, format_str)

# Convenience function alias
def _(key: str, default: Optional[str] = None) -> str:
    """
    Shorthand for translate function.
    
    Args:
        key: String key to translate
        default: Default value if key is not found
        
    Returns:
        Translated string
    """
    return translate(key, default) 