import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# Configuration email
EMAIL_USER = os.environ.get('EMAIL_USER', '')
EMAIL_PASS = os.environ.get('EMAIL_PASS', '')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')

def get_db_path():
    """Obtenir le chemin de la base de données selon l'environnement"""
    if os.environ.get('RENDER'):
        # Sur Render, utiliser le répertoire /opt/render/project/src
        return '/opt/render/project/src/messages.db'
    else:
        # En local, utiliser le répertoire courant
        return 'messages.db'

def init_database():
    """Initialise la base de données SQLite"""
    try:
        db_path = get_db_path()
        print(f"🔧 Initialisation BDD: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Créer la table messages si elle n'existe pas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de données initialisée avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur initialisation BDD: {e}")
        return False

def save_message_to_db(name, email, message, timestamp):
    """Sauvegarde un message dans la base de données"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (name, email, message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (name, email, message, timestamp))
        
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Message {message_id} sauvegardé en base de données")
        return message_id
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde en BDD: {e}")
        return None

def get_messages_from_db():
    """Récupère tous les messages de la base de données"""
    try:
        db_path = get_db_path()
        
        # Initialiser la BDD si elle n'existe pas
        if not os.path.exists(db_path):
            print("🔧 BDD n'existe pas, initialisation...")
            init_database()
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, message, timestamp, created_at
            FROM messages
            ORDER BY created_at DESC
        ''')
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'message': row[3],
                'timestamp': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        print(f"📊 {len(messages)} messages récupérés de la BDD")
        return messages
    except Exception as e:
        print(f"❌ Erreur lors de la lecture BDD: {e}")
        return []

def send_notification_email(message_data):
    """Envoie une notification email"""
    if not all([EMAIL_USER, EMAIL_PASS, ADMIN_EMAIL]):
        print("⚠️ Configuration email manquante, email non envoyé")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"🔔 Nouveau message Tunelith - {message_data['name']}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #004aad, #ff6600); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <h2>📨 Nouveau Message Tunelith</h2>
                </div>
                <div style="background: white; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px; margin-top: 10px;">
                    <p><strong>👤 Nom:</strong> {message_data['name']}</p>
                    <p><strong>📧 Email:</strong> {message_data['email']}</p>
                    <p><strong>🕒 Date:</strong> {message_data['timestamp']}</p>
                    <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 15px;">
                        <strong>💬 Message:</strong><br>
                        {message_data['message']}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, ADMIN_EMAIL, msg.as_string())
        server.quit()
        
        print(f"✅ Email envoyé à {ADMIN_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur email: {e}")
        return False

@app.route('/')
def home():
    """Page d'accueil principale"""
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    """Traitement des messages du formulaire de contact"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        print(f"📨 Nouveau message reçu de {name} ({email})")
        
        # Validation
        if not all([name, email, message]):
            print("❌ Champs manquants")
            return jsonify({'error': 'Tous les champs sont obligatoires', 'success': False}), 400
        
        if '@' not in email or '.' not in email:
            print("❌ Email invalide")
            return jsonify({'error': 'Adresse email invalide', 'success': False}), 400
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialiser la BDD si nécessaire
        db_path = get_db_path()
        if not os.path.exists(db_path):
            print("🔧 Initialisation de la BDD...")
            init_result = init_database()
            if not init_result:
                return jsonify({'error': 'Erreur d\'initialisation de la base de données', 'success': False}), 500
        
        # Sauvegarder en base de données
        message_id = save_message_to_db(name, email, message, timestamp)
        
        if message_id:
            print(f"✅ Message {message_id} sauvegardé avec succès")
            
            # Préparer les données pour la notification
            message_data = {
                'id': message_id,
                'name': name,
                'email': email,
                'message': message,
                'timestamp': timestamp
            }
            
            # Envoyer notification email (non bloquant si ça échoue)
            email_sent = send_notification_email(message_data)
            
            # Réponse de succès
            response_data = {
                'success': True, 
                'message': 'Message envoyé avec succès!', 
                'id': message_id,
                'email_sent': email_sent
            }
            
            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(response_data)
            else:
                # Sinon, rediriger vers la page d'accueil
                return redirect(url_for('home'))
        else:
            print("❌ Échec de la sauvegarde")
            return jsonify({'error': 'Erreur lors de la sauvegarde', 'success': False}), 500
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return jsonify({'error': 'Erreur interne du serveur', 'success': False}), 500

@app.route('/messages')
def view_messages():
    """Page d'administration des messages"""
    try:
        messages = get_messages_from_db()
        print(f"📋 Affichage de {len(messages)} messages")
        return render_template('messages.html', messages=messages)
    except Exception as e:
        print(f"❌ Erreur lors de l'affichage: {e}")
        return f"Erreur lors du chargement des messages: {e}", 500

@app.route('/api/messages')
def api_messages():
    """API pour récupérer les messages en JSON"""
    try:
        messages = get_messages_from_db()
        return jsonify({
            'success': True,
            'count': len(messages),
            'messages': messages
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/test_db')
def test_database():
    """Route de test pour vérifier la base de données"""
    try:
        db_path = get_db_path()
        
        # S'assurer que la BDD existe
        if not os.path.exists(db_path):
            print("🔧 BDD n'existe pas, création...")
            init_result = init_database()
            if not init_result:
                return jsonify({
                    'database_status': 'ERROR',
                    'error': 'Impossible de créer la base de données',
                    'db_path': db_path
                }), 500
        
        messages = get_messages_from_db()
        return jsonify({
            'database_status': 'OK',
            'messages_count': len(messages),
            'database_exists': os.path.exists(db_path),
            'db_path': db_path,
            'environment': 'Render' if os.environ.get('RENDER') else 'Local',
            'recent_messages': messages[:3] if messages else []
        })
    except Exception as e:
        return jsonify({
            'database_status': 'ERROR',
            'error': str(e),
            'db_path': get_db_path()
        }), 500

@app.route('/health')
def health_check():
    """Contrôle de santé avec info base de données"""
    try:
        messages_count = len(get_messages_from_db())
        db_path = get_db_path()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'messages_in_db': messages_count,
            'database_exists': os.path.exists(db_path),
            'database_path': db_path,
            'email_configured': bool(EMAIL_USER and EMAIL_PASS and ADMIN_EMAIL),
            'environment': 'Render' if os.environ.get('RENDER') else 'Local',
            'version': '2.2'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/debug')
def debug_info():
    """Informations de debug"""
    try:
        db_path = get_db_path()
        current_dir = os.getcwd()
        
        return jsonify({
            'python_version': os.sys.version,
            'current_directory': current_dir,
            'files_in_directory': [f for f in os.listdir('.') if not f.startswith('.')],
            'database_exists': os.path.exists(db_path),
            'database_path': db_path,
            'environment_vars': {
                'EMAIL_USER': bool(EMAIL_USER),
                'EMAIL_PASS': bool(EMAIL_PASS),
                'ADMIN_EMAIL': bool(ADMIN_EMAIL),
                'PORT': os.environ.get('PORT', 'Not set'),
                'RENDER': os.environ.get('RENDER', 'Not on Render')
            },
            'flask_version': '2.3+',
            'writable_directories': check_writable_dirs()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_writable_dirs():
    """Vérifier les répertoires où on peut écrire"""
    test_dirs = ['.', '/tmp', '/opt/render/project/src']
    writable = {}
    
    for dir_path in test_dirs:
        try:
            if os.path.exists(dir_path):
                test_file = os.path.join(dir_path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                writable[dir_path] = True
            else:
                writable[dir_path] = False
        except:
            writable[dir_path] = False
    
    return writable

# Initialiser la base de données au démarrage
try:
    print("🚀 Initialisation de l'application Tunelith...")
    init_database()
    print("✅ Application prête!")
except Exception as e:
    print(f"❌ Erreur lors de l'initialisation: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🚀 Démarrage Tunelith")
    print(f"📊 Environment: {'Render' if os.environ.get('RENDER') else 'Local'}")
    print(f"📁 Database path: {get_db_path()}")
    print(f"🌐 Port: {port}")
    print(f"🔍 Debug mode: {debug_mode}")
    print(f"📧 Email configured: {bool(EMAIL_USER and EMAIL_PASS and ADMIN_EMAIL)}")
    
    if not os.environ.get('RENDER'):
        print(f"📊 Test URLs:")
        print(f"   - Site: http://localhost:{port}/")
        print(f"   - Messages: http://localhost:{port}/messages")
        print(f"   - Test DB: http://localhost:{port}/test_db")
        print(f"   - Health: http://localhost:{port}/health")
        print(f"   - Debug: http://localhost:{port}/debug")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
