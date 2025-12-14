# Especificación de Requisitos y Arquitectura: Sistema Financiero RGV

**Autor:** Sergio Cortez  
**Rol:** Ingeniero de Software Full-Stack  
**Fecha:** Diciembre, 2025

---

## 1. Introducción

### 1.1 Propósito

Este documento define la arquitectura y las decisiones de diseño para el Sistema de Gestión de Gastos de RGV. El objetivo es digitalizar y automatizar el flujo de aprobación de gastos y su conciliación con cuentas bancarias reales.

### 1.2 Alcance

El sistema abarca desde la solicitud de un gasto por un empleado, su ciclo de aprobación por la gerencia, hasta la ejecución del pago por tesorería, afectando los saldos bancarios en tiempo real.

---

## 2. Requerimientos del Negocio

### 2.1 Flujo de Aprobación (Workflow)

El sistema implementa una máquina de estados para garantizar que ningún gasto se pague sin autorización:

1.  **Solicitud:** El usuario crea un gasto (Estado: `Borrador`).
2.  **Revisión:** El usuario envía el gasto a gerencia (Estado: `Por Aprobar`).
3.  **Decisión:** El gerente aprueba o rechaza.
    - Si **Rechaza**: El flujo termina.
    - Si **Aprueba**: El gasto queda habilitado para pago.

### 2.2 Lógica Financiera (Tesorería)

- **Validación de Saldo:** El sistema no debe permitir pagar un gasto si la cuenta bancaria seleccionada no tiene fondos suficientes (`Account.balance >= Expense.amount`).
- **Integridad:** Al confirmar un pago, se debe restar el monto de la cuenta y actualizar el estado del gasto a `PAGADO` en una sola transacción atómica.

---

## 3. Arquitectura del Sistema

### 3.1 Diagrama Entidad-Relación (ERD)

Se diseñó un modelo relacional normalizado para asegurar la integridad de datos.

- **Accounts (1) ↔ (N) Payments:** Una cuenta bancaria tiene múltiples pagos históricos.
- **Expenses (1) ↔ (1) Payments:** Un gasto tiene asociada una única orden de pago exitosa.

> _Ver diagrama completo en: `docs/diagrama_er.png`_

### 3.2 Diagrama de Flujo (BPMN)

El proceso sigue un carril lógico separado por roles (Solicitante, Aprobador, Sistema).

> _Ver diagrama completo en: `docs/diagrama_flujo.png`_

---

## 4. Decisiones de Diseño y Justificación

### 4.1 Uso de MySQL y SQLAlchemy

- **Decisión:** Uso de base de datos relacional (MySQL 8) con ORM.
- **Justificación:** Al tratarse de datos financieros, se requiere consistencia estricta (ACID). NoSQL no es adecuado para manejo de saldos contables donde la precisión decimal y las relaciones son críticas. SQLAlchemy permite manejar transacciones (`commit`/`rollback`) para asegurar que el dinero no se pierda si hay un error a mitad del proceso.

### 4.2 Renderizado del lado del Servidor (Jinja2)

- **Decisión:** Uso de Flask + Jinja2 en lugar de una SPA (React/Angular).
- **Justificación:** Dado el requisito de tiempo de entrega y la naturaleza del aplicativo (Dashboard administrativo interno), el renderizado en servidor simplifica la arquitectura, elimina la necesidad de una API REST compleja para todo el CRUD y facilita el despliegue en un solo contenedor.

### 4.3 Validación de "Doble Partida"

- **Decisión:** El modelo `Payment` actúa como tabla pivote con lógica.
- **Justificación:** Separar `Expense` (la obligación) de `Payment` (la transacción) permite tener gastos aprobados que aún no se han pagado, y permite auditar _cuándo_ y _desde qué cuenta_ salió el dinero exacto.

### 4.4 Dockerización

- **Decisión:** Entorno completo en `docker-compose`.
- **Justificación:** Garantiza que el evaluador pueda ejecutar el proyecto con un solo comando, eliminando el clásico problema de "funciona en mi máquina" debido a diferencias de versiones de Python o configuración de MySQL local.

---

## 5. Casos Límite Considerados (Edge Cases)

1.  **Fondos Insuficientes:** El sistema bloquea el intento de pago antes de tocar la base de datos si `Saldo < Monto`.
2.  **Cancelación de Pagos:** Se implementó un flujo de reversa. Si un pago se cancela, el Gasto regresa a estado `APROBADO` (no se elimina), permitiendo intentar el pago nuevamente con otra cuenta bancaria.
3.  **Edición Bloqueada:** Un gasto no se puede editar ni borrar una vez que ha sido enviado a aprobación o pagado, garantizando la inmutabilidad de la historia financiera.
