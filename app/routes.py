from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .models import db, Account, Expense, Payment, ExpenseStatus, PaymentStatus
from decimal import Decimal

main_bp = Blueprint('main', __name__)

@main_bp.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Retorna todas las cuentas en formato JSON"""
    accounts = Account.query.all()
    return jsonify([{
        'id': a.id,
        'name': a.name,
        'account_number': a.account_number,
        'balance': float(a.balance), # Convertimos Decimal a float para JSON
        'currency': a.currency
    } for a in accounts])

@main_bp.route('/api/accounts', methods=['POST'])
def create_account():
    """Crea una nueva cuenta bancaria"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'account_number' not in data:
        return jsonify({'error': 'Faltan datos obligatorios'}), 400

    try:
        new_account = Account(
            name=data['name'],
            account_number=data['account_number'],
            balance=data.get('balance', 0.00),
            currency=data.get('currency', 'MXN')
        )
        db.session.add(new_account)
        db.session.commit()
        return jsonify({'message': 'Cuenta creada exitosamente', 'id': new_account.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/')
def index():
    return "<h1>El sistema Accounting RGV está funcionando 🚀</h1>"