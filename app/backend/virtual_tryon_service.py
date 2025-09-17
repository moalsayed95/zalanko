"""
Virtual Try-On Service for Zalanko Fashion Platform
Integrates Google Vertex AI Gemini 2.5 Flash Image Preview for virtual try-on functionality.
"""

import os
import base64
import logging
from typing import Optional, Tuple, Dict, Any
from io import BytesIO

from PIL import Image
from google import genai
from google.genai import types

logger = logging.getLogger("virtual_tryon")


class VirtualTryOnError(Exception):
    """Custom exception for virtual try-on related errors."""
    pass


class VirtualTryOnService:
    """Service for generating virtual try-on images using Google Vertex AI."""

    def __init__(self):
        """Initialize the virtual try-on service with Google Cloud credentials."""
        self.api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")

        if not self.api_key or not self.project_id:
            raise VirtualTryOnError("Google Cloud credentials not found in environment")

        try:
            self.client = genai.Client(
                vertexai=True,
                api_key=self.api_key
            )
            # Use global location for image generation capability
            self.model = f"projects/{self.project_id}/locations/global/publishers/google/models/gemini-2.5-flash-image-preview"
            logger.info("✅ VirtualTryOnService initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize VirtualTryOnService: {e}")
            raise VirtualTryOnError(f"Failed to initialize Vertex AI client: {e}")

    def validate_image(self, image_data: bytes, max_size_mb: int = 10) -> bool:
        """
        Validate image data for virtual try-on processing.

        Args:
            image_data: Raw image bytes
            max_size_mb: Maximum allowed file size in MB

        Returns:
            True if image is valid, False otherwise
        """
        try:
            # Check file size
            if len(image_data) > max_size_mb * 1024 * 1024:
                logger.warning(f"Image too large: {len(image_data)} bytes")
                return False

            # Validate image format
            img = Image.open(BytesIO(image_data))

            # Check dimensions (reasonable size for processing)
            width, height = img.size
            if width < 200 or height < 200 or width > 8000 or height > 8000:
                logger.warning(f"Image dimensions out of range: {width}x{height}")
                return False

            logger.info(f"✅ Image dimensions valid: {width}x{height}")

            return True

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False

    def preprocess_image(self, image_data: bytes, target_format: str = "JPEG") -> bytes:
        """
        Preprocess image for optimal virtual try-on results.

        Args:
            image_data: Raw image bytes
            target_format: Target image format (JPEG or PNG)

        Returns:
            Preprocessed image bytes
        """
        try:
            img = Image.open(BytesIO(image_data))

            # Convert to RGB if needed
            if img.mode != 'RGB' and target_format == "JPEG":
                img = img.convert('RGB')
            elif img.mode != 'RGBA' and target_format == "PNG":
                img = img.convert('RGBA')

            # Resize if too large (maintain aspect ratio)
            max_dimension = 1024
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to {new_size}")

            # Save to bytes
            buffer = BytesIO()
            img.save(buffer, format=target_format, quality=90 if target_format == "JPEG" else None)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise VirtualTryOnError(f"Failed to preprocess image: {e}")

    async def generate_virtual_tryon(
        self,
        person_image: bytes,
        clothing_image: bytes,
        product_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Generate virtual try-on image using Vertex AI.

        Args:
            person_image: Person's photo as bytes
            clothing_image: Clothing item image as bytes
            product_info: Optional product information for better prompting

        Returns:
            Tuple of (success, image_bytes, error_message)
        """
        try:
            logger.info("🔄 Starting virtual try-on generation")

            # Validate images
            if not self.validate_image(person_image):
                return False, None, "Invalid person image"

            if not self.validate_image(clothing_image):
                return False, None, "Invalid clothing image"

            # Preprocess images
            person_processed = self.preprocess_image(person_image, "JPEG")
            clothing_processed = self.preprocess_image(clothing_image, "PNG")

            # Create enhanced prompt based on product info
            prompt_text = self._create_enhanced_prompt(product_info)

            # Create content with images and prompt
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=prompt_text),
                        types.Part(
                            inline_data=types.Blob(
                                data=person_processed,
                                mime_type="image/jpeg"
                            )
                        ),
                        types.Part(
                            inline_data=types.Blob(
                                data=clothing_processed,
                                mime_type="image/png"
                            )
                        )
                    ]
                )
            ]

            # Configure generation parameters
            generate_content_config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=32768,
                response_modalities=["TEXT", "IMAGE"],
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="OFF"
                    )
                ]
            )

            # Generate virtual try-on
            logger.info("📡 Sending request to Vertex AI...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config
            )

            logger.info("✅ Received response from Vertex AI")

            # Extract image from response
            result_image = self._extract_image_from_response(response)
            if result_image:
                logger.info(f"🎉 Virtual try-on generated successfully: {len(result_image)} bytes")
                return True, result_image, None
            else:
                logger.warning("⚠️ No image found in response")
                return False, None, "No image generated in response"

        except Exception as e:
            logger.error(f"❌ Virtual try-on generation failed: {e}")
            return False, None, f"Generation failed: {str(e)}"

    def _create_enhanced_prompt(self, product_info: Optional[Dict[str, Any]] = None) -> str:
        """Create an enhanced prompt based on product information."""
        base_prompt = (
            "Create a realistic virtual try-on image. Take the person from the first image and "
            "show them wearing the clothing item from the second image. Make it look natural and "
            "realistic with proper fit, lighting, and shadows. Generate a high-quality result image "
            "that maintains the person's pose and background while seamlessly integrating the clothing item."
        )

        if product_info:
            # Add specific product details to improve generation
            product_details = []
            if product_info.get("category"):
                product_details.append(f"clothing category: {product_info['category']}")
            if product_info.get("materials"):
                product_details.append(f"material: {', '.join(product_info['materials'][:2])}")
            if product_info.get("colors"):
                product_details.append(f"color: {', '.join(product_info['colors'][:2])}")

            if product_details:
                base_prompt += f" The clothing item is {', '.join(product_details)}."

        return base_prompt

    def _extract_image_from_response(self, response) -> Optional[bytes]:
        """Extract image data from Vertex AI response."""
        try:
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    if hasattr(part.inline_data, 'data'):
                                        image_data = part.inline_data.data

                                        # Handle different data types
                                        if isinstance(image_data, str):
                                            # Base64 string
                                            return base64.b64decode(image_data)
                                        elif isinstance(image_data, bytes):
                                            # Already bytes
                                            return image_data
                                        else:
                                            logger.warning(f"Unexpected image data type: {type(image_data)}")

            return None

        except Exception as e:
            logger.error(f"Failed to extract image from response: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if the virtual try-on service is healthy."""
        try:
            # Simple API connectivity test
            # Note: This doesn't actually call the model but verifies client setup
            return bool(self.client and self.api_key and self.project_id)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global instance for easy importing
virtual_tryon_service = VirtualTryOnService()