# Zalanko Backend - Fashion E-commerce AI Server

This document provides a comprehensive overview of the Zalanko backend architecture, explaining how each component works and how they interact to create an AI-powered fashion e-commerce platform.

## 📁 Architecture Overview

The backend is built with Python using aiohttp for async HTTP handling and integrates deeply with Azure AI services. It serves as a middleware between the React frontend and Azure services, providing real-time voice interaction, search capabilities, and image serving.

```
app/backend/
├── app.py                    # Main application server
├── rtmt.py                   # Real-time middle tier (WebSocket proxy)
├── ragtools.py               # RAG tools for fashion search
├── search_manager.py         # Azure AI Search integration
├── index_manager.py          # Search index creation and data loading
├── image_proxy.py            # Authenticated image serving
├── image_tools/              # Image management utilities
│   ├── image_utils.py        # Image URL generation service
│   └── ...                   # Additional image tools
├── setup_intvect.py          # Legacy integrated vectorization setup
└── tests/                    # Integration tests
```

## 🚀 Core Components

### 1. `app.py` - Main Application Server

**Purpose**: Entry point for the entire backend application, sets up the aiohttp server with all necessary services.

**Key Responsibilities**:
- **Server Setup**: Creates aiohttp web application with WebSocket support
- **Authentication**: Configures Azure credentials (Key or DefaultAzureCredential)
- **Service Initialization**: Sets up SearchManager, ImageService, and RTMiddleTier
- **Environment Configuration**: Loads environment variables and handles dev/prod modes
- **Route Registration**: Registers static file serving and image proxy routes

**Key Features**:
```python
# Azure AI integration
rtmt = RTMiddleTier(
    credentials=llm_credential,
    endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
    voice_choice="alloy"
)

# Fashion-specific system message
rtmt.system_message = """
You are an AI fashion assistant for a premium clothing store...
"""

# Search integration
search_manager = SearchManager(
    service_name=os.getenv("AZURE_SEARCH_SERVICE_NAME"),
    api_key=os.getenv("AZURE_SEARCH_API_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
)
```

**Endpoints**:
- `/realtime` - WebSocket endpoint for real-time AI conversation
- `/api/images/{product_id}/{filename}` - Authenticated image serving
- `/` - Static file serving for frontend

### 2. `rtmt.py` - Real-Time Middle Tier

**Purpose**: WebSocket proxy that bridges the frontend and Azure OpenAI's realtime API, enabling server-side tool integration.

**Key Responsibilities**:
- **WebSocket Proxying**: Forwards messages between client and Azure OpenAI realtime endpoint
- **Tool Call Processing**: Handles server-side RAG tool executions
- **Message Filtering**: Processes and modifies messages before forwarding
- **Session Management**: Manages conversation sessions and context

**Architecture**:
```python
class RTMiddleTier:
    endpoint: str                    # Azure OpenAI endpoint
    deployment: str                  # GPT realtime model deployment
    tools: dict[str, Tool] = {}      # Server-side tools
    system_message: Optional[str]    # Fashion assistant system prompt
    temperature: Optional[float]     # AI response temperature
    voice_choice: Optional[str]      # Voice selection for TTS
```

**Message Processing Flow**:
1. **Client → Server**: Processes user messages and tool results
2. **Server → Azure OpenAI**: Forwards messages to realtime API
3. **Azure OpenAI → Server**: Receives AI responses and tool calls
4. **Server → Client**: Processes tool calls, sends responses to frontend

**Tool Integration**:
- Executes fashion search tools server-side
- Returns results to both AI and client
- Maintains conversation context across tool calls

### 3. `ragtools.py` - RAG Tools for Fashion Search

**Purpose**: Defines all the tools available to the AI assistant for fashion e-commerce operations.

**Available Tools**:

1. **`search`** - Natural language product search
   ```python
   # Supports both vector and filtered search
   results = await search_manager.search_with_vector_and_filters(
       text_query=query,
       brand=filters.get('brand'),
       category=filters.get('category'),
       max_price=filters.get('max_price'),
       # ... other filters
   )
   ```

2. **`get_product_details`** - Detailed product information
3. **`add_to_cart`** - Shopping cart management
4. **`manage_wishlist`** - Favorites functionality
5. **`navigate_page`** - UI navigation control
6. **`get_recommendations`** - Personalized suggestions
7. **`update_style_preferences`** - User preference tracking

**Tool Result Flow**:
- Tools execute server-side with Azure AI Search integration
- Results sent to client via `ToolResultDirection.TO_CLIENT`
- Frontend updates UI based on tool results
- AI receives search results for contextual responses

### 4. `search_manager.py` - Azure AI Search Integration

**Purpose**: Comprehensive search interface that provides vector search, filtered search, and hybrid search capabilities for fashion products.

**Search Capabilities**:

#### Vector Search
```python
async def search_by_embedding(self, query: str, k: int = 3):
    query_embedding = self._calculate_embedding(query)
    vector_query = VectorizedQuery(
        vector=query_embedding,
        fields="embedding",
        k_nearest_neighbors=k
    )
    # Uses Azure OpenAI text-embedding-3-large
```

#### Filtered Search
```python
async def search_by_filters(self,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    color: Optional[str] = None,
    # ... 10+ fashion-specific filters
):
    # Constructs OData filter strings
    # Supports array filtering (colors, sizes, materials)
```

#### Hybrid Search
```python
async def search_with_vector_and_filters(self, text_query: str, **filters):
    # Combines semantic similarity with precise filtering
    # Uses vector_filter_mode="preFilter" for optimal performance
```

**Fashion-Specific Features**:
- **Multi-color support**: `colors/any(c: c eq 'black')`
- **Size filtering**: `sizes/any(s: s eq 'M')`
- **Material matching**: `search.ismatch('cotton', 'materials')`
- **Price ranges**: `price ge 50.0 and price le 200.0`
- **Sale filtering**: `on_sale eq true`

### 5. `index_manager.py` - Search Index Management

**Purpose**: Creates and populates Azure AI Search indexes with fashion product data and vector embeddings.

**Key Operations**:

#### Index Schema Creation
```python
def _build_index(self) -> SearchIndex:
    fields = [
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="title", type="Edm.String"),
        SearchableField(name="description", type="Edm.String"),
        SimpleField(name="brand", type="Edm.String", filterable=True),
        SimpleField(name="price", type="Edm.Double", filterable=True),
        # Fashion-specific fields
        SearchField(name="colors", type=Collection(String), filterable=True),
        SearchField(name="sizes", type=Collection(String), filterable=True),
        SearchField(name="materials", type=Collection(String), searchable=True),
        # Vector field for semantic search
        SearchField(name="embedding", type=Collection(Single),
                   vector_search_dimensions=3072)
    ]
```

#### Data Processing
```python
async def upload_documents(self, documents: List[Dict[str, Any]]):
    for doc in documents:
        # Generate embeddings
        combined_text = f"{doc['title']} {doc['description']} {doc['brand']}"
        doc["embedding"] = self._calculate_embedding(combined_text)

        # Flatten nested structures
        doc["ratings_average"] = doc["ratings"].get("average", 0.0)
        doc["ratings_count"] = doc["ratings"].get("count", 0)
```

**Index Features**:
- **Vector Search**: HNSW algorithm with cosine similarity
- **Semantic Search**: Title and description prioritization
- **Faceted Navigation**: Brand, category, color facets
- **Full-text Search**: Across multiple fields

### 6. `image_proxy.py` - Authenticated Image Serving

**Purpose**: Provides secure access to Azure Storage blob images without exposing storage credentials to the frontend.

**Security Features**:
- **Azure AD Authentication**: Uses DefaultAzureCredential
- **Path Validation**: Prevents directory traversal attacks
- **Caching Headers**: Optimizes image delivery
- **CORS Support**: Enables frontend access

**Image Flow**:
```python
async def get_blob_stream(self, product_id: str, filename: str):
    blob_name = f"{product_id}/{filename}"  # Organized by product ID
    blob_client = self.blob_service_client.get_blob_client(blob_name)
    blob_data = await blob_client.download_blob()
    return await blob_data.readall()
```

**Endpoints**:
- `/api/images/{product_id}/{filename}` - Serves authenticated product images

### 7. `image_tools/image_utils.py` - Image URL Service

**Purpose**: Converts product image filenames to authenticated backend URLs for frontend consumption.

**Key Methods**:
```python
def get_image_urls(self, product_id: str, image_filenames: List[str]) -> List[str]:
    backend_base = os.getenv("BACKEND_URL", "http://localhost:8765")
    return [
        f"{backend_base}/api/images/{product_id}/{filename}"
        for filename in image_filenames
    ]

def enhance_product_with_images(self, product: Dict[str, Any]) -> Dict[str, Any]:
    # Adds imageUrls field to search results
    enhanced_product = product.copy()
    enhanced_product['imageUrls'] = self.get_image_urls(
        product.get('id', ''), product.get('images', [])
    )
    return enhanced_product
```

## 🔄 Data Flow Architecture

### 1. Voice Query Processing
```
Frontend (Voice) → WebSocket → rtmt.py → Azure OpenAI Realtime API
                                     ↓
                            Tool Call (search) → ragtools.py
                                     ↓
                         SearchManager → Azure AI Search
                                     ↓
                    Enhanced Results ← ImageService
                                     ↓
                            Frontend ← Tool Result
```

### 2. Search Process
```
1. User speaks: "Show me black leather jackets under €200"
2. Azure OpenAI processes voice and generates tool call
3. ragtools.py executes search tool with filters
4. search_manager.py performs hybrid vector + filtered search
5. Results enhanced with image URLs via ImageService
6. Frontend receives products and updates UI
7. AI provides contextual fashion advice
```

### 3. Image Serving
```
Frontend requests image → image_proxy.py → Azure Storage Blob
                                     ↓
              Authenticated download ← DefaultAzureCredential
                                     ↓
                    Frontend ← Cached image response
```

## 🛠️ Development Workflow

### Setup and Initialization
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AZURE_OPENAI_ENDPOINT="..."
export AZURE_SEARCH_SERVICE_NAME="..."
export AZURE_STORAGE_ACCOUNT_NAME="..."

# Create and populate search index
python index_manager.py

# Start development server
python app.py
```

### Adding New Search Filters
1. **Extend SearchManager**: Add filter parameter to search methods
2. **Update RAG Tools**: Add filter to search tool schema
3. **Modify Index**: Ensure field is filterable in index schema
4. **Test Integration**: Verify filter works in voice queries

### Adding New Tools
1. **Define Schema**: Create tool schema in ragtools.py
2. **Implement Handler**: Add async tool function
3. **Register Tool**: Add to RTMiddleTier tools dictionary
4. **Frontend Integration**: Handle tool results in React components

## 🔐 Security & Authentication

### Azure Authentication
- **Development**: Azure Key Credentials from environment
- **Production**: DefaultAzureCredential with managed identity
- **Service-to-Service**: Bearer tokens for Azure OpenAI access

### Image Security
- **No Direct Access**: Frontend never accesses Azure Storage directly
- **Proxy Authentication**: Backend handles all blob authentication
- **Path Validation**: Prevents unauthorized file access

### Environment Configuration
```env
# Required Azure services
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_REALTIME_DEPLOYMENT=gpt-4o-realtime-preview
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
AZURE_SEARCH_SERVICE_NAME=your-search-service
AZURE_SEARCH_INDEX=fashion-products
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account

# Optional overrides
AZURE_OPENAI_API_KEY=...        # Use key instead of managed identity
AZURE_SEARCH_API_KEY=...        # Use key instead of managed identity
BACKEND_URL=http://localhost:8765  # For image URL generation
```

## 🧪 Testing

### Integration Tests
```bash
cd tests/
python -m pytest test_search_integration.py -v
```

### Manual Testing
```python
# Test search functionality
from search_manager import SearchManager
search_manager = SearchManager(...)
results = await search_manager.search_by_filters(brand="Nike", max_price=100.0)

# Test image service
from image_tools.image_utils import ImageService
image_service = ImageService()
urls = image_service.get_image_urls("CLO001", ["image1.jpg"])
```

## 🚀 Performance Optimizations

### Search Performance
- **Vector Caching**: Azure OpenAI embeddings cached in search index
- **Filtered Pre-filtering**: Filters applied before vector search
- **Faceted Results**: Efficient category-based navigation

### Image Performance
- **Proxy Caching**: 1-hour cache headers on image responses
- **Lazy Loading**: Images loaded on-demand from blob storage
- **CDN Ready**: Architecture supports CDN integration

### WebSocket Performance
- **Async Processing**: All I/O operations use asyncio
- **Connection Pooling**: Efficient Azure service connections
- **Message Batching**: Optimized real-time message handling

## 📊 Monitoring & Debugging

### Logging
```python
import logging
logger = logging.getLogger("voicerag")
logger.info("Search query processed", extra={"query": query, "results": len(results)})
```

### Common Issues
1. **Search returning no results**: Check index population and embedding model
2. **Images not loading**: Verify Azure Storage credentials and container access
3. **WebSocket connection failures**: Check Azure OpenAI endpoint and deployment name
4. **Tool calls not executing**: Verify ragtools.py tool registration

---

The Zalanko backend provides a sophisticated foundation for AI-powered fashion e-commerce, combining real-time voice interaction, advanced search capabilities, and secure image serving in a scalable, cloud-native architecture.