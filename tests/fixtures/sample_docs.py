"""
Test fixtures with sample content for different file types.
"""

# Sample Markdown content
SAMPLE_MARKDOWN = """# MLOps Platform Setup

This document describes how to set up the MLOps platform.

## Harbor Registry Configuration

To configure Harbor registry:

```bash
# Set admin password
export HARBOR_ADMIN_PASSWORD="your-password"

# Deploy Harbor
ansible-playbook -i inventory/production/hosts infrastructure/cluster/site.yml --tags harbor
```

### Troubleshooting

If you encounter certificate issues:

1. Check k3s certificate authority
2. Verify harbor service is running
3. Test connection: `curl -k https://harbor.local`

## Dependencies

- K3s cluster (>= 1.24)
- MetalLB load balancer
- Sealed Secrets controller

## Configuration

See `inventory/production/group_vars/all.yml` for configuration options.
"""

# Sample YAML content
SAMPLE_YAML = """---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: harbor-core
  namespace: harbor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: harbor-core
  template:
    metadata:
      labels:
        app: harbor-core
    spec:
      containers:
      - name: core
        image: goharbor/harbor-core:v2.9.0
        env:
        - name: CORE_SECRET
          valueFrom:
            secretKeyRef:
              name: harbor-core-secret
              key: secret
        ports:
        - containerPort: 8080
"""

# Sample Python content
SAMPLE_PYTHON = """#!/usr/bin/env python3
'''
MLflow model serving utilities
'''

import mlflow
import pandas as pd
from typing import Dict, Any


class ModelServer:
    '''Serves MLflow models for inference.'''
    
    def __init__(self, model_uri: str):
        '''Initialize model server.
        
        Args:
            model_uri: MLflow model URI
        '''
        self.model = mlflow.pyfunc.load_model(model_uri)
        self.model_uri = model_uri
    
    def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        '''Make predictions on input data.
        
        Args:
            data: Input DataFrame
            
        Returns:
            Dict with predictions and metadata
        '''
        predictions = self.model.predict(data)
        return {
            'predictions': predictions.tolist(),
            'model_uri': self.model_uri,
            'input_shape': data.shape
        }


def validate_input(data: pd.DataFrame, required_columns: list) -> bool:
    '''Validate input data has required columns.'''
    return all(col in data.columns for col in required_columns)


# Configuration
MODEL_CONFIG = {
    'staging_uri': 'models:/fraud-detection/Staging',
    'production_uri': 'models:/fraud-detection/Production',
    'required_features': ['amount', 'merchant_category', 'time_of_day']
}
"""

# Sample Shell script content
SAMPLE_SHELL = """#!/bin/bash
# Harbor registry setup script

set -euo pipefail

HARBOR_NAMESPACE="harbor"
HARBOR_ADMIN_PASSWORD="${HARBOR_ADMIN_PASSWORD:-admin123}"

echo "Setting up Harbor registry..."

# Create namespace
kubectl create namespace $HARBOR_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create admin secret
kubectl create secret generic harbor-admin-secret \\
    --from-literal=password="$HARBOR_ADMIN_PASSWORD" \\
    --namespace=$HARBOR_NAMESPACE \\
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy Harbor using Helm
helm repo add harbor https://helm.goharbor.io
helm repo update

helm upgrade --install harbor harbor/harbor \\
    --namespace $HARBOR_NAMESPACE \\
    --set expose.type=loadBalancer \\
    --set expose.loadBalancer.IP=192.168.1.210 \\
    --set harborAdminPassword="$HARBOR_ADMIN_PASSWORD" \\
    --wait

echo "Harbor deployed successfully at http://192.168.1.210"
echo "Login with admin/$HARBOR_ADMIN_PASSWORD"
"""

# Sample JSON configuration
SAMPLE_JSON = """{
  "repo_type": "mlops-platform",
  "keywords": [
    "harbor", "k3s", "metallb", "seldon", "mlflow"
  ],
  "file_patterns": [
    "*.yml", "*.yaml", "*.md", "*.sh", "*.py"
  ],
  "exclude_paths": [
    ".git", "__pycache__", "venv", ".pytest_cache"
  ],
  "extraction_focus": [
    "ansible_tasks", "kubernetes_resources", "shell_commands"
  ],
  "cross_references": {
    "ansible_roles": "infrastructure/cluster/roles/*/",
    "scripts": "scripts/*.sh",
    "documentation": "*.md"
  }
}"""

# Expected extraction results for testing
EXPECTED_MARKDOWN_KNOWLEDGE = {
    "concepts": ["harbor registry", "mlops platform", "k3s cluster"],
    "commands": ["ansible-playbook", "curl -k"],
    "configurations": ["inventory/production/group_vars/all.yml"],
    "troubleshooting": ["certificate issues", "harbor service", "connection test"],
    "dependencies": ["K3s cluster", "MetalLB load balancer", "Sealed Secrets controller"]
}

EXPECTED_PYTHON_KNOWLEDGE = {
    "functions": ["__init__", "predict", "validate_input"],
    "variables": ["MODEL_CONFIG"],
    "dependencies": ["mlflow", "pandas"],
    "concepts": ["model server", "mlflow models", "inference"]
}

EXPECTED_YAML_KNOWLEDGE = {
    "configurations": ["harbor-core", "deployment", "kubernetes"],
    "concepts": ["harbor core", "kubernetes deployment"],
    "dependencies": ["goharbor/harbor-core:v2.9.0"]
}