"""
Trading monitoring and alerts for live trading.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from ..core.base import BaseComponent


class TradingMonitor(BaseComponent):
    """Monitor trading activities and generate alerts."""
    
    def __init__(self, **kwargs):
        """Initialize trading monitor."""
        super().__init__(**kwargs)
        self.alerts = []
        self.monitoring_rules = {}
        self.alert_callbacks = []
        self.monitoring_active = False
        self.logger.info("Initializing trading monitor")
    
    def add_monitoring_rule(self, rule_name: str, rule_func: Callable, 
                           threshold: float = None, **kwargs) -> bool:
        """Add a monitoring rule."""
        try:
            self.monitoring_rules[rule_name] = {
                'function': rule_func,
                'threshold': threshold,
                'parameters': kwargs,
                'active': True,
                'last_triggered': None
            }
            
            self.logger.info(f"Added monitoring rule: {rule_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add monitoring rule: {str(e)}")
            return False
    
    def add_alert_callback(self, callback: Callable) -> bool:
        """Add alert callback function."""
        self.alert_callbacks.append(callback)
        return True
    
    def start_monitoring(self) -> bool:
        """Start monitoring."""
        try:
            self.monitoring_active = True
            self.logger.info("Trading monitoring started")
            
            # In a real implementation, this would start a monitoring loop
            # For now, we'll provide the framework
            
            return True
            
        except Exception as e:
            self.monitoring_active = False
            self.logger.error(f"Failed to start monitoring: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop monitoring."""
        try:
            self.monitoring_active = False
            self.logger.info("Trading monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {str(e)}")
            return False
    
    def check_rule(self, rule_name: str, data: Dict[str, Any]) -> bool:
        """Check a specific monitoring rule."""
        if rule_name not in self.monitoring_rules:
            return False
        
        rule = self.monitoring_rules[rule_name]
        if not rule['active']:
            return False
        
        try:
            # Execute the rule function
            result = rule['function'](data, rule['threshold'], **rule['parameters'])
            
            # Check if rule was triggered
            if result:
                self._trigger_alert(rule_name, data, result)
                rule['last_triggered'] = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Rule check failed for {rule_name}: {str(e)}")
            return False
    
    def check_all_rules(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """Check all active monitoring rules."""
        results = {}
        
        for rule_name in self.monitoring_rules:
            if self.monitoring_rules[rule_name]['active']:
                results[rule_name] = self.check_rule(rule_name, data)
        
        return results
    
    def _trigger_alert(self, rule_name: str, data: Dict[str, Any], result: Any):
        """Trigger an alert."""
        alert = {
            'rule_name': rule_name,
            'timestamp': datetime.now(),
            'data': data,
            'result': result,
            'severity': self._determine_severity(rule_name, result)
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"Alert triggered: {rule_name}")
        
        # Notify alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {str(e)}")
    
    def _determine_severity(self, rule_name: str, result: Any) -> str:
        """Determine alert severity."""
        # Simple severity determination based on rule name
        if 'loss' in rule_name.lower() or 'drawdown' in rule_name.lower():
            return 'HIGH'
        elif 'position' in rule_name.lower() or 'concentration' in rule_name.lower():
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert['timestamp'] > cutoff_time]
    
    def clear_alerts(self, hours: int = None) -> int:
        """Clear old alerts."""
        if hours is None:
            # Clear all alerts
            count = len(self.alerts)
            self.alerts.clear()
        else:
            # Clear alerts older than specified hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            original_count = len(self.alerts)
            self.alerts = [alert for alert in self.alerts if alert['timestamp'] > cutoff_time]
            count = original_count - len(self.alerts)
        
        self.logger.info(f"Cleared {count} alerts")
        return count
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a monitoring rule."""
        if rule_name in self.monitoring_rules:
            self.monitoring_rules[rule_name]['active'] = True
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a monitoring rule."""
        if rule_name in self.monitoring_rules:
            self.monitoring_rules[rule_name]['active'] = False
            return True
        return False
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring status."""
        return {
            'monitoring_active': self.monitoring_active,
            'total_rules': len(self.monitoring_rules),
            'active_rules': sum(1 for rule in self.monitoring_rules.values() if rule['active']),
            'total_alerts': len(self.alerts),
            'recent_alerts': len(self.get_alerts(hours=1)),
            'rules': {name: {
                'active': rule['active'],
                'last_triggered': rule['last_triggered']
            } for name, rule in self.monitoring_rules.items()}
        }

