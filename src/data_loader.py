import json 


def load_json_file(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def get_test_cases(data):
    return data['test_cases']

def get_sample_test_cases(data, num_samples=10):
    test_cases = get_test_cases(data)
    return test_cases[:num_samples]


def extract_applicant_details(prompt_text):
    """
    Parse the applicant details from the question text.
    
    Looks for lines like:
    - age: 61
    - gender: Male
    - occupation: Software Engineer
    """
    details = {}
    
    fields = ['age', 'gender', 'occupation', 'annual_income', 'education', 
              'marital_status', 'city_type', 'nationality', 'kyc_completed', 
              'account_type_requested', 'credit_score']
    
    lines = prompt_text.split('\n')
    
    for line in lines:
        for field in fields:
            if f'- {field}:' in line:
                # Extract value after "- {field}:"
                parts = line.split(f'- {field}:')
                if len(parts) > 1:
                    value = parts[1].strip()
                    details[field] = value
    return details

if __name__ == "__main__":

    print("Loading JSON File..")
    data = load_json_file('data/bfsi_test_cases.json')

    print("Extracting first 10 test cases..")
    test_cases = get_sample_test_cases(data, num_samples=10)

    print("\n first test case loaded:")
    first_case = test_cases[0]
    print(f" ID : {first_case['category']}")
    print(f"   Category: {first_case['category']}")
    print(f"   Name: {first_case['name']}")

    
    print("\n--- APPLICANT DETAILS ---")
    question = first_case['payload']['question']
    details = extract_applicant_details(question)
    
    if details:
        for key, value in details.items():
            print(f"{key}: {value}")
    else:
        print("ERROR: No details extracted!")
        print("\nDEBUG: First 500 chars of question:")
        print(question[:500])


    


    all_test_cases = get_test_cases(data)
    print(f"\n Total test cases in file: {len(all_test_cases)}")

