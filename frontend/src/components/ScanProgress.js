import React from 'react';
import { FaSync } from 'react-icons/fa';

const ScanProgress = ({ progress }) => {
  return (
    <div className="scan-progress-container mb-4">
      <div className="d-flex justify-content-between align-items-center mb-2">
        <div className="d-flex align-items-center gap-2">
          <FaSync className="fa-spin" style={{ color: '#E84545' }} />
          <strong>Scanning in progress...</strong>
        </div>
        <span className="fw-bold">{Math.round(progress)}%</span>
      </div>
      <div className="scan-progress-bar">
        <div 
          className="scan-progress-fill" 
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="mt-2">
        <small className="text-muted">
          Fetching data from exchange API. This may take 10-15 seconds...
        </small>
      </div>
    </div>
  );
};

export default ScanProgress;