try:
    import pkgutil
except ImportError:
    raise ImportError("pkgutil module is required for this package to function correctly.")

try:
    __path__ = pkgutil.extend_path(__path__, __name__)
except Exception as e:
    # Log or handle the exception appropriately
    raise RuntimeError(f"Failed to extend package path: {e}")