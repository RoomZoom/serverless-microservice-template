#!/usr/bin/env python3
"""Test script to verify AWS adapters can be imported without AWS credentials"""

import os
import sys

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'

try:
    print("Testing AWS adapter imports...")
    
    print("Importing DynamoDB adapter...")
    from src.adapters import dynamodb_adapter
    print("✅ DynamoDB adapter imported successfully")
    
    print("Importing SQS adapter...")
    from src.adapters import sqs_adapter
    print("✅ SQS adapter imported successfully")
    
    print("Importing Kafka adapter...")
    from src.adapters import kafka_adapter
    print("✅ Kafka adapter imported successfully")
    
    print("\n✅ All AWS adapters imported successfully!")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
