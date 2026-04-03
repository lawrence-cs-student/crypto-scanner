from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
from datetime import datetime
import threading
import time
import os


# Import both scanners
from scanner import CryptoScanner  # Your original Bybit scanner
from mexc_scanner import MexcWickScanner  # MEXC scanner

app = FastAPI(title="Crypto Scanner API", version="1.0.0")

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://localhost:8000"
).split(",")

# Enable CORS for React frontend

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Initialize scanners
bybit_scanner = CryptoScanner()
mexc_scanner = MexcWickScanner()  # Scan all pairs

# Store for background scan results
scan_cache = {
    "bybit": {
        "last_scan": None,
        "results": None,
        "status": "idle",
        "next_scan": None
    },
    "mexc": {
        "last_scan": None,
        "results": None,
        "status": "idle",
        "next_scan": None
    }
}

async def perform_bybit_scan():
    """Perform Bybit scan"""
    try:
        scan_cache["bybit"]["status"] = "scanning"
        print(f"[{datetime.now()}] Starting Bybit scan...")
        
        results = await bybit_scanner.full_scan(25)
        
        scan_cache["bybit"]["results"] = results
        scan_cache["bybit"]["last_scan"] = datetime.now()
        scan_cache["bybit"]["status"] = "completed"
        
        print(f"[{datetime.now()}] Bybit scan completed. Found {len(results.get('gainers', []))} gainers and {len(results.get('losers', []))} losers.")
        
    except Exception as e:
        scan_cache["bybit"]["status"] = "error"
        scan_cache["bybit"]["results"] = {"error": str(e)}
        print(f"Bybit scan error: {e}")

async def perform_mexc_scan():
    """Perform MEXC scan with wick/body ratio criteria"""
    try:
        scan_cache["mexc"]["status"] = "scanning"
        print(f"[{datetime.now()}] Starting MEXC scan...")
        print(f"📊 Criteria: ONE side (upper/lower) >= {mexc_scanner.min_wick_ratio}x body size")
        print(f"🚫 Filter: BOTH sides significant = indecision (filtered out)")
        
        # Use the full_scan method
        results = await mexc_scanner.full_scan(max_workers=50)
        
        # Format results for frontend
        if 'error' not in results:
            formatted_results = {
                'timestamp': results['timestamp'],
                'exchange': 'MEXC',
                'total_scanned': results['total_scanned'],
                'total_patterns_found': results['total_patterns_found'],
                'scan_duration_seconds': results.get('scan_duration_seconds', 0),
                'min_wick_ratio': results.get('min_wick_ratio', mexc_scanner.min_wick_ratio),
                'strong_patterns_count': results.get('strong_patterns_count', 0),
                'extreme_patterns_count': results.get('extreme_patterns_count', 0),
                'top_wick_patterns': [mexc_scanner.format_pattern_for_display(p) for p in results['top_wick_patterns']],
                'bottom_wick_patterns': [mexc_scanner.format_pattern_for_display(p) for p in results['bottom_wick_patterns']]
            }
            scan_cache["mexc"]["results"] = formatted_results
        else:
            scan_cache["mexc"]["results"] = results
        
        scan_cache["mexc"]["last_scan"] = datetime.now()
        scan_cache["mexc"]["status"] = "completed"
        
        print(f"[{datetime.now()}] MEXC scan completed!")
        print(f"   • Total scanned: {results.get('total_scanned', 0)} symbols")
        print(f"   • Patterns found: {results.get('total_patterns_found', 0)}")
        print(f"   • Strong patterns (3x+): {results.get('strong_patterns_count', 0)}")
        print(f"   • Extreme patterns (5x+): {results.get('extreme_patterns_count', 0)}")
        print(f"   • Duration: {results.get('scan_duration_seconds', 0)} seconds")
        
    except Exception as e:
        scan_cache["mexc"]["status"] = "error"
        scan_cache["mexc"]["results"] = {"error": str(e)}
        print(f"MEXC scan error: {e}")

async def perform_all_scans():
    """Perform both scans simultaneously"""
    await asyncio.gather(
        perform_bybit_scan(),
        perform_mexc_scan()
    )

def schedule_scans():
    """Background thread to schedule scans"""
    while True:
        try:
            now = datetime.now()
            current_minute = now.minute
            
            # Determine next scan time (at :25 and :55)
            if current_minute < 25:
                target_minute = 25
            elif current_minute < 55:
                target_minute = 55
            else:
                target_minute = 25
                now = now.replace(hour=now.hour + 1)
            
            next_scan_time = now.replace(minute=target_minute, second=0, microsecond=0)
            
            if next_scan_time <= datetime.now():
                next_scan_time = next_scan_time.replace(hour=next_scan_time.hour + 1)
            
            # Update next scan times
            scan_cache["bybit"]["next_scan"] = next_scan_time
            scan_cache["mexc"]["next_scan"] = next_scan_time
            
            # Wait until next scan
            time_until_scan = (next_scan_time - datetime.now()).total_seconds()
            
            if time_until_scan > 0:
                time.sleep(min(time_until_scan, 60))
            
            # Perform scans at scheduled time
            if datetime.now() >= next_scan_time:
                print(f"\n{'='*60}")
                print(f"📅 Scheduled scan starting at {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(perform_all_scans())
                loop.close()
            
        except Exception as e:
            print(f"Scheduler error: {e}")
            time.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    print("🚀 Starting Crypto Scanner API...")
    print(f"📊 MEXC Scanner Criteria: ONE side >= {mexc_scanner.min_wick_ratio}x body size")
    print(f"🎯 Scanning top {mexc_scanner.top_volume_limit} MEXC futures pairs by volume")
    print(f"🔴 Top wicks: Only on RED candles (bearish rejection)")
    print(f"🟢 Bottom wicks: Only on GREEN candles (bullish bounce)")
    print(f"🚫 Both wicks significant: FILTERED OUT (indecision/doji)")
    
    # Initialize next scan time
    now = datetime.now()
    current_minute = now.minute
    
    if current_minute < 25:
        target_minute = 25
    elif current_minute < 55:
        target_minute = 55
    else:
        target_minute = 25
        now = now.replace(hour=now.hour + 1)
    
    next_scan = now.replace(minute=target_minute, second=0, microsecond=0)
    
    scan_cache["bybit"]["next_scan"] = next_scan
    scan_cache["mexc"]["next_scan"] = next_scan
    
    print(f"📅 Next scheduled scan: {next_scan.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Start background thread
    thread = threading.Thread(target=schedule_scans, daemon=True)
    thread.start()
    
    # Perform initial scans immediately
    print("🔄 Performing initial scans...")
    await perform_all_scans()

@app.get("/")
async def root():
    return {
        "message": "Crypto Scanner API",
        "scanners": [
            "Bybit Momentum Scanner (2-candle pattern)",
            "MEXC Wick Scanner (Wick >= 2x body)"
        ],
        "mexc_criteria": {
            "min_wick_ratio": mexc_scanner.min_wick_ratio,
            "description": f"One side (upper/lower) must be >= {mexc_scanner.min_wick_ratio}x body size",
            "scans_top_volume": mexc_scanner.top_volume_limit,
            "filter_indecision": True
        },
        "status": {
            "bybit": scan_cache["bybit"]["status"],
            "mexc": scan_cache["mexc"]["status"]
        },
        "docs": "/docs"
    }

@app.get("/api/scan/bybit")
async def get_bybit_results(force_scan: bool = False):
    """Get Bybit scanner results"""
    if force_scan:
        asyncio.create_task(perform_bybit_scan())
        return {"message": "Bybit scan triggered", "status": "scanning"}
    
    if scan_cache["bybit"]["results"] is None:
        raise HTTPException(status_code=404, detail="No scan results available yet")
    
    if "error" in scan_cache["bybit"]["results"]:
        raise HTTPException(status_code=500, detail=scan_cache["bybit"]["results"]["error"])
    
    return scan_cache["bybit"]["results"]

@app.get("/api/scan/mexc")
async def get_mexc_results(force_scan: bool = False):
    """Get MEXC wick scanner results"""
    if force_scan:
        asyncio.create_task(perform_mexc_scan())
        return {"message": "MEXC scan triggered", "status": "scanning"}
    
    if scan_cache["mexc"]["results"] is None:
        raise HTTPException(status_code=404, detail="No scan results available yet")
    
    if "error" in scan_cache["mexc"]["results"]:
        raise HTTPException(status_code=500, detail=scan_cache["mexc"]["results"]["error"])
    
    return scan_cache["mexc"]["results"]

@app.get("/api/scan/all")
async def get_all_results():
    """Get results from both scanners"""
    return {
        "bybit": scan_cache["bybit"]["results"],
        "mexc": scan_cache["mexc"]["results"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """Get scanner status"""
    return {
        "bybit": {
            "status": scan_cache["bybit"]["status"],
            "last_scan": scan_cache["bybit"]["last_scan"].isoformat() if scan_cache["bybit"]["last_scan"] else None,
            "next_scan": scan_cache["bybit"]["next_scan"].isoformat() if scan_cache["bybit"]["next_scan"] else None
        },
        "mexc": {
            "status": scan_cache["mexc"]["status"],
            "last_scan": scan_cache["mexc"]["last_scan"].isoformat() if scan_cache["mexc"]["last_scan"] else None,
            "next_scan": scan_cache["mexc"]["next_scan"].isoformat() if scan_cache["mexc"]["next_scan"] else None,
            "criteria": {
                "min_wick_ratio": mexc_scanner.min_wick_ratio,
                "description": f"Wick must be >= {mexc_scanner.min_wick_ratio}x body size",
                "top_volume_limit": mexc_scanner.top_volume_limit,
                "filters": {
                    "top_wick": "Only on RED candles (bearish rejection)",
                    "bottom_wick": "Only on GREEN candles (bullish bounce)",
                    "indecision": "BOTH sides significant -> FILTERED OUT"
                }
            }
        }
    }

@app.post("/api/scan/bybit/manual")
async def manual_bybit_scan():
    """Trigger manual Bybit scan"""
    asyncio.create_task(perform_bybit_scan())
    return {"message": "Manual Bybit scan triggered", "status": "scanning"}

@app.post("/api/scan/mexc/manual")
async def manual_mexc_scan():
    """Trigger manual MEXC scan"""
    asyncio.create_task(perform_mexc_scan())
    return {
        "message": "Manual MEXC scan triggered",
        "status": "scanning",
        "criteria": f"Wick >= {mexc_scanner.min_wick_ratio}x body size"
    }

@app.get("/api/mexc/criteria")
async def get_mexc_criteria():
    """Get MEXC scanner criteria"""
    return {
        "min_wick_ratio": mexc_scanner.min_wick_ratio,
        "description": f"ONE side (upper OR lower) must be >= {mexc_scanner.min_wick_ratio}x body size",
        "timeframe": mexc_scanner.timeframe,
        "top_volume_limit": mexc_scanner.top_volume_limit,
        "filters": {
            "dominant_wick": f"Upper OR lower wick >= {mexc_scanner.min_wick_ratio}x body",
            "indecision_filter": "BOTH upper AND lower wick >= body -> FILTERED OUT",
            "color_filter": "Top wicks on RED candles | Bottom wicks on GREEN candles"
        },
        "pattern_interpretation": {
            "top_wick": "Large upper wick on red candle = strong selling pressure at highs. Price rejected during bearish move.",
            "bottom_wick": "Large lower wick on green candle = strong buying pressure at lows. Price bounced during bullish move."
        },
        "volume_filter": f"Top {mexc_scanner.top_volume_limit} pairs by 24h volume"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scanners": {
            "bybit": scan_cache["bybit"]["status"],
            "mexc": scan_cache["mexc"]["status"]
        },
        "mexc_criteria": {
            "active": True,
            "min_wick_ratio": mexc_scanner.min_wick_ratio,
            "top_volume_limit": mexc_scanner.top_volume_limit,
            "single_sided_only": True,
            "filter_indecision": True
        }
    }