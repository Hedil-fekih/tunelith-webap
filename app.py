import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# Configuration pour la production
if os.environ.get('FLASK_ENV') != 'development':
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
@app.route('/')
def home():
    """Page d'accueil principale"""
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    """Traitement des messages du formulaire de contact"""
    try:
        # Récupération des données du formulaire
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validation basique
        if not all([name, email, message]):
            return jsonify({'error': 'Tous les champs sont obligatoires'}), 400
        
        # Validation email basique
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Adresse email invalide'}), 400
        
        # Préparation des données avec timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_data = {
            'timestamp': timestamp,
            'name': name,
            'email': email,
            'message': message
        }
        
        # Sauvegarde dans un fichier texte (format lisible)
        with open("messages.txt", "a", encoding="utf-8") as f:
            f.write(f"=== NOUVEAU MESSAGE ===\n")
            f.write(f"Date: {timestamp}\n")
            f.write(f"Nom: {name}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Message: {message}\n")
            f.write(f"{'='*50}\n\n")
        
        # Sauvegarde aussi en JSON pour traitement futur
        try:
            # Charger les messages existants
            try:
                with open("messages.json", "r", encoding="utf-8") as f:
                    messages = json.load(f)
            except FileNotFoundError:
                messages = []
            
            # Ajouter le nouveau message
            messages.append(message_data)
            
            # Sauvegarder
            with open("messages.json", "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde JSON: {e}")
        
        # Réponse de succès
        if request.content_type == 'application/json' or request.headers.get('Accept') == 'application/json':
            return jsonify({'success': True, 'message': 'Message envoyé avec succès!'})
        else:
            return redirect(url_for('home'))
            
    except Exception as e:
        print(f"Erreur lors du traitement du message: {e}")
        if request.content_type == 'application/json' or request.headers.get('Accept') == 'application/json':
            return jsonify({'error': 'Erreur interne du serveur'}), 500
        else:
            return redirect(url_for('home'))

@app.route('/messages')
def view_messages():
    """Page d'administration pour voir les messages (optionnel)"""
    try:
        messages = []
        if os.path.exists("messages.json"):
            with open("messages.json", "r", encoding="utf-8") as f:
                messages = json.load(f)
        
        # Trier par date (plus récent en premier)
        messages.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return render_template('messages.html', messages=messages)
    except Exception as e:
        return f"Erreur lors du chargement des messages: {e}", 500

@app.route('/api/stats')
def api_stats():
    """API pour obtenir des statistiques du site"""
    try:
        stats = {
            'projets_realises': 50,
            'clients_satisfaits': 30,
            'annees_experience': 3,
            'support': '24/7'
        }
        
        # Compter les messages si le fichier existe
        if os.path.exists("messages.json"):
            with open("messages.json", "r", encoding="utf-8") as f:
                messages = json.load(f)
                stats['messages_recus'] = len(messages)
        else:
            stats['messages_recus'] = 0
            
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Point de contrôle de santé de l'application"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0'
    })

@app.errorhandler(404)
def not_found_error(error):
    """Gestionnaire d'erreur 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    return render_template('500.html'), 500

# Configuration pour le développement
if __name__ == "__main__":
    # Créer les dossiers nécessaires s'ils n'existent pas
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Configuration du serveur
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🚀 Démarrage de Tunelith Web App sur le port {port}")
    print(f"📧 Les messages seront sauvegardés dans messages.txt et messages.json")
    print(f"🌐 Accès: http://localhost:{port}")
    
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=debug_mode
    )