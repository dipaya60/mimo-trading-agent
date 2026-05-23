import os

class Config:
    MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    MIMO_MODEL = os.getenv("MIMO_MODEL", "MiMo-V2.5-Pro")
    DEFAULT_CHAINS = ["ethereum", "arbitrum", "optimism", "polygon", "base", "solana"]
    RISK_TOLERANCE = os.getenv("RISK_TOLERANCE", "medium")
    MAX_POSITION_PCT = float(os.getenv("MAX_POSITION_PCT", "10"))
    STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "5"))
