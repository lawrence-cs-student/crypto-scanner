import requests
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple

BASE_URL = "https://api.bybit.com"
INTERVAL = "30"
LIMIT = 2


class CryptoScanner:
    def __init__(self):
        self.session = requests.Session()
    
    def get_top_gainers_losers(self, top_n: int = 25) -> Tuple[List[Dict], List[Dict]]:
        """Get top N gainers and losers based on 24h price change %"""
        url = f"{BASE_URL}/v5/market/tickers"
        params = {"category": "linear"}
        res = self.session.get(url, params=params).json()
        
        if res["retCode"] != 0:
            raise Exception("Symbol fetch failed")

        # Filter USDT symbols and calculate price change %
        usdt_symbols = []
        for s in res["result"]["list"]:
            if s["symbol"].endswith("USDT"):
                try:
                    price_change_pct = float(s.get("price24hPcnt", 0)) * 100
                    usdt_symbols.append({
                        "symbol": s["symbol"],
                        "change_pct": price_change_pct,
                        "volume": float(s.get("turnover24h", 0)),
                        "last_price": float(s.get("lastPrice", 0)),
                        "high_24h": float(s.get("highPrice24h", 0)),
                        "low_24h": float(s.get("lowPrice24h", 0))
                    })
                except (ValueError, TypeError):
                    continue

        # Sort by price change % and get top gainers and losers
        usdt_symbols.sort(key=lambda x: x["change_pct"], reverse=True)

        # Top gainers (highest positive %)
        top_gainers = usdt_symbols[:top_n]

        # Top losers (lowest negative %)
        top_losers = usdt_symbols[-top_n:]
        top_losers.reverse()  # Reverse to show biggest losers first

        return top_gainers, top_losers

    def get_last_candles(self, symbol: str, limit: int = LIMIT) -> List[Dict]:
        """Fetch last N candles for a symbol"""
        url = f"{BASE_URL}/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": INTERVAL,
            "limit": limit
        }
        res = self.session.get(url, params=params).json()
        if res["retCode"] != 0 or len(res["result"]["list"]) < limit:
            return []

        return [
            {
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4])
            } for c in res["result"]["list"]
        ]

    def has_both_wicks(self, c: Dict) -> bool:
        """Check if candle has both upper and lower wicks"""
        return c["high"] > max(c["open"], c["close"]) and c["low"] < min(c["open"], c["close"])

    def wicks_touch(self, prev: Dict, curr: Dict, direction: str) -> bool:
        """Check if current candle's wick touches previous candle's body"""
        if direction == "green":
            curr_body_top = max(curr["open"], curr["close"])
            prev_body_top = max(prev["open"], prev["close"])
            return curr["high"] >= prev_body_top and curr_body_top <= prev["high"]

        if direction == "red":
            curr_body_bottom = min(curr["open"], curr["close"])
            prev_body_bottom = min(prev["open"], prev["close"])
            return curr["low"] <= prev_body_bottom and curr_body_bottom >= prev["low"]

        return False

    def wick_reaches_open_without_exceeding_extreme(self, prev: Dict, curr: Dict, direction: str) -> bool:
        """Check if current candle's wick reaches previous open without exceeding extremes"""
        if direction == "red":
            return curr["high"] >= prev["open"] and curr["high"] <= prev["high"]
        elif direction == "green":
            return curr["low"] <= prev["open"] and curr["low"] >= prev["low"]
        return False

    def detect_2_candles(self, candles: List[Dict], target_direction: Optional[str] = None) -> Optional[str]:
        """Detect 2-candle momentum pattern"""
        if len(candles) < 2:
            return None

        # Check if both candles are the same direction
        both_red = candles[0]["close"] < candles[0]["open"] and candles[1]["close"] < candles[1]["open"]
        both_green = candles[0]["close"] > candles[0]["open"] and candles[1]["close"] > candles[1]["open"]

        # If target_direction is "red", ONLY check red pattern
        if target_direction == "red":
            if not both_red:
                return None

            if not (self.has_both_wicks(candles[0]) and self.has_both_wicks(candles[1])):
                return None

            if not (self.wicks_touch(candles[1], candles[0], "red") and
                    self.wick_reaches_open_without_exceeding_extreme(candles[1], candles[0], "red")):
                return None

            return "🔴 2 Red w/ Wicks + Wick Touch + Open Reached"

        # If target_direction is "green", ONLY check green pattern
        if target_direction == "green":
            if not both_green:
                return None

            if not (self.has_both_wicks(candles[0]) and self.has_both_wicks(candles[1])):
                return None

            if not (self.wicks_touch(candles[1], candles[0], "green") and
                    self.wick_reaches_open_without_exceeding_extreme(candles[1], candles[0], "green")):
                return None

            return "🟢 2 Green w/ Wicks + Wick Touch + Open Reached"

        # If no target_direction specified, check both
        if both_red:
            if not (self.has_both_wicks(candles[0]) and self.has_both_wicks(candles[1])):
                return None
            if not (self.wicks_touch(candles[1], candles[0], "red") and
                    self.wick_reaches_open_without_exceeding_extreme(candles[1], candles[0], "red")):
                return None
            return "🔴 2 Red w/ Wicks + Wick Touch + Open Reached"

        if both_green:
            if not (self.has_both_wicks(candles[0]) and self.has_both_wicks(candles[1])):
                return None
            if not (self.wicks_touch(candles[1], candles[0], "green") and
                    self.wick_reaches_open_without_exceeding_extreme(candles[1], candles[0], "green")):
                return None
            return "🟢 2 Green w/ Wicks + Wick Touch + Open Reached"

        return None

    async def scan_symbols(self, symbols: List[Dict], direction: str) -> List[Dict]:
        """Scan a list of symbols for patterns"""
        results = []
        for coin in symbols:
            symbol = coin["symbol"]
            try:
                candles = self.get_last_candles(symbol)
                if candles:
                    pattern = self.detect_2_candles(candles, direction if direction != "both" else None)
                    if pattern:
                        results.append({
                            "symbol": symbol,
                            "pattern": pattern,
                            "change_pct": coin["change_pct"],
                            "last_price": coin["last_price"],
                            "volume": coin["volume"],
                            "high_24h": coin["high_24h"],
                            "low_24h": coin["low_24h"]
                        })
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        return results

    async def full_scan(self, top_n: int = 25) -> Dict:
        """Perform a full scan of top gainers and losers"""
        try:
            gainers, losers = self.get_top_gainers_losers(top_n)
            
            # Scan both directions concurrently
            gainer_results, loser_results = await asyncio.gather(
                self.scan_symbols(gainers, "green"),
                self.scan_symbols(losers, "red")
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "gainers": gainer_results,
                "losers": loser_results,
                "total_gainers_scanned": len(gainers),
                "total_losers_scanned": len(losers)
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }