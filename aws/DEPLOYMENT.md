# SecurityMesh AI - AWS Deployment Guide
## AWS Global Vibe AI Coding Hackathon 2025

This guide will help you deploy SecurityMesh AI to AWS Account **732782171072** for the hackathon submission.

---

## Prerequisites

### 1. AWS Account Setup
- AWS Account ID: **732782171072**
- AWS Region: **us-east-1** (recommended)
- IAM user with administrator access or equivalent permissions

### 2. Install Required Tools

**AWS CLI:**
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version  # Should show aws-cli/2.x.x or higher
```

**AWS SAM CLI:**
```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Verify installation
sam --version  # Should show SAM CLI, version 1.x.x or higher
```

**Python 3.11:**
```bash
# Check Python version
python3 --version  # Should be 3.11.x

# If not installed:
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip
```

### 3. Configure AWS Credentials

```bash
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json
```

Verify configuration:
```bash
aws sts get-caller-identity

# Should return:
# {
#     "UserId": "...",
#     "Account": "732782171072",
#     "Arn": "..."
# }
```

---

## Deployment Steps

### Step 1: Clone Repository and Checkout Branch

```bash
# Clone the repository
git clone https://github.com/reconsumeralization/unified-intelligence-platform.git
cd unified-intelligence-platform

# Checkout hackathon branch
git checkout aws-global-vibe-2025

# Verify you're on the correct branch
git branch  # Should show: * aws-global-vibe-2025
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r aws/requirements.txt

# Verify installation
pip list | grep boto3  # Should show boto3==1.34.162
```

### Step 3: Enable AWS Bedrock Models

Before deploying, ensure Bedrock models are enabled in your AWS account:

```bash
# Navigate to AWS Console → Bedrock → Model access
# Or use CLI:
aws bedrock list-foundation-models --region us-east-1

# Request access to required models:
# - anthropic.claude-3-5-sonnet-20241022-v2:0
# - amazon.titan-text-express-v1
# - ai21.j2-ultra-v1
```

**Important:** Model access approval can take a few minutes. Proceed once approved.

### Step 4: Build SAM Application

```bash
# Navigate to AWS directory
cd aws

# Build the SAM application
sam build

# Expected output:
# Building codeuri: ...
# Running PythonPipBuilder:ResolveDependencies
# Build Succeeded
```

### Step 5: Deploy to AWS

```bash
# Deploy with guided prompts
sam deploy --guided

# You will be prompted:
# - Stack Name: securitymesh-ai-prod
# - AWS Region: us-east-1
# - Parameter BedrockModelId: anthropic.claude-3-5-sonnet-20241022-v2:0
# - Parameter DeploymentStage: prod
# - Confirm changes before deploy: Y
# - Allow SAM CLI IAM role creation: Y
# - Allow Lambda Function URL: N
# - Save arguments to configuration file: Y
# - SAM configuration file: samconfig.toml
# - SAM configuration environment: prod
```

Deployment will take **10-15 minutes**. Expected output:
```
CloudFormation stack changeset
---------------------------------
Operation       LogicalResourceId                   ResourceType
---------------------------------
+ Add           AgentMemoryTable                     AWS::DynamoDB::Table
+ Add           ThreatIntelligenceTable              AWS::DynamoDB::Table
+ Add           TaskQueueTable                       AWS::DynamoDB::Table
+ Add           ThreatIntelligenceBucket             AWS::S3::Bucket
+ Add           AgentEventBus                        AWS::Events::EventBus
+ Add           GeminiAgentFunction                  AWS::Lambda::Function
+ Add           WriterAgentFunction                  AWS::Lambda::Function
+ Add           RewriterAgentFunction                AWS::Lambda::Function
+ Add           TranslatorAgentFunction              AWS::Lambda::Function
+ Add           SummarizerAgentFunction              AWS::Lambda::Function
+ Add           ProofreaderAgentFunction             AWS::Lambda::Function
+ Add           LanguageDetectorAgentFunction        AWS::Lambda::Function
+ Add           PromptGeneratorAgentFunction         AWS::Lambda::Function
+ Add           ThreatAnalysisAgentFunction          AWS::Lambda::Function
+ Add           ThreatAnalysisStateMachine           AWS::StepFunctions::StateMachine
+ Add           ThreatIntelligenceApi                AWS::ApiGateway::RestApi
---------------------------------

Changeset created successfully. arn:aws:cloudformation:...

2024-11-06 10:00:00 | CREATE_IN_PROGRESS   | AWS::CloudFormation::Stack   | securitymesh-ai-prod
...
[10-15 minutes of resource creation logs]
...
2024-11-06 10:15:00 | CREATE_COMPLETE      | AWS::CloudFormation::Stack   | securitymesh-ai-prod

Successfully created/updated stack - securitymesh-ai-prod in us-east-1
```

### Step 6: Verify Deployment

```bash
# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name securitymesh-ai-prod \
  --region us-east-1 \
  --query 'Stacks[0].Outputs'

# Should return:
# [
#   {
#     "OutputKey": "ApiEndpoint",
#     "OutputValue": "https://xxxxx.execute-api.us-east-1.amazonaws.com/prod"
#   },
#   {
#     "OutputKey": "GeminiAgentArn",
#     "OutputValue": "arn:aws:lambda:us-east-1:732782171072:function:securitymesh-gemini-agent-prod"
#   },
#   ...
# ]
```

---

## Testing the Deployment

### Test 1: Invoke Lambda Agent Directly

```bash
# Test Gemini agent
aws lambda invoke \
  --function-name securitymesh-gemini-agent-prod \
  --region us-east-1 \
  --payload '{"agent_type":"gemini","task_id":"test-001","task_type":"threat_analysis","data":{"cve_id":"CVE-2024-1234","description":"Remote code execution","severity":"CRITICAL","affected_systems":["Apache 2.4.x"]}}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json | python3 -m json.tool
```

Expected output:
```json
{
  "statusCode": 200,
  "body": "{\"status\":\"success\",\"analysis\":{...},\"agent\":\"gemini\"}",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Test 2: Execute Step Functions Workflow

```bash
# Get State Machine ARN
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name securitymesh-ai-prod \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

# Start execution
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --region us-east-1 \
  --input '{
    "task_id": "test-workflow-001",
    "cve_id": "CVE-2024-5678",
    "data": {
      "cve_id": "CVE-2024-5678",
      "description": "SQL injection vulnerability in web application",
      "severity": "HIGH",
      "affected_systems": ["PostgreSQL 14.x", "MySQL 8.x"],
      "indicators": {
        "ip_addresses": ["192.168.1.100"],
        "file_hashes": ["abc123def456"],
        "domains": ["malicious.example.com"]
      }
    }
  }' \
  --name test-workflow-$(date +%s)

# View execution status
aws stepfunctions describe-execution \
  --execution-arn [ARN from previous command] \
  --region us-east-1
```

### Test 3: Query DynamoDB Tables

```bash
# Check agent memory
aws dynamodb scan \
  --table-name securitymesh-agent-memory-prod \
  --region us-east-1 \
  --max-items 10

# Check threat intelligence
aws dynamodb scan \
  --table-name securitymesh-threat-intelligence-prod \
  --region us-east-1 \
  --max-items 10
```

### Test 4: Verify S3 Buckets

```bash
# List buckets
aws s3 ls | grep securitymesh

# Expected output:
# securitymesh-threat-data-732782171072
# securitymesh-agent-logs-732782171072

# Check bucket contents
aws s3 ls s3://securitymesh-threat-data-732782171072/reports/
```

---

## Monitoring and Observability

### CloudWatch Logs

```bash
# View Gemini agent logs
aws logs tail /aws/lambda/securitymesh-gemini-agent-prod \
  --follow \
  --region us-east-1

# View all Lambda function logs
for func in gemini writer rewriter translator summarizer proofreader langdetect promptgen threatanalysis; do
  echo "=== $func agent logs ==="
  aws logs tail /aws/lambda/securitymesh-$func-agent-prod \
    --since 5m \
    --region us-east-1
done
```

### CloudWatch Metrics

```bash
# Get Lambda invocation metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=securitymesh-gemini-agent-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-1

# Get error metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=securitymesh-gemini-agent-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

### EventBridge Events

```bash
# List event rules
aws events list-rules \
  --event-bus-name securitymesh-agent-communication-prod \
  --region us-east-1

# Put test event
aws events put-events \
  --entries file://test-event.json \
  --region us-east-1
```

Create `test-event.json`:
```json
[
  {
    "Source": "securitymesh.test",
    "DetailType": "TestEvent",
    "Detail": "{\"message\":\"Test event from deployment\"}",
    "EventBusName": "securitymesh-agent-communication-prod"
  }
]
```

---

## Cost Monitoring

### Estimated Monthly Costs (Moderate Load: 1000 threats/day)

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| AWS Bedrock | 30K requests | ~$45 |
| Lambda | 3M invocations | ~$20 |
| DynamoDB | On-demand | ~$15 |
| S3 | 100GB storage | ~$2 |
| Step Functions | 1K executions | ~$25 |
| EventBridge | 100K events | ~$1 |
| API Gateway | 10K requests | ~$0.04 |
| CloudWatch | Logs & metrics | ~$5 |
| **Total** | | **~$113/month** |

**Note:** Actual costs may vary. Monitor with AWS Cost Explorer.

### Set Up Cost Alerts

```bash
# Create budget alert
aws budgets create-budget \
  --account-id 732782171072 \
  --budget file://budget.json \
  --region us-east-1
```

Create `budget.json`:
```json
{
  "BudgetName": "SecurityMeshAI-Monthly-Budget",
  "BudgetLimit": {
    "Amount": "150",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

---

## Troubleshooting

### Issue: Bedrock InvokeModel Access Denied

**Error:**
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the InvokeModel operation
```

**Solution:**
1. Navigate to AWS Console → Bedrock → Model access
2. Request access to required models
3. Wait for approval (usually < 5 minutes)
4. Redeploy if needed

### Issue: Lambda Timeout

**Error:**
```
Task timed out after 300.00 seconds
```

**Solution:**
```bash
# Increase timeout (up to 900 seconds)
aws lambda update-function-configuration \
  --function-name securitymesh-gemini-agent-prod \
  --timeout 600 \
  --region us-east-1
```

### Issue: DynamoDB Throttling

**Error:**
```
ProvisionedThroughputExceededException
```

**Solution:**
Tables use on-demand capacity, but if throttling occurs:
```bash
# Check current capacity mode
aws dynamodb describe-table \
  --table-name securitymesh-agent-memory-prod \
  --region us-east-1 \
  --query 'Table.BillingModeSummary'

# Already on-demand, throttling should not occur
# If it does, check for burst traffic or increase WCU/RCU
```

### Issue: Step Functions Execution Failed

**Check execution history:**
```bash
aws stepfunctions get-execution-history \
  --execution-arn [EXECUTION_ARN] \
  --region us-east-1 \
  --max-results 100
```

---

## Cleanup (After Hackathon)

**WARNING:** This will delete all resources and data. Only run after hackathon judging is complete.

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack \
  --stack-name securitymesh-ai-prod \
  --region us-east-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name securitymesh-ai-prod \
  --region us-east-1

# Empty and delete S3 buckets (not automatically deleted)
aws s3 rm s3://securitymesh-threat-data-732782171072 --recursive
aws s3 rb s3://securitymesh-threat-data-732782171072

aws s3 rm s3://securitymesh-agent-logs-732782171072 --recursive
aws s3 rb s3://securitymesh-agent-logs-732782171072

# Verify deletion
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE \
  --region us-east-1 | grep securitymesh-ai-prod
```

---

## Next Steps

1. **Register for Hackathon:** https://dorahacks.io/hackathon/awsvibecoding/detail
2. **Record Demo Video:** Follow VIDEO_SCRIPT.md
3. **Take Screenshots:** Dashboard, agents, analysis results
4. **Submit to Devpost:** Use DEVPOST.md content
5. **Submit by Dec 1, 2025**

---

## Support

For deployment issues:
- **GitHub Issues:** https://github.com/reconsumeralization/unified-intelligence-platform/issues
- **AWS Support:** https://console.aws.amazon.com/support/

---

**Deployment Status:** Production-ready
**Last Updated:** November 6, 2025
**AWS Account:** 732782171072
**Hackathon:** AWS Global Vibe AI Coding 2025
