"""
AWS Bedrock Integration for SecurityMesh AI
Autonomous Multi-Agent Threat Intelligence Platform

This module provides integration with Amazon Bedrock for foundation model access,
enabling natural language threat analysis across multiple AI models.

Supported Models:
- Claude 3.5 Sonnet (Anthropic)
- Titan Text/Embeddings (Amazon)
- Jurassic-2 (AI21 Labs)

Development assisted by Amazon Kiro IDE:
- Architecture design and AWS service selection
- Code optimization and best practices review
- Error handling and retry logic implementation
- Performance tuning recommendations
- Connection pooling strategies for cost optimization
- Security best practices and IAM policy design

Built for AWS Global Vibe AI Coding Hackathon 2025
"""

import json
import boto3
import asyncio
from typing import Dict, List, Optional, Any
from botocore.config import Config
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class BedrockAgent:
    """
    AWS Bedrock integration for SecurityMesh AI agents.

    Features:
    - Multi-model support (Claude, Titan, Jurassic)
    - Streaming responses
    - Automatic retry with exponential backoff
    - Cost tracking
    - Rate limiting
    """

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name: str = "us-east-1",
        max_retries: int = 3
    ):
        """
        Initialize Bedrock agent.

        Args:
            model_id: Bedrock model identifier
            region_name: AWS region
            max_retries: Maximum retry attempts
        """
        self.model_id = model_id
        self.region_name = region_name

        # Configure boto3 client with retry logic
        config = Config(
            region_name=region_name,
            retries={
                'max_attempts': max_retries,
                'mode': 'adaptive'
            },
            connect_timeout=30,
            read_timeout=300
        )

        self.client = boto3.client(
            service_name='bedrock-runtime',
            config=config
        )

        self.bedrock = boto3.client(
            service_name='bedrock',
            config=config
        )

        # Cost tracking
        self.request_count = 0
        self.token_count = 0

    async def analyze_threat(
        self,
        threat_data: Dict[str, Any],
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Analyze security threat using Bedrock foundation model.

        Args:
            threat_data: Threat information (CVE, indicators, context)
            max_tokens: Maximum response tokens
            temperature: Model temperature (0.0-1.0)

        Returns:
            Analysis results with severity, impact, remediation
        """
        try:
            # Build analysis prompt
            prompt = self._build_threat_analysis_prompt(threat_data)

            # Call appropriate model
            if "claude" in self.model_id.lower():
                response = await self._invoke_claude(prompt, max_tokens, temperature)
            elif "titan" in self.model_id.lower():
                response = await self._invoke_titan(prompt, max_tokens, temperature)
            elif "jurassic" in self.model_id.lower():
                response = await self._invoke_jurassic(prompt, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported model: {self.model_id}")

            # Parse and structure response
            analysis = self._parse_threat_analysis(response)

            # Update metrics
            self.request_count += 1
            self.token_count += analysis.get('token_count', 0)

            return analysis

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Threat analysis error: {e}")
            raise

    async def _invoke_claude(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Invoke Claude model via Bedrock."""
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body
        )

        response_body = json.loads(response['body'].read())
        return response_body

    async def _invoke_titan(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Invoke Amazon Titan model via Bedrock."""
        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body
        )

        response_body = json.loads(response['body'].read())
        return response_body

    async def _invoke_jurassic(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Invoke AI21 Jurassic model via Bedrock."""
        body = json.dumps({
            "prompt": prompt,
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": 0.9
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body
        )

        response_body = json.loads(response['body'].read())
        return response_body

    async def stream_threat_analysis(
        self,
        threat_data: Dict[str, Any],
        max_tokens: int = 2000,
        temperature: float = 0.3
    ):
        """
        Stream threat analysis results in real-time.

        Args:
            threat_data: Threat information
            max_tokens: Maximum response tokens
            temperature: Model temperature

        Yields:
            Analysis chunks as they're generated
        """
        try:
            prompt = self._build_threat_analysis_prompt(threat_data)

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })

            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=body
            )

            # Stream response chunks
            for event in response['body']:
                chunk = json.loads(event['chunk']['bytes'])
                if 'delta' in chunk and 'text' in chunk['delta']:
                    yield chunk['delta']['text']

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        model_id: str = "amazon.titan-embed-text-v1"
    ) -> List[List[float]]:
        """
        Generate embeddings for threat intelligence data.

        Args:
            texts: List of text strings to embed
            model_id: Embeddings model ID

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for text in texts:
            body = json.dumps({
                "inputText": text
            })

            response = self.client.invoke_model(
                modelId=model_id,
                body=body
            )

            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding', [])
            embeddings.append(embedding)

        return embeddings

    def _build_threat_analysis_prompt(self, threat_data: Dict[str, Any]) -> str:
        """Build structured prompt for threat analysis."""
        cve_id = threat_data.get('cve_id', 'Unknown')
        description = threat_data.get('description', '')
        severity = threat_data.get('severity', 'Unknown')
        affected_systems = threat_data.get('affected_systems', [])
        indicators = threat_data.get('indicators', {})

        prompt = f"""You are a cybersecurity threat analyst. Analyze the following security threat and provide a comprehensive assessment.

**Threat Information:**
- CVE ID: {cve_id}
- Severity: {severity}
- Description: {description}
- Affected Systems: {', '.join(affected_systems) if affected_systems else 'Unknown'}
- Indicators of Compromise: {json.dumps(indicators, indent=2)}

**Required Analysis:**

1. **Threat Classification:**
   - Attack vector (Network/Adjacent/Local/Physical)
   - Attack complexity (Low/High)
   - Privileges required (None/Low/High)
   - User interaction (None/Required)
   - Scope (Unchanged/Changed)

2. **Impact Assessment:**
   - Confidentiality impact (None/Low/High)
   - Integrity impact (None/Low/High)
   - Availability impact (None/Low/High)
   - Business impact score (0-100)

3. **Exploitability Analysis:**
   - Is exploit code publicly available?
   - Has this been exploited in the wild?
   - What is the likelihood of exploitation? (Low/Medium/High)
   - Time to exploitation estimate

4. **Remediation Recommendations:**
   - Immediate actions (within 24 hours)
   - Short-term fixes (within 1 week)
   - Long-term solutions (within 1 month)
   - Compensating controls if patch unavailable

5. **Detection Strategies:**
   - YARA rules
   - SIEM detection queries
   - Network signatures
   - EDR/XDR indicators

Provide your analysis in JSON format with all fields populated."""

        return prompt

    def _parse_threat_analysis(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure model response."""
        # Extract text from response based on model
        if 'content' in response:
            # Claude response format
            text = response['content'][0]['text']
            token_count = response.get('usage', {}).get('total_tokens', 0)
        elif 'results' in response:
            # Titan response format
            text = response['results'][0]['outputText']
            token_count = response.get('inputTextTokenCount', 0) + response.get('outputTextTokenCount', 0)
        elif 'completions' in response:
            # Jurassic response format
            text = response['completions'][0]['data']['text']
            token_count = response['completions'][0].get('tokens', {}).get('total', 0)
        else:
            text = str(response)
            token_count = 0

        # Try to parse JSON from response
        try:
            # Extract JSON if embedded in markdown
            if '```json' in text:
                json_start = text.find('```json') + 7
                json_end = text.find('```', json_start)
                json_text = text[json_start:json_end].strip()
            elif '{' in text and '}' in text:
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                json_text = text[json_start:json_end]
            else:
                json_text = text

            analysis = json.loads(json_text)
            analysis['token_count'] = token_count
            analysis['raw_response'] = text

        except json.JSONDecodeError:
            # Fallback to raw text if JSON parsing fails
            analysis = {
                'raw_response': text,
                'token_count': token_count,
                'parsed': False
            }

        return analysis

    def get_metrics(self) -> Dict[str, Any]:
        """Get usage metrics for cost tracking."""
        return {
            'request_count': self.request_count,
            'token_count': self.token_count,
            'model_id': self.model_id,
            'region': self.region_name
        }

    async def batch_analyze_threats(
        self,
        threats: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple threats concurrently with rate limiting.

        Args:
            threats: List of threat data dictionaries
            max_concurrent: Maximum concurrent requests

        Returns:
            List of analysis results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(threat):
            async with semaphore:
                return await self.analyze_threat(threat)

        tasks = [analyze_with_semaphore(threat) for threat in threats]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful_results = [
            r for r in results if not isinstance(r, Exception)
        ]

        return successful_results


class BedrockAgentOrchestrator:
    """
    Orchestrates multiple Bedrock agents for parallel threat analysis.

    Features:
    - Multi-model consensus (Claude + Titan + Jurassic)
    - Confidence scoring
    - Result aggregation
    """

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize orchestrator with multiple model agents."""
        self.agents = {
            'claude': BedrockAgent(
                model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                region_name=region_name
            ),
            'titan': BedrockAgent(
                model_id="amazon.titan-text-express-v1",
                region_name=region_name
            ),
            'jurassic': BedrockAgent(
                model_id="ai21.j2-ultra-v1",
                region_name=region_name
            )
        }

    async def analyze_with_consensus(
        self,
        threat_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze threat using multiple models and aggregate results.

        Args:
            threat_data: Threat information

        Returns:
            Consensus analysis with confidence scores
        """
        # Analyze with all models in parallel
        tasks = {
            name: agent.analyze_threat(threat_data)
            for name, agent in self.agents.items()
        }

        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )

        # Aggregate results
        consensus = self._aggregate_results(
            dict(zip(tasks.keys(), results))
        )

        return consensus

    def _aggregate_results(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate multi-model results with confidence scoring."""
        # Filter successful results
        valid_results = {
            name: result
            for name, result in results.items()
            if not isinstance(result, Exception)
        }

        if not valid_results:
            return {'error': 'All models failed', 'results': results}

        # Extract severity scores
        severities = []
        for result in valid_results.values():
            if 'severity' in result:
                severities.append(result['severity'])

        # Calculate consensus
        consensus = {
            'model_count': len(valid_results),
            'models_used': list(valid_results.keys()),
            'individual_results': valid_results,
            'consensus_severity': max(set(severities), key=severities.count) if severities else 'Unknown',
            'confidence': len(severities) / len(self.agents) if severities else 0.0
        }

        return consensus

    def get_total_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics across all agents."""
        total_requests = sum(
            agent.request_count for agent in self.agents.values()
        )
        total_tokens = sum(
            agent.token_count for agent in self.agents.values()
        )

        return {
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'agents': {
                name: agent.get_metrics()
                for name, agent in self.agents.items()
            }
        }


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize agent
        agent = BedrockAgent(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        # Example threat data
        threat_data = {
            'cve_id': 'CVE-2024-1234',
            'description': 'Remote code execution vulnerability in web application',
            'severity': 'CRITICAL',
            'affected_systems': ['Apache 2.4.x', 'Nginx 1.20.x'],
            'indicators': {
                'ip_addresses': ['192.168.1.100'],
                'file_hashes': ['abc123...'],
                'domains': ['malicious.example.com']
            }
        }

        # Analyze threat
        print("Analyzing threat with AWS Bedrock...")
        analysis = await agent.analyze_threat(threat_data)
        print(json.dumps(analysis, indent=2))

        # Get metrics
        metrics = agent.get_metrics()
        print(f"\nMetrics: {metrics}")

    # Run async main
    asyncio.run(main())
