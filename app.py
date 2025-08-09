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

def init_database():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect('messages.db')
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
    print("✅ Base de données initialisée")

def save_message_to_db(name, email, message, timestamp):
    """Sauvegarde un message dans la base de données"""
    try:
        conn = sqlite3.connect('messages.db')
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
        conn = sqlite3.connect('messages.db')
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
        return messages
    except Exception as e:
        print(f"❌ Erreur lors de la lecture BDD: {e}")
        return []

def send_notification_email(message_data):
    """Envoie une notification email"""
    if not all([EMAIL_USER, EMAIL_PASS, ADMIN_EMAIL]):
        print("⚠️ Configuration email manquante")
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
                    <p style="margin-top: 20px;">
                        <a href="https://votre-app.onrender.com/messages" 
                           style="background: #ff6600; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                           Voir tous les messages
                        </a>
                    </p>
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
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        print(f"📨 Nouveau message reçu de {name} ({email})")
        
        # Validation
        if not all([name, email, message]):
            print("❌ Champs manquants")
            return jsonify({'error': 'Tous les champs sont obligatoires'}), 400
        
        if '@' not in email or '.' not in email:
            print("❌ Email invalide")
            return jsonify({'error': 'Adresse email invalide'}), 400
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
            
            # Envoyer notification email
            send_notification_email(message_data)
            
            # Réponse de succès
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': True, 'message': 'Message envoyé avec succès!', 'id': message_id})
            else:
                return redirect(url_for('home'))
        else:
            print("❌ Échec de la sauvegarde")
            return jsonify({'error': 'Erreur lors de la sauvegarde'}), 500
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/messages')
def view_messages():
    """Page d'administration des messages"""
    try:
        messages = get_messages_from_db()
        print(f"📋 {len(messages)} messages trouvés en base")
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
        return jsonify({'error': str(e)}), 500

@app.route('/test_db')
def test_database():
    """Route de test pour vérifier la base de données"""
    try:
        messages = get_messages_from_db()
        return jsonify({
            'database_status': 'OK',
            'messages_count': len(messages),
            'messages': messages
        })
    except Exception as e:
        return jsonify({
            'database_status': 'ERROR',
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Contrôle de santé avec info base de données"""
    try:
        messages_count = len(get_messages_from_db())
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'messages_in_db': messages_count,
            'version': '2.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Initialiser la base de données au démarrage
@app.before_first_request
def before_first_request():
    init_database()

if __name__ == "__main__":
    # Initialiser la BDD en mode développement
    init_database()
    
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🚀 Démarrage Tunelith avec base de données SQLite")
    print(f"📊 URL de test: http://localhost:{port}/test_db")
    print(f"📧 Page messages: http://localhost:{port}/messages")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
