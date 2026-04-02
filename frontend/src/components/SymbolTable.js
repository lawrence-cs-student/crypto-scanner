import React, { useState } from 'react';
import { Button, Collapse } from 'react-bootstrap';
import { FaArrowUp, FaArrowDown, FaInfoCircle, FaChartLine } from 'react-icons/fa';

const SymbolTable = ({ data, title, variant, icon }) => {
  const [showDetails, setShowDetails] = useState({});

  const toggleDetails = (symbol) => {
    setShowDetails(prev => ({ ...prev, [symbol]: !prev[symbol] }));
  };

  const formatNumber = (num) => {
    if (!num && num !== 0) return 'N/A';
    if (num > 1000000) return `$${(num / 1000000).toFixed(2)}M`;
    if (num > 1000) return `$${(num / 1000000).toFixed(2)}M`;
    return `$${num.toFixed(4)}`;
  };

  if (!data || data.length === 0) {
    return (
      <div className="table-wrapper">
        <div className="text-center py-5">
          <FaChartLine size={48} style={{ color: '#6A9AC4' }} />
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
            <th>24h Change</th>
            <th>Last Price</th>
            <th>24h Volume</th>
            <th>24h Range</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <React.Fragment key={idx}>
              <tr>
                <td className="fw-bold">{item.symbol}</td>
                <td>
                  <span className={`badge-modern ${variant === 'success' ? 'badge-success' : 'badge-danger'}`}>
                    {variant === 'success' ? <FaArrowUp className="me-1" /> : <FaArrowDown className="me-1" />}
                    {item.pattern.split(' ').slice(0, 3).join(' ')}
                  </span>
                </td>
                <td className={item.change_pct > 0 ? 'text-success' : 'text-danger'}>
                  {item.change_pct > 0 ? '+' : ''}{item.change_pct.toFixed(2)}%
                </td>
                <td>{formatNumber(item.last_price)}</td>
                <td>{formatNumber(item.volume)}</td>
                <td>
                  <small>{formatNumber(item.low_24h)} - {formatNumber(item.high_24h)}</small>
                </td>
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
                        <strong>Pattern:</strong> {item.pattern}<br />
                        <strong>24h High/Low:</strong> {formatNumber(item.high_24h)} / {formatNumber(item.low_24h)}<br />
                        <strong>Volume:</strong> {formatNumber(item.volume)}
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

export default SymbolTable;