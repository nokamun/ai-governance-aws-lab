import boto3
import json

s3 = boto3.client('s3')
BUCKET = 'driftlock-ai-knowledge-lab'

def lambda_handler(event, context):

    test_cases = [
        {
            "label": "Approved research document - AI Governance Notes",
            "key": "public-research/ai_governance_notes.txt"
        },
        {
            "label": "Approved research document - Market Trends",
            "key": "public-research/market_trends.txt"
        },
        {
            "label": "Sensitive document - Pricing Strategy",
            "key": "sensitive-internal/pricing_strategy.txt"
        },
        {
            "label": "Sensitive document - Product Roadmap",
            "key": "sensitive-internal/product_roadmap.txt"
        }
    ]

    results = []

    for test in test_cases:
        try:
            response = s3.get_object(Bucket=BUCKET, Key=test['key'])
            results.append({
                "test": test['label'],
                "result": "ALLOWED",
                "status": "Access granted"
            })
        except Exception as e:
            error_code = e.response['Error']['Code']
            results.append({
                "test": test['label'],
                "result": "DENIED",
                "status": f"Access blocked — {error_code}"
            })

    print(json.dumps(results, indent=2))
    return results
