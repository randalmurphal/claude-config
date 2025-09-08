#!/bin/bash

# Global Backup Script for Critical Files
# Works across all projects to protect important files

GLOBAL_BACKUP_DIR="$HOME/.claude/backups"
PROJECT_BACKUP_DIR=".backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Ensure global backup directory exists
mkdir -p "$GLOBAL_BACKUP_DIR"

# Function to determine if we're in a project directory
is_project_dir() {
    [[ -f "package.json" ]] || [[ -f "go.mod" ]] || [[ -f "requirements.txt" ]] || \
    [[ -f "Cargo.toml" ]] || [[ -f "pom.xml" ]] || [[ -f "build.gradle" ]] || \
    [[ -d ".git" ]]
}

# Function to backup a file with verification
backup_file() {
    local file="$1"
    local backup_dir="$2"
    
    if [[ ! -f "$file" ]]; then
        return 1
    fi
    
    local file_basename=$(basename "$file")
    local backup_path="$backup_dir/${file_basename}.${TIMESTAMP}.backup"
    
    cp -p "$file" "$backup_path" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        echo "✅ Backed up: $file"
        return 0
    else
        echo "❌ Failed to backup: $file"
        return 1
    fi
}

# Function to backup directory as archive
backup_directory() {
    local dir="$1"
    local backup_dir="$2"
    
    if [[ ! -d "$dir" ]]; then
        return 1
    fi
    
    local dir_basename=$(basename "$dir")
    local backup_path="$backup_dir/${dir_basename}_${TIMESTAMP}.tar.gz"
    
    tar -czf "$backup_path" "$dir" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        echo "✅ Archived: $dir"
        return 0
    else
        echo "❌ Failed to archive: $dir"
        return 1
    fi
}

# Determine backup location
if is_project_dir; then
    BACKUP_DIR="$PROJECT_BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    echo "📁 Using project backup directory: $BACKUP_DIR"
else
    BACKUP_DIR="$GLOBAL_BACKUP_DIR/$(basename "$PWD")_$TIMESTAMP"
    mkdir -p "$BACKUP_DIR"
    echo "📁 Using global backup directory: $BACKUP_DIR"
fi

echo "🔄 Starting critical files backup..."
echo "⏰ Timestamp: $TIMESTAMP"

# Critical configuration files
CRITICAL_FILES=(
    "package.json"
    "package-lock.json"
    "go.mod"
    "go.sum"
    "requirements.txt"
    "Pipfile"
    "Pipfile.lock"
    "Cargo.toml"
    "Cargo.lock"
    "pom.xml"
    "build.gradle"
    "docker-compose.yml"
    "docker-compose.yaml"
    "Dockerfile"
    ".env"
    ".env.local"
    ".env.production"
    "config.json"
    "config.yaml"
    "config.yml"
    "settings.json"
    ".gitignore"
    "README.md"
    "LICENSE"
    "CLAUDE.md"
)

# Backup each critical file if it exists
backup_count=0
for file in "${CRITICAL_FILES[@]}"; do
    if backup_file "$file" "$BACKUP_DIR"; then
        ((backup_count++))
    fi
done

# Backup database files
for db_file in *.db *.sqlite *.sqlite3; do
    if backup_file "$db_file" "$BACKUP_DIR"; then
        ((backup_count++))
    fi
done

# Backup data files (limit size to avoid huge backups)
for data_file in *.csv *.json *.xml; do
    if [[ -f "$data_file" ]]; then
        size=$(stat -f%z "$data_file" 2>/dev/null || stat -c%s "$data_file" 2>/dev/null)
        if [[ $size -lt 10485760 ]]; then  # Less than 10MB
            if backup_file "$data_file" "$BACKUP_DIR"; then
                ((backup_count++))
            fi
        else
            echo "⚠️  Skipped large file: $data_file ($(numfmt --to=iec $size))"
        fi
    fi
done

# Backup small directories
BACKUP_DIRS=("config" "configs" "settings" ".vscode" ".idea")
for dir in "${BACKUP_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        dir_size=$(du -s "$dir" | cut -f1)
        if [[ $dir_size -lt 10240 ]]; then  # Less than 10MB
            if backup_directory "$dir" "$BACKUP_DIR"; then
                ((backup_count++))
            fi
        else
            echo "⚠️  Skipped large directory: $dir"
        fi
    fi
done

# Clean up old backups (keep last 20)
if [[ "$BACKUP_DIR" == "$PROJECT_BACKUP_DIR" ]]; then
    echo "🧹 Cleaning old project backups..."
    cd "$BACKUP_DIR" 2>/dev/null && ls -t | tail -n +21 | xargs -r rm 2>/dev/null
fi

# Summary
echo ""
echo "✨ Backup complete!"
echo "📊 Files backed up: $backup_count"
echo "📍 Backup location: $BACKUP_DIR"

# Create restore script
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
# Restore script for this backup
echo "This directory contains backups from $(date)"
echo "To restore a file: cp [backup_file] [original_location]"
echo "Files in this backup:"
ls -la
EOF
chmod +x "$BACKUP_DIR/restore.sh"