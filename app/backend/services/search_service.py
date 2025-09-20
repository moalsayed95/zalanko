"""
Improved Search Service for Zalanko.
Provides robust search functionality with proper error handling and logging.
"""

import asyncio
from typing import List, Dict, Any, Optional

from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from config.settings import settings
from utils.logger import get_logger
from exceptions import SearchError, ConfigurationError, ExternalServiceError


logger = get_logger(__name__)


class SearchService:
    """Enhanced search service with proper error handling and validation."""

    def __init__(self):
        """Initialize search service with configuration validation."""
        try:
            self._validate_configuration()
            self._initialize_clients()
            logger.info("SearchService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SearchService: {e}")
            raise ConfigurationError(f"SearchService initialization failed: {e}")

    def _validate_configuration(self) -> None:
        """Validate required configuration for search service."""
        if not settings.azure_search_service_name:
            raise ConfigurationError("Azure Search service name not configured")
        if not settings.azure_openai_endpoint:
            raise ConfigurationError("Azure OpenAI endpoint not configured")

    def _initialize_clients(self) -> None:
        """Initialize Azure clients."""
        # Azure Search client
        search_endpoint = f"https://{settings.azure_search_service_name}.search.windows.net"
        search_credential = AzureKeyCredential(settings.azure_search_api_key) if settings.azure_search_api_key else None

        if not search_credential:
            raise ConfigurationError("Azure Search credentials not found")

        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=settings.azure_search_index,
            credential=search_credential
        )

        # Azure OpenAI client for embeddings
        self.openai_client = AzureOpenAI(
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key
        )

    async def _calculate_embedding(self, text: str) -> List[float]:
        """
        Calculate embedding for given text with error handling.

        Args:
            text: Text to calculate embedding for

        Returns:
            List of embedding values

        Raises:
            ExternalServiceError: If embedding calculation fails
        """
        try:
            logger.debug(f"Calculating embedding for text: {text[:50]}...")
            response = self.openai_client.embeddings.create(
                input=text,
                model=settings.azure_openai_embedding_model
            )

            if not response.data:
                raise ExternalServiceError("Empty response from embedding service")

            embedding = response.data[0].embedding
            logger.debug(f"Successfully calculated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Failed to calculate embedding: {e}")
            raise ExternalServiceError(f"Embedding calculation failed: {e}")

    async def search_by_embedding(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search using vector embeddings with error handling.

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of search results

        Raises:
            SearchError: If search operation fails
        """
        try:
            logger.info(f"Performing embedding search for: '{query}' (k={k})")

            # Calculate embedding
            query_embedding = await self._calculate_embedding(query)

            # Create vector query
            vector_query = VectorizedQuery(
                kind="vector",
                vector=query_embedding,
                fields="embedding",
                k_nearest_neighbors=k,
                exhaustive=False
            )

            # Perform search
            results = await self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["id", "title", "description", "brand", "category", "price",
                       "sale_price", "on_sale", "colors", "sizes", "materials",
                       "style_tags", "ratings", "images", "availability"]
            )

            # Process results
            processed_results = []
            async for result in results:
                processed_results.append(dict(result))

            logger.info(f"Found {len(processed_results)} results for embedding search")
            return processed_results

        except Exception as e:
            logger.error(f"Embedding search failed: {e}")
            raise SearchError(f"Embedding search failed: {e}")

    async def search_by_filters(
        self,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        color: Optional[str] = None,
        on_sale: Optional[bool] = None,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search using filters with error handling.

        Args:
            brand: Filter by brand
            category: Filter by category
            max_price: Maximum price filter
            min_price: Minimum price filter
            color: Filter by color
            on_sale: Filter by sale status
            k: Maximum number of results

        Returns:
            List of filtered search results

        Raises:
            SearchError: If search operation fails
        """
        try:
            # Build filter expression
            filters = []
            if brand:
                filters.append(f"brand eq '{brand}'")
            if category:
                filters.append(f"category eq '{category}'")
            if max_price is not None:
                filters.append(f"price le {max_price}")
            if min_price is not None:
                filters.append(f"price ge {min_price}")
            if color:
                filters.append(f"colors/any(c: c eq '{color}')")
            if on_sale is not None:
                filters.append(f"on_sale eq {str(on_sale).lower()}")

            filter_expression = " and ".join(filters) if filters else None

            logger.info(f"Performing filtered search with filters: {filter_expression}")

            # Perform search
            results = await self.search_client.search(
                search_text="*",
                filter=filter_expression,
                top=k,
                select=["id", "title", "description", "brand", "category", "price",
                       "sale_price", "on_sale", "colors", "sizes", "materials",
                       "style_tags", "ratings", "images", "availability"]
            )

            # Process results
            processed_results = []
            async for result in results:
                processed_results.append(dict(result))

            logger.info(f"Found {len(processed_results)} results for filtered search")
            return processed_results

        except Exception as e:
            logger.error(f"Filtered search failed: {e}")
            raise SearchError(f"Filtered search failed: {e}")

    async def search_with_vector_and_filters(
        self,
        text_query: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        color: Optional[str] = None,
        on_sale: Optional[bool] = None,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector search and filters.

        Args:
            text_query: Text query for vector search
            Other args: Filter parameters
            k: Maximum number of results

        Returns:
            List of search results combining vector and filter search

        Raises:
            SearchError: If search operation fails
        """
        try:
            logger.info(f"Performing hybrid search: query='{text_query}', filters present")

            # If no text query, use filter search only
            if not text_query:
                return await self.search_by_filters(
                    brand=brand, category=category, max_price=max_price,
                    min_price=min_price, color=color, on_sale=on_sale, k=k
                )

            # Calculate embedding for text query
            query_embedding = await self._calculate_embedding(text_query)

            # Build filter expression
            filters = []
            if brand:
                filters.append(f"brand eq '{brand}'")
            if category:
                filters.append(f"category eq '{category}'")
            if max_price is not None:
                filters.append(f"price le {max_price}")
            if min_price is not None:
                filters.append(f"price ge {min_price}")
            if color:
                filters.append(f"colors/any(c: c eq '{color}')")
            if on_sale is not None:
                filters.append(f"on_sale eq {str(on_sale).lower()}")

            filter_expression = " and ".join(filters) if filters else None

            # Create vector query
            vector_query = VectorizedQuery(
                kind="vector",
                vector=query_embedding,
                fields="embedding",
                k_nearest_neighbors=k * 2,  # Get more results for filtering
                exhaustive=False
            )

            # Perform hybrid search
            results = await self.search_client.search(
                search_text=text_query,
                vector_queries=[vector_query],
                filter=filter_expression,
                top=k,
                select=["id", "title", "description", "brand", "category", "price",
                       "sale_price", "on_sale", "colors", "sizes", "materials",
                       "style_tags", "ratings", "images", "availability"]
            )

            # Process results
            processed_results = []
            async for result in results:
                processed_results.append(dict(result))

            logger.info(f"Found {len(processed_results)} results for hybrid search")
            return processed_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise SearchError(f"Hybrid search failed: {e}")

    async def close(self) -> None:
        """Close search client connections."""
        try:
            await self.search_client.close()
            logger.info("SearchService connections closed")
        except Exception as e:
            logger.error(f"Error closing SearchService: {e}")


# Singleton instance
search_service = SearchService()