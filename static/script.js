// static/script.js
let countdownDate = new Date().getTime() + 12 * 60 * 60 * 1000; // 12 hours from now

function updateTimer() {
    const now = new Date().getTime();
    const distance = countdownDate - now;

    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    document.getElementById('time').textContent = `${hours}:${minutes}:${seconds}`;

    if (distance < 0) {
        clearInterval(timerInterval);
        document.getElementById('time').textContent = '00:00:00';
        // Disable voting
        document.getElementById('voteForm').style.display = 'none';
        window.location.href = '/compare'; // Redirect to compare page
    }
}

const timerInterval = setInterval(updateTimer, 1000);

document.getElementById('voteForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const voterName = document.getElementById('voterName').value;
    if (!voterName) {
        alert('투표자 이름을 입력하세요.');
        return;
    }
    const voteData = {
        voterName: voterName,
        name: formData.get('name'),
        mbti: formData.get('mbti')
    };

    fetch('/vote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(voteData),
    }).then(response => response.json()).then(data => {
        alert('투표가 완료되었습니다!');
        document.getElementById('voteForm').reset();
        document.getElementById('voterName').value = '';
        updateResults();
    });
});

document.getElementById('compareButton').addEventListener('click', function() {
    window.location.href = '/compare';
});

function updateResults() {
    fetch('/results').then(response => response.blob()).then(imageBlob => {
        const imageObjectURL = URL.createObjectURL(imageBlob);
        document.getElementById('resultsImage').src = imageObjectURL;
    });
}

updateTimer();  // Timer initialization
updateResults();
