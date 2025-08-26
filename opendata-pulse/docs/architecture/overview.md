# Architecture Overview

*This document provides a high-level overview of the OpenData Pulse system architecture.*

## System Architecture

OpenData Pulse is a serverless application built on AWS that ingests, processes, and serves NSW government open data through multiple interfaces including web dashboards, GraphQL APIs, and MCP tools.

## Core Components

### Infrastructure Stacks
- **DataStack** - S3 storage, DynamoDB, Glue, Athena for data management
- **ComputeStack** - Lambda functions for data processing and ETL
- **APIStack** - AppSync GraphQL API with Cognito authentication
- **FrontendStack** - Amplify hosting and CloudFront distribution
- **LocationStack** - Amazon Location Service for geographic visualization

### Data Flow
1. **Ingestion** - Scheduled Lambda functions fetch data from NSW APIs
2. **Processing** - ETL Lambda transforms raw data into curated formats
3. **Storage** - Multi-layer storage in S3 (raw/curated) and DynamoDB (hot aggregates)
4. **Access** - Data served through GraphQL API and MCP tools

## Technology Stack
- **Infrastructure**: AWS CDK with Python
- **Backend**: Python Lambda functions with Powertools
- **Frontend**: React with Apollo Client
- **API**: AppSync GraphQL
- **AI/ML**: Amazon Bedrock for natural language processing

*Generated automatically from CDK stack definitions*