# ===== bias_calculator.py =====
import json
from collections import defaultdict

def load_detailed_results(filename='results/detailed_results.json'):
    """Load detailed results from JSON"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {filename} not found. Run batch_process.py first.")
        return []


def calculate_bias_metrics(results):
    """Calculate bias metrics from results"""
    
    total = len([r for r in results if 'error' not in r])
    bias_by_attribute = defaultdict(lambda: {'count': 0, 'cases': []})
    decision_counts = {'APPROVE': 0, 'REJECT': 0, 'UNCLEAR': 0}
    total_bias_cases = 0
    
    for result in results:
        if 'error' in result:
            continue
        
        decision = result.get('original_decision', 'UNCLEAR')
        if decision in decision_counts:
            decision_counts[decision] += 1
        
        if result.get('bias_found'):
            total_bias_cases += 1
            for bias in result.get('bias_details', []):
                attr = bias['attribute']
                bias_by_attribute[attr]['count'] += 1
                bias_by_attribute[attr]['cases'].append({
                    'test_id': result['test_id'],
                    'original_value': bias['original_value'],
                    'new_value': bias['new_value'],
                    'decision_changed': f"{bias['original_decision']} → {bias['counterfactual_decision']}"
                })
    
    metrics = {
        'total_profiles': total,
        'total_bias_cases': total_bias_cases,
        'overall_bias_percentage': round((total_bias_cases / total * 100), 2) if total > 0 else 0,
        'decision_distribution': {
            'approved': {'count': decision_counts['APPROVE'], 'percentage': round((decision_counts['APPROVE'] / total * 100), 2) if total > 0 else 0},
            'rejected': {'count': decision_counts['REJECT'], 'percentage': round((decision_counts['REJECT'] / total * 100), 2) if total > 0 else 0},
            'unclear': {'count': decision_counts['UNCLEAR'], 'percentage': round((decision_counts['UNCLEAR'] / total * 100), 2) if total > 0 else 0},
        },
        'bias_by_attribute': {}
    }
    
    for attribute, data in sorted(bias_by_attribute.items()):
        count = data['count']
        percentage = round((count / total * 100), 2) if total > 0 else 0
        metrics['bias_by_attribute'][attribute] = {
            'count': count,
            'percentage': percentage,
            'examples': data['cases'][:2]
        }
    
    return metrics


def save_metrics(metrics, filename='results/metrics.json'):
    """Save metrics to JSON"""
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Metrics saved to {filename}")


def print_metrics(metrics):
    """Print metrics in human-readable format"""
    
    print("\n" + "="*60)
    print("BIAS DETECTION METRICS REPORT")
    print("="*60 + "\n")
    
    print(f"Total Profiles Tested: {metrics['total_profiles']}")
    print(f"Bias Cases Found: {metrics['total_bias_cases']}")
    print(f"Overall Bias Rate: {metrics['overall_bias_percentage']:.2f}%")
    
    print("\n--- DECISION DISTRIBUTION ---")
    for decision, data in metrics['decision_distribution'].items():
        print(f"{decision.upper():10s}: {data['count']:4d} ({data['percentage']:6.2f}%)")
    
    if metrics['bias_by_attribute']:
        print("\n--- BIAS BY ATTRIBUTE ---")
        for attribute, data in metrics['bias_by_attribute'].items():
            print(f"{attribute.upper():15s}: {data['count']:3d} cases ({data['percentage']:6.2f}%)")
    else:
        print("\n⚠️  No bias detected by attribute")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("\n=== BIAS CALCULATOR ===\n")
    
    print("Loading detailed results...")
    results = load_detailed_results()
    
    if not results:
        print("No results found. Run batch_process.py first.")
    else:
        print(f"Loaded {len(results)} results")
        
        print("Calculating metrics...")
        metrics = calculate_bias_metrics(results)
        
        print_metrics(metrics)
        save_metrics(metrics)
        
        print("SUCCESS: bias_calculator.py works!\n")