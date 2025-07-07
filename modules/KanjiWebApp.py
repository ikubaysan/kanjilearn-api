from flask import Flask, jsonify, request, render_template_string
import requests

app = Flask(__name__)

KANJI_API_BASE_URL = "http://localhost:5733/random_kanji/"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>Random Kanji Viewer</title>
</head>
<body>
    <h2>Random Kanji Info</h2>
    <pre id='kanjiInfo'>Loading...</pre>
    <div id='autoplay-warning' style='color:red; display:none;'>⚠️ Your browser blocked autoplay. Click anywhere on the page to start audio.</div>
    <div>
        <label><input type='checkbox' class='levelCheckbox' value='5' checked>N5</label>
        <label><input type='checkbox' class='levelCheckbox' value='4' checked>N4</label>
        <label><input type='checkbox' class='levelCheckbox' value='3' checked>N3</label>
        <label><input type='checkbox' class='levelCheckbox' value='2' checked>N2</label>
        <label><input type='checkbox' class='levelCheckbox' value='1' checked>N1</label>
    </div>
    <div>
        <button id='refreshBtn'>Force Refresh</button>
        <label for='intervalInput'>Auto-refresh interval (seconds):</label>
        <input type='number' id='intervalInput' min='1' />
    </div>
    <script>
        let autoRefreshInterval = null;

        async function fetchAndRender() {
            try {
                const levels = Array.from(document.querySelectorAll('.levelCheckbox:checked')).map(cb => cb.value).join(',');
                const url = levels ? `/get_kanji?levels=${levels}` : '/get_kanji';
                const response = await fetch(url);
                const data = await response.json();
                document.getElementById('kanjiInfo').textContent = data.kanji_info;
                playAudioSequentially(data.audio_urls);
            } catch (e) {
                document.getElementById('kanjiInfo').textContent = 'Error fetching kanji.';
                console.error(e);
            }
        }

        async function playAudioSequentially(audioUrls) {
            const warning = document.getElementById('autoplay-warning');
            for (const url of audioUrls) {
                const audio = new Audio(url);
                try {
                    await audio.play();
                    await new Promise(resolve => audio.onended = resolve);
                } catch (error) {
                    console.warn('Autoplay blocked:', error);
                    warning.style.display = 'block';
                    break;
                }
            }
        }

        document.getElementById('refreshBtn').addEventListener('click', fetchAndRender);
        document.getElementById('intervalInput').addEventListener('change', function() {
            let interval = parseInt(this.value);
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
            if (!isNaN(interval) && interval > 0) {
                autoRefreshInterval = setInterval(fetchAndRender, interval * 1000);
            }
        });

        document.addEventListener('click', () => {
            const warning = document.getElementById('autoplay-warning');
            if (warning.style.display !== 'none') {
                warning.style.display = 'none';
                fetchAndRender();
            }
        });

        window.onload = fetchAndRender;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_kanji')
def get_kanji():
    try:
        levels = request.args.get('levels', '')
        url = KANJI_API_BASE_URL + (levels if levels else '') + '?audio=true&json=true'
        response = requests.get(url, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
