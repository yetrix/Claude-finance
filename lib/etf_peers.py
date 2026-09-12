"""Curated ETF peer groups (same category, different issuer) for expense-ratio
and cost comparisons. Not exhaustive — covers common broad-market, sector, and
style categories."""

PEER_GROUPS: list[list[str]] = [
    ["SPY", "VOO", "IVV", "SPLG"],
    ["QQQ", "QQQM", "ONEQ"],
    ["VTI", "ITOT", "SCHB"],
    ["VUG", "SCHG", "IVW"],
    ["VTV", "SCHV", "IVE"],
    ["XLK", "VGT", "FTEC"],
    ["XLF", "VFH", "KBE"],
    ["XLV", "VHT", "IYH"],
    ["XLE", "VDE", "IYE"],
    ["XLI", "VIS", "IYJ"],
    ["XLY", "VCR", "FDIS"],
    ["XLP", "VDC", "FSTA"],
    ["XLU", "VPU", "FUTY"],
    ["XLRE", "VNQ", "IYR"],
    ["XLB", "VAW", "IYM"],
    ["XLC", "VOX", "FCOM"],
    ["VXUS", "IXUS", "VEU"],
    ["VWO", "IEMG", "SCHE"],
    ["AGG", "BND", "SCHZ"],
    ["VYM", "SCHD", "DVY"],
    ["ARKK", "QQQM"],
]


def get_peers(ticker: str) -> list[str]:
    """Return the curated peer tickers for `ticker` (excluding itself), or [] if
    it isn't in any known category."""
    ticker = ticker.upper()
    for group in PEER_GROUPS:
        if ticker in group:
            return [t for t in group if t != ticker]
    return []
