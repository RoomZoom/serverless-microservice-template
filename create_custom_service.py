#!/usr/bin/env python3
"""
Custom Service Generator Script

This script creates a new microservice from the serverless-microservice-template
with customizable resource names for lambda handlers, SQS queues, DynamoDB tables,
Kafka topics, and API Gateway endpoints.
"""

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List


class ServiceCustomizer:
    def __init__(self):
        self.template_dir = Path(__file__).parent
        self.replacements = {}
        
    def get_user_inputs(self) -> Dict[str, str]:
        """Collect customization inputs from user"""
        print("🚀 Creating a new microservice from serverless-microservice-template")
        print("=" * 60)
        
        inputs = {}
        
        while True:
            service_name = input("Enter new service name (e.g., 'user-management'): ").strip()
            if service_name and re.match(r'^[a-z0-9-]+$', service_name):
                inputs['service_name'] = service_name
                break
            print("❌ Service name must contain only lowercase letters, numbers, and hyphens")
        
        handler = input(f"Lambda handler [default: main.handler]: ").strip()
        inputs['lambda_handler'] = handler if handler else "main.handler"
        
        table_name = input(f"DynamoDB table name [default: {service_name}-table]: ").strip()
        inputs['dynamodb_table'] = table_name if table_name else f"{service_name}-table"
        
        queue_name = input(f"SQS queue name [default: {service_name}-queue]: ").strip()
        inputs['sqs_queue'] = queue_name if queue_name else f"{service_name}-queue"
        
        kafka_topic = input(f"Kafka main topic [default: {service_name}-events]: ").strip()
        inputs['kafka_topic'] = kafka_topic if kafka_topic else f"{service_name}-events"
        
        kafka_dlq = input(f"Kafka DLQ topic [default: {service_name}-dlq]: ").strip()
        inputs['kafka_dlq'] = kafka_dlq if kafka_dlq else f"{service_name}-dlq"
        
        api_name = input(f"API Gateway name [default: {service_name}-api]: ").strip()
        inputs['api_gateway'] = api_name if api_name else f"{service_name}-api"
        
        default_target = f"../{service_name}"
        target_dir = input(f"Target directory [default: {default_target}]: ").strip()
        inputs['target_dir'] = target_dir if target_dir else default_target
        
        return inputs
    
    def prepare_replacements(self, inputs: Dict[str, str]) -> Dict[str, str]:
        """Prepare find-replace mappings"""
        service_name = inputs['service_name']
        
        replacements = {
            'microservice-template': service_name,
            'microservice_template': service_name.replace('-', '_'),
            
            'main.handler': inputs['lambda_handler'],
            
            'my-table': inputs['dynamodb_table'],
            f'my-table-{"{ENVIRONMENT}"}': f'{inputs["dynamodb_table"]}-{"{ENVIRONMENT}"}',
            f'my-table-{"{environment}"}': f'{inputs["dynamodb_table"]}-{"{environment}"}',
            
            'my-queue': inputs['sqs_queue'],
            f'my-queue-{"{ENVIRONMENT}"}': f'{inputs["sqs_queue"]}-{"{ENVIRONMENT}"}',
            f'my-queue-{"{environment}"}': f'{inputs["sqs_queue"]}-{"{environment}"}',
            
            'microservice-events': inputs['kafka_topic'],
            'microservice-dlq': inputs['kafka_dlq'],
            f'microservice-events-{"{ENVIRONMENT}"}': f'{inputs["kafka_topic"]}-{"{ENVIRONMENT}"}',
            f'microservice-events-{"{environment}"}': f'{inputs["kafka_topic"]}-{"{environment}"}',
            
            'my-microservice': service_name,
        }
        
        return replacements
    
    def get_files_to_process(self, target_dir: Path) -> List[Path]:
        """Get list of files that need text replacement"""
        extensions = {'.py', '.tf', '.md', '.yml', '.yaml', '.json', '.txt', '.env'}
        files_to_process = []
        
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.terraform'}
        exclude_files = {'create_custom_service.py', 'deployment.zip'}
        
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                    
                file_path = Path(root) / file
                if file_path.suffix in extensions or file_path.name in {'.env', 'Makefile'}:
                    files_to_process.append(file_path)
        
        return files_to_process
    
    def replace_in_file(self, file_path: Path, replacements: Dict[str, str]) -> bool:
        """Replace text in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            for old_text, new_text in replacements.items():
                content = content.replace(old_text, new_text)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            
        return False
    
    def copy_template(self, target_dir: str) -> Path:
        """Copy template to target directory"""
        target_path = Path(target_dir).resolve()
        
        if target_path.exists():
            response = input(f"Directory {target_path} already exists. Overwrite? [y/N]: ")
            if response.lower() != 'y':
                print("❌ Operation cancelled")
                sys.exit(1)
            shutil.rmtree(target_path)
        
        print(f"📁 Copying template to {target_path}...")
        shutil.copytree(self.template_dir, target_path, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '.pytest_cache', 'node_modules', '.terraform',
            '*.pyc', 'deployment.zip', 'create_custom_service.py'
        ))
        
        return target_path
    
    def update_makefile_service_name(self, target_dir: Path, service_name: str):
        """Update the default SERVICE_NAME in Makefile"""
        makefile_path = target_dir / 'Makefile'
        if makefile_path.exists():
            with open(makefile_path, 'r') as f:
                content = f.read()
            
            content = re.sub(
                r'SERVICE_NAME \?= microservice-template',
                f'SERVICE_NAME ?= {service_name}',
                content
            )
            
            with open(makefile_path, 'w') as f:
                f.write(content)
    
    def create_service(self):
        """Main method to create customized service"""
        try:
            inputs = self.get_user_inputs()
            
            print("\n📋 Configuration Summary:")
            print("-" * 30)
            for key, value in inputs.items():
                print(f"{key:15}: {value}")
            
            confirm = input("\nProceed with these settings? [Y/n]: ").strip()
            if confirm.lower() == 'n':
                print("❌ Operation cancelled")
                return
            
            target_dir = self.copy_template(inputs['target_dir'])
            
            replacements = self.prepare_replacements(inputs)
            
            self.update_makefile_service_name(target_dir, inputs['service_name'])
            
            files_to_process = self.get_files_to_process(target_dir)
            
            print(f"\n🔄 Processing {len(files_to_process)} files...")
            
            modified_count = 0
            for file_path in files_to_process:
                if self.replace_in_file(file_path, replacements):
                    modified_count += 1
                    print(f"  ✅ {file_path.relative_to(target_dir)}")
            
            print(f"\n🎉 Successfully created '{inputs['service_name']}' service!")
            print(f"📁 Location: {target_dir}")
            print(f"📝 Modified {modified_count} files")
            
            print(f"\n🚀 Next steps:")
            print(f"1. cd {target_dir}")
            print(f"2. make init")
            print(f"3. Configure your MSK cluster details in terraform/dev/main.tf")
            print(f"4. make deploy-dev")
            
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    customizer = ServiceCustomizer()
    customizer.create_service()
