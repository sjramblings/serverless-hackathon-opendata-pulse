# ApiStack Reference Guide
## OpenData Pulse Authentication & API Infrastructure

This document provides quick reference information for the ApiStack resources deployed in Task 1.3.

---

## 🔐 **Cognito User Pool**

### **User Pool Details**
- **Name**: `opendata-pulse-users`
- **ID**: Available in CloudFormation outputs
- **Region**: Same as deployment region
- **Status**: Active

### **Authentication Features**
- **Self Sign-up**: ✅ Enabled
- **Email Verification**: ✅ Required
- **MFA**: ✅ Optional (SMS/OTP)
- **Device Tracking**: ✅ Enabled
- **Account Recovery**: ✅ Email-only

### **Password Policy**
- **Minimum Length**: 8 characters
- **Requirements**: Uppercase, lowercase, digits, symbols
- **Expiration**: Not set (can be configured)

### **User Attributes**
```json
{
  "email": "user@example.com",           // Required
  "given_name": "John",                  // Optional
  "family_name": "Doe",                  // Optional
  "phone_number": "+61412345678",        // Optional
  "custom:region_preference": "Sydney",  // Custom
  "custom:subscription_level": "basic"   // Custom
}
```

---

## 📱 **App Client**

### **Client Details**
- **Name**: `opendata-pulse-web-client`
- **Type**: Public client (no secret)
- **Provider**: Cognito only
- **Callback URLs**: 
  - `http://localhost:3000/callback`
  - `https://*.amplifyapp.com/callback`

### **OAuth Scopes**
- `email`: User's email address
- `openid`: OpenID Connect standard
- `profile`: User profile information

---

## 🆔 **Identity Pool**

### **Pool Details**
- **Name**: `opendata-pulse-identity-pool`
- **Unauthenticated Access**: ❌ Disabled
- **Identity Providers**: Cognito User Pool only

### **Role Mapping**
```
Authenticated Users → AuthenticatedRole
Unauthenticated Users → UnauthenticatedRole
```

---

## 🗄️ **AppSync GraphQL API**

### **API Details**
- **Name**: `opendata-pulse-api`
- **Authentication**: Cognito User Pool
- **Authorization**: JWT tokens
- **X-Ray Tracing**: ✅ Enabled
- **Schema**: NSW air quality data

### **GraphQL Endpoint**
```
https://{api-id}.appsync-api.{region}.amazonaws.com/graphql
```

### **Authentication Headers**
```javascript
{
  "Authorization": "Bearer {jwt_token}",
  "Content-Type": "application/json"
}
```

---

## 🛡️ **WAF Web ACL**

### **ACL Details**
- **Name**: `OpenDataPulseWebACL`
- **Scope**: Regional
- **Default Action**: Allow
- **Monitoring**: CloudWatch metrics enabled

### **Protection Features**
- **DDoS Protection**: Basic
- **Attack Detection**: Can be enhanced with rules
- **Rate Limiting**: Can be added
- **IP Filtering**: Can be configured

---

## 🔑 **IAM Roles**

### **Authenticated Role**
- **Name**: `AuthenticatedUserRole`
- **Trust Policy**: Cognito Identity Pool
- **Permissions**: AppSync access, CloudWatch logs
- **Use Case**: Authenticated users accessing API

### **Unauthenticated Role**
- **Name**: `UnauthenticatedUserRole`
- **Trust Policy**: Cognito Identity Pool
- **Permissions**: Minimal (for future use)
- **Use Case**: Public access (if enabled later)

---

## 🔧 **Common Operations**

### **User Management**
```bash
# List users
aws cognito-idp list-users --user-pool-id {user-pool-id}

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id {user-pool-id} \
  --username "user@example.com" \
  --user-attributes Name=email,Value="user@example.com" \
  --temporary-password "TempPass123!"

# Confirm user
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id {user-pool-id} \
  --username "user@example.com"
```

### **AppSync Operations**
```bash
# List APIs
aws appsync list-graphql-apis

# Get API details
aws appsync get-graphql-api --api-id {api-id}

# Test query (requires authentication)
curl -X POST \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { health }"}' \
  {graphql-url}
```

### **WAF Operations**
```bash
# List Web ACLs
aws wafv2 list-web-acls --scope REGIONAL

# Get Web ACL details
aws wafv2 get-web-acl --name OpenDataPulseWebACL --scope REGIONAL --id {acl-id}
```

---

## 📊 **CloudFormation Outputs**

After deployment, the stack provides these outputs:

```bash
# Get all outputs
aws cloudformation describe-stacks \
  --stack-name OpenDataPulseApiStack \
  --query 'Stacks[0].Outputs'

# Get specific outputs
aws cloudformation describe-stacks \
  --stack-name OpenDataPulseApiStack \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text
```

### **Available Outputs**
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito User Pool Client ID
- `IdentityPoolId`: Cognito Identity Pool ID
- `GraphQLApiUrl`: AppSync GraphQL API URL
- `GraphQLApiId`: AppSync GraphQL API ID
- `WebACLId`: WAF Web ACL ID

---

## 🔐 **Security & Permissions**

### **Authentication Flow**
1. User signs up with email
2. Email verification required
3. User signs in with credentials
4. Cognito returns JWT tokens
5. Tokens used for AppSync API access

### **Authorization**
- **AppSync**: Requires valid JWT token
- **WAF**: Regional protection layer
- **IAM**: Role-based access control
- **Encryption**: All data encrypted in transit

### **Security Best Practices**
- ✅ Strong password policy
- ✅ Email verification required
- ✅ Optional MFA support
- ✅ Device tracking enabled
- ✅ WAF protection active
- ✅ Least privilege IAM roles

---

## 💰 **Cost Optimization**

### **Cognito Costs**
- **User Pool**: $0.0055 per MAU (Monthly Active User)
- **MFA SMS**: $0.0064 per SMS
- **Storage**: Free for standard attributes

### **AppSync Costs**
- **Queries**: $4.00 per million queries
- **Data Transfer**: $0.09 per GB
- **Real-time**: $2.00 per million real-time updates

### **WAF Costs**
- **Web ACL**: $5.00 per month
- **Requests**: $0.60 per million requests
- **Rule Groups**: $1.00 per rule group per month

### **Estimated Monthly Costs**
- **10 users**: ~$5-10/month
- **100 users**: ~$10-20/month
- **1000 users**: ~$20-50/month

---

## 🚨 **Monitoring & Alerts**

### **Recommended CloudWatch Alarms**
```bash
# Cognito authentication failures
aws cloudwatch put-metric-alarm \
  --alarm-name "Cognito-AuthFailures" \
  --metric-name AuthFailures \
  --namespace AWS/Cognito \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold

# AppSync 4xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name "AppSync-4xxErrors" \
  --metric-name 4xxError \
  --namespace AWS/AppSync \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## 🔄 **Integration Points**

### **Frontend Integration**
```javascript
// Amplify configuration
const awsconfig = {
  Auth: {
    region: 'ap-southeast-2',
    userPoolId: 'ap-southeast-2_xxxxxxxxx',
    userPoolWebClientId: 'xxxxxxxxxxxxxxxxxxxxxxxxxx',
    identityPoolId: 'ap-southeast-2:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
  },
  API: {
    graphql_endpoint: 'https://xxxxxxxxxx.appsync-api.ap-southeast-2.amazonaws.com/graphql',
    graphql_headers: async () => ({
      'x-api-key': 'da2-xxxxxxxxxxxxxxxxxxxxxxxxxx'
    })
  }
};
```

### **Lambda Integration**
```python
import boto3
import jwt

def lambda_handler(event, context):
    # Verify JWT token
    token = event['headers']['Authorization'].replace('Bearer ', '')
    
    # Decode token (verify with Cognito)
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    # Extract user information
    user_id = decoded['sub']
    email = decoded['email']
    
    # Process request
    return {
        'statusCode': 200,
        'body': f'Hello {email}!'
    }
```

---

## 🚀 **Next Phase Integration**

### **Phase 2 Integration**
- Lambda functions will use Cognito tokens for authentication
- Data pipeline will access S3/DynamoDB through IAM roles
- Frontend will integrate with Cognito for user management
- MCP tools will use API keys or service roles

### **Phase 3 Integration**
- Gen-AI layer will authenticate through Cognito
- Real-time subscriptions will use authenticated connections
- User preferences will be stored in Cognito attributes
- Analytics will track authenticated user behavior

---

**This reference guide should be updated as the infrastructure evolves through subsequent phases.** 