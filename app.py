from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import os
import threading

# Name the Flask instance 'server' to avoid conflict with module name 'app'
server = Flask(__name__)
CORS(server)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

def keep_alive():
    time.sleep(60)
    while True:
        try:
            base = os.environ.get('RENDER_EXTERNAL_URL', '')
            if base:
                requests.get(f'{base}/health', timeout=10)
        except:
            pass
        time.sleep(600)

threading.Thread(target=keep_alive, daemon=True).start()

@server.route('/')
@server.route('/mark')
def mark():
    try:
        with open('plan1_mark.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f'Error: {e}', 500

@server.route('/bill')
def bill():
    try:
        with open('plan1_bill.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f'Error: {e}', 500

@server.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': time.time()})

@server.route('/quote/<ticker>')
def quote(ticker):
    ticker = ticker.upper().strip()
    try:
        for host in ['query1', 'query2']:
            url = f'https://{host}.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2y&includePrePost=false'
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('chart', {}).get('result'):
                    return jsonify({'source': 'yahoo', 'data': data})
        r2 = requests.get(f'https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d', headers=HEADERS, timeout=10)
        if r2.status_code == 200 and len(r2.text) > 100 and 'No data' not in r2.text:
            return jsonify({'source': 'stooq', 'data': r2.text})
        return jsonify({'error': f'No data for {ticker}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@server.route('/batch')
def batch():
    tickers = [t.strip().upper() for t in request.args.get('tickers','').split(',') if t.strip()]
    if not tickers:
        return jsonify({'error': 'No tickers'}), 400
    results = {}
    for ticker in tickers[:20]:
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2y&includePrePost=false'
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if data.get('chart', {}).get('result'):
                    results[ticker] = {'source': 'yahoo', 'data': data}
                    continue
            r2 = requests.get(f'https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d', headers=HEADERS, timeout=8)
            if r2.status_code == 200 and len(r2.text) > 100:
                results[ticker] = {'source': 'stooq', 'data': r2.text}
            else:
                results[ticker] = {'error': 'No data'}
        except Exception as e:
            results[ticker] = {'error': str(e)}
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
