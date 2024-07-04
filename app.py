from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import io
import koreanize_matplotlib
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)

NAMES = ["박정호", "류범상", "김경민", "유동원", "이은경", "김가은", "한경훈", "배재형", "공준식", "김태영"]
MBTIS = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP", "CUTE", "SEXY"]

votes = {name: {mbti: 0 for mbti in MBTIS} for name in NAMES}

actual_mbti = {
    "유동원": "INTJ",
    "이은경": "ISFJ",
    "김경민": "ISTJ",
    "류범상": "INTP",
    "박정호": "INTJ",
    "김가은": "ENTJ",
    "한경훈": "ISTJ",
    "배재형": "ESFJ",
    "공준식": "INTJ",
    "김태영": "ISFJ"
}
vote_details = []

start_time = datetime.now()
end_time = start_time + timedelta(hours=12)

@app.route('/')
def index():
    user_votes = [vote_detail['name'] for vote_detail in vote_details if vote_detail['voterName'] == session.get('username')]
    return render_template('index.html', user_votes=user_votes if user_votes else [], end_time=end_time.timestamp(), names=NAMES, mbtis=MBTIS)

@app.route('/vote', methods=['POST'])
def vote():
    data = request.json
    voter_name = data['voterName']
    name = data['name']
    mbti = data['mbti']
    
    # Check if the user has already voted for this person
    for vote_detail in vote_details:
        if vote_detail['voterName'] == voter_name and vote_detail['name'] == name:
            return jsonify({'status': 'fail', 'message': '이미 해당 사람에게 투표하셨습니다!'})

    votes[name][mbti] += 1
    vote_details.append({'voterName': voter_name, 'name': name, 'mbti': mbti})

    return jsonify({'status': 'success', 'message': '투표가 성공적으로 완료되었습니다.'})

@app.route('/results', methods=['GET'])
def results():
    fig, axes = plt.subplots(3, 3, figsize=(15, 15))
    axes = axes.flatten()

    for ax, (name, mbti_votes) in zip(axes, votes.items()):
        labels = [mbti for mbti, count in mbti_votes.items() if count > 0]
        sizes = [count for count in mbti_votes.values() if count > 0]
        if sum(sizes) == 0:
            ax.text(0.5, 0.5, '아직 투표수가 부족합니다', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
            ax.set_title(name, fontsize=12)
            ax.axis('off')
        else:
            ax.pie(sizes, labels=labels, autopct='%1.1f%%')
            ax.set_title(name, fontsize=12)

    for ax in axes[len(votes):]:
        ax.axis('off')

    plt.tight_layout()
    img = io.BytesIO()  # 수정된 부분
    plt.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')

@app.route('/compare')
def compare():
    results = {}
    show_results = False
    for name, mbti_votes in votes.items():
        total_votes = sum(mbti_votes.values())
        if total_votes >= 5:
            show_results = True
            most_voted_mbti = max(mbti_votes, key=mbti_votes.get)
            actual = actual_mbti[name]
            if most_voted_mbti == actual:
                results[name] = "MATCH"
            else:
                results[name] = f"Voted: {most_voted_mbti}, Actual: {actual}"
        else:
            results[name] = f"투표수가 부족합니다 ({total_votes}/5)"

    return render_template('compare.html', results=results, show_results=show_results)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'adminpassword':
            session['admin'] = True
            return redirect(url_for('vote_details_page'))
        else:
            return render_template('admin.html', error='비밀번호가 틀렸습니다.')
    return render_template('admin.html')

@app.route('/vote_details')
def vote_details_page():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    return render_template('vote_details.html', vote_details=vote_details, actual_mbti=actual_mbti)

@app.route('/delete_vote', methods=['POST'])
def delete_vote():
    if 'username' not in session:
        return jsonify({'status': 'fail', 'message': '로그인이 필요합니다.'})

    data = request.json
    voter_name = data['voterName']
    name = data['name']

    global vote_details
    vote_details = [vote_detail for vote_detail in vote_details if not (vote_detail['voterName'] == voter_name and vote_detail['name'] == name)]
    
    votes[name] = {mbti: 0 for mbti in votes[name].keys()}  # 해당 이름의 모든 MBTI 투표를 초기화합니다.
    return jsonify({'status': 'success', 'message': '재투표가 가능하게 되었습니다.'})

@app.route('/update_mbti', methods=['POST'])
def update_mbti():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    data = request.form
    name = data['name']
    actual_mbti[name] = data['mbti']
    return redirect(url_for('vote_details_page'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 데이터베이스와 테이블을 생성합니다.
    app.run(host='0.0.0.0', port=5000)
