#!/usr/bin/env python3
"""Simple test to verify the AgentForge benchmark framework"""

import asyncio
import sys

# Test the framework import
print("Testing framework import...")

try:
    from apps.api.benchmark_simplified import ScientificBenchmarkSimplified
    print("Framework imported successfully")
except ImportError as e:
    print(f"Failed to import framework: {e}")
    sys.exit(1)

# Test basic initialization
print("\nTesting initialization...")
try:
    benchmark = ScientificBenchmarkSimplified(
        db_url="postgresql://agentforge:agentforge@localhost:5432/agentforge",
        api_base="http://localhost:8000/api/v1"
    )
    print("Initialization successful")
    print("  - Tasks defined:", len(benchmark.tasks))
    print("  - Conditions:", list(benchmark.conditions.keys()))
    
    # Test analysis function
    test_condition_results = {
        'A': {'avg_score': 75.5, 'successful_tasks': 4, 'tasks_completed': 5},
        'B': {'avg_score': 78.2, 'successful_tasks': 4, 'tasks_completed': 5},
        'C': {'avg_score': 85.3, 'successful_tasks': 5, 'tasks_completed': 5},
        'D': {'avg_score': 76.8, 'successful_tasks': 4, 'tasks_completed': 5},
    }
    
    analysis = benchmark._analyze_results(test_condition_results)
    
    print("\nTest Analysis Results:")
    print("  Best Single Model:", analysis['best_single_model'])
    print("  AgentForge Team Score:", format(analysis['team_score'], '.1f'))
    print("  Team vs Single Delta:", format(analysis['team_vs_single']['percent'], '+.1f'), '%')
    print("  Success Criteria Met:", analysis['success_criteria_met'])
    print("  Collaboration Benefit:", format(analysis['collaboration_benefit'], '.1f'), "points")
    
    # Test success criteria
    if analysis['success_criteria_met']:
        print("\nSUCCESS CRITERIA MET - Team outperforms single models!")
    else:
        print("\nFAIL SUCCESS CRITERIA - Team does not demonstrate superiority")
        
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("BENCHMARK FRAMEWORK VALIDATION COMPLETE")
print("="*70)
print("\nThe AgentForge Scientific Benchmark framework is ready for execution!")
print("\nTo run the full benchmark:")
print("  cd apps/api")
print("  python benchmark_simplified.py")
print("\nFor the full scientific version:")
print("  python benchmark_scientific.py")
print("\nSee BENCHMARK_README.md for detailed instructions.")