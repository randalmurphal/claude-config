#!/usr/bin/env python3
"""Continuous improvement system - learns from each project to improve orchestration"""

import json
from pathlib import Path
from datetime import datetime

def aggregate_learnings():
    """Aggregate learnings from multiple projects"""
    global_learnings_file = Path.home() / '.claude' / 'ORCHESTRATION_LEARNINGS.json'
    
    # Load existing global learnings
    if global_learnings_file.exists():
        global_learnings = json.loads(global_learnings_file.read_text())
    else:
        global_learnings = {
            'projects_analyzed': 0,
            'common_failures': {},
            'successful_patterns': {},
            'validator_performance': {},
            'sub_agent_performance': {},
            'recommended_adjustments': []
        }
    
    # Load current project's retrospective
    retrospective = Path('.claude/RETROSPECTIVE_REPORT.json')
    if not retrospective.exists():
        return
    
    report = json.loads(retrospective.read_text())
    
    # Update global statistics
    global_learnings['projects_analyzed'] += 1
    
    # Aggregate validator performance
    for validator, stats in report['effectiveness']['validators'].items():
        if validator not in global_learnings['validator_performance']:
            global_learnings['validator_performance'][validator] = {
                'total_triggers': 0,
                'total_failures': 0,
                'projects_used': 0
            }
        
        global_learnings['validator_performance'][validator]['total_triggers'] += stats['triggers']
        global_learnings['validator_performance'][validator]['total_failures'] += stats['failures']
        global_learnings['validator_performance'][validator]['projects_used'] += 1
    
    # Track common failure patterns
    for failure_type, count in report['metrics']['stats'].get('validation_failures', {}).items():
        if failure_type not in global_learnings['common_failures']:
            global_learnings['common_failures'][failure_type] = 0
        global_learnings['common_failures'][failure_type] += count
    
    # Track successful patterns
    for pattern in report['effectiveness']['patterns']['successful']:
        if pattern not in global_learnings['successful_patterns']:
            global_learnings['successful_patterns'][pattern] = 0
        global_learnings['successful_patterns'][pattern] += 1
    
    # Generate insights after multiple projects
    if global_learnings['projects_analyzed'] >= 3:
        global_learnings['insights'] = generate_insights(global_learnings)
    
    # Save updated learnings
    global_learnings_file.parent.mkdir(exist_ok=True)
    global_learnings_file.write_text(json.dumps(global_learnings, indent=2))
    
    return global_learnings

def generate_insights(learnings):
    """Generate insights from aggregated learnings"""
    insights = {
        'validator_adjustments': {},
        'process_improvements': [],
        'new_features_needed': []
    }
    
    # Analyze validator effectiveness across projects
    for validator, stats in learnings['validator_performance'].items():
        if stats['projects_used'] >= 2:
            failure_rate = stats['total_failures'] / stats['total_triggers'] if stats['total_triggers'] > 0 else 0
            
            if failure_rate > 0.7:
                insights['validator_adjustments'][validator] = 'Too strict - reduce thresholds'
            elif failure_rate < 0.1 and stats['total_triggers'] > 10:
                insights['validator_adjustments'][validator] = 'Too lenient or unnecessary'
    
    # Identify systemic issues
    for failure_type, count in learnings['common_failures'].items():
        if count > learnings['projects_analyzed'] * 2:  # Averaging >2 per project
            if failure_type == 'error_handling':
                insights['process_improvements'].append(
                    'Error handling consistently fails - need better error-designer agent'
                )
            elif failure_type == 'security':
                insights['process_improvements'].append(
                    'Security issues common - run security-auditor earlier in process'
                )
            elif failure_type == 'documentation':
                insights['process_improvements'].append(
                    'Documentation always lacking - make doc-maintainer run automatically'
                )
    
    # Identify missing features
    if learnings['projects_analyzed'] >= 5:
        avg_score = sum(p.get('overall_score', 0) for p in []) / learnings['projects_analyzed']
        if avg_score < 7:
            insights['new_features_needed'].append(
                'Overall scores consistently low - need better initial architecture planning'
            )
    
    return insights

def apply_learnings():
    """Apply learnings to improve orchestration templates"""
    learnings_file = Path.home() / '.claude' / 'ORCHESTRATION_LEARNINGS.json'
    
    if not learnings_file.exists():
        return
    
    learnings = json.loads(learnings_file.read_text())
    
    if 'insights' not in learnings:
        return
    
    # Create improvement recommendations file
    improvements = {
        'timestamp': datetime.now().isoformat(),
        'based_on_projects': learnings['projects_analyzed'],
        'automatic_adjustments': [],
        'manual_review_needed': []
    }
    
    # Suggest automatic adjustments
    for validator, adjustment in learnings['insights'].get('validator_adjustments', {}).items():
        if 'Too strict' in adjustment:
            improvements['automatic_adjustments'].append({
                'type': 'validator_threshold',
                'validator': validator,
                'action': 'increase_tolerance',
                'reason': f"Failed {learnings['validator_performance'][validator]['total_failures']} times across projects"
            })
        elif 'Too lenient' in adjustment:
            improvements['manual_review_needed'].append({
                'type': 'validator_review',
                'validator': validator,
                'issue': 'May be unnecessary',
                'evidence': f"Only {learnings['validator_performance'][validator]['total_failures']} failures in {learnings['validator_performance'][validator]['total_triggers']} triggers"
            })
    
    # Process improvements
    for improvement in learnings['insights'].get('process_improvements', []):
        improvements['manual_review_needed'].append({
            'type': 'process_change',
            'recommendation': improvement
        })
    
    # Save improvements file
    improvements_file = Path.home() / '.claude' / 'ORCHESTRATION_IMPROVEMENTS.json'
    improvements_file.write_text(json.dumps(improvements, indent=2))
    
    return improvements

def main():
    """Run continuous improvement analysis"""
    # Aggregate learnings from current project
    learnings = aggregate_learnings()
    
    if learnings and learnings['projects_analyzed'] > 0:
        # Apply learnings to generate improvements
        improvements = apply_learnings()
        
        # Create summary
        summary = f"""
# Orchestration Continuous Improvement

## Projects Analyzed: {learnings['projects_analyzed']}

## Most Common Issues:
{chr(10).join(f"- {k}: {v} occurrences" for k, v in sorted(learnings['common_failures'].items(), key=lambda x: x[1], reverse=True)[:5])}

## Most Successful Patterns:
{chr(10).join(f"- {k}: {v} times" for k, v in sorted(learnings['successful_patterns'].items(), key=lambda x: x[1], reverse=True)[:5])}

## Recommended Adjustments:
{chr(10).join(f"- {k}: {v}" for k, v in learnings.get('insights', {}).get('validator_adjustments', {}).items())}

See ~/.claude/ORCHESTRATION_IMPROVEMENTS.json for detailed recommendations.
"""
        
        # Write summary to file for review
        summary_file = Path.home() / '.claude' / 'IMPROVEMENT_SUMMARY.md'
        summary_file.write_text(summary)

if __name__ == "__main__":
    main()