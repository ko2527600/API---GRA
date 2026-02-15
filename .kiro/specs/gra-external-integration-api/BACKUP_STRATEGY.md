# Database Backup Strategy

## Overview

This document outlines the comprehensive database backup and disaster recovery strategy for the GRA External Integration API. The strategy ensures data protection, compliance with GRA requirements, and business continuity.

---

## 1. Backup Requirements

### 1.1 Compliance Requirements

- **REQ-INT-009**: Implement database backups
- **REQ-AUDIT-013**: Retain audit logs for minimum 7 years
- **REQ-AUDIT-014**: Retain submission records for minimum 7 years
- **REQ-AUDIT-015**: Implement data archival strategy
- **REQ-COM-001**: Ensure data protection and confidentiality

### 1.2 Business Requirements

- Minimize data loss (RPO: Recovery Point Objective)
- Minimize downtime (RTO: Recovery Time Objective)
- Support disaster recovery scenarios
- Enable point-in-time recovery
- Maintain backup integrity and verifiability

---

## 2. Backup Architecture

### 2.1 Backup Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  BackupService (app/services/backup_service.py)     │   │
│  │  - Orchestrates backup operations                    │   │
│  │  - Manages backup lifecycle                          │   │
│  │  - Handles verification and cleanup                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Scheduler Layer                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  BackupScheduler (app/services/backup_scheduler.py) │   │
│  │  - APScheduler for automated backups                 │   │
│  │  - Cron-based scheduling                             │   │
│  │  - Cleanup job management                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Utility Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DatabaseBackupManager (app/utils/backup.py)        │   │
│  │  - pg_dump for backup creation                       │   │
│  │  - psql for restoration                              │   │
│  │  - Compression and decompression                     │   │
│  │  - Backup listing and statistics                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Storage Layer                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Backup Directory (backups/)                   │   │
│  │  - Primary backup storage                            │   │
│  │  - Compressed SQL files (.sql.gz)                    │   │
│  │  - Timestamped naming convention                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Archive Directory (archives/)                       │   │
│  │  - Long-term storage for aged backups                │   │
│  │  - Compliance retention (7 years)                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Key Components

#### BackupService
- **Location**: `app/services/backup_service.py`
- **Responsibilities**:
  - Orchestrate backup operations
  - Track backup status and history
  - Verify backup integrity
  - Manage retention policies
  - Provide status reporting

#### BackupScheduler
- **Location**: `app/services/backup_scheduler.py`
- **Responsibilities**:
  - Initialize and manage APScheduler
  - Schedule daily backups
  - Schedule weekly cleanup jobs
  - Handle scheduler lifecycle

#### DatabaseBackupManager
- **Location**: `app/utils/backup.py`
- **Responsibilities**:
  - Execute pg_dump for backups
  - Execute psql for restoration
  - Handle compression/decompression
  - List and analyze backups
  - Calculate backup statistics

#### BackupConfig
- **Location**: `app/config/backup_config.py`
- **Responsibilities**:
  - Centralize backup configuration
  - Load settings from environment variables
  - Provide configuration defaults

---

## 3. Backup Strategy

### 3.1 Backup Schedule

| Backup Type | Frequency | Time | Retention |
|-------------|-----------|------|-----------|
| Daily Full Backup | Daily | 2:00 AM UTC | 30 days |
| Weekly Cleanup | Weekly | Sunday 3:00 AM UTC | N/A |
| Manual Backup | On-demand | Any time | 30 days |

### 3.2 Backup Configuration

```python
# Environment Variables (from .env)
BACKUP_DIR=backups                          # Local backup directory
ENABLE_SCHEDULED_BACKUPS=True               # Enable automated backups
BACKUP_SCHEDULE_HOUR=2                      # Backup time (hour)
BACKUP_SCHEDULE_MINUTE=0                    # Backup time (minute)
BACKUP_RETENTION_DAYS=30                    # Retention period
COMPRESS_BACKUPS=True                       # Enable compression
VERIFY_BACKUP_INTEGRITY=True                # Verify after backup
ENABLE_BACKUP_NOTIFICATIONS=False           # Email notifications
BACKUP_NOTIFICATION_EMAIL=admin@example.com # Notification email
ENABLE_ARCHIVAL=True                        # Enable archival
ARCHIVE_DIR=archives                        # Archive directory
ARCHIVE_AFTER_DAYS=365                      # Archive after 1 year
ENABLE_REMOTE_BACKUP=False                  # Remote backup support
```

### 3.3 Backup Process Flow

```
1. Backup Trigger
   ├─ Scheduled (daily at 2:00 AM)
   ├─ Manual (via CLI or API)
   └─ On-demand (via API endpoint)

2. Pre-Backup Checks
   ├─ Verify database connectivity
   ├─ Check backup directory availability
   └─ Ensure sufficient disk space

3. Backup Execution
   ├─ Execute pg_dump with full schema and data
   ├─ Generate timestamped backup file
   └─ Monitor backup progress

4. Post-Backup Processing
   ├─ Compress backup file (gzip)
   ├─ Verify backup integrity
   ├─ Calculate backup statistics
   └─ Log backup completion

5. Retention Management
   ├─ Check backup age against retention policy
   ├─ Archive old backups (if enabled)
   └─ Delete expired backups
```

---

## 4. Backup Operations

### 4.1 Creating Backups

#### Automated Backup
```bash
# Backups run automatically at configured time (2:00 AM UTC)
# No manual intervention required
```

#### Manual Backup via CLI
```bash
# Create a backup immediately
python scripts/backup.py backup

# Create uncompressed backup
python scripts/backup.py backup --no-compress
```

#### Manual Backup via API
```python
from app.services.backup_service import BackupService

backup_service = BackupService()
success, message = backup_service.perform_backup()
```

### 4.2 Listing Backups

#### Via CLI
```bash
python scripts/backup.py list
```

#### Output Example
```
Found 5 backup(s):

1. backup_gra_db_20250210_020000.sql.gz
   Size: 45.23 MB
   Modified: 2025-02-10T02:00:15
   Compressed: True

2. backup_gra_db_20250209_020000.sql.gz
   Size: 44.98 MB
   Modified: 2025-02-09T02:00:12
   Compressed: True
```

### 4.3 Restoring from Backup

#### Via CLI
```bash
# Restore from specific backup
python scripts/backup.py restore backups/backup_gra_db_20250210_020000.sql.gz

# Confirmation prompt will appear
# Are you sure? This will overwrite the current database. (yes/no):
```

#### Via API
```python
from app.services.backup_service import BackupService

backup_service = BackupService()
success, message = backup_service.restore_from_backup(
    "backups/backup_gra_db_20250210_020000.sql.gz"
)
```

#### Restoration Process
1. Verify backup file exists and is readable
2. Decompress if necessary (for .gz files)
3. Connect to database
4. Execute psql with backup SQL
5. Verify restoration success
6. Clean up temporary files

### 4.4 Cleanup Operations

#### Manual Cleanup
```bash
# Clean up backups older than 30 days (default)
python scripts/backup.py cleanup

# Clean up backups older than 60 days
python scripts/backup.py cleanup --days 60
```

#### Automatic Cleanup
- Runs weekly on Sunday at 3:00 AM UTC
- Removes backups older than `BACKUP_RETENTION_DAYS`
- Logs freed disk space

---

## 5. Backup Verification

### 5.1 Integrity Verification

Backups are automatically verified after creation:

```python
# Verification checks:
1. File exists and is readable
2. File size is non-zero
3. For compressed files: gzip integrity check
4. For uncompressed files: basic file validation
```

### 5.2 Verification Status

```bash
# Check backup status
python scripts/backup.py status

# Output:
# Backup Status:
#   Last Backup: 2025-02-10T02:00:15
#   Last Status: True
#   Total Backups: 5
#   Total Size: 225.45 MB
#   Oldest: 2025-02-06T02:00:12
#   Newest: 2025-02-10T02:00:15
#   Directory: backups/
```

### 5.3 Restore Testing

Regular restore testing is recommended:

```bash
# 1. Create test database
createdb gra_db_test

# 2. Restore backup to test database
PGPASSWORD=password psql -h localhost -U postgres -d gra_db_test < backup_file.sql

# 3. Verify data integrity
SELECT COUNT(*) FROM submissions;
SELECT COUNT(*) FROM audit_logs;

# 4. Drop test database
dropdb gra_db_test
```

---

## 6. Retention Policy

### 6.1 Data Retention Schedule

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| Database Backups | 30 days | Disaster recovery window |
| Audit Logs | 7 years | GRA compliance requirement |
| Submission Records | 7 years | GRA compliance requirement |
| Archived Backups | 7 years | Long-term compliance |

### 6.2 Archival Strategy

```
Timeline:
├─ Days 0-30: Active Backups (backups/ directory)
│  └─ Used for disaster recovery
│  └─ Automatically cleaned up after 30 days
│
├─ Days 31-365: Archived Backups (archives/ directory)
│  └─ Moved from active backups
│  └─ Retained for compliance
│  └─ Accessible for historical recovery
│
└─ After 365 days: Long-term Archive
   └─ Consider external storage
   └─ Maintain for 7-year compliance
```

### 6.3 Retention Policy Retrieval

```bash
# View retention policy
python scripts/backup.py policy

# Output:
# Data Retention Policy:
#   Backup Retention: 30 days
#   Audit Log Retention: 7 years
#   Submission Retention: 7 years
#   Archive After: 365 days
#   Archival Enabled: True
#
# Compliance Notes:
#   audit_logs: Retained for 7 years per GRA compliance requirements
#   submissions: Retained for 7 years per GRA compliance requirements
#   backups: Retained for 30 days for disaster recovery
```

---

## 7. Disaster Recovery

### 7.1 Recovery Scenarios

#### Scenario 1: Data Corruption
```
1. Identify corruption in production database
2. Stop application to prevent further writes
3. Restore from most recent backup
4. Verify data integrity
5. Resume application
```

#### Scenario 2: Accidental Data Deletion
```
1. Identify deletion time
2. Find backup created after deletion but before discovery
3. Restore from backup to test environment
4. Verify recovered data
5. Restore to production if acceptable
```

#### Scenario 3: Complete Database Failure
```
1. Provision new database server
2. Create empty database
3. Restore from most recent backup
4. Verify all tables and data
5. Update connection strings
6. Resume application
```

### 7.2 Recovery Time Objectives (RTO)

| Scenario | RTO | Notes |
|----------|-----|-------|
| Data Corruption | 30 minutes | Restore from backup |
| Accidental Deletion | 1 hour | Identify and restore backup |
| Database Failure | 2 hours | Provision new server + restore |
| Complete System Failure | 4 hours | Full infrastructure recovery |

### 7.3 Recovery Point Objectives (RPO)

| Backup Type | RPO | Notes |
|-------------|-----|-------|
| Daily Backup | 24 hours | Maximum data loss |
| Hourly Backup | 1 hour | With additional configuration |
| Continuous Replication | Near-zero | Requires additional setup |

---

## 8. Monitoring and Alerting

### 8.1 Backup Monitoring

```python
# Get backup status
from app.services.backup_service import BackupService

backup_service = BackupService()
status = backup_service.get_backup_status()

# Status includes:
# - last_backup_time: ISO timestamp of last backup
# - last_backup_status: Success/failure of last backup
# - total_backups: Number of backups in retention
# - total_size_mb: Total size of all backups
# - oldest_backup: Timestamp of oldest backup
# - newest_backup: Timestamp of newest backup
# - backup_directory: Path to backup directory
# - retention_days: Configured retention period
# - compression_enabled: Compression status
# - scheduled_backups_enabled: Scheduler status
# - recent_backups: List of 5 most recent backups
```

### 8.2 Scheduler Status

```python
from app.services.backup_scheduler import get_scheduler_status

status = get_scheduler_status()

# Status includes:
# - enabled: Whether scheduled backups are enabled
# - running: Whether scheduler is currently running
# - jobs: List of scheduled jobs with next run times
```

### 8.3 Alert Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Backup failed | Critical | Investigate immediately |
| No backup in 48 hours | High | Check scheduler status |
| Backup size anomaly | Medium | Verify data integrity |
| Insufficient disk space | High | Clean up old backups |
| Restore test failed | Critical | Verify backup integrity |

---

## 9. Security Considerations

### 9.1 Backup Security

- **Encryption**: Backups stored in plain text (consider adding encryption)
- **Access Control**: Restrict backup directory permissions
- **Credentials**: Database password passed via environment variable
- **Audit Trail**: All backup operations logged

### 9.2 Secure Backup Practices

```bash
# Set restrictive permissions on backup directory
chmod 700 backups/
chmod 700 archives/

# Verify backup file permissions
ls -la backups/

# Encrypt sensitive backups (optional)
gpg --symmetric backup_file.sql.gz
```

### 9.3 Credential Management

```python
# Database credentials from environment
DATABASE_URL=postgresql://user:password@host:port/database

# Password passed securely via PGPASSWORD
env["PGPASSWORD"] = self.db_password
```

---

## 10. Maintenance and Testing

### 10.1 Regular Maintenance Tasks

| Task | Frequency | Owner |
|------|-----------|-------|
| Verify backup completion | Daily | Automated |
| Review backup logs | Weekly | DevOps |
| Test restore procedure | Monthly | DevOps |
| Verify retention policy | Quarterly | DBA |
| Update backup documentation | Annually | DevOps |

### 10.2 Restore Testing Procedure

```bash
# Monthly restore test procedure

# 1. Create test environment
createdb gra_db_test

# 2. Select random backup from last 30 days
ls -lt backups/ | head -5

# 3. Restore to test database
PGPASSWORD=password psql -h localhost -U postgres -d gra_db_test < backup_file.sql

# 4. Verify data integrity
psql -h localhost -U postgres -d gra_db_test << EOF
SELECT COUNT(*) as submission_count FROM submissions;
SELECT COUNT(*) as audit_count FROM audit_logs;
SELECT MAX(created_at) as latest_submission FROM submissions;
EOF

# 5. Document results
echo "Restore test completed successfully on $(date)" >> restore_test_log.txt

# 6. Clean up
dropdb gra_db_test
```

### 10.3 Backup Validation Checklist

- [ ] Backup file created successfully
- [ ] Backup file size is reasonable (not zero)
- [ ] Backup file is readable
- [ ] Compression applied (if enabled)
- [ ] Backup timestamp is current
- [ ] Backup logged in audit trail
- [ ] Retention policy applied
- [ ] Old backups cleaned up

---

## 11. Troubleshooting

### 11.1 Common Issues

#### Issue: Backup fails with "pg_dump not found"
```
Solution:
1. Verify PostgreSQL is installed
2. Add PostgreSQL bin directory to PATH
3. On Linux: export PATH=$PATH:/usr/lib/postgresql/14/bin
4. On macOS: brew install postgresql
5. On Windows: Add PostgreSQL bin to system PATH
```

#### Issue: Backup fails with "connection refused"
```
Solution:
1. Verify database is running
2. Check DATABASE_URL is correct
3. Verify database credentials
4. Check network connectivity
5. Review database logs for errors
```

#### Issue: Backup file is corrupted
```
Solution:
1. Check disk space during backup
2. Verify file permissions
3. Test restore to verify integrity
4. Check system logs for I/O errors
5. Consider hardware failure
```

#### Issue: Restore fails with "permission denied"
```
Solution:
1. Verify backup file is readable
2. Check database user permissions
3. Verify database exists
4. Check disk space for restore
5. Review database logs
```

### 11.2 Debug Logging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# View detailed backup logs
tail -f logs/backup.log

# Check scheduler status
python scripts/backup.py status
```

---

## 12. API Endpoints

### 12.1 Backup Status Endpoint

```
GET /api/backup/status

Response:
{
  "last_backup_time": "2025-02-10T02:00:15",
  "last_backup_status": true,
  "total_backups": 5,
  "total_size_mb": 225.45,
  "oldest_backup": "2025-02-06T02:00:12",
  "newest_backup": "2025-02-10T02:00:15",
  "backup_directory": "backups/",
  "retention_days": 30,
  "compression_enabled": true,
  "scheduled_backups_enabled": true,
  "recent_backups": [...]
}
```

### 12.2 Manual Backup Endpoint

```
POST /api/backup/create

Response:
{
  "success": true,
  "message": "Backup completed successfully: backups/backup_gra_db_20250210_120000.sql.gz"
}
```

### 12.3 Retention Policy Endpoint

```
GET /api/backup/policy

Response:
{
  "backup_retention_days": 30,
  "audit_log_retention_years": 7,
  "submission_retention_years": 7,
  "archive_after_days": 365,
  "archival_enabled": true,
  "archive_directory": "archives/",
  "compliance_notes": {...}
}
```

---

## 13. Configuration Examples

### 13.1 Development Environment

```bash
# .env.development
BACKUP_DIR=backups
ENABLE_SCHEDULED_BACKUPS=False
BACKUP_RETENTION_DAYS=7
COMPRESS_BACKUPS=True
VERIFY_BACKUP_INTEGRITY=True
ENABLE_ARCHIVAL=False
```

### 13.2 Production Environment

```bash
# .env.production
BACKUP_DIR=/var/backups/gra-db
ENABLE_SCHEDULED_BACKUPS=True
BACKUP_SCHEDULE_HOUR=2
BACKUP_SCHEDULE_MINUTE=0
BACKUP_RETENTION_DAYS=30
COMPRESS_BACKUPS=True
VERIFY_BACKUP_INTEGRITY=True
ENABLE_BACKUP_NOTIFICATIONS=True
BACKUP_NOTIFICATION_EMAIL=ops@example.com
ENABLE_ARCHIVAL=True
ARCHIVE_DIR=/var/archives/gra-db
ARCHIVE_AFTER_DAYS=365
```

### 13.3 Disaster Recovery Environment

```bash
# .env.disaster-recovery
BACKUP_DIR=/mnt/backup-storage/gra-db
ENABLE_SCHEDULED_BACKUPS=True
BACKUP_SCHEDULE_HOUR=1
BACKUP_SCHEDULE_MINUTE=0
BACKUP_RETENTION_DAYS=90
COMPRESS_BACKUPS=True
VERIFY_BACKUP_INTEGRITY=True
ENABLE_REMOTE_BACKUP=True
REMOTE_BACKUP_URL=https://backup-service.example.com
ENABLE_ARCHIVAL=True
ARCHIVE_DIR=/mnt/archive-storage/gra-db
ARCHIVE_AFTER_DAYS=180
```

---

## 14. References

### 14.1 Related Documentation
- Database Schema: `alembic/versions/001_initial_schema.py`
- Configuration: `app/config/backup_config.py`
- Service Implementation: `app/services/backup_service.py`
- CLI Tool: `scripts/backup.py`

### 14.2 External References
- PostgreSQL pg_dump: https://www.postgresql.org/docs/current/app-pgdump.html
- PostgreSQL psql: https://www.postgresql.org/docs/current/app-psql.html
- APScheduler: https://apscheduler.readthedocs.io/
- GRA Compliance: [GRA Documentation]

---

## 15. Appendix

### 15.1 Backup File Naming Convention

```
backup_<database_name>_<YYYYMMDD>_<HHMMSS>.sql[.gz]

Examples:
- backup_gra_db_20250210_020000.sql.gz
- backup_gra_db_20250209_020000.sql.gz
- backup_gra_db_20250208_020000.sql.gz
```

### 15.2 Directory Structure

```
project-root/
├── backups/                          # Active backups (30-day retention)
│   ├── backup_gra_db_20250210_020000.sql.gz
│   ├── backup_gra_db_20250209_020000.sql.gz
│   └── ...
├── archives/                         # Archived backups (7-year retention)
│   ├── backup_gra_db_20240210_020000.sql.gz
│   └── ...
├── app/
│   ├── services/
│   │   ├── backup_service.py
│   │   └── backup_scheduler.py
│   ├── utils/
│   │   └── backup.py
│   └── config/
│       └── backup_config.py
└── scripts/
    └── backup.py
```

### 15.3 Environment Variables Reference

```bash
# Backup Directory
BACKUP_DIR                          # Path to backup directory
ARCHIVE_DIR                         # Path to archive directory

# Scheduling
ENABLE_SCHEDULED_BACKUPS            # Enable/disable automated backups
BACKUP_SCHEDULE_HOUR                # Hour for daily backup (0-23)
BACKUP_SCHEDULE_MINUTE              # Minute for daily backup (0-59)

# Retention
BACKUP_RETENTION_DAYS               # Days to retain backups
AUDIT_LOG_RETENTION_YEARS           # Years to retain audit logs
SUBMISSION_RETENTION_YEARS          # Years to retain submissions
ARCHIVE_AFTER_DAYS                  # Days before archiving backups

# Features
COMPRESS_BACKUPS                    # Enable/disable compression
VERIFY_BACKUP_INTEGRITY             # Enable/disable verification
ENABLE_ARCHIVAL                     # Enable/disable archival
ENABLE_BACKUP_NOTIFICATIONS         # Enable/disable notifications
BACKUP_NOTIFICATION_EMAIL           # Email for notifications
ENABLE_REMOTE_BACKUP                # Enable/disable remote backup
REMOTE_BACKUP_URL                   # Remote backup service URL
REMOTE_BACKUP_API_KEY               # Remote backup API key
```

---

**Document Version**: 1.0  
**Last Updated**: February 10, 2025  
**Status**: Complete
