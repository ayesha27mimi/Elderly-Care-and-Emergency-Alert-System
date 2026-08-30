from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
import pymysql
from functools import wraps
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = 'your_secret_key_change_this'

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Database connection
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='elderly_care',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Family required decorator
def family_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'family':
            flash('Family member access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Caregiver required decorator
def caregiver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'caregiver':
            flash('Caregiver access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Doctor required decorator
def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'doctor':
            flash('Doctor access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Elderly required decorator
def elderly_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'elderly':
            flash('Elderly access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to log activity
def log_activity(user_id, action, details):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details, ip_address)
            VALUES (%s, %s, %s, %s)
        """, (user_id, action, details, request.remote_addr))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")

# ============== PUBLIC ROUTES ==============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    flash('Thank you! Your message has been sent successfully.', 'success')
    return redirect(url_for('contacts'))

# ============== LOGIN & SIGNUP ==============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                
                log_activity(user['id'], 'Login', 'Successful login')
                
                # Redirect based on role
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'family':
                    return redirect(url_for('family_dashboard'))
                elif user['role'] == 'caregiver':
                    return redirect(url_for('caregiver_dashboard'))
                elif user['role'] == 'doctor':
                    return redirect(url_for('doctor_dashboard'))
                elif user['role'] == 'elderly':
                    return redirect(url_for('elderly_dashboard'))
                else:
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form.get('phone', '')
        role = request.form['role']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users(username, password, role, email, phone) VALUES(%s, %s, %s, %s, %s)",
                (username, password, role, email, phone)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ============== ADMIN DASHBOARD ==============

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM elderly_person")
    elderly_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM doctor")
    doctor_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM caregiver")
    caregiver_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM alerts WHERE status='pending'")
    alert_count = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM alerts 
        WHERE status='pending' AND type IN ('fall', 'high_bp', 'low_oxygen', 'high_hr')
    """)
    critical_alerts = cursor.fetchone()['count']
    
    stats = {
        'total_users': total_users,
        'elderly_count': elderly_count,
        'doctor_count': doctor_count,
        'caregiver_count': caregiver_count,
        'alert_count': alert_count,
        'critical_alerts': critical_alerts
    }
    
    cursor.execute("""
        SELECT role, COUNT(*) as count 
        FROM users 
        GROUP BY role
        ORDER BY role
    """)
    role_data = cursor.fetchall()
    role_labels = [row['role'].capitalize() for row in role_data]
    role_counts = [row['count'] for row in role_data]
    
    alert_dates = []
    alert_counts = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM alerts 
            WHERE DATE(created_at) = %s
        """, (date,))
        count = cursor.fetchone()['count']
        alert_dates.append((datetime.now() - timedelta(days=i)).strftime('%b %d'))
        alert_counts.append(count)
    
    cursor.execute("""
        SELECT a.*, e.full_name 
        FROM alerts a 
        LEFT JOIN elderly_person e ON a.elderly_id = e.id 
        ORDER BY a.created_at DESC LIMIT 5
    """)
    recent_alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html',
                         stats=stats,
                         role_labels=role_labels,
                         role_counts=role_counts,
                         alert_dates=alert_dates,
                         alert_counts=alert_counts,
                         recent_alerts=recent_alerts)

# ============== USER MANAGEMENT ==============

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    sort_by = request.args.get('sort', 'id')
    
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    
    if search:
        query += " AND (username LIKE %s OR email LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if role_filter:
        query += " AND role = %s"
        params.append(role_filter)
    
    if sort_by in ['id', 'username', 'created_at', 'role']:
        query += f" ORDER BY {sort_by}"
    else:
        query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    phone = request.form.get('phone')
    role = request.form.get('role')
    
    if not username or not password or not role:
        flash('Username, password, and role are required!', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, email, phone, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password, email, phone, role))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'User Created', f'Created user: {username}')
        
        flash(f'User {username} added successfully!', 'success')
    except pymysql.IntegrityError:
        flash('Username already exists!', 'error')
    except Exception as e:
        flash(f'Error adding user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        username = user['username'] if user else 'Unknown'
        
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'User Deleted', f'Deleted user: {username}')
        
        flash('User deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

# ============== ELDERLY MANAGEMENT ==============

@app.route('/admin/elderly')
@admin_required
def admin_elderly():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, u.username as caregiver_name 
        FROM elderly_person e 
        LEFT JOIN users u ON e.primary_caregiver_id = u.id 
        ORDER BY e.created_at DESC
    """)
    elderly = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_elderly.html', elderly=elderly)

@app.route('/admin/elderly/delete/<int:elderly_id>', methods=['POST'])
@admin_required
def delete_elderly(elderly_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT full_name FROM elderly_person WHERE id = %s", (elderly_id,))
        person = cursor.fetchone()
        name = person['full_name'] if person else 'Unknown'
        
        cursor.execute("DELETE FROM elderly_person WHERE id=%s", (elderly_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Elderly Deleted', f'Deleted record: {name}')
        
        flash('Elderly person deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting: {str(e)}', 'error')
    
    return redirect(url_for('admin_elderly'))

# ============== ALERTS MANAGEMENT ==============

@app.route('/admin/alerts')
@admin_required
def admin_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, e.full_name 
        FROM alerts a 
        LEFT JOIN elderly_person e ON a.elderly_id = e.id 
        ORDER BY a.created_at DESC
    """)
    alerts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_alerts.html', alerts=alerts)

@app.route('/admin/alerts/update/<int:alert_id>', methods=['POST'])
@admin_required
def update_alert(alert_id):
    status = request.form['status']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts 
            SET status=%s, responded_by=%s, responded_role=%s 
            WHERE id=%s
        """, (status, session['username'], session['role'], alert_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Alert Updated', f'Changed alert #{alert_id} status to {status}')
        
        flash('Alert updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating alert: {str(e)}', 'error')
    
    return redirect(url_for('admin_alerts'))

# ============== FAMILY DASHBOARD ==============

@app.route('/family/dashboard')
@family_required
def family_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get elderly person(s) linked to this family member
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE id IN (
            SELECT elderly_id FROM family_elderly_link WHERE family_user_id = %s
        ) OR primary_caregiver_id = %s
        LIMIT 1
    """, (session['user_id'], session['user_id']))
    elderly = cursor.fetchone()
    
    if not elderly:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
    
    elderly_id = elderly['id'] if elderly else None
    
    # Get latest health data
    health_data = {}
    if elderly_id:
        cursor.execute("""
            SELECT * FROM health_data 
            WHERE elderly_id = %s 
            ORDER BY updated_at DESC LIMIT 1
        """, (elderly_id,))
        health_data = cursor.fetchone() or {}
    
    # Get active alerts count
    cursor.execute("""
        SELECT COUNT(*) as count FROM alerts 
        WHERE elderly_id = %s AND status = 'pending'
    """, (elderly_id,))
    active_alerts = cursor.fetchone()['count']
    
    # Get upcoming appointments
    cursor.execute("""
        SELECT COUNT(*) as count FROM appointments 
        WHERE elderly_id = %s AND status = 'scheduled'
        AND appointment_time > NOW()
    """, (elderly_id,))
    upcoming_appointments = cursor.fetchone()['count']
    
    # Get recent alerts
    cursor.execute("""
        SELECT * FROM alerts 
        WHERE elderly_id = %s 
        ORDER BY created_at DESC LIMIT 5
    """, (elderly_id,))
    recent_alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('family_dashboard.html',
                         elderly=elderly,
                         health_data=health_data,
                         active_alerts=active_alerts,
                         upcoming_appointments=upcoming_appointments,
                         recent_alerts=recent_alerts)

@app.route('/family/health-monitoring')
@family_required
def family_health_monitoring():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE id IN (
            SELECT elderly_id FROM family_elderly_link WHERE family_user_id = %s
        ) OR primary_caregiver_id = %s
        LIMIT 1
    """, (session['user_id'], session['user_id']))
    elderly = cursor.fetchone()
    
    if not elderly:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
    
    elderly_id = elderly['id'] if elderly else None
    
    # Get latest health data
    cursor.execute("""
        SELECT * FROM health_data 
        WHERE elderly_id = %s 
        ORDER BY updated_at DESC LIMIT 1
    """, (elderly_id,))
    health_data = cursor.fetchone()
    
    # Get health history (last 10 records)
    cursor.execute("""
        SELECT * FROM health_data 
        WHERE elderly_id = %s 
        ORDER BY updated_at DESC LIMIT 10
    """, (elderly_id,))
    health_history = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('family_health_monitoring.html',
                         elderly=elderly,
                         health_data=health_data,
                         health_history=health_history)

@app.route('/family/health-stats')
@family_required
def family_health_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE id IN (
            SELECT elderly_id FROM family_elderly_link WHERE family_user_id = %s
        ) OR primary_caregiver_id = %s
        LIMIT 1
    """, (session['user_id'], session['user_id']))
    elderly = cursor.fetchone()
    
    if not elderly:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
    
    elderly_id = elderly['id'] if elderly else None
    
    # Get health data for last 30 days
    cursor.execute("""
        SELECT * FROM health_data 
        WHERE elderly_id = %s 
        AND updated_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        ORDER BY updated_at ASC
    """, (elderly_id,))
    health_data = cursor.fetchall()
    
    # Get alert type distribution
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM alerts 
        WHERE elderly_id = %s 
        GROUP BY type
    """, (elderly_id,))
    alert_types = cursor.fetchall()
    
    # Get alert frequency by hour
    cursor.execute("""
        SELECT HOUR(created_at) as hour, COUNT(*) as count 
        FROM alerts 
        WHERE elderly_id = %s 
        GROUP BY HOUR(created_at)
        ORDER BY hour
    """, (elderly_id,))
    alert_hours = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('family_health_stats.html',
                         elderly=elderly,
                         health_data=health_data,
                         alert_types=alert_types,
                         alert_hours=alert_hours)

@app.route('/family/contact-team')
@family_required
def family_contact_team():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE id IN (
            SELECT elderly_id FROM family_elderly_link WHERE family_user_id = %s
        ) OR primary_caregiver_id = %s
        LIMIT 1
    """, (session['user_id'], session['user_id']))
    elderly = cursor.fetchone()
    
    if not elderly:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
    
    # Get assigned doctor
    cursor.execute("""
        SELECT u.*, d.specialization 
        FROM doctor d
        JOIN users u ON d.user_id = u.id
        LIMIT 1
    """)
    doctor = cursor.fetchone()
    
    # Get assigned caregiver
    cursor.execute("""
        SELECT u.*, c.shift 
        FROM caregiver c
        JOIN users u ON c.user_id = u.id
        WHERE u.id = %s
    """, (elderly['primary_caregiver_id'],)) if elderly else None
    caregiver = cursor.fetchone() if elderly else None
    
    cursor.close()
    conn.close()
    
    return render_template('family_contact_team.html',
                         elderly=elderly,
                         doctor=doctor,
                         caregiver=caregiver)

@app.route('/family/alerts')
@family_required
def family_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE id IN (
            SELECT elderly_id FROM family_elderly_link WHERE family_user_id = %s
        ) OR primary_caregiver_id = %s
        LIMIT 1
    """, (session['user_id'], session['user_id']))
    elderly = cursor.fetchone()
    
    if not elderly:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
    
    elderly_id = elderly['id'] if elderly else None
    
    # Get alerts
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    
    query = "SELECT * FROM alerts WHERE elderly_id = %s"
    params = [elderly_id]
    
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
    
    if type_filter:
        query += " AND type = %s"
        params.append(type_filter)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('family_alerts.html',
                         elderly=elderly,
                         alerts=alerts)

@app.route('/family/messages')
@family_required
def family_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get received messages
    cursor.execute("""
        SELECT m.*, u.username as from_username 
        FROM messages m
        JOIN users u ON m.from_user = u.id
        WHERE m.to_user = %s
        ORDER BY m.created_at DESC
    """, (session['user_id'],))
    received_messages = cursor.fetchall()
    
    # Get sent messages
    cursor.execute("""
        SELECT m.*, u.username as to_username 
        FROM messages m
        JOIN users u ON m.to_user = u.id
        WHERE m.from_user = %s
        ORDER BY m.created_at DESC
    """, (session['user_id'],))
    sent_messages = cursor.fetchall()
    
    # Get all users for sending messages
    cursor.execute("""
        SELECT id, username, role 
        FROM users 
        WHERE role IN ('doctor', 'caregiver', 'admin')
        AND id != %s
    """, (session['user_id'],))
    available_users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('family_messages.html',
                         received_messages=received_messages,
                         sent_messages=sent_messages,
                         available_users=available_users)

@app.route('/family/messages/send', methods=['POST'])
@family_required
def send_message():
    to_user = request.form.get('to_user')
    subject = request.form.get('subject')
    body = request.form.get('body')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (from_user, to_user, subject, body)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], to_user, subject, body))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Message sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'error')
    
    return redirect(url_for('family_messages'))

@app.route('/family/download_health_report')
@family_required
def download_health_report():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE id IN (
            SELECT elderly_id FROM family_elderly_link WHERE family_user_id = %s
        ) OR primary_caregiver_id = %s
        LIMIT 1
    """, (session['user_id'], session['user_id']))
    elderly = cursor.fetchone()
    
    if not elderly:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
    
    elderly_id = elderly['id'] if elderly else None
    
    # Get health data
    cursor.execute("""
        SELECT * FROM health_data 
        WHERE elderly_id = %s 
        ORDER BY updated_at DESC LIMIT 30
    """, (elderly_id,))
    health_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"<b>Health Report - {elderly['full_name']}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Date
    date_text = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    elements.append(date_text)
    elements.append(Spacer(1, 12))
    
    # Health data table
    if health_data:
        table_data = [['Date', 'Heart Rate', 'Blood Pressure', 'Blood Sugar', 'Temperature']]
        
        for record in health_data:
            table_data.append([
                record['updated_at'].strftime('%Y-%m-%d'),
                str(record.get('heart_rate', 'N/A')),
                record.get('blood_pressure', 'N/A'),
                str(record.get('blood_sugar', 'N/A')),
                str(record.get('temperature', 'N/A'))
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
    
    doc.build(elements)
    
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=health_report_{elderly["full_name"]}_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

# API endpoint for real-time notifications
@app.route('/api/family/notifications')
@family_required
def get_notifications():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE id IN (
            SELECT elderly_id FROM family_elderly_link WHERE family_user_id = %s
        ) OR primary_caregiver_id = %s
        LIMIT 1
    """, (session['user_id'], session['user_id']))
    elderly = cursor.fetchone()
    
    if not elderly:
        return jsonify({'notifications': []})
    
    elderly_id = elderly['id']
    
    # Get new alerts
    cursor.execute("""
        SELECT * FROM alerts 
        WHERE elderly_id = %s 
        AND status = 'pending'
        AND created_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
        ORDER BY created_at DESC
    """, (elderly_id,))
    new_alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    notifications = []
    for alert in new_alerts:
        notifications.append({
            'id': alert['id'],
            'type': alert['type'],
            'description': alert['description'],
            'created_at': alert['created_at'].strftime('%H:%M:%S'),
            'priority': 'high' if alert['type'] in ['fall', 'high_bp', 'low_oxygen'] else 'medium'
        })
    
    return jsonify({'notifications': notifications})


# ============== CAREGIVER DASHBOARD ROUTES ==============
@app.route('/caregiver/dashboard')
@caregiver_required
def caregiver_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get caregiver info
    cursor.execute("""
        SELECT c.*, u.username, u.email 
        FROM caregiver c
        JOIN users u ON c.user_id = u.id
        WHERE u.id = %s
    """, (session['user_id'],))
    caregiver = cursor.fetchone()
    
    # Get assigned elderly persons
    cursor.execute("""
        SELECT * FROM elderly_person 
        WHERE primary_caregiver_id = %s
        ORDER BY full_name
    """, (session['user_id'],))
    assigned_elderly = cursor.fetchall()
    
    # Get selected elderly ID from query parameter or use first one
    selected_elderly_id = request.args.get('elderly_id', type=int)
    if not selected_elderly_id and assigned_elderly:
        selected_elderly_id = assigned_elderly[0]['id']
    
    # Initialize variables
    selected_elderly = None
    latest_health = None
    vital_history = []
    recent_alerts = []
    today_tasks = []
    all_tasks = []
    all_alerts = []
    family_members = []
    doctor = None
    
    if selected_elderly_id:
        # Get selected elderly details
        cursor.execute("""
            SELECT * FROM elderly_person WHERE id = %s
        """, (selected_elderly_id,))
        selected_elderly = cursor.fetchone()
        
        if selected_elderly:
            # Get latest health data
            cursor.execute("""
                SELECT * FROM health_data 
                WHERE elderly_id = %s 
                ORDER BY updated_at DESC LIMIT 1
            """, (selected_elderly_id,))
            latest_health = cursor.fetchone()
            
            # FIXED: Get vital signs history for graphs (last 7 days) from health_data table
            cursor.execute("""
                SELECT 
                    DATE(updated_at) as date,
                    AVG(heart_rate) as avg_hr,
                    AVG(blood_sugar) as avg_sugar,
                    AVG(temperature) as avg_temp,
                    AVG(CAST(SUBSTRING_INDEX(blood_pressure, '/', 1) AS UNSIGNED)) as avg_bp_sys,
                    AVG(CAST(SUBSTRING_INDEX(blood_pressure, '/', -1) AS UNSIGNED)) as avg_bp_dia
                FROM health_data
                WHERE elderly_id = %s 
                AND updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(updated_at)
                ORDER BY date ASC
            """, (selected_elderly_id,))
            vital_history_raw = cursor.fetchall()
            
            # Format data for JavaScript
            if vital_history_raw and len(vital_history_raw) > 0:
                for record in vital_history_raw:
                    vital_history.append({
                        'date': record['date'].strftime('%b %d'),
                        'avg_hr': float(record['avg_hr']) if record['avg_hr'] else None,
                        'avg_sugar': float(record['avg_sugar']) if record['avg_sugar'] else None,
                        'avg_temp': float(record['avg_temp']) if record['avg_temp'] else None,
                        'avg_bp_sys': float(record['avg_bp_sys']) if record['avg_bp_sys'] else None,
                        'avg_bp_dia': float(record['avg_bp_dia']) if record['avg_bp_dia'] else None
                    })
            else:
                # Create empty data points for last 7 days if no data
                for i in range(6, -1, -1):
                    vital_history.append({
                        'date': (datetime.now() - timedelta(days=i)).strftime('%b %d'),
                        'avg_hr': None,
                        'avg_sugar': None,
                        'avg_temp': None,
                        'avg_bp_sys': None,
                        'avg_bp_dia': None
                    })
            
            # Get recent alerts for this patient
            cursor.execute("""
                SELECT a.*, e.full_name 
                FROM alerts a
                JOIN elderly_person e ON a.elderly_id = e.id
                WHERE a.elderly_id = %s
                ORDER BY a.created_at DESC LIMIT 10
            """, (selected_elderly_id,))
            recent_alerts = cursor.fetchall()
            
            # Get today's tasks for this patient
            cursor.execute("""
                SELECT t.*, e.full_name 
                FROM tasks t
                LEFT JOIN elderly_person e ON t.elderly_id = e.id
                WHERE t.elderly_id = %s 
                AND t.assigned_to = %s 
                AND DATE(t.due_date) = CURDATE()
                ORDER BY t.priority DESC
            """, (selected_elderly_id, session['user_id']))
            today_tasks = cursor.fetchall()
            
            # FIXED: Get family members linked to this elderly person
            cursor.execute("""
                SELECT DISTINCT u.id, u.username, u.email, u.phone 
                FROM users u
                JOIN family_elderly_link fel ON u.id = fel.family_user_id
                WHERE fel.elderly_id = %s AND u.role = 'family'
            """, (selected_elderly_id,))
            family_members = cursor.fetchall()
            
            # Get doctor (any doctor in the system for now)
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.phone, d.specialization 
                FROM users u
                JOIN doctor d ON u.id = d.user_id
                WHERE u.role = 'doctor'
                LIMIT 1
            """)
            doctor = cursor.fetchone()
    
    # Get all tasks for caregiver
    cursor.execute("""
        SELECT t.*, e.full_name 
        FROM tasks t
        LEFT JOIN elderly_person e ON t.elderly_id = e.id
        WHERE t.assigned_to = %s
        ORDER BY t.due_date ASC, t.priority DESC
    """, (session['user_id'],))
    all_tasks = cursor.fetchall()
    
    # Get all alerts for caregiver's patients
    cursor.execute("""
        SELECT a.*, e.full_name 
        FROM alerts a
        JOIN elderly_person e ON a.elderly_id = e.id
        WHERE e.primary_caregiver_id = %s
        ORDER BY a.created_at DESC
    """, (session['user_id'],))
    all_alerts = cursor.fetchall()
    
    # Summary stats
    cursor.execute("""
        SELECT COUNT(*) as count FROM elderly_person 
        WHERE primary_caregiver_id = %s
    """, (session['user_id'],))
    total_patients = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM alerts 
        WHERE elderly_id IN (
            SELECT id FROM elderly_person WHERE primary_caregiver_id = %s
        ) AND status = 'pending'
    """, (session['user_id'],))
    pending_alerts = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM tasks 
        WHERE assigned_to = %s AND status = 'pending'
    """, (session['user_id'],))
    pending_tasks = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    stats = {
        'total_patients': total_patients,
        'pending_alerts': pending_alerts,
        'pending_tasks': pending_tasks
    }
    
    return render_template('caregiver_dashboard.html',
                         caregiver=caregiver,
                         assigned_elderly=assigned_elderly,
                         selected_elderly=selected_elderly,
                         selected_elderly_id=selected_elderly_id,
                         latest_health=latest_health,
                         vital_history=vital_history,
                         recent_alerts=recent_alerts,
                         today_tasks=today_tasks,
                         all_tasks=all_tasks,
                         all_alerts=all_alerts,
                         family_members=family_members,
                         doctor=doctor,
                         stats=stats,
                         current_date=datetime.now().strftime('%A, %B %d, %Y'))


@app.route('/caregiver/vital-signs/record', methods=['POST'])
@caregiver_required
def record_vital_signs():
    elderly_id = request.form.get('elderly_id')
    bp_systolic = request.form.get('bp_systolic')
    bp_diastolic = request.form.get('bp_diastolic')
    blood_sugar = request.form.get('blood_sugar')
    temperature = request.form.get('temperature')
    heart_rate = request.form.get('heart_rate')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert into health_data table (your existing table has id as auto_increment)
        cursor.execute("""
            INSERT INTO health_data 
            (elderly_id, blood_pressure, blood_sugar, temperature, heart_rate, updated_at)
            VALUES (%s, CONCAT(%s, '/', %s), %s, %s, %s, NOW())
        """, (elderly_id, bp_systolic, bp_diastolic, blood_sugar, temperature, heart_rate))
        
        conn.commit()
        
        # Check for abnormal vitals and create alerts + notify family/doctors
        bp_sys_int = int(bp_systolic)
        bp_dia_int = int(bp_diastolic)
        heart_rate_int = int(heart_rate)
        blood_sugar_float = float(blood_sugar)
        temp_float = float(temperature)
        
        alerts_created = []
        
        # High Blood Pressure Alert
        if bp_sys_int > 140 or bp_dia_int > 90:
            cursor.execute("""
                INSERT INTO alerts (elderly_id, type, description, status)
                VALUES (%s, 'high_bp', %s, 'pending')
            """, (elderly_id, f'High blood pressure detected: {bp_systolic}/{bp_diastolic} mmHg'))
            alerts_created.append(('High Blood Pressure', f'{bp_systolic}/{bp_diastolic} mmHg'))
        
        # High Heart Rate Alert
        if heart_rate_int > 100:
            cursor.execute("""
                INSERT INTO alerts (elderly_id, type, description, status)
                VALUES (%s, 'high_hr', %s, 'pending')
            """, (elderly_id, f'High heart rate detected: {heart_rate} bpm'))
            alerts_created.append(('High Heart Rate', f'{heart_rate} bpm'))
        
        # Low Heart Rate Alert
        if heart_rate_int < 60:
            cursor.execute("""
                INSERT INTO alerts (elderly_id, type, description, status)
                VALUES (%s, 'low_hr', %s, 'pending')
            """, (elderly_id, f'Low heart rate detected: {heart_rate} bpm'))
            alerts_created.append(('Low Heart Rate', f'{heart_rate} bpm'))
        
        # High Blood Sugar Alert
        if blood_sugar_float > 180:
            cursor.execute("""
                INSERT INTO alerts (elderly_id, type, description, status)
                VALUES (%s, 'high_sugar', %s, 'pending')
            """, (elderly_id, f'High blood sugar detected: {blood_sugar} mg/dL'))
            alerts_created.append(('High Blood Sugar', f'{blood_sugar} mg/dL'))
        
        # Low Blood Sugar Alert
        if blood_sugar_float < 70:
            cursor.execute("""
                INSERT INTO alerts (elderly_id, type, description, status)
                VALUES (%s, 'low_sugar', %s, 'pending')
            """, (elderly_id, f'Low blood sugar detected: {blood_sugar} mg/dL'))
            alerts_created.append(('Low Blood Sugar', f'{blood_sugar} mg/dL'))
        
        # Fever Alert
        if temp_float > 38.0:
            cursor.execute("""
                INSERT INTO alerts (elderly_id, type, description, status)
                VALUES (%s, 'fever', %s, 'pending')
            """, (elderly_id, f'Fever detected: {temperature}°C'))
            alerts_created.append(('Fever', f'{temperature}°C'))
        
        # Low Temperature Alert
        if temp_float < 36.0:
            cursor.execute("""
                INSERT INTO alerts (elderly_id, type, description, status)
                VALUES (%s, 'low_temp', %s, 'pending')
            """, (elderly_id, f'Low temperature detected: {temperature}°C'))
            alerts_created.append(('Low Temperature', f'{temperature}°C'))
        
        conn.commit()
        
        # SEND NOTIFICATIONS TO FAMILY MEMBERS AND DOCTORS
        if alerts_created:
            # Get family members for this elderly person
            cursor.execute("""
                SELECT DISTINCT u.id, u.username, u.email 
                FROM users u
                JOIN family_elderly_link fel ON u.id = fel.family_user_id
                WHERE fel.elderly_id = %s AND u.role = 'family'
            """, (elderly_id,))
            family_members = cursor.fetchall()
            
            # Get doctors
            cursor.execute("""
                SELECT u.id, u.username, u.email 
                FROM users u
                JOIN doctor d ON u.id = d.user_id
                WHERE u.role = 'doctor'
            """)
            doctors = cursor.fetchall()
            
            # Get elderly name
            cursor.execute("SELECT full_name FROM elderly_person WHERE id = %s", (elderly_id,))
            elderly_person = cursor.fetchone()
            elderly_name = elderly_person['full_name'] if elderly_person else 'Patient'
            
            # Create alert message
            alert_message = f"Abnormal vital signs detected for {elderly_name}:\n"
            for alert_type, value in alerts_created:
                alert_message += f"- {alert_type}: {value}\n"
            
            # Send to family members
            for family in family_members:
                cursor.execute("""
                    INSERT INTO communications 
                    (from_user_id, to_user_id, elderly_id, subject, message, comm_type)
                    VALUES (%s, %s, %s, %s, %s, 'urgent')
                """, (session['user_id'], family['id'], elderly_id, 
                      f'URGENT: Abnormal Vitals - {elderly_name}', alert_message))
            
            # Send to doctors
            for doctor in doctors:
                cursor.execute("""
                    INSERT INTO communications 
                    (from_user_id, to_user_id, elderly_id, subject, message, comm_type)
                    VALUES (%s, %s, %s, %s, %s, 'urgent')
                """, (session['user_id'], doctor['id'], elderly_id, 
                      f'URGENT: Abnormal Vitals - {elderly_name}', alert_message))
            
            conn.commit()
            flash(f'Vital signs recorded. {len(alerts_created)} alert(s) created and family/doctors notified!', 'warning')
        else:
            flash('Vital signs recorded successfully. All values are normal.', 'success')
        
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Vital Signs Recorded', f'Recorded vitals for elderly #{elderly_id}')
        
    except Exception as e:
        flash(f'Error recording vital signs: {str(e)}', 'error')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('caregiver_dashboard', elderly_id=elderly_id))


@app.route('/caregiver/communication/send', methods=['POST'])
@caregiver_required
def send_communication():
    to_user_id = request.form.get('to_user_id')
    elderly_id = request.form.get('elderly_id')
    subject = request.form.get('subject')
    message = request.form.get('message')
    comm_type = request.form.get('comm_type', 'routine')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert into communications table
        cursor.execute("""
            INSERT INTO communications 
            (from_user_id, to_user_id, elderly_id, subject, message, comm_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['user_id'], to_user_id, elderly_id, subject, message, comm_type))
        
        conn.commit()
        
        # If urgent, also create an alert
        if comm_type == 'urgent':
            cursor.execute("""
                INSERT INTO alerts 
                (elderly_id, type, description, status)
                VALUES (%s, 'urgent_communication', %s, 'pending')
            """, (elderly_id, f'Urgent message: {subject}'))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Communication Sent', f'Sent {comm_type} message to user #{to_user_id}')
        flash('Message sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('caregiver_dashboard', elderly_id=elderly_id))


@app.route('/caregiver/task/update/<int:task_id>', methods=['POST'])
@caregiver_required
def caregiver_update_task(task_id):
    status = request.form.get('status')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tasks 
            SET status = %s, updated_at = NOW()
            WHERE id = %s AND assigned_to = %s
        """, (status, task_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Task Updated', f'Updated task #{task_id} to {status}')
        flash('Task updated successfully!', 'success')
        
    except Exception as e:
        flash(f'Error updating task: {str(e)}', 'error')
    
    return redirect(url_for('caregiver_dashboard'))


@app.route('/caregiver/task/add', methods=['POST'])
@caregiver_required
def caregiver_add_task():
    elderly_id = request.form.get('elderly_id')
    title = request.form.get('title')
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    priority = request.form.get('priority', 'medium')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks 
            (elderly_id, assigned_to, title, description, due_date, priority, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW())
        """, (elderly_id, session['user_id'], title, description, due_date, priority))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Task Created', f'Created task: {title}')
        flash('Task added successfully!', 'success')
        
    except Exception as e:
        flash(f'Error adding task: {str(e)}', 'error')
    
    return redirect(url_for('caregiver_dashboard', elderly_id=elderly_id))


@app.route('/caregiver/task/delete/<int:task_id>', methods=['POST'])
@caregiver_required
def caregiver_delete_task(task_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM tasks 
            WHERE id = %s AND assigned_to = %s
        """, (task_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Task Deleted', f'Deleted task #{task_id}')
        flash('Task deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting task: {str(e)}', 'error')
    
    return redirect(url_for('caregiver_dashboard'))


@app.route('/caregiver/note/add', methods=['POST'])
@caregiver_required
def caregiver_add_note():
    elderly_id = request.form.get('elderly_id')
    note = request.form.get('note')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO caregiver_notes 
            (elderly_id, caregiver_id, note, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (elderly_id, session['user_id'], note))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Note Added', f'Added note for elderly #{elderly_id}')
        flash('Note added successfully!', 'success')
        
    except Exception as e:
        flash(f'Error adding note: {str(e)}', 'error')
    
    return redirect(url_for('caregiver_dashboard', elderly_id=elderly_id))

@app.route('/caregiver/alert/respond/<int:alert_id>', methods=['POST'])
@caregiver_required
def caregiver_respond_alert(alert_id):
    status = request.form.get('status', 'resolved')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alerts 
            SET status = %s, responded_by = %s, responded_role = %s, updated_at = NOW()
            WHERE id = %s
        """, (status, session['username'], session['role'], alert_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Alert Responded', f'Responded to alert #{alert_id}')
        flash('Alert updated successfully!', 'success')
        
    except Exception as e:
        flash(f'Error updating alert: {str(e)}', 'error')
    
    return redirect(url_for('caregiver_dashboard'))

@app.route('/caregiver/appointment/add', methods=['POST'])
@caregiver_required
def caregiver_add_appointment():
    elderly_id = request.form.get('elderly_id')
    appointment_type = request.form.get('appointment_type')
    appointment_time = request.form.get('appointment_time')
    notes = request.form.get('notes', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get a doctor (first available)
        cursor.execute("SELECT user_id FROM doctor LIMIT 1")
        doctor = cursor.fetchone()
        doctor_id = doctor['user_id'] if doctor else None
        
        # Insert appointment
        cursor.execute("""
            INSERT INTO appointments 
            (elderly_id, doctor_id, appointment_type, appointment_time, notes, status, created_at)
            VALUES (%s, %s, %s, %s, %s, 'scheduled', NOW())
        """, (elderly_id, doctor_id, appointment_type, appointment_time, notes))
        
        conn.commit()
        
        # Get elderly name for notification
        cursor.execute("SELECT full_name FROM elderly_person WHERE id = %s", (elderly_id,))
        elderly = cursor.fetchone()
        elderly_name = elderly['full_name'] if elderly else 'Patient'
        
        # Notify doctor if assigned
        if doctor_id:
            cursor.execute("""
                INSERT INTO communications 
                (from_user_id, to_user_id, elderly_id, subject, message, comm_type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'routine', NOW())
            """, (session['user_id'], doctor_id, elderly_id,
                  'New Appointment Scheduled',
                  f'Caregiver has scheduled a {appointment_type} appointment for {elderly_name} at {appointment_time}'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Appointment Created', f'Scheduled {appointment_type} for elderly #{elderly_id}')
        flash('Appointment scheduled successfully!', 'success')
        
    except Exception as e:
        flash(f'Error scheduling appointment: {str(e)}', 'error')
        print(f"Appointment error: {str(e)}")
    
    return redirect(url_for('caregiver_dashboard', elderly_id=elderly_id))

@app.route('/caregiver/elderly/<int:elderly_id>')
@caregiver_required
def caregiver_elderly_details(elderly_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get elderly details
    cursor.execute("SELECT * FROM elderly_person WHERE id = %s", (elderly_id,))
    elderly = cursor.fetchone()
    
    if not elderly:
        flash('Patient not found', 'error')
        return redirect(url_for('caregiver_dashboard'))
    
    # Get latest health data
    cursor.execute("""
        SELECT * FROM health_data 
        WHERE elderly_id = %s 
        ORDER BY updated_at DESC LIMIT 1
    """, (elderly_id,))
    latest_health = cursor.fetchone()
    
    # Get vital history (last 7 days)
    cursor.execute("""
        SELECT 
            DATE(updated_at) as date,
            AVG(heart_rate) as avg_hr,
            AVG(blood_sugar) as avg_sugar,
            AVG(temperature) as avg_temp,
            AVG(CAST(SUBSTRING_INDEX(blood_pressure, '/', 1) AS UNSIGNED)) as avg_bp_sys,
            AVG(CAST(SUBSTRING_INDEX(blood_pressure, '/', -1) AS UNSIGNED)) as avg_bp_dia
        FROM health_data
        WHERE elderly_id = %s 
        AND updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(updated_at)
        ORDER BY date ASC
    """, (elderly_id,))
    vital_history_raw = cursor.fetchall()
    
    vital_history = []
    for record in vital_history_raw:
        vital_history.append({
            'date': record['date'].strftime('%b %d'),
            'avg_hr': record['avg_hr'],
            'avg_sugar': record['avg_sugar'],
            'avg_temp': record['avg_temp'],
            'avg_bp_sys': record['avg_bp_sys'],
            'avg_bp_dia': record['avg_bp_dia']
        })
    
    # Get alerts
    cursor.execute("""
        SELECT * FROM alerts 
        WHERE elderly_id = %s 
        ORDER BY created_at DESC LIMIT 10
    """, (elderly_id,))
    alerts = cursor.fetchall()
    
    # Get tasks
    cursor.execute("""
        SELECT * FROM tasks 
        WHERE elderly_id = %s 
        ORDER BY due_date ASC
    """, (elderly_id,))
    tasks = cursor.fetchall()
    
    # FIXED: Get appointments
    cursor.execute("""
        SELECT * FROM appointments 
        WHERE elderly_id = %s 
        ORDER BY appointment_time DESC
        LIMIT 20
    """, (elderly_id,))
    appointments = cursor.fetchall()
    
    # Get notes
    cursor.execute("""
        SELECT n.*, u.username 
        FROM caregiver_notes n
        JOIN users u ON n.caregiver_id = u.id
        WHERE n.elderly_id = %s 
        ORDER BY n.created_at DESC
    """, (elderly_id,))
    notes = cursor.fetchall()
    
    # Get family members
    cursor.execute("""
        SELECT DISTINCT u.id, u.username, u.email, u.phone 
        FROM users u
        JOIN family_elderly_link fel ON u.id = fel.family_user_id
        WHERE fel.elderly_id = %s AND u.role = 'family'
    """, (elderly_id,))
    family_members = cursor.fetchall()
    
    # Get doctor
    cursor.execute("""
        SELECT u.id, u.username, u.email, u.phone, d.specialization 
        FROM users u
        JOIN doctor d ON u.id = d.user_id
        WHERE u.role = 'doctor'
        LIMIT 1
    """)
    doctor = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('caregiver_elderly_details.html',
                         elderly=elderly,
                         latest_health=latest_health,
                         vital_history=vital_history,
                         alerts=alerts,
                         tasks=tasks,
                         appointments=appointments,
                         notes=notes,
                         family_members=family_members,
                         doctor=doctor)

# ============== DOCTOR DASHBOARD ROUTES ==============
@app.route('/doctor/dashboard')
@doctor_required
def doctor_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get doctor info
    cursor.execute("""
        SELECT d.*, u.username, u.email, u.phone 
        FROM doctor d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = %s
    """, (session['user_id'],))
    doctor_info = cursor.fetchone()
    
    # Get all patients
    cursor.execute("""
        SELECT e.*, 
               u.username as caregiver_name,
               (SELECT COUNT(*) FROM alerts WHERE elderly_id = e.id AND status = 'pending') as pending_alerts,
               (SELECT COUNT(*) FROM appointments WHERE elderly_id = e.id AND status = 'scheduled' AND appointment_time > NOW()) as upcoming_appointments
        FROM elderly_person e
        LEFT JOIN users u ON e.primary_caregiver_id = u.id
        ORDER BY e.full_name
    """)
    all_patients = cursor.fetchall()
    
    # Get selected patient
    selected_patient_id = request.args.get('patient_id', type=int)
    if not selected_patient_id and all_patients:
        selected_patient_id = all_patients[0]['id']
    
    selected_patient = None
    latest_vitals = None
    vital_history = []
    recent_alerts = []
    prescriptions = []
    appointments = []
    
    if selected_patient_id:
        # Get selected patient details
        cursor.execute("""
            SELECT e.*, u.username as caregiver_name, u.phone as caregiver_phone
            FROM elderly_person e
            LEFT JOIN users u ON e.primary_caregiver_id = u.id
            WHERE e.id = %s
        """, (selected_patient_id,))
        selected_patient = cursor.fetchone()
        
        if selected_patient:
            # Get latest vitals from health_data
            cursor.execute("""
                SELECT * FROM health_data 
                WHERE elderly_id = %s 
                ORDER BY updated_at DESC LIMIT 1
            """, (selected_patient_id,))
            latest_vitals = cursor.fetchone()
            
            # Get vital history (last 30 days) from health_data
            cursor.execute("""
                SELECT 
                    DATE(updated_at) as date,
                    AVG(heart_rate) as avg_hr,
                    AVG(blood_sugar) as avg_sugar,
                    AVG(temperature) as avg_temp,
                    AVG(CAST(SUBSTRING_INDEX(blood_pressure, '/', 1) AS UNSIGNED)) as avg_bp_sys,
                    AVG(CAST(SUBSTRING_INDEX(blood_pressure, '/', -1) AS UNSIGNED)) as avg_bp_dia
                FROM health_data
                WHERE elderly_id = %s 
                AND updated_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(updated_at)
                ORDER BY date ASC
            """, (selected_patient_id,))
            vital_history = cursor.fetchall()
            
            # Get recent alerts
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE elderly_id = %s 
                ORDER BY created_at DESC LIMIT 10
            """, (selected_patient_id,))
            recent_alerts = cursor.fetchall()
            
            # Get prescriptions
            cursor.execute("""
                SELECT p.*, u.username as doctor_name
                FROM prescriptions p
                LEFT JOIN users u ON p.doctor_id = u.id
                WHERE p.elderly_id = %s 
                ORDER BY p.created_at DESC
            """, (selected_patient_id,))
            prescriptions = cursor.fetchall()
            
            # Get appointments
            cursor.execute("""
                SELECT a.*, u.username as doctor_name
                FROM appointments a
                LEFT JOIN users u ON a.doctor_id = u.id
                WHERE a.elderly_id = %s 
                ORDER BY a.appointment_time DESC
                LIMIT 10
            """, (selected_patient_id,))
            appointments = cursor.fetchall()
    
    # Dashboard statistics
    cursor.execute("SELECT COUNT(*) as count FROM elderly_person")
    total_patients = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM appointments 
        WHERE doctor_id = %s AND status = 'scheduled' 
        AND DATE(appointment_time) = CURDATE()
    """, (session['user_id'],))
    today_appointments = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM alerts 
        WHERE status = 'pending'
    """)
    pending_alerts = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM prescriptions 
        WHERE doctor_id = %s 
        AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """, (session['user_id'],))
    recent_prescriptions = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    stats = {
        'total_patients': total_patients,
        'today_appointments': today_appointments,
        'pending_alerts': pending_alerts,
        'recent_prescriptions': recent_prescriptions
    }
    
    return render_template('doctor_dashboard.html',
                         doctor_info=doctor_info,
                         all_patients=all_patients,
                         selected_patient=selected_patient,
                         selected_patient_id=selected_patient_id,
                         latest_vitals=latest_vitals,
                         vital_history=vital_history,
                         recent_alerts=recent_alerts,
                         prescriptions=prescriptions,
                         appointments=appointments,
                         stats=stats)


@app.route('/doctor/prescription/add', methods=['POST'])
@doctor_required
def add_prescription():
    elderly_id = request.form.get('elderly_id')
    medication_name = request.form.get('medication_name')
    dosage = request.form.get('dosage')
    duration = request.form.get('duration', '30 days')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate start and end dates
        start_date = datetime.now().date()
        
        # Parse duration
        end_date = start_date + timedelta(days=30)  # Default 30 days
        if duration:
            duration_lower = duration.lower()
            if 'day' in duration_lower:
                days = int(''.join(filter(str.isdigit, duration)))
                end_date = start_date + timedelta(days=days)
            elif 'week' in duration_lower:
                weeks = int(''.join(filter(str.isdigit, duration)))
                end_date = start_date + timedelta(weeks=weeks)
            elif 'month' in duration_lower:
                months = int(''.join(filter(str.isdigit, duration)))
                end_date = start_date + timedelta(days=months*30)
        
        cursor.execute("""
            INSERT INTO prescriptions 
            (elderly_id, doctor_id, medicine, dosage, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (elderly_id, session['user_id'], medication_name, dosage, start_date, end_date))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Prescription Added', f'Added prescription for patient #{elderly_id}')
        flash('Prescription added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding prescription: {str(e)}', 'error')
    
    return redirect(url_for('doctor_dashboard', patient_id=elderly_id))


@app.route('/doctor/prescription/delete/<int:prescription_id>', methods=['POST'])
@doctor_required
def delete_prescription(prescription_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get elderly_id before deletion for redirect
        cursor.execute("SELECT elderly_id FROM prescriptions WHERE id = %s", (prescription_id,))
        result = cursor.fetchone()
        elderly_id = result['elderly_id'] if result else None
        
        cursor.execute("DELETE FROM prescriptions WHERE id = %s AND doctor_id = %s", 
                      (prescription_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Prescription Deleted', f'Deleted prescription #{prescription_id}')
        flash('Prescription deleted successfully!', 'success')
        
        if elderly_id:
            return redirect(url_for('doctor_dashboard', patient_id=elderly_id))
    except Exception as e:
        flash(f'Error deleting prescription: {str(e)}', 'error')
    
    return redirect(url_for('doctor_dashboard'))


@app.route('/doctor/appointment/add', methods=['POST'])
@doctor_required
def doctor_add_appointment():
    elderly_id = request.form.get('elderly_id')
    appointment_time = request.form.get('appointment_time')
    appointment_type = request.form.get('appointment_type')
    notes = request.form.get('notes', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments 
            (elderly_id, doctor_id, appointment_time, appointment_type, notes, status)
            VALUES (%s, %s, %s, %s, %s, 'scheduled')
        """, (elderly_id, session['user_id'], appointment_time, appointment_type, notes))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Appointment Created', f'Created appointment for patient #{elderly_id}')
        flash('Appointment scheduled successfully!', 'success')
    except Exception as e:
        flash(f'Error scheduling appointment: {str(e)}', 'error')
    
    return redirect(url_for('doctor_dashboard', patient_id=elderly_id))


@app.route('/doctor/appointment/update/<int:appointment_id>', methods=['POST'])
@doctor_required
def update_appointment_status(appointment_id):
    status = request.form.get('status')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get elderly_id before update for redirect
        cursor.execute("SELECT elderly_id FROM appointments WHERE id = %s", (appointment_id,))
        result = cursor.fetchone()
        elderly_id = result['elderly_id'] if result else None
        
        cursor.execute("""
            UPDATE appointments 
            SET status = %s
            WHERE id = %s AND doctor_id = %s
        """, (status, appointment_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Appointment Updated', f'Updated appointment #{appointment_id}')
        flash('Appointment updated successfully!', 'success')
        
        if elderly_id:
            return redirect(url_for('doctor_dashboard', patient_id=elderly_id))
    except Exception as e:
        flash(f'Error updating appointment: {str(e)}', 'error')
    
    return redirect(url_for('doctor_dashboard'))


@app.route('/doctor/appointment/delete/<int:appointment_id>', methods=['POST'])
@doctor_required
def delete_appointment(appointment_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get elderly_id before deletion for redirect
        cursor.execute("SELECT elderly_id FROM appointments WHERE id = %s", (appointment_id,))
        result = cursor.fetchone()
        elderly_id = result['elderly_id'] if result else None
        
        cursor.execute("DELETE FROM appointments WHERE id = %s AND doctor_id = %s", 
                      (appointment_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Appointment Deleted', f'Deleted appointment #{appointment_id}')
        flash('Appointment deleted successfully!', 'success')
        
        if elderly_id:
            return redirect(url_for('doctor_dashboard', patient_id=elderly_id))
    except Exception as e:
        flash(f'Error deleting appointment: {str(e)}', 'error')
    
    return redirect(url_for('doctor_dashboard'))


@app.route('/doctor/alerts')
@doctor_required
def doctor_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    
    query = """
        SELECT a.*, e.full_name 
        FROM alerts a
        JOIN elderly_person e ON a.elderly_id = e.id
        WHERE 1=1
    """
    params = []
    
    if status_filter:
        query += " AND a.status = %s"
        params.append(status_filter)
    
    if type_filter:
        query += " AND a.type = %s"
        params.append(type_filter)
    
    query += " ORDER BY a.created_at DESC"
    
    cursor.execute(query, params)
    alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('doctor_alerts.html', alerts=alerts)


@app.route('/doctor/alerts/respond/<int:alert_id>', methods=['POST'])
@doctor_required
def doctor_respond_alert(alert_id):
    status = request.form.get('status')
    response_notes = request.form.get('response_notes', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts 
            SET status = %s, 
                responded_by = %s, 
                responded_role = %s,
                response_notes = %s
            WHERE id = %s
        """, (status, session['username'], session['role'], response_notes, alert_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Alert Responded', f'Responded to alert #{alert_id}')
        flash('Alert response recorded successfully!', 'success')
    except Exception as e:
        flash(f'Error responding to alert: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('doctor_alerts'))

# ============== ELDERLY DASHBOARD ROUTES ==============

@app.route('/elderly/dashboard')
@elderly_required
def elderly_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Map username to elderly_person
    # elder_karim -> Karim Ahmed (id=1)
    # elder_jahan -> Jahan Begum (id=2)  
    # elder_mina -> Mina Khatun (id=3)
    # elder_hasan -> Hasan Ali (id=4)
    
    username_mapping = {
        'elder_karim': 1,
        'elder_jahan': 2,
        'elder_mina': 3,
        'elder_hasan': 4,
        'karin_ahmed': 1,
        'mina_khatun': 3
    }
    
    # Get elderly_id from mapping
    elderly_id = username_mapping.get(session['username'])
    
    if not elderly_id:
        # Fallback: try to find by similar name
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
        elderly_id = elderly['id'] if elderly else None
    else:
        cursor.execute("SELECT * FROM elderly_person WHERE id = %s", (elderly_id,))
        elderly = cursor.fetchone()
    
    if not elderly:
        flash('Your profile is not set up. Please contact the administrator.', 'error')
        cursor.close()
        conn.close()
        return render_template('elderly_dashboard.html', elderly=None, 
                             latest_health=None, upcoming_appointments=[], 
                             prescriptions=[], caregiver=None, doctor=None,
                             family_members=[], recent_alerts=[], stats={},
                             current_date=datetime.now().strftime('%A, %B %d, %Y'))
    
    elderly_id = elderly['id']
    
    # Get latest health data
    cursor.execute("""
        SELECT * FROM health_data 
        WHERE elderly_id = %s 
        ORDER BY updated_at DESC LIMIT 1
    """, (elderly_id,))
    latest_health = cursor.fetchone()
    
    # Get upcoming appointments
    cursor.execute("""
        SELECT a.*, u.username as doctor_name, d.specialization
        FROM appointments a
        LEFT JOIN doctor d ON a.doctor_id = d.user_id
        LEFT JOIN users u ON d.user_id = u.id
        WHERE a.elderly_id = %s 
        AND a.status = 'scheduled'
        AND a.appointment_time >= NOW()
        ORDER BY a.appointment_time ASC
        LIMIT 10
    """, (elderly_id,))
    upcoming_appointments = cursor.fetchall()
    
    # Get active prescriptions
    cursor.execute("""
        SELECT * FROM prescriptions
        WHERE elderly_id = %s
        AND (end_date IS NULL OR end_date >= CURDATE())
        ORDER BY created_at DESC
    """, (elderly_id,))
    prescriptions = cursor.fetchall()
    
    # Get caregiver info
    caregiver = None
    if elderly.get('primary_caregiver_id'):
        cursor.execute("""
            SELECT u.*, c.shift 
            FROM users u
            LEFT JOIN caregiver c ON u.id = c.user_id
            WHERE u.id = %s
        """, (elderly['primary_caregiver_id'],))
        caregiver = cursor.fetchone()
    
    # Get doctor info
    cursor.execute("""
        SELECT u.*, d.specialization 
        FROM users u
        JOIN doctor d ON u.id = d.user_id
        WHERE u.role = 'doctor'
        LIMIT 1
    """)
    doctor = cursor.fetchone()
    
    # Get family members
    cursor.execute("""
        SELECT u.*, f.relationship 
        FROM users u
        JOIN family_elderly_link f ON u.id = f.family_user_id
        WHERE f.elderly_id = %s AND u.role = 'family'
    """, (elderly_id,))
    family_members = cursor.fetchall()
    
    # Get recent alerts
    cursor.execute("""
        SELECT * FROM alerts 
        WHERE elderly_id = %s 
        ORDER BY created_at DESC LIMIT 5
    """, (elderly_id,))
    recent_alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Stats
    stats = {
        'upcoming_appointments': len(upcoming_appointments),
        'active_prescriptions': len(prescriptions),
        'recent_alerts': len(recent_alerts)
    }
    
    return render_template('elderly_dashboard.html',
                         elderly=elderly,
                         latest_health=latest_health,
                         upcoming_appointments=upcoming_appointments,
                         prescriptions=prescriptions,
                         caregiver=caregiver,
                         doctor=doctor,
                         family_members=family_members,
                         recent_alerts=recent_alerts,
                         stats=stats,
                         current_date=datetime.now().strftime('%A, %B %d, %Y'))


@app.route('/elderly/emergency', methods=['POST'])
@elderly_required
def elderly_emergency():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Map username to elderly_person ID
    username_mapping = {
        'elder_karim': 1,
        'elder_jahan': 2,
        'elder_mina': 3,
        'elder_hasan': 4,
        'karin_ahmed': 1,
        'mina_khatun': 3
    }
    
    elderly_id = username_mapping.get(session['username'])
    
    if not elderly_id:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
        elderly_id = elderly['id'] if elderly else None
    else:
        cursor.execute("SELECT * FROM elderly_person WHERE id = %s", (elderly_id,))
        elderly = cursor.fetchone()
    
    if not elderly:
        flash('Error: Profile not found', 'error')
        return redirect(url_for('elderly_dashboard'))
    
    try:
        # Create emergency alert
        cursor.execute("""
            INSERT INTO alerts (elderly_id, type, description, status, created_at)
            VALUES (%s, 'emergency', %s, 'pending', NOW())
        """, (elderly_id, f'🚨 EMERGENCY: {elderly["full_name"]} has requested immediate assistance!'))
        conn.commit()
        
        emergency_message = f'🚨 EMERGENCY ALERT 🚨\n\n{elderly["full_name"]} has pressed the emergency button and needs IMMEDIATE assistance!\n\nLocation: {elderly["address"]}\nEmergency Contact: {elderly["emergency_contact"]}\n\nPlease respond immediately!'
        
        # 1. Notify Caregiver (CHANGED TO 'urgent')
        if elderly.get('primary_caregiver_id'):
            cursor.execute("""
                INSERT INTO communications 
                (from_user_id, to_user_id, elderly_id, subject, message, comm_type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'urgent', NOW())
            """, (session['user_id'], elderly['primary_caregiver_id'], elderly_id,
                  '🚨 EMERGENCY ALERT', emergency_message))
        
        # 2. Notify Family Members (CHANGED TO 'urgent')
        cursor.execute("""
            SELECT u.id 
            FROM users u
            JOIN family_elderly_link fel ON u.id = fel.family_user_id
            WHERE fel.elderly_id = %s AND u.role = 'family'
        """, (elderly_id,))
        family_members = cursor.fetchall()
        
        for family in family_members:
            cursor.execute("""
                INSERT INTO communications 
                (from_user_id, to_user_id, elderly_id, subject, message, comm_type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'urgent', NOW())
            """, (session['user_id'], family['id'], elderly_id,
                  '🚨 EMERGENCY ALERT', emergency_message))
        
        # 3. Notify All Doctors (CHANGED TO 'urgent')
        cursor.execute("""
            SELECT u.id 
            FROM users u
            JOIN doctor d ON u.id = d.user_id
            WHERE u.role = 'doctor'
        """)
        doctors = cursor.fetchall()
        
        for doctor in doctors:
            cursor.execute("""
                INSERT INTO communications 
                (from_user_id, to_user_id, elderly_id, subject, message, comm_type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'urgent', NOW())
            """, (session['user_id'], doctor['id'], elderly_id,
                  '🚨 EMERGENCY ALERT', emergency_message))
        
        # 4. Notify Admin (CHANGED TO 'urgent')
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        admin = cursor.fetchone()
        if admin:
            cursor.execute("""
                INSERT INTO communications 
                (from_user_id, to_user_id, elderly_id, subject, message, comm_type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'urgent', NOW())
            """, (session['user_id'], admin['id'], elderly_id,
                  '🚨 EMERGENCY ALERT', emergency_message))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Emergency Alert', f'Emergency button pressed by {elderly["full_name"]}')
        
        flash('🚨 EMERGENCY ALERT SENT! Your caregiver, family, doctor, and administrator have been notified immediately.', 'warning')
        
    except Exception as e:
        flash(f'Error sending emergency alert: {str(e)}', 'error')
        print(f"Emergency error: {str(e)}")
    
    return redirect(url_for('elderly_dashboard'))


@app.route('/elderly/appointment/add', methods=['POST'])
@elderly_required
def elderly_add_appointment():
    appointment_type = request.form.get('appointment_type')
    appointment_time = request.form.get('appointment_time')
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Map username to elderly_person ID
    username_mapping = {
        'elder_karim': 1,
        'elder_jahan': 2,
        'elder_mina': 3,
        'elder_hasan': 4,
        'karin_ahmed': 1,
        'mina_khatun': 3
    }
    
    elderly_id = username_mapping.get(session['username'])
    
    if not elderly_id:
        cursor.execute("SELECT * FROM elderly_person ORDER BY id LIMIT 1")
        elderly = cursor.fetchone()
        elderly_id = elderly['id'] if elderly else None
    else:
        cursor.execute("SELECT * FROM elderly_person WHERE id = %s", (elderly_id,))
        elderly = cursor.fetchone()
    
    if not elderly:
        flash('Error: Profile not found', 'error')
        return redirect(url_for('elderly_dashboard'))
    
    try:
        # Get a doctor
        cursor.execute("SELECT user_id FROM doctor LIMIT 1")
        doctor = cursor.fetchone()
        doctor_id = doctor['user_id'] if doctor else None
        
        # Insert appointment
        cursor.execute("""
            INSERT INTO appointments 
            (elderly_id, doctor_id, appointment_type, appointment_time, notes, status, created_at)
            VALUES (%s, %s, %s, %s, %s, 'scheduled', NOW())
        """, (elderly_id, doctor_id, appointment_type, appointment_time, notes))
        
        conn.commit()
        
        # Notify caregiver
        if elderly.get('primary_caregiver_id'):
            cursor.execute("""
                INSERT INTO communications 
                (from_user_id, to_user_id, elderly_id, subject, message, comm_type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'routine', NOW())
            """, (session['user_id'], elderly['primary_caregiver_id'], elderly_id,
                  'New Appointment Scheduled',
                  f'{elderly["full_name"]} has scheduled a {appointment_type} appointment for {appointment_time}'))
            
        # Notify doctor if assigned
        if doctor_id:
            cursor.execute("""
                INSERT INTO communications 
                (from_user_id, to_user_id, elderly_id, subject, message, comm_type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'routine', NOW())
            """, (session['user_id'], doctor_id, elderly_id,
                  'New Appointment Request',
                  f'{elderly["full_name"]} has requested a {appointment_type} appointment for {appointment_time}'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(session['user_id'], 'Appointment Scheduled', f'Scheduled {appointment_type} appointment')
        
        flash('Appointment scheduled successfully! Your caregiver and doctor have been notified.', 'success')
        
    except Exception as e:
        flash(f'Error scheduling appointment: {str(e)}', 'error')
        print(f"Appointment error: {str(e)}")
    
    return redirect(url_for('elderly_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000) 