"""
Real-time risk control for live trading.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..core.base import BaseComponent


class LiveRiskControl(BaseComponent):
    """Real-time risk control system."""
    
    def __init__(self, max_position_size: float = 0.1, max_daily_loss: float = 0.05, 
                 max_drawdown: float = 0.15, **kwargs):
        """Initialize risk control."""
        super().__init__(**kwargs)
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.daily_pnl = 0.0
        self.peak_equity = 0.0
        self.risk_limits = {}
        self.alert_callbacks = []
        self.logger.info("Initializing live risk control")
    
    def add_alert_callback(self, callback) -> bool:
        """Add alert callback function."""
        self.alert_callbacks.append(callback)
        return True
    
    def check_position_risk(self, symbol: str, quantity: float, portfolio_value: float, 
                           current_price: float) -> bool:
        """Check if position size is within risk limits."""
        try:
            position_value = abs(quantity) * current_price
            position_ratio = position_value / portfolio_value
            
            # Check maximum position size
            if position_ratio > self.max_position_size:
                self._trigger_alert("POSITION_SIZE_EXCEEDED", {
                    'symbol': symbol,
                    'position_ratio': position_ratio,
                    'max_allowed': self.max_position_size
                })
                return False
            
            # Check symbol-specific limits
            if symbol in self.risk_limits:
                symbol_limit = self.risk_limits[symbol]
                if position_ratio > symbol_limit:
                    self._trigger_alert("SYMBOL_LIMIT_EXCEEDED", {
                        'symbol': symbol,
                        'position_ratio': position_ratio,
                        'symbol_limit': symbol_limit
                    })
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Risk check failed: {str(e)}")
            return False
    
    def check_daily_loss_limit(self, current_equity: float, initial_equity: float) -> bool:
        """Check if daily loss limit is exceeded."""
        try:
            daily_pnl = current_equity - initial_equity
            daily_pnl_ratio = daily_pnl / initial_equity
            
            if daily_pnl_ratio < -self.max_daily_loss:
                self._trigger_alert("DAILY_LOSS_LIMIT_EXCEEDED", {
                    'daily_pnl': daily_pnl,
                    'daily_pnl_ratio': daily_pnl_ratio,
                    'max_daily_loss': self.max_daily_loss
                })
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Daily loss check failed: {str(e)}")
            return False
    
    def check_drawdown_limit(self, current_equity: float) -> bool:
        """Check if maximum drawdown is exceeded."""
        try:
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            
            if self.peak_equity > 0:
                drawdown = (self.peak_equity - current_equity) / self.peak_equity
                
                if drawdown > self.max_drawdown:
                    self._trigger_alert("DRAWDOWN_LIMIT_EXCEEDED", {
                        'current_drawdown': drawdown,
                        'max_drawdown': self.max_drawdown,
                        'peak_equity': self.peak_equity,
                        'current_equity': current_equity
                    })
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Drawdown check failed: {str(e)}")
            return False
    
    def check_concentration_risk(self, positions: Dict[str, float], portfolio_value: float) -> bool:
        """Check portfolio concentration risk."""
        try:
            total_position_value = sum(abs(value) for value in positions.values())
            
            if total_position_value > portfolio_value * 0.95:  # 95% of portfolio
                self._trigger_alert("CONCENTRATION_RISK_HIGH", {
                    'total_position_value': total_position_value,
                    'portfolio_value': portfolio_value,
                    'concentration_ratio': total_position_value / portfolio_value
                })
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Concentration risk check failed: {str(e)}")
            return False
    
    def set_symbol_limit(self, symbol: str, limit: float) -> bool:
        """Set position size limit for specific symbol."""
        try:
            self.risk_limits[symbol] = limit
            self.logger.info(f"Set risk limit for {symbol}: {limit:.2%}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set symbol limit: {str(e)}")
            return False
    
    def comprehensive_risk_check(self, symbol: str, quantity: float, portfolio_value: float, 
                               current_price: float, current_equity: float, 
                               initial_equity: float, positions: Dict[str, float]) -> Dict[str, bool]:
        """Perform comprehensive risk checks."""
        results = {
            'position_risk': self.check_position_risk(symbol, quantity, portfolio_value, current_price),
            'daily_loss': self.check_daily_loss_limit(current_equity, initial_equity),
            'drawdown': self.check_drawdown_limit(current_equity),
            'concentration': self.check_concentration_risk(positions, portfolio_value)
        }
        
        # Overall risk check passes only if all individual checks pass
        results['overall'] = all(results.values())
        
        return results
    
    def _trigger_alert(self, alert_type: str, details: Dict[str, Any]):
        """Trigger risk alert."""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now(),
            'details': details
        }
        
        self.logger.warning(f"Risk alert: {alert_type}")
        
        # Notify alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {str(e)}")
    
    def reset_daily_limits(self):
        """Reset daily risk limits (call at start of trading day)."""
        self.daily_pnl = 0.0
        self.logger.info("Daily risk limits reset")
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status."""
        return {
            'max_position_size': self.max_position_size,
            'max_daily_loss': self.max_daily_loss,
            'max_drawdown': self.max_drawdown,
            'current_daily_pnl': self.daily_pnl,
            'peak_equity': self.peak_equity,
            'symbol_limits': dict(self.risk_limits),
            'active_alerts': len(self.alert_callbacks)
        }

