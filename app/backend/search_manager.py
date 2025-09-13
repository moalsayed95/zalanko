import os
import dotenv
import asyncio
from typing import List, Dict, Any, Optional

from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

dotenv.load_dotenv(override=True)

class SearchManager:
    def __init__(
        self,
        service_name: str,
        api_key: str,
        index_name: str,
        embedding_model: str,
    ):
        self.index_name = index_name
        self.embedding_model = embedding_model
        self.azure_search_endpoint = f"https://{service_name}.search.windows.net"
        self.azure_search_credential = AzureKeyCredential(api_key)

        self.search_client = SearchClient(
            endpoint=self.azure_search_endpoint,
            index_name=self.index_name,
            credential=self.azure_search_credential
        )

        self.azure_openai_client = AzureOpenAI(
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )

    def _calculate_embedding(self, text: str) -> List[float]:
        response = self.azure_openai_client.embeddings.create(input=text, model=self.embedding_model)
        return response.data[0].embedding

    async def search_by_embedding(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self._calculate_embedding(query)
        vector_query = VectorizedQuery(
            kind="vector",
            vector=query_embedding,
            fields="embedding",
            k_nearest_neighbors=k,
            exhaustive=False
        )

        results = await self.search_client.search(vector_queries=[vector_query])
        output = []
        async for page in results.by_page():
            async for doc in page:
                output.append(doc)
        return output

    async def search_by_filters(
        self,
        # Fashion-specific filters
        brand: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        gender: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        material: Optional[str] = None,
        on_sale: Optional[bool] = None,
        season: Optional[str] = None,
        # Legacy filters for backward compatibility
        location: Optional[str] = None,
        min_rooms: Optional[int] = None,
        furnished: Optional[bool] = None,
        pet_friendly: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        # Construct OData filter string
        filters = []
        
        # Fashion-specific filters
        if brand:
            filters.append(f"brand eq '{brand}'")
        if category:
            filters.append(f"category eq '{category}'")
        if subcategory:
            filters.append(f"subcategory eq '{subcategory}'")
        if gender:
            filters.append(f"gender eq '{gender}'")
        if max_price is not None:
            filters.append(f"price le {max_price}")
        if min_price is not None:
            filters.append(f"price ge {min_price}")
        if color:
            filters.append(f"colors/any(c: c eq '{color}')")
        if size:
            filters.append(f"sizes/any(s: s eq '{size}')")
        if material:
            # Use search.ismatch with proper field specification
            filters.append(f"search.ismatch('{material}', 'materials')")
        if on_sale is not None:
            filters.append(f"on_sale eq {str(on_sale).lower()}")
        if season:
            filters.append(f"season eq '{season}'")
            
        # Legacy filters for backward compatibility
        if location:
            filters.append(f"search.in(location, '{location}', ',')")
        if min_rooms is not None:
            filters.append(f"rooms ge {min_rooms}")
        if furnished is not None:
            filters.append(f"furnished eq {str(furnished).lower()}")
        if pet_friendly is not None:
            filters.append(f"pet_friendly eq {str(pet_friendly).lower()}")

        filter_str = " and ".join(filters) if filters else None

        results = await self.search_client.search(
            search_text="",
            filter=filter_str,
            query_type="simple",
            top=50
        )
        output = []
        async for page in results.by_page():
            async for doc in page:
                output.append(doc)
        return output

    async def search_with_vector_and_filters(
        self,
        text_query: str,
        k: int = 3,
        # Fashion filters
        brand: Optional[str] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        material: Optional[str] = None,
        on_sale: Optional[bool] = None,
        # Legacy filters
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query_embedding = self._calculate_embedding(text_query)
        # Construct OData filter string
        filters = []
        
        # Fashion filters
        if brand:
            filters.append(f"brand eq '{brand}'")
        if category:
            filters.append(f"category eq '{category}'")
        if gender:
            filters.append(f"gender eq '{gender}'")
        if max_price is not None:
            filters.append(f"price le {max_price}")
        if min_price is not None:
            filters.append(f"price ge {min_price}")
        if color:
            filters.append(f"colors/any(c: c eq '{color}')")
        if size:
            filters.append(f"sizes/any(s: s eq '{size}')")
        if material:
            filters.append(f"search.ismatch('{material}', 'materials')")
        if on_sale is not None:
            filters.append(f"on_sale eq {str(on_sale).lower()}")
            
        # Legacy filters
        if location:
            filters.append(f"location eq '{location}'")

        filter_str = " and ".join(filters) if filters else None

        vector_query = VectorizedQuery(
            kind="vector",
            vector=query_embedding,
            fields="embedding",
            k_nearest_neighbors=k
        )

        results = await self.search_client.search(
            vector_queries=[vector_query],
            filter=filter_str,
            vector_filter_mode="preFilter"
        )
        output = []
        async for page in results.by_page():
            async for doc in page:
                output.append(doc)
        return output

    async def close(self):
        """Close the Azure Search client and clean up resources"""
        if hasattr(self, 'search_client'):
            await self.search_client.close()

if __name__ == "__main__":

    search_manager = SearchManager(
        service_name=os.getenv("AZURE_SEARCH_SERVICE_NAME"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX"),
        embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
    )

    # search by embedding
    # results = asyncio.run(search_manager.search_by_embedding("stlyiii", k=5))
    # for r in results:
    #     print("---------------------------------------------")
    #     print(f"Title: {r['title']}")
    #     print(f"Description: {r['description']}")
    #     print(f"Location: {r['location']}")

    # example of search by filters - fashion
    results = asyncio.run(search_manager.search_by_filters(brand="Nike", category="Sportswear", max_price=100.0))
    for r in results:
        print("---------------------------------------------")
        print(f"Title: {r['title']}")
        print(f"Description: {r['description']}")
        print(f"Brand: {r['brand']}")
        print(f"Price: €{r['price']}")

