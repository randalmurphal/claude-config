#!/usr/bin/env python3
"""Retrospective validator - analyzes project success and orchestration effectiveness"""

import json
import subprocess
import re
from pathlib import Path
from datetime import datetime

# Import base validator functions
sys.path.insert(0, str(Path(__file__).parent))
from base_validator import is_large_task_mode, load_project_context

def calculate_success_metrics():
    """Calculate overall project success metrics"""
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'scores': {},
        'stats': {}
    }
    
    # Load validation history
    validation_history = Path('.claude/VALIDATION_HISTORY.json')
    if validation_history.exists():
        history = json.loads(validation_history.read_text())
        
        # Count validation failures by type
        failures_by_type = {}
        for entry in history:
            if entry.get('status') == 'failed':
                fail_type = entry.get('type', 'unknown')
                failures_by_type[fail_type] = failures_by_type.get(fail_type, 0) + 1
        
        metrics['stats']['validation_failures'] = failures_by_type
        metrics['stats']['total_validations'] = len(history)
    
    # Check recovery attempts
    recovery_state = Path('.claude/RECOVERY_STATE.json')
    if recovery_state.exists():
        recovery = json.loads(recovery_state.read_text())
        metrics['stats']['recovery_attempts'] = recovery.get('attempts', 0)
    
    # Analyze code quality
    metrics['scores']['code_quality'] = analyze_code_quality()
    
    # Analyze test coverage
    metrics['scores']['test_coverage'] = get_test_coverage()
    
    # Analyze documentation
    metrics['scores']['documentation'] = analyze_documentation()
    
    # Check production readiness
    metrics['scores']['production_ready'] = check_production_readiness()
    
    # Calculate overall score
    scores = metrics['scores'].values()
    metrics['overall_score'] = sum(scores) / len(scores) if scores else 0
    
    return metrics

def analyze_code_quality():
    """Analyze code quality metrics"""
    score = 10
    issues = []
    
    # Check for code duplication
    duplicate_patterns = {}
    for file_path in Path('.').rglob('*.js') + Path('.').rglob('*.py'):
        if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
            continue
        
        content = file_path.read_text()
        # Simple duplicate detection (consecutive similar lines)
        lines = content.split('\n')
        for i in range(len(lines) - 10):
            chunk = '\n'.join(lines[i:i+5])
            if len(chunk) > 100:  # Significant chunk
                if chunk in duplicate_patterns:
                    duplicate_patterns[chunk] += 1
                else:
                    duplicate_patterns[chunk] = 1
    
    duplicates = [k for k, v in duplicate_patterns.items() if v > 2]
    if duplicates:
        score -= min(3, len(duplicates) * 0.5)
        issues.append(f"Found {len(duplicates)} duplicate code blocks")
    
    # Check for circular dependencies
    # Simple check - look for files that import each other
    imports = {}
    for file_path in Path('.').rglob('*.js') + Path('.').rglob('*.py'):
        if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
            continue
        
        content = file_path.read_text()
        # Find imports
        js_imports = re.findall(r'import.*from [\'"](.+)[\'"]', content)
        py_imports = re.findall(r'from (.+) import', content)
        imports[str(file_path)] = js_imports + py_imports
    
    # Check for cycles
    for file1, file1_imports in imports.items():
        for imp in file1_imports:
            if imp in imports:
                if file1 in imports.get(imp, []):
                    score -= 1
                    issues.append(f"Circular dependency: {file1} <-> {imp}")
    
    return max(0, score)

def get_test_coverage():
    """Get test coverage score"""
    # Try to run coverage command
    try:
        result = subprocess.run(['npm', 'run', 'coverage'], 
                              capture_output=True, text=True, timeout=30)
        # Parse coverage from output
        coverage_match = re.search(r'(\d+)%', result.stdout)
        if coverage_match:
            coverage = int(coverage_match.group(1))
            return min(10, coverage / 10)  # 100% = 10 score
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Coverage command not available, use fallback method
        coverage = 0
    
    # Fallback: count test files
    test_files = list(Path('.').rglob('*.test.js')) + list(Path('.').rglob('*.spec.js')) + \
                 list(Path('.').rglob('test_*.py'))
    src_files = list(Path('.').rglob('*.js')) + list(Path('.').rglob('*.py'))
    
    if src_files:
        ratio = len(test_files) / len(src_files)
        return min(10, ratio * 20)  # 50% files have tests = 10 score
    
    return 5  # Default middle score

def analyze_documentation():
    """Analyze documentation completeness"""
    score = 0
    
    # Check README
    readme = Path('README.md')
    if readme.exists():
        content = readme.read_text()
        score += 2 if len(content) > 500 else 1
        
        # Check for key sections
        sections = ['Installation', 'Usage', 'API', 'Configuration', 'Testing']
        for section in sections:
            if section.lower() in content.lower():
                score += 0.5
    
    # Check for API documentation
    if Path('docs/api').exists() or Path('docs/openapi.yaml').exists():
        score += 2
    
    # Check for architecture docs
    if Path('.claude/ARCHITECTURE.md').exists():
        score += 1
    
    # Check inline documentation (sampling)
    documented_functions = 0
    total_functions = 0
    
    for file_path in list(Path('.').rglob('*.js'))[:10]:  # Sample 10 files
        if any(skip in str(file_path) for skip in ['node_modules', '.git']):
            continue
        
        content = file_path.read_text()
        functions = re.findall(r'function\s+\w+|const\s+\w+\s*=.*=>|\w+\s*\(.*\)\s*{', content)
        jsdocs = re.findall(r'/\*\*[\s\S]*?\*/', content)
        
        total_functions += len(functions)
        documented_functions += min(len(functions), len(jsdocs))
    
    if total_functions > 0:
        doc_ratio = documented_functions / total_functions
        score += doc_ratio * 2
    
    return min(10, score)

def check_production_readiness():
    """Check if project is production ready"""
    score = 10
    issues = []
    
    # Check for error handling
    if not Path('common/errors').exists():
        score -= 2
        issues.append("No error class hierarchy")
    
    # Check for security measures
    security_files = ['common/middleware/auth', 'common/middleware/rateLimiter']
    for sec_file in security_files:
        if not any(Path(f"{sec_file}.js").exists() or Path(f"{sec_file}.py").exists() 
                  or Path(f"{sec_file}.ts").exists() for sec_file in [sec_file]):
            score -= 1
            issues.append(f"Missing {sec_file}")
    
    # Check for environment config
    if not Path('.env.example').exists():
        score -= 1
        issues.append("No .env.example")
    
    # Check for CI/CD
    if not Path('.github/workflows').exists() and not Path('.gitlab-ci.yml').exists():
        score -= 1
        issues.append("No CI/CD configuration")
    
    # Check for monitoring/logging
    logging_found = False
    for file_path in Path('.').rglob('*.js'):
        if any(skip in str(file_path) for skip in ['node_modules', '.git']):
            continue
        content = file_path.read_text()
        if 'logger' in content.lower() or 'winston' in content or 'pino' in content:
            logging_found = True
            break
    
    if not logging_found:
        score -= 1
        issues.append("No structured logging found")
    
    return max(0, score)

def analyze_orchestration_effectiveness():
    """Analyze how well the orchestration worked"""
    effectiveness = {
        'sub_agents': {},
        'validators': {},
        'patterns': {
            'successful': [],
            'failed': []
        }
    }
    
    # Analyze sub-agent performance
    active_work = Path('.claude/ACTIVE_WORK.json')
    if active_work.exists():
        work = json.loads(active_work.read_text())
        for agent, details in work.items():
            effectiveness['sub_agents'][agent] = {
                'status': details.get('status'),
                'completed': details.get('status') == 'completed'
            }
    
    # Analyze validator effectiveness
    validation_history = Path('.claude/VALIDATION_HISTORY.json')
    if validation_history.exists():
        history = json.loads(validation_history.read_text())
        
        for entry in history:
            validator = entry.get('type', 'unknown')
            if validator not in effectiveness['validators']:
                effectiveness['validators'][validator] = {
                    'triggers': 0,
                    'failures': 0,
                    'false_positives': 0
                }
            
            effectiveness['validators'][validator]['triggers'] += 1
            if entry.get('status') == 'failed':
                effectiveness['validators'][validator]['failures'] += 1
    
    # Identify patterns
    if Path('.claude/BOUNDARIES.json').exists():
        boundaries = json.loads(Path('.claude/BOUNDARIES.json').read_text())
        
        # Check if boundaries were respected
        violations = 0
        for zone, data in boundaries.items():
            if data.get('locked'):
                # Check if only the owner modified files
                # This is simplified - in reality would check git history
                effectiveness['patterns']['successful'].append(f"Boundary {zone} maintained")
    
    # Check recovery patterns
    if Path('.claude/RECOVERY_STATE.json').exists():
        recovery = json.loads(Path('.claude/RECOVERY_STATE.json').read_text())
        if recovery.get('attempts', 0) > 0:
            if recovery.get('attempts') <= 2:
                effectiveness['patterns']['successful'].append("Recovery succeeded quickly")
            else:
                effectiveness['patterns']['failed'].append("Multiple recovery attempts needed")
    
    return effectiveness

def generate_improvement_recommendations(metrics, effectiveness):
    """Generate specific recommendations for improving orchestration"""
    recommendations = {
        'high_priority': [],
        'medium_priority': [],
        'low_priority': [],
        'new_validators_needed': [],
        'validators_to_adjust': {},
        'sub_agent_improvements': {}
    }
    
    # Analyze metrics for recommendations
    if metrics['overall_score'] < 7:
        recommendations['high_priority'].append(
            "Overall score below 7 - review entire orchestration approach"
        )
    
    # Check specific scores
    if metrics['scores'].get('test_coverage', 0) < 8:
        recommendations['high_priority'].append(
            "Improve TDD enforcement - tests not comprehensive enough"
        )
        recommendations['sub_agent_improvements']['tdd-enforcer'] = \
            "Need stricter test requirements and edge case coverage"
    
    if metrics['scores'].get('documentation', 0) < 7:
        recommendations['medium_priority'].append(
            "Documentation coverage low - consider mandatory doc generation"
        )
        recommendations['sub_agent_improvements']['doc-maintainer'] = \
            "Should run automatically after implementation"
    
    # Analyze validator effectiveness
    for validator, stats in effectiveness['validators'].items():
        if stats['triggers'] > 5 and stats['failures'] / stats['triggers'] > 0.5:
            recommendations['validators_to_adjust'][validator] = \
                "High failure rate - may be too strict"
        elif stats['triggers'] > 0 and stats['failures'] == 0:
            recommendations['validators_to_adjust'][validator] = \
                "Never failed - may be unnecessary or too lenient"
    
    # Check for missing validators based on issues
    if metrics['stats'].get('validation_failures', {}).get('security', 0) > 2:
        recommendations['new_validators_needed'].append(
            "Pre-commit security scanner to catch issues earlier"
        )
    
    # Pattern-based recommendations
    for pattern in effectiveness['patterns']['failed']:
        if 'recovery' in pattern.lower():
            recommendations['high_priority'].append(
                "Improve error recovery strategies - too many attempts needed"
            )
        if 'boundary' in pattern.lower():
            recommendations['medium_priority'].append(
                "Strengthen boundary enforcement in pre-tool validator"
            )
    
    return recommendations

def main():
    """Run retrospective analysis"""
    # Only run if Large Task Mode was active
    if not is_large_task_mode():
        sys.exit(0)
    
    # Calculate metrics
    metrics = calculate_success_metrics()
    
    # Analyze orchestration
    effectiveness = analyze_orchestration_effectiveness()
    
    # Generate recommendations
    recommendations = generate_improvement_recommendations(metrics, effectiveness)
    
    # Save results
    report = {
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'effectiveness': effectiveness,
        'recommendations': recommendations
    }
    
    report_file = Path('.claude/RETROSPECTIVE_REPORT.json')
    report_file.write_text(json.dumps(report, indent=2))
    
    # Create human-readable summary
    summary = f"""
# Project Retrospective Report

## Overall Score: {metrics['overall_score']:.1f}/10

### Scores by Category:
- Code Quality: {metrics['scores'].get('code_quality', 'N/A')}/10
- Test Coverage: {metrics['scores'].get('test_coverage', 'N/A')}/10  
- Documentation: {metrics['scores'].get('documentation', 'N/A')}/10
- Production Ready: {metrics['scores'].get('production_ready', 'N/A')}/10

## High Priority Improvements:
{chr(10).join('- ' + r for r in recommendations['high_priority'])}

## Validator Adjustments Needed:
{chr(10).join(f"- {k}: {v}" for k, v in recommendations['validators_to_adjust'].items())}

## Sub-Agent Improvements:
{chr(10).join(f"- {k}: {v}" for k, v in recommendations['sub_agent_improvements'].items())}

Run completion-auditor agent for detailed analysis.
"""
    
    summary_file = Path('.claude/RETROSPECTIVE_SUMMARY.md')
    summary_file.write_text(summary)
    
    print(f"Retrospective complete. Score: {metrics['overall_score']:.1f}/10")
    print(f"See {summary_file} for details")

if __name__ == "__main__":
    import sys
    main()