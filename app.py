import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, render_template_string
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# Configuration email - MODIFIÉE
EMAIL_USER = os.environ.get('EMAIL_USER', 'hedilfekih15@gmail.com')  # Votre email
EMAIL_PASS = os.environ.get('EMAIL_PASS', '')  # Mot de passe d'application Gmail
ADMIN_EMAIL = 'hedilfekih15@gmail.com'  # Email de destination

# Template HTML pour la page principale
INDEX_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tunelith - Innovation Technologique</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <!-- Votre CSS ici -->
</head>
<body>
    <!-- Votre contenu HTML ici -->
</body>
</html>
"""

# Template pour la page d'administration des messages
MESSAGES_ADMIN_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Messages - Tunelith Admin</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
            margin: 0;
            padding: 2rem;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #004aad, #ff6600);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,74,173,0.3);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #004aad;
        }
        
        .messages-container {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .message-item {
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }
        
        .message-item:hover {
            border-color: #ff6600;
            box-shadow: 0 5px 20px rgba(255,102,0,0.1);
        }
        
        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f1f5f9;
        }
        
        .sender-info {
            font-weight: bold;
            color: #004aad;
        }
        
        .timestamp {
            color: #666;
            font-size: 0.9rem;
        }
        
        .message-content {
            background: #f8fafc;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ff6600;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        
        .back-button {
            background: linear-gradient(45deg, #004aad, #ff6600);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 10px;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 2rem;
            transition: transform 0.3s ease;
        }
        
        .back-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255,102,0,0.4);
            color: white;
            text-decoration: none;
        }
        
        .no-messages {
            text-align: center;
            padding: 3rem;
            color: #666;
        }
        
        .no-messages i {
            font-size: 4rem;
            color: #e2e8f0;
            margin-bottom: 1rem;
        }

        .refresh-button {
            background: linear-gradient(45deg, #22c55e, #16a34a);
            color: white;
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            margin-left: 1rem;
            transition: all 0.3s ease;
        }

        .refresh-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(34,197,94,0.4);
        }

        .email-status {
            padding: 0.5rem 1rem;
            border-radius: 5px;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }

        .email-sent {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }

        .email-failed {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">
            <i class="fas fa-arrow-left"></i> Retour au site
        </a>
        <button onclick="location.reload()" class="refresh-button">
            <i class="fas fa-sync-alt"></i> Actualiser
        </button>
        
        <div class="header">
            <h1><i class="fas fa-envelope"></i> Administration des Messages</h1>
            <p>Gestion des messages reçus via le formulaire de contact</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ messages|length }}</div>
                <div>Messages Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">
                    {% set today = moment().strftime('%Y-%m-%d') if moment else '2024-12-' %}
                    {{ messages|selectattr('timestamp', 'match', '.*' + today + '.*')|list|length }}
                </div>
                <div>Aujourd'hui</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">
                    {% if messages %}
                        {{ messages[0].timestamp.split(' ')[0] if messages[0].timestamp else 'N/A' }}
                    {% else %}
                        N/A
                    {% endif %}
                </div>
                <div>Dernier message</div>
            </div>
        </div>
        
        <div class="messages-container">
            <h2><i class="fas fa-comments"></i> Messages Reçus ({{ messages|length }})</h2>
            
            {% if messages %}
                {% for message in messages %}
                <div class="message-item">
                    <div class="message-header">
                        <div class="sender-info">
                            <i class="fas fa-user"></i> {{ message.name }}
                            <br>
                            <small><i class="fas fa-envelope"></i> {{ message.email }}</small>
                            {% if message.get('email_sent') %}
                                <div class="email-status email-sent">
                                    <i class="fas fa-check"></i> Email envoyé
                                </div>
                            {% else %}
                                <div class="email-status email-failed">
                                    <i class="fas fa-times"></i> Email non envoyé
                                </div>
                            {% endif %}
                        </div>
                        <div class="timestamp">
                            <i class="fas fa-clock"></i> {{ message.timestamp }}
                        </div>
                    </div>
                    <div class="message-content">
                        {{ message.message }}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-messages">
                    <i class="fas fa-inbox"></i>
                    <h3>Aucun message pour le moment</h3>
                    <p>Les messages envoyés via le formulaire de contact apparaîtront ici.</p>
                    <p style="margin-top: 1rem; font-size: 0.9rem; color: #888;">
                        <strong>Debug:</strong> Vérifiez que le formulaire envoie bien les données à /send_message
                    </p>
                </div>
            {% endif %}
        </div>
    </div>

    <script>
        // Auto-refresh toutes les 30 secondes
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""

def init_database():
    """Initialise la base de données SQLite"""
    try:
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        
        # Créer la table messages avec une colonne pour le statut email
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                email_sent BOOLEAN DEFAULT 0,
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

def save_message_to_db(name, email, message, timestamp, email_sent=False):
    """Sauvegarde un message dans la base de données"""
    try:
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (name, email, message, timestamp, email_sent)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, message, timestamp, email_sent))
        
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Message {message_id} sauvegardé: {name} - {email} (Email: {'✓' if email_sent else '✗'})")
        return message_id
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde en BDD: {e}")
        return None

def get_messages_from_db():
    """Récupère tous les messages de la base de données"""
    try:
        if not os.path.exists('messages.db'):
            print("📂 Création de la base de données...")
            init_database()
            
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, message, timestamp, email_sent, created_at
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
                'email_sent': bool(row[5]) if row[5] is not None else False,
                'created_at': row[6]
            })
        
        conn.close()
        print(f"📊 {len(messages)} messages récupérés de la base")
        return messages
    except Exception as e:
        print(f"❌ Erreur lors de la lecture BDD: {e}")
        return []

def send_notification_email(message_data):
    """Envoie une notification email - VERSION AMÉLIORÉE"""
    print(f"🔧 Configuration email:")
    print(f"   EMAIL_USER: {EMAIL_USER}")
    print(f"   EMAIL_PASS: {'***' if EMAIL_PASS else 'VIDE'}")
    print(f"   ADMIN_EMAIL: {ADMIN_EMAIL}")
    
    if not EMAIL_PASS:
        print("⚠️ EMAIL_PASS n'est pas configuré - impossible d'envoyer l'email")
        return False
    
    try:
        # Créer le message email
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_USER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"🔔 Nouveau message Tunelith - {message_data['name']}"
        
        # Corps du message HTML avec design amélioré
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #f8fafc; }}
                .header {{ 
                    background: linear-gradient(135deg, #004aad, #ff6600); 
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ 
                    background: #e3f2fd; 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin: 15px 0;
                    border-left: 4px solid #ff6600;
                }}
                .message-box {{ 
                    background: #f5f5f5; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin: 20px 0;
                    font-style: italic;
                }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📨 Nouveau Message Tunelith</h1>
                    <p>Un nouveau message a été reçu sur votre site web</p>
                </div>
                <div class="content">
                    <div class="info-box">
                        <p><strong>👤 Nom du contact:</strong> {message_data['name']}</p>
                        <p><strong>📧 Email:</strong> {message_data['email']}</p>
                        <p><strong>🕒 Date et heure:</strong> {message_data['timestamp']}</p>
                    </div>
                    
                    <div class="message-box">
                        <strong>💬 Message:</strong><br><br>
                        {message_data['message'].replace('\n', '<br>')}
                    </div>
                    
                    <div class="footer">
                        <p>Ce message a été envoyé automatiquement depuis votre site web Tunelith</p>
                        <p>Pour répondre, utilisez directement l'adresse email: {message_data['email']}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Version texte simple comme fallback
        text_body = f"""
        Nouveau message Tunelith
        
        Nom: {message_data['name']}
        Email: {message_data['email']}
        Date: {message_data['timestamp']}
        
        Message:
        {message_data['message']}
        
        ---
        Message automatique depuis votre site Tunelith
        """
        
        # Attacher les deux versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Configuration SMTP pour Gmail
        print("📤 Connexion au serveur SMTP Gmail...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        
        # Envoyer l'email
        server.sendmail(EMAIL_USER, ADMIN_EMAIL, msg.as_string())
        server.quit()
        
        print(f"✅ Email de notification envoyé avec succès à {ADMIN_EMAIL}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erreur d'authentification SMTP: {e}")
        print("💡 Vérifiez que vous utilisez un 'App Password' pour Gmail")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi d'email: {e}")
        return False

@app.route('/')
def home():
    """Page d'accueil principale"""
    try:
        return render_template('index.html')
    except:
        print("⚠️ Template index.html non trouvé, utilisation du HTML intégré")
        return render_template_string(INDEX_HTML)

@app.route('/send_message', methods=['POST'])
def send_message():
    """Traitement des messages du formulaire de contact - VERSION AMÉLIORÉE"""
    try:
        # Récupérer les données du formulaire
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        print(f"\n📨 NOUVEAU MESSAGE REÇU:")
        print(f"   👤 Nom: {name}")
        print(f"   📧 Email: {email}")
        print(f"   💬 Message: {message[:100]}...")
        
        # Validation des données
        if not all([name, email, message]):
            error_msg = 'Tous les champs sont obligatoires'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        if '@' not in email or '.' not in email:
            error_msg = 'Adresse email invalide'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Créer un timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🕒 Timestamp: {timestamp}")
        
        # Initialiser la BDD si nécessaire
        if not os.path.exists('messages.db'):
            print("📂 Base de données non existante, création...")
            init_result = init_database()
            if not init_result:
                return jsonify({'success': False, 'error': 'Erreur de base de données'}), 500
        
        # Préparer les données pour la notification
        message_data = {
            'name': name,
            'email': email,
            'message': message,
            'timestamp': timestamp
        }
        
        # Envoyer notification email EN PREMIER
        print("📤 Tentative d'envoi d'email...")
        email_sent = send_notification_email(message_data)
        
        # Sauvegarder en base de données avec le statut email
        message_id = save_message_to_db(name, email, message, timestamp, email_sent)
        
        if message_id:
            print(f"✅ Message sauvegardé avec l'ID: {message_id}")
            
            # Vérifier que le message est bien en base
            messages = get_messages_from_db()
            print(f"📊 Total de messages en base après sauvegarde: {len(messages)}")
            
            # Réponse de succès détaillée
            success_message = "Message envoyé avec succès!"
            if email_sent:
                success_message += " Une notification email a été envoyée."
            else:
                success_message += " Note: La notification email n'a pas pu être envoyée."
            
            response_data = {
                'success': True, 
                'message': success_message,
                'id': message_id,
                'email_sent': email_sent,
                'total_messages': len(messages),
                'details': {
                    'name': name,
                    'email': email,
                    'timestamp': timestamp
                }
            }
            
            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(response_data)
            else:
                return redirect(url_for('home'))
                
        else:
            error_msg = 'Erreur lors de la sauvegarde du message'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        error_msg = f'Erreur interne du serveur: {str(e)}'
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/messages')
def view_messages():
    """Page d'administration des messages"""
    try:
        messages = get_messages_from_db()
        print(f"📋 Page admin: {len(messages)} messages à afficher")
        return render_template_string(MESSAGES_ADMIN_HTML, messages=messages)
    except Exception as e:
        error_msg = f"Erreur lors du chargement des messages: {e}"
        print(f"❌ {error_msg}")
        return f"<h1>Erreur</h1><p>{error_msg}</p><a href='/'>Retour</a>", 500

@app.route('/test_email')
def test_email():
    """Test d'envoi d'email"""
    try:
        test_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'message': 'Ceci est un test d\'envoi d\'email depuis Tunelith.',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result = send_notification_email(test_data)
        
        return jsonify({
            'email_test': 'SUCCESS' if result else 'FAILED',
            'config_check': {
                'EMAIL_USER': EMAIL_USER,
                'EMAIL_PASS_SET': bool(EMAIL_PASS),
                'ADMIN_EMAIL': ADMIN_EMAIL
            },
            'message': 'Email de test envoyé avec succès!' if result else 'Échec de l\'envoi de l\'email de test.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages')
def api_messages():
    """API pour récupérer les messages en JSON"""
    try:
        messages = get_messages_from_db()
        return jsonify({
            'success': True,
            'count': len(messages),
            'messages': messages,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Contrôle de santé avec info base de données et email"""
    try:
        messages_count = len(get_messages_from_db())
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'messages_in_db': messages_count,
            'database_exists': os.path.exists('messages.db'),
            'email_configured': {
                'EMAIL_USER': EMAIL_USER,
                'EMAIL_PASS_SET': bool(EMAIL_PASS),
                'ADMIN_EMAIL': ADMIN_EMAIL,
                'fully_configured': bool(EMAIL_USER and EMAIL_PASS and ADMIN_EMAIL)
            },
            'version': '3.0-email-fixed'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Initialiser la base de données au démarrage
print("🚀 Initialisation de l'application Tunelith v3.0...")
print(f"📧 Configuration email: {EMAIL_USER} -> {ADMIN_EMAIL}")
init_database()

if __name__ == "__main__":
    init_database()
    
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🌐 Démarrage de Tunelith sur le port {port}")
    print(f"📊 URL de test de la BDD: http://localhost:{port}/test_db")
    print(f"📧 Page d'administration: http://localhost:{port}/messages")
    print(f"✉️ Test d'email: http://localhost:{port}/test_email")
    print(f"💡 IMPORTANT: Configurez EMAIL_PASS avec un App Password Gmail!")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
