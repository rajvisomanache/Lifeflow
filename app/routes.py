from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from . import db
from .models import Hospital, AdminUser, Donor, Recipient, Inventory, DonationLog, BloodRequest, BloodTransfer
from datetime import datetime

routes_bp = Blueprint('routes', __name__, template_folder='templates', static_folder='static')

# -------------------------------
# HTML Page Routes
# -------------------------------

@routes_bp.route('/login-page')
def login_page():
    """Login/Signup page."""
    return render_template('login.html')

@routes_bp.route('/donate-page')
def donate_page():
    """Add Donor page (accessible after login)."""
    return render_template('donate.html')

@routes_bp.route('/dashboard')
def dashboard():
    """Dashboard after login."""
    return redirect(url_for('routes.donate_page'))


# -------------------------------
# Admin Auth: Login & Signup
# -------------------------------

@routes_bp.route('/login', methods=['POST'])
def login_api():
    data = request.get_json()
    email, password = data.get('email'), data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = AdminUser.query.filter_by(email=email).first()
    if user and user.check_password(password):
        return jsonify({"message": "Login successful!", "redirect_url": url_for('routes.dashboard')}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@routes_bp.route('/signup', methods=['POST'])
def signup_api():
    data = request.get_json()
    name, email, password = data.get('name'), data.get('email'), data.get('password')

    if not all([name, email, password]):
        return jsonify({"error": "Missing required fields"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if AdminUser.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    try:
        new_user = AdminUser(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Signup successful! Please login."}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Signup Error: {e}")
        return jsonify({"error": "Internal error during signup"}), 500


# -------------------------------
# Donor Management
# -------------------------------

@routes_bp.route('/donors', methods=['GET'])
def get_donors():
    try:
        donors = Donor.query.all()
        return jsonify([{
            "id": d.id,
            "name": d.name,
            "blood_type": d.blood_type,
            "contact_info": d.contact_info,
            "last_donation_date": d.last_donation_date.isoformat() if d.last_donation_date else None
        } for d in donors]), 200
    except Exception as e:
        print(f"Error fetching donors: {e}")
        return jsonify({"error": "Could not retrieve donors"}), 500

@routes_bp.route('/donors', methods=['POST'])
def add_donor():
    data = request.get_json()
    name = data.get('name')
    blood_type = data.get('blood_type')
    contact_info = data.get('contact_info')
    last_donation_date_str = data.get('last_donation_date')

    if not name or not blood_type:
        return jsonify({"error": "Name and blood type are required"}), 400

    valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    if blood_type.upper() not in valid_types:
        return jsonify({"error": "Invalid blood type"}), 400

    try:
        last_donation_date = datetime.strptime(last_donation_date_str, '%Y-%m-%d').date() if last_donation_date_str else None

        donor = Donor(name=name, blood_type=blood_type.upper(), contact_info=contact_info, last_donation_date=last_donation_date)
        db.session.add(donor)
        db.session.commit()

        return jsonify({
            "message": f"Donor '{donor.name}' added successfully!",
            "donor": {
                "id": donor.id,
                "name": donor.name,
                "blood_type": donor.blood_type,
                "contact_info": donor.contact_info,
                "last_donation_date": donor.last_donation_date.isoformat() if donor.last_donation_date else None
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding donor: {e}")
        return jsonify({"error": "Failed to add donor"}), 500


# -------------------------------
# Hospital Management
# -------------------------------

@routes_bp.route('/hospitals', methods=['GET'])
def get_hospitals():
    try:
        hospitals = Hospital.query.all()
        return jsonify([{
            "id": h.id, "name": h.name, "location": h.location, "contact_info": h.contact_info
        } for h in hospitals]), 200
    except Exception as e:
        print(f"Error getting hospitals: {e}")
        return jsonify({"error": "Could not retrieve hospitals"}), 500

@routes_bp.route('/hospitals', methods=['POST'])
def add_hospital():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Missing hospital name"}), 400

    try:
        hospital = Hospital(**data)
        db.session.add(hospital)
        db.session.commit()
        return jsonify({"message": f"Hospital '{hospital.name}' added", "id": hospital.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding hospital: {e}")
        return jsonify({"error": "Failed to add hospital"}), 500


# -------------------------------
# Inventory Management
# -------------------------------

@routes_bp.route('/inventory', methods=['GET'])
def get_inventory():
    try:
        inventory = Inventory.query.all()
        return jsonify([{
            "id": i.id, "blood_type": i.blood_type, "units": i.units, "hospital_id": i.hospital_id
        } for i in inventory]), 200
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        return jsonify({"error": "Could not retrieve inventory"}), 500

@routes_bp.route('/inventory', methods=['POST'])
def add_inventory():
    data = request.get_json()
    blood_type = data.get('blood_type')
    units = data.get('units')
    hospital_id = data.get('hospital_id')

    if not all([blood_type, units is not None, hospital_id]):
        return jsonify({"error": "Missing required fields"}), 400
    if not isinstance(units, int) or units < 0:
        return jsonify({"error": "Units must be a non-negative integer"}), 400

    try:
        inventory = Inventory.query.filter_by(blood_type=blood_type.upper(), hospital_id=hospital_id).first()
        if inventory:
            inventory.units += units
            db.session.commit()
            return jsonify({"message": "Inventory updated", "id": inventory.id}), 200
        else:
            new_inventory = Inventory(blood_type=blood_type.upper(), units=units, hospital_id=hospital_id)
            db.session.add(new_inventory)
            db.session.commit()
            return jsonify({"message": "Inventory added", "id": new_inventory.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Inventory error: {e}")
        return jsonify({"error": "Failed to manage inventory"}), 500

# -------------------------
# Recipients API Routes
# -------------------------
@routes_bp.route('/recipients', methods=['GET'])
def get_recipients():
    try:
        recipients = Recipient.query.all()
        return jsonify([{
            "id": r.id,
            "name": r.name,
            "blood_type": r.blood_type,
            "hospital_id": r.hospital_id,
            "contact_info": r.contact_info,
            "request_date": r.request_date.isoformat() if r.request_date else None
        } for r in recipients]), 200
    except Exception as e:
        print(f"Error fetching recipients: {e}")
        return jsonify({"error": "Could not retrieve recipients"}), 500


@routes_bp.route('/recipients', methods=['POST'])
def add_recipient():
    data = request.get_json()
    name = data.get('name')
    blood_type = data.get('blood_type')
    hospital_id = data.get('hospital_id')
    contact_info = data.get('contact_info')
    request_date_str = data.get('request_date')

    if not all([name, blood_type, hospital_id]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        from datetime import datetime
        request_date = datetime.strptime(request_date_str, '%Y-%m-%d').date() if request_date_str else None
        recipient = Recipient(
            name=name,
            blood_type=blood_type.upper(),
            hospital_id=hospital_id,
            contact_info=contact_info,
            request_date=request_date
        )
        db.session.add(recipient)
        db.session.commit()
        return jsonify({"message": f"Recipient '{recipient.name}' added", "id": recipient.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding recipient: {e}")
        return jsonify({"error": "Failed to add recipient"}), 500

# -------------------------
# Blood Transfer Logs API Routes
# -------------------------
@routes_bp.route('/transfers', methods=['GET'])
def get_transfers():
    try:
        transfers = BloodTransfer.query.all()
        return jsonify([{
            "id": t.id,
            "recipient_id": t.recipient_id,
            "inventory_id": t.inventory_id,
            "units_transferred": t.units_transferred,
            "transfer_date": t.transfer_date.isoformat() if t.transfer_date else None
        } for t in transfers]), 200
    except Exception as e:
        print(f"Error retrieving transfer logs: {e}")
        return jsonify({"error": "Failed to fetch transfers"}), 500


@routes_bp.route('/transfers', methods=['POST'])
def add_transfer():
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    inventory_id = data.get('inventory_id')
    units_transferred = data.get('units_transferred')
    transfer_date_str = data.get('transfer_date')

    if not all([recipient_id, inventory_id, units_transferred]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        from datetime import datetime
        transfer_date = datetime.strptime(transfer_date_str, '%Y-%m-%d').date() if transfer_date_str else None

        transfer = BloodTransfer(
            recipient_id=recipient_id,
            inventory_id=inventory_id,
            units_transferred=units_transferred,
            transfer_date=transfer_date
        )
        db.session.add(transfer)
        db.session.commit()
        return jsonify({"message": "Blood transfer recorded", "id": transfer.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error recording transfer: {e}")
        return jsonify({"error": "Failed to record transfer"}), 500


