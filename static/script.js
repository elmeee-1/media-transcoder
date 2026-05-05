let selectedType = 'video';
let currentJobId = null;
let pollInterval = null;

document.addEventListener('DOMContentLoaded', function() {

    document.getElementById('btnVideo').addEventListener('click', function() {
        selectedType = 'video';
        document.getElementById('btnVideo').classList.add('active');
        document.getElementById('btnAudio').classList.remove('active');
    });

    document.getElementById('btnAudio').addEventListener('click', function() {
        selectedType = 'audio';
        document.getElementById('btnAudio').classList.add('active');
        document.getElementById('btnVideo').classList.remove('active');
    });

    document.querySelector('.download-btn').addEventListener('click', async function() {
        const url = document.getElementById('urlInput').value.trim();

        if (!url) {
            alert('Please paste a YouTube URL first.');
            return;
        }

        document.getElementById('progressCard').style.display = 'block';
        document.getElementById('progressFill').style.width = '0%';
        document.getElementById('progressPercent').textContent = '0%';
        document.getElementById('statusText').textContent = 'Starting download...';
        document.getElementById('saveBtn').style.display = 'none';

        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, media_type: selectedType })
        });

        const data = await response.json();
        currentJobId = data.job_id;

        pollInterval = setInterval(checkStatus, 1000);
    });

   document.getElementById('saveBtn').addEventListener('click', function() {
    const a = document.createElement('a');
    a.href = `/file/${currentJobId}`;
    a.download = '';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});

});

async function checkStatus() {
    const response = await fetch(`/status/${currentJobId}`);
    const data = await response.json();

    document.getElementById('progressFill').style.width = data.progress + '%';
    document.getElementById('progressPercent').textContent = data.progress + '%';

    if (data.status === 'downloading') {
        document.getElementById('statusText').textContent = '⬇️ Downloading...';
    } else if (data.status === 'done') {
        clearInterval(pollInterval);
        document.getElementById('statusText').textContent = '✅ Done! Click below to save.';
        document.getElementById('saveBtn').style.display = 'block';
    } else if (data.status === 'error') {
        clearInterval(pollInterval);
        document.getElementById('statusText').textContent = '❌ Error — check the URL and try again.';
    }
}