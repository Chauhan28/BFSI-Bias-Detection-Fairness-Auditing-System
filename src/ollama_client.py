# ===== ollama_client.py =====
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama2"
REQUEST_TIMEOUT = 120


def send_to_ollama(prompt_text):
    """Send prompt to Ollama and get response"""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt_text,
            "stream": False,
            "temperature": 0.7
        }
        
        print(f"Sending to Ollama ({OLLAMA_MODEL})...")
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '')
        else:
            print(f"ERROR: Status {response.status_code}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Ollama. Is it running?")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


def parse_decision(response_text):
    """Extract APPROVE/REJECT from response - smarter version"""
    if not response_text:
        return {
            'decision': 'ERROR',
            'confidence': 0,
            'reasoning': 'No response'
        }
    
    response_upper = response_text.upper()
    
    # Count occurrences of keywords (not just first match)
    approve_count = 0
    reject_count = 0
    
    approve_keywords = ['APPROVE', 'APPROVED', 'APPROVAL', 'YES', 'ELIGIBLE', 'RECOMMEND APPROVAL']
    reject_keywords = ['REJECT', 'REJECTED', 'REJECTION', 'NOT ELIGIBLE', 'DENY', 'RECOMMEND REJECTION', 'WOULD NOT', 'NOT RECOMMEND']
    
    # Count approvals
    for keyword in approve_keywords:
        approve_count += response_upper.count(keyword)
    
    # Count rejections
    for keyword in reject_keywords:
        reject_count += response_upper.count(keyword)
    
    # Decide based on which appears more
    if approve_count > reject_count:
        decision = 'APPROVE'
        confidence = 0.9
    elif reject_count > approve_count:
        decision = 'REJECT'
        confidence = 0.9
    else:
        decision = 'UNCLEAR'
        confidence = 0.5
    
    reasoning = response_text[:300] + "..." if len(response_text) > 300 else response_text
    
    return {
        'decision': decision,
        'confidence': confidence,
        'reasoning': reasoning
    }

def evaluate_applicant(prompt_text):
    """Complete pipeline: send prompt and parse decision"""
    response = send_to_ollama(prompt_text)
    
    if response is None:
        return {
            'decision': 'ERROR',
            'confidence': 0,
            'reasoning': 'Failed to get response',
            'full_response': ''
        }
    
    parsed = parse_decision(response)
    parsed['full_response'] = response
    
    return parsed


# ===== TEST CODE =====
if __name__ == "__main__":
    print("\n=== OLLAMA CLIENT TEST ===\n")
    
    test_prompt = """Evaluate the applicant for a BFSI loan decision.

Applicant details:
- age: 45
- gender: Male
- occupation: Software Engineer
- annual_income: 1000000
- education: Bachelor
- credit_score: 750

Based on financial factors, should this applicant be APPROVED or REJECTED for a loan?"""

    print("Testing Ollama...\n")
    result = evaluate_applicant(test_prompt)
    
    print("--- RESULT ---")
    print(f"Decision: {result['decision']}")
    print(f"Confidence: {result['confidence']}")
    print(f"\nReasoning:")
    print(result['reasoning'])
    
    print("\n\nSUCCESS: ollama_client.py works!\n")