import sqlite3
import os
from werkzeug.security import generate_password_hash # Import untuk hashing password

DB_NAME = "users.db" # Tetap menggunakan users.db

def get_db_connection():
    """Membuka koneksi ke database SQLite"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Memungkinkan akses kolom berdasarkan nama
    return conn

def delete_old_database():
    """Menghapus database lama jika ada"""
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("\U0001F5D1️ Database lama berhasil dihapus!")
    else:
        print("✅ Tidak ada database lama, lanjut membuat yang baru.")

def init_db():
    """Inisialisasi database: Buat ulang tabel jika perlu"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Buat tabel users jika belum ada
    # Tambahkan kolom 'role' dan 'created_at'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, -- Tambahkan UNIQUE
            password TEXT NOT NULL,
            email TEXT UNIQUE, -- Tambahkan UNIQUE
            role TEXT NOT NULL DEFAULT 'user', -- Default role 'user'
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Buat tabel posts (sebelumnya messages) jika belum ada
    # Ubah 'username' menjadi 'user_id' (FOREIGN KEY)
    # Ubah 'message' menjadi 'text_content'
    # Ubah 'image_url' menjadi 'image_filename'
    # Ubah 'timestamp' menjadi 'created_at', tambah 'updated_at'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, -- Kunci asing ke tabel users
            text_content TEXT NOT NULL,
            image_filename TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Tambah akun admin default jika belum ada
    # PASTIKAN PASSWORD DI-HASH!
    admin_exist = conn.execute("SELECT 1 FROM users WHERE username = 'admin'").fetchone() # Periksa lebih efisien
    if not admin_exist:
        hashed_admin_password = generate_password_hash('admin123') # HASH PASSWORD
        conn.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                     ('admin', hashed_admin_password, 'admin@example.com', 'admin'))
        print("✅ Akun admin default 'admin' (password: admin123) berhasil ditambahkan!")
    else:
        print("ℹ️ Akun admin default sudah ada.")
    
    conn.commit()
    conn.close()

# --- Fungsi User ---

def add_user(username, hashed_password, email=None, role='user'):
    """Menambahkan user baru ke database."""
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                 (username, hashed_password, email, role))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    """Mengambil data user berdasarkan username."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Mengambil data user berdasarkan ID."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def get_all_users():
    """Mengambil data semua pengguna."""
    conn = get_db_connection()
    # Pilih kolom yang relevan, jangan password
    users = conn.execute('SELECT id, username, email, role, created_at FROM users').fetchall()
    conn.close()
    return users

def delete_user(user_id):
    """Menghapus pengguna berdasarkan ID. Posts terkait akan terhapus otomatis karena ON DELETE CASCADE."""
    conn = get_db_connection()
    # Anda mungkin ingin mendapatkan nama pengguna atau file gambar yang perlu dihapus dari disk sebelum menghapus user
    # Implementasi penghapusan file gambar yang terkait dengan postingan user yang akan dihapus:
    posts_to_delete_images = conn.execute("SELECT image_filename FROM posts WHERE user_id = ?", (user_id,)).fetchall()
    
    # Hapus user (ini akan memicu ON DELETE CASCADE pada tabel posts)
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    # Hapus file gambar setelah transaksi DB
    UPLOAD_DIR = os.path.join(os.path.abspath("."), "static", "uploads") # Pastikan path ini benar
    for post in posts_to_delete_images:
        if post['image_filename']:
            filepath = os.path.join(UPLOAD_DIR, post['image_filename'])
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"🗑️ Deleted image: {post['image_filename']}")
                except OSError as e:
                    print(f"❌ Error deleting image {post['image_filename']}: {e}")
    return True


def update_user(user_id, username=None, email=None, role=None): # Tambah role
    """Mengupdate data pengguna"""
    conn = get_db_connection()
    update_fields = []
    params = []
    
    if username:
        update_fields.append("username = ?")
        params.append(username)
    if email:
        update_fields.append("email = ?")
        params.append(email)
    if role: # Tambah update role
        update_fields.append("role = ?")
        params.append(role)
    
    if update_fields:
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        params.append(user_id)
        conn.execute(query, params)
        conn.commit()
    
    conn.close()
    return True


# --- Fungsi Post ---

def add_post(user_id, text_content, image_filename=None):
    """Menambahkan post baru."""
    conn = get_db_connection()
    conn.execute("INSERT INTO posts (user_id, text_content, image_filename) VALUES (?, ?, ?)",
                 (user_id, text_content, image_filename))
    conn.commit()
    conn.close()

def get_post_by_id(post_id):
    """Mengambil 1 post berdasarkan ID."""
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    return post

def get_posts_by_user(user_id):
    """Mengambil semua post oleh user tertentu."""
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return posts

def update_post(post_id, new_text_content, new_image_filename): # Sesuaikan nama parameter
    """Mengupdate post."""
    conn = get_db_connection()
    conn.execute('''
        UPDATE posts 
        SET text_content = ?, image_filename = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (new_text_content, new_image_filename, post_id))
    conn.commit()
    conn.close()
    return True

def delete_post(post_id):
    """Menghapus post berdasarkan ID."""
    conn = get_db_connection()
    # Sebelum menghapus dari DB, ambil nama file gambar untuk dihapus dari disk
    post = conn.execute('SELECT image_filename FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

    # Hapus file gambar dari disk jika ada
    if post and post['image_filename']:
        UPLOAD_DIR = os.path.join(os.path.abspath("."), "static", "uploads") # Pastikan path ini benar
        filepath = os.path.join(UPLOAD_DIR, post['image_filename'])
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"🗑️ Deleted image: {post['image_filename']}")
            except OSError as e:
                print(f"❌ Error deleting image {post['image_filename']}: {e}")
    return True

def get_all_posts():
    """Mengambil semua post."""
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return posts

def get_all_posts_with_username():
    """Mengambil semua post dengan informasi username dari user yang memposting."""
    conn = get_db_connection()
    posts = conn.execute("""
        SELECT 
            p.id, p.user_id, p.text_content, p.image_filename, 
            p.created_at, p.updated_at,
            u.username 
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()
    return posts

def get_post_counts_by_date():
    """Menghitung jumlah post per tanggal (untuk statistik admin)."""
    conn = get_db_connection()
    result = conn.execute('''
        SELECT 
            STRFTIME('%Y-%m-%d', created_at) AS date, 
            COUNT(id) AS count
        FROM posts
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7 -- Ambil 7 hari terakhir sebagai contoh
    ''').fetchall()
    conn.close()
    return result

def search_posts(keyword, limit=10, offset=0):
    """Mencari post berdasarkan kata kunci (dalam konten atau username)."""
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT 
            p.id, p.user_id, p.text_content, p.image_filename, p.created_at, p.updated_at,
            u.username
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.text_content LIKE ? OR u.username LIKE ?
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
    ''', (f'%{keyword}%', f'%{keyword}%', limit, offset))
    
    posts = cursor.fetchall()
    conn.close()
    return posts

# Fungsi `get_user_profile` di sini sebenarnya duplikat dari `get_posts_by_user`
# Jika `get_user_profile` dimaksudkan untuk juga mendapatkan data profil user itu sendiri, 
# maka perlu diubah. Untuk saat ini, saya asumsikan `get_posts_by_user` sudah cukup.
# Jika Anda tetap ingin `get_user_profile` yang mengembalikan detail user DAN post-nya, 
# maka logicnya harus dipisah atau diubah.
# Untuk saat ini, saya akan menghapus `get_user_profile` yang lama karena mirip `get_posts_by_user`.

if __name__ == "__main__":
    pilihan = input("❗ Apakah Anda ingin menghapus database lama? (y/n): ").strip().lower()
    if pilihan == "y":
        delete_old_database()

    init_db()
    print("✅ Database berhasil diinisialisasi!")