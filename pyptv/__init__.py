from .__version__ import __version__ as __version__

# Traits is only required for the legacy Qt/TraitsUI GUI. Make it optional so
# headless/test environments can import pyptv without installing traits.
try:  # pragma: no cover - trivial import guard
	from traits.etsconfig.etsconfig import ETSConfig
except Exception:  # Traits not available; skip configuring toolkit
	ETSConfig = None  # type: ignore[assignment]
else:  # Traits available; set default toolkit to Qt
	ETSConfig.toolkit = "qt"

