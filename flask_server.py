# from flask import Flask, Response

# app = Flask(__name__)

# @app.route("/file")
# def file_stream():
#     def generate():
#         with open("LastNight_44100.wav", "rb") as f:
#             while True:
#                 chunk = f.read(1024)
#                 if not chunk:
#                     break
#                 yield chunk

#     return Response(generate(), mimetype="application/octet-stream")

# app.run(host="0.0.0.0", port=8000)


# server.py - روی کامپیوتر اجرا کنید
# این سرور فایل‌های دایرکتوری جاری را سرو می‌کند

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import socket

class FileServer(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """پاسخ به درخواست GET"""
        
        # حذف / از ابتدای path
        file_path = self.path.lstrip('/')
        
        # اگر خالی بود، لیست فایل‌ها را نمایش بده
        if not file_path or file_path == '/':
            self.send_file_list()
            return
        
        # بررسی وجود فایل
        if not os.path.exists(file_path):
            self.send_error(404, f"File not found: {file_path}")
            return
        
        # ارسال فایل
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
            self.end_headers()
            
            # ارسال به صورت chunk برای فایل‌های بزرگ
            chunk_size = 8192
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            
            print(f"✓ File sent: {file_path} ({len(content)} bytes)")
            
        except Exception as e:
            print(f"✗ Error sending file: {e}")
            self.send_error(500, str(e))
    
    def send_file_list(self):
        """نمایش لیست فایل‌های موجود"""
        try:
            files = []
            for item in os.listdir('.'):
                if os.path.isfile(item):
                    size = os.path.getsize(item)
                    files.append((item, size))
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>File Server</title>
                <style>
                    body { font-family: Arial; margin: 40px; background: #f5f5f5; }
                    h1 { color: #333; }
                    table { background: white; border-collapse: collapse; width: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background: #4CAF50; color: white; }
                    tr:hover { background: #f5f5f5; }
                    a { color: #2196F3; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                    .size { color: #666; }
                </style>
            </head>
            <body>
                <h1>📁 Available Files</h1>
                <table>
                    <tr>
                        <th>File Name</th>
                        <th>Size</th>
                        <th>Download</th>
                    </tr>
            """
            
            for filename, size in files:
                size_str = self.format_size(size)
                html += f"""
                    <tr>
                        <td>{filename}</td>
                        <td class="size">{size_str}</td>
                        <td><a href="/{filename}">Download</a></td>
                    </tr>
                """
            
            html += """
                </table>
            </body>
            </html>
            """
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def format_size(self, size):
        """فرمت حجم فایل"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def log_message(self, format, *args):
        """لاگ درخواست‌ها"""
        print(f"[{self.address_string()}] {format % args}")


def get_local_ip():
    """پیدا کردن IP لوکال"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def main():
    PORT = 8000
    
    print("=" * 60)
    print("🚀 File Server Starting...")
    print("=" * 60)
    
    # نمایش فایل‌های موجود
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    print(f"\n📦 {len(files)} files available in current directory:")
    for f in files[:10]:  # نمایش 10 فایل اول
        size = os.path.getsize(f)
        print(f"  • {f} ({size:,} bytes)")
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")
    
    # نمایش آدرس‌های قابل استفاده
    local_ip = get_local_ip()
    print(f"\n🌐 Server URLs:")
    print(f"  Local:   http://localhost:{PORT}")
    print(f"  Network: http://{local_ip}:{PORT}")
    print(f"\n💡 Use this URL in ESP32 code:")
    print(f"   http://{local_ip}:{PORT}/filename.ext")
    print("\n" + "=" * 60)
    print("Press Ctrl+C to stop server")
    print("=" * 60 + "\n")
    
    # شروع سرور
    server = HTTPServer(('0.0.0.0', PORT), FileServer)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⛔ Server stopped by user")
        server.shutdown()


if __name__ == '__main__':
    main()