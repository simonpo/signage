"""
Stock quote API client using Alpha Vantage.
"""

import logging
from typing import Optional

from src.clients.base import APIClient
from src.config import Config
from src.models.signage_data import StockData

logger = logging.getLogger(__name__)


class StockClient(APIClient):
    """Client for Alpha Vantage stock quote API."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        """Initialize with API key from config."""
        super().__init__()
        
        self.api_key = Config.STOCK_API_KEY
        self.symbol = Config.STOCK_SYMBOL
        
        if not self.api_key:
            logger.warning("STOCK_API_KEY not configured - stock quotes will be disabled")
        if not self.symbol:
            logger.warning("STOCK_SYMBOL not configured - stock quotes will be disabled")
    
    def get_quote(self) -> Optional[StockData]:
        """
        Fetch current stock quote for configured symbol.
        
        Returns:
            StockData object or None on failure/not configured
        """
        if not self.api_key or not self.symbol:
            logger.debug("Stock client not fully configured, skipping")
            return None
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": self.symbol,
            "apikey": self.api_key
        }
        
        response = self._make_request(self.BASE_URL, params=params)
        
        if not response:
            logger.error("Failed to fetch stock quote")
            return None
        
        try:
            data = response.json()
            quote = data.get("Global Quote", {})
            
            if not quote:
                logger.error("Empty quote response - check API key and symbol")
                return None
            
            price = quote.get("05. price", "N/A")
            change_percent = quote.get("10. change percent", "N/A")
            
            # Clean up percentage format
            if change_percent != "N/A":
                change_percent = f"{change_percent}"
            
            stock = StockData(
                symbol=self.symbol,
                price=price,
                change_percent=change_percent
            )
            
            logger.info(f"Stock {self.symbol}: ${price} ({change_percent})")
            return stock
        
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse stock response: {e}")
            return None
