"""
AWS Lambda Handler for SecurityMesh AI Agents
Serverless agent execution with auto-scaling and distributed memory

This Lambda function handles:
- Individual agent execution (Gemini, Writer, Rewriter, etc.)
- DynamoDB memory access
- EventBridge communication
- Step Functions orchestration
"""

import json
import os
import asyncio
from typing import Dict, Any
import boto3
from bedrock_integration import BedrockAgent

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')
s3 = boto3.client('s3')

# Environment variables
MEMORY_TABLE = os.environ.get('MEMORY_TABLE', 'agent-memory')
EVENT_BUS = os.environ.get('EVENT_BUS', 'agent-communication')
THREAT_BUCKET = os.environ.get('THREAT_BUCKET', 'threat-intelligence-data')


class LambdaAgent:
    """Lambda-based security agent with distributed memory."""

    def __init__(self, agent_type: str):
        """
        Initialize Lambda agent.

        Args:
            agent_type: Type of agent (gemini, writer, rewriter, etc.)
        """
        self.agent_type = agent_type
        self.bedrock = BedrockAgent()
        self.memory_table = dynamodb.Table(MEMORY_TABLE)

    async def execute(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task.

        Args:
            event: Lambda event containing task data

        Returns:
            Agent execution results
        """
        task_id = event.get('task_id')
        task_type = event.get('task_type')
        task_data = event.get('data', {})

        print(f"Agent {self.agent_type} executing task {task_id} ({task_type})")

        # Load agent memory
        memory = await self._load_memory()

        # Execute based on task type
        if task_type == 'threat_analysis':
            result = await self._analyze_threat(task_data, memory)
        elif task_type == 'cve_enrichment':
            result = await self._enrich_cve(task_data, memory)
        elif task_type == 'report_generation':
            result = await self._generate_report(task_data, memory)
        else:
            result = {'error': f'Unknown task type: {task_type}'}

        # Update memory
        await self._save_memory(memory, result)

        # Publish results to EventBridge
        await self._publish_result(task_id, result)

        return result

    async def _analyze_threat(
        self,
        threat_data: Dict[str, Any],
        memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze threat using Bedrock."""
        # Use Bedrock for analysis
        analysis = await self.bedrock.analyze_threat(threat_data)

        # Add context from memory
        if 'similar_threats' in memory:
            analysis['historical_context'] = memory['similar_threats'][:5]

        return {
            'status': 'success',
            'analysis': analysis,
            'agent': self.agent_type
        }

    async def _enrich_cve(
        self,
        cve_data: Dict[str, Any],
        memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich CVE with additional intelligence."""
        cve_id = cve_data.get('cve_id')

        # Check if already enriched
        if cve_id in memory.get('enriched_cves', {}):
            print(f"Using cached enrichment for {cve_id}")
            return memory['enriched_cves'][cve_id]

        # Enrich with Bedrock
        enrichment = await self.bedrock.analyze_threat(cve_data)

        # Store in memory cache
        if 'enriched_cves' not in memory:
            memory['enriched_cves'] = {}
        memory['enriched_cves'][cve_id] = enrichment

        return {
            'status': 'success',
            'cve_id': cve_id,
            'enrichment': enrichment,
            'agent': self.agent_type
        }

    async def _generate_report(
        self,
        report_data: Dict[str, Any],
        memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate security report."""
        report_type = report_data.get('type', 'summary')
        threats = report_data.get('threats', [])

        # Generate report with Bedrock
        prompt = f"""Generate a {report_type} security report for the following threats:

{json.dumps(threats, indent=2)}

Include:
- Executive summary
- Threat breakdown
- Risk assessment
- Recommendations
"""

        report = await self.bedrock._invoke_claude(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.3
        )

        # Save report to S3
        report_key = f"reports/{report_data.get('report_id', 'unknown')}.json"
        s3.put_object(
            Bucket=THREAT_BUCKET,
            Key=report_key,
            Body=json.dumps(report, indent=2)
        )

        return {
            'status': 'success',
            'report_location': f"s3://{THREAT_BUCKET}/{report_key}",
            'agent': self.agent_type
        }

    async def _load_memory(self) -> Dict[str, Any]:
        """Load agent memory from DynamoDB."""
        try:
            response = self.memory_table.get_item(
                Key={'agent_id': self.agent_type}
            )
            return response.get('Item', {}).get('memory', {})
        except Exception as e:
            print(f"Memory load error: {e}")
            return {}

    async def _save_memory(
        self,
        memory: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """Save updated memory to DynamoDB."""
        try:
            # Update memory with new knowledge
            if 'recent_tasks' not in memory:
                memory['recent_tasks'] = []

            memory['recent_tasks'].append({
                'timestamp': boto3.dynamodb.types.Decimal(str(asyncio.get_event_loop().time())),
                'result_summary': str(result)[:500]
            })

            # Keep only last 100 tasks
            memory['recent_tasks'] = memory['recent_tasks'][-100:]

            # Save to DynamoDB
            self.memory_table.put_item(
                Item={
                    'agent_id': self.agent_type,
                    'memory': memory
                }
            )
        except Exception as e:
            print(f"Memory save error: {e}")

    async def _publish_result(self, task_id: str, result: Dict[str, Any]):
        """Publish result to EventBridge for other agents."""
        try:
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': f'securitymesh.agent.{self.agent_type}',
                        'DetailType': 'AgentTaskComplete',
                        'Detail': json.dumps({
                            'task_id': task_id,
                            'agent': self.agent_type,
                            'result': result
                        }),
                        'EventBusName': EVENT_BUS
                    }
                ]
            )
        except Exception as e:
            print(f"Event publish error: {e}")


def lambda_handler(event, context):
    """
    AWS Lambda handler for agent execution.

    Event Format:
    {
        "agent_type": "gemini",
        "task_id": "task-123",
        "task_type": "threat_analysis",
        "data": {
            "cve_id": "CVE-2024-1234",
            "description": "..."
        }
    }

    Returns:
        Agent execution results
    """
    print(f"Lambda invoked with event: {json.dumps(event)}")

    # Extract agent type
    agent_type = event.get('agent_type', 'gemini')

    # Initialize agent
    agent = LambdaAgent(agent_type)

    # Execute task (wrap async in sync for Lambda)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(agent.execute(event))

    return {
        'statusCode': 200,
        'body': json.dumps(result),
        'headers': {
            'Content-Type': 'application/json'
        }
    }


# For local testing
if __name__ == "__main__":
    test_event = {
        'agent_type': 'gemini',
        'task_id': 'test-123',
        'task_type': 'threat_analysis',
        'data': {
            'cve_id': 'CVE-2024-1234',
            'description': 'Remote code execution vulnerability',
            'severity': 'CRITICAL',
            'affected_systems': ['Apache 2.4.x']
        }
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
