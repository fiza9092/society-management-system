from extensions import db
from flask_login import UserMixin
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'resident'
    email = db.Column(db.String(100), unique=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    flat_no = db.Column(db.String(10), nullable=False)
    contact = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True)
    member_type = db.Column(db.String(20))  # 'Owner' or 'Tenant'
    join_date = db.Column(db.DateTime, default=datetime.now)
    
    complaints = db.relationship('Complaint', backref='member', lazy=True)
    bills = db.relationship('MaintenanceBill', backref='member', lazy=True)


class Complaint(db.Model):
    __tablename__ = 'complaint'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    date_requested = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'In Progress', 'Completed'
    category = db.Column(db.String(50), default='General')  # 'Plumbing', 'Electrical', 'Cleaning', 'Other'
    priority = db.Column(db.String(20), default='Medium')  # 'Low', 'Medium', 'High', 'Urgent'
    assigned_to = db.Column(db.String(100))
    resolved_date = db.Column(db.DateTime)
    remarks = db.Column(db.Text)

class MaintenanceBill(db.Model):
    __tablename__ = 'maintenance_bill'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    bill_number = db.Column(db.String(50), unique=True, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    
    # Bill Details - Set default values to 0.0 instead of None
    maintenance_amount = db.Column(db.Float, default=0.0, nullable=False)
    sinking_fund = db.Column(db.Float, default=0.0, nullable=False)
    parking_fee = db.Column(db.Float, default=0.0, nullable=False)
    water_charges = db.Column(db.Float, default=0.0, nullable=False)
    electricity_charges = db.Column(db.Float, default=0.0, nullable=False)
    garbage_fee = db.Column(db.Float, default=0.0, nullable=False)
    late_fee = db.Column(db.Float, default=0.0, nullable=False)
    discount = db.Column(db.Float, default=0.0, nullable=False)
    
    # Totals
    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    
    # Status
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Unpaid', nullable=False)  # 'Unpaid', 'Paid', 'Overdue', 'Partially Paid'
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    remarks = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def calculate_totals(self):
        # Ensure all values are floats (not None)
        self.maintenance_amount = float(self.maintenance_amount or 0.0)
        self.sinking_fund = float(self.sinking_fund or 0.0)
        self.parking_fee = float(self.parking_fee or 0.0)
        self.water_charges = float(self.water_charges or 0.0)
        self.electricity_charges = float(self.electricity_charges or 0.0)
        self.garbage_fee = float(self.garbage_fee or 0.0)
        self.late_fee = float(self.late_fee or 0.0)
        self.discount = float(self.discount or 0.0)
        
        self.subtotal = (self.maintenance_amount + self.sinking_fund + self.parking_fee + 
                        self.water_charges + self.electricity_charges + self.garbage_fee)
        self.total_amount = self.subtotal + self.late_fee - self.discount
        
    def check_overdue(self):
        if self.status == 'Unpaid' and date.today() > self.due_date:
            self.status = 'Overdue'
            # Add late fee if not already added
            if self.late_fee == 0:
                self.late_fee = 100.00  # Standard late fee
                self.calculate_totals()
class MaintenanceSetting(db.Model):
    """Global maintenance settings"""
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True)
    setting_value = db.Column(db.Float, default=0.0)
    description = db.Column(db.String(200))
    
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('maintenance_bill.id'))
    amount = db.Column(db.Float)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    remarks = db.Column(db.Text)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))