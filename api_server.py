from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import yfinance as yf
from ai_bot import SimpleAIBot
from safety import SafetyManager
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global variables
trading_bot = None
bot_status = {
    'running': False,
    'money': 10000,
    'stocks_owned': 0,
    'last_trade': None,
    'current_price': 0,
    'prediction': None,
    'confidence': 0,
    'trade_history': []
}
safety_manager = SafetyManager(max_loss_per_day=500)

@app.route('/api/status', methods=['GET'])
def get_bot_status():
    """Get current bot status for Flutter app"""
    try:
        # Get current stock price
        stock = yf.Ticker("AAPL")
        current_price = stock.history(period="1d")['Close'].iloc[-1]
        bot_status['current_price'] = float(current_price)
        
        return jsonify(bot_status)
    except Exception as e:
        print(f"Error getting status: {e}")
        return jsonify(bot_status)

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    global bot_status
    
    if bot_status['running']:
        return jsonify({'message': 'Bot is already running!'}), 400
    
    bot_status['running'] = True
    
    # Start bot in background thread
    threading.Thread(target=run_bot_loop, daemon=True).start()
    return jsonify({'message': 'Bot started successfully!'})

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    global bot_status
    bot_status['running'] = False
    return jsonify({'message': 'Bot stopped successfully!'})

@app.route('/api/trades', methods=['GET'])
def get_trade_history():
    """Get trading history"""
    return jsonify(bot_status['trade_history'])

def run_bot_loop():
    """Main bot loop running in background"""
    global bot_status, trading_bot, safety_manager
    
    try:
        # Initialize the AI bot
        if trading_bot is None:
            print("🤖 Initializing AI Trading Bot...")
            trading_bot = SimpleAIBot()
            trading_bot.money = bot_status['money']
            trading_bot.stocks_owned = bot_status['stocks_owned']
            
            # Train the model
            print("🧠 Training AI model...")
            trading_bot.train_ai_model("AAPL")
            print("✅ Bot initialized and trained!")
        
        safety_manager.reset_daily_counter(trading_bot.money)
        
        while bot_status['running']:
            try:
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Making trading decision...")
                
                # Safety check
                if not safety_manager.check_if_safe_to_trade(trading_bot.money):
                    print("🛑 Safety limit reached - stopping for today")
                    bot_status['running'] = False
                    break
                
                # Get AI prediction
                prediction, confidence = trading_bot.predict_next_move("AAPL")
                
                if prediction is not None:
                    bot_status['prediction'] = 'UP' if prediction == 1 else 'DOWN'
                    bot_status['confidence'] = float(confidence)
                    
                    # Execute trading decision
                    old_money = trading_bot.money
                    old_stocks = trading_bot.stocks_owned
                    
                    trading_bot.execute_ai_trade("AAPL")
                    
                    # Update bot status
                    bot_status['money'] = float(trading_bot.money)
                    bot_status['stocks_owned'] = int(trading_bot.stocks_owned)
                    bot_status['last_trade'] = datetime.now().isoformat()
                    
                    # Record trade if something changed
                    if old_money != trading_bot.money or old_stocks != trading_bot.stocks_owned:
                        current_price = yf.Ticker("AAPL").history(period="1d")['Close'].iloc[-1]
                        
                        trade_record = {
                            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'action': 'BUY' if trading_bot.stocks_owned > old_stocks else 'SELL',
                            'price': float(current_price),
                            'shares': abs(trading_bot.stocks_owned - old_stocks),
                            'profit': float(trading_bot.money - old_money) if old_money != trading_bot.money else 0
                        }
                        
                        bot_status['trade_history'].append(trade_record)
                        
                        # Keep only last 50 trades
                        if len(bot_status['trade_history']) > 50:
                            bot_status['trade_history'] = bot_status['trade_history'][-50:]
                
                print(f"💰 Current Portfolio: ${trading_bot.money:.2f}")
                print(f"📈 Stocks Owned: {trading_bot.stocks_owned}")
                
                # Wait 1 hour before next decision (3600 seconds)
                # For testing, use 60 seconds instead
                wait_time = 60  # Change to 3600 for production
                print(f"⏳ Waiting {wait_time} seconds until next decision...")
                
                for i in range(wait_time):
                    if not bot_status['running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error in bot loop: {e}")
                time.sleep(10)  # Wait 10 seconds before retry
                
    except Exception as e:
        print(f"❌ Fatal error in bot initialization: {e}")
        bot_status['running'] = False

if __name__ == '__main__':
    print("🚀 Starting Trading Bot API Server...")
    print("📱 Flutter app can connect to: http://YOUR_IP:5000")
    print("🔍 Bot will trade AAPL stock using AI predictions")
    print("⚠️  Starting with $10,000 virtual money")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
