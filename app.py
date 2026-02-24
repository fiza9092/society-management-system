# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from extensions import db, login_manager
from models import User, Member, Complaint, MaintenanceBill, Notice
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import random
import os

app = Flask(__name__)

# ===== SECRET KEY CONFIGURATION =====
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///society.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== ROOT ROUTE =====
@app.route('/')
def index():
    return render_template('index.html')

# ===== AUTH ROUTES =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('resident_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# ===== ADMIN DASHBOARD =====
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    # Basic counts
    members_count = Member.query.count()
    pending_complaints = Complaint.query.filter_by(status='Pending').count()
    notices = Notice.query.order_by(Notice.date_posted.desc()).limit(5).all()
    
    # Complaint statistics
    complaints = Complaint.query.order_by(Complaint.date_requested.desc()).limit(5).all()
    
    # Billing statistics
    total_collected = db.session.query(db.func.sum(MaintenanceBill.total_amount)).filter_by(status='Paid').scalar() or 0
    pending_amount = db.session.query(db.func.sum(MaintenanceBill.total_amount)).filter(MaintenanceBill.status.in_(['Unpaid', 'Overdue'])).scalar() or 0
    overdue_count = MaintenanceBill.query.filter_by(status='Overdue').count()
    
    # Recent bills
    bills = MaintenanceBill.query.order_by(MaintenanceBill.year.desc(), MaintenanceBill.month.desc()).limit(5).all()
    
    
    
    
    return render_template('admin/dashboard.html', 
                         members_count=members_count,
                         pending_complaints=pending_complaints,
                         notices=notices,
                         complaints=complaints,
                         total_collected=total_collected,
                         pending_amount=pending_amount,
                         overdue_count=overdue_count,
                         bills=bills)

# ===== MEMBER MANAGEMENT =====
@app.route('/admin/members')
@login_required
def admin_members():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    members = Member.query.all()
    return render_template('admin/members.html', members=members)

@app.route('/admin/members/delete/<int:id>')
@login_required
def delete_member(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    member = Member.query.get_or_404(id)
    
    # Check if member has related records
    if member.complaints or member.bills:
        flash('Cannot delete member with existing records!', 'danger')
        return redirect(url_for('admin_members'))
    
    # Also delete associated user
    user = User.query.filter_by(email=member.email).first()
    if user:
        db.session.delete(user)
    
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted successfully!', 'success')
    return redirect(url_for('admin_members'))

# ===== CREATE RESIDENT ACCOUNT =====
@app.route('/admin/create-resident', methods=['GET', 'POST'])
@login_required
def create_resident():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        name = request.form.get('name')
        flat_no = request.form.get('flat_no')
        contact = request.form.get('contact')
        member_type = request.form.get('member_type')
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('create_resident'))
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already exists!', 'danger')
            return redirect(url_for('create_resident'))
        
        # Create new user (resident)
        new_user = User(username=username, password=password, role='resident', email=email)
        db.session.add(new_user)
        db.session.flush()  # To get the user ID
        
        # Create member record
        new_member = Member(
            name=name, 
            flat_no=flat_no, 
            contact=contact, 
            email=email, 
            member_type=member_type
        )
        db.session.add(new_member)
        
        db.session.commit()
        flash(f'Resident account created successfully! Username: {username}', 'success')
        return redirect(url_for('admin_members'))
    
    return render_template('admin/create_resident.html')


# ===== COMPLAINTS MANAGEMENT =====
@app.route('/admin/complaints')
@login_required
def admin_complaints():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    complaints = Complaint.query.order_by(Complaint.date_requested.desc()).all()
    members = Member.query.all()
    
    # Statistics
    total = len(complaints)
    pending = Complaint.query.filter_by(status='Pending').count()
    in_progress = Complaint.query.filter_by(status='In Progress').count()
    completed = Complaint.query.filter_by(status='Completed').count()
    
    return render_template('admin/complaints.html', 
                         complaints=complaints, 
                         members=members,
                         total=total,
                         pending=pending,
                         in_progress=in_progress,
                         completed=completed)

@app.route('/admin/complaints/update/<int:id>/<status>')
@login_required
def update_complaint(id, status):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    complaint = Complaint.query.get_or_404(id)
    complaint.status = status
    
    if status == 'Completed':
        complaint.resolved_date = datetime.now()
    
    db.session.commit()
    flash(f'Complaint marked as {status}!', 'success')
    return redirect(url_for('admin_complaints'))

@app.route('/admin/complaints/add', methods=['POST'])
@login_required
def add_complaint():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    description = request.form.get('description')
    member_id = request.form.get('member_id')
    category = request.form.get('category')
    priority = request.form.get('priority')
    
    new_complaint = Complaint(
        description=description,
        member_id=member_id,
        category=category,
        priority=priority,
        status='Pending'
    )
    db.session.add(new_complaint)
    db.session.commit()
    
    flash('Complaint added successfully!', 'success')
    return redirect(url_for('admin_complaints'))

@app.route('/admin/complaints/delete/<int:id>')
@login_required
def delete_complaint(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    complaint = Complaint.query.get_or_404(id)
    db.session.delete(complaint)
    db.session.commit()
    flash('Complaint deleted!', 'success')
    return redirect(url_for('admin_complaints'))

# ===== MAINTENANCE BILLING ROUTES =====
@app.route('/admin/billing')
@login_required
def admin_billing():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    bills = MaintenanceBill.query.order_by(MaintenanceBill.year.desc(), MaintenanceBill.month.desc()).all()
    members = Member.query.all()
    
    # Statistics
    total_collected = db.session.query(db.func.sum(MaintenanceBill.total_amount)).filter_by(status='Paid').scalar() or 0
    pending_amount = db.session.query(db.func.sum(MaintenanceBill.total_amount)).filter(MaintenanceBill.status.in_(['Unpaid', 'Overdue'])).scalar() or 0
    overdue_count = MaintenanceBill.query.filter_by(status='Overdue').count()
    paid_count = MaintenanceBill.query.filter_by(status='Paid').count()
    unpaid_count = MaintenanceBill.query.filter_by(status='Unpaid').count()
    
    return render_template('admin/billing.html', 
                         bills=bills, 
                         members=members,
                         total_collected=total_collected,
                         pending_amount=pending_amount,
                         overdue_count=overdue_count,
                         paid_count=paid_count,
                         unpaid_count=unpaid_count,
                         current_month=current_month,
                         current_year=current_year)

@app.route('/admin/billing/generate', methods=['POST'])
@login_required
def generate_bill():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    member_id = request.form.get('member_id')
    month = int(request.form.get('month'))
    year = int(request.form.get('year'))
    
    # Check if bill already exists
    existing_bill = MaintenanceBill.query.filter_by(
        member_id=member_id, month=month, year=year
    ).first()
    
    if existing_bill:
        flash('Bill already exists for this month!', 'danger')
        return redirect(url_for('admin_billing'))
    
    # Get member
    member = Member.query.get(member_id)
    
    # Generate bill number
    bill_number = f"BILL/{year}/{month}/{member.flat_no}/{random.randint(1000, 9999)}"
    
    # Get settings
    settings = {
        'maintenance_amount': 1000.00,
        'sinking_fund': 200.00,
        'parking_fee': 100.00 if member.flat_no.startswith('1') else 0.00,
        'water_charges': 150.00,
        'electricity_charges': 300.00,
        'garbage_fee': 50.00
    }
    
    # Calculate due date (10th of next month)
    if month == 12:
        due_date = date(year+1, 1, 10)
    else:
        due_date = date(year, month+1, 10)
    
    # Create bill
    bill = MaintenanceBill(
        member_id=member_id,
        bill_number=bill_number,
        month=month,
        year=year,
        maintenance_amount=settings['maintenance_amount'],
        sinking_fund=settings['sinking_fund'],
        parking_fee=settings['parking_fee'],
        water_charges=settings['water_charges'],
        electricity_charges=settings['electricity_charges'],
        garbage_fee=settings['garbage_fee'],
        late_fee=0.0,
        discount=0.0,
        due_date=due_date,
        status='Unpaid'
    )
    
    bill.calculate_totals()
    db.session.add(bill)
    db.session.commit()
    
    flash(f'Bill generated successfully for {member.name}!', 'success')
    return redirect(url_for('admin_billing'))

@app.route('/admin/billing/generate-all/<int:month>/<int:year>')
@login_required
def generate_all_bills(month, year):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    members = Member.query.all()
    count = 0
    
    for member in members:
        # Check if bill exists
        existing = MaintenanceBill.query.filter_by(
            member_id=member.id, month=month, year=year
        ).first()
        
        if not existing:
            bill_number = f"BILL/{year}/{month}/{member.flat_no}/{random.randint(1000, 9999)}"
            
            if month == 12:
                due_date = date(year+1, 1, 10)
            else:
                due_date = date(year, month+1, 10)
            
            # Determine parking fee
            parking_fee = 100.00 if member.flat_no.startswith('1') else 0.00
            
            bill = MaintenanceBill(
                member_id=member.id,
                bill_number=bill_number,
                month=month,
                year=year,
                maintenance_amount=1000.00,
                sinking_fund=200.00,
                parking_fee=parking_fee,
                water_charges=150.00,
                electricity_charges=300.00,
                garbage_fee=50.00,
                late_fee=0.0,
                discount=0.0,
                due_date=due_date,
                status='Unpaid'
            )
            bill.calculate_totals()
            db.session.add(bill)
            count += 1
    
    db.session.commit()
    flash(f'Generated {count} bills for {month}/{year}!', 'success')
    return redirect(url_for('admin_billing'))

@app.route('/admin/billing/mark-paid/<int:id>', methods=['POST'])
@login_required
def mark_bill_paid(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    bill = MaintenanceBill.query.get_or_404(id)
    bill.status = 'Paid'
    bill.paid_date = date.today()
    bill.payment_method = request.form.get('payment_method')
    bill.transaction_id = request.form.get('transaction_id')
    
    db.session.commit()
    flash(f'Bill marked as paid!', 'success')
    return redirect(url_for('admin_billing'))

@app.route('/admin/billing/delete/<int:id>')
@login_required
def delete_bill(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    bill = MaintenanceBill.query.get_or_404(id)
    db.session.delete(bill)
    db.session.commit()
    flash('Bill deleted!', 'success')
    return redirect(url_for('admin_billing'))

# ===== NOTICES MANAGEMENT =====
@app.route('/admin/notices')
@login_required
def admin_notices():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    notices = Notice.query.order_by(Notice.date_posted.desc()).all()
    return render_template('admin/notices.html', notices=notices)

@app.route('/admin/notices/add', methods=['POST'])
@login_required
def add_notice():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    new_notice = Notice(title=title, content=content, posted_by=current_user.id)
    db.session.add(new_notice)
    db.session.commit()
    
    flash('Notice posted successfully!', 'success')
    return redirect(url_for('admin_notices'))

@app.route('/admin/notices/delete/<int:id>')
@login_required
def delete_notice(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    notice = Notice.query.get_or_404(id)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted successfully!', 'success')
    return redirect(url_for('admin_notices'))

# ===== RESIDENT DASHBOARD =====
@app.route('/resident/dashboard')
@login_required
def resident_dashboard():
    member = Member.query.filter_by(email=current_user.email).first()
    
    if member:
        my_complaints = Complaint.query.filter_by(member_id=member.id).count()
        pending_complaints = Complaint.query.filter_by(member_id=member.id, status='Pending').count()
        my_bills = MaintenanceBill.query.filter_by(member_id=member.id).count()
        unpaid_bills = MaintenanceBill.query.filter_by(member_id=member.id).filter(MaintenanceBill.status.in_(['Unpaid', 'Overdue'])).count()
        recent_notices = Notice.query.order_by(Notice.date_posted.desc()).limit(5).all()
        
        # Get latest bill
        latest_bill = MaintenanceBill.query.filter_by(member_id=member.id).order_by(MaintenanceBill.year.desc(), MaintenanceBill.month.desc()).first()
    else:
        my_complaints = 0
        pending_complaints = 0
        my_bills = 0
        unpaid_bills = 0
        recent_notices = []
        latest_bill = None
    
    return render_template('resident/dashboard.html', 
                         member=member,
                         my_complaints=my_complaints,
                         pending_complaints=pending_complaints,
                         my_bills=my_bills,
                         unpaid_bills=unpaid_bills,
                         recent_notices=recent_notices,
                         latest_bill=latest_bill)


# ===== RESIDENT COMPLAINTS =====
@app.route('/resident/complaints', methods=['GET', 'POST'])
@login_required
def resident_complaints():
    member = Member.query.filter_by(email=current_user.email).first()
    
    if request.method == 'POST' and member:
        description = request.form.get('description')
        category = request.form.get('category')
        priority = request.form.get('priority')
        
        new_complaint = Complaint(
            description=description, 
            member_id=member.id,
            category=category,
            priority=priority,
            status='Pending'
        )
        db.session.add(new_complaint)
        db.session.commit()
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('resident_complaints'))
    
    if member:
        complaints = Complaint.query.filter_by(member_id=member.id).order_by(Complaint.date_requested.desc()).all()
    else:
        complaints = []
    
    return render_template('resident/complaints.html', complaints=complaints)

# ===== RESIDENT BILLS =====
@app.route('/resident/bills')
@login_required
def resident_bills():
    member = Member.query.filter_by(email=current_user.email).first()
    
    if member:
        bills = MaintenanceBill.query.filter_by(member_id=member.id).order_by(MaintenanceBill.year.desc(), MaintenanceBill.month.desc()).all()
        total_paid = db.session.query(db.func.sum(MaintenanceBill.total_amount)).filter_by(member_id=member.id, status='Paid').scalar() or 0
        total_due = db.session.query(db.func.sum(MaintenanceBill.total_amount)).filter_by(member_id=member.id).filter(MaintenanceBill.status.in_(['Unpaid', 'Overdue'])).scalar() or 0
    else:
        bills = []
        total_paid = 0
        total_due = 0
    
    return render_template('resident/bills.html', 
                         bills=bills, 
                         total_paid=total_paid,
                         total_due=total_due)

# ===== RESIDENT PAY BILL =====
@app.route('/resident/bills/pay/<int:id>', methods=['GET', 'POST'])
@login_required
def pay_bill(id):
    bill = MaintenanceBill.query.get_or_404(id)
    member = Member.query.filter_by(email=current_user.email).first()
    
    if not member or bill.member_id != member.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_bills'))
    
    if request.method == 'POST':
        bill.status = 'Paid'
        bill.paid_date = date.today()
        bill.payment_method = request.form.get('payment_method')
        bill.transaction_id = request.form.get('transaction_id')
        bill.remarks = request.form.get('remarks')
        
        db.session.commit()
        flash('Payment successful! Thank you.', 'success')
        return redirect(url_for('resident_bills'))
    
    return render_template('resident/pay_bill.html', bill=bill)

# ===== RESIDENT NOTICES =====
@app.route('/resident/notices')
@login_required
def resident_notices():
    notices = Notice.query.order_by(Notice.date_posted.desc()).all()
    return render_template('resident/notices.html', notices=notices)

# ===== UPDATE OVERDUE BILLS =====
@app.route('/admin/update-overdue')
@login_required
def update_overdue_bills():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    bills = MaintenanceBill.query.filter_by(status='Unpaid').all()
    count = 0
    
    for bill in bills:
        if date.today() > bill.due_date:
            bill.status = 'Overdue'
            if bill.late_fee == 0:
                bill.late_fee = 100.00
                bill.calculate_totals()
            count += 1
    
    db.session.commit()
    flash(f'Updated {count} bills to overdue status!', 'success')
    return redirect(url_for('admin_billing'))

# ===== DATABASE INITIALIZATION =====
@app.cli.command("init-db")
def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(username='admin', password='admin123', role='admin', email='admin@society.com')
        db.session.add(admin)
        
        # Create sample resident
        resident = User(username='john', password='john123', role='resident', email='john@example.com')
        db.session.add(resident)
        
        # Create second resident
        resident2 = User(username='jane', password='jane123', role='resident', email='jane@example.com')
        db.session.add(resident2)
        
        # Add sample members
        member1 = Member(
            name='John Doe', 
            flat_no='101', 
            contact='9876543210', 
            email='john@example.com', 
            member_type='Owner'
        )
        db.session.add(member1)
        
        member2 = Member(
            name='Jane Smith', 
            flat_no='202', 
            contact='9876543211', 
            email='jane@example.com', 
            member_type='Tenant'
        )
        db.session.add(member2)
        
        # Flush to get member IDs
        db.session.flush()
        
        # Add sample complaints
        complaint1 = Complaint(
            description='Water leakage in bathroom',
            member_id=member1.id,
            category='Plumbing',
            priority='High',
            status='Pending'
        )
        db.session.add(complaint1)
        
        complaint2 = Complaint(
            description='Lift not working properly',
            member_id=member2.id,
            category='Electrical',
            priority='Urgent',
            status='In Progress'
        )
        db.session.add(complaint2)
        
        # Add sample notice
        notice = Notice(
            title='Welcome to Society', 
            content='Welcome to our society management system. Please pay your maintenance bills by 10th of every month.',
            posted_by=admin.id
        )
        db.session.add(notice)
        
        # Generate sample bills for last 3 months
        current_date = datetime.now()
        for i in range(3):
            bill_date = current_date - relativedelta(months=i)
            month = bill_date.month
            year = bill_date.year
            
            # Calculate due date (10th of next month)
            if month == 12:
                due_date = date(year + 1, 1, 10)
                paid_date = date(year + 1, 1, 5) if i > 0 else None
            else:
                due_date = date(year, month + 1, 10)
                paid_date = date(year, month + 1, 5) if i > 0 else None
            
            # Bill for member 1 (John)
            bill1 = MaintenanceBill(
                member_id=member1.id,
                bill_number=f"BILL/{year}/{month}/101/{1000 + i}",
                month=month,
                year=year,
                maintenance_amount=1000.00,
                sinking_fund=200.00,
                parking_fee=100.00,
                water_charges=150.00,
                electricity_charges=300.00,
                garbage_fee=50.00,
                late_fee=0.0,
                discount=0.0,
                due_date=due_date,
                status='Paid' if i > 0 else 'Unpaid',
                paid_date=paid_date,
                payment_method='Online' if i > 0 else None,
                transaction_id=f'TXN{year}{month}{member1.id}{i}' if i > 0 else None
            )
            bill1.calculate_totals()
            db.session.add(bill1)
            
            # Calculate due date for member 2
            if month == 12:
                due_date2 = date(year + 1, 1, 10)
                paid_date2 = date(year + 1, 1, 3) if i < 2 else None
            else:
                due_date2 = date(year, month + 1, 10)
                paid_date2 = date(year, month + 1, 3) if i < 2 else None
            
            # Bill for member 2 (Jane)
            bill2 = MaintenanceBill(
                member_id=member2.id,
                bill_number=f"BILL/{year}/{month}/202/{2000 + i}",
                month=month,
                year=year,
                maintenance_amount=1000.00,
                sinking_fund=200.00,
                parking_fee=0.00,
                water_charges=150.00,
                electricity_charges=300.00,
                garbage_fee=50.00,
                late_fee=0.0,
                discount=0.0,
                due_date=due_date2,
                status='Paid' if i < 2 else 'Unpaid',
                paid_date=paid_date2,
                payment_method='Cash' if i < 2 else None,
                transaction_id=f'TXN{year}{month}{member2.id}{i}' if i < 2 else None
            )
            bill2.calculate_totals()
            db.session.add(bill2)
        
        # Add an overdue bill for testing
        last_month = current_date - relativedelta(months=1)
        month = last_month.month
        year = last_month.year
        
        if month == 12:
            overdue_due_date = date(year + 1, 1, 10)
        else:
            overdue_due_date = date(year, month + 1, 10)
        
        overdue_bill = MaintenanceBill(
            member_id=member1.id,
            bill_number=f"BILL/{year}/{month}/101/OVERDUE",
            month=month,
            year=year,
            maintenance_amount=1000.00,
            sinking_fund=200.00,
            parking_fee=100.00,
            water_charges=150.00,
            electricity_charges=300.00,
            garbage_fee=50.00,
            late_fee=100.00,
            discount=0.0,
            due_date=overdue_due_date,
            status='Overdue',
            paid_date=None,
            payment_method=None,
            transaction_id=None
        )
        overdue_bill.calculate_totals()
        db.session.add(overdue_bill)
        
        db.session.commit()
        print("=" * 60)
        print("DATABASE INITIALIZED WITH SAMPLE DATA!")
        print("=" * 60)
        print("Admin Login: admin / admin123")
        print("Resident Logins:")
        print("  - John: john / john123 (Flat 101, Owner)")
        print("  - Jane: jane / jane123 (Flat 202, Tenant)")
        print("=" * 60)
        print("\nBilling Sample Data:")
        print("✅ Paid bills for previous months")
        print("✅ Unpaid bill for current month")
        print("✅ Overdue bill for testing late fees")
        print("=" * 60)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)