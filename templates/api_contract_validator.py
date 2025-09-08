#!/usr/bin/env python3
"""API contract validator - ensures APIs have schemas and follow contracts"""

import json
import sys
import re
import yaml
from pathlib import Path

# Import base validator functions
sys.path.insert(0, str(Path(__file__).parent))
from base_validator import is_large_task_mode, update_validation_log

def find_api_endpoints(project_path):
    """Find all API endpoint definitions in the project"""
    endpoints = []
    
    # Patterns for different frameworks
    patterns = {
        'express': [
            r'app\.(get|post|put|patch|delete|use)\([\'"`](.*?)[\'"`]',
            r'router\.(get|post|put|patch|delete|use)\([\'"`](.*?)[\'"`]',
        ],
        'fastapi': [
            r'@app\.(get|post|put|patch|delete)\([\'"`](.*?)[\'"`]',
            r'@router\.(get|post|put|patch|delete)\([\'"`](.*?)[\'"`]',
        ],
        'django': [
            r'path\([\'"`](.*?)[\'"`]',
            r'url\(r?\^?(.*?)\$?[\'"`]',
        ],
        'gin': [
            r'router\.(GET|POST|PUT|PATCH|DELETE)\([\'"`](.*?)[\'"`]',
        ]
    }
    
    # Search for API files
    api_patterns = ['**/routes/**/*.js', '**/routes/**/*.ts', '**/api/**/*.py', 
                    '**/controllers/**/*.js', '**/handlers/**/*.go']
    
    for pattern in api_patterns:
        for file_path in project_path.glob(pattern):
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
                continue
            
            content = file_path.read_text()
            
            # Check each pattern type
            for framework, framework_patterns in patterns.items():
                for pattern in framework_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        method = match.group(1) if match.lastindex > 1 else 'GET'
                        path = match.group(2) if match.lastindex > 1 else match.group(1)
                        
                        endpoints.append({
                            'file': str(file_path),
                            'method': method.upper(),
                            'path': path,
                            'framework': framework
                        })
    
    return endpoints

def find_schema_definitions(project_path):
    """Find API schema definitions (OpenAPI, Swagger, etc.)"""
    schemas = {}
    
    # Look for OpenAPI/Swagger files
    schema_files = ['**/swagger.json', '**/swagger.yaml', '**/openapi.json', 
                    '**/openapi.yaml', '**/api-spec.json', '**/api-spec.yaml']
    
    for pattern in schema_files:
        for file_path in project_path.glob(pattern):
            try:
                if file_path.suffix == '.json':
                    with open(file_path) as f:
                        spec = json.load(f)
                else:
                    with open(file_path) as f:
                        spec = yaml.safe_load(f)
                
                # Extract paths from OpenAPI spec
                if 'paths' in spec:
                    for path, methods in spec['paths'].items():
                        for method in methods:
                            if method.upper() in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                                key = f"{method.upper()} {path}"
                                schemas[key] = {
                                    'spec_file': str(file_path),
                                    'has_request_schema': 'requestBody' in methods[method],
                                    'has_response_schema': 'responses' in methods[method]
                                }
            except (json.JSONDecodeError, yaml.YAMLError):
                continue
    
    return schemas

def check_validation_middleware(project_path):
    """Check if validation middleware is implemented"""
    validation_found = False
    
    # Look for validation libraries
    validation_patterns = [
        r'import.*joi',  # Joi validation
        r'import.*zod',  # Zod validation
        r'import.*yup',  # Yup validation
        r'from pydantic',  # Pydantic validation
        r'import.*express-validator',  # Express validator
        r'import.*ajv',  # AJV validation
    ]
    
    for file_path in project_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.js', '.ts', '.py']:
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
                continue
            
            content = file_path.read_text()
            for pattern in validation_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    validation_found = True
                    break
    
    return validation_found

def validate_api_contracts():
    """Main validation function"""
    # Exit silently if not in Large Task Mode
    if not is_large_task_mode():
        sys.exit(0)
    
    issues = []
    project_path = Path.cwd()
    
    # Find all API endpoints
    endpoints = find_api_endpoints(project_path)
    
    if not endpoints:
        # No APIs found, skip validation
        sys.exit(0)
    
    # Find schema definitions
    schemas = find_schema_definitions(project_path)
    
    # Check for validation middleware
    has_validation = check_validation_middleware(project_path)
    
    # Validate each endpoint
    undocumented_endpoints = []
    for endpoint in endpoints:
        endpoint_key = f"{endpoint['method']} {endpoint['path']}"
        
        # Check if endpoint has schema
        if endpoint_key not in schemas:
            # Try partial match for parameterized routes
            found = False
            for schema_key in schemas:
                schema_path = schema_key.split(' ')[1]
                endpoint_path = endpoint['path']
                
                # Convert Express :param to OpenAPI {param}
                normalized_endpoint = re.sub(r':(\w+)', r'{\1}', endpoint_path)
                
                if schema_path == normalized_endpoint:
                    found = True
                    break
            
            if not found:
                undocumented_endpoints.append(endpoint)
    
    # Build issues report
    if not schemas:
        issues.append({
            'type': 'no_api_schemas',
            'message': 'No API schema definitions found (OpenAPI/Swagger)',
            'severity': 'high'
        })
    
    if not has_validation:
        issues.append({
            'type': 'no_validation_middleware',
            'message': 'No request validation middleware detected',
            'severity': 'high'
        })
    
    if undocumented_endpoints:
        issues.append({
            'type': 'undocumented_endpoints',
            'message': f'{len(undocumented_endpoints)} endpoints without schemas',
            'endpoints': undocumented_endpoints[:5],  # Show first 5
            'severity': 'medium'
        })
    
    # Report results
    if issues:
        report = []
        
        for issue in issues:
            if issue['type'] == 'no_api_schemas':
                report.append("❌ No API schema definitions (OpenAPI/Swagger) found")
                report.append("  Create /docs/openapi.yaml with endpoint definitions")
            elif issue['type'] == 'no_validation_middleware':
                report.append("❌ No request validation middleware detected")
                report.append("  Add validation using Joi, Zod, Pydantic, etc.")
            elif issue['type'] == 'undocumented_endpoints':
                report.append(f"❌ {issue['message']}")
                for ep in issue.get('endpoints', []):
                    report.append(f"  - {ep['method']} {ep['path']} ({ep['file']})")
        
        # Update validation log
        update_validation_log({
            'type': 'api_contract',
            'status': 'failed',
            'issues': issues
        })
        
        # Return failure
        output = {
            "decision": "block",
            "reason": "API contract issues detected:\n" + "\n".join(report)
        }
        json.dump(output, sys.stdout)
        sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    validate_api_contracts()