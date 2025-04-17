# app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

# db = SQLAlchemy() # db instance is now created in __init__.py
from . import db # Import db from the current package (__init__.py)

class Hospital(db.Model):
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255))
    contact_info = db.Column(db.String(255))

    def __repr__(self):
        return f"<Hospital {self.name}>"


class AdminUser(db.Model):
    __tablename__ = 'adminusers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # Store HASHED passwords, never plain text
    password_hash = db.Column(db.String(255), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=True) # Allow null hospital?

    hospital = db.relationship('Hospital', backref='admin_users')

    # Method to set password (hashes it)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<AdminUser {self.email}>"


class Donor(db.Model):
    __tablename__ = 'donors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    blood_type = db.Column(db.String(3), nullable=False) # Consider validation (e.g., A+, B-, O+, etc.)
    contact_info = db.Column(db.String(255))
    last_donation_date = db.Column(db.Date)

    def __repr__(self):
        return f"<Donor {self.name} - {self.blood_type}>"


class Recipient(db.Model):
    __tablename__ = 'recipients'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    blood_type = db.Column(db.String(3), nullable=False)
    contact_info = db.Column(db.String(255))
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id', ondelete='SET NULL'), nullable=True)
    hospital = db.relationship('Hospital', backref='recipients')

    def __repr__(self):
        return f"<Recipient {self.name} - {self.blood_type}>"


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    blood_type = db.Column(db.String(3), nullable=False)
    units = db.Column(db.Integer, nullable=False, default=0)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False)
    hospital = db.relationship('Hospital', backref='inventory')
    __table_args__ = (
        db.UniqueConstraint('blood_type', 'hospital_id', name='uix_blood_hospital'),
    )

    def __repr__(self):
        return f"<Inventory {self.blood_type} @ Hospital {self.hospital_id}: {self.units} units>"


class DonationLog(db.Model):
    __tablename__ = 'donationlog'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id', ondelete='CASCADE'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False)
    blood_type = db.Column(db.String(3), nullable=False)
    units_donated = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=date.today)
    donor = db.relationship('Donor', backref='donation_logs')
    hospital = db.relationship('Hospital', backref='donation_logs')

    def __repr__(self):
        return f"<DonationLog Donor {self.donor_id} -> Hospital {self.hospital_id} | {self.units_donated} units on {self.date}>"


class BloodRequest(db.Model):
    __tablename__ = 'bloodrequests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipients.id', ondelete='CASCADE'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False)
    blood_type = db.Column(db.String(3), nullable=False)
    units_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending') # Consider Enum for status
    request_date = db.Column(db.Date, default=date.today)
    recipient = db.relationship('Recipient', backref='blood_requests')
    hospital = db.relationship('Hospital', backref='blood_requests')

    def __repr__(self):
        return f"<BloodRequest {self.blood_type} x {self.units_requested} for Recipient {self.recipient_id} @ Hospital {self.hospital_id}>"


class BloodTransfer(db.Model):
    __tablename__ = 'bloodtransfers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False)
    to_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False)
    blood_type = db.Column(db.String(3), nullable=False)
    units_transferred = db.Column(db.Integer, nullable=False)
    transfer_date = db.Column(db.Date, default=date.today)
    from_hospital = db.relationship('Hospital', foreign_keys=[from_hospital_id], backref='outgoing_transfers')
    to_hospital = db.relationship('Hospital', foreign_keys=[to_hospital_id], backref='incoming_transfers')

    def __repr__(self):
        return f"<BloodTransfer {self.units_transferred} units {self.blood_type} from {self.from_hospital_id} to {self.to_hospital_id}>"
