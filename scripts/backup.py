#!/usr/bin/env python
"""Database backup and restore CLI script"""
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.backup_service import BackupService
from app.config.backup_config import backup_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Database backup and restore utility"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a database backup")
    backup_parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Do not compress the backup"
    )
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from a backup")
    restore_parser.add_argument(
        "backup_file",
        help="Path to backup file"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument(
        "--days",
        type=int,
        default=backup_config.BACKUP_RETENTION_DAYS,
        help=f"Retention days (default: {backup_config.BACKUP_RETENTION_DAYS})"
    )
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show backup status")
    
    # Policy command
    policy_parser = subparsers.add_parser("policy", help="Show retention policy")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    backup_service = BackupService()
    
    try:
        if args.command == "backup":
            logger.info("Creating database backup...")
            success, message = backup_service.perform_backup()
            print(message)
            return 0 if success else 1
        
        elif args.command == "restore":
            logger.warning(f"Restoring database from {args.backup_file}...")
            confirm = input("Are you sure? This will overwrite the current database. (yes/no): ")
            if confirm.lower() != "yes":
                print("Restore cancelled")
                return 1
            
            success, message = backup_service.restore_from_backup(args.backup_file)
            print(message)
            return 0 if success else 1
        
        elif args.command == "list":
            backups = backup_service.backup_manager.list_backups()
            if not backups:
                print("No backups found")
                return 0
            
            print(f"\nFound {len(backups)} backup(s):\n")
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['filename']}")
                print(f"   Size: {backup['size_mb']} MB")
                print(f"   Modified: {backup['modified']}")
                print(f"   Compressed: {backup['compressed']}")
                print()
            return 0
        
        elif args.command == "cleanup":
            logger.info(f"Cleaning up backups older than {args.days} days...")
            deleted_count, freed_size = backup_service.cleanup_old_backups()
            print(f"Deleted {deleted_count} backup(s), freed {freed_size} MB")
            return 0
        
        elif args.command == "status":
            status = backup_service.get_backup_status()
            print("\nBackup Status:")
            print(f"  Last Backup: {status.get('last_backup_time', 'Never')}")
            print(f"  Last Status: {status.get('last_backup_status', 'Unknown')}")
            print(f"  Total Backups: {status.get('total_backups', 0)}")
            print(f"  Total Size: {status.get('total_size_mb', 0)} MB")
            print(f"  Oldest: {status.get('oldest_backup', 'N/A')}")
            print(f"  Newest: {status.get('newest_backup', 'N/A')}")
            print(f"  Directory: {status.get('backup_directory', 'N/A')}")
            print()
            return 0
        
        elif args.command == "policy":
            policy = backup_service.get_retention_policy()
            print("\nData Retention Policy:")
            print(f"  Backup Retention: {policy['backup_retention_days']} days")
            print(f"  Audit Log Retention: {policy['audit_log_retention_years']} years")
            print(f"  Submission Retention: {policy['submission_retention_years']} years")
            print(f"  Archive After: {policy['archive_after_days']} days")
            print(f"  Archival Enabled: {policy['archival_enabled']}")
            print("\nCompliance Notes:")
            for key, value in policy['compliance_notes'].items():
                print(f"  {key}: {value}")
            print()
            return 0
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
