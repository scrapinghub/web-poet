import warnings

from web_poet.rules import *  # noqa: F401, F403

msg = "The 'web_poet.overrides' module has been moved into 'web_poet.rules'."
warnings.warn(msg, DeprecationWarning, stacklevel=2)
