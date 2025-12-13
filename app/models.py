from datetime import datetime
import enum
from . import db

# --- ENUMS (Definición de los flujos de estado) ---
class ExpenseStatus(enum.Enum):
    DRAFT = "Borrador"               # Edición libre
    PENDING = "Por Aprobar"          # Enviado a jefe
    APPROVED = "Aprobado"            # Listo para generar pago
    REJECTED = "Rechazado"           # Fin del flujo
    IN_PAYMENT = "En Proceso de Pago" # Ya se generó la orden de pago (bloqueado)

class PaymentStatus(enum.Enum):
    PENDING = "Programado"           # Creado automáticamente
    APPROVED = "Autorizado"          # Tesorería confirma
    PAID = "Pagado / Ejecutado"      # Dinero descontado de cuenta
    CANCELLED = "Cancelado"          # Reverso de operación

# --- MODELOS ---

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=False, unique=True)
    balance = db.Column(db.Numeric(12, 2), default=0.00) 
    currency = db.Column(db.String(3), default='MXN')
    
    payments = db.relationship('Payment', backref='account', lazy=True)

    def __repr__(self):
        return f'<Account {self.name} | ${self.balance}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date_incurred = db.Column(db.Date, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum(ExpenseStatus), default=ExpenseStatus.DRAFT)
    
    # Relación 1 a 1: Un gasto tiene una orden de pago
    payment = db.relationship('Payment', backref='expense', uselist=False)

    def __repr__(self):
        return f'<Expense {self.description} | {self.status.value}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Flujo propio del pago (Requisito clave del examen)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    payment_date = db.Column(db.DateTime, nullable=True) # Se llena al pasar a PAID
    reference_code = db.Column(db.String(50), nullable=True)
    
    # Foreign Keys
    # unique=True en expense_id asegura que no pagues doble el mismo gasto
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False, unique=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)

    def __repr__(self):
        return f'<Payment {self.id} | Status: {self.status.value}>'