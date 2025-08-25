"""
Health Check Lambda Function
Monitors system health and sends alerts using Lambda Powertools
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize Powertools
logger = Logger(service=os.getenv("POWERTOOLS_SERVICE_NAME", "opendata-pulse-health-check"))
tracer = Tracer(service=os.getenv("POWERTOOLS_SERVICE_NAME", "opendata-pulse-health-check"))
metrics = Metrics(namespace=os.getenv("POWERTOOLS_METRICS_NAMESPACE", "OpenDataPulse/HealthCheck"))

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')
sns_client = boto3.client('sns')

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Main handler for health check monitoring
    """
    try:
        logger.info("Starting health check", extra={
            "event_type": "health_check_started",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Add custom metrics
        metrics.add_metric(name="HealthCheckAttempts", unit="Count", value=1)
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {}
        }
        
        # Check S3 buckets (placeholder)
        try:
            # TODO: Check if S3 buckets are accessible
            health_status["checks"]["s3"] = "healthy"
            logger.info("S3 health check passed")
        except Exception as e:
            health_status["checks"]["s3"] = "unhealthy"
            logger.error(f"S3 health check failed: {e}")
            health_status["status"] = "degraded"
        
        # Check DynamoDB table (placeholder)
        try:
            # TODO: Check if DynamoDB table is accessible
            health_status["checks"]["dynamodb"] = "healthy"
            logger.info("DynamoDB health check passed")
        except Exception as e:
            health_status["checks"]["dynamodb"] = "unhealthy"
            logger.error(f"DynamoDB health check failed: {e}")
            health_status["status"] = "degraded"
        
        # Check NSW API connectivity (placeholder)
        try:
            # TODO: Check NSW Air Quality API connectivity
            health_status["checks"]["nsw_api"] = "healthy"
            logger.info("NSW API health check passed")
        except Exception as e:
            health_status["checks"]["nsw_api"] = "unhealthy"
            logger.error(f"NSW API health check failed: {e}")
            health_status["status"] = "degraded"
        
        # Add health metrics
        healthy_checks = sum(1 for check in health_status["checks"].values() if check == "healthy")
        total_checks = len(health_status["checks"])
        
        metrics.add_metric(name="HealthyChecks", unit="Count", value=healthy_checks)
        metrics.add_metric(name="TotalChecks", unit="Count", value=total_checks)
        
        # Send health status notification if degraded
        if health_status["status"] == "degraded":
            notification_message = {
                "status": "degraded",
                "service": "health-check",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "health_status": health_status
            }
            
            try:
                sns_client.publish(
                    TopicArn=os.getenv("NOTIFICATION_TOPIC_ARN"),
                    Message=json.dumps(notification_message),
                    Subject="OpenData Pulse - System Health Degraded"
                )
                logger.warning("Health check detected degraded status, notification sent")
            except Exception as notification_error:
                logger.error(f"Failed to send health notification: {notification_error}")
        
        logger.info("Health check completed", extra={
            "event_type": "health_check_completed",
            "health_status": health_status["status"],
            "healthy_checks": healthy_checks,
            "total_checks": total_checks
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(health_status)
        }
        
    except Exception as e:
        logger.exception("Error in health check", extra={
            "event_type": "health_check_error",
            "error": str(e)
        })
        
        # Add error metrics
        metrics.add_metric(name="HealthCheckErrors", unit="Count", value=1)
        
        # Send error notification
        error_message = {
            "status": "error",
            "service": "health-check",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
        
        try:
            sns_client.publish(
                TopicArn=os.getenv("NOTIFICATION_TOPIC_ARN"),
                Message=json.dumps(error_message),
                Subject="OpenData Pulse - Health Check Error"
            )
        except Exception as notification_error:
            logger.error(f"Failed to send error notification: {notification_error}")
        
        raise 