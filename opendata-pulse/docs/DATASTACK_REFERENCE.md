# DataStack Reference Guide
## OpenData Pulse Core Infrastructure

This document provides quick reference information for the DataStack resources deployed in Task 1.2.

---

## 📦 **S3 Buckets**

### **Raw Data Bucket**
- **Name**: `opendata-pulse-raw-data-{account-id}`
- **Purpose**: Store raw NSW Air Quality API responses
- **Lifecycle**: 30 days → IA, 90 days → Glacier, 365 days → Delete
- **Encryption**: AES256 server-side encryption
- **Access**: Private (public access blocked)

### **Curated Data Bucket**
- **Name**: `opendata-pulse-curated-data-{account-id}`
- **Purpose**: Store processed/parquet data for Athena queries
- **Lifecycle**: Versioned (no automatic deletion)
- **Encryption**: AES256 server-side encryption
- **Access**: Private (public access blocked)

### **Exports Bucket**
- **Name**: `opendata-pulse-exports-{account-id}`
- **Purpose**: Temporary storage for data exports
- **Lifecycle**: 7 days → Delete
- **Encryption**: AES256 server-side encryption
- **Access**: Private (public access blocked)

---

## 🗄️ **DynamoDB Table**

### **Air Quality Table**
- **Name**: `opendata-pulse-air-quality`
- **Partition Key**: `PK` (String)
- **Sort Key**: `SK` (String)
- **Billing**: Pay-per-request (auto-scaling)
- **TTL**: Enabled (attribute: `TTL`)

### **Key Schema Examples**
```
PK: "REGION#Sydney"
SK: "TS#2024-01-15T14:00:00Z"
```

### **Global Secondary Index**
- **Name**: `SuburbIndex`
- **Partition Key**: `SUBURB` (String)
- **Sort Key**: `TIMESTAMP` (String)
- **Projection**: ALL

---

## 🕷️ **Glue Database**

### **Database**
- **Name**: `opendata_pulse_db`
- **Description**: Database for OpenData Pulse datasets
- **Catalog**: AWS Data Catalog

### **Service Role**
- **Name**: `GlueServiceRole`
- **Policy**: `AWSGlueServiceRole`
- **Permissions**: Read/write access to raw and curated S3 buckets

---

## 🔍 **Athena Workgroup**

### **Workgroup**
- **Name**: `opendata-pulse-workgroup`
- **Result Location**: `s3://{curated-bucket}/athena-results/`
- **Configuration**: Enforced

---

## 🔧 **Common Operations**

### **S3 Operations**
```bash
# List buckets
aws s3 ls | grep opendata-pulse

# Create folder structure
aws s3api put-object --bucket opendata-pulse-raw-data-{account-id} --key "nsw-air-quality/raw/"
aws s3api put-object --bucket opendata-pulse-raw-data-{account-id} --key "nsw-air-quality/processed/"
aws s3api put-object --bucket opendata-pulse-raw-data-{account-id} --key "nsw-air-quality/metadata/"

# Upload data
aws s3 cp data.json s3://opendata-pulse-raw-data-{account-id}/nsw-air-quality/raw/
```

### **DynamoDB Operations**
```bash
# Describe table
aws dynamodb describe-table --table-name opendata-pulse-air-quality

# Query by region
aws dynamodb query \
  --table-name opendata-pulse-air-quality \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk":{"S":"REGION#Sydney"}}'

# Query by suburb
aws dynamodb query \
  --table-name opendata-pulse-air-quality \
  --index-name SuburbIndex \
  --key-condition-expression "SUBURB = :suburb" \
  --expression-attribute-values '{":suburb":{"S":"Parramatta"}}'
```

### **Athena Operations**
```sql
-- Set workgroup
SET work_group = 'opendata-pulse-workgroup';

-- Query curated data
SELECT * FROM opendata_pulse_db.air_quality_readings 
WHERE region = 'Sydney' 
AND timestamp >= '2024-01-15';
```

---

## 📊 **CloudFormation Outputs**

After deployment, the stack provides these outputs:

```bash
# Get all outputs
aws cloudformation describe-stacks \
  --stack-name OpenDataPulseDataStack \
  --query 'Stacks[0].Outputs'

# Get specific output
aws cloudformation describe-stacks \
  --stack-name OpenDataPulseDataStack \
  --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' \
  --output text
```

### **Available Outputs**
- `RawBucketName`: S3 bucket for raw NSW air quality data
- `CuratedBucketName`: S3 bucket for curated/processed data
- `ExportsBucketName`: S3 bucket for data exports
- `DynamoDBTableName`: DynamoDB table for air quality hot aggregates

---

## 🔐 **Security & Permissions**

### **IAM Roles**
- **GlueServiceRole**: For Glue operations on S3
- **Permissions**: Read/write access to raw and curated buckets

### **Encryption**
- **S3**: AES256 server-side encryption
- **DynamoDB**: Encryption at rest (default)

### **Access Control**
- **S3**: Public access blocked
- **DynamoDB**: IAM-based access control
- **Athena**: Workgroup-based access control

---

## 💰 **Cost Optimization**

### **S3 Cost Optimization**
- Lifecycle policies move data to cheaper storage tiers
- Raw data: 30 days → IA, 90 days → Glacier
- Exports: 7 days → Delete

### **DynamoDB Cost Optimization**
- Pay-per-request billing for variable workloads
- TTL for automatic data cleanup
- GSI for efficient queries

### **Estimated Monthly Costs**
- **S3**: $5-10/month
- **DynamoDB**: $10-20/month
- **Glue**: $5/month
- **Athena**: $5-15/month
- **Total**: $25-50/month

---

## 🚨 **Monitoring & Alerts**

### **Recommended CloudWatch Alarms**
```bash
# S3 bucket size alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "S3-RawBucket-Size" \
  --metric-name BucketSizeBytes \
  --namespace AWS/S3 \
  --statistic Average \
  --period 86400 \
  --threshold 10737418240 \
  --comparison-operator GreaterThanThreshold

# DynamoDB throttled requests
aws cloudwatch put-metric-alarm \
  --alarm-name "DynamoDB-ThrottledRequests" \
  --metric-name ThrottledRequests \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## 🔄 **Data Flow Integration**

### **NSW API Integration Points**
1. **Raw Data**: Store API responses in `raw/` folder
2. **Processing**: ETL functions read from `raw/`, write to `processed/`
3. **Hot Data**: Real-time data stored in DynamoDB
4. **Analytics**: Athena queries on curated parquet files
5. **Exports**: Temporary files in exports bucket

### **Next Phase Integration**
- Lambda functions will read/write to these resources
- AppSync resolvers will query DynamoDB and Athena
- Frontend will access data through API layer
- MCP tools will use the same data sources

---

**This reference guide should be updated as the infrastructure evolves through subsequent phases.** 