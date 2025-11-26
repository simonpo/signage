"""
Image processing utilities.
Handles cropping, resizing, and overlays for optimal display quality.
"""

import logging

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


def smart_crop_to_fill(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Crop and resize image to exactly fill target dimensions.
    Uses center-weighted cropping - no letterboxing.

    Args:
        image: Input PIL Image
        target_width: Target width in pixels
        target_height: Target height in pixels

    Returns:
        Cropped and resized image at exact target dimensions
    """
    # Calculate aspect ratios
    img_aspect = image.width / image.height
    target_aspect = target_width / target_height

    if img_aspect > target_aspect:
        # Image is wider - crop width
        new_width = int(image.height * target_aspect)
        new_height = image.height
        left = (image.width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = new_height
    else:
        # Image is taller - crop height
        new_width = image.width
        new_height = int(image.width / target_aspect)
        left = 0
        top = (image.height - new_height) // 2
        right = new_width
        bottom = top + new_height

    # Crop to correct aspect ratio
    cropped = image.crop((left, top, right, bottom))

    # Resize to exact target dimensions using high-quality resampling
    resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)

    logger.debug(
        f"Cropped {image.size} → {cropped.size}, " f"resized to {target_width}x{target_height}"
    )

    return resized


def add_text_overlay(image: Image.Image, opacity: float = 0.4) -> Image.Image:
    """
    Add semi-transparent gradient overlay for better text readability.
    Gradient is darker at bottom where timestamps usually appear.

    Args:
        image: Input PIL Image (will be converted to RGBA if needed)
        opacity: Overlay opacity (0.0 to 1.0)

    Returns:
        Image with overlay applied
    """
    # Convert to RGBA if needed
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Create overlay with vertical gradient
    overlay = Image.new("RGBA", image.size)
    draw = ImageDraw.Draw(overlay)

    width, height = image.size

    # Vertical gradient from transparent at top to semi-opaque at bottom
    for y in range(height):
        # Gradient strength increases towards bottom
        alpha = int(opacity * 255 * (y / height))
        color = (0, 0, 0, alpha)
        draw.line([(0, y), (width, y)], fill=color)

    # Composite overlay onto image
    result = Image.alpha_composite(image, overlay)

    # Convert back to RGB
    return result.convert("RGB")


def ensure_exact_size(image: Image.Image, width: int, height: int) -> Image.Image:
    """
    Paranoid check: ensure image is exactly the target size.
    If not, apply smart_crop_to_fill.

    Args:
        image: Input image
        width: Required width
        height: Required height

    Returns:
        Image guaranteed to be exactly width x height
    """
    if image.size == (width, height):
        return image

    logger.warning(
        f"Image size mismatch: got {image.size}, expected ({width}, {height}). "
        f"Applying corrective crop."
    )

    return smart_crop_to_fill(image, width, height)
