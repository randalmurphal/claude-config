#!/usr/bin/env python3
"""Security validator - checks for API and network security issues"""

import json
import sys
import re
from pathlib import Path

# Import base validator functions
sys.path.insert(0, str(Path(__file__).parent))
from base_validator import is_large_task_mode, update_validation_log

# Security vulnerability patterns
SECURITY_PATTERNS = {
    'hardcoded_secrets': [
        r'(?:api[_-]?key|apikey|secret|password|token|auth)\s*[:=]\s*[\'"`][\w\-\.]+[\'"`]',
        r'(?:AWS|aws)[_-]?(?:ACCESS|access)[_-]?(?:KEY|key)[_-]?(?:ID|id)\s*[:=]\s*[\'"`][\w]+[\'"`]',
        r'(?:DATABASE|database|DB|db)[_-]?(?:URL|url|PASSWORD|password)\s*[:=]\s*[\'"`][^\'"`]+[\'"`]',
    ],
    'sql_injection': [
        r'(?:query|execute)\s*\(\s*[\'"`].*?\+.*?[\'"`]',  # String concatenation in SQL
        r'(?:query|execute)\s*\(\s*`.*?\$\{.*?\}.*?`',  # Template literals in SQL
        r'f[\'"`].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\{.*?\}',  # Python f-strings in SQL
    ],
    'xss_vulnerable': [
        r'innerHTML\s*=\s*(?!.*sanitize)',  # innerHTML without sanitization
        r'dangerouslySetInnerHTML',  # React dangerous HTML
        r'v-html\s*=',  # Vue v-html directive
        r'document\.write\(',  # document.write usage
    ],
    'missing_auth': [
        r'app\.(get|post|put|delete)\s*\([^)]*\)\s*,\s*(?:async\s+)?\(',  # Express route without middleware
        r'router\.(get|post|put|delete)\s*\([^)]*\)\s*,\s*(?:async\s+)?\(',  # Router without middleware
    ],
    'insecure_random': [
        r'Math\.random\(\)',  # Using Math.random for security
        r'random\.random\(\)',  # Python random for security
    ]
}

def check_authentication_middleware(file_path, content):
    """Check if API routes have authentication middleware"""
    issues = []
    
    # Skip if not an API file
    if not any(marker in str(file_path) for marker in ['api', 'routes', 'controllers', 'handlers']):
        return issues
    
    lines = content.split('\n')
    
    # Look for auth middleware patterns
    auth_patterns = [
        r'authenticate',
        r'requireAuth',
        r'isAuthenticated',
        r'checkAuth',
        r'verifyToken',
        r'passport\.',
        r'@auth_required',
        r'@login_required',
    ]
    
    # Find routes without authentication
    route_patterns = [
        r'(?:app|router)\.(get|post|put|patch|delete)\s*\([\'"`](.*?)[\'"`]',
        r'@(?:app|router)\.(get|post|put|patch|delete)\s*\([\'"`](.*?)[\'"`]',
    ]
    
    for i, line in enumerate(lines):
        for pattern in route_patterns:
            match = re.search(pattern, line)
            if match:
                method = match.group(1)
                route = match.group(2)
                
                # Skip public routes
                if any(public in route for public in ['/health', '/status', '/public', '/auth/login', '/auth/register']):
                    continue
                
                # Check if line has auth middleware
                has_auth = any(re.search(auth_pattern, line, re.IGNORECASE) for auth_pattern in auth_patterns)
                
                # Check next few lines for auth middleware
                if not has_auth:
                    for j in range(i-2, min(i+3, len(lines))):
                        if j >= 0 and any(re.search(auth_pattern, lines[j], re.IGNORECASE) for auth_pattern in auth_patterns):
                            has_auth = True
                            break
                
                if not has_auth:
                    issues.append({
                        'file': str(file_path),
                        'line': i + 1,
                        'type': 'missing_auth',
                        'route': f"{method.upper()} {route}",
                        'message': 'Route appears to lack authentication middleware'
                    })
    
    return issues

def check_rate_limiting(project_path):
    """Check if rate limiting is configured"""
    rate_limit_patterns = [
        r'express-rate-limit',
        r'rate-?limit',
        r'throttle',
        r'@ratelimit',
        r'RateLimiter',
    ]
    
    for file_path in project_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.js', '.ts', '.py']:
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
                continue
            
            content = file_path.read_text()
            for pattern in rate_limit_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
    
    return False

def check_cors_configuration(project_path):
    """Check if CORS is properly configured"""
    cors_patterns = [
        r'cors\(',
        r'enableCors\(',
        r'CORS\(',
        r'Access-Control-Allow-Origin',
    ]
    
    for file_path in project_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.js', '.ts', '.py']:
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
                continue
            
            content = file_path.read_text()
            for pattern in cors_patterns:
                if re.search(pattern, content):
                    # Check if it's not using wildcard
                    if re.search(r'origin:\s*[\'"`]\*[\'"`]', content):
                        return 'unsafe'
                    return 'configured'
    
    return False

def check_https_enforcement(project_path):
    """Check if HTTPS is enforced"""
    https_patterns = [
        r'forceSSL',
        r'requireHTTPS',
        r'app\.use\(.*https',
        r'redirect.*https',
    ]
    
    for file_path in project_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.js', '.ts', '.py']:
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
                continue
            
            content = file_path.read_text()
            for pattern in https_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
    
    return False

def validate_security():
    """Main validation function"""
    # Exit silently if not in Large Task Mode
    if not is_large_task_mode():
        sys.exit(0)
    
    issues = []
    project_path = Path.cwd()
    
    # Check for hardcoded secrets and vulnerabilities
    for pattern_type, patterns in SECURITY_PATTERNS.items():
        for file_path in project_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip excluded directories and files
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git', 'dist', 'build', '.env.example']):
                continue
            
            # Only check code files
            if file_path.suffix not in ['.js', '.jsx', '.ts', '.tsx', '.py', '.go', '.java']:
                continue
            
            content = file_path.read_text()
            lines = content.split('\n')
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Special handling for certain patterns
                    if pattern_type == 'hardcoded_secrets':
                        # Skip if it's reading from environment
                        line = lines[line_num - 1]
                        if 'process.env' in line or 'os.environ' in line or 'getenv' in line:
                            continue
                    
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'type': pattern_type,
                        'severity': 'critical' if pattern_type in ['hardcoded_secrets', 'sql_injection'] else 'high'
                    })
    
    # Check for missing authentication on routes
    for file_path in project_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.js', '.ts', '.py']:
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
                continue
            
            content = file_path.read_text()
            auth_issues = check_authentication_middleware(file_path, content)
            issues.extend(auth_issues)
    
    # Check for rate limiting
    if not check_rate_limiting(project_path):
        # Only add if we found API files
        if list(project_path.glob('**/api/**/*')) or list(project_path.glob('**/routes/**/*')):
            issues.append({
                'type': 'missing_rate_limiting',
                'message': 'No rate limiting configuration found',
                'severity': 'medium'
            })
    
    # Check CORS configuration
    cors_status = check_cors_configuration(project_path)
    if cors_status == 'unsafe':
        issues.append({
            'type': 'unsafe_cors',
            'message': 'CORS configured with wildcard origin (*)',
            'severity': 'high'
        })
    elif not cors_status:
        # Only add if we found API files
        if list(project_path.glob('**/api/**/*')) or list(project_path.glob('**/routes/**/*')):
            issues.append({
                'type': 'missing_cors',
                'message': 'No CORS configuration found',
                'severity': 'medium'
            })
    
    # Check HTTPS enforcement
    if not check_https_enforcement(project_path):
        # Only add if we found API files
        if list(project_path.glob('**/api/**/*')) or list(project_path.glob('**/routes/**/*')):
            issues.append({
                'type': 'missing_https',
                'message': 'No HTTPS enforcement found',
                'severity': 'medium'
            })
    
    # Report results
    if issues:
        # Group by severity
        critical = [i for i in issues if i.get('severity') == 'critical']
        high = [i for i in issues if i.get('severity') == 'high']
        medium = [i for i in issues if i.get('severity') == 'medium']
        
        report = []
        
        if critical:
            report.append(f"🚨 {len(critical)} CRITICAL security issues:")
            for issue in critical[:3]:
                if 'file' in issue:
                    report.append(f"  - {issue['type']}: {issue['file']}:{issue['line']}")
                else:
                    report.append(f"  - {issue['type']}: {issue.get('message', '')}")
        
        if high:
            report.append(f"❌ {len(high)} HIGH security issues:")
            for issue in high[:3]:
                if 'file' in issue:
                    report.append(f"  - {issue['type']}: {issue['file']}:{issue.get('line', '')}")
                else:
                    report.append(f"  - {issue['type']}: {issue.get('message', '')}")
        
        if medium:
            report.append(f"⚠️ {len(medium)} MEDIUM security issues:")
            for issue in medium[:3]:
                report.append(f"  - {issue['type']}: {issue.get('message', '')}")
        
        # Update validation log
        update_validation_log({
            'type': 'security',
            'status': 'failed',
            'critical_count': len(critical),
            'high_count': len(high),
            'medium_count': len(medium),
            'issues': issues[:20]  # Limit logged issues
        })
        
        # Block only for critical and high severity
        if critical or high:
            output = {
                "decision": "block",
                "reason": "Security vulnerabilities detected:\n" + "\n".join(report) + "\n\nFix critical issues immediately!"
            }
            json.dump(output, sys.stdout)
            sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    validate_security()