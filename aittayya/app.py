# app.py (Final Foolproof Version)

from flask import Flask, render_template, request, jsonify, session, url_for
import os
from bot_logic import BotLogic

app = Flask(__name__)

# --- THIS IS THE FOOLPROOF FIX ---
# The secret key is now read from an environment variable.
# This ensures all server workers use the EXACT SAME key.
# If the variable is not set (for local testing), it uses a default value.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a-default-fallback-key-for-local-testing')
# --- END OF FIX ---

# Initialize the bot logic once.
bot = BotLogic()


@app.route('/')
def home():
    if 'state' not in session:
        session['state'] = {'lang': 'ta', 'menu_level': 'main_menu'}
    
    website_content = bot.fetch_website_content(force_refresh=True)

    # Hardcode static image URLs
    if 'mascotImageUrl' not in website_content: website_content['mascotImageUrl'] = {}
    website_content['mascotImageUrl']['en'] = url_for('static', filename='mascot-police.png')
    website_content['mascotImageUrl']['ta'] = url_for('static', filename='mascot-police.png')

    if 'templeImageUrl' not in website_content: website_content['templeImageUrl'] = {}
    website_content['templeImageUrl']['en'] = url_for('static', filename='tiruchendur_temple.webp')
    website_content['templeImageUrl']['ta'] = url_for('static', filename='tiruchendur_temple.webp')

    return render_template('index.html', website_content=website_content)


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    user_name = "Visitor"

    current_state = session.get('state', {'lang': 'ta', 'menu_level': 'main_menu'})
    
    responses, new_state = bot.process_user_input(
        user_id=None,
        input_type='text', 
        data=question, 
        user_name=user_name, 
        current_state=current_state
    )
    
    session['state'] = new_state
    
    return jsonify(responses)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)