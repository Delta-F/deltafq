"""
Map live data gateway names to DataFetcher source values.
"""

from typing import Dict

_GATEWAY_TO_FETCHER: Dict[str, str] = {
    "yfinance": "yahoo",
    "miniqmt": "miniqmt",
}


def fetcher_source_for_data_gateway(gateway_name: str) -> str:
    """
    LiveEngine registers gateways by short name; DataFetcher uses historical source ids.

    - ``yfinance`` gateway -> ``yahoo`` fetcher (yfinance)
    - ``miniqmt`` gateway -> ``miniqmt`` fetcher (xtquant / miniQMT)
    """
    if gateway_name not in _GATEWAY_TO_FETCHER:
        raise ValueError(
            f"Unknown data gateway {gateway_name!r}. "
            f"Known: {list(_GATEWAY_TO_FETCHER.keys())}"
        )
    return _GATEWAY_TO_FETCHER[gateway_name]
