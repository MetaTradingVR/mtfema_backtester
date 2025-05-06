# Internationalization and Localization

This document outlines the internationalization (i18n) and localization (l10n) framework for the MT 9 EMA Backtester, enabling the application to be used by traders worldwide in their preferred languages.

## Overview

The MT 9 EMA Backtester includes comprehensive internationalization support to make the application accessible to a global audience. This framework provides:

- Multiple language support
- Locale-aware date and number formatting
- Right-to-left (RTL) text direction support
- Translation workflows for contributors

## Supported Languages

The application currently supports the following languages:

| Language | Code | Direction | Status |
|----------|------|-----------|--------|
| English | `en` | LTR | Complete |
| Spanish | `es` | LTR | Partial |
| French | `fr` | LTR | Partial |
| German | `de` | LTR | Partial |
| Chinese | `zh` | LTR | Partial |
| Japanese | `ja` | LTR | Partial |
| Russian | `ru` | LTR | Partial |
| Arabic | `ar` | RTL | Partial |
| Hindi | `hi` | LTR | Partial |
| Portuguese | `pt` | LTR | Partial |

Additional languages can be easily added to the framework.

## Implementation

### Language Selection

The system automatically detects and selects the user's preferred language based on:

1. Explicit user selection (stored in configuration)
2. Environment variable (`MTFEMA_LANGUAGE`)
3. System locale
4. Default to English if no match is found

```python
# Example of language detection
def _detect_language(self) -> str:
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
    return "en"
```

### String Translation

The application uses a key-based translation system:

```python
from mtfema_backtester.utils.localization import translate, _

# Long form
message = translate("backtest.progress", "Backtest Progress")

# Short form (recommended)
message = _("backtest.progress", "Backtest Progress")
```

The second parameter is the default value used if no translation is found.

### Locale-Aware Formatting

Numbers and dates are formatted according to the user's locale:

```python
from mtfema_backtester.utils.localization import format_number, format_date
import datetime

# Format a number
profit_percentage = format_number(15.75, decimal_places=2)  # "15.75" in English, "15,75" in German

# Format a date
current_date = datetime.datetime.now()
formatted_date = format_date(current_date)  # "05/07/2025" in US English, "07/05/2025" in UK English
```

### RTL Support

For right-to-left languages like Arabic, the framework handles text direction:

```python
from mtfema_backtester.utils.localization import get_localization_manager, Direction

# Check the current language direction
manager = get_localization_manager()
direction = manager.get_language_direction()

is_rtl = (direction == Direction.RTL)
```

## Translation Management

### Translation Files

Translations are stored in JSON files in the `translations` directory, with one file per language:

```
translations/
  es.json
  fr.json
  de.json
  ...
```

Each file contains key-value pairs mapping translation keys to translated strings:

```json
{
  "app.name": "Backtester de 9 EMA",
  "backtest.run": "Ejecutar Backtest",
  "results.win_rate": "Tasa de Ganancia",
  // ...
}
```

### Adding New Translations

New translatable strings should follow these guidelines:

1. Use descriptive, hierarchical keys (e.g., `category.subcategory.term`)
2. Provide a default English value for fallback
3. Avoid string concatenation; use placeholders for dynamic content
4. Consider pluralization rules for different languages

```python
# Good:
_("results.trades.count", "Total: {count} trades", {"count": trade_count})

# Avoid:
_("results.trades.total", "Total: ") + str(trade_count) + _("results.trades.suffix", " trades")
```

### Translation Workflow for Contributors

To contribute translations:

1. Run the application with `--generate-translation-template <lang>` to create a template file
2. Fill in the translations in the generated file
3. Submit the completed file via a pull request
4. New translations will be included in the next release

## Using Localization in UI Components

### Text Display

Always use the translation functions for user-visible text:

```python
def render_report_header():
    return f"""
    <h1>{_("report.title", "Backtest Report")}</h1>
    <p>{_("report.generated_at", "Generated at:")} {format_date(datetime.datetime.now())}</p>
    """
```

### Placeholders

For text with dynamic content, use placeholder substitution:

```python
def display_results(win_count, loss_count):
    template = _("results.summary", "Results: {wins} wins, {losses} losses")
    return template.format(wins=win_count, losses=loss_count)
```

### Component Layout

For RTL language support, adjust component layout based on text direction:

```python
def create_navigation_component():
    direction = get_localization_manager().get_language_direction()
    
    if direction == Direction.RTL:
        # Align buttons to left for RTL languages
        button_alignment = "left"
        icon_order = "reverse"
    else:
        # Align buttons to right for LTR languages
        button_alignment = "right"
        icon_order = "normal"
        
    # Create component with appropriate alignment
    # ...
```

## Best Practices

### Translation Keys

- Use hierarchical keys (e.g., `category.subcategory.name`)
- Keep keys lowercase and use underscores or dots as separators
- Use descriptive keys that reflect the context and meaning
- Group related keys together in the same namespace

### Translation Content

- Keep translations concise
- Maintain consistent terminology
- Avoid idioms that may not translate well
- Consider text expansion (some languages take more space than English)
- Provide context notes for translators when needed

### Testing

- Test with non-Latin character sets (e.g., Chinese, Russian, Arabic)
- Verify RTL layout in Arabic
- Check date and number formatting across locales
- Test with longer translated strings (German tends to be longer than English)

## Extending the Framework

### Adding a New Language

To add support for a new language:

1. Add the language to the `_languages` dictionary in `LocalizationManager`
2. Create a translation file in the `translations` directory
3. Begin translating strings for the new language

### Custom Formatting Rules

For languages with special formatting needs:

1. Extend the `format_number` and `format_date` methods
2. Add locale-specific logic for the language
3. Add appropriate test cases

## Future Improvements

Planned enhancements to the localization framework:

1. **Pluralization Support**: Handle different plural forms based on language rules
2. **Translation Memory**: Build a database of previously translated strings
3. **Context-Aware Translation**: Provide context information for translators
4. **Automated Translation Workflows**: Integration with translation services
5. **Live Language Switching**: Change language without application restart 