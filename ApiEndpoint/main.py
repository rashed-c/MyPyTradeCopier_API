from flask import Flask, request, jsonify
from sqlalchemy.dialects.postgresql import JSON
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from sqlalchemy.exc import SQLAlchemyError
import logging
import time


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://tradeapi_user:<pass>@localhost/tradingdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)
migrate = Migrate(app, db)

# Database models
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)




class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)
    stop_loss = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "action": self.action,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "timestamp": self.timestamp,
            "stop_loss": self.stop_loss
        }

class TakeProfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    quantity = db.Column(db.Integer, nullable=False)
    target = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    hit = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "quantity": self.quantity,
            "target": self.target,
            "price": self.price,
            "hit": self.hit
        }



@app.route('/api/place_order', methods=['POST'])
def place_order():
    data = request.json
    logger.debug(f"Received order data: {data}")

    # Check current state of database
    all_orders = Order.query.all()
    logger.debug(f"Current orders in database: {[order.to_dict() for order in all_orders]}")

    all_tp_levels = TakeProfit.query.all()
    logger.debug(f"Current TP levels in database: {[tp.to_dict() for tp in all_tp_levels]}")

    try:
        if 'active_orders' in data:
            # Bulk update format
            for symbol, order_data in data['active_orders'].items():
                process_order(symbol, order_data)

            if 'tp_levels' in data:
                for symbol, tp_levels in data['tp_levels'].items():
                    process_tp_levels(symbol, tp_levels)
        else:
            # Individual order format
            ticker = data.get('ticker')
            symbol = ticker.rstrip('1!')  # Remove '1!' suffix if present
            process_order(symbol, data)

        db.session.commit()
        logger.debug("Database changes committed successfully")
        return jsonify({"success": True, "message": "Orders and TP levels updated successfully"})

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {str(e)}")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500

def process_order(symbol, order_data):
    logger.debug(f"Processing order for symbol: {symbol}")
    logger.debug(f"Order data: {order_data}")

    action = order_data.get('action')
    logger.debug(f"Action: {action}")

    if action == "exit":
        logger.debug(f"Attempting to remove order for symbol: {symbol}")
        removed = Order.query.filter_by(symbol=symbol).delete()
        logger.debug(f"Removed {removed} orders for symbol: {symbol}")

        # Reset 'hit' status for all TP levels of this symbol
        tp_levels = TakeProfit.query.filter_by(symbol=symbol).all()
        for tp in tp_levels:
            tp.hit = False
            logger.debug(f"Reset hit status for TP level of {symbol}")
    else:
        existing_order = Order.query.filter_by(symbol=symbol).first()
        if existing_order:
            logger.debug(f"Updating existing order for {symbol}")
            for key, value in order_data.items():
                if key in ['action', 'quantity', 'entry_price', 'timestamp', 'stop_loss']:
                    setattr(existing_order, key, value)
        else:
            logger.debug(f"Creating new order for {symbol}")
            new_order = Order(
                symbol=symbol,
                action=action,
                quantity=order_data['quantity'],
                entry_price=order_data.get('entry_price') or order_data.get('limitPrice'),
                timestamp=order_data.get('timestamp', int(time.time())),
                stop_loss=order_data.get('stop_loss') or order_data.get('stopLoss')
            )
            db.session.add(new_order)


@app.route('/api/get_active_orders', methods=['GET'])
def get_active_orders():
    try:
        active_orders = {}
        for order in Order.query.all():
            active_orders[order.symbol] = order.to_dict()

        tp_levels = {}
        for tp in TakeProfit.query.all():
            if tp.symbol not in tp_levels:
                tp_levels[tp.symbol] = []
            tp_levels[tp.symbol].append(tp.to_dict())

        return jsonify({
            "success": True,
            "active_orders": active_orders,
            "tp_levels": tp_levels
        })
    except Exception as e:
        logger.error(f"Error fetching active orders: {str(e)}")
        return jsonify({"success": False, "message": f"Error fetching active orders: {str(e)}"}), 500



@app.route('/api/save_tp_levels/<symbol>', methods=['POST'])
def save_tp_levels(symbol):
    data = request.json
    logger.debug(f"Received TP levels data for {symbol}: {data}")

    try:
        levels = data.get('tp_levels', [])
        process_tp_levels(symbol, levels)

        db.session.commit()
        logger.debug(f"TP levels saved successfully for {symbol}")
        return jsonify({"success": True, "message": f"Take profit levels saved successfully for {symbol}"})

    except SQLAlchemyError as e:
        db.session.rollback()
        error_msg = f"Database error while saving TP levels for {symbol}: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
    except Exception as e:
        db.session.rollback()
        error_msg = f"Unexpected error while saving TP levels for {symbol}: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500

def process_tp_levels(symbol, levels):
    logger.debug(f"Processing TP levels for symbol: {symbol}")
    
    # Get existing TP levels for this symbol
    existing_tp_levels = TakeProfit.query.filter_by(symbol=symbol).all()
    existing_tp_dict = {(tp.target, tp.quantity): tp for tp in existing_tp_levels}
    
    # Process new TP levels
    processed_tps = set()
    for level_data in levels:
        key = (level_data['target'], level_data['quantity'])
        if key in existing_tp_dict:
            # Update existing TP level
            existing_tp = existing_tp_dict[key]
            existing_tp.enabled = level_data['enabled']
            existing_tp.price = level_data['price']
            existing_tp.hit = level_data['hit']
            logger.debug(f"Updated existing TP level for {symbol}: {level_data}")
        else:
            # Add new TP level
            new_tp = TakeProfit(
                symbol=symbol,
                enabled=level_data['enabled'],
                quantity=level_data['quantity'],
                target=level_data['target'],
                price=level_data['price'],
                hit=level_data['hit']
            )
            db.session.add(new_tp)
            logger.debug(f"Added new TP level for {symbol}: {level_data}")
        processed_tps.add(key)
    
    # Remove TP levels that are no longer present
    for key, tp in existing_tp_dict.items():
        if key not in processed_tps:
            db.session.delete(tp)
            logger.debug(f"Removed obsolete TP level for {symbol}: {tp.to_dict()}")

    logger.debug(f"Finished processing TP levels for {symbol}")


@app.route('/api/get_tp_levels/<symbol>', methods=['GET'])
def get_tp_levels(symbol):
    logger.debug(f"Retrieving TP levels for symbol: {symbol}")
    try:
        tp_levels = TakeProfit.query.filter_by(symbol=symbol).all()
        tp_levels_data = [tp.to_dict() for tp in tp_levels]
        logger.debug(f"Retrieved {len(tp_levels_data)} TP levels for {symbol}")
        return jsonify({
            "success": True,
            "symbol": symbol,
            "tp_levels": tp_levels_data
        })
    except Exception as e:
        error_msg = f"Error retrieving TP levels for {symbol}: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500


# Individual TP level update endpoint
@app.route('/api/save_tp_level/<symbol>/<int:index>', methods=['PUT'])
def save_individual_tp_level(symbol, index):
    data = request.json
    logger.debug(f"Received individual TP level update for {symbol} at index {index}: {data}")

    try:
        tp_levels = TakeProfit.query.filter_by(symbol=symbol).all()
        if index >= len(tp_levels):
            return jsonify({"success": False, "message": f"TP level index {index} out of range for {symbol}"}), 404

        tp = tp_levels[index]
        tp.enabled = data.get('enabled', tp.enabled)
        tp.quantity = data.get('quantity', tp.quantity)
        tp.target = data.get('target', tp.target)
        tp.price = data.get('price', tp.price)
        tp.hit = data.get('hit', tp.hit)

        db.session.commit()
        logger.debug(f"Updated individual TP level for {symbol} at index {index}")
        return jsonify({"success": True, "message": f"TP level updated for {symbol} at index {index}"})

    except SQLAlchemyError as e:
        db.session.rollback()
        error_msg = f"Database error updating TP level: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
    except Exception as e:
        db.session.rollback()
        error_msg = f"Unexpected error updating TP level: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500

# WebSocket for real-time updates
@socketio.on('connect')
def handle_connect():
    pass
    # Handle client connection

@socketio.on('price_update')
def handle_price_update(data):
    # Process price update
    # Emit update to connected clients
    socketio.emit('price_changed', {'symbol': data['symbol'], 'price': data['price']})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
