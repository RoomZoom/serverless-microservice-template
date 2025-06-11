# src/utils/config.py
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict

_env_cache: Dict[str, Optional[str]] = {}

_ssm_cache: Dict[str, str] = {}

_ssm_client = None


def get_env_variable(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with caching"""
    if name not in _env_cache:
        _env_cache[name] = os.environ.get(name, default)
    return _env_cache[name]


def get_secret(secret_name: str) -> str:
    """Get SSM parameter with caching and client reuse"""
    global _ssm_client
    
    if secret_name in _ssm_cache:
        return _ssm_cache[secret_name]
    
    if _ssm_client is None:
        _ssm_client = boto3.client("ssm")
    
    try:
        param = _ssm_client.get_parameter(Name=secret_name, WithDecryption=True)
        value = param["Parameter"]["Value"]
        _ssm_cache[secret_name] = value
        return value
    except ClientError as e:
        raise Exception(f"Unable to retrieve secret {secret_name}: {str(e)}")


def clear_cache():
    """Clear all caches (useful for testing)"""
    global _env_cache, _ssm_cache
    _env_cache.clear()
    _ssm_cache.clear()
