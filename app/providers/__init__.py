"""Provider package — auto-discovers and registers all providers.

Open/Closed Principle: Adding a new provider only requires creating a new
module in this package decorated with @provider_registry.auto_register.
No changes to this file are needed.
"""
import importlib
import pkgutil

from app.providers.base import provider_registry

# Auto-discover all provider modules to trigger @provider_registry.auto_register decorators.
# Any Python module in this package (except 'base') is imported automatically.
for _, module_name, _ in pkgutil.iter_modules(__path__):
    if module_name != "base":
        importlib.import_module(f".{module_name}", package=__name__)
