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

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_name = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    mbti = db.Column(db.String(10), nullable=False)

NAMES = ["박정호", "류범상", "김경민", "유동원", "이은경", "김가은", "한경훈", "배재형", "공준식", "김태영"]
MBTIS = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP", "CUTE", "SEXY", "IIII", "EEEE"]

actual_mbti = {"유동원": "INTJ",
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

start_time = datetime.now()
end_time = start_time + timedelta(hours=12)

color_map = {
    "INTJ": "#FFB3BA",  # Light Red
    "INTP": "#FFDFBA",  # Light Orange
    "ENTJ": "#FFFFBA",  # Light Yellow
    "ENTP": "#BAFFC9",  # Light Green
    "INFJ": "#BAE1FF",  # Light Blue
    "INFP": "#E6B3FF",  # Light Purple
    "ENFJ": "#FFC0CB",  # Pink
    "ENFP": "#FFD700",  # Gold
    "ISTJ": "#B4A7D6",  # Lavender
    "ISFJ": "#D5A6BD",  # Pale Pink
    "ESTJ": "#A2C4C9",  # Pale Blue
    "ESFJ": "#F9CB9C",  # Light Apricot
    "ISTP": "#C9DAF8",  # Pale Cyan
    "ISFP": "#D9D2E9",  # Pale Lavender
    "ESTP": "#CFE2F3",  # Pale Light Blue
    "ESFP": "#FCE5CD",  # Light Peach
    "CUTE": "#FFFAC8",  # Light Yellowish
    "SEXY": "#FFB3BA",  # Light Red
    "IIII": "#D5A6BD",  # Pale Pink
    "EEEE": "#FFD700"   # Gold
}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    session.permanent = True  # 세션을 영구적으로 설정하여 세션 만료 시간을 적용합니다.
    user_votes = Vote.query.filter_by(voter_name=session['username']).all()
    user_votes_names = [vote.name for vote in user_votes]
    return render_template('index.html', username=session['username'], user_votes=user_votes_names, end_time=end_time.timestamp(), names=NAMES, mbtis=MBTIS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 가입된 아이디입니다.', 'error')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('회원가입을 축하합니다', 'success')
            flash(username, 'username')
            flash(password, 'password')
            return redirect(url_for('register'))
        except Exception as e:
            db.session.rollback()
            flash(f'회원가입 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == ['POST']:
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('없는 아이디입니다. 회원가입을 해주세요', 'error')
        elif not check_password_hash(user.password, password):
            flash('비밀번호가 틀렸습니다. 재입력해주세요. 기억이 안나시면 관리자에게 문의해주세요', 'error')
        else:
            session['username'] = username
            session['has_voted'] = user.has_voted
            session.permanent = True  # 세션을 영구적으로 설정하여 세션 만료 시간을 적용합니다.
            return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    session.pop('has_voted', None)
    return jsonify({'status': 'success'})

@app.route('/vote', methods=['POST'])
def vote():
    if 'username' not in session:
        return redirect(url_for('login'))

    data = request.json
    voter_name = data['voterName']
    name = data['name']
    mbti = data['mbti']
    
    if not voter_name:
        return jsonify({'status': 'fail', 'message': '투표자 이름을 입력해주세요.'})
    
    # Check if the user has already voted for this person
    existing_vote = Vote.query.filter_by(voter_name=voter_name, name=name).first()
    if existing_vote:
        return jsonify({'status': 'fail', 'message': '이미 해당 사람에게 투표하셨습니다!'})

    if mbti in ["CUTE", "SEXY", "IIII", "EEEE"]:
        return jsonify({'status': 'fail', 'message': f"'{voter_name}' 님, '{name}' 이(가) {mbti} 한 건 알지만 {mbti}는 MBTI 가 아닙니다"})

    new_vote = Vote(voter_name=voter_name, name=name, mbti=mbti)
    db.session.add(new_vote)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '투표가 성공적으로 완료되었습니다.'})

@app.route('/delete_vote', methods=['POST'])
def delete_vote():
    if 'username' not in session:
        return jsonify({'status': 'fail', 'message': '로그인이 필요합니다.'})

    data = request.json
    voter_name = data['voterName']
    name = data['name']

    Vote.query.filter_by(voter_name=voter_name, name=name).delete()
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '재투표가 가능하게 되었습니다.'})

@app.route('/results', methods=['GET'])
def results():
    votes = {name: {mbti: 0 for mbti in MBTIS} for name in NAMES}
    all_votes = Vote.query.all()
    for vote in all_votes:
        votes[vote.name][vote.mbti] += 1

    fig, axes = plt.subplots(3, 3, figsize=(15, 15))
    axes = axes.flatten()

    for ax, (name, mbti_votes) in zip(axes, votes.items()):
        labels = [mbti for mbti, count in mbti_votes.items() if count > 0]
        sizes = [count for count in mbti_votes.values() if count > 0]
        colors = [color_map[mbti] for mbti in labels]

        if sum(sizes) == 0:
            ax.text(0.5, 0.5, '아직 투표수가 부족합니다', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
            ax.text(0.5, -0.1, name, horizontalalignment='center', verticalalignment='top', transform=ax.transAxes, fontsize=12)  # 아래쪽에 제목 추가
            ax.axis('off')
        else:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
            ax.text(0.5, -0.1, name, horizontalalignment='center', verticalalignment='top', transform=ax.transAxes, fontsize=12)  # 아래쪽에 제목 추가

    for ax in axes[len(votes):]:
        ax.axis('off')

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')

@app.route('/compare')
def compare():
    votes = {name: {mbti: 0 for mbti in MBTIS} for name in NAMES}
    all_votes = Vote.query.all()
    for vote in all_votes:
        votes[vote.name][vote.mbti] += 1

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
    return render_template('vote_details.html', vote_details=Vote.query.all(), actual_mbti=actual_mbti)

@app.route('/update_mbti', methods=['POST'])
def update_mbti():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    data = request.form
    name = data['name']
    actual_mbti[name] = data['mbti']
    return redirect(url_for('vote_details_page'))

@app.route('/clear_votes', methods=['POST'])
def clear_votes():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    try:
        Vote.query.delete()
        db.session.commit()
        flash('모든 투표 데이터가 초기화되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'투표 데이터 초기화 중 오류가 발생했습니다: {str(e)}', 'error')
    return redirect(url_for('vote_details_page'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 데이터베이스와 테이블을 생성합니다.
    app.run(host='0.0.0.0', port=5000, debug=True)
