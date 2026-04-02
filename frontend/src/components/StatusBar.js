import React from 'react';
import { Card, Row, Col, Badge } from 'react-bootstrap';
import { FaClock, FaSync, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';

const StatusBar = ({ status, lastScan, nextScan, scannerName }) => {
  const formatTime = (isoString) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  const getStatusBadge = () => {
    switch(status) {
      case 'scanning':
        return <Badge bg="warning" className="ms-2"><FaSync className="fa-spin me-1" /> Scanning...</Badge>;
      case 'completed':
        return <Badge bg="success" className="ms-2"><FaCheckCircle className="me-1" /> Active</Badge>;
      case 'error':
        return <Badge bg="danger" className="ms-2"><FaExclamationTriangle className="me-1" /> Error</Badge>;
      default:
        return <Badge bg="secondary" className="ms-2">{status || 'Idle'}</Badge>;
    }
  };

  return (
    <Card className="status-card mb-4">
      <Card.Body>
        <Row>
          <Col md={4} className="mb-2 mb-md-0">
            <small className="text-muted">{scannerName} Scanner Status</small>
            <div className="d-flex align-items-center">
              <span className="fw-bold">Status:</span>
              {getStatusBadge()}
            </div>
          </Col>
          <Col md={4} className="mb-2 mb-md-0">
            <small className="text-muted">Last Scan</small>
            <div>
              <FaClock className="me-1 text-muted" />
              <span className="fw-bold">{formatTime(lastScan)}</span>
            </div>
          </Col>
          <Col md={4}>
            <small className="text-muted">Next Scheduled Scan</small>
            <div>
              <FaClock className="me-1 text-muted" />
              <span className="fw-bold">{formatTime(nextScan)}</span>
            </div>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};

export default StatusBar;