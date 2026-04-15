#!/bin/bash
# investigate-cloudtrail.sh
# Scenario 03 — Phase 1: Document Integrity Controls
#
# Investigates CloudTrail logs for S3 attack attempts by
# driftlock-svc-account. Demonstrates the forensic investigation
# methodology used when LookupEvents does not surface S3 data events.
#
# Why raw log search is necessary:
#   CloudTrail LookupEvents indexes management events reliably
#   but S3 data events — especially AccessDenied results —
#   may not appear in LookupEvents even when captured.
#   The authoritative record is always in the raw log files
#   stored in the CloudTrail S3 bucket.
#
# Investigation methodology:
#   Step 1: Try LookupEvents (fast, may be incomplete)
#   Step 2: List raw log files in CloudTrail S3 bucket
#   Step 3: Download and search raw logs with Python
#   Step 4: Parse results for attacker activity
#
# Prerequisites:
#   - Run as driftlock-dev (NOT svc-account)
#   - AWSCloudTrailFullAccess attached to driftlock-dev
#   - AmazonS3FullAccess attached to driftlock-dev
#   - Run after run-attack-simulation.sh (allow 2-3 min delay)
#
# Usage:
#   chmod +x investigate-cloudtrail.sh
#   ./investigate-cloudtrail.sh

set -e

REGION="us-east-1"
TRAIL_REGION="us-east-2"
TRAIL_NAME="ai-governance-lab-trail"
CLOUDTRAIL_BUCKET="aws-cloudtrail-logs-YOUR_ACCOUNT_ID-5bdd89ef"
ACCOUNT_ID="YOUR_ACCOUNT_ID"
LOG_DIR="$HOME/cloudtrail-logs"
TARGET_USER="driftlock-svc-account"
TODAY=$(date -u +%Y/%m/%d)

echo "================================================"
echo "CloudTrail Forensic Investigation"
echo "Target identity: $TARGET_USER"
echo "Investigation date: $TODAY"
echo "================================================"
echo ""

# Verify investigator identity
echo "[Setup] Verifying investigator identity..."
aws sts get-caller-identity
echo ""

# Step 1 — Try LookupEvents first
echo "================================================"
echo "Step 1: CloudTrail LookupEvents (fast search)"
echo "Note: May not surface S3 data events"
echo "================================================"
aws cloudtrail lookup-events \
  --lookup-attributes "AttributeKey=Username,AttributeValue=$TARGET_USER" \
  --start-time "$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S)" \
  --region "$TRAIL_REGION" \
  --query 'Events[*].{Time:EventTime,Event:EventName,Resource:Resources[0].ResourceName}' \
  --output table \
  || echo "No events found in LookupEvents index"
echo ""

# Step 2 — List raw log files
echo "================================================"
echo "Step 2: Listing raw CloudTrail log files"
echo "Path: s3://$CLOUDTRAIL_BUCKET/AWSLogs/$ACCOUNT_ID/CloudTrail/$REGION/$TODAY/"
echo "================================================"
aws s3 ls \
  "s3://$CLOUDTRAIL_BUCKET/AWSLogs/$ACCOUNT_ID/CloudTrail/$REGION/$TODAY/" \
  --region "$REGION" \
  | tail -10
echo ""

# Step 3 — Download recent log files
echo "================================================"
echo "Step 3: Downloading recent log files..."
echo "================================================"
mkdir -p "$LOG_DIR"
aws s3 cp \
  "s3://$CLOUDTRAIL_BUCKET/AWSLogs/$ACCOUNT_ID/CloudTrail/$REGION/$TODAY/" \
  "$LOG_DIR/" \
  --recursive \
  --region "$REGION" \
  --quiet
echo "Log files downloaded to: $LOG_DIR"
echo "File count: $(ls $LOG_DIR/*.json.gz 2>/dev/null | wc -l)"
echo ""

# Step 4 — Search raw logs for attacker activity
echo "================================================"
echo "Step 4: Searching raw logs for $TARGET_USER activity"
echo "================================================"
FOUND=0
for f in "$LOG_DIR"/*.json.gz; do
    results=$(gunzip -c "$f" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for record in data.get('Records', []):
    identity = record.get('userIdentity', {})
    username = identity.get('userName', '') or \
               identity.get('sessionContext', {}).get(
                   'sessionIssuer', {}).get('userName', '')
    if '$TARGET_USER' in username or 'driftlock-svc' in str(identity):
        print(json.dumps({
            'time':     record.get('eventTime'),
            'event':    record.get('eventName'),
            'user':     username,
            'resource': record.get('requestParameters', {}).get(
                            'bucketName', '') + '/' +
                        record.get('requestParameters', {}).get(
                            'key', ''),
            'error':    record.get('errorCode', 'success'),
            'source_ip': record.get('sourceIPAddress', 'unknown')
        }, indent=2))
" 2>/dev/null)
    if [ -n "$results" ]; then
        echo "$results"
        FOUND=1
    fi
done

if [ "$FOUND" -eq 0 ]; then
    echo "No activity found for $TARGET_USER in downloaded logs."
    echo ""
    echo "Possible reasons:"
    echo "  1. Attack simulation not yet run"
    echo "  2. CloudTrail delivery delay (wait 2-5 minutes)"
    echo "  3. S3 data events not enabled on trail"
    echo "     Run: enable-s3-data-events.sh"
fi

echo ""
echo "================================================"
echo "Investigation complete."
echo ""
echo "Evidence interpretation:"
echo "  errorCode: AccessDenied = attack blocked by policy"
echo "  errorCode: success      = action permitted (verify intent)"
echo ""
echo "For production-scale investigation use Amazon Athena"
echo "to query CloudTrail logs with SQL across date ranges."
echo "================================================"

# Clean up downloaded logs
echo ""
echo "Cleaning up downloaded log files..."
rm -rf "$LOG_DIR"
echo "Done."
