import ccxt
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import time
import warnings

warnings.filterwarnings('ignore')


class MexcWickScanner:
    def __init__(self, api_key: str = None, api_secret: str = None, top_volume_limit: int = 200):
        """
        Initialize MEXC Wick Scanner - Scans top N futures pairs by volume
        CRITERIA: 
        - ONE SIDE (upper OR lower) must have wick >= 2x body size
        - The OTHER SIDE must NOT also be significant (filter indecision candles)
        - Indecision = both upper and lower wicks are >= body size
        """
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })
        
        self.timeframe = '30m'
        self.required_candles = 100
        self.top_volume_limit = top_volume_limit
        
        # Wick must be at least 4x the body size
        self.min_wick_ratio = 4.0
        
        # Cache for symbols
        self.cached_symbols = None
        self.cached_symbols_with_volume = None
        self.last_symbols_fetch = None

    def get_top_futures_by_volume(self, force_refresh: bool = False) -> List[Dict]:
        """Fetch top futures symbols by 24h volume"""
        if not force_refresh and self.cached_symbols_with_volume and self.last_symbols_fetch:
            if (datetime.now() - self.last_symbols_fetch).seconds < 300:
                return self.cached_symbols_with_volume
        
        try:
            print(f"🔄 Fetching MEXC futures by volume...")
            markets = self.exchange.load_markets()
            
            all_futures = []
            for symbol, market in markets.items():
                if (market.get('future') or market.get('swap')) and '/USDT' in symbol:
                    if market.get('linear', False) or not market.get('inverse', False):
                        all_futures.append(symbol)
            
            print(f"📊 Found {len(all_futures)} total futures pairs")
            
            symbols_with_volume = []
            for symbol in all_futures:
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    volume_24h = ticker.get('quoteVolume', 0)
                    
                    if volume_24h > 0:
                        symbols_with_volume.append({
                            'symbol': symbol,
                            'volume_24h': volume_24h,
                            'last_price': ticker.get('last', 0),
                            'change_24h': ticker.get('percentage', 0),
                            'high_24h': ticker.get('high', 0),
                            'low_24h': ticker.get('low', 0)
                        })
                    time.sleep(0.05)
                except:
                    continue
            
            symbols_with_volume.sort(key=lambda x: x['volume_24h'], reverse=True)
            top_symbols = symbols_with_volume[:self.top_volume_limit]
            
            self.cached_symbols_with_volume = top_symbols
            self.cached_symbols = [s['symbol'] for s in top_symbols]
            self.last_symbols_fetch = datetime.now()
            
            print(f"✅ Selected top {len(top_symbols)} pairs by volume")
            return top_symbols
            
        except Exception as e:
            print(f"❌ Volume fetch error: {e}")
            if self.cached_symbols:
                return [{'symbol': s, 'volume_24h': 0} for s in self.cached_symbols]
            return []

    def calculate_candle_metrics(self, candle_data: list) -> Optional[Dict]:
        """Calculate candle metrics"""
        if len(candle_data) < 5:
            return None
        
        timestamp, open_price, high, low, close = candle_data[:5]
        
        body_size = abs(close - open_price)
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low
        total_range = high - low
        
        is_green = close > open_price
        color = 'green' if is_green else 'red'
        
        # Calculate ratios (wick size / body size)
        upper_wick_ratio = upper_wick / body_size if body_size > 0 else 0
        lower_wick_ratio = lower_wick / body_size if body_size > 0 else 0
        
        # Calculate percentages of total candle (for display)
        if total_range > 0:
            body_percentage = (body_size / total_range) * 100
            upper_wick_percentage = (upper_wick / total_range) * 100
            lower_wick_percentage = (lower_wick / total_range) * 100
        else:
            body_percentage = upper_wick_percentage = lower_wick_percentage = 0
        
        return {
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'color': color,
            'is_green': is_green,
            'body_size': body_size,
            'upper_wick': upper_wick,
            'lower_wick': lower_wick,
            'total_range': total_range,
            # Ratios (wick / body)
            'upper_wick_ratio': round(upper_wick_ratio, 2),
            'lower_wick_ratio': round(lower_wick_ratio, 2),
            # Percentages (for display)
            'body_percentage': round(body_percentage, 1),
            'upper_wick_percentage': round(upper_wick_percentage, 1),
            'lower_wick_percentage': round(lower_wick_percentage, 1)
        }

    def detect_wick_pattern(self, current_candle: Dict, previous_candle: Dict) -> Optional[Dict]:
        """
        Detect significant single-sided wick pattern
        
        RULES:
        1. ONE side (upper OR lower) must have wick >= 2x body size
        2. The OTHER side must NOT have wick >= body size (no indecision)
        3. Previous candle must match current candle color (continuation)
        """
        if not current_candle or not previous_candle:
            return None
        
        # Check continuation pattern (previous candle same color)
        if current_candle['color'] != previous_candle['color']:
            return None
        
        # Check if each side has significant wick (>= min_wick_ratio)
        upper_significant = current_candle['upper_wick_ratio'] >= self.min_wick_ratio
        lower_significant = current_candle['lower_wick_ratio'] >= self.min_wick_ratio
        
        # FILTER OUT indecision candles (both sides significant)
        # Example: upper 40%, lower 40%, body 20% -> BOTH significant -> FILTER
        if upper_significant and lower_significant:
            return None  # Indecision candle - filter out
        
        # Check for UPPER WICK DOMINANT (bearish rejection)
        if upper_significant:
            # Only show on RED candles (bearish)
            if current_candle['color'] != 'red':
                return None
            
            wick_type = 'top'
            pattern_strength = current_candle['upper_wick_ratio']
            wick_size = current_candle['upper_wick']
            wick_ratio = current_candle['upper_wick_ratio']
            wick_percentage = current_candle['upper_wick_percentage']
            body_percentage = current_candle['body_percentage']
            other_wick_percentage = current_candle['lower_wick_percentage']
            
            pattern_description = f"Upper wick {wick_ratio:.1f}x body | Upper wick: {wick_percentage:.0f}%, Body: {body_percentage:.0f}%, Lower wick: {other_wick_percentage:.0f}%"
            
        # Check for LOWER WICK DOMINANT (bullish bounce)
        elif lower_significant:
            # Only show on GREEN candles (bullish)
            if current_candle['color'] != 'green':
                return None
            
            wick_type = 'bottom'
            pattern_strength = current_candle['lower_wick_ratio']
            wick_size = current_candle['lower_wick']
            wick_ratio = current_candle['lower_wick_ratio']
            wick_percentage = current_candle['lower_wick_percentage']
            body_percentage = current_candle['body_percentage']
            other_wick_percentage = current_candle['upper_wick_percentage']
            
            pattern_description = f"Lower wick {wick_ratio:.1f}x body | Lower wick: {wick_percentage:.0f}%, Body: {body_percentage:.0f}%, Upper wick: {other_wick_percentage:.0f}%"
        
        else:
            return None  # No significant wick on either side
        
        return {
            'wick_type': wick_type,
            'pattern_strength': pattern_strength,
            'wick_ratio': wick_ratio,
            'wick_size': wick_size,
            'wick_percentage': wick_percentage,
            'body_percentage': body_percentage,
            'other_wick_percentage': other_wick_percentage,
            'pattern_description': pattern_description,
            'current_candle': current_candle,
            'previous_candle': previous_candle,
            'timestamp': datetime.fromtimestamp(current_candle['timestamp'] / 1000),
            'color': current_candle['color'],
            'exchange': 'MEXC',
            'body_size': current_candle['body_size'],
            'candle_color': current_candle['color']
        }

    def analyze_symbol(self, symbol_info: Dict) -> Optional[Dict]:
        """Analyze a single symbol for wick patterns"""
        symbol = symbol_info['symbol']
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=self.timeframe,
                limit=self.required_candles
            )
            
            if len(ohlcv) < 2:
                return None
            
            current_candle = self.calculate_candle_metrics(ohlcv[-1])
            previous_candle = self.calculate_candle_metrics(ohlcv[-2])
            
            pattern = self.detect_wick_pattern(current_candle, previous_candle)
            
            if pattern:
                pattern['symbol'] = symbol
                pattern['current_price'] = current_candle['close']
                pattern['volume_24h'] = symbol_info.get('volume_24h', 0)
                pattern['high_24h'] = symbol_info.get('high_24h', current_candle['high'])
                pattern['low_24h'] = symbol_info.get('low_24h', current_candle['low'])
                pattern['change_24h'] = symbol_info.get('change_24h', 0)
                
                return pattern
            
            return None
            
        except Exception as e:
            return None

    async def scan_symbols_async(self, symbols_with_volume: List[Dict], max_concurrent: int = 20) -> List[Dict]:
        """Scan symbols asynchronously"""
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scan_one(symbol_info):
            async with semaphore:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.analyze_symbol, symbol_info)
                return result
        
        tasks = [scan_one(symbol_info) for symbol_info in symbols_with_volume]
        results = await asyncio.gather(*tasks)
        
        return [r for r in results if r is not None]

    async def full_scan(self, max_workers: int = 20) -> Dict:
        """Perform full scan of top MEXC futures pairs"""
        try:
            print(f"\n{'='*70}")
            print(f"🚀 MEXC WICK SCANNER - NO INDECISION CANDLES")
            print(f"📊 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📏 Criteria: ONE side (upper/lower) must be >= {self.min_wick_ratio}x body size")
            print(f"🚫 Filter: BOTH sides significant = indecision (filtered out)")
            print(f"📈 Volume Filter: Top {self.top_volume_limit} pairs by 24h volume")
            print(f"{'='*70}")
            
            # Get top symbols by volume
            symbols_with_volume = self.get_top_futures_by_volume()
            
            if not symbols_with_volume:
                return {
                    'error': 'No symbols found',
                    'timestamp': datetime.now().isoformat(),
                    'patterns': []
                }
            
            print(f"\n📈 Scanning top {len(symbols_with_volume)} MEXC futures pairs...")
            print(f"⚡ Using {max_workers} concurrent workers")
            print(f"🎯 Looking for dominant wicks (one side only)")
            print(f"🚫 Filtering out indecision candles (both sides have wicks)")
            
            # Scan all symbols
            start_time = datetime.now()
            patterns = await self.scan_symbols_async(symbols_with_volume, max_concurrent=max_workers)
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            # Separate top and bottom wicks
            top_wick_patterns = [p for p in patterns if p['wick_type'] == 'top']
            bottom_wick_patterns = [p for p in patterns if p['wick_type'] == 'bottom']
            
            # Sort by pattern strength (highest wick/body ratio first)
            top_wick_patterns.sort(key=lambda x: x['pattern_strength'], reverse=True)
            bottom_wick_patterns.sort(key=lambda x: x['pattern_strength'], reverse=True)
            
            # Calculate statistics
            strong_patterns = [p for p in patterns if p['pattern_strength'] >= 3.0]  # 3x+
            extreme_patterns = [p for p in patterns if p['pattern_strength'] >= 5.0]  # 5x+
            
            print(f"\n✅ Scan completed in {scan_duration:.1f} seconds")
            print(f"📊 Results:")
            print(f"   • Total scanned: {len(symbols_with_volume)} symbols")
            print(f"   • Total patterns: {len(patterns)}")
            print(f"   • 🔴 Top wicks (bearish): {len(top_wick_patterns)}")
            print(f"   • 🟢 Bottom wicks (bullish): {len(bottom_wick_patterns)}")
            print(f"   • 💪 Strong patterns (3x+): {len(strong_patterns)}")
            print(f"   • ⚡ Extreme patterns (5x+): {len(extreme_patterns)}")
            print(f"   • 🚫 Indecision candles filtered: Yes (both sides significant)")
            
            # Show top 5 strongest patterns
            if patterns:
                print(f"\n🏆 TOP 5 STRONGEST PATTERNS:")
                for i, p in enumerate(patterns[:5]):
                    print(f"   {i+1}. {p['symbol']}: {p['wick_type'].upper()} wick - {p['pattern_strength']:.1f}x body")
                    print(f"      📊 {p['pattern_description']}")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'exchange': 'MEXC',
                'total_scanned': len(symbols_with_volume),
                'total_patterns_found': len(patterns),
                'scan_duration_seconds': round(scan_duration, 1),
                'min_wick_ratio': self.min_wick_ratio,
                'top_volume_limit': self.top_volume_limit,
                'top_wick_patterns': top_wick_patterns,
                'bottom_wick_patterns': bottom_wick_patterns,
                'strong_patterns_count': len(strong_patterns),
                'extreme_patterns_count': len(extreme_patterns)
            }
            
        except Exception as e:
            print(f"❌ Scan error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'exchange': 'MEXC',
                'patterns': []
            }

    def format_pattern_for_display(self, pattern: Dict) -> Dict:
        """Format pattern for JSON response"""
        return {
            'symbol': pattern['symbol'],
            'wick_type': pattern['wick_type'],
            'pattern_strength': pattern['pattern_strength'],
            'wick_ratio': pattern['wick_ratio'],
            'wick_size': pattern['wick_size'],
            'wick_percentage': pattern['wick_percentage'],
            'body_percentage': pattern['body_percentage'],
            'other_wick_percentage': pattern.get('other_wick_percentage', 0),
            'pattern_description': pattern.get('pattern_description', ''),
            'current_price': pattern['current_price'],
            'timestamp': pattern['timestamp'].isoformat(),
            'color': pattern['color'],
            'exchange': pattern.get('exchange', 'MEXC'),
            'body_size': pattern['body_size'],
            'volume_24h': pattern.get('volume_24h', 0),
            'high_24h': pattern.get('high_24h', 0),
            'low_24h': pattern.get('low_24h', 0),
            'change_24h': pattern.get('change_24h', 0),
            'candle_details': {
                'open': pattern['current_candle']['open'],
                'high': pattern['current_candle']['high'],
                'low': pattern['current_candle']['low'],
                'close': pattern['current_candle']['close'],
                'body_size': pattern['current_candle']['body_size'],
                'body_percentage': pattern['current_candle']['body_percentage'],
                'upper_wick_percentage': pattern['current_candle']['upper_wick_percentage'],
                'lower_wick_percentage': pattern['current_candle']['lower_wick_percentage'],
                'candle_color': pattern['current_candle']['color']
            }
        }


# Standalone testing function
async def test_mexc_scanner():
    """Test the MEXC scanner"""
    print("\n" + "="*80)
    print("🔍 TESTING MEXC WICK SCANNER")
    print("📊 Criteria: ONE side (upper/lower) >= 2x body")
    print("🚫 Filter: BOTH sides significant = indecision (filtered)")
    print("="*80)
    
    scanner = MexcWickScanner(top_volume_limit=200)
    
    print("\n📡 Scanning top 200 MEXC futures pairs by volume...")
    print("🎯 What we look for:")
    print("   • 🔴 UPPER WICK DOMINANT: Upper wick >= 2x body, lower wick can be anything")
    print("   • 🟢 LOWER WICK DOMINANT: Lower wick >= 2x body, upper wick can be anything")
    print("   • 🚫 INDECISION: BOTH upper AND lower wick >= body -> FILTERED OUT")
    print(f"   • 📏 Minimum ratio: {scanner.min_wick_ratio}x body size")
    print("-"*80)
    
    results = await scanner.full_scan(max_workers=20)
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        return results
    
    print(f"\n{'='*80}")
    print("📊 SCAN RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Total Scanned: {results['total_scanned']} symbols")
    print(f"🎯 Total Patterns: {results['total_patterns_found']}")
    print(f"🟢 Bottom Wicks (Bullish): {len(results['bottom_wick_patterns'])}")
    print(f"🔴 Top Wicks (Bearish): {len(results['top_wick_patterns'])}")
    print(f"💪 Strong Patterns (3x+): {results['strong_patterns_count']}")
    print(f"⚡ Extreme Patterns (5x+): {results['extreme_patterns_count']}")
    print(f"⏱️  Scan Duration: {results['scan_duration_seconds']} seconds")
    
    # Display top patterns
    if results['bottom_wick_patterns']:
        print(f"\n{'='*80}")
        print("🟢 BOTTOM WICKS (Bullish - Green Candles)")
        print(f"{'='*80}")
        print(f"{'Symbol':<15} {'Ratio':<10} {'Wick%':<8} {'Body%':<8} {'Other%':<8} {'Price':<12}")
        print("-"*80)
        for p in results['bottom_wick_patterns'][:10]:
            formatted = scanner.format_pattern_for_display(p)
            print(f"{formatted['symbol']:<15} {formatted['wick_ratio']:>6.1f}x   "
                  f"{formatted['wick_percentage']:>5.1f}%  "
                  f"{formatted['body_percentage']:>5.1f}%  "
                  f"{formatted['other_wick_percentage']:>5.1f}%  "
                  f"${formatted['current_price']:>10,.2f}")
    
    if results['top_wick_patterns']:
        print(f"\n{'='*80}")
        print("🔴 TOP WICKS (Bearish - Red Candles)")
        print(f"{'='*80}")
        print(f"{'Symbol':<15} {'Ratio':<10} {'Wick%':<8} {'Body%':<8} {'Other%':<8} {'Price':<12}")
        print("-"*80)
        for p in results['top_wick_patterns'][:10]:
            formatted = scanner.format_pattern_for_display(p)
            print(f"{formatted['symbol']:<15} {formatted['wick_ratio']:>6.1f}x   "
                  f"{formatted['wick_percentage']:>5.1f}%  "
                  f"{formatted['body_percentage']:>5.1f}%  "
                  f"{formatted['other_wick_percentage']:>5.1f}%  "
                  f"${formatted['current_price']:>10,.2f}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_mexc_scanner())