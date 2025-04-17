# Configuration System

This document explains the configuration system used in the WA Health backend application to manage environment variables, URLs, and other settings.

## Overview

We've implemented a centralized configuration system using Pydantic's `BaseSettings` to manage all application settings. This approach provides several benefits:

1. **Type safety** - Settings are validated at application startup
2. **Environment variable overrides** - Settings can be overridden through environment variables
3. **Centralized management** - All application settings are defined in one place
4. **Default values** - Sensible defaults for development are provided

## Configuration Structure

The configuration is managed through:

1. **`app/config/config.py`** - The main settings class that defines all application settings
2. **`.env`** - Environment-specific values loaded at runtime
3. **`.env.example`** - Example file showing which variables should be set

## URLs and External Services

All URLs for external services are now centralized in the settings class and can be overridden through environment variables:

- `AUTH_SERVICE_URL` - Base URL for the authentication service
- `VAPI_BASE_URL` - Base URL for the Vapi API
- `POSTMAN_BASE_URL` - Base URL for the Postman mock API
- `CORS_ORIGINS` - List of allowed origins for CORS

## Using Settings in Code

To use settings in your code, import the settings instance:

```python
from app.config.config import settings

# Then use settings directly
auth_url = settings.AUTH_SERVICE_URL
```

## Best Practices

1. **Never hardcode URLs** - Always use the settings system for URLs and other configurable values
2. **Use path constants** - For API endpoints, define constants in the settings class
3. **Environment-specific configuration** - Use environment variables for environment-specific settings
4. **Document new settings** - When adding new settings, document them in this file
5. **Add to example file** - Update the `.env.example` file with placeholder values for any new settings

## Adding New Settings

To add a new setting:

1. Add it to the `Settings` class in `app/config/config.py`
2. Provide a sensible default value if possible
3. Add it to the `.env.example` file with a placeholder or example value
4. Document its purpose in this file

## Future Improvements

Potential future improvements to the configuration system:

1. Add validation for URL formats
2. Implement more complex nested configuration structures
3. Add support for different configuration profiles (dev, staging, prod)
4. Implement configuration versioning and validation

## Updating the Configuration

When making significant changes to the configuration structure:

1. Update this documentation
2. Notify the team of the changes
3. Update the `.env.example` file
4. Ensure backward compatibility where possible
