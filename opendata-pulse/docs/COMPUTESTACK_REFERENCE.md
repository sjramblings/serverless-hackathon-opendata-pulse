# ComputeStack Reference Guide
## OpenData Pulse Lambda Infrastructure

This document provides quick reference information for the ComputeStack resources deployed in Task 1.4.

---

## 🚀 **Lambda Functions**

### **Data Ingestion Function**
- **Name**: `opendata-pulse-ingest-{hash}`
- **Runtime**: Python 3.9
- **Handler**: `index.handler`
- **Timeout**: 5 minutes
- **Memory**: 512 MB
- **Schedule**: Every hour via EventBridge
- **Purpose**: Fetches NSW Air Quality data

### **ETL Processing Function**
- **Name**: `opendata-pulse-etl-{hash}`
- **Runtime**: Python 3.9
- **Handler**: `index.handler`
- **Timeout**: 10 minutes
- **Memory**: 1024 MB
- **Trigger**: Manual or S3 events
- **Purpose**: Processes raw data into curated format

### **Health Check Function**
- **Name**: `opendata-pulse-health-check-{hash}`
- **Runtime**: Python 3.9
- **Handler**: `index.handler`
- **Timeout**: 1 minute
- **Memory**: 128 MB
- **Schedule**: Every 5 minutes via EventBridge
- **Purpose**: Monitors system health

---

## 📦 **Lambda Layers**

### **Common Layer**
- **Path**: `lambda-functions/layers/common`
- **Dependencies**: boto3, requests, pandas, pyarrow, python-dateutil
- **Purpose**: Shared dependencies for all functions

### **Powertools Layer**
- **Path**: `lambda-functions/layers/powertools`
- **Dependencies**: aws-lambda-powertools[all]
- **Purpose**: Observability, logging, tracing, metrics

---

## ⏰ **EventBridge Rules**

### **Data Ingestion Rule**
- **Name**: `OpenDataPulseDataIngestionRule`
- **Schedule**: `rate(1 hour)`
- **Target**: Data Ingestion Lambda Function
- **Description**: Triggers data collection every hour

### **Health Check Rule**
- **Name**: `OpenDataPulseHealthCheckRule`
- **Schedule**: `rate(5 minutes)`
- **Target**: Health Check Lambda Function
- **Description**: Monitors system health every 5 minutes

---

## 📨 **SNS Notification Topic**

### **Topic Details**
- **Name**: `opendata-pulse-notifications`
- **Display Name**: OpenData Pulse Notifications
- **Purpose**: Success/error notifications for all functions

### **Notification Types**
- **Success Notifications**: Data ingestion, ETL processing
- **Error Notifications**: Function failures, processing errors
- **Health Alerts**: System degradation, connectivity issues

---

## 📬 **SQS Dead Letter Queue**

### **Queue Details**
- **Name**: `opendata-pulse-processing-dlq`
- **Retention**: 14 days
- **Purpose**: Captures failed Lambda executions
- **Monitoring**: CloudWatch metrics and alarms

---

## 🔑 **IAM Roles**

### **Lambda Execution Role**
- **Name**: `OpenDataPulseLambdaExecutionRole`
- **Trust Policy**: Lambda service principal
- **Managed Policies**:
  - `AWSLambdaBasicExecutionRole`
  - `AWSLambdaVPCAccessExecutionRole`
- **Custom Permissions**:
  - S3 read/write access
  - SNS publish permissions
  - DynamoDB access
  - SQS send/receive permissions

---

## 🔧 **Common Operations**

### **Lambda Function Management**
```bash
# List functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `opendata-pulse`)].FunctionName'

# Get function details
aws lambda get-function --function-name {function-name}

# Update function code
aws lambda update-function-code \
  --function-name {function-name} \
  --zip-file fileb://function.zip

# Test function
aws lambda invoke \
  --function-name {function-name} \
  --payload '{}' \
  response.json
```

### **EventBridge Rule Management**
```bash
# List rules
aws events list-rules --name-prefix "OpenDataPulse"

# Get rule details
aws events describe-rule --name {rule-name}

# Enable/disable rules
aws events enable-rule --name {rule-name}
aws events disable-rule --name {rule-name}
```

### **SNS Topic Management**
```bash
# List topics
aws sns list-topics --query 'Topics[?contains(TopicArn, `opendata-pulse`)].TopicArn'

# Publish message
aws sns publish \
  --topic-arn {topic-arn} \
  --message "Test message" \
  --subject "Test Subject"

# List subscriptions
aws sns list-subscriptions-by-topic --topic-arn {topic-arn}
```

### **SQS Queue Management**
```bash
# Get queue URL
aws sqs get-queue-url --queue-name opendata-pulse-processing-dlq

# Get queue attributes
aws sqs get-queue-attributes \
  --queue-url {queue-url} \
  --attribute-names All

# Purge queue (if needed)
aws sqs purge-queue --queue-url {queue-url}
```

---

## 📊 **CloudFormation Outputs**

After deployment, the stack provides these outputs:

```bash
# Get all outputs
aws cloudformation describe-stacks \
  --stack-name OpenDataPulseComputeStack \
  --query 'Stacks[0].Outputs'

# Get specific outputs
aws cloudformation describe-stacks \
  --stack-name OpenDataPulseComputeStack \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestFunctionName`].OutputValue' \
  --output text
```

### **Available Outputs**
- `IngestFunctionName`: Data ingestion Lambda function name
- `ETLFunctionName`: ETL processing Lambda function name
- `HealthCheckFunctionName`: Health check Lambda function name
- `NotificationTopicArn`: SNS notification topic ARN
- `DLQUrl`: SQS Dead Letter Queue URL

---

## 🔍 **Monitoring & Observability**

### **CloudWatch Logs**
```bash
# Get log groups
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/opendata-pulse"

# Get recent log events
aws logs filter-log-events \
  --log-group-name "/aws/lambda/opendata-pulse-ingest" \
  --start-time $(date -d '1 hour ago' +%s)000

# Export logs
aws logs create-export-task \
  --log-group-name "/aws/lambda/opendata-pulse-ingest" \
  --from 1640995200000 \
  --to 1641081600000 \
  --destination "s3://your-bucket/logs/" \
  --destination-prefix "opendata-pulse-logs"
```

### **CloudWatch Metrics**
```bash
# Get custom metrics
aws cloudwatch list-metrics \
  --namespace "OpenDataPulse/Ingest" \
  --metric-name "IngestionAttempts"

# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace "OpenDataPulse/Ingest" \
  --metric-name "IngestionAttempts" \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### **X-Ray Tracing**
```bash
# Get trace summaries
aws xray get-trace-summaries \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s)

# Get trace details
aws xray get-trace --trace-id {trace-id}
```

---

## 🚨 **Alerts & Notifications**

### **Recommended CloudWatch Alarms**
```bash
# Lambda error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "Lambda-ErrorRate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value={function-name}

# DLQ message count alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "DLQ-MessageCount" \
  --metric-name ApproximateNumberOfVisibleMessages \
  --namespace AWS/SQS \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=QueueName,Value=opendata-pulse-processing-dlq
```

---

## 🔄 **Lambda Powertools Usage**

### **Environment Variables**
```bash
# Set for all functions
POWERTOOLS_SERVICE_NAME=opendata-pulse-{function-type}
POWERTOOLS_METRICS_NAMESPACE=OpenDataPulse/{FunctionType}
LOG_LEVEL=INFO
```

### **Logger Configuration**
```python
from aws_lambda_powertools import Logger

logger = Logger(service=os.getenv("POWERTOOLS_SERVICE_NAME"))

@logger.inject_lambda_context
def handler(event, context):
    logger.info("Processing started", extra={
        "event_type": "processing_started",
        "data_points": len(data)
    })
```

### **Metrics Configuration**
```python
from aws_lambda_powertools import Metrics

metrics = Metrics(namespace=os.getenv("POWERTOOLS_METRICS_NAMESPACE"))

@metrics.log_metrics
def handler(event, context):
    metrics.add_metric(name="RecordsProcessed", unit="Count", value=100)
```

### **Tracer Configuration**
```python
from aws_lambda_powertools import Tracer

tracer = Tracer(service=os.getenv("POWERTOOLS_SERVICE_NAME"))

@tracer.capture_lambda_handler
def handler(event, context):
    # Automatic X-Ray tracing
    pass
```

---

## 💰 **Cost Optimization**

### **Lambda Optimization**
- **Memory Allocation**: Optimize based on function requirements
- **Timeout Settings**: Set appropriate timeouts
- **Concurrency Limits**: Configure based on expected load
- **Provisioned Concurrency**: For predictable workloads

### **Monitoring Costs**
- **Log Retention**: Configure appropriate retention periods
- **Metrics Filtering**: Use custom metrics sparingly
- **X-Ray Sampling**: Enable sampling for high-volume functions

### **Estimated Costs**
- **Lambda**: $0.20 per 1M requests + $0.0000166667 per GB-second
- **EventBridge**: $1.00 per million events
- **SQS**: $0.40 per million requests
- **SNS**: $0.50 per million publishes
- **CloudWatch**: $0.50 per million custom metrics

---

## 🔐 **Security & Permissions**

### **IAM Best Practices**
- **Least Privilege**: Minimal required permissions
- **Resource-based Policies**: Use for cross-service access
- **Condition Keys**: Restrict access based on conditions
- **Regular Audits**: Review permissions periodically

### **Environment Security**
- **Environment Variables**: No sensitive data in plain text
- **Secrets Manager**: Use for sensitive configuration
- **VPC Access**: Configure if needed for private resources
- **Encryption**: All data encrypted in transit and at rest

---

## 🚀 **Next Phase Integration**

### **Phase 2 Integration**
- Lambda functions will integrate with DataStack resources
- ETL pipeline will process actual NSW air quality data
- Health checks will monitor real API connectivity
- Notifications will include actual processing results

### **Phase 3 Integration**
- Gen-AI functions will use Lambda Powertools
- Real-time processing will be added
- Advanced monitoring and alerting
- Performance optimization and scaling

---

**This reference guide should be updated as the infrastructure evolves through subsequent phases.** 