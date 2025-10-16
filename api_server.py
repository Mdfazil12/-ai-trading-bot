from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Simple bot status without heavy dependencies
bot_status = {
    'running': False,
    'money': 10000.0,
    'stocks_owned': 0,
    'last_trade': None,
    'current_price': 0.0,
    'prediction': 'UP',
    'confidence': 0.75,
    'trade_history': []
}

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current bot status"""
    try:
        # Get current AAPL price
        stock = yf.Ticker("AAPL")
        hist = stock.history(period="1d")
        if not hist.empty:
            current_price = float(hist['Close'].iloc[-1])
            bot_status['current_price'] = current_price
        return jsonify(bot_status)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(bot_status)

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    bot_status['running'] = True
    bot_status['last_trade'] = datetime.now().isoformat()
    
    # Add sample trade to history
    sample_trade = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': 'BUY',
        'shares': 10,
        'price': bot_status['current_price'],
        'profit': 0
    }
    bot_status['trade_history'].append(sample_trade)
    
    return jsonify({'message': '🤖 Trading bot started successfully!'})

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    bot_status['running'] = False
    
    # Add sample sell trade if we have buy trades
    if bot_status['trade_history'] and bot_status['trade_history'][-1]['action'] == 'BUY':
        last_trade = bot_status['trade_history'][-1]
        current_price = bot_status['current_price']
        profit = (current_price - last_trade['price']) * last_trade['shares']
        
        sample_sell = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'SELL',
            'shares': last_trade['shares'],
            'price': current_price,
            'profit': round(profit, 2)
        }
        bot_status['trade_history'].append(sample_sell)
        bot_status['money'] += profit
    
    return jsonify({'message': '🛑 Trading bot stopped successfully!'})

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trading history"""
    return jsonify(bot_status['trade_history'])

@app.route('/', methods=['GET'])
def home():
    """API home page"""
    return jsonify({
        'service': '🤖 AI Trading Bot API',
        'status': '✅ Online',
        'version': '1.0.0',
        'message': 'Trading bot API is running successfully!',
        'features': [
            '📊 Real-time AAPL stock prices',
            '🔄 Start/Stop bot controls',
            '📈 Trade history tracking',
            '💰 Profit/Loss calculations'
        ],
        'endpoints': {
            'status': '/api/status - Get bot status',
            'start': '/api/start_bot - Start the bot',
            'stop': '/api/stop_bot - Stop the bot', 
            'trades': '/api/trades - Get trade history'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting AI Trading Bot API Server...")
    print("📊 AAPL stock trading bot ready!")
    print("🌐 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
