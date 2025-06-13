# === Imports ===
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify, Response
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pandas as pd
import io
import openai
from langdetect import detect

# === App Config ===
app = Flask(__name__)
app.secret_key = 'f033ac7b18ff3721e0c009ff263332ab'

# === Admin Credentials ===
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'tenspick123'

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = 'google_sheets/credentials.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)
spreadsheet_name = "Tenspick Data"
sheet = client.open(spreadsheet_name).sheet1

# === OpenAI Setup ===
openai.api_key = "sk-..."  # Replace with your actual key

# === Routes ===

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/services')
def services():
    services = [
        {"title": "Web Development", "description": "Responsive and custom websites built for your business.", "icon": "fas fa-globe"},
        {"title": "App Development", "description": "Mobile apps for Android and iOS tailored to your needs.", "icon": "fas fa-mobile-alt"},
        {"title": "Image & Video Editing", "description": "Creative and professional media editing services.", "icon": "fas fa-photo-film"},
        {"title": "YouTube Thumbnails", "description": "Eye-catching thumbnails to boost your channel engagement.", "icon": "fab fa-youtube"},
        {"title": "Interior Designs", "description": "Beautiful, smart, and functional interior designs.", "icon": "fas fa-couch"},
        {"title": "SEO & SSL", "description": "Optimize your site and secure it with SSL for better visibility.", "icon": "fas fa-chart-line"},
        {"title": "Digital Marketing", "description": "Reach the right audience with data-driven strategies.", "icon": "fas fa-bullhorn"},
    ]
    return render_template('services.html', services=services)

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        subject = request.form['project']
        message = request.form.get('message', '')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Remove chatbot rows
        all_data = sheet.get_all_values()
        headers = all_data[0]
        user_rows = [row for row in all_data[1:] if not (row and row[1].strip().lower() == "chatbot")]
        sheet.clear()
        sheet.append_row(headers)
        for row in user_rows:
            sheet.append_row(row)

        # Check for duplicates
        for row in user_rows:
            if row[2] == email and row[5] == message:
                flash('⚠ Duplicate submission detected!', 'warning')
                return redirect(url_for('contact'))

        # Save to sheet
        sheet.append_row([timestamp, name, email, phone, subject, message])
        flash('✅ Your message has been sent!', 'success')
        return redirect(url_for('contact'))

    except Exception as e:
        print("❌ Error:", e)
        flash('❌ Something went wrong.', 'danger')
        return redirect(url_for('contact'))

@app.route('/admin-login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid credentials.', 'danger')
            return redirect(url_for('login'))
    return render_template("login.html")

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("✅ Logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    try:
        data = sheet.get_all_records()
        project_counts = {}
        date_counts = {}

        for row in data:
            project = row.get('Project') or row.get('Subject') or 'Unknown'
            date = row['Timestamp'].split(' ')[0]
            project_counts[project] = project_counts.get(project, 0) + 1
            date_counts[date] = date_counts.get(date, 0) + 1

        sorted_dates = sorted(date_counts.items())
        return render_template("admin.html", data=data,
                               project_labels=list(project_counts.keys()),
                               project_values=list(project_counts.values()),
                               date_labels=[d[0] for d in sorted_dates],
                               date_values=[d[1] for d in sorted_dates])

    except Exception as e:
        print("❌ Error loading admin:", e)
        flash("Dashboard error", "danger")
        return redirect(url_for('home'))

@app.route('/export_csv')
def export_csv():
    try:
        records = sheet.get_all_records()
        if not records:
            flash("⚠ No data to export.", "warning")
            return redirect(url_for('admin_dashboard'))

        df = pd.DataFrame(records)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return Response(output, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=contact_submissions.csv"})
    except Exception as e:
        print("❌ CSV export error:", e)
        flash("❌ Failed to export.", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/submit_chat', methods=['POST'])
def submit_chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '').strip()

        if not user_msg:
            return jsonify({'reply': "⚠ Please type something!"})

        try:
            ai_reply = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for TensPick."},
                    {"role": "user", "content": user_msg}
                ]
            ).choices[0].message.content.strip()
        except Exception as e:
            print("OpenAI fallback:", e)
            ai_reply = generate_ai_reply(user_msg)

        # Save chatbot message
        sheet.append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Chatbot", "bot@tenspick.ai", "", "", user_msg])
        return jsonify({'reply': ai_reply})

    except Exception as e:
        print("Chatbot error:", e)
        return jsonify({'reply': "⚠ Error occurred."})

# === Multilingual AI Fallback ===
def generate_ai_reply(user_msg):
    msg = user_msg.lower()
    try:
        lang = detect(msg)
    except:
        lang = 'en'

    replies = {
        'en': {
            "greeting": "👋 Hello! I'm the TensPick AI Assistant. How can I support you today?",
            "services": "🚀 We offer Web/App Development, AI Tools, UI/UX Design, Video Editing, SEO & Marketing.",
            "about": "🏢 TensPick is a creative tech company based in Tirupati, India.",
            "contact": "📧 Email: tenspickindia@gmail.com | 💬 WhatsApp: +91 73308 63893",
            "team": "👨‍💻 Team:\n- S. Manoj Kumar\n- Narayana Naidu\n- Tej Reddy Narpuu Reddy",
            "location": "📍 Tirupati, Andhra Pradesh",
            "pricing": "💰 Our pricing depends on your project needs.",
            "thanks": "😊 You're welcome!",
            "bye": "👋 See you soon!",
            "default": "🤖 I'm still learning. A team member will help you soon."
        },
        'te': {
            "greeting": "🙏 హలో! నేను టెన్స్‌పిక్ AI అసిస్టెంట్. మీకు ఎలా సహాయం చేయగలను?",
            "services": "💼 మేము వెబ్, యాప్ డెవలప్మెంట్, డిజైన్, మార్కెటింగ్ సేవలు అందిస్తున్నాము.",
            "about": "🏢 టెన్స్‌పిక్ ఒక టెక్నాలజీ కంపెనీ, తిరుపతిలో ఉంది.",
            "contact": "📧 ఈమెయిల్: tenspickindia@gmail.com వాట్సప్: +91 73308 63893",
            "team": "👨‍💻 మనం:మనోజ్ కుమార్, నారాయణ నాయుడు, తేజ్ రెడ్డి",
            "location": "📍 తిరుపతి, ఆంధ్ర ప్రదేశ్",
            "pricing": "💰 ధర మీ ప్రాజెక్ట్ ఆధారంగా ఉంటుంది.",
            "thanks": "ధన్యవాదాలు! 😊",
            "bye": "బై బై!",
            "default": "🤖 నేర్చుకుంటున్నాను. త్వరలో మేము మీకు సహాయం చేస్తాం."
        },
        'hi': {
            "greeting": "🙏 नमस्ते! मैं TensPick AI असिस्टेंट हूँ। आपकी मदद के लिए तैयार हूँ!",
            "services": "💼 हम वेब/ऐप विकास, डिज़ाइन, मार्केटिंग सेवाएं प्रदान करते हैं।",
            "about": "🏢 टेन्सपिक तिरुपति में स्थित एक टेक कंपनी है।",
            "contact": "📧 ईमेल: tenspickindia@gmail.com  व्हाट्सएप: +91 73308 63893",
            "team": "👨‍💻 टीम: मनोज कुमार, नारायण नायडू, तेज रेड्डी",
            "location": "📍 तिरुपति, आंध्र प्रदेश",
            "pricing": "💰 हमारी कीमतें प्रोजेक्ट पर निर्भर करती हैं।",
            "thanks": "शुक्रिया! 😊",
            "bye": "अलविदा!",
            "default": "🤖 मैं सीख रहा हूँ। जल्द ही हमारी टीम मदद करेगी।"
        }
    }

    lang_responses = replies.get(lang, replies['en'])

    keywords = {
        "greeting": ["hello", "hi", "hey", "hai", "namaste","hallo", "హలో", "नमस्ते","హాయ్", "హాయ్", "హాయ్", "హాయ్", "హాయ్", "హాయ్", "హాయ్"],
        "services": ["service", "offer", "your work", "సేవ", "सेवा", "सेवाएं", "సేవలు","सेवाएँ", "what do you do", "what services", "what you do", "what services do you provide"],
        "about": ["tenspick", "who are you", "about","What Company", "what company", "who are you", "what is tenspick", "what is your company", "what is tenspick about", "what is your company about", "what is tenspick company", "what is your company name", "what is your company about", "what is tenspick about"],
        "contact": ["contact", "email", "whatsapp", "సంప్రదించండి", "संपर्क","संपर्क करें", "ईमेल", "व्हाट्सएप", "ईमेल", "whatsapp", "whatsapp number", "whatsapp contact", "whatsapp number", "whatsapp contact", "whatsapp number", "whatsapp contact", "whatsapp number", "whatsapp contact", "whatsapp number", "whatsapp contact"],
        "team": ["team", "founder", "founders", "సభ్యులు", "टीम","टीम के सदस्य", "tenspick founders", "10 spick founder", " 10 speed founders", "tenspick members", " tenspick team founders", " founder", "owners", "fonders", "founders"],
        "location": ["location", "address", "place", "చోటు", "स्थान","where is company","where is the place of company"],
        "pricing": ["price", "pricing", "cost", "ధర", "कीमत"," what is the cost", "what is the price", "what is the cost of tenspick projects", "what is the price of project", "what is the cost of project"],
        "thanks": ["thank", "thanks", "ధన్యవాదాలు", "शुक्रिया",""],
        "bye": ["bye", "goodbye", "its am leaving "," i am getting off", "अलविदा"]
    }

    for key, words in keywords.items():
        if any(word in msg for word in words):
            return lang_responses[key]

    return lang_responses["default"]

# === Run Server ===
if __name__ == '__main__':
    app.run(debug=True)
