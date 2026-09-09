"""NexusMind tool integrations.

Modules are intentionally not imported eagerly here so lightweight services and
unit tests do not load optional web-search, vector-store, or Azure dependencies.
Import the specific tool module where it is used.
"""
