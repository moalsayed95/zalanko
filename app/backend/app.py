"""
Improved Zalanko Backend Application.
Production-ready structure with proper error handling, logging, and configuration.
"""

from pathlib import Path
from aiohttp import web
from aiohttp_cors import setup as cors_setup, ResourceOptions
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential

from config.settings import settings
from utils.logger import setup_logging, get_logger, set_request_id
from exceptions import ConfigurationError
from ragtools import attach_rag_tools
from rtmt import RTMiddleTier
from search_manager import SearchManager
from image_tools.image_utils import ImageService
from image_proxy import setup_image_routes
from services.virtual_tryon_endpoint import setup_virtual_tryon_routes


# Setup logging first
setup_logging()
logger = get_logger(__name__)


async def create_app() -> web.Application:
    """
    Create and configure the aiohttp application.

    Returns:
        Configured aiohttp application

    Raises:
        ConfigurationError: If required configuration is missing
    """
    try:
        logger.info("Starting Zalanko backend application")

        # Create application with proper configuration
        app = web.Application(
            client_max_size=settings.max_request_size_mb * 1024 * 1024,
            middlewares=[request_logging_middleware, error_handling_middleware]
        )

        # Setup CORS
        _setup_cors(app)

        # Setup credentials
        llm_credential, search_credential = _setup_credentials()

        # Setup real-time middleware
        rtmt = _setup_rtmt(llm_credential)

        # Setup search manager and image service
        search_manager = _setup_search_manager()
        image_service = _setup_image_service()

        # Attach RAG tools
        attach_rag_tools(rtmt, credentials=search_credential,
                        search_manager=search_manager, image_service=image_service)
        rtmt.attach_to_app(app, "/realtime")

        # Setup routes
        _setup_routes(app)

        logger.info("Zalanko backend application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise ConfigurationError(f"Application creation failed: {e}")


def _setup_cors(app: web.Application) -> None:
    """Setup CORS configuration."""
    cors_setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    logger.debug("CORS configured")


def _setup_credentials() -> tuple:
    """Setup Azure credentials with fallback."""
    try:
        credential = None
        if not settings.azure_openai_api_key or not settings.azure_search_api_key:
            if settings.azure_tenant_id:
                logger.info("Using AzureDeveloperCliCredential with tenant_id")
                credential = AzureDeveloperCliCredential(
                    tenant_id=settings.azure_tenant_id, process_timeout=60
                )
            else:
                logger.info("Using DefaultAzureCredential")
                credential = DefaultAzureCredential()

        llm_credential = (AzureKeyCredential(settings.azure_openai_api_key)
                         if settings.azure_openai_api_key else credential)
        search_credential = (AzureKeyCredential(settings.azure_search_api_key)
                           if settings.azure_search_api_key else credential)

        logger.debug("Credentials configured successfully")
        return llm_credential, search_credential

    except Exception as e:
        logger.error(f"Failed to setup credentials: {e}")
        raise ConfigurationError(f"Credential setup failed: {e}")


def _setup_rtmt(llm_credential) -> RTMiddleTier:
    """Setup real-time middleware tier."""
    try:
        rtmt = RTMiddleTier(
            credentials=llm_credential,
            endpoint=settings.azure_openai_endpoint,
            deployment=settings.azure_openai_realtime_deployment,
            voice_choice=settings.azure_openai_voice_choice
        )

        # Configure RTMT parameters
        rtmt.temperature = 0.7
        rtmt.max_tokens = 1200
        rtmt.system_message = _get_system_message()

        logger.debug("RTMT configured successfully")
        return rtmt

    except Exception as e:
        logger.error(f"Failed to setup RTMT: {e}")
        raise ConfigurationError(f"RTMT setup failed: {e}")


def _setup_search_manager() -> SearchManager:
    """Setup search manager."""
    try:
        search_manager = SearchManager(
            service_name=settings.azure_search_service_name,
            api_key=settings.azure_search_api_key,
            index_name=settings.azure_search_index,
            embedding_model=settings.azure_openai_embedding_model,
        )
        logger.debug("SearchManager configured successfully")
        return search_manager

    except Exception as e:
        logger.error(f"Failed to setup SearchManager: {e}")
        raise ConfigurationError(f"SearchManager setup failed: {e}")


def _setup_image_service() -> ImageService:
    """Setup image service."""
    try:
        image_service = ImageService(
            storage_account=settings.azure_storage_account_name,
            container=settings.azure_storage_container_name
        )
        logger.debug("ImageService configured successfully")
        return image_service

    except Exception as e:
        logger.error(f"Failed to setup ImageService: {e}")
        raise ConfigurationError(f"ImageService setup failed: {e}")


def _setup_routes(app: web.Application) -> None:
    """Setup application routes."""
    try:
        # Setup image proxy routes
        setup_image_routes(app)

        # Setup virtual try-on routes
        setup_virtual_tryon_routes(app)

        # Setup static routes
        current_directory = Path(__file__).parent
        app.add_routes([
            web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))
        ])
        app.router.add_static('/', path=current_directory / 'static', name='static')

        logger.debug("Routes configured successfully")

    except Exception as e:
        logger.error(f"Failed to setup routes: {e}")
        raise ConfigurationError(f"Route setup failed: {e}")


def _get_system_message() -> str:
    """Get the system message for the AI assistant."""
    return """
    You are an AI fashion assistant called "Zalanko", your job is to help users discover and purchase the perfect clothing items.
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
    2- 'get_product_details' tool: **IMPORTANT** - This switches the main product view focus and gets details. Use when users refer to products in the suggestions like "what about that blue dress?", "tell me about the second option", "show me that Nike product", or "what about that one". Always use this when users ask about specific products from the current search results.
    3- 'add_to_cart' tool: Add items to the shopping cart. When users say "add this to cart" or "buy this item" while viewing a product, use this tool.
    4- 'manage_wishlist' tool: **CONTEXTUAL FAVORITES** - Add/remove items from wishlist. Use when users say "add this to favorites", "save this item", "I like this one" while discussing a specific product.
    5- 'navigate_page' tool: Navigate to different store sections (home, wishlist, cart, orders, categories)
    6- 'get_recommendations' tool: Get personalized product recommendations based on user preferences or similar items
    7- 'update_style_preferences' tool: Store and update the user's fashion preferences, sizes, and style choices
    8- 'virtual_try_on' tool: **VIRTUAL TRY-ON** - Generate virtual try-on images when users ask to "try on", "see how it looks on me", or "show me wearing this". If the user hasn't provided a photo, this will open the try-on modal for them to upload their image. This creates realistic visualizations of how clothing items would look on the user.

    SHOPPING EXPERIENCE GUIDELINES:
    - When showing search results, present items with titles, brands, prices, and key details
    - **PRODUCT SWITCHING**: When users ask about specific products from the search results (like "what about that red jacket?", "tell me about the third option", "show me that Zara dress"), ALWAYS use the get_product_details tool with the correct product ID to switch the main view focus to that item
    - **CONTEXTUAL ACTIONS**: When users say contextual phrases like "add this to favorites", "I like this one", "save this item", "add this to cart", or "buy this", use the currently highlighted/discussed product ID with the appropriate tool (manage_wishlist or add_to_cart)
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


@web.middleware
async def request_logging_middleware(request: web.Request, handler):
    """Middleware for request logging and tracing."""
    set_request_id()
    logger.info(f"Incoming {request.method} request to {request.path}")

    try:
        response = await handler(request)
        logger.info(f"Request completed with status {response.status}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise


@web.middleware
async def error_handling_middleware(request: web.Request, handler):
    """Middleware for global error handling."""
    try:
        return await handler(request)
    except web.HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting Zalanko backend server")

        host = "localhost"
        port = 8765

        # Validate configuration before starting
        _ = settings  # This will raise ConfigurationError if config is invalid

        web.run_app(create_app(), host=host, port=port)

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()