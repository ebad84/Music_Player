# ftp_server.py - سرور FTP ساده برای ESP32
# این فایل را روی ESP32 آپلود کنید و اجرا کنید

import socket
import network
import os
import time

class SimpleFTPServer:
    def __init__(self, port=21):
        self.port = port
        self.cwd = '/'
        self.pasv_port = 50000
        
    def start(self):
        # نمایش IP آدرس
        sta_if = network.WLAN(network.STA_IF)
        print('FTP Server starting...')
        print('IP Address:', sta_if.ifconfig()[0])
        print('Port:', self.port)
        print('Username: esp32')
        print('Password: esp32')
        
        addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        
        print('FTP Server is ready!')
        
        while True:
            try:
                cl, addr = s.accept()
                print('Client connected from', addr)
                self.handle_client(cl)
            except Exception as e:
                print('Error:', e)
    
    def handle_client(self, client):
        client.send(b'220 ESP32 FTP Server\r\n')
        dataclient = None
        
        while True:
            try:
                data = client.recv(1024).decode('utf-8').strip()
                if not data:
                    break
                    
                print('Command:', data)
                cmd = data.split()[0].upper()
                
                if cmd == 'USER':
                    client.send(b'331 Password required\r\n')
                    
                elif cmd == 'PASS':
                    client.send(b'230 Logged in\r\n')
                    
                elif cmd == 'SYST':
                    client.send(b'215 UNIX Type: L8\r\n')
                    
                elif cmd == 'PWD':
                    client.send(f'257 "{self.cwd}"\r\n'.encode())
                    
                elif cmd == 'TYPE':
                    client.send(b'200 Type set\r\n')
                    
                elif cmd == 'PASV':
                    # Passive mode
                    self.pasv_port += 1
                    if self.pasv_port > 51000:
                        self.pasv_port = 50000
                    
                    dataclient = socket.socket()
                    dataclient.bind(('0.0.0.0', self.pasv_port))
                    dataclient.listen(1)
                    
                    sta_if = network.WLAN(network.STA_IF)
                    ip = sta_if.ifconfig()[0]
                    ip_parts = ip.split('.')
                    p1 = self.pasv_port >> 8
                    p2 = self.pasv_port & 0xff
                    
                    client.send(f'227 Entering Passive Mode ({ip_parts[0]},{ip_parts[1]},{ip_parts[2]},{ip_parts[3]},{p1},{p2})\r\n'.encode())
                    
                elif cmd == 'LIST':
                    if dataclient:
                        client.send(b'150 Opening data connection\r\n')
                        dc, _ = dataclient.accept()
                        
                        try:
                            files = os.listdir(self.cwd)
                            for f in files:
                                try:
                                    stat = os.stat(self.cwd + '/' + f if self.cwd != '/' else '/' + f)
                                    is_dir = stat[0] & 0x4000
                                    size = stat[6]
                                    dc.send(f'{"d" if is_dir else "-"}rwxr-xr-x 1 owner group {size} Jan 1 00:00 {f}\r\n'.encode())
                                except:
                                    pass
                        except:
                            pass
                        
                        dc.close()
                        dataclient.close()
                        dataclient = None
                        client.send(b'226 Transfer complete\r\n')
                    
                elif cmd == 'CWD':
                    path = data.split(None, 1)[1] if len(data.split()) > 1 else '/'
                    try:
                        if path == '..':
                            self.cwd = '/' if self.cwd == '/' else '/'.join(self.cwd.split('/')[:-1]) or '/'
                        elif path.startswith('/'):
                            self.cwd = path
                        else:
                            self.cwd = self.cwd + '/' + path if self.cwd != '/' else '/' + path
                        client.send(b'250 Directory changed\r\n')
                    except:
                        client.send(b'550 Failed to change directory\r\n')
                
                elif cmd == 'STOR':
                    filename = data.split(None, 1)[1]
                    filepath = self.cwd + '/' + filename if self.cwd != '/' else '/' + filename
                    
                    if dataclient:
                        client.send(b'150 Opening data connection\r\n')
                        dc, _ = dataclient.accept()
                        
                        try:
                            with open(filepath, 'wb') as f:
                                while True:
                                    chunk = dc.recv(1024)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                            client.send(b'226 Transfer complete\r\n')
                            print(f'File saved: {filepath}')
                        except Exception as e:
                            client.send(b'550 Failed to save file\r\n')
                            print(f'Error saving file: {e}')
                        
                        dc.close()
                        dataclient.close()
                        dataclient = None
                
                elif cmd == 'RETR':
                    filename = data.split(None, 1)[1]
                    filepath = self.cwd + '/' + filename if self.cwd != '/' else '/' + filename
                    
                    if dataclient:
                        try:
                            client.send(b'150 Opening data connection\r\n')
                            dc, _ = dataclient.accept()
                            
                            with open(filepath, 'rb') as f:
                                while True:
                                    chunk = f.read(1024)
                                    if not chunk:
                                        break
                                    dc.send(chunk)
                            
                            dc.close()
                            dataclient.close()
                            dataclient = None
                            client.send(b'226 Transfer complete\r\n')
                        except:
                            client.send(b'550 File not found\r\n')
                
                elif cmd == 'DELE':
                    filename = data.split(None, 1)[1]
                    filepath = self.cwd + '/' + filename if self.cwd != '/' else '/' + filename
                    try:
                        os.remove(filepath)
                        client.send(b'250 File deleted\r\n')
                    except:
                        client.send(b'550 Failed to delete file\r\n')
                
                elif cmd == 'QUIT':
                    client.send(b'221 Goodbye\r\n')
                    break
                    
                else:
                    client.send(b'502 Command not implemented\r\n')
                    
            except Exception as e:
                print('Error handling command:', e)
                break
        
        client.close()
        if dataclient:
            dataclient.close()

# اجرای سرور
if __name__ == '__main__':
    server = SimpleFTPServer()
    server.start()