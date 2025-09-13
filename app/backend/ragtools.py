from typing import Any

from search_manager import SearchManager
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from rtmt import RTMiddleTier, Tool, ToolResult, ToolResultDirection

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
    "description": "Get detailed information about a specific clothing item when user asks for more details about a product",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to get details for"
            }
        },
        "required": ["product_id"],
        "additionalProperties": False
    }
}

_add_to_cart_schema = {
    "type": "function",
    "name": "add_to_cart",
    "description": "Add a clothing item to the shopping cart with specified size and color",
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
    "description": "Add or remove a clothing item from the user's wishlist",
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

async def _search_tool(
    search_manager, 
    image_service,
    args: Any
) -> ToolResult:
    query = args['query']
    filters = args.get('filters', {})
    
    print(f"Searching for '{query}' with filters: {filters}")
    
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

    return ToolResult({"products": products}, ToolResultDirection.TO_CLIENT)


async def _get_product_details_tool( 
    args: Any
) -> ToolResult:
    return ToolResult({"product_id": args['product_id']}, ToolResultDirection.TO_CLIENT)

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
    return ToolResult({
        "action": "manage_wishlist",
        "product_id": args['product_id'],
        "wishlist_action": args['action']
    }, ToolResultDirection.TO_CLIENT)


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