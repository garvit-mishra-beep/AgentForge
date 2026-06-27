"""AgentForge evaluation framework.

Behavioral regression evals for the agent layer: structured-output contracts,
reviewer verdict behavior, aggregator decision logic, and injection resistance.
Cases are deterministic (mock providers) so they run in CI without Ollama; a live
mode can drive real models for periodic quality tracking.
"""
