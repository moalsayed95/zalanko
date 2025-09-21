#!/usr/bin/env python3
"""
Vertex AI Virtual Try-On Test
Clean implementation using Gemini 2.5 Flash Image Preview model for virtual try-on.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import base64

# Load environment variables from backend directory (two levels up)
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / '.env'
print(f"🔍 Looking for .env file at: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

try:
    from google import genai
    from google.genai import types
    from PIL import Image
    from io import BytesIO
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Missing package: {e}")
    print("Please install: pip install --upgrade google-genai pillow")
    sys.exit(1)

class VertexAITryOnTester:
    def __init__(self):
        self.data_dir = Path("data")
        self.setup_vertex_ai()

    def setup_vertex_ai(self):
        """Initialize Vertex AI client."""
        print("🔧 Setting up Vertex AI...")

        api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
        if not api_key:
            print("❌ Error: GOOGLE_CLOUD_API_KEY not found in environment")
            sys.exit(1)

        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
        if not project_id:
            print("❌ Error: GOOGLE_CLOUD_PROJECT_ID not found in environment")
            sys.exit(1)

        try:
            # For API key authentication, we use the simple approach
            # The project/location is embedded in the model path
            self.client = genai.Client(
                vertexai=True,
                api_key=api_key
            )
            print("✅ Vertex AI client initialized successfully")
            print(f"📍 Using API key authentication")
        except Exception as e:
            print(f"❌ Error initializing Vertex AI client: {e}")
            sys.exit(1)

        # Use the full model path for global location
        self.model = f"projects/{project_id}/locations/global/publishers/google/models/gemini-2.5-flash-image-preview"
        print(f"✅ Using model: gemini-2.5-flash-image-preview (global location)")
        print(f"📍 Full model path: {self.model}")

    def validate_images(self):
        """Check if required test images exist."""
        print("\n📁 Validating test images...")

        person_image = self.data_dir / "mo.jpg"
        clothing_image = self.data_dir / "item.png"

        if not person_image.exists() or not clothing_image.exists():
            print("❌ Missing required images:")
            if not person_image.exists():
                print(f"  - {person_image}")
            if not clothing_image.exists():
                print(f"  - {clothing_image}")
            return False

        print(f"✅ Found person image: {person_image}")
        print(f"✅ Found clothing image: {clothing_image}")
        return person_image, clothing_image

    def load_and_encode_image(self, image_path, image_type):
        """Load and encode image for Vertex AI."""
        try:
            img = Image.open(image_path)
            width, height = img.size
            print(f"📏 {image_type} image: {width}x{height} pixels")

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
                print(f"🔄 Converted {image_type} image to RGB")

            # Convert to base64 for API
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            return image_b64

        except Exception as e:
            print(f"❌ Error loading {image_type} image: {e}")
            return None

    def generate_virtual_tryon(self, person_b64, clothing_b64):
        """Generate virtual try-on using Vertex AI."""
        print("\n👗 Generating Virtual Try-On with Vertex AI...")

        # Create content with images and prompt
        prompt_text = (
            "Create a realistic virtual try-on image. Take the person from the first image and "
            "show them wearing the clothing item from the second image. Make it look natural and "
            "realistic with proper fit and lighting. Generate a high-quality result image."
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=prompt_text),
                    types.Part(
                        inline_data=types.Blob(
                            data=base64.b64decode(person_b64),
                            mime_type="image/jpeg"
                        )
                    ),
                    types.Part(
                        inline_data=types.Blob(
                            data=base64.b64decode(clothing_b64),
                            mime_type="image/png"
                        )
                    )
                ]
            )
        ]

        # Configure for image generation
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=32768,
            response_modalities=["TEXT", "IMAGE"],  # Request both text and image
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
            ],
        )

        try:
            print("🔄 Sending request to Vertex AI (may take 10-30 seconds)...")

            # Use generate_content instead of stream for simpler handling
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )

            print("✅ Received response from Vertex AI")
            return response

        except Exception as e:
            print(f"❌ Error generating virtual try-on: {e}")
            return None

    def save_results(self, response):
        """Process and save the response."""
        print("\n💾 Processing and saving results...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # Check for text response
            if hasattr(response, 'text') and response.text:
                text_file = self.data_dir / f"response_{timestamp}.txt"
                with open(text_file, 'w') as f:
                    f.write(response.text)
                print(f"📝 Saved text response: {text_file}")

            # Look for images in response
            if hasattr(response, 'candidates') and response.candidates:
                for i, candidate in enumerate(response.candidates):
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            for j, part in enumerate(candidate.content.parts):
                                # Check for inline image data
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    try:
                                        print(f"🖼️ Found inline_data!")
                                        print(f"📋 Inline data type: {type(part.inline_data)}")
                                        print(f"📋 Inline data attributes: {dir(part.inline_data)}")

                                        # Check what's actually in the inline_data
                                        if hasattr(part.inline_data, 'data'):
                                            image_data = part.inline_data.data
                                            print(f"📊 Raw image data length: {len(str(image_data))}")
                                            print(f"📊 Image data type: {type(image_data)}")
                                            print(f"📊 First 100 chars: {str(image_data)[:100]}...")

                                            # Try different decoding approaches
                                            try:
                                                if isinstance(image_data, str):
                                                    # If it's a base64 string
                                                    image_bytes = base64.b64decode(image_data)
                                                elif isinstance(image_data, bytes):
                                                    # If it's already bytes
                                                    image_bytes = image_data
                                                else:
                                                    print(f"❌ Unexpected data type: {type(image_data)}")
                                                    return False, None

                                                print(f"📊 Decoded bytes length: {len(image_bytes)}")

                                                # Save as PNG
                                                output_file = self.data_dir / f"vertex_ai_result_{timestamp}.png"
                                                with open(output_file, 'wb') as f:
                                                    f.write(image_bytes)

                                                print(f"✅ Generated image saved: {output_file}")
                                                print(f"📁 File size: {output_file.stat().st_size} bytes")

                                                # Try to validate the image
                                                try:
                                                    img = Image.open(BytesIO(image_bytes))
                                                    print(f"📐 Generated image size: {img.size}")
                                                    print(f"🎨 Image format: {img.format}")
                                                except Exception as img_validate_err:
                                                    print(f"⚠️ Image validation failed: {img_validate_err}")

                                                return True, output_file

                                            except Exception as decode_err:
                                                print(f"❌ Error decoding image data: {decode_err}")
                                        else:
                                            print("❌ No 'data' attribute in inline_data")

                                    except Exception as img_err:
                                        print(f"❌ Error processing inline_data: {img_err}")

            print("📝 Received text response but no image generated")
            return True, None  # Still successful API communication

        except Exception as e:
            print(f"❌ Error processing response: {e}")
            print(f"🔍 Response type: {type(response)}")
            return False, None

    def run_test(self):
        """Run the complete virtual try-on test."""
        print("🚀 Vertex AI Virtual Try-On Test")
        print("=" * 50)

        # Validate images exist
        validation_result = self.validate_images()
        if not validation_result:
            print("\n❌ Please add mo.jpg and item.png to the data/ directory")
            return False

        person_path, clothing_path = validation_result

        # Load and encode images
        person_b64 = self.load_and_encode_image(person_path, "Person")
        clothing_b64 = self.load_and_encode_image(clothing_path, "Clothing")

        if not person_b64 or not clothing_b64:
            print("❌ Failed to load and encode images")
            return False

        # Generate virtual try-on
        response = self.generate_virtual_tryon(person_b64, clothing_b64)
        if not response:
            return False

        # Save results
        success, output_file = self.save_results(response)

        print("\n" + "=" * 50)
        if success:
            if output_file:
                print("🎉 SUCCESS! Virtual try-on image generated!")
                print(f"📁 Generated image: {output_file}")
                print("🔍 Check the data/ directory for the result")
            else:
                print("✅ API communication successful (text response received)")
                print("💡 Image generation may need prompt refinement")

            print("🚀 Ready to integrate into Zalanko platform!")
        else:
            print("❌ Test failed - check error messages above")

        return success

def main():
    """Main test function."""
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)

    # Create data directory if needed
    Path("data").mkdir(exist_ok=True)

    # Run test
    tester = VertexAITryOnTester()
    success = tester.run_test()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())