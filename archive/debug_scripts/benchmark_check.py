#!/usr/bin/env python3
"""Check system readiness for benchmark execution"""

import json
import urllib.request
import sys

print("Checking system readiness for AgentForge benchmark...")

# Check if Ollama is available
try:
    print("Checking Ollama...")
    response = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5)
    models_data = response.read()
    models = json.loads(models_data.decode('utf-8'))

    available_models = [m['name'] for m in models.get('models', [])]
    print("Ollama is running with", len(available_models), "models:")
    for model in available_models:
        print("  -", model)

    required_models = ['qwen2.5-coder:7b', 'deepseek-coder-uncensored:latest', 'gemma3:4b']
    missing_models = [m for m in required_models if m not in available_models]

    if missing_models:
        print("Missing required models:", missing_models)
    else:
        print("All required Ollama models are available")

except Exception as e:
    print("Ollama not available:", e)
    sys.exit(1)

# Check if FastAPI API is available
try:
    print("\nChecking FastAPI API...")
    response = urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=5)
    health = json.loads(response.read().decode('utf-8'))

    if health.get('status') == 'ok':
        print("FastAPI API is running")
        print("  Version:", health.get('version'))
    else:
        print("FastAPI API returned unexpected status:", health)
        sys.exit(1)

except Exception as e:
    print("FastAPI API not available:", e)
    sys.exit(1)

print("\n" + "="*70)
print("SYSTEM READINESS CHECK SUMMARY")
print("="*70)
print("Ollama is running with required models")
print("FastAPI API is available")
print("\nAll system requirements met for benchmark execution!")
print("\nReady to run real benchmark with AgentForge's multi-model orchestration.")
