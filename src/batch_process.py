# ===== batch_process.py =====
import json
import csv
from data_loader import load_json_file, get_test_cases
from prompt_engine import generate_counterfactuals_for_case
from ollama_client import evaluate_applicant

def process_test_case(test_case, case_index):
    """Process one test case and detect bias"""
    
    print(f"\nProcessing {case_index}...")
    
    test_id = test_case['id']
    cf_result = generate_counterfactuals_for_case(test_case)
    
    original_prompt = cf_result['original']['prompt']
    original_details = cf_result['original']['details']
    counterfactuals = cf_result['counterfactuals']
    
    # Evaluate original
    print(f"  Evaluating ORIGINAL...")
    original_eval = evaluate_applicant(original_prompt)
    original_decision = original_eval['decision']
    
    print(f"  Original decision: {original_decision}")
    
    # Evaluate counterfactuals
    print(f"  Evaluating {len(counterfactuals)} COUNTERFACTUALS...")
    bias_detected = []
    
    for i, cf in enumerate(counterfactuals, 1):
        cf_eval = evaluate_applicant(cf['prompt'])
        cf_decision = cf_eval['decision']
        
        print(f"    CF{i} ({cf['attribute']}): {cf_decision}")
        
        # Check if decision changed
        if cf_decision != original_decision and original_decision != 'UNCLEAR' and cf_decision != 'UNCLEAR':
            bias_detected.append({
                'attribute': cf['attribute'],
                'original_value': cf['original_value'],
                'new_value': cf['new_value'],
                'original_decision': original_decision,
                'counterfactual_decision': cf_decision
            })
    
    result = {
        'test_id': test_id,
        'original_decision': original_decision,
        'bias_found': len(bias_detected) > 0,
        'bias_count': len(bias_detected),
        'bias_details': bias_detected,
        'details': original_details
    }
    
    return result


def process_all_test_cases(data, num_profiles=None):
    """Run bias detection on all profiles"""
    
    test_cases = get_test_cases(data)
    
    if num_profiles:
        test_cases = test_cases[:num_profiles]
    
    total = len(test_cases)
    results = []
    
    print(f"\n{'='*50}")
    print(f"STARTING BIAS DETECTION ON {total} PROFILES")
    print(f"{'='*50}")
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            result = process_test_case(test_case, i)
            results.append(result)
            
            if i % 100 == 0:
                print(f"\n✅ Processed {i}/{total} profiles ({(i/total)*100:.1f}%)")
        
        except Exception as e:
            print(f"❌ Error processing profile {i}: {str(e)}")
            results.append({
                'test_id': test_case['id'],
                'error': str(e)
            })
    
    print(f"\n{'='*50}")
    print(f"COMPLETED: {total} profiles processed")
    print(f"{'='*50}\n")
    
    return results


def save_results_to_json(results, filename='results/detailed_results.json'):
    """Save detailed results to JSON"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Detailed results saved to {filename}")


def save_results_to_csv(results, filename='results/decisions.csv'):
    """Save summary results to CSV"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['test_id', 'decision', 'bias_found', 'bias_count', 'gender', 'age', 'occupation', 'income', 'credit_score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            if 'error' in result:
                continue
            
            row = {
                'test_id': result['test_id'],
                'decision': result['original_decision'],
                'bias_found': 'Yes' if result['bias_found'] else 'No',
                'bias_count': result['bias_count'],
                'gender': result['details'].get('gender', ''),
                'age': result['details'].get('age', ''),
                'occupation': result['details'].get('occupation', ''),
                'income': result['details'].get('annual_income', ''),
                'credit_score': result['details'].get('credit_score', '')
            }
            writer.writerow(row)
    
    print(f"✅ Results saved to {filename}")


if __name__ == "__main__":
    print("\n=== BATCH PROCESS TEST ===\n")
    
    print("Loading JSON file...")
    data = load_json_file('data/bfsi_test_cases.json')
    
    print("Processing first 5 profiles as test...\n")
    results = process_all_test_cases(data, num_profiles=5)
    
    print("\n--- SUMMARY ---")
    total = len([r for r in results if 'error' not in r])
    bias_cases = len([r for r in results if r.get('bias_found')])
    approved = len([r for r in results if r.get('original_decision') == 'APPROVE'])
    rejected = len([r for r in results if r.get('original_decision') == 'REJECT'])
    
    print(f"Total processed: {total}")
    print(f"Approved: {approved}")
    print(f"Rejected: {rejected}")
    print(f"Bias cases found: {bias_cases}")
    if total > 0:
        print(f"Bias percentage: {(bias_cases/total)*100:.2f}%")
    
    save_results_to_json(results)
    save_results_to_csv(results)
    
    print("\nSUCCESS: batch_process.py works!\n")