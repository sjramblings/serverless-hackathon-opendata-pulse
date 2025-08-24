# Product Specification — OpenData Pulse (Gen-AI + MCP Edition)

---

## 1. Product Overview

**OpenData Pulse** is a **serverless application** that ingests open government datasets (e.g., air quality, transport, health), transforms them into queryable APIs, and provides **real-time dashboards and insights**.

A **Gen-AI layer** allows users to interact with data in plain language ("What were the top 5 LGAs for PM2.5 in the last 24 hours?").

An **MCP interface** exposes the same data access as programmable tools, enabling developers and AI assistants to query and subscribe directly.

**Primary Audiences:**

- **Citizens**: View live dashboards & summaries.
- **Developers**: Use GraphQL & MCP tools to embed datasets in their own apps.
- **Organizations**: Subscribe to alerts and reports for actionable decisions.

---

## 2. Goals & Success Metrics

- **Goal 1**: Make open data accessible & actionable with low technical friction.
- **Goal 2**: Provide a Gen-AI natural language layer to reduce learning curve.
- **Goal 3**: Enable reuse via MCP so others can build apps on top of OpenData Pulse.

**Success Metrics**:

- Query latency < 2s for aggregates.
- Support at least 2 hero datasets (Air Quality + Traffic).
- Handle 100 concurrent users (Cognito-authenticated).
- Provide at least 5 functional MCP tools.
- Demonstrate end-to-end in a 3-minute hackathon demo.

---

## 3. Key Features

### 3.1 Data Ingestion & Processing

- Scheduled fetches (via EventBridge) from open APIs.
- **Primary Data Source**: NSW Air Quality Data API (https://data.airquality.nsw.gov.au/docs/index.html)
  - Real-time air quality data for New South Wales, Australia
  - Covers PM2.5, PM10, NO2, O3, CO measurements
  - Geographic coverage: NSW suburbs and LGAs
  - Update frequency: Hourly/daily (government standard)
- **Data Process Flow**:
  1. EventBridge Rule triggers hourly data ingestion
  2. Lambda Ingest Function calls NSW API for all monitoring stations
  3. Raw data stored in S3 with NSW-specific partitioning: `raw/nsw-air-quality/raw/YYYY/MM/DD/HH/`
  4. Lambda ETL Function processes raw data:
     - Normalizes measurements and calculates AQI
     - Validates data quality and enriches with geographic metadata
     - Stores processed data in S3 curated (parquet) and DynamoDB (hot aggregates)
- Lambda ETL jobs to normalize data.
- Storage layers:
    - **Raw**: S3 bucket (`raw/`) with NSW-specific partitioning
    - **Curated**: S3 bucket (`curated/` parquet for Athena queries)
    - **Hot aggregates**: DynamoDB for real-time access

### 3.2 Query & API Layer

- **AppSync GraphQL API**
    - Entities: `Dataset`, `AirQualityReading`, `TrafficVolume`, `SubscriptionAlert`
    - Resolvers:
        - DynamoDB (hot aggregates)
        - Athena SQL (historical queries)
- **Cognito-authenticated** queries with JWT access.

### 3.3 Gen-AI Natural Language Layer

- **NL->Query Lambda**:
    - Uses Amazon Bedrock to translate natural language → GraphQL/Athena SQL.
    - Validates against dataset schema (no hallucinations).
- **Explain & Summarize Lambda**:
    - Converts raw query results into insights (trends, anomalies, "so what").
- **Optional Forecasting**: Bedrock prompt with historical data for predictive summaries.

### 3.4 MCP Integration

- MCP Server (Node.js) deployed as Lambda Function URL or Fargate service.
- Exposes tools:
    1. `dataset.catalog` → list datasets + schema
    2. `pulse.query` → NL query → GraphQL/SQL results
    3. `pulse.explain` → summaries from Bedrock
    4. `pulse.export` → export results to CSV/Parquet (pre-signed S3 URL)
    5. `pulse.alert.create` → define alert rules, routed via EventBridge → Pinpoint/email/webhook

### 3.5 Frontend

- React app hosted on **Amplify Hosting / S3 + CloudFront**
- **Interactive Map Visualization** using Amazon Location Service:
  - Real-time air quality station markers with color-coded AQI levels
  - Interactive station information on click/hover
  - Geographic queries and region selection tools
  - Heat maps and contour lines for air quality interpolation
  - Mobile-responsive touch interactions
  - Historical data time-slider for trend analysis
- Features:
    - Dashboard per dataset (map, chart, table)
    - Natural language query box ("Ask the data")
    - Export button for CSV download
    - Login (Cognito) for personalized alerts
- Optional: Embed QuickSight dashboard for polished visuals.

---

## 4. User Flows

### 4.1 Citizen User

1. Logs into web app (Cognito).
2. Views dashboard of "Air Quality in NSW."
3. Types: "Show top 3 suburbs with worst PM2.5 today."
4. System runs NL→Query → GraphQL → DynamoDB.
5. UI shows bar chart + "Parramatta, Bankstown, Liverpool are trending highest in Sydney."
6. User clicks **Export CSV** → gets pre-signed URL.

### 4.2 Developer (via MCP)

```bash
> mcp call dataset.catalog
# Returns ["AirQualityReading", "TrafficVolume"]

> mcp call pulse.query \
  natural_language_query="Hourly PM2.5 average in Sydney last 24h"
# Returns rows + query_id

> mcp call pulse.explain query_id=abc123
# "Trend upward 12% since yesterday, likely morning inversion pattern."

> mcp call pulse.alert.create \
  condition="pm25 > 75 for 10m in postcode 2000" channel="webhook:https://hook.site/..."
# "Alert created"

```

---

## 5. Technical Architecture

**Data Layer**

- **S3 (Raw + Curated)**
- **Glue Crawler** → Athena table creation
- **DynamoDB** for hot, low-latency aggregates

**Compute & Processing**

- **Lambda**:
    - Ingest (ETL pipelines)
    - NL→Query handler
    - Summarizer/Forecaster
    - Exporter (S3 presigned URL generator)
- **Step Functions** (optional) for orchestration

**APIs & Access**

- **AppSync (GraphQL)**
- **Cognito (Auth)**
- **MCP Server** (Python Lambda URL or Fargate)

**AI Layer**

- **Amazon Bedrock** (Claude/Sonar)
- Prompt templates stored in SSM Parameter Store

**Frontend**

- **Amplify Hosting / CloudFront**
- React + Apollo Client for GraphQL queries
- **Amazon Location Service** for interactive map visualization
- Optional QuickSight embedding

**Notifications**

- **EventBridge Rules** for alerts
- **Pinpoint / SNS / Webhooks** for outbound

---

## 6. Data Schema (example: Air Quality)

**NSW Air Quality Data Structure**
Based on NSW Government API (https://data.airquality.nsw.gov.au/docs/index.html)

```graphql
type AirQualityReading {
  id: ID!
  station_id: String!
  region: String!           # NSW region (e.g., "Sydney", "Newcastle", "Central Coast")
  suburb: String!           # Specific suburb/LGA
  postcode: String!         # NSW postcode
  latitude: Float!
  longitude: Float!
  timestamp: AWSDateTime!   # AEST/AEDT timezone
  pm25: Float              # PM2.5 concentration (μg/m³)
  pm10: Float              # PM10 concentration (μg/m³)
  no2: Float               # Nitrogen dioxide (ppb)
  o3: Float                # Ozone (ppb)
  co: Float                # Carbon monoxide (ppm)
  aqi: Float               # Air Quality Index (calculated)
  data_quality: String     # Data quality indicator
}
```

**Hot Aggregates (DynamoDB PK/SK)**

- PK: `REGION#<nsw_region>` (e.g., `REGION#Sydney`, `REGION#Newcastle`)
- SK: `TS#<ISO8601-hour>` (AEST/AEDT timezone)
- Attributes: pollutants, averages, min/max, suburb breakdowns

---

## 7. Security & Compliance

- **IAM least privilege** per Lambda & AppSync resolver.
- **Data partitioning** in S3 (raw/curated/exports).
- **API quotas** via AppSync and Function URLs.
- **WAF** on endpoints to prevent abuse.
- **Auth**: Cognito user pools; separate scopes for web users vs MCP tools.

---

## 8. Deliverables

- **Infrastructure as Code**: AWS CDK stacks using Python.
- **Web App**: Amplify-hosted React app.
- **MCP Server**: Python, exposing 5 tools.
- **Gen-AI Prompts**: System prompts for NL→Query + Summarizer.
- **Demo Assets**:
    - GitHub repo (CDK + frontend + MCP code)
    - Demo video (≤3 min) showing ingestion → query → insight → export
    - Architecture diagram (Lucidchart/Mermaid/CloudFormation Designer)
    - README.md with setup instructions

---

## 9. Roadmap / Nice-to-Have Extensions

- Add more datasets (health, crime stats, traffic incidents).
- Multi-region support.
- Add **forecasting models** (e.g., Bedrock Titan Time Series, if released).
- Gamify with community dashboards ("compare your suburb").
- Developer marketplace: publish MCP tools as a public registry.

---

## 10. Judging Fit (Hackathon Criteria)

- **Innovation & Creativity**: NL query + AI summaries + MCP = unique differentiator.
- **Architecture & Best Practices**: Pure serverless, IaC with CDK, event-driven, least privilege.
- **Completeness & Demo**: End-to-end flow in 3 minutes (ingest → API → GenAI query → insight → export). 