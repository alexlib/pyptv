from .__version__ import __version__ as __version__
try:
	from traits.etsconfig.etsconfig import ETSConfig

	ETSConfig.toolkit = "qt"
except ModuleNotFoundError:
	# Traits is an optional dependency for headless/non-GUI usage.
	# GUI entrypoints will still require traits/traitsui to be installed.
	pass

