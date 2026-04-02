import React from 'react';
import { FaClock, FaSync, FaCheckCircle, FaExclamationTriangle, FaSpinner } from 'react-icons/fa';

const StatusCard = ({ status, lastScan, nextScan, scannerName, isLoading, isScanning }) => {
  const formatTime = (isoString) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  const getStatusBadge = () => {
    if (isScanning) {
      return <span className="status-badge status-scanning"><FaSpinner className="fa-spin me-1" /> Scanning...</span>;
    }
    
    switch(status) {
      case 'scanning':
        return <span className="status-badge status-scanning"><FaSync className="fa-spin me-1" /> Scanning...</span>;
      case 'completed':
        return <span className="status-badge status-active"><FaCheckCircle className="me-1" /> Active</span>;
      case 'error':
        return <span className="status-badge status-error"><FaExclamationTriangle className="me-1" /> Error</span>;
      default:
        return <span className="status-badge">{status || 'Idle'}</span>;
    }
  };

  return (
    <div className="status-card fade-in-up">
      <div className="status-grid">
        <div className="status-item">
          <div className="status-label">Scanner Status</div>
          <div className="status-value">
            {getStatusBadge()}
          </div>
        </div>
        <div className="status-item">
          <div className="status-label">Last Scan</div>
          <div className="status-value">
            <FaClock className="me-1" />
            {isLoading ? 'Loading...' : formatTime(lastScan)}
          </div>
        </div>
        <div className="status-item">
          <div className="status-label">Next Scheduled Scan</div>
          <div className="status-value">
            <FaClock className="me-1" />
            {isLoading ? 'Loading...' : formatTime(nextScan)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusCard;