"""Ticker -> logo resolution. Reads pre-downloaded files from assets/logos/ and
encodes them as base64 data URLs at render time (no live third-party fetch)."""
from __future__ import annotations

import base64
import os

import streamlit as st

LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logos")
LOGO_EXTENSIONS = ["svg", "png", "ico", "jpg", "jpeg"]

_MIME = {
    "svg": "image/svg+xml",
    "png": "image/png",
    "ico": "image/x-icon",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}

# Ticker -> primary company/issuer domain. Used by scripts/fetch_logos.py to source
# logos, and kept here so the mapping travels with the code. ~125 top US tickers + ETFs.
TICKER_DOMAINS: dict[str, str] = {
    "AAPL": "apple.com", "MSFT": "microsoft.com", "NVDA": "nvidia.com", "GOOGL": "abc.xyz",
    "GOOG": "abc.xyz", "AMZN": "amazon.com", "META": "meta.com", "TSLA": "tesla.com",
    "AVGO": "broadcom.com", "BRK-B": "berkshirehathaway.com", "LLY": "lilly.com",
    "JPM": "jpmorganchase.com", "V": "visa.com", "XOM": "exxonmobil.com", "UNH": "unitedhealthgroup.com",
    "MA": "mastercard.com", "COST": "costco.com", "HD": "homedepot.com", "PG": "pg.com",
    "NFLX": "netflix.com", "JNJ": "jnj.com", "ABBV": "abbvie.com", "CRM": "salesforce.com",
    "BAC": "bankofamerica.com", "ORCL": "oracle.com", "MRK": "merck.com", "CVX": "chevron.com",
    "KO": "coca-colacompany.com", "AMD": "amd.com", "PEP": "pepsico.com", "ADBE": "adobe.com",
    "WMT": "walmart.com", "TMO": "thermofisher.com", "MCD": "mcdonalds.com", "CSCO": "cisco.com",
    "ABT": "abbott.com", "LIN": "linde.com", "ACN": "accenture.com", "GE": "ge.com",
    "IBM": "ibm.com", "PM": "pmi.com", "TXN": "ti.com", "INTU": "intuit.com",
    "QCOM": "qualcomm.com", "CAT": "caterpillar.com", "AMGN": "amgen.com", "DHR": "danaher.com",
    "NOW": "servicenow.com", "ISRG": "intuitive.com", "VZ": "verizon.com", "NEE": "nexteraenergy.com",
    "DIS": "disney.com", "CMCSA": "comcastcorporation.com", "PFE": "pfizer.com", "WFC": "wellsfargo.com",
    "COP": "conocophillips.com", "RTX": "rtx.com", "UBER": "uber.com", "SPGI": "spglobal.com",
    "HON": "honeywell.com", "UNP": "up.com", "LOW": "lowes.com", "GS": "goldmansachs.com",
    "SCHW": "schwab.com", "ELV": "elevancehealth.com", "T": "att.com", "BLK": "blackrock.com",
    "BKNG": "bookingholdings.com", "AXP": "americanexpress.com", "PLD": "prologis.com",
    "SYK": "stryker.com", "MDT": "medtronic.com", "MS": "morganstanley.com", "TJX": "tjx.com",
    "ADP": "adp.com", "GILD": "gilead.com", "VRTX": "vrtx.com", "C": "citigroup.com",
    "MMC": "marshmclennan.com", "LRCX": "lamresearch.com", "ADI": "analog.com", "AMAT": "appliedmaterials.com",
    "SBUX": "starbucks.com", "MDLZ": "mondelezinternational.com", "REGN": "regeneron.com",
    "PGR": "progressive.com", "CB": "chubb.com", "ETN": "eaton.com", "BSX": "bostonscientific.com",
    "FI": "fiserv.com", "KLAC": "kla.com", "SO": "southerncompany.com", "ZTS": "zoetis.com",
    "DUK": "duke-energy.com", "SNPS": "synopsys.com", "CDNS": "cadence.com", "SLB": "slb.com",
    "PANW": "paloaltonetworks.com", "ITW": "itw.com", "MU": "micron.com", "EQIX": "equinix.com",
    "SHW": "sherwin-williams.com", "CME": "cmegroup.com", "APD": "airproducts.com", "AON": "aon.com",
    "ICE": "ice.com", "CL": "colgatepalmolive.com", "MO": "altria.com", "FDX": "fedex.com",
    "NOC": "northropgrumman.com", "TGT": "target.com", "EOG": "eogresources.com", "CSX": "csx.com",
    "APH": "amphenol.com", "WM": "wm.com", "MCK": "mckesson.com", "PSA": "publicstorage.com",
    "ORLY": "oreillyauto.com", "MAR": "marriott.com", "PYPL": "paypal.com", "NSC": "norfolksouthern.com",
    "ROP": "ropertech.com", "AJG": "ajg.com", "TT": "trane.com", "CMG": "chipotle.com",
    "CI": "cignagroup.com", "EMR": "emerson.com", "MSI": "motorolasolutions.com", "NXPI": "nxp.com",
    "SPY": "ssga.com", "QQQ": "invesco.com", "VOO": "vanguard.com", "IVV": "ishares.com",
    "XLK": "ssga.com", "XLF": "ssga.com", "XLV": "ssga.com", "XLE": "ssga.com",
    "XLI": "ssga.com", "XLY": "ssga.com", "XLP": "ssga.com", "XLU": "ssga.com",
    "XLRE": "ssga.com", "XLB": "ssga.com", "XLC": "ssga.com",
}

# Known simple-icons slugs for tickers that have a clean brand icon there.
TICKER_SIMPLEICON_SLUGS: dict[str, str] = {
    "AAPL": "apple", "MSFT": "microsoft", "NVDA": "nvidia", "GOOGL": "google", "GOOG": "google",
    "AMZN": "amazon", "META": "meta", "TSLA": "tesla", "NFLX": "netflix", "ADBE": "adobe",
    "CRM": "salesforce", "ORCL": "oracle", "CSCO": "cisco", "IBM": "ibm", "INTU": "intuit",
    "QCOM": "qualcomm", "AMD": "amd", "UBER": "uber", "PYPL": "paypal", "V": "visa",
    "MA": "mastercard", "DIS": "disney", "SBUX": "starbucks", "TGT": "target", "FDX": "fedex",
    "MCD": "mcdonalds", "WMT": "walmart", "KO": "cocacola", "PEP": "pepsi", "T": "att",
    "VZ": "verizon", "SPGI": "spglobal", "PANW": "paloaltonetworks", "NOW": "servicenow",
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_logo_data_url(ticker: str) -> str | None:
    """Return a base64 data: URL for a locally-stored logo, or None if unavailable."""
    ticker = ticker.upper()
    for ext in LOGO_EXTENSIONS:
        path = os.path.join(LOGO_DIR, f"{ticker}.{ext}")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("ascii")
                return f"data:{_MIME[ext]};base64,{encoded}"
            except Exception:
                return None
    return None


def render_logo_html(ticker: str, size: int = 32) -> str:
    """Return an <img> tag for the ticker's logo, or a text-initial placeholder."""
    data_url = get_logo_data_url(ticker)
    if data_url:
        return (
            f'<img src="{data_url}" width="{size}" height="{size}" '
            f'style="border-radius:6px;object-fit:contain;background:#fff;padding:2px;" />'
        )
    initial = ticker[0] if ticker else "?"
    font_size = max(10, int(size * 0.45))
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:6px;background:#2b3a4d;'
        f'display:flex;align-items:center;justify-content:center;color:#fff;'
        f'font-size:{font_size}px;font-weight:600;">{initial}</div>'
    )
