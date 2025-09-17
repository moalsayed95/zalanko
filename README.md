# Zalanko - AI-Powered Fashion E-commerce Platform

Zalanko is a modern fashion e-commerce platform that combines real-time voice interaction with AI-powered product search. Users can discover clothing items through natural language voice commands, powered by Azure AI services and a React-based frontend with a sleek dark theme design.

## Architecture

### Frontend
- **Technology**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with dark theme design
- **Key Features**:
  - Real-time voice interaction with WebSocket connection
  - Fashion catalog browsing with detailed product views
  - Shopping cart and favorites functionality
  - Responsive design optimized for fashion e-commerce

### Backend
- **Technology**: Python + aiohttp (async web server)
- **Key Components**:
  - `app.py`: Main application server with WebSocket endpoints
  - `rtmt.py`: Real-time multi-turn conversation handling
  - `search_manager.py`: Azure AI Search integration
  - `ragtools.py`: RAG tools for fashion-specific search operations
  - `index_manager.py`: Search index creation and data population

### Data & Search
- **Data Source**: JSON-based fashion product catalog (`data/clothing_data.json`)
- **Search Engine**: Azure AI Search with vector embeddings
- **AI Integration**: Azure OpenAI for embeddings and real-time chat

## Key Features

### Voice-Powered Shopping
- Real-time voice interaction through WebSocket connection
- Natural language product queries (e.g., "show me black leather jackets under �200")
- AI fashion assistant that understands style preferences and provides personalized recommendations

### Advanced Search Capabilities
- **Vector Search**: Semantic search using Azure OpenAI embeddings
- **Filtered Search**: Multi-dimensional filtering by:
  - Brand, category, gender
  - Price range, colors, sizes
  - Materials, style tags
  - Sale status and availability
- **Hybrid Search**: Combines vector similarity with traditional filters

### Fashion-Focused Features
- **Virtual Try-On**: AI-powered virtual try-on using Google Vertex AI Gemini 2.5 Flash Image Preview
- **Voice-Activated Try-On**: Say "try this on virtually" to open the try-on modal seamlessly
- **Real-time Image Generation**: High-quality virtual try-on results (1.6MB+ images) in 10-30 seconds
- Detailed product information (materials, sizing, care instructions)
- Style preferences tracking and personalized recommendations
- Shopping cart and wishlist functionality
- Comprehensive product ratings and reviews

## =' Technology Stack

### Frontend Dependencies
- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icons
- **WebSocket** - Real-time communication

### Backend Dependencies
- **aiohttp** - Async HTTP server with CORS support
- **Azure SDK** - Search, Identity, and Storage integration
- **OpenAI** - Azure OpenAI for embeddings and chat
- **Google Generative AI** - Vertex AI Gemini for virtual try-on
- **Pillow** - Image processing and validation
- **python-dotenv** - Environment configuration

### Azure Services
- **Azure AI Search** - Vector and filtered search
- **Azure OpenAI** - GPT realtime and text-embedding models
- **Azure Storage** - Product image storage

### Google Cloud Services
- **Vertex AI** - Gemini 2.5 Flash Image Preview for virtual try-on
- **Google Cloud Project** - API key authentication for Gemini access

## Data Structure

### Product Schema
```json
{
  "id": "CLO001",
  "title": "Essential Cotton T-Shirt",
  "description": "Soft organic cotton t-shirt...",
  "brand": "Zara",
  "category": "T-Shirts & Tops",
  "subcategory": "Basic Tees",
  "gender": "unisex",
  "price": 19.99,
  "sale_price": null,
  "on_sale": false,
  "colors": ["white", "black", "navy"],
  "sizes": ["XS", "S", "M", "L", "XL"],
  "materials": ["100% Organic Cotton"],
  "style_tags": ["casual", "basic", "everyday"],
  "ratings": {"average": 4.3, "count": 892},
  "images": ["fashion_model_1.jpg"],
  "availability": "in_stock",
  "sustainability_score": 8
}
```

### Search Index Features
- **Vector embeddings** for semantic search using Azure OpenAI
- **Filterable fields** for precise product discovery
- **Faceted search** for category-based navigation
- **Full-text search** across titles, descriptions, and tags

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Azure account with AI Search, OpenAI, and Storage services

### Environment Setup
1. Copy environment variables:
```bash
./get-keys.sh --resource-group <your-resource-group>
```

2. Configure backend environment (create `.env` file):
```
# Azure Services
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_REALTIME_DEPLOYMENT=gpt-realtime
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
AZURE_SEARCH_SERVICE_NAME=your-search-service
AZURE_SEARCH_API_KEY=your-search-key
AZURE_SEARCH_INDEX=fashion-products
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_CONTAINER_NAME=product-images
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection

# Google Cloud Services (for Virtual Try-On)
GOOGLE_CLOUD_API_KEY=your-google-api-key
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# Backend Configuration
BACKEND_URL=http://localhost:8765
```

### Database Setup
Create and populate the search index:
```bash
cd app/backend
python index_manager.py
```

### Development

#### Backend
```bash
cd app/backend
pip install -r ../../requirements.txt
python app.py
```

#### Frontend
```bash
cd app/frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://127.0.0.1:5173
- Backend: http://localhost:8765

### Production Build

#### Frontend
```bash
cd app/frontend
npm run build
```

#### Docker Deployment
```bash
docker build -t zalanko ./app
docker run -p 8000:8000 zalanko
```

## <� Search Implementation Details

### Vector Search
- Uses Azure OpenAI `text-embedding-3-large` model
- Combines product title, description, brand, and style tags for embeddings
- HNSW algorithm for efficient similarity search

### Search Tools Available to AI Assistant
1. **`search`** - Natural language product search with filters
2. **`get_product_details`** - Detailed product information
3. **`add_to_cart`** - Shopping cart management
4. **`manage_wishlist`** - Favorites functionality
5. **`navigate_page`** - UI navigation control
6. **`get_recommendations`** - Personalized product suggestions
7. **`update_style_preferences`** - User preference tracking
8. **`virtual_try_on`** - AI-powered virtual try-on image generation

### Search Filters
- **Brand filtering**: Exact match on fashion brands
- **Category/subcategory**: Hierarchical product classification
- **Price range**: Min/max price filtering
- **Color matching**: Multi-color support per product
- **Size availability**: Size-based filtering
- **Material search**: Fabric and material matching
- **Sale status**: On-sale product filtering

## AI-Powered Virtual Try-On

### Technology Stack
- **AI Model**: Google Vertex AI Gemini 2.5 Flash Image Preview
- **Location**: Global endpoint (required for image generation)
- **Input**: Person photo + clothing item image + natural language prompt
- **Output**: High-quality virtual try-on images (832x1248px, ~1.6MB)
- **Processing Time**: 10-30 seconds per generation

### Virtual Try-On Features
- **Voice Activation**: Say "try this on virtually" to automatically open try-on modal
- **Seamless UX**: Voice command opens modal with product pre-loaded
- **Image Processing**: Automatic validation, resizing, and format conversion
- **Quality Output**: Realistic lighting, proper fit, natural appearance
- **Download & Share**: Save generated images locally or share with others

### Technical Implementation
```python
# Virtual try-on service integration
from virtual_tryon_service import virtual_tryon_service

# Generate virtual try-on
success, result_image, error = await virtual_tryon_service.generate_virtual_tryon(
    person_image_bytes,
    clothing_image_bytes,
    product_info
)
```

### API Endpoints
- **POST** `/api/virtual-tryon` - Generate virtual try-on images
- **GET** `/api/virtual-tryon-results/{filename}` - Serve generated images
- **OPTIONS** `/api/virtual-tryon` - CORS preflight handling

## GPT Realtime API Implementation

### Custom WebSocket Implementation
- **No dedicated SDK used** - Direct WebSocket connection via aiohttp
- **Custom middle tier** (`rtmt.py`) that proxies messages between client and Azure OpenAI
- **Endpoint**: `/openai/realtime` on Azure OpenAI service
- **API Version**: `2024-10-01-preview`

### Real-time Features
- **WebSocket Communication**: Bidirectional communication between frontend and backend
- **Tool Integration**: Server-side RAG tools for fashion search and virtual try-on
- **Voice Processing**: Real-time audio streaming and processing
- **Session Management**: Conversation state and context retention

## Real-time Features

### AI Assistant Capabilities
- Fashion expertise with style advice
- Personalized recommendations based on user preferences
- Multi-turn conversations with context retention
- Product comparison and detailed explanations

## UI/UX Highlights

### Dark Theme Design
- Modern gradient-based color scheme (purple/pink/orange)
- Responsive layout optimized for product browsing
- Animated voice interaction indicators
- Smooth transitions and hover effects

### Product Display
- Large featured product view with detailed information
- Horizontal scrolling product suggestions
- Color and size selection interfaces
- Shopping cart with pricing calculations

## Development Guidelines

### Code Organization
- Clean separation between UI components and business logic
- Shared utility functions for colors, pricing, and formatting
- TypeScript types for type-safe development
- Consistent naming conventions and file structure

### Adding New Features
1. Review existing patterns in the codebase
2. Follow established TypeScript and React conventions
3. Maintain the dark theme design consistency
4. Use existing utility functions where possible
5. Ensure proper error handling and loading states

## Interactive Voice Commands

### Product Discovery
- `"Show me black leather jackets under 200 euros"`
- `"I'm looking for casual summer dresses"`
- `"Find me Nike sneakers in size 42"`

### Shopping Actions
- `"Add this jacket to my cart in medium size"`
- `"Add this dress to my wishlist"`
- `"Show me my shopping cart"`

### Style Assistance
- `"I prefer minimalist style and sustainable materials"`
- `"What colors go well with this outfit?"`
- `"Show me similar items to this dress"`

### Virtual Try-On Commands
- `"Try this on virtually"`
- `"Show me wearing this dress"`
- `"How would this look on me?"`
- `"Let me see myself in this outfit"`

---