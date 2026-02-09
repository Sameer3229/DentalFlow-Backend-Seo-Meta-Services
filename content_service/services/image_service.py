import os
import uuid
from PIL import Image
from django.conf import settings
from google import genai
from google.genai import types
from django.conf import settings
api_key=settings.GEMINI_API_KEY


def imagen_client():
    """
    Initialize Google GenAI client using environment variable.
    """
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY missing. Please set it in environment variables.")
    
    return genai.Client(api_key=api_key)


def generate_image_from_post(content: str, platform: str) -> str:
    """
    Generate a social media image for given content and platform.
    
    Returns:
        str: URL path to the saved image (relative to MEDIA_ROOT)
    """
#     prompt = f"""
# Create a high-quality social media graphic inspired by:

# \"\"\"{content}\"\"\"

# Rules:
# - No text inside the image
# - Clean, modern, aesthetic
# - Style matches {platform}
# """
    prompt = f"""
Create a visually appealing social media graphic.

- Inspired by the mood and theme of the following post, but do NOT include any text:
\"\"\"{content}\"\"\"
- Style: modern, clean, professional, aesthetic
- Platform: {platform} (adapt colors and design to fit)
- Focus on imagery, symbols, abstract representation, or illustrations
- No logos, no text, no captions
- High quality, photorealistic or digital art style
"""
    client = imagen_client()

    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1)
    )

    # Get PIL image object
    image: Image.Image = response.generated_images[0].image

    # Save image to MEDIA_ROOT/generated/
    filename = f"{uuid.uuid4().hex}.png"
    output_dir = os.path.join(settings.MEDIA_ROOT, "generated")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    image.save(output_path)

    # Return relative URL path
    return f"/media/generated/{filename}"
