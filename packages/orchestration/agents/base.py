import logging
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract Base Class for all LLM agents in AgentOS."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Invoke the agent with a prompt and system instruction."""
        pass


class OpenAIAgent(BaseAgent):
    """Agent implementing OpenAI / GPT-4 model connections."""
    async def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model=self.model_name or "gpt-4o",
            openai_api_base=self.base_url
        )
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = await llm.ainvoke(messages)
        return response.content


class GeminiAgent(BaseAgent):
    """Agent implementing Google Gemini model connections."""
    async def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.model_name or "gemini-1.5-flash"
        )
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = await llm.ainvoke(messages)
        return response.content


class ClaudeAgent(BaseAgent):
    """Agent implementing Anthropic Claude model connections."""
    async def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatAnthropic(
            anthropic_api_key=self.api_key,
            model=self.model_name or "claude-3-5-sonnet-20240620"
        )
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = await llm.ainvoke(messages)
        return response.content


class MockAgent(BaseAgent):
    """Fallback high-fidelity mock agent matching context templates for flawless pitch/demo runs."""
    
    def __init__(self, role: str):
        super().__init__(model_name="mock-agent")
        self.role = role

    async def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        logger.info(f"MockAgent fallback invoked for role: {self.role}")
        
        # Determine prompt keywords to customize mock output
        prompt_lower = prompt.lower()
        
        if self.role == "planner":
            # Return plan phases matching project prompt
            title = "Sample Application"
            if "todo" in prompt_lower:
                title = "FastAPI + React Todo App with JWT"
            elif "auth" in prompt_lower:
                title = "JWT Authentication Service"
            elif "e-commerce" in prompt_lower or "store" in prompt_lower:
                title = "E-Commerce Backend Gateway"
                
            plan = {
                "objective": f"Architect and construct {title}",
                "phases": [
                    {
                        "name": "Database Schema & Entity Models",
                        "description": "Establish tables, constraints, and index declarations",
                        "estimated_hours": 3
                    },
                    {
                        "name": "Core Service handlers & REST APIs",
                        "description": "Write implementation logic, routes, and validations",
                        "estimated_hours": 6
                    },
                    {
                        "name": "Integration Test Cases & Mock suite",
                        "description": "Develop full test suite verifying edge conditions",
                        "estimated_hours": 3
                    }
                ]
            }
            return json.dumps(plan)
            
        elif self.role == "coder":
            # Return source and test files matching prompt
            file_prefix = "todo" if "todo" in prompt_lower else "auth" if "auth" in prompt_lower else "app"
            artifacts = {
                "artifacts": [
                    {
                        "type": "source_file",
                        "name": f"src/{file_prefix}_handler.py",
                        "content": f"# Generated by Coder Agent\nimport jwt\nimport datetime\n\nclass {file_prefix.title()}Handler:\n    def __init__(self, secret_key: str = 'super-secret'):\n        self.secret_key = secret_key\n        self.db = []\n\n    def process_item(self, item: dict) -> dict:\n        \"\"\"Process and record data with simple input checks\"\"\"\n        if not item.get('name'):\n            raise ValueError('Name field is required.')\n            \n        # Simulation check logic\n        if 'test_fail' in item:\n            # Simulated validation bug to trigger testing fail loop\n            pass\n            \n        item['id'] = len(self.db) + 1\n        item['created_at'] = datetime.datetime.utcnow().isoformat()\n        self.db.append(item)\n        return item\n"
                    },
                    {
                        "type": "unit_tests",
                        "name": f"tests/test_{file_prefix}_handler.py",
                        "content": f"import unittest\nfrom src.{file_prefix}_handler import {file_prefix.title()}Handler\n\nclass Test{file_prefix.title()}(unittest.TestCase):\n    def setUp(self):\n        self.handler = {file_prefix.title()}Handler()\n\n    def test_process_success(self):\n        res = self.handler.process_item({{'name': 'Buy milk'}})\n        self.assertEqual(res['id'], 1)\n        self.assertIsNotNone(res['created_at'])\n\n    def test_missing_name_fail(self):\n        with self.assertRaises(ValueError):\n            self.handler.process_item({{}})\n"
                    },
                    {
                        "type": "readme",
                        "name": "README.md",
                        "content": f"# {file_prefix.title()} Service\n\nGenerated by AgentOS AI Team.\n\n## Setup & Run\n1. Install dependencies\n2. Run handler functions\n"
                    }
                ]
            }
            return json.dumps(artifacts)
            
        elif self.role == "tester":
            # Return test results
            results = {
                "status": "passed",
                "failures": [],
                "logs": [
                    "TestRunner starting checks...",
                    "Running tests/test_handler.py",
                    "test_process_success ... OK",
                    "test_missing_name_fail ... OK",
                    "SUCCESS: All 2 tests passed successfully. Coverage: 98%"
                ]
            }
            if "fail_test" in prompt_lower:
                results["status"] = "failed"
                results["failures"] = ["test_process_success failed: expected 1 got None"]
                results["logs"] = [
                    "TestRunner starting checks...",
                    "Running tests/test_handler.py",
                    "test_process_success ... FAILED (expected 1 got None)",
                    "test_missing_name_fail ... OK",
                    "FAILURE: 1 of 2 tests failed."
                ]
            return json.dumps(results)
            
        elif self.role == "reviewer":
            # Return code review
            review = {
                "status": "approved",
                "quality_score": 95,
                "coverage": 98,
                "complexity": 2,
                "comments": [
                    "Optimal database session controls and security policies.",
                    "Comprehensive unit tests cover boundary logic."
                ]
            }
            if "reject_review" in prompt_lower:
                review["status"] = "rejected"
                review["quality_score"] = 65
                review["rejection_reason"] = "Missing JWT token signature checks in handler initialization"
                review["improvements"] = [
                    "Inject and validate JWT secret key parameter.",
                    "Verify token expiration parameters."
                ]
            return json.dumps(review)

        return "Mock Response"
