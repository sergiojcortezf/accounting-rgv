from app import create_app, db
from app.models import Account, Expense, Payment, ExpenseStatus, PaymentStatus
from datetime import datetime, timedelta
import random

app = create_app()

def seed_data():
    with app.app_context():
        print("Iniciando sembrado de datos...")
        
        db.drop_all()
        db.create_all()
        print("Base de datos limpiada y recreada.")

        accounts = [
            Account(name="BBVA Principal", account_number="0123456789", balance=150000.00, currency="MXN"),
            Account(name="Santander Nómina", account_number="9876543210", balance=45000.50, currency="MXN"),
            Account(name="Caja Chica Efectivo", account_number="EFECTIVO-01", balance=5000.00, currency="MXN")
        ]
        db.session.add_all(accounts)
        db.session.commit()
        print(f"Se crearon {len(accounts)} cuentas bancarias.")

        categories = ["Oficina", "Viáticos", "Software", "Nómina", "Marketing", "Mantenimiento"]
        expenses = []
        
        for i in range(20):
            days_ago = random.randint(0, 30)
            date = datetime.now() - timedelta(days=days_ago)
            amount = round(random.uniform(500.00, 15000.00), 2)
            category = random.choice(categories)
            
            status_choice = random.choice(list(ExpenseStatus))
            
            # Evitamos estados intermedios complejos para el seed simple, 
            # nos enfocamos en: Borrador, Pendiente, Aprobado y Pagado.
            if status_choice == ExpenseStatus.IN_PAYMENT: 
                status_choice = ExpenseStatus.APPROVED
            
            expense = Expense(
                description=f"Gasto simulado #{i+1} - {category}",
                amount=amount,
                category=category,
                date_incurred=date,
                status=status_choice
            )
            expenses.append(expense)

        db.session.add_all(expenses)
        db.session.commit()

        # 4. Generar Pagos para los gastos que salieron como 'PAID'
        # (Para mantener la integridad de datos)
        paid_expenses = [e for e in expenses if e.status == ExpenseStatus.PAID]
        
        for expense in paid_expenses:
            # Elegir cuenta al azar
            acc = random.choice(accounts)
            
            payment = Payment(
                amount=expense.amount,
                expense_id=expense.id,
                account_id=acc.id,
                status=PaymentStatus.PAID,
                payment_date=expense.date_incurred, # Asumimos se pagó el mismo día
                reference_code=f"SEED-{random.randint(1000,9999)}"
            )

            acc.balance = float(acc.balance) - float(expense.amount)
            db.session.add(payment)
        
        db.session.commit()
        print(f"Se crearon {len(expenses)} gastos y {len(paid_expenses)} pagos históricos.")
        print("¡Datos listos para la demo!")

if __name__ == "__main__":
    seed_data()