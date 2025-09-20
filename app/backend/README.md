# Zalanko Backend

Production-ready backend for the Zalanko fashion e-commerce platform with AI-powered voice search capabilities.

## Architecture

- **Framework**: aiohttp (async Python web framework)
- **AI Integration**: Azure OpenAI for real-time voice conversations
- **Search**: Azure AI Search with vector embeddings
- **Virtual Try-On**: Google Vertex AI Gemini 2.5 Flash
- **Storage**: Azure Blob Storage for product images

## Directory Structure

```
app/backend/
├── app.py                     # Main application entry point
├── ragtools.py               # RAG tools for fashion assistant
├── rtmt.py                   # Real-time middleware tier
├── search_manager.py         # Azure Search integration
├── image_proxy.py           # Image proxy service
├── index_manager.py         # Search index management
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized configuration
├── utils/
│   ├── __init__.py
│   └── logger.py            # Structured logging
├── services/
│   ├── __init__.py
│   ├── search_service.py          # Search service layer
│   ├── virtual_tryon_service.py   # Virtual try-on service
│   └── virtual_tryon_endpoint.py  # Virtual try-on API endpoints
├── exceptions/
│   ├── __init__.py          # Custom exception hierarchy
├── image_tools/             # Image processing utilities
├── tests/                   # Test suites
└── static/                  # Static web assets
```

## Production Features

- **Centralized Configuration**: Environment-based settings with validation
- **Structured Logging**: Request tracing and comprehensive error logging
- **Error Handling**: Custom exception hierarchy with proper error responses
- **Input Validation**: Parameter validation for all API endpoints
- **Middleware**: Request logging and global error handling
- **Type Safety**: Full type hints throughout the codebase

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your Azure credentials
   ```

3. **Create Search Index**:
   ```bash
   python index_manager.py
   ```

4. **Start Server**:
   ```bash
   python app.py
   ```

The server will start on `http://localhost:8765`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes* |
| `AZURE_OPENAI_REALTIME_DEPLOYMENT` | Real-time model deployment name | Yes |
| `AZURE_SEARCH_SERVICE_NAME` | Azure Search service name | Yes |
| `AZURE_SEARCH_API_KEY` | Azure Search API key | Yes* |
| `AZURE_SEARCH_INDEX` | Search index name | Yes |
| `AZURE_STORAGE_ACCOUNT_NAME` | Storage account for images | Yes |
| `AZURE_TENANT_ID` | Azure tenant ID for auth | No** |

*Required unless using Azure AD authentication
**Required for Azure AD authentication

## API Endpoints

- **WebSocket**: `/realtime` - Real-time voice conversation
- **Images**: `/api/images/{product_id}/{filename}` - Product image proxy
- **Virtual Try-On**: `/api/virtual-tryon` - Virtual try-on processing
- **Static**: `/` - Frontend static files

## Development

### Adding New Tools

1. Define tool schema in `ragtools.py`
2. Implement tool handler function
3. Register tool in `attach_rag_tools()`
4. Add proper error handling and logging

### Testing

```bash
python -m pytest tests/
```

### Logging

Logs are structured with request IDs for tracing:
```
2024-01-01 12:00:00 INFO [req_123] Starting search for: "black jacket"
2024-01-01 12:00:01 INFO [req_123] Search completed: Found 5 products
```

## Deployment

For production deployment, ensure:

1. All environment variables are properly set
2. Azure services are provisioned and configured
3. Search index is created and populated
4. SSL/TLS is configured for WebSocket connections
5. Proper logging configuration for production

## Monitoring

- Application logs include request tracing
- Azure service metrics available in Azure Portal
- WebSocket connection status in application logs