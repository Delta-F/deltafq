"""
Connection management for live trading.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..core.base import BaseComponent
from ..core.exceptions import TradingError


class ConnectionManager(BaseComponent):
    """Manage connections to trading systems."""
    
    def __init__(self, **kwargs):
        """Initialize connection manager."""
        super().__init__(**kwargs)
        self.connections = {}
        self.connection_configs = {}
        self.health_check_interval = 60  # seconds
        self.last_health_check = {}
    
    def initialize(self) -> bool:
        """Initialize connection manager."""
        self.logger.info("Initializing connection manager")
        return True
    
    def add_connection(self, name: str, connection_type: str, config: Dict[str, Any]) -> bool:
        """Add a connection configuration."""
        try:
            self.connection_configs[name] = {
                'type': connection_type,
                'config': config,
                'created_at': datetime.now(),
                'last_used': None,
                'status': 'disconnected'
            }
            
            self.logger.info(f"Added connection: {name} ({connection_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add connection: {str(e)}")
            return False
    
    def connect(self, name: str) -> bool:
        """Establish connection."""
        try:
            if name not in self.connection_configs:
                raise TradingError(f"Connection {name} not found")
            
            config = self.connection_configs[name]
            connection_type = config['type']
            
            # Create connection based on type
            if connection_type == 'broker':
                connection = self._create_broker_connection(config['config'])
            elif connection == 'data_feed':
                connection = self._create_data_feed_connection(config['config'])
            else:
                raise TradingError(f"Unknown connection type: {connection_type}")
            
            # Test connection
            if self._test_connection(connection):
                self.connections[name] = connection
                self.connection_configs[name]['status'] = 'connected'
                self.connection_configs[name]['last_used'] = datetime.now()
                self.last_health_check[name] = datetime.now()
                
                self.logger.info(f"Connected: {name}")
                return True
            else:
                self.logger.error(f"Connection test failed: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect {name}: {str(e)}")
            return False
    
    def disconnect(self, name: str) -> bool:
        """Disconnect from service."""
        try:
            if name in self.connections:
                # Close connection
                connection = self.connections[name]
                if hasattr(connection, 'close'):
                    connection.close()
                
                del self.connections[name]
                self.connection_configs[name]['status'] = 'disconnected'
                
                self.logger.info(f"Disconnected: {name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect {name}: {str(e)}")
            return False
    
    def get_connection(self, name: str):
        """Get connection object."""
        return self.connections.get(name)
    
    def is_connected(self, name: str) -> bool:
        """Check if connection is active."""
        return name in self.connections and self.connection_configs.get(name, {}).get('status') == 'connected'
    
    def health_check(self, name: str) -> bool:
        """Perform health check on connection."""
        try:
            if name not in self.connections:
                return False
            
            connection = self.connections[name]
            
            # Perform health check based on connection type
            if hasattr(connection, 'ping'):
                result = connection.ping()
            elif hasattr(connection, 'is_connected'):
                result = connection.is_connected()
            else:
                # Default health check
                result = True
            
            # Update last health check time
            self.last_health_check[name] = datetime.now()
            
            if not result:
                self.logger.warning(f"Health check failed: {name}")
                self.connection_configs[name]['status'] = 'unhealthy'
            else:
                self.connection_configs[name]['status'] = 'connected'
            
            return result
            
        except Exception as e:
            self.logger.error(f"Health check error for {name}: {str(e)}")
            self.connection_configs[name]['status'] = 'error'
            return False
    
    def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all connections."""
        results = {}
        
        for name in self.connections:
            results[name] = self.health_check(name)
        
        return results
    
    def auto_reconnect(self, name: str, max_attempts: int = 3) -> bool:
        """Attempt to automatically reconnect."""
        try:
            if name not in self.connection_configs:
                return False
            
            for attempt in range(max_attempts):
                self.logger.info(f"Reconnection attempt {attempt + 1} for {name}")
                
                if self.connect(name):
                    self.logger.info(f"Successfully reconnected: {name}")
                    return True
                
                # Wait before next attempt
                import time
                time.sleep(5)
            
            self.logger.error(f"Failed to reconnect {name} after {max_attempts} attempts")
            return False
            
        except Exception as e:
            self.logger.error(f"Auto-reconnect failed for {name}: {str(e)}")
            return False
    
    def _create_broker_connection(self, config: Dict[str, Any]):
        """Create broker connection."""
        # Placeholder for broker connection creation
        return MockConnection('broker', config)
    
    def _create_data_feed_connection(self, config: Dict[str, Any]):
        """Create data feed connection."""
        # Placeholder for data feed connection creation
        return MockConnection('data_feed', config)
    
    def _test_connection(self, connection) -> bool:
        """Test connection."""
        try:
            # Simple connection test
            if hasattr(connection, 'test'):
                return connection.test()
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all connections."""
        return {
            'total_connections': len(self.connection_configs),
            'active_connections': len(self.connections),
            'connections': {
                name: {
                    'type': config['type'],
                    'status': config['status'],
                    'last_used': config['last_used'],
                    'last_health_check': self.last_health_check.get(name)
                }
                for name, config in self.connection_configs.items()
            }
        }


class MockConnection:
    """Mock connection for testing."""
    
    def __init__(self, connection_type: str, config: Dict[str, Any]):
        self.connection_type = connection_type
        self.config = config
        self.connected = True
    
    def test(self) -> bool:
        """Test connection."""
        return True
    
    def ping(self) -> bool:
        """Ping connection."""
        return True
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected
    
    def close(self):
        """Close connection."""
        self.connected = False
