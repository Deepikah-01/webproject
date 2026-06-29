from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# ==========================
# CONFIG
# ==========================
app.config["SECRET_KEY"] = "studyhub_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studyhub.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    assignments = db.relationship('Assignment', backref='user', lazy=True)
    attendance = db.relationship('Attendance', backref='user', lazy=True)
    timetable = db.relationship('Timetable', backref='user', lazy=True)
    cgpa_records = db.relationship('CGPA', backref='user', lazy=True)

class Assignment(db.Model):
    __tablename__ = 'assignment'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), nullable=False, default='Medium')
    status = db.Column(db.String(50), nullable=False, default='Pending')
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(120), nullable=False)
    total_classes = db.Column(db.Integer, nullable=False, default=0)
    attended_classes = db.Column(db.Integer, nullable=False, default=0)
    attendance_percentage = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), nullable=False, default='Needs Attention')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Timetable(db.Model):
    __tablename__ = 'timetable'

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    period = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    faculty = db.Column(db.String(120), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class CGPA(db.Model):
    __tablename__ = 'cgpa'

    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(5), nullable=False)
    grade_points = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password")

    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing = User.query.filter_by(email=email).first()

        if existing:
            flash("Email already exists")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration Successful")
        return redirect(url_for("login"))

    return render_template("register.html")
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/dashboard')
@login_required
def dashboard():
    cgpa_records = CGPA.query.filter_by(user_id=current_user.id).all()
    total_credits = sum(record.credits for record in cgpa_records)
    total_points = sum(record.credits * record.grade_points for record in cgpa_records)
    current_cgpa = round(total_points / total_credits, 2) if total_credits else 0.0

    return render_template(
        'dashboard.html',
        current_date=datetime.now().strftime('%B %d, %Y'),
        notes_count=0,
        tasks=[],
        exams=[],
        recent_notes=[],
        current_cgpa=current_cgpa
    )

@app.route('/notes')
@login_required
def notes():
    return render_template('notes.html', notes=[])

@app.route('/planner')
@login_required
def planner():
    return render_template('planner.html', tasks=[])

@app.route('/exams')
@login_required
def exams():
    return render_template('exams.html', upcoming_exams=[], past_exams=[])

@app.route('/assignments')
@login_required
def assignments():
    assignments_list = Assignment.query.filter_by(user_id=current_user.id).order_by(Assignment.due_date.asc()).all()
    return render_template('assignment.html', assignments=assignments_list)

@app.route('/assignments/add', methods=['POST'])
@login_required
def add_assignment():
    title = request.form.get('title', '').strip()
    subject = request.form.get('subject', '').strip()
    due_date_str = request.form.get('due_date', '').strip()
    priority = request.form.get('priority', 'Medium').strip()
    status = request.form.get('status', 'Pending').strip()
    description = request.form.get('description', '').strip()

    if not title or not subject:
        flash('Title and subject are required for assignments.')
        return redirect(url_for('assignments'))

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid due date format. Please use YYYY-MM-DD.')
            return redirect(url_for('assignments'))

    assignment = Assignment(
        title=title,
        subject=subject,
        due_date=due_date,
        priority=priority,
        status=status,
        description=description,
        user_id=current_user.id
    )

    db.session.add(assignment)
    db.session.commit()
    return redirect(url_for('assignments'))

@app.route('/assignments/edit/<int:assignment_id>', methods=['POST'])
@login_required
def edit_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first()
    if not assignment:
        flash('Assignment not found.')
        return redirect(url_for('assignments'))

    title = request.form.get('title', '').strip()
    subject = request.form.get('subject', '').strip()
    due_date_str = request.form.get('due_date', '').strip()
    priority = request.form.get('priority', 'Medium').strip()
    status = request.form.get('status', 'Pending').strip()
    description = request.form.get('description', '').strip()

    if not title or not subject:
        flash('Title and subject are required for assignments.')
        return redirect(url_for('assignments'))

    assignment.title = title
    assignment.subject = subject
    assignment.priority = priority
    assignment.status = status
    assignment.description = description

    if due_date_str:
        try:
            assignment.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid due date format. Please use YYYY-MM-DD.')
            return redirect(url_for('assignments'))
    else:
        assignment.due_date = None

    db.session.commit()
    return redirect(url_for('assignments'))

@app.route('/assignments/delete/<int:assignment_id>', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first()
    if assignment:
        db.session.delete(assignment)
        db.session.commit()
    return redirect(url_for('assignments'))

@app.route('/attendance')
@login_required
def attendance():
    search = request.args.get('search', '').strip()
    query = Attendance.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(Attendance.subject.ilike(f'%{search}%'))
    attendance_records = query.order_by(Attendance.subject.asc()).all()
    return render_template('attendance.html', attendance_records=attendance_records, search=search)

@app.route('/attendance/add', methods=['POST'])
@login_required
def add_attendance():
    subject = request.form.get('subject', '').strip()
    total_classes = request.form.get('total_classes', '0').strip()
    attended_classes = request.form.get('attended_classes', '0').strip()

    if not subject:
        flash('Subject is required.')
        return redirect(url_for('attendance'))

    try:
        total = int(total_classes)
        attended = int(attended_classes)
    except ValueError:
        flash('Class counts must be whole numbers.')
        return redirect(url_for('attendance'))

    if total < 0 or attended < 0 or attended > total:
        flash('Please enter valid class counts.')
        return redirect(url_for('attendance'))

    percentage = round((attended / total) * 100, 2) if total else 0.0
    status = 'Good' if percentage >= 75 else 'Needs Attention'

    record = Attendance(
        subject=subject,
        total_classes=total,
        attended_classes=attended,
        attendance_percentage=percentage,
        status=status,
        user_id=current_user.id
    )
    db.session.add(record)
    db.session.commit()
    return redirect(url_for('attendance'))

@app.route('/attendance/edit/<int:attendance_id>', methods=['POST'])
@login_required
def edit_attendance(attendance_id):
    record = Attendance.query.filter_by(id=attendance_id, user_id=current_user.id).first()
    if not record:
        flash('Attendance record not found.')
        return redirect(url_for('attendance'))

    subject = request.form.get('subject', '').strip()
    total_classes = request.form.get('total_classes', '0').strip()
    attended_classes = request.form.get('attended_classes', '0').strip()

    if not subject:
        flash('Subject is required.')
        return redirect(url_for('attendance'))

    try:
        total = int(total_classes)
        attended = int(attended_classes)
    except ValueError:
        flash('Class counts must be whole numbers.')
        return redirect(url_for('attendance'))

    if total < 0 or attended < 0 or attended > total:
        flash('Please enter valid class counts.')
        return redirect(url_for('attendance'))

    percentage = round((attended / total) * 100, 2) if total else 0.0
    status = 'Good' if percentage >= 75 else 'Needs Attention'

    record.subject = subject
    record.total_classes = total
    record.attended_classes = attended
    record.attendance_percentage = percentage
    record.status = status
    db.session.commit()
    return redirect(url_for('attendance'))

@app.route('/attendance/delete/<int:attendance_id>', methods=['POST'])
@login_required
def delete_attendance(attendance_id):
    record = Attendance.query.filter_by(id=attendance_id, user_id=current_user.id).first()
    if record:
        db.session.delete(record)
        db.session.commit()
    return redirect(url_for('attendance'))

@app.route('/cgpa')
@login_required
def cgpa():
    search = request.args.get('search', '').strip()
    semester_filter = request.args.get('semester', '').strip()
    query = CGPA.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(CGPA.subject.ilike(f'%{search}%'))
    if semester_filter:
        query = query.filter(CGPA.semester == semester_filter)

    records = query.order_by(CGPA.semester.asc(), CGPA.subject.asc()).all()

    semesters = sorted({record.semester for record in CGPA.query.filter_by(user_id=current_user.id).all()})

    total_credits = sum(record.credits for record in records)
    total_points = sum(record.credits * record.grade_points for record in records)
    overall_cgpa = round(total_points / total_credits, 2) if total_credits else 0.0

    semester_summary = {}
    for semester in semesters:
        semester_records = [record for record in records if record.semester == semester]
        sem_credits = sum(record.credits for record in semester_records)
        sem_points = sum(record.credits * record.grade_points for record in semester_records)
        semester_summary[semester] = {
            'credits': sem_credits,
            'gpa': round(sem_points / sem_credits, 2) if sem_credits else 0.0
        }

    return render_template('cgpa.html', records=records, search=search, semester_filter=semester_filter, semesters=semesters, semester_summary=semester_summary, overall_cgpa=overall_cgpa, total_credits=total_credits)

@app.route('/cgpa/add', methods=['POST'])
@login_required
def add_cgpa_record():
    semester = request.form.get('semester', '').strip()
    subject = request.form.get('subject', '').strip()
    credits = request.form.get('credits', '0').strip()
    grade = request.form.get('grade', '').strip().upper()

    if not semester or not subject or not grade:
        flash('Semester, subject, and grade are required.')
        return redirect(url_for('cgpa'))

    try:
        credit_value = int(credits)
    except ValueError:
        flash('Credits must be a whole number.')
        return redirect(url_for('cgpa'))

    grade_points = {
        'O': 10,
        'A+': 9,
        'A': 8,
        'B+': 7,
        'B': 6,
        'C': 5,
        'U': 0,
    }.get(grade)

    if grade_points is None:
        flash('Please choose a valid grade.')
        return redirect(url_for('cgpa'))

    record = CGPA(
        semester=semester,
        subject=subject,
        credits=credit_value,
        grade=grade,
        grade_points=grade_points,
        user_id=current_user.id
    )
    db.session.add(record)
    db.session.commit()
    return redirect(url_for('cgpa'))

@app.route('/cgpa/edit/<int:record_id>', methods=['POST'])
@login_required
def edit_cgpa_record(record_id):
    record = CGPA.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        flash('CGPA record not found.')
        return redirect(url_for('cgpa'))

    semester = request.form.get('semester', '').strip()
    subject = request.form.get('subject', '').strip()
    credits = request.form.get('credits', '0').strip()
    grade = request.form.get('grade', '').strip().upper()

    if not semester or not subject or not grade:
        flash('Semester, subject, and grade are required.')
        return redirect(url_for('cgpa'))

    try:
        credit_value = int(credits)
    except ValueError:
        flash('Credits must be a whole number.')
        return redirect(url_for('cgpa'))

    grade_points = {
        'O': 10,
        'A+': 9,
        'A': 8,
        'B+': 7,
        'B': 6,
        'C': 5,
        'U': 0,
    }.get(grade)

    if grade_points is None:
        flash('Please choose a valid grade.')
        return redirect(url_for('cgpa'))

    record.semester = semester
    record.subject = subject
    record.credits = credit_value
    record.grade = grade
    record.grade_points = grade_points
    db.session.commit()
    return redirect(url_for('cgpa'))

@app.route('/cgpa/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_cgpa_record(record_id):
    record = CGPA.query.filter_by(id=record_id, user_id=current_user.id).first()
    if record:
        db.session.delete(record)
        db.session.commit()
    return redirect(url_for('cgpa'))

@app.route('/timetable')
@login_required
def timetable():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    periods = list(range(1, 9))
    entries = Timetable.query.filter_by(user_id=current_user.id).all()
    entries_by_day = {day: {} for day in days}

    for entry in entries:
        entries_by_day.setdefault(entry.day, {})[entry.period] = entry

    return render_template('timetable.html', days=days, periods=periods, entries_by_day=entries_by_day)

@app.route('/timetable/add', methods=['POST'])
@login_required
def add_timetable_entry():
    day = request.form.get('day', '').strip()
    period = request.form.get('period', '').strip()
    subject = request.form.get('subject', '').strip()
    faculty = request.form.get('faculty', '').strip()
    room = request.form.get('room', '').strip()

    if day not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        flash('Please select a valid day.')
        return redirect(url_for('timetable'))

    try:
        period_number = int(period)
    except ValueError:
        flash('Please enter a valid period number.')
        return redirect(url_for('timetable'))

    if not (1 <= period_number <= 8):
        flash('Period must be between 1 and 8.')
        return redirect(url_for('timetable'))

    if not subject or not faculty or not room:
        flash('Subject, faculty, and room are required.')
        return redirect(url_for('timetable'))

    existing_entry = Timetable.query.filter_by(user_id=current_user.id, day=day, period=period_number).first()

    if existing_entry:
        existing_entry.subject = subject
        existing_entry.faculty = faculty
        existing_entry.room = room
    else:
        entry = Timetable(
            day=day,
            period=period_number,
            subject=subject,
            faculty=faculty,
            room=room,
            user_id=current_user.id
        )
        db.session.add(entry)

    db.session.commit()
    return redirect(url_for('timetable'))

@app.route('/timetable/edit/<int:timetable_id>', methods=['POST'])
@login_required
def edit_timetable_entry(timetable_id):
    entry = Timetable.query.filter_by(id=timetable_id, user_id=current_user.id).first()
    if not entry:
        flash('Timetable entry not found.')
        return redirect(url_for('timetable'))

    day = request.form.get('day', '').strip()
    period = request.form.get('period', '').strip()
    subject = request.form.get('subject', '').strip()
    faculty = request.form.get('faculty', '').strip()
    room = request.form.get('room', '').strip()

    if day not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        flash('Please select a valid day.')
        return redirect(url_for('timetable'))

    try:
        period_number = int(period)
    except ValueError:
        flash('Please enter a valid period number.')
        return redirect(url_for('timetable'))

    if not (1 <= period_number <= 8):
        flash('Period must be between 1 and 8.')
        return redirect(url_for('timetable'))

    if not subject or not faculty or not room:
        flash('Subject, faculty, and room are required.')
        return redirect(url_for('timetable'))

    entry.day = day
    entry.period = period_number
    entry.subject = subject
    entry.faculty = faculty
    entry.room = room
    db.session.commit()
    return redirect(url_for('timetable'))

@app.route('/timetable/delete/<int:timetable_id>', methods=['POST'])
@login_required
def delete_timetable_entry(timetable_id):
    entry = Timetable.query.filter_by(id=timetable_id, user_id=current_user.id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('timetable'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)