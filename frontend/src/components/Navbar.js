import React from 'react';
import { Navbar as BootstrapNavbar, Container } from 'react-bootstrap';
import { FaBitcoin, FaChartLine, FaWrench } from 'react-icons/fa';

const Navbar = () => {
  return (
    <BootstrapNavbar className="navbar-custom" expand="lg">
      <Container>
        <BootstrapNavbar.Brand href="/">
          <FaBitcoin className="me-2" />
          Crypto Scanner Suite
        </BootstrapNavbar.Brand>
        <BootstrapNavbar.Toggle aria-controls="basic-navbar-nav" />
        <BootstrapNavbar.Collapse id="basic-navbar-nav" className="justify-content-end">
          <div className="d-flex gap-3">
            <div className="text-center">
              <FaChartLine className="me-1" style={{ color: '#E84545' }} />
              <small className="text-white-50">Bybit Momentum</small>
            </div>
            <div className="text-center">
              <FaWrench className="me-1" style={{ color: '#E84545' }} />
              <small className="text-white-50">MEXC Wick Patterns</small>
            </div>
          </div>
        </BootstrapNavbar.Collapse>
      </Container>
    </BootstrapNavbar>
  );
};

export default Navbar;