# 📈 Sistema Financiero RGV

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)

> Una solución full-stack robusta para la gestión de ciclo de gastos, aprobaciones y transacciones bancarias, asegurando integridad financiera.

## 🚀 Características Principales

- **Integridad Transaccional:** Implementación estricta de lógica de doble partida. El dinero no se crea ni se destruye, solo se transfiere mediante transacciones atómicas (`ACID`).
- **Máquina de Estados Finita:** Control estricto del ciclo de vida del gasto: `Borrador` → `Por Aprobar` → `Aprobado` → `Pagado` (o `Rechazado`).
- **Dashboard Ejecutivo:** Visualización de KPIs financieros en tiempo real utilizando **Chart.js** (Saldos globales, desglose por categorías y estatus).
- **Validación de Fondos:** Sistema inteligente ("Botón Mágico") que impide la generación de órdenes de pago si la cuenta origen no tiene saldo suficiente.
- **Data Seeding:** Script automatizado para poblar la base de datos con escenarios financieros complejos para demostraciones.
- **Infraestructura Sólida:**
  - 🐳 **Dockerized:** Base de datos MySQL 8.0 y Aplicación Python orquestadas con Docker Compose.
  - 🛡️ **Seguridad:** Manejo de variables de entorno y prevención de inyección SQL vía ORM.

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.11, Flask 3.0, SQLAlchemy (ORM).
- **Base de Datos:** MySQL 8.0 (Persistencia Relacional).
- **Frontend:** HTML5, Bootstrap 5, Jinja2 (Server-Side Rendering), Chart.js.
- **Infraestructura:** Docker & Docker Compose.
- **Librerías Clave:** `PyMySQL`, `Axios`.

## ⚡ Inicio Rápido

1.  **Clonar y arrancar:**

    ```bash
    git clone https://github.com/sergiojcortezf/accounting-rgv
    cd accounting-rgv
    docker-compose up --build
    ```

    _(Nota: La primera ejecución puede tardar unos minutos mientras MySQL se inicializa)._

2.  **Acceder:**

    - 📊 **Dashboard:** [http://localhost:5000](http://localhost:5000)
    - 🧾 **Gastos:** [http://localhost:5000/expenses](http://localhost:5000/expenses)
    - 🏦 **Cuentas:** [http://localhost:5000/accounts](http://localhost:5000/accounts)

3.  **Cargar Datos de Prueba (Seed):**
    Para ver el dashboard con datos "vivos" (Gráficos, cuentas con saldo, historial):
    ```bash
    docker-compose exec web python seed.py
    ```

## 📖 Documentación Técnica

Para detalles profundos sobre la arquitectura, diagramas de flujo, esquema de base de datos y decisiones de diseño, consulta el archivo [DOCUMENTATION.md](./DOCUMENTATION.md).

---

Hecho por **Sergio Cortez** para la prueba técnica de **RGV Soluciones Estratégicas**.
