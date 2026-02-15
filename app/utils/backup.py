"""Database backup and restore utilities"""
import os
import subprocess
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseBackupManager:
    """Manages database backups and restoration"""
    
    def __init__(self, backup_dir: str = "backups"):
        """
        Initialize backup manager
        
        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.db_url = settings.DATABASE_URL
        self._parse_db_connection()
    
    def _parse_db_connection(self) -> None:
        """Parse PostgreSQL connection string"""
        # Format: postgresql://user:password@host:port/database
        try:
            parts = self.db_url.replace("postgresql://", "").split("@")
            credentials = parts[0].split(":")
            host_db = parts[1].split("/")
            
            self.db_user = credentials[0]
            self.db_password = credentials[1] if len(credentials) > 1 else ""
            self.db_host = host_db[0].split(":")[0]
            self.db_port = host_db[0].split(":")[1] if ":" in host_db[0] else "5432"
            self.db_name = host_db[1]
        except Exception as e:
            logger.error(f"Failed to parse database connection string: {e}")
            raise
    
    def create_backup(self, compress: bool = True) -> Tuple[bool, str]:
        """
        Create a database backup
        
        Args:
            compress: Whether to compress the backup file
            
        Returns:
            Tuple of (success: bool, backup_file_path: str)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{self.db_name}_{timestamp}.sql"
            
            # Set environment variable for password
            env = os.environ.copy()
            if self.db_password:
                env["PGPASSWORD"] = self.db_password
            
            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", self.db_port,
                "-U", self.db_user,
                "-d", self.db_name,
                "-F", "plain",
                "-v"
            ]
            
            logger.info(f"Starting database backup to {backup_file}")
            
            with open(backup_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=3600  # 1 hour timeout
                )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr.decode()}")
                backup_file.unlink()
                return False, ""
            
            # Compress if requested
            if compress:
                compressed_file = Path(str(backup_file) + ".gz")
                with open(backup_file, "rb") as f_in:
                    with gzip.open(compressed_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                backup_file.unlink()
                backup_file = compressed_file
                logger.info(f"Backup compressed to {backup_file}")
            
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Database backup completed successfully: {backup_file} ({file_size:.2f} MB)")
            
            return True, str(backup_file)
        
        except subprocess.TimeoutExpired:
            logger.error("Database backup timed out after 1 hour")
            return False, ""
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False, ""
    
    def restore_backup(self, backup_file: str) -> Tuple[bool, str]:
        """
        Restore database from backup
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_file}"
            
            # Handle compressed files
            if backup_file.endswith(".gz"):
                temp_file = backup_path.parent / f"temp_{backup_path.stem}"
                logger.info(f"Decompressing backup file...")
                with gzip.open(backup_path, "rb") as f_in:
                    with open(temp_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = temp_file
            else:
                restore_file = backup_path
            
            # Set environment variable for password
            env = os.environ.copy()
            if self.db_password:
                env["PGPASSWORD"] = self.db_password
            
            # Run psql to restore
            cmd = [
                "psql",
                "-h", self.db_host,
                "-p", self.db_port,
                "-U", self.db_user,
                "-d", self.db_name
            ]
            
            logger.info(f"Starting database restore from {backup_file}")
            
            with open(restore_file, "r") as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=3600  # 1 hour timeout
                )
            
            # Clean up temp file if it was created
            if backup_file.endswith(".gz"):
                restore_file.unlink()
            
            if result.returncode != 0:
                error_msg = result.stderr.decode()
                logger.error(f"psql restore failed: {error_msg}")
                return False, error_msg
            
            logger.info(f"Database restore completed successfully from {backup_file}")
            return True, "Database restored successfully"
        
        except subprocess.TimeoutExpired:
            logger.error("Database restore timed out after 1 hour")
            return False, "Restore operation timed out"
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False, str(e)
    
    def list_backups(self) -> list:
        """
        List all available backups
        
        Returns:
            List of backup file information
        """
        backups = []
        try:
            for backup_file in sorted(self.backup_dir.glob("backup_*.sql*"), reverse=True):
                file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                modified_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_mb": round(file_size, 2),
                    "modified": modified_time.isoformat(),
                    "compressed": backup_file.suffix == ".gz"
                })
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self, retention_days: int = 30) -> Tuple[int, int]:
        """
        Delete backups older than retention period
        
        Args:
            retention_days: Number of days to retain backups
            
        Returns:
            Tuple of (deleted_count, total_size_freed_mb)
        """
        try:
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
            deleted_count = 0
            total_size_freed = 0
            
            for backup_file in self.backup_dir.glob("backup_*.sql*"):
                if backup_file.stat().st_mtime < cutoff_time:
                    file_size = backup_file.stat().st_size / (1024 * 1024)
                    backup_file.unlink()
                    deleted_count += 1
                    total_size_freed += file_size
                    logger.info(f"Deleted old backup: {backup_file.name}")
            
            logger.info(f"Cleanup completed: {deleted_count} backups deleted, {total_size_freed:.2f} MB freed")
            return deleted_count, round(total_size_freed, 2)
        
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return 0, 0
    
    def get_backup_stats(self) -> Dict:
        """
        Get backup statistics
        
        Returns:
            Dictionary with backup statistics
        """
        try:
            backups = self.list_backups()
            total_size = sum(b["size_mb"] for b in backups)
            
            return {
                "total_backups": len(backups),
                "total_size_mb": round(total_size, 2),
                "oldest_backup": backups[-1]["modified"] if backups else None,
                "newest_backup": backups[0]["modified"] if backups else None,
                "backup_directory": str(self.backup_dir)
            }
        except Exception as e:
            logger.error(f"Failed to get backup stats: {e}")
            return {}
