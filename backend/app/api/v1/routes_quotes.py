from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.quote import DelayedQuote
from app.services.delayed_data import (
    fetch_delayed_quotes,
    get_cached_delayed_quote,
    get_cached_delayed_quotes,
    refresh_delayed_quotes,
)

router = APIRouter()


@router.get("/", response_model=List[DelayedQuote])
def read_delayed_quotes(symbols: Optional[str] = Query(
    None,
    description="Comma-separated symbols to fetch delayed quotes for.",
)):
    if not symbols:
        raise HTTPException(status_code=400, detail="Query parameter 'symbols' is required.")

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="At least one symbol must be provided.")

    quotes = get_cached_delayed_quotes(symbol_list)
    if not quotes:
        raise HTTPException(status_code=404, detail="No delayed quotes available for requested symbols.")

    return quotes


@router.get("/refresh", response_model=List[DelayedQuote])
def refresh_delayed_quotes_endpoint(symbols: Optional[str] = Query(
    None,
    description="Comma-separated symbols to refresh delayed quotes for.",
)):
    if not symbols:
        raise HTTPException(status_code=400, detail="Query parameter 'symbols' is required.")

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="At least one symbol must be provided.")

    quotes = refresh_delayed_quotes(symbol_list)
    if not quotes:
        raise HTTPException(status_code=404, detail="No delayed quotes available for requested symbols.")

    return list(quotes.values())


@router.get("/{symbol}", response_model=DelayedQuote)
def read_delayed_quote(symbol: str):
    quote = get_cached_delayed_quote(symbol)
    if quote is None:
        quote_map = fetch_delayed_quotes([symbol])
        quote = quote_map.get(symbol.upper())

    if quote is None:
        raise HTTPException(status_code=404, detail=f"No delayed quote available for {symbol}.")

    return quote
