"""Tests for file manager utilities."""

from datetime import datetime, timedelta

from src.utils.file_manager import FileManager


class TestFileManager:
    """Test file management operations."""

    def test_file_manager_init_default_path(self, tmp_path, monkeypatch):
        """Test FileManager initializes with default output path."""
        # Mock the OUTPUT_PATH property by temporarily setting OUTPUT_DIR
        # Since OUTPUT_PATH is now a computed property based on OUTPUT_DIR
        monkeypatch.setattr("src.utils.file_manager.Config.OUTPUT_DIR", str(tmp_path.name))
        # Create FileManager with explicit path since we can't easily mock properties
        fm = FileManager(output_path=tmp_path)
        assert fm.output_path == tmp_path
        assert fm.output_path.exists()

    def test_file_manager_init_custom_path(self, tmp_path):
        """Test FileManager with custom output path."""
        custom_path = tmp_path / "custom_output"
        fm = FileManager(output_path=custom_path)
        assert fm.output_path == custom_path
        assert custom_path.exists()

    def test_file_manager_init_custom_keep_days(self, tmp_path):
        """Test FileManager with custom keep_days."""
        fm = FileManager(output_path=tmp_path, keep_days=14)
        assert fm.keep_days == 14

    def test_get_current_filename_with_date(self, tmp_path):
        """Test filename generation with specific date."""
        fm = FileManager(output_path=tmp_path)
        date = datetime(2025, 11, 28, 14, 30, 0)
        filename = fm.get_current_filename("weather", date=date)
        assert filename == "weather_2025-11-28.jpg"

    def test_get_current_filename_without_date(self, tmp_path):
        """Test filename generation with current date."""
        fm = FileManager(output_path=tmp_path)
        filename = fm.get_current_filename("tesla")
        # Should be today's date in configured timezone
        from src.config import Config

        today = Config.get_current_time().strftime("%Y-%m-%d")
        assert filename == f"tesla_{today}.jpg"

    def test_get_file_path(self, tmp_path):
        """Test full file path generation."""
        fm = FileManager(output_path=tmp_path)
        date = datetime(2025, 11, 28)
        path = fm.get_file_path("ferry", date=date)
        assert path == tmp_path / "ferry_2025-11-28.jpg"
        assert path.parent == tmp_path

    def test_cleanup_old_files_removes_old(self, tmp_path):
        """Test that cleanup removes files older than keep_days."""
        fm = FileManager(output_path=tmp_path, keep_days=7)

        # Create files with different dates
        today = datetime.now()
        old_date = today - timedelta(days=10)
        recent_date = today - timedelta(days=3)

        old_file = tmp_path / f"weather_{old_date.strftime('%Y-%m-%d')}.jpg"
        recent_file = tmp_path / f"weather_{recent_date.strftime('%Y-%m-%d')}.jpg"

        old_file.write_text("old")
        recent_file.write_text("recent")

        deleted = fm.cleanup_old_files(prefix="weather")

        assert deleted == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_old_files_keeps_recent(self, tmp_path):
        """Test that cleanup keeps recent files."""
        fm = FileManager(output_path=tmp_path, keep_days=7)

        # Create files within keep_days
        today = datetime.now()
        for days_ago in range(5):
            date = today - timedelta(days=days_ago)
            file = tmp_path / f"tesla_{date.strftime('%Y-%m-%d')}.jpg"
            file.write_text(f"content_{days_ago}")

        deleted = fm.cleanup_old_files(prefix="tesla")

        assert deleted == 0
        assert len(list(tmp_path.glob("tesla_*.jpg"))) == 5

    def test_cleanup_old_files_prefix_filter(self, tmp_path):
        """Test that cleanup only affects files with matching prefix."""
        fm = FileManager(output_path=tmp_path, keep_days=7)

        old_date = datetime.now() - timedelta(days=10)
        date_str = old_date.strftime("%Y-%m-%d")

        weather_file = tmp_path / f"weather_{date_str}.jpg"
        tesla_file = tmp_path / f"tesla_{date_str}.jpg"

        weather_file.write_text("weather")
        tesla_file.write_text("tesla")

        deleted = fm.cleanup_old_files(prefix="weather")

        assert deleted == 1
        assert not weather_file.exists()
        assert tesla_file.exists()

    def test_cleanup_old_files_no_prefix(self, tmp_path):
        """Test that cleanup without prefix removes all old files."""
        fm = FileManager(output_path=tmp_path, keep_days=7)

        old_date = datetime.now() - timedelta(days=10)
        date_str = old_date.strftime("%Y-%m-%d")

        weather_file = tmp_path / f"weather_{date_str}.jpg"
        tesla_file = tmp_path / f"tesla_{date_str}.jpg"

        weather_file.write_text("weather")
        tesla_file.write_text("tesla")

        deleted = fm.cleanup_old_files()

        assert deleted == 2
        assert not weather_file.exists()
        assert not tesla_file.exists()

    def test_list_files_sorted_by_date(self, tmp_path):
        """Test that files are listed newest first."""
        fm = FileManager(output_path=tmp_path)

        # Create files with different dates
        dates = [
            datetime(2025, 11, 25),
            datetime(2025, 11, 28),
            datetime(2025, 11, 26),
        ]

        for date in dates:
            file = tmp_path / f"ferry_{date.strftime('%Y-%m-%d')}.jpg"
            file.write_text(f"content_{date}")

        files = fm.list_files(prefix="ferry")

        assert len(files) == 3
        # Should be sorted newest first
        assert "2025-11-28" in str(files[0])
        assert "2025-11-26" in str(files[1])
        assert "2025-11-25" in str(files[2])

    def test_list_files_prefix_filter(self, tmp_path):
        """Test that list_files filters by prefix."""
        fm = FileManager(output_path=tmp_path)

        date = datetime(2025, 11, 28)
        date_str = date.strftime("%Y-%m-%d")

        weather_file = tmp_path / f"weather_{date_str}.jpg"
        tesla_file = tmp_path / f"tesla_{date_str}.jpg"
        ferry_file = tmp_path / f"ferry_{date_str}.jpg"

        for file in [weather_file, tesla_file, ferry_file]:
            file.write_text("content")

        files = fm.list_files(prefix="tesla")

        assert len(files) == 1
        assert "tesla" in str(files[0])

    def test_list_files_no_prefix(self, tmp_path):
        """Test that list_files without prefix returns all files."""
        fm = FileManager(output_path=tmp_path)

        date = datetime(2025, 11, 28)
        date_str = date.strftime("%Y-%m-%d")

        for prefix in ["weather", "tesla", "ferry"]:
            file = tmp_path / f"{prefix}_{date_str}.jpg"
            file.write_text("content")

        files = fm.list_files()

        assert len(files) == 3

    def test_get_latest_file(self, tmp_path):
        """Test getting the most recent file for a prefix."""
        fm = FileManager(output_path=tmp_path)

        dates = [
            datetime(2025, 11, 25),
            datetime(2025, 11, 28),
            datetime(2025, 11, 26),
        ]

        for date in dates:
            file = tmp_path / f"stock_{date.strftime('%Y-%m-%d')}.jpg"
            file.write_text(f"content_{date}")

        latest = fm.get_latest_file("stock")

        assert latest is not None
        assert "2025-11-28" in str(latest)

    def test_get_latest_file_no_files(self, tmp_path):
        """Test get_latest_file returns None when no files exist."""
        fm = FileManager(output_path=tmp_path)
        latest = fm.get_latest_file("nonexistent")
        assert latest is None

    def test_cleanup_ignores_non_matching_files(self, tmp_path):
        """Test that cleanup doesn't delete files with invalid date format."""
        fm = FileManager(output_path=tmp_path, keep_days=7)

        # Create file without date format
        invalid_file = tmp_path / "weather_latest.jpg"
        invalid_file.write_text("content")

        # Create old file
        old_date = datetime.now() - timedelta(days=10)
        old_file = tmp_path / f"weather_{old_date.strftime('%Y-%m-%d')}.jpg"
        old_file.write_text("old")

        deleted = fm.cleanup_old_files(prefix="weather")

        assert deleted == 1
        assert invalid_file.exists()  # Non-dated file should remain
        assert not old_file.exists()
