"""Tests for cache manager module."""

import sqlite3
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from jquants_report.data.cache import CacheManager


class TestCacheManager:
    """Test cases for CacheManager class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create CacheManager instance with temporary directory."""
        return CacheManager(temp_cache_dir, default_ttl_hours=24)

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "code": ["1301", "1302", "1303"],
                "price": [100, 200, 300],
                "volume": [1000, 2000, 3000],
            }
        )

    def test_cache_dir_creation(self, temp_cache_dir):
        """Test cache directory is created."""
        cache_manager = CacheManager(temp_cache_dir / "new_cache")
        assert cache_manager.cache_dir.exists()

    def test_set_and_get_cache(self, cache_manager, sample_dataframe):
        """Test setting and getting cache."""
        key = "test_data"
        cache_manager.set(key, sample_dataframe)

        retrieved = cache_manager.get(key)
        assert retrieved is not None
        assert len(retrieved) == len(sample_dataframe)
        assert list(retrieved.columns) == list(sample_dataframe.columns)

    def test_get_nonexistent_cache(self, cache_manager):
        """Test getting non-existent cache returns None."""
        result = cache_manager.get("nonexistent_key")
        assert result is None

    def test_cache_expiration(self, cache_manager, sample_dataframe):
        """Test cache expiration."""
        key = "expiring_data"
        # Set cache with very short TTL
        cache_manager.set(key, sample_dataframe, ttl_hours=0.0001)

        # Wait for expiration
        time.sleep(0.5)

        # Should return None after expiration
        result = cache_manager.get(key)
        assert result is None

    def test_cache_not_expired(self, cache_manager, sample_dataframe):
        """Test cache before expiration."""
        key = "fresh_data"
        cache_manager.set(key, sample_dataframe, ttl_hours=1)

        # Should retrieve valid data
        result = cache_manager.get(key)
        assert result is not None
        assert len(result) == len(sample_dataframe)

    def test_invalidate_cache(self, cache_manager, sample_dataframe):
        """Test cache invalidation."""
        key = "invalidate_test"
        cache_manager.set(key, sample_dataframe)

        # Verify cache exists
        assert cache_manager.get(key) is not None

        # Invalidate
        cache_manager.invalidate(key)

        # Should return None after invalidation
        assert cache_manager.get(key) is None

    def test_clear_all_cache(self, cache_manager, sample_dataframe):
        """Test clearing all cache entries."""
        cache_manager.set("key1", sample_dataframe)
        cache_manager.set("key2", sample_dataframe)
        cache_manager.set("key3", sample_dataframe)

        # Clear all
        cache_manager.clear_all()

        # All should be gone
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None

    def test_empty_dataframe_not_cached(self, cache_manager):
        """Test that empty DataFrames are not cached."""
        key = "empty_test"
        empty_df = pd.DataFrame()
        cache_manager.set(key, empty_df)

        # Should not be cached
        result = cache_manager.get(key)
        assert result is None

    def test_cache_size(self, cache_manager):
        """Test cache size calculation."""
        # SQLite database has initial size even when empty (schema, metadata)
        initial_size = cache_manager.get_cache_size()
        assert initial_size > 0

        # Add large enough data to increase database size
        large_df = pd.DataFrame({
            "code": [f"{i:04d}" for i in range(1000)],
            "price": list(range(1000)),
            "volume": list(range(1000)),
            "name": [f"Company {i}" for i in range(1000)],
        })
        cache_manager.set("large_data", large_df)

        new_size = cache_manager.get_cache_size()
        assert new_size >= initial_size  # Size should not decrease

    def test_cleanup_expired(self, cache_manager, sample_dataframe):
        """Test cleanup of expired entries."""
        # Set one with short TTL and one with long TTL
        cache_manager.set("short_ttl", sample_dataframe, ttl_hours=0.0001)
        cache_manager.set("long_ttl", sample_dataframe, ttl_hours=24)

        # Wait for short TTL to expire
        time.sleep(0.5)

        # Cleanup
        removed_count = cache_manager.cleanup_expired()

        # One should be removed
        assert removed_count >= 1

        # Long TTL should still exist
        assert cache_manager.get("long_ttl") is not None

    def test_special_characters_in_key(self, cache_manager, sample_dataframe):
        """Test handling of special characters in cache keys."""
        key = "data/2024-01-15:quotes"
        cache_manager.set(key, sample_dataframe)

        result = cache_manager.get(key)
        assert result is not None

    def test_cache_with_different_data_types(self, cache_manager):
        """Test caching DataFrames with different data types."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
                "date_col": pd.date_range("2024-01-01", periods=3),
            }
        )

        key = "mixed_types"
        cache_manager.set(key, df)

        result = cache_manager.get(key)
        assert result is not None
        assert list(result.columns) == list(df.columns)
        assert result["int_col"].dtype == df["int_col"].dtype
        assert result["str_col"].dtype == df["str_col"].dtype

    def test_multiple_cache_operations(self, cache_manager, sample_dataframe):
        """Test multiple cache operations in sequence."""
        key = "multi_op_test"

        # Set
        cache_manager.set(key, sample_dataframe)
        assert cache_manager.get(key) is not None

        # Update
        updated_df = sample_dataframe.copy()
        updated_df["new_column"] = [10, 20, 30]
        cache_manager.set(key, updated_df)

        result = cache_manager.get(key)
        assert "new_column" in result.columns

        # Invalidate
        cache_manager.invalidate(key)
        assert cache_manager.get(key) is None

    def test_sqlite_database_created(self, cache_manager):
        """Test SQLite database is created."""
        db_path = cache_manager.cache_dir / "cache.db"
        assert db_path.exists()

    def test_sqlite_schema_exists(self, cache_manager):
        """Test SQLite database has correct schema."""
        db_path = cache_manager.cache_dir / "cache.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        assert "cache_entries" in tables
        assert "cache_metadata" in tables

        conn.close()

    def test_migration_from_parquet(self, temp_cache_dir):
        """Test migration of existing parquet files."""
        # Create sample parquet and meta files before CacheManager init
        sample_df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        parquet_path = temp_cache_dir / "test_key.parquet"
        meta_path = temp_cache_dir / "test_key.meta"

        sample_df.to_parquet(parquet_path, index=False)
        expires_at = datetime.now() + timedelta(hours=24)
        with open(meta_path, "w") as f:
            f.write(expires_at.isoformat())

        # Initialize cache manager (triggers migration)
        cache_manager = CacheManager(temp_cache_dir)

        # Verify data is in SQLite
        result = cache_manager.get("test_key")
        assert result is not None
        assert len(result) == 3

        # Verify old files deleted
        assert not parquet_path.exists()
        assert not meta_path.exists()

    def test_migration_skips_expired(self, temp_cache_dir):
        """Test migration skips expired files."""
        sample_df = pd.DataFrame({"a": [1, 2, 3]})
        parquet_path = temp_cache_dir / "expired_key.parquet"
        meta_path = temp_cache_dir / "expired_key.meta"

        sample_df.to_parquet(parquet_path, index=False)
        # Set expiration in the past
        expires_at = datetime.now() - timedelta(hours=1)
        with open(meta_path, "w") as f:
            f.write(expires_at.isoformat())

        cache_manager = CacheManager(temp_cache_dir)

        # Should not exist in cache
        result = cache_manager.get("expired_key")
        assert result is None

        # Old files should still be deleted
        assert not parquet_path.exists()
        assert not meta_path.exists()

    def test_migration_runs_only_once(self, temp_cache_dir):
        """Test migration only runs once."""
        # Create first cache manager (triggers migration)
        _ = CacheManager(temp_cache_dir)

        # Create a parquet file after migration completed
        sample_df = pd.DataFrame({"a": [1, 2, 3]})
        parquet_path = temp_cache_dir / "new_file.parquet"
        meta_path = temp_cache_dir / "new_file.meta"

        sample_df.to_parquet(parquet_path, index=False)
        expires_at = datetime.now() + timedelta(hours=24)
        with open(meta_path, "w") as f:
            f.write(expires_at.isoformat())

        # Create second cache manager - should not migrate the new file
        cache_manager2 = CacheManager(temp_cache_dir)

        # New file should NOT be in database (migration already completed)
        result = cache_manager2.get("new_file")
        assert result is None

        # Parquet file should still exist
        assert parquet_path.exists()

    def test_concurrent_access(self, temp_cache_dir, sample_dataframe):
        """Test concurrent database access."""
        cache_manager = CacheManager(temp_cache_dir)
        errors = []

        def writer(thread_id: int) -> None:
            try:
                for i in range(5):
                    cache_manager.set(f"concurrent_key_{thread_id}_{i}", sample_dataframe)
            except Exception as e:
                errors.append(e)

        def reader(thread_id: int) -> None:
            try:
                for i in range(5):
                    cache_manager.get(f"concurrent_key_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]
        threads += [threading.Thread(target=reader, args=(i,)) for i in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_data_integrity(self, cache_manager, sample_dataframe):
        """Test data integrity after serialization/deserialization."""
        key = "integrity_test"
        cache_manager.set(key, sample_dataframe)

        result = cache_manager.get(key)
        assert result is not None

        # Check values match
        pd.testing.assert_frame_equal(result, sample_dataframe)
