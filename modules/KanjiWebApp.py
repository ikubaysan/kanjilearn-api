import os
from flask import Flask, jsonify, request, render_template_string
from modules.Config import Config
import requests
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KanjiWebApp:
    def __init__(self, config: Config):
        self.config = config
        self.app = Flask(__name__)

        # Construct base URL using public hostname and port
        self.kanji_api_base_url = f"{self.config.public_hostname}:{self.config.port}/random_kanji/"

        # Register routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/get_kanji', 'get_kanji', self.get_kanji)

        logger.info(f"KanjiWebApp initialized with API base URL: {self.kanji_api_base_url}")

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
        <div style='margin-top: 1em;'>
            <button id='refreshBtn'>Force Refresh</button>
            <label for='intervalInput'>Auto-refresh interval (seconds):</label>
            <input type='number' id='intervalInput' min='1' />
            <div id='interval-validation' style='color:red; display:none;'></div>
        </div>
        <script>
            let autoRefreshInterval = null;
            let currentAudioUrls = [];
            let currentAudio = null;
            let stopAudioPlayback = false;

            async function fetchAndRender() {
                const refreshBtn = document.getElementById('refreshBtn');
                refreshBtn.disabled = true;
                try {
                    const levels = Array.from(document.querySelectorAll('.levelCheckbox:checked')).map(cb => cb.value).join(',');
                    const url = levels ? `/get_kanji?levels=${levels}` : '/get_kanji';
                    const response = await fetch(url);
                    const data = await response.json();
                    document.getElementById('kanjiInfo').textContent = data.kanji_info;

                    // Stop previous audio playback
                    stopAudioPlayback = true;
                    if (currentAudio) {
                        currentAudio.pause();
                        currentAudio.currentTime = 0;
                        currentAudio = null;
                    }

                    currentAudioUrls = data.audio_urls;
                    stopAudioPlayback = false; // allow playback of new kanji
                    playAudioSequentially(currentAudioUrls);
                } catch (e) {
                    document.getElementById('kanjiInfo').textContent = 'Error fetching kanji.';
                    console.error(e);
                } finally {
                    refreshBtn.disabled = false;
                }
            }

            async function playAudioSequentially(audioUrls) {
                if (!audioUrls || audioUrls.length === 0) return;
                const warning = document.getElementById('autoplay-warning');

                for (const url of audioUrls) {
                    if (stopAudioPlayback) break;

                    const audio = new Audio(url);
                    currentAudio = audio;

                    try {
                        await audio.play();
                        await new Promise((resolve) => {
                            audio.onended = resolve;
                            audio.onerror = resolve;
                        });
                    } catch (error) {
                        console.warn('Autoplay blocked or error:', error);
                        warning.style.display = 'block';
                        break;
                    }
                }

                currentAudio = null;
            }

            document.getElementById('refreshBtn').addEventListener('click', fetchAndRender);
            document.getElementById('intervalInput').addEventListener('input', function() {
                const validation = document.getElementById('interval-validation');
                let interval = parseInt(this.value);
                if (!this.value) {
                    validation.style.display = 'none';
                    if (autoRefreshInterval) {
                        clearInterval(autoRefreshInterval);
                        autoRefreshInterval = null;
                    }
                    return;
                }
                if (isNaN(interval) || interval < 30) {
                    validation.textContent = 'Interval must be at least 30 seconds.';
                    validation.style.display = 'block';
                    if (autoRefreshInterval) {
                        clearInterval(autoRefreshInterval);
                        autoRefreshInterval = null;
                    }
                } else {
                    validation.style.display = 'none';
                    if (autoRefreshInterval) {
                        clearInterval(autoRefreshInterval);
                        autoRefreshInterval = null;
                    }
                    autoRefreshInterval = setInterval(fetchAndRender, interval * 1000);
                }
            });

            document.addEventListener('click', () => {
                const warning = document.getElementById('autoplay-warning');
                if (warning.style.display !== 'none') {
                    warning.style.display = 'none';
                    playAudioSequentially(currentAudioUrls);  // play current kanji audio without fetching new
                }
            });

            window.onload = fetchAndRender;
        </script>
    </body>
    </html>
    """

    def index(self):
        return render_template_string(self.HTML_TEMPLATE)

    def get_kanji(self):
        try:
            levels = request.args.get('levels', '')
            url = self.kanji_api_base_url + (levels if levels else '') + '?audio=true&json=true'
            logger.info(f"Requesting kanji from {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return jsonify(response.json())
        except Exception as e:
            logger.error(f"Error fetching kanji: {e}")
            return jsonify({'error': str(e)}), 500

    def run(self, host='0.0.0.0', debug=True):
        port = self.config.webapp_port
        self.app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    config = Config(os.path.join(base_dir, 'config.ini'))
    app = KanjiWebApp(config)
    app.run()
