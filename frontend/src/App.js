import React, { useState, useEffect } from 'react';
import { Container, Alert } from 'react-bootstrap';
import { FaChartLine, FaWrench } from 'react-icons/fa';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

import StatusCard from './components/StatusCard';
import ScanControls from './components/ScanControls';
import SymbolTable from './components/SymbolTable';
import WickTable from './components/WickTable';
import CriteriaPanel from './components/CriteriaPanel';
import ScanProgress from './components/ScanProgress';
import { scannerAPI } from './services/api';

function App() {
  const [bybitData, setBybitData] = useState(null);
  const [mexcData, setMexcData] = useState(null);
  const [bybitStatus, setBybitStatus] = useState({});
  const [mexcStatus, setMexcStatus] = useState({});
  
  // Separate loading states for each scanner
  const [bybitLoading, setBybitLoading] = useState(true);
  const [mexcLoading, setMexcLoading] = useState(true);
  const [scanningBybit, setScanningBybit] = useState(false);
  const [scanningMexc, setScanningMexc] = useState(false);
  
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activeScanner, setActiveScanner] = useState('bybit');
  const [scanProgress, setScanProgress] = useState(0);

  const fetchBybit = async () => {
    try {
      const [bybitResponse, statusResponse] = await Promise.all([
        scannerAPI.getScanResults('bybit'),
        scannerAPI.getStatus()
      ]);
      setBybitData(bybitResponse);
      setBybitStatus(statusResponse.bybit);
      setMexcStatus(statusResponse.mexc);
    } catch (err) {
      console.error('Bybit fetch error:', err);
    } finally {
      setBybitLoading(false);
    }
  };

  const fetchMexc = async () => {
    try {
      const response = await scannerAPI.getScanResults('mexc');
      setMexcData(response);
    } catch (err) {
      console.error('MEXC fetch error:', err);
    } finally {
      setMexcLoading(false);
    }
  };

  const fetchData = () => {
    fetchBybit();
    fetchMexc();
  };

  const handleManualScan = async (scanner) => {
    try {
      setError(null);
      
      // Set scanning state for specific scanner
      if (scanner === 'bybit') {
        setScanningBybit(true);
        setBybitLoading(true);
      } else {
        setScanningMexc(true);
        setMexcLoading(true);
      }
      
      // Animate progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 95) {
          progress = 95;
        }
        setScanProgress(progress);
      }, 500);
      
      // Trigger the scan
      await scannerAPI.triggerManualScan(scanner);
      
      // Wait for scan to complete (15 seconds for API to process)
      setTimeout(async () => {
        clearInterval(interval);
        setScanProgress(100);
        
          // Fetch updated data for the triggered scanner only
        if (scanner === 'bybit') await fetchBybit();
        else await fetchMexc();
        
        // Reset scanning states
        if (scanner === 'bybit') {
          setScanningBybit(false);
          setBybitLoading(false);
        } else {
          setScanningMexc(false);
          setMexcLoading(false);
        }
        
        // Reset progress
        setTimeout(() => setScanProgress(0), 500);
      }, 15000);
      
    } catch (err) {
      setError(err.message);
      if (scanner === 'bybit') {
        setScanningBybit(false);
        setBybitLoading(false);
      } else {
        setScanningMexc(false);
        setMexcLoading(false);
      }
    }
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(prev => !prev);
  };

  useEffect(() => {
    fetchData();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchData();
      }, 30000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const bybitCriteria = {
    name: "Bybit Momentum Scanner",
    description: "2-candle momentum pattern detection on Bybit futures",
    timeframe: "30 minutes",
    filters: [
      { icon: "🟢", text: "Bullish Pattern: 2 green candles with both wicks", color: "success" },
      { icon: "🔴", text: "Bearish Pattern: 2 red candles with both wicks", color: "danger" },
      { icon: "📏", text: "Wick touch: Current candle wick touches previous candle body", color: "info" },
      { icon: "🎯", text: "Open reached: Wick reaches previous candle open", color: "info" }
    ],
    rules: [
      "Both candles must have upper AND lower wicks",
      "Candles must be same direction (both green or both red)",
      "Current candle wick must touch previous candle body",
      "Wick must reach previous open without exceeding extremes"
    ],
    markets: "Top 25 Gainers & Top 25 Losers (USDT pairs)",
    scanSchedule: "Every 30 minutes at :25 and :55"
  };

  const mexcCriteria = {
    name: "MEXC Wick Scanner",
    description: "Single candle wick pattern detection on zero-fee futures",
    timeframe: "30 minutes",
    filters: [
      { icon: "🟢", text: "Bottom Wick: Only on GREEN candles (bullish bounce)", color: "success" },
      { icon: "🔴", text: "Top Wick: Only on RED candles (bearish rejection)", color: "danger" },
      { icon: "🚫", text: "Both wicks: FILTERED OUT for cleaner signals", color: "warning" },
      { icon: "📏", text: "Wick size ≥ Body size (1.0x or higher)", color: "info" }
    ],
    rules: [
      "Current candle must have significant wick (≥ body size)",
      "Bottom wicks only appear on green candles",
      "Top wicks only appear on red candles",
      "Candles with both wicks are filtered out",
      "Previous candle must match current candle color"
    ],
    markets: "Zero-fee USDT-M perpetual futures (25+ pairs)",
    scanSchedule: "Every 30 minutes at :25 and :55"
  };

  const currentData = activeScanner === 'bybit' ? bybitData : mexcData;
  const currentStatus = activeScanner === 'bybit' ? bybitStatus : mexcStatus;
  const currentCriteria = activeScanner === 'bybit' ? bybitCriteria : mexcCriteria;
  const currentLoading = activeScanner === 'bybit' ? bybitLoading : mexcLoading;
  const currentScanning = activeScanner === 'bybit' ? scanningBybit : scanningMexc;

  if (bybitLoading && mexcLoading && !bybitData && !mexcData) {
    return (
      <div className="app-container">
        <Container className="loading-container">
          <div className="spinner-modern"></div>
          <div className="loading-text">Loading scanner data...</div>
        </Container>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Container fluid className="main-container">
        {/* Header */}
        <div className="app-header fade-in-up">
          <h1 className="app-title">
            Crypto Scanner App
          </h1>
          <p className="app-subtitle">
            Dual scanner system | Bybit Wick Failing + MEXC Long Wick Patterns
          </p>
        </div>

        {/* Scanner Selection Cards */}
        <div className="scanner-grid fade-in-up">
          <div 
            className={`scanner-card ${activeScanner === 'bybit' ? 'scanner-card-active' : ''}`}
            onClick={() => setActiveScanner('bybit')}
          >
            <div className="scanner-card-content">
              <div className="scanner-icon">
                <FaChartLine style={{ color: '#4A70A9' }} />
              </div>
              <h3 className="scanner-title">Bybit Momentum</h3>
              <p className="scanner-description">2-candle pattern scanner with wick confirmation</p>
              {activeScanner === 'bybit' && <div className="scanner-badge">Active</div>}
              {scanningBybit && <div className="scanner-scanning-badge">Scanning...</div>}
              <div className="scanner-stats">
                <div className="stat-item">
                  <div className="stat-label">Patterns Found</div>
                  <div className="stat-value">
                    {bybitLoading ? '...' : (bybitData?.gainers?.length || 0) + (bybitData?.losers?.length || 0)}
                  </div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">24h Change</div>
                  <div className="stat-value">
                    {bybitLoading ? '...' : (bybitData?.gainers?.[0]?.change_pct?.toFixed(1) || '0')}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div 
            className={`scanner-card ${activeScanner === 'mexc' ? 'scanner-card-active' : ''}`}
            onClick={() => setActiveScanner('mexc')}
          >
            <div className="scanner-card-content">
              <div className="scanner-icon">
                <FaWrench style={{ color: '#4A70A9' }} />
              </div>
              <h3 className="scanner-title">MEXC Wick Scanner</h3>
              <p className="scanner-description">Zero-fee futures | Wick pattern detection</p>
              {activeScanner === 'mexc' && <div className="scanner-badge">Active</div>}
              {scanningMexc && <div className="scanner-scanning-badge">Scanning...</div>}
              <div className="scanner-stats">
                <div className="stat-item">
                  <div className="stat-label">Patterns Found</div>
                  <div className="stat-value">
                    {mexcLoading ? '...' : (mexcData?.total_patterns_found || 0)}
                  </div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Scanned</div>
                  <div className="stat-value">
                    {mexcLoading ? '...' : (mexcData?.total_scanned || 0)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Criteria Panel */}
        <CriteriaPanel criteria={currentCriteria} />

        {/* Status and Controls */}
        <StatusCard 
          status={currentStatus.status}
          lastScan={currentStatus.last_scan}
          nextScan={currentStatus.next_scan}
          scannerName={currentCriteria.name}
          isLoading={currentLoading}
          isScanning={currentScanning}
        />
        
        <ScanControls
          onManualScan={() => handleManualScan(activeScanner)}
          onAutoRefreshToggle={toggleAutoRefresh}
          autoRefresh={autoRefresh}
          isScanning={currentScanning}
          error={error}
          scannerName={currentCriteria.name}
        />
        
        {/* Scan Progress */}
        {currentScanning && scanProgress > 0 && (
          <ScanProgress progress={scanProgress} />
        )}
        
        {/* Results */}
        {!currentLoading && currentData && activeScanner === 'bybit' && (
          <>
            <SymbolTable
              data={currentData.gainers}
              title="Bullish Patterns - Top Gainers"
              variant="success"
              icon={<FaChartLine />}
            />
            <SymbolTable
              data={currentData.losers}
              title="Bearish Patterns - Top Losers"
              variant="danger"
              icon={<FaChartLine />}
            />
          </>
        )}
        
        {!currentLoading && currentData && activeScanner === 'mexc' && (
          <>
            <div className="stats-grid">
              <div className="stat-card-modern">
                <div className="stat-card-icon">📊</div>
                <div className="stat-card-value">{currentData.total_scanned || 0}</div>
                <div className="stat-card-label">Symbols Scanned</div>
              </div>
              <div className="stat-card-modern">
                <div className="stat-card-icon">🎯</div>
                <div className="stat-card-value">{currentData.total_patterns_found || 0}</div>
                <div className="stat-card-label">Patterns Found</div>
              </div>
              <div className="stat-card-modern">
                <div className="stat-card-icon">🟢</div>
                <div className="stat-card-value">{currentData.bottom_wick_patterns?.length || 0}</div>
                <div className="stat-card-label">Bottom Wicks (Bullish)</div>
              </div>
              <div className="stat-card-modern">
                <div className="stat-card-icon">🔴</div>
                <div className="stat-card-value">{currentData.top_wick_patterns?.length || 0}</div>
                <div className="stat-card-label">Top Wicks (Bearish)</div>
              </div>
            </div>
            
            <WickTable
              data={currentData.bottom_wick_patterns}
              title="Bottom Wicks (Bullish - Green Candles)"
              wickType="bottom"
            />
            <WickTable
              data={currentData.top_wick_patterns}
              title="Top Wicks (Bearish - Red Candles)"
              wickType="top"
            />
          </>
        )}
        
        {/* Loading State for Current Scanner */}
        {currentLoading && !currentScanning && (
          <div className="loading-state">
            <div className="spinner-modern"></div>
            <p>Loading {activeScanner === 'bybit' ? 'Bybit' : 'MEXC'} data...</p>
          </div>
        )}
        
        {error && (
          <Alert variant="danger" onClose={() => setError(null)} dismissible className="mt-3">
            <Alert.Heading>Error</Alert.Heading>
            <p>{error}</p>
          </Alert>
        )}
      </Container>
    </div>
  );
}

export default App;