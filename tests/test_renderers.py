"""
Tests for image rendering.
"""

import tempfile
from pathlib import Path

from PIL import Image

from src.config import Config
from src.models.signage_data import SignageContent, TeslaData
from src.renderers.image_renderer import SignageRenderer


def test_renderer_initialization():
    """Test that renderer initializes with fonts."""
    renderer = SignageRenderer()
    assert renderer.width == 3840
    assert renderer.height == 2160
    assert renderer.font_title is not None
    assert renderer.font_body is not None
    assert renderer.font_small is not None


def test_render_tesla_signage():
    """Test rendering Tesla signage to exact dimensions."""
    renderer = SignageRenderer()
    
    # Create test data
    tesla_data = TeslaData(
        battery_level="85",
        battery_unit="%",
        range="250",
        range_unit=" mi"
    )
    
    content = tesla_data.to_signage()
    
    # Render to temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        result = renderer.render(content, output_path)
        
        # Verify file exists
        assert result.exists()
        
        # Verify dimensions
        img = Image.open(result)
        assert img.size == (3840, 2160)
        assert img.mode == "RGB"
        
        img.close()
    
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_image_exact_dimensions():
    """Paranoid test: ensure all rendered images are EXACTLY 3840x2160."""
    from src.utils.image_utils import ensure_exact_size
    
    # Create test image of wrong size
    img = Image.new("RGB", (1920, 1080))
    
    # Correct it
    corrected = ensure_exact_size(img, 3840, 2160)
    
    # Verify
    assert corrected.size == (3840, 2160)
