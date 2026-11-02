"""Guide's explicit Chevron extension configuration."""

from chevron import Extension

_configured = False


def configure_chevron_extensions() -> None:
    """Enable only the Chevron extensions adopted by Guide templates."""
    global _configured
    if _configured:
        return
    Extension.enable(Extension.CONDITIONAL_SECTIONS | Extension.ENHANCED_ITERATORS)
    _configured = True
