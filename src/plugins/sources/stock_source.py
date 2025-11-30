"""
Stock quote data source plugin.
Wraps StockClient from existing codebase.
"""

import logging

from src.clients.stock import StockClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("stock")
class StockSource(BaseSource):
    """Stock quote data source plugin."""

    def validate_config(self) -> bool:
        """Validate stock config."""
        # Optional: Can specify symbol in config, otherwise uses Config
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch stock quote data."""
        logger.info(f"[{self.source_id}] Fetching stock data")

        try:
            client = StockClient()
            stock_data = client.get_quote()

            if not stock_data:
                logger.warning(f"[{self.source_id}] No stock data available")
                return None

            logger.info(
                f"[{self.source_id}] {stock_data.symbol} ${stock_data.price} "
                f"({stock_data.change_percent})"
            )

            # Convert to signage content
            return stock_data.to_signage()

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch stock data: {e}")
            return None
