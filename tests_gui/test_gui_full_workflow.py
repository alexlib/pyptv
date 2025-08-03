import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None or os.environ.get("QT_QPA_PLATFORM") == "offscreen",
    reason="GUI/Qt tests require a display (DISPLAY or QT_QPA_PLATFORM)"
)
