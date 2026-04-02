import asyncio
from scanner import CryptoScanner

async def test():
    scanner = CryptoScanner()
    print("Testing scanner...")
    
    # Test getting top gainers/losers
    gainers, losers = scanner.get_top_gainers_losers(5)
    print(f"\nTop 5 Gainers:")
    for g in gainers:
        print(f"  {g['symbol']}: {g['change_pct']:.2f}%")
    
    print(f"\nTop 5 Losers:")
    for l in losers:
        print(f"  {l['symbol']}: {l['change_pct']:.2f}%")
    
    # Test full scan
    print("\nRunning full scan...")
    results = await scanner.full_scan(10)
    print(f"Found {len(results['gainers'])} gainer patterns")
    print(f"Found {len(results['losers'])} loser patterns")
    
    for g in results['gainers'][:3]:
        print(f"  {g['symbol']}: {g['pattern']} (+{g['change_pct']:.2f}%)")

if __name__ == "__main__":
    asyncio.run(test())