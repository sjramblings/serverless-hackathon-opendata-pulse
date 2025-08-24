# OpenData Pulse - Gen-AI + MCP Edition

A serverless application that ingests open government datasets, transforms them into queryable APIs, and provides real-time dashboards and insights with Gen-AI natural language interaction and MCP tools.

## 🚀 Project Overview

OpenData Pulse makes open data accessible and actionable with:
- **Real-time data ingestion** from NSW Air Quality API
- **Gen-AI natural language queries** for data exploration
- **Interactive maps** using Amazon Location Service
- **MCP interface** for developer integration
- **Serverless architecture** built with AWS CDK

## 🏗️ Architecture

The project consists of multiple CDK stacks:

- **DataStack**: S3, DynamoDB, Glue, Athena
- **ComputeStack**: Lambda functions, EventBridge
- **ApiStack**: AppSync GraphQL API, Cognito
- **FrontendStack**: Amplify hosting
- **LocationStack**: Amazon Location Service

## 📁 Project Structure

```
opendata-pulse/
├── infrastructure/          # CDK stack definitions
│   ├── data_stack.py       # Data storage resources
│   ├── compute_stack.py    # Compute and processing
│   ├── api_stack.py        # API and authentication
│   ├── frontend_stack.py   # Frontend hosting
│   └── location_stack.py   # Location services
├── lambda-functions/        # Lambda function code
│   ├── ingest/             # Data ingestion
│   ├── etl/                # ETL processing
│   └── layers/             # Shared dependencies
├── frontend/               # React application
├── mcp-server/            # MCP server implementation
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── app.py                 # Main CDK application
├── cdk.json              # CDK configuration
└── requirements.txt       # Python dependencies
```

## 🛠️ Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.9+
- Node.js 18+
- AWS CDK v2+

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd opendata-pulse

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. AWS Configuration

```bash
# Configure AWS credentials
aws configure

# Set default region (recommended: ap-southeast-2 for Sydney)
aws configure set default.region ap-southeast-2
```

### 3. Deploy Infrastructure

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all

# Or deploy specific stack
cdk deploy OpenDataPulseDataStack
```

### 4. Development

```bash
# Synthesize CloudFormation templates
cdk synth

# View differences
cdk diff

# Watch for changes
cdk watch
```

## 🔧 Configuration

### Environment Variables

Set these in your CDK context or environment:

- `account`: AWS account ID
- `region`: AWS region (default: ap-southeast-2)

### NSW Air Quality API

The application integrates with the [NSW Air Quality Data API](https://data.airquality.nsw.gov.au/docs/index.html) for real-time air quality data.

## 🧪 Testing

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=infrastructure

# Lint code
flake8 infrastructure/
black infrastructure/
```

## 📊 Data Flow

1. **Ingestion**: EventBridge triggers hourly data fetch from NSW API
2. **Processing**: Lambda ETL functions normalize and enrich data
3. **Storage**: Data stored in S3 (raw/curated) and DynamoDB (hot)
4. **Query**: AppSync GraphQL API provides data access
5. **Visualization**: React frontend with interactive maps
6. **AI**: Gen-AI layer for natural language queries

## 🔐 Security

- IAM least privilege access
- Cognito user authentication
- S3 bucket encryption
- WAF protection for APIs
- Data partitioning and access controls

## 📈 Monitoring

- CloudWatch logs for Lambda functions
- CloudTrail for API access
- S3 access logs
- DynamoDB metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check the documentation in `/docs`
- Review the CDK stack outputs

## 🗺️ Roadmap

- [ ] Phase 1: Foundation & Infrastructure ✅
- [ ] Phase 2: Data Pipeline & Storage
- [ ] Phase 3: Gen-AI & MCP Integration
- [ ] Phase 4: Frontend Development
- [ ] Phase 5: Testing & Deployment 