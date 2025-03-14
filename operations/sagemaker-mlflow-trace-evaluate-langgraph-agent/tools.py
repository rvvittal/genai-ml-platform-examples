from langchain_core.tools import tool

from data import STOCK_PRICE

# Define the tools for the agent to use

@tool
def get_stock_price_data(symbol: str) -> float:
    """Fetches the current stock price for a given symbol.

    Args:
        symbol: The name of the stock symbol (e.g., 'AMZN', 'AAPL', 'NVDA').

    Returns:
        float: The current price of the stock in dollars per stock.

    Raises:
        KeyError: If the specified stock is not found in the data source.
    """
    try:
        stock_name = symbol.upper().strip()
        if stock_name not in STOCK_PRICE:
            raise KeyError(
                f"Stock symbol'{stock_name}' not found. Available stock symbols: {', '.join(STOCK_PRICE.keys())}"
            )
        return STOCK_PRICE[stock_name]
    except Exception as e:
        raise Exception(f"Error fetching Stock price: {str(e)}")
