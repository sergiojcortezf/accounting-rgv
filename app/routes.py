from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .models import db, Account, Expense, Payment, ExpenseStatus, PaymentStatus
from decimal import Decimal
from datetime import datetime

main_bp = Blueprint('main', __name__)

# --- RUTAS DE API (JSON) PARA CUENTAS ---

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

# --- API DE GASTOS (EXPENSES) ---

@main_bp.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Listar todos los gastos ordenados por fecha"""
    expenses = Expense.query.order_by(Expense.date_incurred.desc()).all()
    result = []
    for e in expenses:
        result.append({
            'id': e.id,
            'description': e.description,
            'amount': float(e.amount),
            'category': e.category,
            'status': e.status.value, # Enviamos el texto legible (Ej: "Por Aprobar")
            'date': e.date_incurred.strftime('%Y-%m-%d'),
            # Si tiene pago, mandamos info básica
            'payment_status': e.payment.status.value if e.payment else 'N/A'
        })
    return jsonify(result)

@main_bp.route('/api/expenses', methods=['POST'])
def create_expense():
    """Crear un nuevo gasto en estado BORRADOR"""
    data = request.get_json()
    
    try:
        fecha_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        new_expense = Expense(
            description=data['description'],
            amount=data['amount'],
            category=data['category'],
            date_incurred=fecha_obj,
            status=ExpenseStatus.DRAFT
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({'message': 'Gasto registrado', 'id': new_expense.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@main_bp.route('/api/expenses/<int:id>/action', methods=['POST'])
def change_expense_status(id):
    """
    MÁQUINA DE ESTADOS:
    Recibe una acción: 'send', 'approve', 'reject'
    y cambia el estatus según las reglas del diagrama.
    """
    expense = Expense.query.get_or_404(id)
    data = request.get_json()
    action = data.get('action')

    # Reglas de Negocio (State Machine)
    if action == 'send':
        if expense.status == ExpenseStatus.DRAFT:
            expense.status = ExpenseStatus.PENDING
        else:
            return jsonify({'error': 'Solo borradores pueden enviarse a revisión'}), 400
            
    elif action == 'approve':
        if expense.status == ExpenseStatus.PENDING:
            expense.status = ExpenseStatus.APPROVED
        else:
            return jsonify({'error': 'El gasto no está en revisión'}), 400
            
    elif action == 'reject':
        if expense.status == ExpenseStatus.PENDING:
            expense.status = ExpenseStatus.REJECTED
        else:
            return jsonify({'error': 'El gasto no está en revisión'}), 400
            
    else:
        return jsonify({'error': 'Acción no válida'}), 400

    db.session.commit()
    return jsonify({'message': f'Estado actualizado a: {expense.status.value}'})

# --- API DE PAGOS (PAYMENTS) Y TESORERÍA ---

@main_bp.route('/api/payments/prepare', methods=['POST'])
def prepare_payment():
    """
    PASO 1: BOTÓN "GENERAR PAGO"
    - Recibe: expense_id, account_id
    - Verifica: ¿El gasto está aprobado? ¿Hay fondos suficientes?
    - Acción: Crea el objeto Payment (Pendiente) y bloquea el Gasto (En Proceso).
    """
    data = request.get_json()
    expense_id = data.get('expense_id')
    account_id = data.get('account_id')
    
    expense = Expense.query.get_or_404(expense_id)
    account = Account.query.get_or_404(account_id)
    
    # 1. Validaciones de Negocio
    if expense.status != ExpenseStatus.APPROVED:
        return jsonify({'error': 'El gasto no está APROBADO para pago'}), 400
        
    if account.balance < expense.amount:
        return jsonify({'error': 'Fondos Insuficientes en la cuenta seleccionada'}), 400
        
    try:
        # 2. Crear el Pago (Estado: PENDING / Programado)
        new_payment = Payment(
            amount=expense.amount,
            expense_id=expense.id,
            account_id=account.id,
            status=PaymentStatus.PENDING,
            reference_code=f"REF-{datetime.now().strftime('%H%M%S')}" # Generamos una ref temporal
        )
        
        # 3. Bloquear el Gasto para que nadie más lo pague
        expense.status = ExpenseStatus.IN_PAYMENT
        
        db.session.add(new_payment)
        db.session.commit()
        
        return jsonify({
            'message': 'Pago programado exitosamente. Requiere confirmación.', 
            'payment_id': new_payment.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/payments/<int:payment_id>/confirm', methods=['POST'])
def confirm_payment(payment_id):
    """
    PASO 2: EJECUTAR PAGO (DOBLE PARTIDA)
    - Acción: Resta el saldo de la cuenta y marca todo como PAGADO.
    """
    payment = Payment.query.get_or_404(payment_id)
    account = Account.query.get(payment.account_id)
    expense = Expense.query.get(payment.expense_id)
    
    if payment.status != PaymentStatus.PENDING:
        return jsonify({'error': 'El pago no está pendiente'}), 400
        
    try:        
        # 1. Restar dinero (Salida de Banco)
        account.balance -= payment.amount
        
        # 2. Actualizar estados
        payment.status = PaymentStatus.PAID
        payment.payment_date = datetime.utcnow()
        expense.status = ExpenseStatus.PAID
        
        db.session.commit()
        
        return jsonify({'message': 'Pago ejecutado correctamente. Saldo actualizado.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error en transacción: {str(e)}'}), 500

@main_bp.route('/api/payments/<int:payment_id>/cancel', methods=['POST'])
def cancel_payment(payment_id):
    """
    FLUJO ALTERNO: CANCELAR OPERACIÓN
    - Acción: Cancela el pago y LIBERA el gasto (regresa a Aprobado)
    """
    payment = Payment.query.get_or_404(payment_id)
    expense = Expense.query.get(payment.expense_id)
    
    if payment.status != PaymentStatus.PENDING:
        return jsonify({'error': 'Solo se pueden cancelar pagos pendientes'}), 400
        
    try:
        payment.status = PaymentStatus.CANCELLED
        expense.status = ExpenseStatus.APPROVED 
        
        db.session.commit()
        return jsonify({'message': 'Pago cancelado. Gasto liberado para nuevo intento.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- VISTAS FRONTEND (HTML) ---

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/accounts')
def view_accounts():
    # Obtenemos todas las cuentas para pasarlas a la plantilla
    accounts = Account.query.all()
    return render_template('accounts.html', accounts=accounts)

@main_bp.route('/expenses')
def view_expenses():
    # Obtenemos gastos ordenados recientes primero
    expenses = Expense.query.order_by(Expense.date_incurred.desc()).all()
    return render_template('expenses.html', expenses=expenses, now_date=datetime.now().strftime('%Y-%m-%d'))