from .__version__ import __version__ as __version__

# Make Traits optional so importing the package in headless/test environments
# does not require installing the full TraitsUI stack.
try:  # pragma: no cover - import guard
	from traits.etsconfig.etsconfig import ETSConfig
except Exception:
	ETSConfig = None
else:
	ETSConfig.toolkit = "qt"

