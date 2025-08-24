# Phase 1: Foundation & Infrastructure Setup
## OpenData Pulse Build Tasks

### **Phase 1 Overview**
This phase establishes the foundational infrastructure and project structure using AWS CDK with Python. We'll create the core storage, compute, and security components that all subsequent phases will build upon.

---

## **Task 1.1: Project Structure & CDK Setup**
**Estimated Time**: 2-3 hours
**Priority**: Critical

### Subtasks:
- [ ] Initialize AWS CDK project with Python
- [ ] Set up project directory structure:
  ```
  opendata-pulse/
  ├── infrastructure/          # CDK stacks
  ├── frontend/               # React application
  ├── mcp-server/            # MCP server code
  ├── lambda-functions/      # Lambda function code
  ├── docs/                  # Documentation
  └── scripts/               # Utility scripts
  ```
- [ ] Configure CDK app with multiple stacks:
  - `DataStack` - S3, DynamoDB, Glue
  - `ComputeStack` - Lambda functions, EventBridge
  - `ApiStack` - AppSync, Cognito
  - `FrontendStack` - Amplify hosting
- [ ] Set up Python virtual environment and dependencies
- [ ] Configure CDK context and environment variables
- [ ] Create initial `app.py` with stack definitions

### Deliverables:
- CDK project structure
- Basic stack definitions
- Development environment setup

---

## **Task 1.2: Core Infrastructure Stack**
**Estimated Time**: 4-6 hours
**Priority**: Critical

### Subtasks:
- [ ] **S3 Buckets Setup**:
  - Raw data bucket (`raw/`) with NSW-specific partitioning:
    - `raw/nsw-air-quality/` for NSW government API data
    - `raw/nsw-air-quality/raw/` for API responses
    - `raw/nsw-air-quality/processed/` for normalized data
    - `raw/nsw-air-quality/metadata/` for station info and schemas
  - Curated data bucket (`curated/`) with parquet partitioning
  - Exports bucket (`exports/`) with temporary access
  - Configure bucket policies and encryption
- [ ] **DynamoDB Tables**:
  - Hot aggregates table with proper partitioning
  - PK: `REGION#<nsw_region>` (e.g., `REGION#Sydney`, `REGION#Newcastle`)
  - SK: `TS#<ISO8601-hour>` (AEST/AEDT timezone)
  - Configure auto-scaling and backup policies
  - Set up TTL for data retention
  - Consider geographic indexes for suburb-based queries
- [ ] **Glue Database & Crawler**:
  - Create Glue database for Athena
  - Configure crawler for S3 data discovery
  - Set up IAM roles for Glue operations
- [ ] **Athena Workgroup**:
  - Configure query result location
  - Set up cost controls and query limits

### Deliverables:
- S3 buckets with proper policies
- DynamoDB table with optimal schema
- Glue crawler configuration
- Athena workgroup setup

---

## **Task 1.3: Authentication & Security**
**Estimated Time**: 3-4 hours
**Priority**: Critical

### Subtasks:
- [ ] **Cognito User Pool**:
  - Create user pool with app client
  - Configure password policies and MFA
  - Set up user attributes (email, region preferences)
  - Configure triggers for user management
- [ ] **IAM Roles & Policies**:
  - Lambda execution roles with least privilege
  - AppSync service role
  - Glue service role
  - User pool roles for authenticated/unauthenticated access
- [ ] **WAF Configuration**:
  - Set up WAF rules for API protection
  - Configure rate limiting and DDoS protection
  - Set up IP allow/deny lists if needed
- [ ] **Security Groups & VPC** (if needed):
  - Configure VPC for private resources
  - Set up security groups for Lambda functions

### Deliverables:
- Cognito user pool with app client
- IAM roles with least privilege access
- WAF configuration for API protection
- Security groups and VPC setup

---

## **Task 1.4: Basic Lambda Infrastructure**
**Estimated Time**: 2-3 hours
**Priority**: High

### Subtasks:
- [ ] **Lambda Layer Setup**:
  - Create shared layers for common dependencies
  - Configure Python runtime and environment variables
  - Set up logging and monitoring
- [ ] **EventBridge Rules**:
  - Create basic rules for scheduled data ingestion
  - Configure targets for Lambda functions
  - Set up error handling and dead letter queues
- [ ] **Basic Lambda Functions**:
  - Data ingestion function (placeholder) - NSW Air Quality API client
  - ETL processing function (placeholder) - NSW data normalization
  - Health check function for testing
  - NSW API rate limiting and error handling

### Deliverables:
- Lambda layers and basic functions
- EventBridge rules for scheduling
- Basic error handling and monitoring

---

## **Task 1.5: Development & Testing Setup**
**Estimated Time**: 2-3 hours
**Priority**: Medium

### Subtasks:
- [ ] **Local Development**:
  - Set up CDK local testing and debugging
  - Configure local DynamoDB for development
  - Set up environment-specific configurations
- [ ] **Testing Infrastructure**:
  - Create basic unit tests for CDK constructs
  - Set up integration test environment
  - Configure CI/CD pipeline structure
- [ ] **Documentation**:
  - Create README with setup instructions
  - Document stack architecture and dependencies
  - Create development workflow documentation

### Deliverables:
- Local development environment
- Basic testing framework
- Initial documentation

---

## **Phase 1 Success Criteria**
- [ ] CDK project successfully deploys all stacks
- [ ] S3 buckets accessible with proper permissions
- [ ] DynamoDB table created with correct schema
- [ ] Cognito user pool accessible and configurable
- [ ] Basic Lambda functions deploy and execute
- [ ] All IAM roles follow least privilege principle
- [ ] Local development environment functional

---

## **Phase 1 Dependencies & Prerequisites**
- AWS CLI configured with appropriate permissions
- Python 3.9+ installed
- Node.js 18+ installed (for CDK)
- AWS CDK v2+ installed
- Appropriate AWS account and region access
- Access to NSW Air Quality Data API (https://data.airquality.nsw.gov.au/docs/index.html)
- Understanding of NSW timezone (AEST/AEDT) and geographic regions
- CDK Toolkit for local development and testing

---

## **Phase 1 Risk Mitigation**
- **Risk**: CDK deployment failures due to IAM permissions
  - **Mitigation**: Test with minimal permissions first, gradually add required permissions
- **Risk**: S3 bucket naming conflicts
  - **Mitigation**: Use unique naming convention with environment prefixes
- **Risk**: Cognito configuration complexity
  - **Mitigation**: Start with basic configuration, add advanced features incrementally
- **Risk**: NSW API rate limiting or data quality issues
  - **Mitigation**: Implement exponential backoff, data validation, and fallback strategies
- **Risk**: NSW timezone handling complexity
  - **Mitigation**: Use UTC internally, convert to AEST/AEDT for user display only

---

## **Next Phase Preparation**
After completing Phase 1, we'll have:
- Solid foundation for data storage and processing
- Authentication system ready for user management
- Basic compute infrastructure for Lambda functions
- Development environment for rapid iteration

**Phase 2 will focus on**: Data Pipeline & Storage implementation 