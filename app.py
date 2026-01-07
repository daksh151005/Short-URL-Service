from flask import Flask, request, jsonify, redirect, render_template, send_file
from models import db, URL, Click
from utils import generate_short_code
from datetime import datetime, timedelta, timezone
import qrcode
import io
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    original_url = data.get('url')
    custom_code = data.get('custom_code')
    expiry_days = data.get('expiry_days')

    if not original_url:
        return jsonify({'error': 'URL is required'}), 400

    if custom_code:
        if not custom_code.replace('_', '').replace('-', '').isalnum():
            return jsonify({'error': 'Custom code must be alphanumeric, underscores, or hyphens only'}), 400
        if URL.query.filter_by(short_code=custom_code).first():
            return jsonify({'error': 'Custom code already exists'}), 400
        short_code = custom_code
    else:
        short_code = generate_short_code()
        while URL.query.filter_by(short_code=short_code).first():
            short_code = generate_short_code()

    expiry_date = None
    if expiry_days:
        expiry_date = datetime.now(timezone.utc) + timedelta(days=int(expiry_days))
    new_url = URL(original_url=original_url, short_code=short_code, expiry_date=expiry_date)
    db.session.add(new_url)
    db.session.commit()

    return jsonify({'short_url': f'{request.host_url}{short_code}'})

@app.route('/<short_code>')
def redirect_to_url(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if url_entry:
        if url_entry.expiry_date and datetime.now(timezone.utc) > url_entry.expiry_date:
            return jsonify({'error': 'URL has expired'}), 410
        url_entry.clicks += 1
        click = Click(url_id=url_entry.id)
        db.session.add(click)
        db.session.commit()
        return redirect(url_entry.original_url)
    return jsonify({'error': 'URL not found'}), 404

@app.route('/stats/<short_code>')
def get_stats(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if url_entry:
        clicks_history = [click.timestamp.isoformat() for click in url_entry.clicks_history]
        return jsonify({
            'original_url': url_entry.original_url,
            'short_code': url_entry.short_code,
            'clicks': url_entry.clicks,
            'created_at': url_entry.created_at.isoformat(),
            'expiry_date': url_entry.expiry_date.isoformat() if url_entry.expiry_date else None,
            'clicks_history': clicks_history
        })
    return jsonify({'error': 'URL not found'}), 404

@app.route('/urls')
def get_all_urls():
    urls = URL.query.all()
    return jsonify([{
        'id': url.id,
        'original_url': url.original_url,
        'short_code': url.short_code,
        'clicks': url.clicks,
        'created_at': url.created_at.isoformat(),
        'expiry_date': url.expiry_date.isoformat() if url.expiry_date else None
    } for url in urls])

@app.route('/qr/<short_code>')
def generate_qr(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if url_entry:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f'{request.host_url}{short_code}')
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    return jsonify({'error': 'URL not found'}), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
