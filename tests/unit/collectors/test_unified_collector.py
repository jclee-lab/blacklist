"""
Unit tests for unified collector base classes
Tests unified_collector.py with mocked dependencies
Target: 55% → 80% coverage (33 statements)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from typing import Any, List


@pytest.mark.unit
class TestCollectionConfig:
    """Test CollectionConfig class"""

    def test_initialization_defaults(self):
        """Test CollectionConfig initializes with correct defaults"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        assert config.enabled is True
        assert config.days_interval == 7
        assert config.max_retries == 3
        assert config.timeout == 30
        assert config.batch_size == 100

    def test_get_date_range_with_default_days(self):
        """Test get_date_range uses days_interval when days=None"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()
        config.days_interval = 10  # Set custom interval

        start_date, end_date = config.get_date_range()  # days=None

        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Check date range is approximately 10 days
        delta = (end - start).days
        assert delta == 10

    def test_get_date_range_with_custom_days(self):
        """Test get_date_range with explicitly provided days"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        start_date, end_date = config.get_date_range(days=5)

        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Check date range is approximately 5 days
        delta = (end - start).days
        assert delta == 5

    def test_get_date_range_format(self):
        """Test get_date_range returns YYYY-MM-DD format"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        start_date, end_date = config.get_date_range()

        # Verify format by parsing
        assert len(start_date) == 10  # YYYY-MM-DD
        assert len(end_date) == 10
        assert start_date.count("-") == 2
        assert end_date.count("-") == 2

        # Should be valid dates
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

    def test_get_date_range_with_one_day(self):
        """Test get_date_range with days=1"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        start_date, end_date = config.get_date_range(days=1)

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        delta = (end - start).days
        assert delta == 1

    def test_get_date_range_with_large_days(self):
        """Test get_date_range with large day count"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        start_date, end_date = config.get_date_range(days=365)

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        delta = (end - start).days
        assert delta == 365

    def test_config_attribute_modification(self):
        """Test CollectionConfig attributes can be modified"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        # Modify attributes
        config.enabled = False
        config.days_interval = 14
        config.max_retries = 5
        config.timeout = 60
        config.batch_size = 200

        assert config.enabled is False
        assert config.days_interval == 14
        assert config.max_retries == 5
        assert config.timeout == 60
        assert config.batch_size == 200


@pytest.mark.unit
class TestBaseCollector:
    """Test BaseCollector abstract class"""

    def test_cannot_instantiate_directly(self):
        """Test BaseCollector cannot be instantiated (abstract class)"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        config = CollectionConfig()

        # Should raise TypeError for abstract class
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseCollector("test", config)

    def test_concrete_implementation_initialization(self):
        """Test concrete implementation of BaseCollector"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        # Create concrete implementation
        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        collector = TestCollector("test_source", config)

        assert collector.source_name == "test_source"
        assert collector.config == config
        assert collector.logger is not None
        assert collector.source_type == "test"

    def test_validate_config_enabled(self):
        """Test validate_config returns True when enabled"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        config.enabled = True

        collector = TestCollector("test", config)

        result = collector.validate_config()
        assert result is True

    def test_validate_config_disabled(self):
        """Test validate_config returns False when disabled"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        config.enabled = False

        collector = TestCollector("test", config)

        result = collector.validate_config()
        assert result is False

    def test_get_status_returns_dict(self):
        """Test get_status returns correct dictionary structure"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        collector = TestCollector("my_source", config)

        status = collector.get_status()

        assert isinstance(status, dict)
        assert status["source"] == "my_source"
        assert status["enabled"] is True
        assert status["last_run"] is None
        assert status["status"] == "ready"

    def test_get_status_with_disabled_config(self):
        """Test get_status reflects disabled state"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        config.enabled = False

        collector = TestCollector("test", config)

        status = collector.get_status()

        assert status["enabled"] is False

    def test_logger_naming_convention(self):
        """Test logger uses correct naming convention"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        collector = TestCollector("my_collector", config)

        # Logger name should be core.collectors.unified_collector.my_collector
        assert "my_collector" in collector.logger.name

    @pytest.mark.asyncio
    async def test_collect_data_abstract_method(self):
        """Test _collect_data is implemented in concrete class"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return [{"test": "data"}]

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        collector = TestCollector("test", config)

        result = await collector._collect_data()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == {"test": "data"}

    def test_source_type_property(self):
        """Test source_type property returns correct type"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "custom_type"

        config = CollectionConfig()
        collector = TestCollector("test", config)

        assert collector.source_type == "custom_type"


@pytest.mark.unit
class TestCollectionConfigEdgeCases:
    """Test edge cases for CollectionConfig"""

    def test_get_date_range_with_zero_days(self):
        """Test get_date_range with days=0"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        start_date, end_date = config.get_date_range(days=0)

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Should return same date (delta=0)
        delta = (end - start).days
        assert delta == 0

    def test_multiple_get_date_range_calls_consistent(self):
        """Test multiple calls to get_date_range return consistent results"""
        from core.collectors.unified_collector import CollectionConfig

        config = CollectionConfig()

        # Call multiple times
        result1 = config.get_date_range(days=5)
        result2 = config.get_date_range(days=5)

        # Should be very close (might differ by 1 day if called at midnight)
        start1, end1 = result1
        start2, end2 = result2

        # Both should have 5 day interval
        delta1 = (
            datetime.strptime(end1, "%Y-%m-%d")
            - datetime.strptime(start1, "%Y-%m-%d")
        ).days
        delta2 = (
            datetime.strptime(end2, "%Y-%m-%d")
            - datetime.strptime(start2, "%Y-%m-%d")
        ).days

        assert delta1 == 5
        assert delta2 == 5


@pytest.mark.unit
class TestBaseCollectorEdgeCases:
    """Test edge cases for BaseCollector"""

    def test_multiple_collectors_independent(self):
        """Test multiple collector instances are independent"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config1 = CollectionConfig()
        config2 = CollectionConfig()
        config2.enabled = False

        collector1 = TestCollector("source1", config1)
        collector2 = TestCollector("source2", config2)

        # Collectors should be independent
        assert collector1.source_name == "source1"
        assert collector2.source_name == "source2"
        assert collector1.config.enabled is True
        assert collector2.config.enabled is False

    def test_collector_with_custom_config_values(self):
        """Test collector works with customized config"""
        from core.collectors.unified_collector import (
            BaseCollector,
            CollectionConfig,
        )

        class TestCollector(BaseCollector):
            async def _collect_data(self) -> List[Any]:
                return []

            @property
            def source_type(self) -> str:
                return "test"

        config = CollectionConfig()
        config.max_retries = 10
        config.timeout = 120
        config.batch_size = 500

        collector = TestCollector("test", config)

        assert collector.config.max_retries == 10
        assert collector.config.timeout == 120
        assert collector.config.batch_size == 500
