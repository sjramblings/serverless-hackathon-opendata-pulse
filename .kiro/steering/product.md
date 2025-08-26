# OpenData Pulse Product Overview

OpenData Pulse is a serverless application that makes open government datasets accessible and actionable through real-time dashboards, Gen-AI natural language queries, and MCP (Model Context Protocol) integration.

## Core Value Proposition

- **Real-time data ingestion** from NSW Air Quality API with hourly updates
- **Gen-AI natural language interface** for data exploration ("Show top 3 suburbs with worst PM2.5 today")
- **Interactive maps** using Amazon Location Service for geographic visualization
- **MCP tools** for developer integration and programmatic access
- **Serverless architecture** ensuring scalability and cost-effectiveness

## Primary Audiences

- **Citizens**: View live dashboards and air quality summaries
- **Developers**: Use GraphQL API and MCP tools to embed datasets in applications
- **Organizations**: Subscribe to alerts and reports for actionable decisions

## Key Features

- Scheduled data ingestion from NSW Government APIs
- Multi-layer storage (S3 raw/curated, DynamoDB hot aggregates)
- AppSync GraphQL API with Cognito authentication
- React frontend with interactive maps
- Natural language query processing via Amazon Bedrock
- MCP server exposing 5+ tools for data access and alerts

## Success Metrics

- Query latency < 2s for aggregates
- Support 100+ concurrent users
- Handle NSW air quality data with geographic coverage
- Demonstrate end-to-end functionality in 3-minute demo