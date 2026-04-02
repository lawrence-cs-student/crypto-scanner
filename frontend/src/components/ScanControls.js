import React from 'react';
import { FaSync, FaBell, FaChartLine, FaSpinner } from 'react-icons/fa';

const ScanControls = ({ 
  onManualScan, 
  onAutoRefreshToggle, 
  autoRefresh, 
  isScanning,
  error,
  scannerName
}) => {
  return (
    <div className="controls-wrapper fade-in-up">
      <div className="d-flex gap-3">
        <button
          className="btn-modern btn-primary"
          onClick={onManualScan}
          disabled={isScanning}
        >
          {isScanning ? (
            <>
              <FaSpinner className="fa-spin" />
              Scanning {scannerName}...
            </>
          ) : (
            <>
              <FaSync />
              Scan {scannerName}
            </>
          )}
        </button>
        
        <button
          className={`btn-modern ${autoRefresh ? 'btn-primary' : 'btn-outline'}`}
          onClick={onAutoRefreshToggle}
          disabled={isScanning}
        >
          <FaBell />
          Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
        </button>
      </div>
      
      <div className="d-flex align-items-center gap-2">
        <FaChartLine style={{ color: '#9DB2BF' }} />
        <small style={{ color: '#6A9AC4' }}>
          Scans automatically at :25 and :55 every hour
        </small>
      </div>
    </div>
  );
};

export default ScanControls;