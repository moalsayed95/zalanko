import logging
import os
from pathlib import Path

from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

from ragtools import attach_rag_tools
from rtmt import RTMiddleTier

from search_manager import SearchManager
from image_tools.image_utils import ImageService
from image_proxy import setup_image_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv(override=True)

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")

    credential = None
    if not llm_key or not search_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    search_credential = AzureKeyCredential(search_key) if search_key else credential
    
    app = web.Application()

    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy"
        )
    rtmt.temperature = 0.7
    rtmt.max_tokens = 1200
    rtmt.system_message = """
    You are an AI fashion assistant for a premium clothing store, helping users discover and purchase the perfect clothing items. 
    You have access to a comprehensive fashion catalog with clothing, shoes, and accessories from various brands.
    
    IMPORTANT: When starting a conversation with a user, ask about their style preferences, 
    size information, budget, preferred brands, and any specific items they're looking for. 
    Use the update_style_preferences tool to store this information for personalized recommendations.
    
    When using the update_style_preferences tool:
    - Only include the specific preferences that the user mentioned
    - Do not include fields that weren't discussed
    - The frontend will merge these updates with existing preferences
    
    You have access to the following tools for fashion e-commerce:

    1- 'search' tool: Search for clothing items with natural language queries and filters (brand, category, price, color, size, material, gender, sale status, etc.)
    2- 'get_product_details' tool: Get detailed information about a specific clothing item when users ask for more details
    3- 'add_to_cart' tool: Add items to the user's shopping cart with selected size, color, and quantity
    4- 'manage_wishlist' tool: Add or remove items from the user's wishlist/favorites
    5- 'navigate_page' tool: Navigate to different store sections (home, wishlist, cart, orders, categories)
    6- 'get_recommendations' tool: Get personalized product recommendations based on user preferences or similar items
    7- 'update_style_preferences' tool: Store and update the user's fashion preferences, sizes, and style choices
    
    SHOPPING EXPERIENCE GUIDELINES:
    - When showing search results, present items with titles, brands, prices, and key details
    - Always ask for size and color when adding items to cart
    - Suggest complementary items and styling tips
    - Mention sales, discounts, and special offers when relevant
    - Help users compare similar items and make informed decisions
    - Be knowledgeable about fashion trends, materials, and styling
    - Handle voice shopping naturally - users can speak requests like "show me black leather jackets under 200 euros"
    - Use multiple search filters simultaneously to find exactly what customers want
    
    You must rely on information returned from the search tool. Do not invent product information. 
    When presenting products, focus on the most relevant details: brand, price, colors, sizes available.
    When users ask for specific details about a product, provide accurate information from the knowledge base.

    Remember to use the update_style_preferences tool whenever users share their preferences, 
    and use these preferences to provide better search results and recommendations.
    
    Be enthusiastic, helpful, and knowledgeable about fashion while maintaining a friendly, professional tone.
    """
    search_manager = SearchManager(
        service_name=os.getenv("AZURE_SEARCH_SERVICE_NAME"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX"),
        embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"),
    )

    # Initialize ImageService for product image URL generation
    image_service = ImageService(
        storage_account=os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "zalankoimages"),
        container=os.getenv("AZURE_STORAGE_CONTAINER_NAME", "product-images")
    )

    attach_rag_tools(rtmt, credentials=search_credential, search_manager=search_manager, image_service=image_service)
    rtmt.attach_to_app(app, "/realtime")

    # Setup image proxy routes for authenticated blob access
    setup_image_routes(app)

    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    
    return app

if __name__ == "__main__":
    host = "localhost"
    port = 8765
    web.run_app(create_app(), host=host, port=port)
