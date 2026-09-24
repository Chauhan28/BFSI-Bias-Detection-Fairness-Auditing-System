# ===== explanation_consistency.py =====
import json
from data_loader import load_json_file, get_sample_test_cases
from ollama_client import evaluate_applicant
from prompt_engine import generate_counterfactuals_for_case

def test_consistency(test_case, num_retests=3):
    """Test same profile multiple times to check consistency"""
    
    test_id = test_case['id']
    cf_result = generate_counterfactuals_for_case(test_case)
    
    original_prompt = cf_result['original']['prompt']
    
    # Test same profile N times
    decisions = []
    explanations = []
    
    print(f"  Testing {test_id}...")
    
    for attempt in range(num_retests):
        result = evaluate_applicant(original_prompt)
        decisions.append(result['decision'])
        explanations.append(result['reasoning'][:100])  # First 100 chars
    
    # Check consistency
    all_same_decision = len(set(decisions)) == 1
    
    # Check explanation similarity (simple word overlap)
    words_sets = [set(exp.lower().split()) for exp in explanations]
    common_words = words_sets[0].intersection(words_sets[1]).intersection(words_sets[2])
    total_words = words_sets[0].union(words_sets[1]).union(words_sets[2])
    
    similarity = len(common_words) / len(total_words) if total_words else 0
    
    # Calculate consistency score
    consistency_score = 0
    if all_same_decision:
        consistency_score += 50
    if similarity > 0.5:
        consistency_score += 50
    
    result = {
        'test_id': test_id,
        'decisions': decisions,
        'all_decisions_same': all_same_decision,
        'explanation_similarity': round(similarity, 2),
        'consistency_score': consistency_score,
        'status': '✅ CONSISTENT' if consistency_score > 70 else '⚠️  INCONSISTENT'
    }
    
    print(f"    Score: {consistency_score}/100 - {result['status']}")
    return result


def analyze_consistency(num_profiles=30):
    """Analyze consistency on N profiles"""
    
    print("\n" + "="*70)
    print(f"EXPLANATION CONSISTENCY TEST ({num_profiles} profiles)")
    print("="*70 + "\n")
    
    data = load_json_file('data/bfsi_test_cases.json')
    test_cases = get_sample_test_cases(data, num_samples=num_profiles)
    
    all_results = []
    
    for test_case in test_cases:
        result = test_consistency(test_case, num_retests=3)
        all_results.append(result)
    
    # Calculate metrics
    print("\n" + "="*70)
    print("CONSISTENCY ANALYSIS RESULTS")
    print("="*70 + "\n")
    
    avg_score = sum(r['consistency_score'] for r in all_results) / len(all_results)
    consistent_count = len([r for r in all_results if r['all_decisions_same']])
    avg_similarity = sum(r['explanation_similarity'] for r in all_results) / len(all_results)
    
    print(f"Overall Consistency Score: {avg_score:.1f}/100")
    print(f"Decision Consistency: {consistent_count}/{len(all_results)} ({consistent_count/len(all_results)*100:.1f}%)")
    print(f"Average Explanation Similarity: {avg_similarity:.2f}/1.0")
    
    if avg_score > 80:
        print("\n✅ Model is RELIABLE")
    elif avg_score > 60:
        print("\n⚠️  Model has some consistency issues")
    else:
        print("\n❌ Model is UNRELIABLE")
    
    # Save results
    with open('results/consistency_analysis.json', 'w') as f:
        json.dump({
            'overall_score': round(avg_score, 2),
            'decision_consistency_rate': round(consistent_count/len(all_results)*100, 2),
            'explanation_similarity': round(avg_similarity, 2),
            'profiles_tested': len(all_results),
            'detailed_results': all_results
        }, f, indent=2)
    
    print(f"\n✅ Results saved to results/consistency_analysis.json\n")
    return all_results


if __name__ == "__main__":
    print("\n=== EXPLANATION CONSISTENCY ANALYZER ===\n")
    analyze_consistency(num_profiles=30)