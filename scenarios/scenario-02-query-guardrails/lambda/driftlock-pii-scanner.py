import boto3
import json
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3', region_name='us-east-1')

BUCKET = 'driftlock-ai-knowledge-lab-east1'
PREFIX = 'public-research/'

# PII detection patterns
PII_PATTERNS = {
    'Email Address': re.compile(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    ),
    'Phone Number': re.compile(
        r'(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        re.IGNORECASE
    ),
    'Social Security Number': re.compile(
        r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b'
    ),
    'Credit Card Number': re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    ),
    'AWS Access Key': re.compile(
        r'\bAKIA[0-9A-Z]{16}\b'
    ),
    'AWS Secret Key': re.compile(
        r'(?i)aws.{0,20}secret.{0,20}[\'"][0-9a-zA-Z/+]{40}[\'"]'
    ),
    'IP Address': re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ),
    'Internal IP Address': re.compile(
        r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    ),
    'Date of Birth': re.compile(
        r'\b(?:DOB|Date of Birth|Born)[:\s]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        re.IGNORECASE
    ),
    'Employee ID': re.compile(
        r'\bEMP-\d{6}\b'
    ),
    'AWS Account ID': re.compile(
        r'\b\d{12}\b'
    ),
    'Passport Number': re.compile(
        r'\b[A-Z]{1,2}\d{6,9}\b'
    ),
    'Bank Routing Number': re.compile(
        r'\b\d{9}\b'
    ),
    'ZIP Code with PII Context': re.compile(
        r'(?i)(?:zip|postal)[:\s]+\d{5}(?:-\d{4})?'
    ),
}

# Patterns that need context to avoid false positives
CONTEXT_REQUIRED = {
    'AWS Account ID',
    'Bank Routing Number',
    'Passport Number',
}


def scan_text_for_pii(text, document_key):
    findings = []

    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)

        if matches:
            # For patterns requiring context, verify
            # surrounding text before flagging
            if pii_type in CONTEXT_REQUIRED:
                context_keywords = {
                    'AWS Account ID': [
                        'account', 'aws', 'iam', 'arn'
                    ],
                    'Bank Routing Number': [
                        'routing', 'aba', 'bank', 'wire'
                    ],
                    'Passport Number': [
                        'passport', 'travel', 'document'
                    ],
                }

                keywords = context_keywords.get(pii_type, [])
                context_found = any(
                    kw in text.lower() for kw in keywords
                )

                if not context_found:
                    continue

            findings.append({
                'pii_type': pii_type,
                'match_count': len(matches),
                'confidence': 'HIGH' if pii_type not in CONTEXT_REQUIRED
                              else 'MEDIUM'
            })

            logger.warning(
                f"PII DETECTED | Document: {document_key} | "
                f"Type: {pii_type} | Matches: {len(matches)} | "
                f"Confidence: HIGH"
            )

    return findings


def lambda_handler(event, context):

    logger.info("Starting regex-based PII scan of knowledge repository")
    logger.info(f"Bucket: {BUCKET} | Prefix: {PREFIX}")
    logger.info(f"Active PII patterns: {len(PII_PATTERNS)}")

    scan_results = []
    pii_detected = False

    # Step 1 — List all documents in public-research/
    try:
        response = s3.list_objects_v2(
            Bucket=BUCKET,
            Prefix=PREFIX
        )
    except Exception as e:
        logger.error(f"Failed to list S3 objects: {str(e)}")
        return {
            "status": "ERROR",
            "message": f"Failed to list S3 objects: {str(e)}"
        }

    objects = response.get('Contents', [])

    if not objects:
        logger.warning("No documents found in public-research/")
        return {
            "status": "WARNING",
            "message": "No documents found in public-research/"
        }

    logger.info(f"Found {len(objects)} objects — beginning scan")

    # Step 2 — Scan each document
    for obj in objects:
        key = obj['Key']

        # Skip folder placeholder objects
        if key.endswith('/'):
            continue

        logger.info(f"Scanning: {key}")

        try:
            # Read document from S3
            s3_response = s3.get_object(Bucket=BUCKET, Key=key)
            text = s3_response['Body'].read().decode('utf-8')

            if not text.strip():
                logger.warning(f"Document is empty: {key}")
                continue

            # Step 3 — Run regex PII patterns
            findings = scan_text_for_pii(text, key)

            if findings:
                pii_detected = True
                pii_types = [f['pii_type'] for f in findings]

                logger.warning(
                    f"PII DETECTED in {key} | "
                    f"Types: {pii_types}"
                )

                scan_results.append({
                    "document": key,
                    "status": "PII_DETECTED",
                    "findings": findings,
                    "pii_types": pii_types,
                    "total_findings": len(findings),
                    "action_required": "Human review required — "
                                      "document may contain sensitive data"
                })

            else:
                logger.info(f"CLEAN: No PII detected in {key}")
                scan_results.append({
                    "document": key,
                    "status": "CLEAN",
                    "findings": [],
                    "pii_types": [],
                    "total_findings": 0,
                    "action_required": "None"
                })

        except Exception as e:
            logger.error(f"Error scanning {key}: {str(e)}")
            scan_results.append({
                "document": key,
                "status": "ERROR",
                "error": str(e),
                "action_required": "Investigate scan error"
            })

    # Step 4 — Build final report
    clean_count = sum(
        1 for r in scan_results if r['status'] == 'CLEAN'
    )
    pii_count = sum(
        1 for r in scan_results if r['status'] == 'PII_DETECTED'
    )
    error_count = sum(
        1 for r in scan_results if r['status'] == 'ERROR'
    )

    overall_status = "CLEAN" if not pii_detected else "PII_DETECTED"

    report = {
        "scanner": "regex-based PII detection",
        "production_equivalent": "Amazon Comprehend or Amazon Macie",
        "patterns_evaluated": len(PII_PATTERNS),
        "scan_summary": {
            "overall_status": overall_status,
            "bucket": BUCKET,
            "prefix": PREFIX,
            "total_documents_scanned": len(scan_results),
            "clean": clean_count,
            "pii_detected": pii_count,
            "errors": error_count,
            "action_required": "None" if not pii_detected
                               else "Review flagged documents immediately"
        },
        "document_results": scan_results
    }

    logger.info(
        f"Scan complete: {json.dumps(report['scan_summary'], indent=2)}"
    )

    return report
