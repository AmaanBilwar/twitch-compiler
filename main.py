from flask import Flask, request, jsonify, render_template


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('collect-clips.html')

@app.route('/collect-clips', methods=['POST'])
def collect_clips():
    try:
        username = request.form.get('username')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
            
        from clips_collector import collect_clip_urls
        collect_clip_urls(username)
        
        return jsonify({
            'message': f'Successfully collected clips for {username}',
            'filename': f'{username}_clips.csv'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
