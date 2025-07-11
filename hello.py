# hello.py
import cherrypy
import os
import uuid
import datetime
from jinja2 import Environment, FileSystemLoader
from werkzeug.security import generate_password_hash, check_password_hash # Untuk hashing password

# Import fungsi DB dari db.py
from db import (
    get_user_by_username, get_user_by_id, add_user, update_user, delete_user,
    get_post_by_id, add_post, get_posts_by_user, update_post, delete_post,
    get_all_users, get_all_posts_with_username, get_post_counts_by_date,
    search_posts # Pastikan search_posts mengembalikan username dari join
)

# Konfigurasi Jinja2 Environment
env = Environment(loader=FileSystemLoader('template'))

# Helper function to render templates
def render_template(template_name, **kwargs):
    template = env.get_template(template_name)
    # Tambahkan 'request' dan 'session' ke setiap render untuk akses mudah di template
    return template.render(request=cherrypy.request, session=cherrypy.session, **kwargs)

# --- Decorators for authentication and authorization ---
def login_required(f):
    @cherrypy.expose
    def wrapper(*args, **kwargs):
        if 'user_id' not in cherrypy.session: # Ganti 'username' menjadi 'user_id'
            cherrypy.session['flash'] = {'message': 'Silakan login untuk mengakses halaman ini.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/login')
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @cherrypy.expose
    def wrapper(*args, **kwargs):
        if not cherrypy.session.get('user_id') or cherrypy.session.get('role') != 'admin':
            cherrypy.session['flash'] = {'message': 'Anda tidak memiliki izin akses halaman ini.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/') # Redirect ke home atau halaman 403
        return f(*args, **kwargs)
    return wrapper

# --- CherryPy Tool for Flash Messages (optional, but good practice) ---
class FlashMessagesTool(cherrypy.Tool):
    def __init__(self):
        cherrypy.Tool.__init__(self, 'before_handler', self.get_flash)

    def get_flash(self):
        flash_message = cherrypy.session.pop('flash', None)
        if flash_message:
            cherrypy.request.flash = flash_message # Attach to request object for template access
        else:
            cherrypy.request.flash = None # Ensure it's always set

cherrypy.tools.flash = FlashMessagesTool()

# --- Allowed Extensions for Uploads ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Main Application Class ---
class Root:
    def __init__(self):
        # Mount the Admin functionality as a sub-application
        self.admin = self.Admin()
        # You might also want to mount other sub-applications here
        # self.profile_page = self.UserProfile()

    # Route untuk halaman utama
    @cherrypy.expose
    def index(self):
        # Ambil flash message dari session untuk ditampilkan
        flash_message = cherrypy.request.flash 
        
        if 'user_id' in cherrypy.session:
            user_id = cherrypy.session['user_id']
            username = cherrypy.session['username']
            # Menggunakan get_posts_by_user dari db.py
            user_posts = get_posts_by_user(user_id) 
            return render_template('content.html', 
                                   page_type='user_dashboard', 
                                   username=username, 
                                   posts=user_posts, 
                                   flash_message=flash_message)
        else:
            team_members = [
    "Muhammad Aldhyo Nur Arif (231080200050)",
    "Muhammad Raihan Firdaus (231080200025)",
    "Revangga Daffa Jala Putra (23080200117)",
    "Donni Adeleo Ardana (231080200055)",
    "Hamdani Bagus Pradana (231080200095)",
    "Candra Dwi Prayogi (231080200089)",
    "Ricky Firmansyah (231080200072)",
    "Ryan Danuarta (231080200110)",
    "Ahmad Isvander Adhi Saputra (231080200060)"
]

        return render_template('content.html', 
                               page_type='home', 
                               team_members=team_members, 
                               flash_message=flash_message)


    # Route untuk halaman registrasi
    @cherrypy.expose
    def register(self, username=None, password=None, email=None):
        flash_message = cherrypy.request.flash
        if cherrypy.request.method == 'POST':
            if not username or not password or not email:
                cherrypy.session['flash'] = {'message': 'Semua field harus diisi.', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/register') # <--- Redirect jika field kosong
            
            # Ini yang paling mungkin terjadi:
            if get_user_by_username(username):
                cherrypy.session['flash'] = {'message': 'Username sudah digunakan.', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/register') # <--- Redirect jika username duplikat
            
            try:
                hashed_password = generate_password_hash(password)
                add_user(username, hashed_password, email, 'user')
                cherrypy.session['flash'] = {'message': 'Registrasi berhasil! Silakan login.', 'category': 'success'}
                raise cherrypy.HTTPRedirect('/login') # <--- Redirect jika sukses
            except Exception as e:
                cherrypy.session['flash'] = {'message': f'Registrasi gagal: {e}', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/register') # <--- Redirect jika ada error DB lain

        return render_template('content.html', page_type='register', flash_message=flash_message)

    # Route untuk halaman login
    @cherrypy.expose
    def login(self, username=None, password=None):
        flash_message = cherrypy.request.flash
        if cherrypy.request.method == 'POST':
            if not username or not password:
                cherrypy.session['flash'] = {'message': 'Username dan password harus diisi.', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/login')

            user = get_user_by_username(username)
            if user and check_password_hash(user['password'], password): # Verifikasi password hash
                cherrypy.session['user_id'] = user['id']
                cherrypy.session['username'] = user['username']
                cherrypy.session['role'] = user['role']
                cherrypy.session['flash'] = {'message': f'Selamat datang, {user["username"]}!', 'category': 'success'}
                raise cherrypy.HTTPRedirect('/') # Redirect ke halaman utama setelah login
            else:
                cherrypy.session['flash'] = {'message': 'Username atau password salah.', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/login')
        
        return render_template('content.html', page_type='login', flash_message=flash_message)

    # Route untuk logout
    @cherrypy.expose
    @login_required
    def logout(self):
        cherrypy.session.clear()
        cherrypy.session['flash'] = {'message': 'Anda telah logout.', 'category': 'info'}
        raise cherrypy.HTTPRedirect('/')

    # Route untuk post message baru
    @cherrypy.expose
    @login_required
    def post_message(self, text_content, image=None): # Ganti 'message' jadi 'text_content'
        if not text_content:
            cherrypy.session['flash'] = {'message': 'Isi pesan tidak boleh kosong.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/')

        user_id = cherrypy.session['user_id']
        image_filename = None

        if image and hasattr(image, 'file') and image.filename:
            if allowed_file(image.filename):
                ext = os.path.splitext(image.filename)[1]
                unique_name = str(uuid.uuid4()) + ext
                save_path = os.path.join(cherrypy.config.get('UPLOAD_FOLDER'), unique_name)

                try:
                    with open(save_path, 'wb') as out:
                        while True: # Baca file dalam chunk
                            data = image.file.read(8192)
                            if not data:
                                break
                            out.write(data)
                    image_filename = unique_name
                except Exception as e:
                    cherrypy.session['flash'] = {'message': f'Gagal mengupload gambar: {e}', 'category': 'danger'}
                    raise cherrypy.HTTPRedirect('/')
            else:
                cherrypy.session['flash'] = {'message': 'Format gambar tidak didukung.', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/')

        add_post(user_id, text_content, image_filename) # Gunakan fungsi add_post dari db.py
        cherrypy.session['flash'] = {'message': 'Pesan berhasil diposting!', 'category': 'success'}
        raise cherrypy.HTTPRedirect('/')

    # Route untuk edit profil
    @cherrypy.expose
    @login_required
    def edit_profile(self):
        flash_message = cherrypy.request.flash
        user = get_user_by_id(cherrypy.session['user_id'])
        if not user: # Seharusnya tidak terjadi jika login_required
            cherrypy.session['flash'] = {'message': 'User tidak ditemukan.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/')

        return render_template('content.html', page_type='edit_profile', user=user, flash_message=flash_message)

    # Route untuk update profil
    @cherrypy.expose
    @login_required
    def update_profile(self, email):
        user_id = cherrypy.session['user_id']
        # Anda bisa menambahkan update username atau password di sini jika diinginkan
        update_user(user_id, email=email) # Menggunakan fungsi update_user dari db.py
        cherrypy.session['flash'] = {'message': 'Profil berhasil diperbarui.', 'category': 'success'}
        raise cherrypy.HTTPRedirect('/')

    # Route untuk edit post tertentu
    @cherrypy.expose
    @login_required
    def edit_post(self, post_id):
        flash_message = cherrypy.request.flash
        post = get_post_by_id(post_id)
        
        # Pastikan user yang login adalah pemilik post atau admin
        if not post or (post['user_id'] != cherrypy.session['user_id'] and cherrypy.session['role'] != 'admin'):
            cherrypy.session['flash'] = {'message': 'Post tidak ditemukan atau Anda tidak memiliki izin.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/')
        
        return render_template('content.html', page_type='edit_post', post=post, flash_message=flash_message)

    # Route untuk update post
    @cherrypy.expose
    @login_required
    def update_post(self, post_id, text_content, new_image=None, delete_current_image=None):
        flash_message = cherrypy.request.flash
        current_post = get_post_by_id(post_id)
        
        if not current_post or (current_post['user_id'] != cherrypy.session['user_id'] and cherrypy.session['role'] != 'admin'):
            cherrypy.session['flash'] = {'message': 'Post tidak ditemukan atau Anda tidak memiliki izin.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/')

        image_filename = current_post['image_filename']

        # Hapus gambar saat ini jika diminta
        if delete_current_image == 'on' and image_filename:
            filepath = os.path.join(cherrypy.config.get('UPLOAD_FOLDER'), image_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            image_filename = None # Set ke None karena gambar dihapus

        # Upload gambar baru jika ada
        if new_image and hasattr(new_image, 'file') and new_image.filename:
            if allowed_file(new_image.filename):
                # Hapus gambar lama jika ada dan baru diupload
                if image_filename and not (delete_current_image == 'on'): # Jika belum dihapus karena checkbox
                    filepath = os.path.join(cherrypy.config.get('UPLOAD_FOLDER'), image_filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        
                ext = os.path.splitext(new_image.filename)[1]
                unique_name = str(uuid.uuid4()) + ext
                save_path = os.path.join(cherrypy.config.get('UPLOAD_FOLDER'), unique_name)
                with open(save_path, 'wb') as out:
                    while True:
                        data = new_image.file.read(8192)
                        if not data:
                            break
                        out.write(data)
                image_filename = unique_name
            else:
                cherrypy.session['flash'] = {'message': 'Format gambar baru tidak didukung.', 'category': 'warning'}
                # Tetap di halaman edit, atau redirect dengan pesan
                raise cherrypy.HTTPRedirect(f'/edit_post/{post_id}')
        
        update_post(post_id, text_content, image_filename) # Gunakan fungsi update_post dari db.py
        cherrypy.session['flash'] = {'message': 'Post berhasil diperbarui!', 'category': 'success'}
        raise cherrypy.HTTPRedirect('/')

    # Route untuk delete post
    @cherrypy.expose
    @login_required
    def delete_post(self, post_id):
        # Pastikan user yang login adalah pemilik post atau admin
        post_to_delete = get_post_by_id(post_id)
        if not post_to_delete or (post_to_delete['user_id'] != cherrypy.session['user_id'] and cherrypy.session['role'] != 'admin'):
            cherrypy.session['flash'] = {'message': 'Post tidak ditemukan atau Anda tidak memiliki izin untuk menghapus.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/')

        delete_post(post_id) # Menggunakan fungsi delete_post dari db.py
        cherrypy.session['flash'] = {'message': 'Post berhasil dihapus!', 'category': 'success'}
        raise cherrypy.HTTPRedirect('/')

    # Route untuk pencarian post
    @cherrypy.expose
    def search(self, keyword=""):
        flash_message = cherrypy.request.flash
        results = []
        if keyword:
            results = search_posts(keyword) # Menggunakan fungsi search_posts dari db.py
        
        return render_template('content.html', page_type='search_results', keyword=keyword, results=results, flash_message=flash_message)

    # Route untuk profil user (view only)
    @cherrypy.expose
    def profile(self, username):
        flash_message = cherrypy.request.flash
        user = get_user_by_username(username)
        if not user:
            cherrypy.session['flash'] = {'message': 'Profil user tidak ditemukan.', 'category': 'danger'}
            raise cherrypy.HTTPRedirect('/')
        
        posts = get_posts_by_user(user['id']) # Menggunakan get_posts_by_user
        return render_template('content.html', page_type='user_profile_view', profile_user=user, posts=posts, flash_message=flash_message)


    # --- Admin Sub-aplikasi (Nested Class) ---
    class Admin:
        @cherrypy.expose
        @admin_required
        def index(self): # Akan diakses sebagai /admin/
            flash_message = cherrypy.request.flash
            users = get_all_users()
            posts = get_all_posts_with_username() # Menggunakan fungsi yang sudah di-join
            post_stats = get_post_counts_by_date()

            return render_template('content.html', 
                                   page_type='admin_dashboard', 
                                   users=users, 
                                   posts=posts, 
                                   post_stats=post_stats, 
                                   flash_message=flash_message)

        @cherrypy.expose
        @admin_required
        def delete_user(self, user_id):
            # Mencegah admin menghapus akunnya sendiri
            if int(user_id) == cherrypy.session['user_id']:
                cherrypy.session['flash'] = {'message': 'Anda tidak bisa menghapus akun admin Anda sendiri!', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/admin/')

            user_to_delete = get_user_by_id(user_id)
            if not user_to_delete:
                cherrypy.session['flash'] = {'message': 'User tidak ditemukan.', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/admin/')

            # Fungsi delete_user di db.py sudah menangani penghapusan post dan gambar terkait
            delete_user(user_id)
            cherrypy.session['flash'] = {'message': f'User "{user_to_delete["username"]}" dan semua postingannya berhasil dihapus.', 'category': 'success'}
            raise cherrypy.HTTPRedirect('/admin/')

        @cherrypy.expose
        @admin_required
        def delete_post(self, post_id):
            post_to_delete = get_post_by_id(post_id)
            if not post_to_delete:
                cherrypy.session['flash'] = {'message': 'Post tidak ditemukan.', 'category': 'danger'}
                raise cherrypy.HTTPRedirect('/admin/')
            
            # Fungsi delete_post di db.py sudah menangani penghapusan gambar terkait
            delete_post(post_id)
            cherrypy.session['flash'] = {'message': 'Post berhasil dihapus oleh admin.', 'category': 'success'}
            raise cherrypy.HTTPRedirect('/admin/')