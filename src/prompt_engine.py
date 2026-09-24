# ===== prompt_engine.py =====
# Purpose: Create counterfactuals (modify one attribute at a time) and regenerate prompts

import json
from data_loader import extract_applicant_details

# ===== MAPPING: Attributes to their counterfactual values =====
COUNTERFACTUAL_VALUES = {
    'gender': ['Male', 'Female'],
    'age': ['25', '35', '45', '55'],
    'nationality': ['Indian', 'Foreign'],
    'city_type': ['Urban', 'Rural', 'Semi-Urban'],
    'marital_status': ['Single', 'Married', 'Divorced'],
    'education': ['High School', 'Diploma', 'Bachelor', 'Masters'],
    'occupation': ['Software Engineer', 'Farmer', 'Teacher', 'Doctor', 'Business Owner'],
    'credit_score': ['350', '550', '750', '850']
}


# ===== FUNCTION 1: Create one counterfactual =====
def create_counterfactual(applicant_details, attribute_to_change, new_value):
    """Create a counterfactual by changing ONE attribute."""
    counterfactual = applicant_details.copy()
    counterfactual[attribute_to_change] = new_value
    return counterfactual


# ===== FUNCTION 2: Regenerate prompt with new details =====
def regenerate_prompt(original_prompt, original_details, new_details):
    """
    Rebuild the prompt with updated applicant details.
    Carefully replaces each changed field.
    """
    modified_prompt = original_prompt
    
    # Find and replace each field that changed
    for field, new_value in new_details.items():
        if field in original_details:
            original_value = original_details[field]
            
            # Skip if value didn't change
            if str(original_value) == str(new_value):
                continue
            
            # Create old and new patterns
            # Try to match "- field: value" format
            old_pattern = f"- {field}: {original_value}"
            new_pattern = f"- {field}: {new_value}"
            
            # Replace in prompt
            if old_pattern in modified_prompt:
                modified_prompt = modified_prompt.replace(old_pattern, new_pattern)
    
    return modified_prompt


# ===== FUNCTION 3: Create all counterfactuals for one test case =====
def generate_counterfactuals_for_case(test_case):
    """
    For ONE test case, create counterfactuals for key attributes.
    """
    
    test_id = test_case['id']
    original_prompt = test_case['payload']['question']
    original_details = extract_applicant_details(original_prompt)
    
    result = {
        'test_id': test_id,
        'original': {
            'prompt': original_prompt,
            'details': original_details
        },
        'counterfactuals': []
    }
    
    # Attributes to test for bias
    attributes_to_test = ['gender', 'age', 'nationality', 'city_type', 'marital_status']
    
    for attribute in attributes_to_test:
        if attribute in original_details:
            original_value = original_details[attribute]
            
            if attribute in COUNTERFACTUAL_VALUES:
                possible_values = COUNTERFACTUAL_VALUES[attribute]
                
                # Pick first different value
                for new_value in possible_values:
                    if str(new_value) != str(original_value):
                        # Create new details with changed attribute
                        new_details = create_counterfactual(original_details, attribute, new_value)
                        
                        # Regenerate prompt
                        new_prompt = regenerate_prompt(original_prompt, original_details, new_details)
                        
                        # Check if prompt actually changed
                        prompt_changed = (new_prompt != original_prompt)
                        
                        result['counterfactuals'].append({
                            'attribute': attribute,
                            'original_value': original_value,
                            'new_value': new_value,
                            'prompt': new_prompt,
                            'details': new_details,
                            'prompt_changed': prompt_changed
                        })
                        
                        break
    
    return result


# ===== TEST CODE =====
if __name__ == "__main__":
    print("\n=== PROMPT ENGINE TEST ===\n")
    
    from data_loader import load_json_file, get_sample_test_cases
    
    print("Loading JSON...")
    data = load_json_file('data/bfsi_test_cases.json')
    test_cases = get_sample_test_cases(data, num_samples=1)
    first_case = test_cases[0]
    
    print("Generating counterfactuals...")
    result = generate_counterfactuals_for_case(first_case)
    
    print(f"\nTest ID: {result['test_id']}")
    
    print("\n--- ORIGINAL ---")
    original_prompt = result['original']['prompt']
    print(f"First 300 chars:\n{original_prompt[:300]}\n")
    
    print(f"\n--- COUNTERFACTUALS ({len(result['counterfactuals'])} generated) ---")
    for i, cf in enumerate(result['counterfactuals'], 1):
        print(f"\n{i}. {cf['attribute'].upper()}")
        print(f"   Original value: {cf['original_value']} → New value: {cf['new_value']}")
        print(f"   Prompt changed: {cf['prompt_changed']}")
        
        # Show the specific changed line
        lines = cf['prompt'].split('\n')
        for line in lines:
            if f"- {cf['attribute']}:" in line:
                print(f"   Modified line: {line}")
                break
    
    print("\n\nSUCCESS: prompt_engine.py works!\n")