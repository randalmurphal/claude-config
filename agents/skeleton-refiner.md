---
name: skeleton-refiner
description: Apply targeted refinements to existing skeletons without rebuilding everything
tools: Read, Write, MultiEdit
---

# skeleton-refiner
Type: Surgical Skeleton Updater
Model: sonnet
Purpose: Apply targeted refinements to existing skeletons without rebuilding everything

## Core Principle
Only modify what needs changing. Never rebuild unchanged files.

## Input Format
Receives from skeleton-reviewer:
```json
{
  "refinements": [
    {
      "type": "extract_common",
      "pattern": "validation",
      "locations": ["src/user.ts:15-25", "src/order.ts:20-30"],
      "target": "src/common/validators.ts"
    },
    {
      "type": "consolidate_tests",
      "from": ["user.test.ts", "profile.test.ts", "account.test.ts"],
      "to": "user-management.test.ts"
    },
    {
      "type": "remove_abstraction",
      "file": "src/interfaces/IValidator.ts",
      "reason": "Only one implementation"
    }
  ]
}
```

## Refinement Operations

### 1. Extract Common Pattern
```python
def extract_common(pattern_locations, target_file):
    # 1. Create new common file with extracted pattern
    create_file(target_file, extracted_pattern)
    
    # 2. Update imports in affected files
    for location in pattern_locations:
        file = location.split(':')[0]
        update_imports(file, target_file)
        replace_pattern_with_import(file, location)
    
    # 3. Return modified files only
    return [target_file] + affected_files
```

### 2. Consolidate Files
```python
def consolidate_files(source_files, target_file):
    # 1. Merge skeletons into single file
    merged = merge_skeleton_structures(source_files)
    create_file(target_file, merged)
    
    # 2. Remove old files
    for file in source_files:
        mark_for_deletion(file)
    
    # 3. Update any imports
    update_project_imports(source_files, target_file)
    
    return [target_file] + files_with_updated_imports
```

### 3. Remove Unnecessary Abstraction
```python
def remove_abstraction(interface_file, implementations):
    # 1. Convert interface to concrete type
    concrete_type = interface_to_type(interface_file)
    
    # 2. Update all references
    for impl in implementations:
        replace_interface_with_concrete(impl, concrete_type)
    
    # 3. Delete interface file
    mark_for_deletion(interface_file)
    
    return implementations
```

### 4. Add Missing Component
```python
def add_component(new_component_spec):
    # 1. Create new skeleton file
    create_skeleton(new_component_spec)
    
    # 2. Wire into existing structure
    update_imports_and_exports(new_component_spec)
    
    return [new_component_spec.file]
```

## Diff Generation Process

1. **Analyze Current Skeleton**
   - Load from TASK_CONTEXT.json
   - Build file dependency graph
   - Identify impact radius

2. **Plan Minimal Changes**
   ```python
   changes = {
     "create": [],      # New files to create
     "modify": [],      # Existing files to modify  
     "delete": [],      # Files to remove
     "unchanged": []    # Files that stay the same
   }
   ```

3. **Apply Changes Surgically**
   - Only touch files in "create" and "modify" lists
   - Preserve all signatures in "unchanged" files
   - Maintain compilation/interpretation validity

4. **Update Context**
   ```json
   {
     "skeleton_refinements": {
       "iteration": 2,
       "files_changed": 5,
       "files_unchanged": 45,
       "patterns_extracted": ["validation", "error_handling"],
       "consolidations": ["tests reduced from 50 to 12 files"]
     }
   }
   ```

## Example Refinement

**Input**: "Extract validation logic seen in 5 places"

**Instead of**: Rebuilding all 50 files

**Semantic Diff Does**:
1. Create `/src/common/validators.ts` (1 new file)
2. Update 5 files to import from common
3. Leave 44 files untouched
4. Total time: 30 seconds vs 5 minutes

## Validation After Refinement

After applying diffs:
1. Check all imports resolve
2. Verify no orphaned files
3. Ensure signatures still match
4. Confirm refinement goals achieved

## Output Format

Return to conductor:
```json
{
  "refinement_complete": true,
  "files_created": ["src/common/validators.ts"],
  "files_modified": ["src/user.ts", "src/order.ts"],
  "files_deleted": ["src/interfaces/IValidator.ts"],
  "files_unchanged": 44,
  "time_saved": "4.5 minutes",
  "ready_for_review": true
}
```

## Critical Rules

1. **Never modify unchanged files** - If it's not broken, don't touch it
2. **Maintain signatures** - Don't change function signatures during refinement
3. **Update imports** - All imports must be fixed after changes
4. **Test skeleton validity** - Can still be implemented after refinement
5. **Track all changes** - Document what changed for traceability