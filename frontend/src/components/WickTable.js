// src/components/WickTable.js
import React, { useState } from 'react';
import { Button, Collapse } from 'react-bootstrap';
import { FaInfoCircle, FaWrench, FaArrowUp, FaArrowDown } from 'react-icons/fa';

const WickTable = ({ data, title, wickType }) => {
  const [showDetails, setShowDetails] = useState({});

  const toggleDetails = (symbol) => {
    setShowDetails(prev => ({ ...prev, [symbol]: !prev[symbol] }));
  };

  const formatNumber = (num) => {
    if (!num && num !== 0) return 'N/A';
    if (num > 1000000) return `$${(num / 1000000).toFixed(2)}M`;
    if (num > 1000) return `$${(num / 1000).toFixed(2)}K`;
    return `$${num.toFixed(4)}`;
  };

  if (!data || data.length === 0) {
    return (
      <div className="table-wrapper">
        <div className="text-center py-5">
          <FaWrench size={48} style={{ color: '#6A9AC4' }} />
          <p className="mt-3" style={{ color: '#6A9AC4' }}>No {title.toLowerCase()} detected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="table-modern">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Pattern</th>
            <th>Wick/Body Ratio</th>  
            <th>Current Price</th>
            <th>Wick Size</th>
            <th>Body Size</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <React.Fragment key={idx}>
              <tr>
                <td className="fw-bold">{item.symbol}</td>
                <td>
                  <span className={`badge-modern ${wickType === 'bottom' ? 'badge-success' : 'badge-danger'}`}>
                    {wickType === 'bottom' ? <FaArrowUp className="me-1" /> : <FaArrowDown className="me-1" />}
                    {wickType === 'bottom' ? 'Bottom Wick' : 'Top Wick'}
                  </span>
                </td>
            
                <td className="fw-bold">
                  <span className={`strength-badge ${
                    item.pattern_strength >= 5 ? 'extreme' : 
                    item.pattern_strength >= 3 ? 'strong' : 
                    'normal'
                  }`}>
                    {item.wick_ratio || item.pattern_strength}x
                  </span>
                </td>
                <td>{formatNumber(item.current_price)}</td>
                <td>{formatNumber(item.wick_size)}</td>
                <td>{formatNumber(item.body_size)}</td>
                <td>
                  <Button
                    variant="link"
                    size="sm"
                    onClick={() => toggleDetails(item.symbol)}
                    style={{ color: '#E84545' }}
                  >
                    <FaInfoCircle />
                  </Button>
                </td>
              </tr>
              <tr>
                <td colSpan="7" className="p-0">
                  <Collapse in={showDetails[item.symbol]}>
                    <div className="p-3" style={{ background: 'rgba(7, 20, 40, 0.7)', color: '#6A9AC4' }}>
                      <small>
                        <strong>Pattern Details:</strong> {wickType === 'bottom' ? 'Bottom wick on green candle - Bullish bounce' : 'Top wick on red candle - Bearish rejection'}<br />
                        <strong>Pattern Strength:</strong> {item.pattern_strength}x body size<br />
                        <strong>Wick Percentage:</strong> {item.wick_percentage}% of total candle<br />
                        <strong>Candle:</strong> Open: ${item.candle_details?.open?.toFixed(4)} | High: ${item.candle_details?.high?.toFixed(4)} | Low: ${item.candle_details?.low?.toFixed(4)} | Close: ${item.candle_details?.close?.toFixed(4)}<br />
                        <strong>24h Change:</strong> {item.change_24h ? `${item.change_24h > 0 ? '+' : ''}${item.change_24h.toFixed(2)}%` : 'N/A'}<br />
                        <strong>Interpretation:</strong> {wickType === 'bottom' 
                          ? 'Strong buying pressure at lows. Price bounced during bullish move. Potential support level formed.'
                          : 'Strong selling pressure at highs. Price rejected during bearish move. Potential resistance level formed.'}
                      </small>
                    </div>
                  </Collapse>
                </td>
              </tr>
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default WickTable;