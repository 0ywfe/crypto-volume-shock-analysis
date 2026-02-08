# config.py
# v0.4 — LSE Volume Shock Drift Configuration

from dataclasses import dataclass


@dataclass
class Config:
    # =========================
    # VOLUME SHOCK DETECTION
    # =========================
    VOLUME_LOOKBACK_DAYS: int = 20
    VOLUME_SHOCK_THRESHOLD_STD: float = 2.0
    
    # =========================
    # FORWARD RETURN HORIZONS
    # =========================
    FORWARD_HORIZONS_DAYS: list = None
    
    def __post_init__(self):
        if self.FORWARD_HORIZONS_DAYS is None:
            self.FORWARD_HORIZONS_DAYS = [1, 3, 5, 10]
    
    # =========================
    # LIQUIDITY PROXY
    # =========================
    LIQUIDITY_ADV_WINDOW_DAYS: int = 60
    LIQUIDITY_QUINTILES: int = 5
    
    # =========================
    # CONVICTION & REGIME FILTERS
    # =========================
    HIGH_CONVICTION_RANGE_THRESHOLD_PCT: float = 5.0
    DIRECTION_CHANGE_THRESHOLD_PCT: float = 0.5
    
    # =========================
    # NEW: EXTENDED TESTING
    # =========================
    EXTENDED_HORIZONS: list = None  # [20, 30, 60, 90]
    EARNINGS_PROXY_THRESHOLD_PCT: float = 10.0  # |price change| > 10% = likely earnings
    
    # Trailing stop parameters
    TRAILING_STOP_LOSER_DAYS: int = 3
    TRAILING_STOP_LOSER_PCT: float = -2.0
    TRAILING_STOP_WINNER_GIVEBACK_PCT: float = 5.0
    
    # Market cap bins (in £M)
    MCAP_BINS: list = None  # [50, 200, 500, 2000, 5000]
    
    def __post_init__(self):
        if self.FORWARD_HORIZONS_DAYS is None:
            self.FORWARD_HORIZONS_DAYS = [1, 3, 5, 10]
        if self.EXTENDED_HORIZONS is None:
            self.EXTENDED_HORIZONS = [20, 30, 60, 90]
        if self.MCAP_BINS is None:
            self.MCAP_BINS = [50, 200, 500, 2000, 5000]
    
    # =========================
    # TRANSACTION COSTS
    # =========================
    TRANSACTION_COST_BPS: float = 50.0
    
    # =========================
    # DATA REQUIREMENTS
    # =========================
    MIN_OBSERVATIONS_PER_STOCK: int = 100