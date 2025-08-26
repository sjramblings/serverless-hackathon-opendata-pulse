# MCP Server Tools Documentation

*Comprehensive documentation for all MCP tools with usage examples and integration patterns.*

## MCP Server Overview

The OpenData Pulse MCP (Model Context Protocol) server exposes 5+ tools for programmatic access to NSW government data, enabling integration with AI assistants and automated systems.

## Available Tools

### 1. Air Quality Query Tool
**Tool Name**: `query_air_quality`
**Purpose**: Query current and historical air quality data

**Parameters**:
- `suburb` (string, optional): Specific suburb name
- `pollutant` (string, optional): PM2.5, PM10, Ozone, NO2
- `time_range` (string, optional): 1h, 24h, 7d, 30d
- `limit` (integer, optional): Maximum results (default: 10)

**Example Usage**:
```json
{
  "tool": "query_air_quality",
  "parameters": {
    "suburb": "Sydney",
    "pollutant": "PM2.5",
    "time_range": "24h"
  }
}
```

### 2. Geographic Search Tool
**Tool Name**: `search_by_location`
**Purpose**: Find air quality data near geographic coordinates

**Parameters**:
- `latitude` (float, required): Latitude coordinate
- `longitude` (float, required): Longitude coordinate
- `radius` (float, optional): Search radius in kilometers (default: 10)
- `pollutant` (string, optional): Filter by specific pollutant

**Example Usage**:
```json
{
  "tool": "search_by_location",
  "parameters": {
    "latitude": -33.8688,
    "longitude": 151.2093,
    "radius": 5.0
  }
}
```

### 3. Health Index Alert Tool
**Tool Name**: `create_health_alert`
**Purpose**: Create alerts for health index thresholds

**Parameters**:
- `suburb` (string, required): Target suburb
- `threshold` (integer, required): Health index threshold (0-300)
- `notification_method` (string, required): email, sms, webhook
- `contact` (string, required): Contact information

**Example Usage**:
```json
{
  "tool": "create_health_alert",
  "parameters": {
    "suburb": "Sydney",
    "threshold": 100,
    "notification_method": "email",
    "contact": "user@example.com"
  }
}
```

### 4. Data Export Tool
**Tool Name**: `export_data`
**Purpose**: Export historical data in various formats

**Parameters**:
- `format` (string, required): csv, json, parquet
- `start_date` (string, required): ISO 8601 date
- `end_date` (string, required): ISO 8601 date
- `suburbs` (array, optional): List of suburbs to include
- `pollutants` (array, optional): List of pollutants to include

**Example Usage**:
```json
{
  "tool": "export_data",
  "parameters": {
    "format": "csv",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "suburbs": ["Sydney", "Melbourne"],
    "pollutants": ["PM2.5", "PM10"]
  }
}
```

### 5. System Health Tool
**Tool Name**: `check_system_health`
**Purpose**: Monitor system status and data freshness

**Parameters**:
- `component` (string, optional): ingestion, etl, api, frontend
- `detailed` (boolean, optional): Include detailed metrics

**Example Usage**:
```json
{
  "tool": "check_system_health",
  "parameters": {
    "component": "ingestion",
    "detailed": true
  }
}
```

## Integration Patterns

### AI Assistant Integration
```python
# Example integration with MCP client
import mcp_client

client = mcp_client.Client("opendata-pulse-mcp-server")

# Query air quality for natural language request
response = client.call_tool("query_air_quality", {
    "suburb": "Sydney",
    "time_range": "24h"
})

# Process response for AI assistant
air_quality_summary = f"Current PM2.5 in Sydney: {response['pm25']} μg/m³"
```

### Automated Monitoring
```python
# Example automated health monitoring
import schedule
import time

def check_data_freshness():
    health_status = client.call_tool("check_system_health", {
        "component": "ingestion",
        "detailed": True
    })
    
    if health_status['last_update'] > 2:  # hours
        send_alert("Data ingestion delayed")

schedule.every(30).minutes.do(check_data_freshness)
```

### Custom Dashboard Integration
```javascript
// Example React component integration
const AirQualityWidget = () => {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    mcpClient.callTool('query_air_quality', {
      suburb: 'Sydney',
      time_range: '24h'
    }).then(setData);
  }, []);
  
  return (
    <div>
      <h3>Sydney Air Quality</h3>
      <p>PM2.5: {data?.pm25} μg/m³</p>
    </div>
  );
};
```

## Authentication and Authorization

### API Key Authentication
- Each MCP client requires a valid API key
- Keys are managed through the Cognito user pool
- Rate limiting applies per API key

### Permission Scopes
- **Read**: Query air quality data
- **Alert**: Create and manage alerts
- **Export**: Export historical data
- **Admin**: System health and configuration

*Content will be generated from MCP server implementation analysis*