import json
import boto3

s3 = boto3.client('s3')

BUCKET = "driftlock-ai-knowledge-lab"

def lambda_handler(event, context):
    query = event.get("query", "").lower()

    if "market" in query or "trend" in query:
        key = "public-research/market_trends.txt"
    elif "governance" in query:
        key = "public-research/ai_governance_notes.txt"
    elif "roadmap" in query:
        key = "sensitive-internal/product_roadmap.txt"
    elif "pricing" in query:
        key = "sensitive-internal/pricing_strategy.txt"
    else:
        return {
            "statusCode": 200,
            "body": json.dumps("No relevant research found.")
        }

    try:
        response = s3.get_object(Bucket=BUCKET, Key=key)
        content = response["Body"].read().decode("utf-8")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "document": key,
                "content": content
            })
        }

    except Exception:
        return {
            "statusCode": 403,
            "body": json.dumps("Access denied to requested resource.")
        }
