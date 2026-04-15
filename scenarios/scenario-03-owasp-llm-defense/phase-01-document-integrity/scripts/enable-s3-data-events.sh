#!/bin/bash
# enable-s3-data-events.sh
# Scenario 03 — Phase 1: Document Integrity Controls
#
# Enables S3 data event logging on the CloudTrail trail
# for both the demo bucket and the production knowledge base bucket.
#
# Why this is needed:
#   CloudTrail captures management events by default.
#   S3 object-level operations (PutObject, DeleteObject, GetObject)
#   are data events and require explicit configuration.
#   Without this, S3 attack attempts leave no audit trail.
#
# Prerequisites:
#   - AWS CLI configured as driftlock-dev
#   - AWSCloudTrailFullAccess attached to driftlock-dev
#   - Trail: ai-governance-lab-trail (home region: us-east-2)
#
# Usage:
#   chmod +x enable-s3-data-events.sh
#   ./enable-s3-data-events.sh

set -e

TRAIL_NAME="ai-governance-lab-trail"
TRAIL_REGION="us-east-2"
KB_BUCKET="driftlock-ai-knowledge-lab-east1"
DEMO_BUCKET="driftlock-owasp-demo"

echo "================================================"
echo "Enabling S3 Data Events on CloudTrail Trail"
echo "Trail:       $TRAIL_NAME"
echo "Home region: $TRAIL_REGION"
echo "Buckets:     $KB_BUCKET"
echo "             $DEMO_BUCKET"
echo "================================================"
echo ""

# Step 1 — Verify trail exists and check current configuration
echo "[1/3] Verifying trail configuration..."
aws cloudtrail get-event-selectors \
  --trail-name "$TRAIL_NAME" \
  --region "$TRAIL_REGION"

echo ""
echo "[2/3] Adding S3 data event selectors..."

aws cloudtrail put-event-selectors \
  --trail-name "$TRAIL_NAME" \
  --region "$TRAIL_REGION" \
  --advanced-event-selectors '[
    {
      "Name": "Management events selector",
      "FieldSelectors": [
        {
          "Field": "eventCategory",
          "Equals": ["Management"]
        }
      ]
    },
    {
      "Name": "S3 data events - knowledge base and demo buckets",
      "FieldSelectors": [
        {
          "Field": "eventCategory",
          "Equals": ["Data"]
        },
        {
          "Field": "resources.type",
          "Equals": ["AWS::S3::Object"]
        },
        {
          "Field": "resources.ARN",
          "StartsWith": [
            "arn:aws:s3:::driftlock-ai-knowledge-lab-east1/",
            "arn:aws:s3:::driftlock-owasp-demo/"
          ]
        }
      ]
    }
  ]'

echo ""
echo "[3/3] Verifying updated configuration..."
aws cloudtrail get-event-selectors \
  --trail-name "$TRAIL_NAME" \
  --region "$TRAIL_REGION"

echo ""
echo "================================================"
echo "S3 data events enabled successfully."
echo ""
echo "Events now captured:"
echo "  - PutObject on both buckets"
echo "  - GetObject on both buckets"
echo "  - DeleteObject on both buckets"
echo ""
echo "Note: Allow 2-5 minutes for events to appear"
echo "      after the first S3 operation."
echo ""
echo "Cost note:"
echo "  S3 data events cost approx \$0.10 per 100,000 events."
echo "  Scoped to two buckets to minimize cost."
echo "================================================"
