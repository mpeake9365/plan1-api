from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)  # Allow requests from any origin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': time.time()})

@app.route('/quote/<ticker>')
def quote(ticker):
    ticker = ticker.upper().strip()
    try:
        # Try Yahoo Finance v8 chart endpoint (2 years daily data)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2y&includePrePost=false'
        r = requests.get(url, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            # Try query2
            url2 = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2y&includePrePost=false'
            r = requests.get(url2, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            data = r.json()
            if data.get('chart', {}).get('result'):
                return jsonify({'source': 'yahoo', 'data': data})

        # Fallback: Stooq CSV
        stooq_url = f'https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d'
        r2 = requests.get(stooq_url, headers=HEADERS, timeout=10)
        if r2.status_code == 200 and len(r2.text) > 100 and 'No data' not in r2.text:
            return jsonify({'source': 'stooq', 'data': r2.text})

        return jsonify({'error': f'No data found for {ticker}'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/batch')
def batch():
    """Fetch multiple tickers at once"""
    tickers_param = request.args.get('tickers', '')
    tickers = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
    
    if not tickers:
        return jsonify({'error': 'No tickers provided'}), 400
    if len(tickers) > 20:
        return jsonify({'error': 'Max 20 tickers per batch'}), 400

    results = {}
    for ticker in tickers:
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2y&includePrePost=false'
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if data.get('chart', {}).get('result'):
                    results[ticker] = {'source': 'yahoo', 'data': data}
                    continue
            # Stooq fallback
            r2 = requests.get(f'https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d', headers=HEADERS, timeout=8)
            if r2.status_code == 200 and len(r2.text) > 100:
                results[ticker] = {'source': 'stooq', 'data': r2.text}
            else:
                results[ticker] = {'error': 'No data'}
        except Exception as e:
            results[ticker] = {'error': str(e)}

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
