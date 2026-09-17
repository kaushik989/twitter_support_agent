import os
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.agent import AntigravitySupportAgent
from src.baselines import SimpleMLBaseline

print("[*] Initializing AI Agent for Web Interface...")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SAMPLE_PATH = os.path.join(DATA_DIR, "apple_support_sample.json")
GOLDEN_PATH = os.path.join(DATA_DIR, "golden_set.json")

with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
    sample_records = json.load(f)

agent = AntigravitySupportAgent(confidence_threshold=0.70)
agent.train(sample_records[:9800])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AppleSupport AI Agent Console</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-5xl mx-auto space-y-6">
        <!-- Header -->
        <header class="flex items-center justify-between glass p-6 rounded-2xl shadow-xl">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-black flex items-center justify-center text-white text-2xl shadow-md border border-gray-700">
                    <i class="fa-brands fa-apple"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        @AppleSupport AI Support Console
                        <span class="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium">Live Active</span>
                    </h1>
                    <p class="text-sm text-slate-400">Data-driven Intent Classifier, Grounded RAG & Risk Safety Router</p>
                </div>
            </div>
            <div class="text-right hidden sm:block">
                <span class="text-xs text-slate-400 block">Dataset</span>
                <span class="text-sm font-semibold text-sky-400">Thought Vector Twitter (106k pairs)</span>
            </div>
        </header>

        <!-- Main Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Left: Input & Preset Samples -->
            <div class="lg:col-span-5 space-y-6">
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-lg font-semibold text-slate-200 flex items-center gap-2">
                        <i class="fa-brands fa-twitter text-sky-400"></i> Incoming Customer Tweet
                    </h2>
                    
                    <div>
                        <textarea id="tweetInput" rows="4" class="w-full bg-slate-900/90 border border-slate-700 rounded-xl p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition" placeholder="Type a customer query directed to @AppleSupport..."></textarea>
                    </div>

                    <button id="btnSubmit" onclick="processTweet()" class="w-full py-3 bg-sky-500 hover:bg-sky-400 text-white font-semibold rounded-xl shadow-lg shadow-sky-500/20 transition flex items-center justify-center gap-2">
                        <i class="fa-solid fa-paper-plane"></i> Process with AI Agent
                    </button>
                </div>

                <!-- Sample Presets -->
                <div class="glass p-6 rounded-2xl space-y-3">
                    <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                        <i class="fa-solid fa-vial"></i> Quick Test Scenarios
                    </h3>
                    <div class="space-y-2 text-xs">
                        <button onclick="loadSample('iOS 11 update makes my phone freeze every time I open Messages. Any fix?')" class="w-full text-left p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition">
                            📱 <strong>Technical:</strong> Software freeze after iOS update
                        </button>
                        <button onclick="loadSample('I forgot my Apple ID password and my account is locked! Need help ASAP')" class="w-full text-left p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition">
                            🔐 <strong>Account (Escalate):</strong> Locked Apple ID / Password
                        </button>
                        <button onclick="loadSample('My iPhone screen shattered when I dropped it. How much for repair?')" class="w-full text-left p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition">
                            🔨 <strong>Hardware (Escalate):</strong> Shattered screen repair
                        </button>
                        <button onclick="loadSample('How do I turn off location services for specific apps in iOS?')" class="w-full text-left p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition">
                            ⚙️ <strong>How-To (Auto):</strong> Change location settings
                        </button>
                        <button onclick="loadSample('This is unacceptable!! Apple charged me $299 for a subscription I canceled!')" class="w-full text-left p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition">
                            😡 <strong>Complaint & Billing (Escalate):</strong> Unauthorized charge
                        </button>
                    </div>
                </div>
            </div>

            <!-- Right: Agent Execution Output -->
            <div class="lg:col-span-7 space-y-6">
                <!-- Result Container -->
                <div id="outputCard" class="glass p-6 rounded-2xl space-y-6 hidden">
                    <!-- Routing Decision Banner -->
                    <div id="decisionBanner" class="p-4 rounded-xl border flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div id="decisionIcon" class="w-10 h-10 rounded-full flex items-center justify-center text-lg"></div>
                            <div>
                                <div id="decisionTitle" class="font-bold text-base"></div>
                                <div id="decisionReason" class="text-xs opacity-90"></div>
                            </div>
                        </div>
                        <span id="decisionBadge" class="text-xs font-bold uppercase px-3 py-1 rounded-full"></span>
                    </div>

                    <!-- Intent & Confidence -->
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                            <span class="text-xs text-slate-400 block mb-1">Predicted Intent</span>
                            <span id="resIntent" class="font-semibold text-sky-400 text-sm"></span>
                        </div>
                        <div class="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                            <span class="text-xs text-slate-400 block mb-1">Classifier Confidence</span>
                            <div class="flex items-center gap-2">
                                <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                    <div id="resConfBar" class="bg-sky-500 h-full transition-all duration-500" style="width: 0%"></div>
                                </div>
                                <span id="resConfText" class="text-xs font-bold text-slate-300"></span>
                            </div>
                        </div>
                    </div>

                    <!-- Drafted Response -->
                    <div class="space-y-2">
                        <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                            <i class="fa-solid fa-comment-dots"></i> Drafted Grounded Response
                        </h3>
                        <div class="bg-slate-900/90 border border-slate-700/80 p-4 rounded-xl text-slate-200 text-sm leading-relaxed relative">
                            <div class="flex items-center gap-2 mb-2 text-xs font-semibold text-sky-400">
                                <i class="fa-brands fa-apple"></i> @AppleSupport
                            </div>
                            <p id="resReply"></p>
                        </div>
                    </div>

                    <!-- Grounded RAG Context -->
                    <div class="space-y-2">
                        <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                            <i class="fa-solid fa-database"></i> Grounded Historical Resolution Match
                        </h3>
                        <div id="ragContext" class="space-y-2"></div>
                    </div>
                </div>

                <!-- Empty State -->
                <div id="emptyState" class="glass p-12 rounded-2xl text-center space-y-3">
                    <div class="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center text-slate-500 text-2xl mx-auto">
                        <i class="fa-solid fa-robot"></i>
                    </div>
                    <h3 class="text-base font-semibold text-slate-300">Ready for Query Processing</h3>
                    <p class="text-xs text-slate-400 max-w-sm mx-auto">Enter a customer tweet on the left or select a quick test scenario to view real-time intent classification, grounded reply drafting, and escalation routing.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function loadSample(text) {
            document.getElementById('tweetInput').value = text;
            processTweet();
        }

        async function processTweet() {
            const tweet = document.getElementById('tweetInput').value.trim();
            if (!tweet) return;

            const btn = document.getElementById('btnSubmit');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

            try {
                const res = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tweet })
                });
                const data = await res.json();
                renderResult(data);
            } catch (err) {
                alert('Error processing request: ' + err);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Process with AI Agent';
            }
        }

        function renderResult(data) {
            document.getElementById('emptyState').classList.add('hidden');
            const card = document.getElementById('outputCard');
            card.classList.remove('hidden');

            // Routing Banner
            const banner = document.getElementById('decisionBanner');
            const icon = document.getElementById('decisionIcon');
            const title = document.getElementById('decisionTitle');
            const reason = document.getElementById('decisionReason');
            const badge = document.getElementById('decisionBadge');

            if (data.decision === 'ESCALATE') {
                banner.className = 'p-4 rounded-xl border bg-amber-500/10 border-amber-500/30 text-amber-200';
                icon.className = 'w-10 h-10 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center text-lg';
                icon.innerHTML = '<i class="fa-solid fa-user-shield"></i>';
                title.textContent = 'ESCALATE TO HUMAN REPRESENTATIVE';
                reason.textContent = data.escalation_reason;
                badge.className = 'text-xs font-bold uppercase px-3 py-1 rounded-full bg-amber-500/30 text-amber-300 border border-amber-500/40';
                badge.textContent = 'Tier-2 Human Escalation';
            } else {
                banner.className = 'p-4 rounded-xl border bg-emerald-500/10 border-emerald-500/30 text-emerald-200';
                icon.className = 'w-10 h-10 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-lg';
                icon.innerHTML = '<i class="fa-solid fa-robot"></i>';
                title.textContent = 'AUTO-HANDLE (SAFE AI RESOLUTION)';
                reason.textContent = data.escalation_reason;
                badge.className = 'text-xs font-bold uppercase px-3 py-1 rounded-full bg-emerald-500/30 text-emerald-300 border border-emerald-500/40';
                badge.textContent = 'Automated AI Reply';
            }

            // Intent & Confidence
            document.getElementById('resIntent').textContent = data.intent;
            const confPct = Math.round(data.intent_confidence * 100);
            document.getElementById('resConfBar').style.width = confPct + '%';
            document.getElementById('resConfText').textContent = confPct + '%';

            // Reply
            document.getElementById('resReply').textContent = data.reply;

            // RAG Matches
            const ragDiv = document.getElementById('ragContext');
            ragDiv.innerHTML = '';
            if (data.retrieved_context && data.retrieved_context.length > 0) {
                data.retrieved_context.forEach((ctx, i) => {
                    const el = document.createElement('div');
                    el.className = 'p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs space-y-1';
                    el.innerHTML = `
                        <div class="flex justify-between text-slate-400 font-medium">
                            <span>Historical Customer Match #${i+1}</span>
                            <span class="text-sky-400">Sim: ${(ctx.score * 100).toFixed(1)}%</span>
                        </div>
                        <div class="text-slate-300"><strong>Query:</strong> ${ctx.historical_query}</div>
                        <div class="text-slate-400"><strong>Resolution:</strong> ${ctx.historical_reply}</div>
                    `;
                    ragDiv.appendChild(el);
                });
            }
        }
    </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/process":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                tweet = payload.get("tweet", "")
                result = agent.process_tweet(tweet)
                
                # Format retrieved context
                clean_context = []
                for item in result.get("retrieved_context", []):
                    clean_context.append({
                        "score": float(item["score"]),
                        "historical_query": item["historical_query"],
                        "historical_reply": item["historical_reply"]
                    })
                result["retrieved_context"] = clean_context
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print("=" * 65)
    print(f"  🚀 @AppleSupport AI Agent Web Console running live!")
    print(f"  👉 Open URL in your browser: http://localhost:{port}")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
