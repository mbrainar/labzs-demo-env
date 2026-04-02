from flask import Flask, render_template_string
from skyfield.api import load, Topos
from datetime import datetime, timezone
import math

app = Flask(__name__)

# Load ephemeris
eph = load('de421.bsp')

# Define locations
earth = eph['earth']
moon = eph['moon']
sun = eph['sun']

def get_moon_phase():
    # Current time
    now = datetime.now(timezone.utc)
    ts = load.timescale()
    t = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)

    # Positions
    earth_pos = earth.at(t)
    moon_pos = earth_pos.observe(moon)

    # Phase angle
    phase_angle = moon_pos.phase_angle(sun).degrees

    # Phase fraction (0 to 1)
    phase_fraction = (1 + math.cos(math.radians(phase_angle))) / 2

    # Determine phase name
    if phase_fraction < 0.125:
        phase_name = "New Moon"
        emoji = "🌑"
    elif phase_fraction < 0.375:
        phase_name = "Waxing Crescent"
        emoji = "🌒"
    elif phase_fraction < 0.625:
        phase_name = "First Quarter"
        emoji = "🌓"
    elif phase_fraction < 0.875:
        phase_name = "Waxing Gibbous"
        emoji = "🌔"
    elif phase_fraction < 0.9375:
        phase_name = "Full Moon"
        emoji = "🌕"
    elif phase_fraction < 0.96875:
        phase_name = "Waning Gibbous"
        emoji = "🌖"
    elif phase_fraction < 0.984375:
        phase_name = "Last Quarter"
        emoji = "🌗"
    else:
        phase_name = "Waning Crescent"
        emoji = "🌘"

    return {
        'phase_name': phase_name,
        'emoji': emoji,
        'phase_fraction': phase_fraction,
        'date': now.strftime('%Y-%m-%d %H:%M:%S UTC')
    }

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moon Cycle Tracker</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0c0c0c, #1a1a2e);
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 2rem;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            text-align: center;
            max-width: 600px;
            width: 100%;
        }
        .moon-emoji {
            font-size: 8rem;
            margin: 1rem 0;
        }
        .phase-name {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 1rem 0;
        }
        .phase-fraction {
            font-size: 1.2rem;
            color: #cccccc;
            margin: 0.5rem 0;
        }
        .date {
            font-size: 1rem;
            color: #aaaaaa;
            margin: 1rem 0;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            overflow: hidden;
            margin: 1rem 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcf7f, #4d96ff);
            transition: width 0.5s ease;
        }
        .phases {
            display: flex;
            justify-content: space-around;
            margin-top: 2rem;
            flex-wrap: wrap;
        }
        .phase-item {
            text-align: center;
            margin: 0.5rem;
        }
        .phase-item .emoji {
            font-size: 2rem;
        }
        .phase-item .name {
            font-size: 0.8rem;
            color: #cccccc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Moon Cycle Tracker</h1>
        <div class="moon-emoji">{{ moon.emoji }}</div>
        <div class="phase-name">{{ moon.phase_name }}</div>
        <div class="phase-fraction">Illumination: {{ "%.1f"|format(moon.phase_fraction * 100) }}%</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ moon.phase_fraction * 100 }}%"></div>
        </div>
        <div class="date">As of {{ moon.date }}</div>
        
        <div class="phases">
            <div class="phase-item">
                <div class="emoji">🌑</div>
                <div class="name">New Moon</div>
            </div>
            <div class="phase-item">
                <div class="emoji">🌒</div>
                <div class="name">Waxing Crescent</div>
            </div>
            <div class="phase-item">
                <div class="emoji">🌓</div>
                <div class="name">First Quarter</div>
            </div>
            <div class="phase-item">
                <div class="emoji">🌔</div>
                <div class="name">Waxing Gibbous</div>
            </div>
            <div class="phase-item">
                <div class="emoji">🌕</div>
                <div class="name">Full Moon</div>
            </div>
            <div class="phase-item">
                <div class="emoji">🌖</div>
                <div class="name">Waning Gibbous</div>
            </div>
            <div class="phase-item">
                <div class="emoji">🌗</div>
                <div class="name">Last Quarter</div>
            </div>
            <div class="phase-item">
                <div class="emoji">🌘</div>
                <div class="name">Waning Crescent</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    moon_data = get_moon_phase()
    return render_template_string(HTML_TEMPLATE, moon=moon_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)