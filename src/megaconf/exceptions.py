class UnsupportedConfigFileError(ValueError):
    """Raised when a configuration file has an unsupported extension."""


class FlatKeyConflictError(ValueError):
    """Raised when flat override keys define conflicting nested paths."""
