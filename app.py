from flask import Flask, request, jsonify, redirect, render_template
from models import db, URL
from utils import generate_short_code
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
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400

    short_code = generate_short_code()
    while URL.query.filter_by(short_code=short_code).first():
        short_code = generate_short_code()

    new_url = URL(original_url=original_url, short_code=short_code)
    db.session.add(new_url)
    db.session.commit()

    return jsonify({'short_url': f'{request.host_url}{short_code}'})

@app.route('/<short_code>')
def redirect_to_url(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if url_entry:
        url_entry.clicks += 1
        db.session.commit()
        return redirect(url_entry.original_url)
    return jsonify({'error': 'URL not found'}), 404

@app.route('/stats/<short_code>')
def get_stats(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if url_entry:
        return jsonify({
            'original_url': url_entry.original_url,
            'short_code': url_entry.short_code,
            'clicks': url_entry.clicks,
            'created_at': url_entry.created_at.isoformat()
        })
    return jsonify({'error': 'URL not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
