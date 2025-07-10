import os
import cherrypy
from hello import Root
from db import init_db

BASE_DIR = os.path.abspath(".")
SESSION_DIR = os.path.join(BASE_DIR, "sessions")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(SESSION_DIR, exist_ok=True)# app.py
import os
import cherrypy
from hello import Root # Ganti HelloWorld menjadi Root
from db import init_db

BASE_DIR = os.path.abspath(".")
SESSION_DIR = os.path.join(BASE_DIR, "sessions")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

if __name__ == '__main__':
    # Pastikan database diinisialisasi sebelum CherryPy dimulai
    init_db()

    cherrypy.config.update({
        'tools.sessions.on': True,
        'tools.sessions.storage_type': 'file',
        'tools.sessions.storage_path': SESSION_DIR,
        'tools.sessions.timeout': 60, # Session timeout in minutes
        'server.socket_host': '0.0.0.0', # Mengizinkan akses dari mana saja (untuk pengembangan)
        'server.socket_port': 8080,
        'UPLOAD_FOLDER': UPLOAD_DIR, # Tambahkan ini agar bisa diakses di hello.py
    })

    # Mount aplikasi utama Anda
    cherrypy.quickstart(Root(), '/', { # Ganti HelloWorld() menjadi Root()
        '/': {
            'tools.sessions.on': True,
            'tools.flash.on': True, # Mengaktifkan flash message tool
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(BASE_DIR, 'static')
        }
    })
os.makedirs(UPLOAD_DIR, exist_ok=True)

if __name__ == '__main__':
    init_db()

    cherrypy.config.update({
        'tools.sessions.on': True,
        'tools.sessions.storage_type': 'file',
        'tools.sessions.storage_path': SESSION_DIR,
        'tools.sessions.timeout': 60,
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 8080,
        'UPLOAD_FOLDER': UPLOAD_DIR, # Tambahkan ini juga, penting untuk hello.py
    })

    cherrypy.quickstart(Root(), '/', { # <-- BARIS INI BERUBAH
        '/': {
            'tools.sessions.on': True,
            'tools.flash.on': True, # Pastikan ini juga ada jika Anda pakai flash messages
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(BASE_DIR, 'static')
        }
    })
