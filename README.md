# Full Stack Trading Application

A comprehensive trading platform consisting of a PyQt5 desktop client and Flask-based API server with real-time data synchronization and PostgreSQL database integration.

## System Architecture

### Client Application
- PyQt5-based desktop trading interface
- Real-time market data via Databento API
- Asynchronous API communication
- Automated trading features

### Server Application
- Flask REST API
- PostgreSQL database
- WebSocket support for real-time updates
- SQLAlchemy ORM
- Flask-Migrate for database migrations

## Features

### Trading Features
- Real-time market data streaming
- Multiple take-profit levels with automated execution
- Dynamic stop-loss management
- Support for micro and mini futures contracts
- Historical data replay mode
- OHLCV-1m data archiving
- ATR-based stop loss calculations
- Trade timer with automated actions

### Server Features
- Real-time trade synchronization
- Persistent storage of orders and take-profit levels
- WebSocket integration for price updates
- Database migrations support
- Comprehensive error handling and logging
- Transaction management
- Bulk update support

## System Requirements

### Client Requirements
```
Python 3.x
PyQt5
aiohttp
requests
databento
pandas
pytz
```

### Server Requirements
```
Python 3.x
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-SocketIO
PostgreSQL
psycopg2-binary
```

## Installation

### Client Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd trading-app/client
```

2. Install client dependencies:
```bash
pip install -r requirements.txt
```

### Server Setup
1. Navigate to server directory:
```bash
cd trading-app/server
```

2. Install server dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
```bash
createdb tradingdb
```

4. Configure database:
```bash
export DATABASE_URL="postgresql://username:password@localhost/tradingdb"
```

5. Initialize and run migrations:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Configuration

### Client Configuration
Create `settings.json`:
```json
{
    "api_url": "http://api.your-domain.com",
    "databento_key": "your-databento-key",
    "archive_key": "your-archive-key",
    "atr_period": 14,
    "atr_lookback": 390
}
```

### Server Configuration
Create `config.py`:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/tradingdb'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'your-secret-key'
```

## API Endpoints

### Orders
```
POST /api/place_order
- Place new order or update existing
- Supports bulk updates

GET /api/get_active_orders
- Retrieve all active orders and TP levels

POST /api/clear_trade/{ticker}
- Clear specific trade and associated TP levels
```

### Take Profit Levels
```
POST /api/save_tp_levels/{symbol}
- Save or update multiple TP levels

GET /api/get_tp_levels/{symbol}
- Retrieve TP levels for specific symbol

PUT /api/save_tp_level/{symbol}/{index}
- Update individual TP level
```

### WebSocket Events
```
'connect': Client connection event
'price_update': Real-time price updates
'price_changed': Price change notifications
```

## Database Schema

### Orders Table
```sql
CREATE TABLE order (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price FLOAT NOT NULL,
    timestamp INTEGER NOT NULL,
    stop_loss JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Take Profit Table
```sql
CREATE TABLE take_profit (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    quantity INTEGER NOT NULL,
    target FLOAT NOT NULL,
    price FLOAT NOT NULL,
    hit BOOLEAN DEFAULT FALSE
);
```

## Running the Application

### Start the Server
```bash
cd server
flask run
```

### Start the Client
```bash
cd client
python trading_app.py
```

## Development

### Adding New Features
1. Server-side:
   - Add new endpoints in Flask application
   - Update database models if needed
   - Add corresponding WebSocket events
   - Implement error handling and logging

2. Client-side:
   - Add new UI elements in PyQt5
   - Implement API integration in AsyncWorker
   - Add corresponding event handlers
   - Update state management

### Debugging
- Server logs are available in logging output
- Client maintains detailed operation logs
- Database queries can be monitored through SQLAlchemy logging

## Error Handling

### Server-side
- SQLAlchemy error capture
- Transaction rollback on failures
- Detailed error logging
- Proper HTTP status codes

### Client-side
- Network error recovery
- API communication retry mechanism
- Data validation
- Automatic reconnection

## Security Considerations

- API authentication required
- Database password protection
- HTTPS for API communication
- Input validation and sanitization
- Secure credential storage

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## Testing

### Server Tests
```bash
python -m pytest tests/
```

### Client Tests
```bash
python -m pytest tests/
```

## Deployment

### Server Deployment
1. Set up production database
2. Configure WSGI server (e.g., Gunicorn)
3. Set up reverse proxy (e.g., Nginx)
4. Configure SSL certificates
5. Set environment variables

### Client Distribution
1. Package application
2. Configure production API endpoints
3. Set up auto-updates if needed
4. Create installers

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This application requires proper setup of both client and server components, as well as valid API credentials and market data subscriptions to function properly.