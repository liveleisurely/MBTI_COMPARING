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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # SQLAlchemy 경고를 피하기 위해 추가

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)

votes = {name: {mbti: 0 for mbti in ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ",
                                     "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP", "CUTE", "SEXY"]} 
         for name in ["박정호", "류범상", "김경민", "유동원", "이은경", "김가은", "한경훈", "배재형", "공준식","김태영"]}

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
vote_details = []

start_time = datetime.now()
end_time = start_time + timedelta(hours=12)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    session.permanent = True  # 세션을 영구적으로 설정하여 세션 만료 시간을 적용합니다.
    user_votes = [vote_detail['name'] for vote_detail in vote_details if vote_detail['voterName'] == session['username']]
    return render_template('index.html', username=session['username'], user_votes=user_votes if user_votes else [], end_time=end_time.timestamp())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 사용 중인 아이디입니다.', 'error')
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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            session['has_voted'] = user.has_voted
            session.permanent = True  # 세션을 영구적으로 설정하여 세션 만료 시간을 적용합니다.
            return redirect(url_for('index'))
        else:
            flash('로그인 정보가 일치하지 않습니다.', 'error')
    
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
    name = data['name']
    mbti = data['mbti']
    
    # Check if the user has already voted for this person
    for vote_detail in vote_details:
        if vote_detail['voterName'] == session['username'] and vote_detail['name'] == name:
            return jsonify({'status': 'fail', 'message': '이미 해당 사람에게 투표하셨습니다!'})

    votes[name][mbti] += 1
    vote_details.append({'voterName': session['username'], 'name': name, 'mbti': mbti})

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
        if total_votes >= 7:
            show_results = True
            most_voted_mbti = max(mbti_votes, key=mbti_votes.get)
            actual = actual_mbti[name]
            if most_voted_mbti == actual:
                results[name] = "MATCH"
            else:
                results[name] = f"Voted: {most_voted_mbti}, Actual: {actual}"
        else:
            results[name] = f"투표수가 부족합니다 ({total_votes}/9)"

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
    app.run(host='0.0.0.0', port=5000, debug=True)
