from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
import matplotlib.pyplot as plt
import io
import koreanize_matplotlib

app = Flask(__name__)
app.secret_key = 'supersecretkey'

votes = {name: {mbti: 0 for mbti in ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ",
                                     "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP", "CUTE", "SEXY"]} 
         for name in ["박정호", "류범상", "김경민", "유동원", "이은경", "김가은", "한경훈", "배재형", "공준식"]}
actual_mbti = {"유동원": "INTJ",
               "이은경": "ISFJ",
               "김경민": "ISTJ",
               "류범상": "INTP",
               "박정호": "INTJ",
               "김가은": "ENTJ",
               "한경훈": "ISTJ",
               "배재형": "ESFJ",
               "공준식": "INTJ"
            }
vote_details = []


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote', methods=['POST'])
def vote():
    data = request.json
    voter_name = data['voterName']
    name = data['name']
    mbti = data['mbti']
    votes[name][mbti] += 1
    vote_details.append({'voterName': voter_name, 'name': name, 'mbti': mbti})
    return jsonify({'status': 'success'})

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
    img = io.BytesIO()
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
    #app.run(debug=True)
    app.run(host='0.0.0.0',port=5000)
