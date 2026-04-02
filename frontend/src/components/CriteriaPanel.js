import React, { useState } from 'react';
import { FaInfoCircle, FaFilter, FaClock, FaChartLine, FaChevronDown, FaChevronUp } from 'react-icons/fa';

const CriteriaPanel = ({ criteria }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="criteria-panel fade-in-up">
      <div className="criteria-header" onClick={() => setShowDetails(!showDetails)}>
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <FaInfoCircle className="me-2" />
            <strong>Scanner Criteria & Filters</strong>
            <span className="ms-2">- {criteria.name}</span>
          </div>
          {showDetails ? <FaChevronUp /> : <FaChevronDown />}
        </div>
      </div>
      
      <div className="criteria-content">
        <div className="filter-grid">
          {criteria.filters.map((filter, idx) => (
            <div key={idx} className="filter-chip">
              <div className="filter-icon">{filter.icon}</div>
              <div className="filter-text">{filter.text}</div>
            </div>
          ))}
        </div>
        
        {showDetails && (
          <div className="rules-container">
            <div className="rules-title">
              <FaChartLine /> Detailed Rules & Requirements
            </div>
            <ul className="rules-list">
              {criteria.rules.map((rule, idx) => (
                <li key={idx}>{rule}</li>
              ))}
            </ul>
            <div className="mt-3 pt-2">
              <small style={{ color: '#6A9AC4' }}>
                <strong>📊 Market:</strong> {criteria.markets}<br />
                <strong>⏰ Schedule:</strong> {criteria.scanSchedule}
              </small>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CriteriaPanel;