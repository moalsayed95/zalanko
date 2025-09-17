from typing import Any
import base64
import time
from datetime import datetime
import aiohttp

from search_manager import SearchManager
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from rtmt import RTMiddleTier, Tool, ToolResult, ToolResultDirection
from virtual_tryon_service import virtual_tryon_service

async def fetch_image_from_url(url: str) -> bytes:
    """Fetch image data from URL."""
    session = None
    try:
        print(f"🌐 Fetching image from: {url}")
        session = aiohttp.ClientSession()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                image_data = await response.read()
                print(f"✅ Successfully fetched {len(image_data)} bytes from {url}")
                return image_data
            else:
                print(f"❌ Failed to fetch image: HTTP {response.status}")
                raise Exception(f"HTTP {response.status}")
    except Exception as e:
        print(f"❌ Error fetching image from {url}: {e}")
        raise
    finally:
        if session:
            await session.close()

_search_tool_schema = {
    "type": "function",
    "name": "search",
    "description": "Search for clothing items in the fashion catalog. Use this to find products based on style descriptions, brands, categories, or specific features.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query for clothing items (e.g., 'black leather jacket', 'summer dresses', 'Nike sneakers')"
            },
            "filters": {
                "type": "object",
                "properties": {
                    "brand": {"type": "string", "description": "Filter by brand (e.g., 'Nike', 'Zara')"},
                    "category": {"type": "string", "description": "Filter by category (e.g., 'T-Shirts & Tops', 'Outerwear')"},
                    "gender": {"type": "string", "description": "Filter by gender (men, women, unisex)"},
                    "max_price": {"type": "number", "description": "Maximum price filter"},
                    "min_price": {"type": "number", "description": "Minimum price filter"},
                    "color": {"type": "string", "description": "Filter by color"},
                    "size": {"type": "string", "description": "Filter by size"},
                    "material": {"type": "string", "description": "Filter by material (e.g., 'Cotton', 'Polyester', 'Leather')"},
                    "on_sale": {"type": "boolean", "description": "Filter for items on sale"}
                }
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

_get_product_details_schema = {
    "type": "function",
    "name": "get_product_details",
    "description": "Switch focus to and get detailed information about a specific clothing item. Use when user asks about 'that product', 'the blue one', 'the second option', or wants to see details of a specific product from the suggestions.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to focus on and get details for (e.g., 'CLO001', 'CLO005')"
            }
        },
        "required": ["product_id"],
        "additionalProperties": False
    }
}

_add_to_cart_schema = {
    "type": "function",
    "name": "add_to_cart",
    "description": "Add a clothing item to the shopping cart with specified size and color. Use when users say 'add this to cart', 'buy this item', 'I want to purchase this', or similar phrases about the currently discussed product.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to add to cart"
            },
            "size": {
                "type": "string",
                "description": "Selected size for the item"
            },
            "color": {
                "type": "string",
                "description": "Selected color for the item"
            },
            "quantity": {
                "type": "integer",
                "description": "Quantity to add (default: 1)",
                "default": 1
            }
        },
        "required": ["product_id", "size", "color"],
        "additionalProperties": False
    }
}


_manage_wishlist_schema = {
    "type": "function",
    "name": "manage_wishlist",
    "description": "Add or remove a clothing item from the user's wishlist/favorites. Use when users say contextual phrases like 'add this to favorites', 'save this item', 'I like this one', or 'remove from favorites' about the currently discussed product.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to add or remove from wishlist"
            },
            "action": {
                "type": "string",
                "description": "Either 'add' or 'remove'",
                "enum": ["add", "remove"]
            }
        },
        "required": ["product_id", "action"],
        "additionalProperties": False
    }
}


_navigate_page_schema = {
    "type": "function",
    "name": "navigate_page",
    "description": "Navigate to different pages in the fashion store",
    "parameters": {
        "type": "object",
        "properties": {
            "page": {
                "type": "string",
                "description": "The page to navigate to",
                "enum": ["home", "wishlist", "cart", "orders", "profile", "categories"]
            },
            "category": {
                "type": "string",
                "description": "Specific category to navigate to (when page is 'categories')"
            }
        },
        "required": ["page"],
        "additionalProperties": False
    }
}

_get_recommendations_schema = {
    "type": "function",
    "name": "get_recommendations",
    "description": "Get personalized clothing recommendations based on user preferences or similar items",
    "parameters": {
        "type": "object",
        "properties": {
            "based_on_product_id": {
                "type": "string",
                "description": "Get recommendations based on a specific product (optional)"
            },
            "style_preference": {
                "type": "string",
                "description": "Style preference for recommendations (e.g., 'casual', 'formal', 'sporty')"
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price for recommendations"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_update_style_preferences_schema = {
    "type": "function",
    "name": "update_style_preferences",
    "description": "Update the user's fashion and style preferences. Only include fields that were specifically mentioned by the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "budget": {
                "type": "object",
                "properties": {
                    "min": {"type": "number"},
                    "max": {"type": "number"}
                }
            },
            "preferred_brands": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of preferred fashion brands"
            },
            "sizes": {
                "type": "object",
                "properties": {
                    "tops": {"type": "string"},
                    "bottoms": {"type": "string"},
                    "shoes": {"type": "string"},
                    "dresses": {"type": "string"}
                }
            },
            "style_preferences": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Style preferences (e.g., 'casual', 'formal', 'sporty', 'minimalist')"
            },
            "preferred_colors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Preferred colors"
            },
            "avoided_materials": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Materials to avoid (e.g., 'wool', 'silk')"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_virtual_try_on_schema = {
    "type": "function",
    "name": "virtual_try_on",
    "description": "Generate a virtual try-on image showing how a clothing item would look on the user. Use when users ask to 'try on', 'see how it looks on me', or 'visualize wearing' a specific product.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to try on (from current search results or highlighted product)"
            },
            "person_image_base64": {
                "type": "string",
                "description": "Base64 encoded image of the person (user's photo). Optional - if not provided, will open try-on modal for user to upload photo."
            },
            "user_message": {
                "type": "string",
                "description": "Optional message about how the user wants to see the item (e.g., 'show me in casual setting')"
            }
        },
        "required": ["product_id"],
        "additionalProperties": False
    }
}

async def _search_tool(
    search_manager, 
    image_service,
    args: Any
) -> ToolResult:
    query = args['query']
    filters = args.get('filters', {})

    print(f"🔍 SEARCH: Looking for '{query}' with filters: {filters}")
    
    # Use filters if provided, otherwise just do vector search
    if filters:
        results = await search_manager.search_with_vector_and_filters(
            text_query=query,
            k=10,
            brand=filters.get('brand'),
            category=filters.get('category'),
            gender=filters.get('gender'),
            max_price=filters.get('max_price'),
            min_price=filters.get('min_price'),
            color=filters.get('color'),
            size=filters.get('size'),
            material=filters.get('material'),
            on_sale=filters.get('on_sale')
        )
    else:
        results = await search_manager.search_by_embedding(query, k=10)

    products = []
    for r in results:
        product = {
            "id": r.get("id", "unknown_id"),
            "title": r.get("title", ""),
            "description": r.get("description", ""),
            "brand": r.get("brand", ""),
            "category": r.get("category", ""),
            "price": r.get("price", 0.0),
            "sale_price": r.get("sale_price"),
            "on_sale": r.get("on_sale", False),
            "colors": r.get("colors", []),
            "sizes": r.get("sizes", []),
            "materials": r.get("materials", []),
            "style_tags": r.get("style_tags", []),
            "ratings": r.get("ratings", {}),
            "images": r.get("images", []),
            "availability": r.get("availability", "")
        }
        
        # Enhance product with image URLs if image_service is available
        if image_service:
            product = image_service.enhance_product_with_images(product)
        
        products.append(product)

    # Log the product IDs that are available for switching
    product_ids = [p['id'] for p in products]
    print(f"📦 SEARCH RESULTS: Found {len(products)} products: {product_ids}")

    return ToolResult({"products": products}, ToolResultDirection.TO_CLIENT)


async def _get_product_details_tool(
    args: Any
) -> ToolResult:
    product_id = args['product_id']
    print(f"🔄 PRODUCT SWITCH: User asked for details on product {product_id}")

    # Return the product ID in the format that triggers frontend highlighting
    result = {"id": product_id}
    print(f"✅ TOOL RESPONSE: Switching main view to product {product_id}")
    return ToolResult(result, ToolResultDirection.TO_CLIENT)

async def _add_to_cart_tool( 
    args: Any
) -> ToolResult:
    return ToolResult({
        "action": "add_to_cart",
        "product_id": args['product_id'],
        "size": args['size'],
        "color": args['color'],
        "quantity": args.get('quantity', 1)
    }, ToolResultDirection.TO_CLIENT)

async def _manage_wishlist_tool(args: Any) -> ToolResult:
    product_id = args['product_id']
    action = args['action']

    print(f"💖 WISHLIST ACTION: {action} product {product_id}")

    # Return the product ID in the format frontend expects for favorites
    result = {"favorite_id": product_id}
    print(f"✅ WISHLIST RESPONSE: {result}")

    return ToolResult(result, ToolResultDirection.TO_CLIENT)


async def _navigate_page_tool(args: Any) -> ToolResult:
    # Return the requested page to navigate to
    return ToolResult({"navigate_to": args['page']}, ToolResultDirection.TO_CLIENT)

async def _get_recommendations_tool(args: Any) -> ToolResult:
    return ToolResult({
        "action": "get_recommendations",
        "based_on_product_id": args.get('based_on_product_id'),
        "style_preference": args.get('style_preference'),
        "max_price": args.get('max_price')
    }, ToolResultDirection.TO_CLIENT)

async def _update_style_preferences_tool(args: Any) -> ToolResult:
    return ToolResult({
        "action": "update_style_preferences",
        "preferences": args
    }, ToolResultDirection.TO_CLIENT)

async def _virtual_try_on_tool(
    search_manager,
    image_service,
    args: Any
) -> ToolResult:
    product_id = args['product_id']
    person_image_base64 = args.get('person_image_base64', None)
    user_message = args.get('user_message', '')

    print(f"🎬 === VIRTUAL TRY-ON STARTED ===")
    print(f"👗 Product ID: {product_id}")
    print(f"📸 Person image provided: {person_image_base64 is not None}")
    if person_image_base64:
        print(f"📸 Person image data length: {len(person_image_base64)} characters")
    print(f"💬 User message: {user_message}")

    try:
        # Step 1: Get product details for enhanced prompting
        print(f"🔍 Step 1: Searching for product {product_id}")
        results = await search_manager.search_by_filters()
        print(f"📋 Found {len(results)} total products in database")

        product_info = None
        product_result = None

        # Find the specific product
        for i, result in enumerate(results):
            if result.get("id") == product_id:
                product_info = {
                    "title": result.get("title", ""),
                    "category": result.get("category", ""),
                    "materials": result.get("materials", []),
                    "colors": result.get("colors", []),
                    "brand": result.get("brand", "")
                }
                product_result = result
                print(f"✅ Found product at index {i}: {product_info['title']}")
                break

        if not product_info:
            print(f"❌ ERROR: Product {product_id} not found in {len(results)} products")
            # Log first few product IDs for debugging
            sample_ids = [r.get("id", "no-id") for r in results[:5]]
            print(f"🔍 Sample product IDs: {sample_ids}")

            return ToolResult({
                "action": "virtual_try_on_error",
                "error": f"Product {product_id} not found in catalog"
            }, ToolResultDirection.TO_CLIENT)

        # Step 2: Handle person image
        print(f"🧑 Step 2: Processing person image")

        # If no person image provided, open the try-on modal
        if not person_image_base64:
            print(f"📱 No person image provided - opening try-on modal")
            return ToolResult({
                "action": "open_virtual_try_on_modal",
                "product_id": product_id,
                "product_info": product_info,
                "message": f"I'll open the virtual try-on for {product_info.get('title', 'this item')}. Please upload your photo to see how it looks on you!"
            }, ToolResultDirection.TO_CLIENT)

        try:
            person_image_bytes = base64.b64decode(person_image_base64)
            print(f"✅ Successfully decoded person image: {len(person_image_bytes)} bytes")
        except Exception as e:
            print(f"❌ ERROR: Failed to decode person image: {e}")
            return ToolResult({
                "action": "virtual_try_on_error",
                "error": "Invalid person image data"
            }, ToolResultDirection.TO_CLIENT)

        # Step 3: Handle clothing image
        print(f"👔 Step 3: Processing clothing image")
        clothing_image_bytes = None

        if product_result and product_result.get("images"):
            product_images = product_result["images"]
            print(f"📸 Product has {len(product_images)} images: {product_images[:3]}")

            # Try to fetch the first product image
            if image_service and len(product_images) > 0:
                print(f"🔗 Attempting to fetch clothing image via image_service")
                try:
                    # Get the first image URL
                    image_urls = image_service.get_image_urls(product_id, [product_images[0]])
                    if image_urls and len(image_urls) > 0:
                        image_url = image_urls[0]
                        print(f"🌐 Got image URL: {image_url}")

                        # Fetch the actual image data
                        try:
                            clothing_image_bytes = await fetch_image_from_url(image_url)
                            print(f"✅ Successfully fetched clothing image: {len(clothing_image_bytes)} bytes")
                        except Exception as fetch_error:
                            print(f"❌ Failed to fetch clothing image: {fetch_error}")
                    else:
                        print(f"❌ No image URLs generated for product {product_id}")
                except Exception as img_error:
                    print(f"❌ Error getting image URL: {img_error}")

        if not clothing_image_bytes:
            print(f"⚠️ No clothing image available - returning request for manual upload")
            return ToolResult({
                "action": "virtual_try_on_request",
                "product_id": product_id,
                "product_info": product_info,
                "needs_clothing_image": True,
                "message": f"I need the clothing image for {product_info.get('title', 'this item')} to generate your virtual try-on. The product image couldn't be automatically fetched."
            }, ToolResultDirection.TO_CLIENT)

        # Step 4: Generate virtual try-on (when we have both images)
        print(f"🎨 Step 4: Generating virtual try-on with Vertex AI")
        try:
            success, result_image, error_msg = await virtual_tryon_service.generate_virtual_tryon(
                person_image_bytes,
                clothing_image_bytes,
                product_info
            )

            if success and result_image:
                print(f"🎉 Virtual try-on generation successful: {len(result_image)} bytes")

                # Step 5: Save result to local storage
                result_filename = f"tryon_{product_id}_{int(time.time())}.png"

                # Create results directory if it doesn't exist
                from pathlib import Path
                results_dir = Path("virtual_tryon_results")
                results_dir.mkdir(exist_ok=True)

                # Save the image file
                result_path = results_dir / result_filename
                with open(result_path, "wb") as f:
                    f.write(result_image)

                print(f"💾 Saved result image: {result_path} ({len(result_image)} bytes)")

                # Return the URL to access the saved image
                result_url = f"/api/virtual-tryon-results/{result_filename}"

                return ToolResult({
                    "action": "virtual_try_on_result",
                    "product_id": product_id,
                    "image_url": result_url,
                    "timestamp": datetime.now().isoformat()
                }, ToolResultDirection.TO_CLIENT)
            else:
                print(f"❌ Virtual try-on generation failed: {error_msg}")
                return ToolResult({
                    "action": "virtual_try_on_error",
                    "error": f"Generation failed: {error_msg}"
                }, ToolResultDirection.TO_CLIENT)

        except Exception as gen_error:
            print(f"❌ Exception during generation: {gen_error}")
            return ToolResult({
                "action": "virtual_try_on_error",
                "error": f"Generation exception: {str(gen_error)}"
            }, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        print(f"❌ VIRTUAL TRY-ON FAILED with exception: {e}")
        import traceback
        print(f"📚 Full traceback: {traceback.format_exc()}")
        return ToolResult({
            "action": "virtual_try_on_error",
            "error": f"Virtual try-on failed: {str(e)}"
        }, ToolResultDirection.TO_CLIENT)
    finally:
        print(f"🎬 === VIRTUAL TRY-ON ENDED ===")


def attach_rag_tools(rtmt: RTMiddleTier,
    credentials: AzureKeyCredential | DefaultAzureCredential,
    search_manager: SearchManager, 
    image_service = None
    ) -> None:
    
    if not isinstance(credentials, AzureKeyCredential):
        credentials.get_token("https://search.azure.com/.default") # warm this up before we start getting requests

    rtmt.tools["search"] = Tool(
        schema=_search_tool_schema, 
        target=lambda args: _search_tool(search_manager, image_service, args)
    )

    rtmt.tools["get_product_details"] = Tool(
        schema=_get_product_details_schema, 
        target=lambda args: _get_product_details_tool(args)
    )

    rtmt.tools["add_to_cart"] = Tool(
        schema=_add_to_cart_schema, 
        target=lambda args: _add_to_cart_tool(args)
    )

    rtmt.tools["manage_wishlist"] = Tool(
        schema=_manage_wishlist_schema,
        target=lambda args: _manage_wishlist_tool(args)
    )

    rtmt.tools["navigate_page"] = Tool(
        schema=_navigate_page_schema,
        target=lambda args: _navigate_page_tool(args)
    )

    rtmt.tools["get_recommendations"] = Tool(
        schema=_get_recommendations_schema,
        target=lambda args: _get_recommendations_tool(args)
    )

    rtmt.tools["update_style_preferences"] = Tool(
        schema=_update_style_preferences_schema,
        target=lambda args: _update_style_preferences_tool(args)
    )

    rtmt.tools["virtual_try_on"] = Tool(
        schema=_virtual_try_on_schema,
        target=lambda args: _virtual_try_on_tool(search_manager, image_service, args)
    )