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
from prompts import FASHION_ASSISTANT_SYSTEM_MESSAGE
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
        rtmt.system_message = FASHION_ASSISTANT_SYSTEM_MESSAGE

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