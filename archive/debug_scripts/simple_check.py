#!/usr/bin/env python3
import sys

# Simple test to import the benchmark
print("Testing benchmark framework import...")

try:
    sys.path.insert(0, 'apps/api')
    from benchmark_simplified import ScientificBenchmarkSimplified
    print("✅ Successfully imported ScientificBenchmarkSimplified")
    
    # Test initialization
    benchmark = ScientificBenchmarkSimplified(
        db_url="postgresql://agentforge:agentforge@localhost:5432/agentforge",
        api_base="http://localhost:8000/api/v1"
    )
    print("✅ Successfully initialized ScientificBenchmarkSimplified")
    
    # Print basic information
    print(f"  - Tasks defined: {len(benchmark.tasks)}")
    print(f"  - Conditions: {list(benchmark.conditions.keys())}")
    
    # Test analysis function
    test_condition_results = {
        'A': {'avg_score': 75.5, 'successful_tasks': 4, 'tasks_completed': 5},
        'B': {'avg_score': 78.2, 'successful_tasks': 4, 'tasks_completed': 5},
        'C': {'avg_score': 85.3, 'successful_tasks': 5, 'tasks_completed': 5},
        'D': {'avg_score': 76.8, 'successful_tasks': 4, 'tasks_completed': 5},
    }
    
    analysis = benchmark._analyze_results(test_condition_results)
    
    print("\nTest Analysis Results:")
    print(f"  Best Single Model: {analysis['best_single_model']}")
    print(f"  AgentForge Team Score: {analysis['team_score']:.1f}")
    print(f"  Team vs Single Delta: {analysis['team_vs_single']['percent']:+.1f}%")
    print(f"  Success Criteria Met: {analysis['success_criteria_met']}")
    print(f"  Collaboration Benefit: {analysis['collaboration_benefit']:.1f} points")
    
    # Test success criteria
    if analysis['success_criteria_met']:
        print("\n✅ SUCCESS CRITERIA MET - Team outperforms single models!")
    else:
        print("\n❌ FAIL SUCCESS CRITERIA - Team does not demonstrate superiority")
        
    print("\n✅ All tests passed successfully!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)