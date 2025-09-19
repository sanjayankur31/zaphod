#!/usr/bin/env python3
"""
File: zaphod/__init__.py

Copyright 2025 Ankur Sinha
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("zaphod")
except ImportError:
    import importlib_metadata

    __version__ = importlib_metadata.version("zaphod")
