# Core Module API Reference

## Config

Configuration management for DeltaFQ.

### Methods

- `__init__(config_file=None)`: Initialize configuration
- `get(key, default=None)`: Get configuration value
- `set(key, value)`: Set configuration value

## Logger

Logging system for DeltaFQ components.

### Methods

- `__init__(name="deltafq", level="INFO")`: Initialize logger
- `debug(message)`: Log debug message
- `info(message)`: Log info message
- `warning(message)`: Log warning message
- `error(message)`: Log error message
- `critical(message)`: Log critical message

## BaseComponent

Base class for all DeltaFQ components.

### Methods

- `__init__(name=None, config=None)`: Initialize component
- `initialize() -> bool`: Initialize the component
- `cleanup()`: Cleanup resources
- `get_info() -> Dict[str, Any]`: Get component information

