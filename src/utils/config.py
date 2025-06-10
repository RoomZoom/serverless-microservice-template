# src/utils/config.py
import os
import boto3
from botocore.exceptions import ClientError


def get_env_variable(name, default=None):
    return os.environ.get(name, default)


def get_secret(secret_name):
    client = boto3.client("ssm")
    try:
        param = client.get_parameter(Name=secret_name, WithDecryption=True)
        return param["Parameter"]["Value"]
    except ClientError as e:
        raise Exception(f"Unable to retrieve secret {secret_name}: {str(e)}")
