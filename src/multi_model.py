# ===== free_multi_model_comparison.py =====
import json
import requests
from data_loader import load_json_file, get_sample_test_cases, get_test_cases
from prompt_engine import generate_counterfactuals_for_case
from ollama_client import parse_decision

# ===== MODEL 1: OLLAMA LLAMA2 =====
def query_ollama_llama2(prompt):
    """Query Ollama llama2"""
    try:
        payload = {
            "model": "llama2",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get('response', '')
        return None
    except:
        return None


# ===== MODEL 2: OLLAMA MISTRAL =====
def query_ollama_mistral(prompt):
    """Query Ollama mistral"""
    try:
        payload = {
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get('response', '')
        return None
    except:
        return None


# ===== MODEL 3: GOOGLE GEMINI FLASH =====
        
        
def query_gemini_flash(prompt):
    """Query Google Gemini Flash (faster & cheaper)"""
    try:
        import google.generativeai as genai
        
        # Use environment variable instead of hardcoded key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("ERROR: Set GOOGLE_API_KEY environment variable")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

# ===== TEST ONE PROFILE =====
def test_profile_on_model(test_case, model_name, query_func):
    """Test one profile on a model"""
    
    test_id = test_case['id']
    cf_result = generate_counterfactuals_for_case(test_case)
    
    original_prompt = cf_result['original']['prompt']
    counterfactuals = cf_result['counterfactuals']
    
    # Evaluate original
    original_response = query_func(original_prompt)
    if not original_response:
        return None
    
    original_decision = parse_decision(original_response)['decision']
    
    # Evaluate counterfactuals
    bias_cases = 0
    
    for cf in counterfactuals:
        cf_response = query_func(cf['prompt'])
        if cf_response:
            cf_decision = parse_decision(cf_response)['decision']
            
            if (cf_decision != original_decision and 
                original_decision != 'UNCLEAR' and 
                cf_decision != 'UNCLEAR'):
                bias_cases += 1
    
    return {
        'test_id': test_id,
        'original_decision': original_decision,
        'bias_cases': bias_cases,
        'bias_percentage': (bias_cases / len(counterfactuals) * 100) if counterfactuals else 0
    }


# ===== MAIN COMPARISON =====
def compare_free_models(num_profiles=20):
    """Compare all 3 free models"""
    
    print("\n" + "="*70)
    print(f"FREE MULTI-MODEL COMPARISON ({num_profiles} profiles)")
    print("="*70 + "\n")
    
    data = load_json_file('data/bfsi_test_cases.json')
    all_test_cases = get_test_cases(data)
    test_cases = all_test_cases[:num_profiles]
    
    models = {
        'ollama-llama2': query_ollama_llama2,
        'ollama-mistral': query_ollama_mistral,
        'gemini-flash': query_gemini_flash  # Using Flash!
    }
    
    all_results = {}
    
    for model_name, query_func in models.items():
        print(f"Testing {model_name.upper()}...")
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"  Profile {i}/{num_profiles}...", end='\r')
            result = test_profile_on_model(test_case, model_name, query_func)
            if result:
                results.append(result)
        
        if results:
            total_bias = sum(r['bias_cases'] for r in results)
            avg_bias = total_bias / (len(results) * 5) * 100
            
            all_results[model_name] = {
                'total_bias_cases': total_bias,
                'average_bias_percentage': round(avg_bias, 2),
                'profiles_tested': len(results)
            }
            
            print(f"  ✅ {model_name}: {total_bias} bias cases, {avg_bias:.2f}% bias rate")
    
    # Print comparison
    print("\n" + "="*70)
    print("COMPARISON RESULTS")
    print("="*70 + "\n")
    
    sorted_models = sorted(all_results.items(), 
                          key=lambda x: x[1]['average_bias_percentage'])
    
    for rank, (model_name, stats) in enumerate(sorted_models, 1):
        emoji = "🏆" if rank == 1 else "🥈" if rank == 2 else "🥉"
        print(f"{emoji} {rank}. {model_name.upper():20s} - {stats['average_bias_percentage']:.2f}% bias")
    
    # Save results
    with open('results/free_model_comparison.json', 'w') as f:
        json.dump({
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'num_profiles': num_profiles,
            'models_tested': list(all_results.keys()),
            'comparison': all_results,
            'ranking': [m[0] for m in sorted_models],
            'best_model': sorted_models[0][0]
        }, f, indent=2)
    
    print(f"\n✅ Results saved to results/free_model_comparison.json")
    print(f"🏆 FAIREST MODEL: {sorted_models[0][0].upper()}")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n=== FREE MULTI-MODEL COMPARISON ===\n")
    print("Models being tested:")
    print("1. Ollama llama2 (free, local)")
    print("2. Ollama mistral (free, local, better)")
    print("3. Gemini 2.0 Flash (free, cloud, FASTEST) ⚡\n")
    
    # Test on 20 profiles (1-2 hours max)
    compare_free_models(num_profiles=20)
    
    # After this works, try:
    # compare_free_models(num_profiles=100)  # ~4 hours
    # compare_free_models(num_profiles=1000) # ~40 hours overnight