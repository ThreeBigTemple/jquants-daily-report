"""Cache management for J-Quants data using SQLite.

This module provides functionality for caching API data locally using SQLite database.
Includes cache expiration management and automatic migration from legacy parquet files.
"""

import io
import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Database schema version for future migrations
SCHEMA_VERSION = 1


class CacheManager:
    """Manages local cache for J-Quants API data using SQLite.

    Caches are stored in a SQLite database for efficient storage and retrieval.
    Each cache entry has an expiration time for automatic invalidation.
    """

    DB_FILENAME = "cache.db"

    def __init__(self, cache_dir: Path, default_ttl_hours: int = 24):
        """Initialize CacheManager.

        Args:
            cache_dir: Directory path for storing the cache database.
            default_ttl_hours: Default time-to-live for cache entries in hours.
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl_hours = default_ttl_hours
        self._db_path = self.cache_dir / self.DB_FILENAME
        self._ensure_cache_dir()
        self._init_database()
        self._migrate_from_files()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cache directory ensured: {self.cache_dir}")

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with proper error handling.

        Yields:
            SQLite connection object.
        """
        conn = sqlite3.connect(str(self._db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create cache entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT NOT NULL UNIQUE,
                    data BLOB NOT NULL,
                    row_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    compression TEXT DEFAULT 'pickle'
                )
            """)

            # Create indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_key
                ON cache_entries(cache_key)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON cache_entries(expires_at)
            """)

            # Create metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Set schema version
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache_metadata (key, value)
                VALUES ('schema_version', ?)
            """,
                (str(SCHEMA_VERSION),),
            )

            logger.debug("Database schema initialized")

    def _serialize_dataframe(self, df: pd.DataFrame) -> bytes:
        """Serialize DataFrame to bytes.

        Args:
            df: DataFrame to serialize.

        Returns:
            Serialized bytes.
        """
        buffer = io.BytesIO()
        df.to_pickle(buffer)
        return buffer.getvalue()

    def _deserialize_dataframe(self, data: bytes) -> pd.DataFrame:
        """Deserialize bytes to DataFrame.

        Args:
            data: Serialized bytes.

        Returns:
            Deserialized DataFrame.
        """
        buffer = io.BytesIO(data)
        return pd.read_pickle(buffer)

    def _sanitize_key(self, key: str) -> str:
        """Sanitize cache key for consistent storage.

        Args:
            key: Original cache key.

        Returns:
            Sanitized cache key.
        """
        # Keep the key as-is for SQLite (no need for filename sanitization)
        return key

    def get(self, key: str) -> pd.DataFrame | None:
        """Retrieve data from cache.

        Args:
            key: Cache key identifier.

        Returns:
            Cached DataFrame if valid, None if expired or not found.
        """
        sanitized_key = self._sanitize_key(key)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT data, expires_at, row_count
                FROM cache_entries
                WHERE cache_key = ?
            """,
                (sanitized_key,),
            )

            row = cursor.fetchone()

            if row is None:
                logger.debug(f"Cache miss: {key}")
                return None

            # Check expiration
            expires_at = datetime.fromisoformat(row["expires_at"])
            if datetime.now() >= expires_at:
                logger.debug(f"Cache expired: {key}")
                self._remove_entry(cursor, sanitized_key)
                conn.commit()
                return None

            try:
                df = self._deserialize_dataframe(row["data"])
                logger.info(f"Cache hit: {key} ({row['row_count']} rows)")
                return df
            except Exception as e:
                logger.error(f"Failed to deserialize cache {key}: {e}")
                self._remove_entry(cursor, sanitized_key)
                conn.commit()
                return None

    def set(self, key: str, data: pd.DataFrame, ttl_hours: int | None = None) -> None:
        """Store data in cache.

        Args:
            key: Cache key identifier.
            data: DataFrame to cache.
            ttl_hours: Time-to-live in hours. Uses default if not specified.
        """
        if data.empty:
            logger.warning(f"Attempted to cache empty DataFrame for key: {key}")
            return

        sanitized_key = self._sanitize_key(key)
        ttl = ttl_hours if ttl_hours is not None else self.default_ttl_hours

        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=ttl)

        try:
            serialized_data = self._serialize_dataframe(data)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO cache_entries
                    (cache_key, data, row_count, created_at, expires_at, compression)
                    VALUES (?, ?, ?, ?, ?, 'pickle')
                """,
                    (
                        sanitized_key,
                        serialized_data,
                        len(data),
                        created_at.isoformat(),
                        expires_at.isoformat(),
                    ),
                )

            logger.info(
                f"Cached {len(data)} rows for key: {key} "
                f"(expires: {expires_at.strftime('%Y-%m-%d %H:%M')})"
            )
        except Exception as e:
            logger.error(f"Failed to write cache {key}: {e}")

    def _remove_entry(self, cursor: sqlite3.Cursor, key: str) -> None:
        """Remove a cache entry (internal method, no commit).

        Args:
            cursor: Database cursor.
            key: Cache key to remove.
        """
        cursor.execute("DELETE FROM cache_entries WHERE cache_key = ?", (key,))
        logger.debug(f"Removed cache entry: {key}")

    def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry.

        Args:
            key: Cache key identifier.
        """
        logger.info(f"Invalidating cache: {key}")
        sanitized_key = self._sanitize_key(key)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            self._remove_entry(cursor, sanitized_key)

    def clear_all(self) -> None:
        """Clear all cache entries."""
        logger.info("Clearing all cache entries")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache_entries")
            logger.info("All cache entries cleared")

    def get_cache_size(self) -> int:
        """Get total size of cache database in bytes.

        Returns:
            Total cache size in bytes.
        """
        try:
            return self._db_path.stat().st_size
        except Exception as e:
            logger.error(f"Failed to get cache size: {e}")
            return 0

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries.

        Returns:
            Number of entries removed.
        """
        logger.info("Cleaning up expired cache entries")

        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Count expired entries
            cursor.execute(
                """
                SELECT COUNT(*) FROM cache_entries WHERE expires_at < ?
            """,
                (now,),
            )
            count = cursor.fetchone()[0]

            # Delete expired entries
            cursor.execute(
                """
                DELETE FROM cache_entries WHERE expires_at < ?
            """,
                (now,),
            )

            logger.info(f"Removed {count} expired cache entries")
            return count

    def _migrate_from_files(self) -> None:
        """Migrate existing parquet/meta files to SQLite (one-time)."""
        # Check if migration already completed
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT value FROM cache_metadata WHERE key = 'migration_completed'
            """
            )
            row = cursor.fetchone()
            if row and row["value"] == "true":
                return  # Migration already done

        # Find parquet files to migrate
        parquet_files = list(self.cache_dir.glob("*.parquet"))
        if not parquet_files:
            self._mark_migration_completed()
            return

        logger.info(f"Migrating {len(parquet_files)} cache files to SQLite...")
        migrated_count = 0

        for parquet_path in parquet_files:
            key = parquet_path.stem  # Filename without extension
            meta_path = self.cache_dir / f"{key}.meta"

            try:
                # Read parquet data
                df = pd.read_parquet(parquet_path)

                # Read expiration from meta file
                if meta_path.exists():
                    with open(meta_path) as f:
                        expiry_str = f.read().strip()
                        expires_at = datetime.fromisoformat(expiry_str)
                else:
                    # Default to 24 hours from now if no meta
                    expires_at = datetime.now() + timedelta(hours=24)

                # Skip if already expired
                if datetime.now() >= expires_at:
                    logger.debug(f"Skipping expired file: {key}")
                    self._delete_old_files(parquet_path, meta_path)
                    continue

                # Calculate remaining TTL
                remaining_hours = (expires_at - datetime.now()).total_seconds() / 3600

                # Insert into database
                self.set(key, df, ttl_hours=remaining_hours)
                migrated_count += 1

                # Delete old files after successful migration
                self._delete_old_files(parquet_path, meta_path)

            except Exception as e:
                logger.warning(f"Failed to migrate {key}: {e}")
                continue

        logger.info(f"Migration completed: {migrated_count} files migrated")
        self._mark_migration_completed()

    def _delete_old_files(self, parquet_path: Path, meta_path: Path) -> None:
        """Delete old parquet and meta files.

        Args:
            parquet_path: Path to parquet file.
            meta_path: Path to meta file.
        """
        try:
            if parquet_path.exists():
                parquet_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete old files: {e}")

    def _mark_migration_completed(self) -> None:
        """Mark migration as completed in metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache_metadata (key, value)
                VALUES ('migration_completed', 'true')
            """
            )
