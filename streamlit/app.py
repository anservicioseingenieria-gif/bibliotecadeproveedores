# ============================================================
# APP PROFESIONAL - BIBLIOTECA DE PRECIOS Y COTIZADOR
# STREAMLIT + SQLITE
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

# ============================================================
# AUTENTICACIÓN
# ============================================================

def verificar_contraseña(contraseña):
    """Verifica la contraseña (hasheada)"""
    contraseña_hasheada = hashlib.sha256(contraseña.encode()).hexdigest()
    # Contraseña: BBC
    contraseña_correcta = hashlib.sha256("BBC".encode()).hexdigest()
    return contraseña_hasheada == contraseña_correcta

def login():
    """Interfaz de login"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔐 Biblioteca de Precios")
        st.write("Ingresa tu contraseña para acceder")
        
        contraseña = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar"):
            if verificar_contraseña(contraseña):
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

# Verificar autenticación
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    login()
    st.stop()

# ============================================================
# CONFIGURACIÓN PÁGINA
# ============================================================

st.set_page_config(
    page_title="Biblioteca de Precios",
    page_icon="💼",
    layout="wide"
)

# ============================================================
# ESTILOS CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #F4F4F4;
}

h1, h2, h3 {
    color: #0B1F3A;
}

.stButton>button {
    background-color: #0B1F3A;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.5rem 1rem;
}

.stButton>button:hover {
    background-color: #163A6B;
    color: white;
}

div[data-testid="stMetric"] {
    background-color: white;
    border-radius: 12px;
    padding: 15px;
    border-left: 5px solid #0B1F3A;
}

table {
    background-color: white;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# CONEXIÓN SQLITE
# ============================================================

conn = sqlite3.connect("biblioteca_precios.db", check_same_thread=False)
cursor = conn.cursor()

# ============================================================
# CREAR TABLAS
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    referencia TEXT,
    proveedor TEXT,
    precio_compra REAL,
    margen REAL,
    precio_venta REAL,
    iva TEXT,
    fecha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cotizaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    cantidad INTEGER,
    precio_unitario REAL,
    iva TEXT,
    total REAL,
    fecha TEXT
)
""")

conn.commit()

# ============================================================
# SIDEBAR CON BOTÓN CERRAR SESIÓN
# ============================================================

st.sidebar.title("📦 MENÚ")

# Botón de cerrar sesión en el sidebar
if st.sidebar.button("🚪 Cerrar sesión"):
    st.session_state.autenticado = False
    st.rerun()

menu = st.sidebar.radio(
    "Selecciona una opción",
    [
        "Dashboard",
        "Proveedores",
        "Productos",
        "Cotizador"
    ]
)

# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    st.title("💼 Biblioteca de Precios")

    total_productos = pd.read_sql("SELECT * FROM productos", conn)
    total_proveedores = pd.read_sql("SELECT * FROM proveedores", conn)

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Productos",
            len(total_productos)
        )

    with col2:
        st.metric(
            "Total Proveedores",
            len(total_proveedores)
        )

    st.divider()

    st.subheader("📋 Productos Registrados")

    if not total_productos.empty:
        st.dataframe(total_productos, use_container_width=True)
    else:
        st.info("No hay productos registrados.")

# ============================================================
# PROVEEDORES
# ============================================================

elif menu == "Proveedores":

    st.title("🏢 Gestión de Proveedores")

    with st.form("form_proveedor"):

        nombre = st.text_input("Nombre proveedor")

        guardar = st.form_submit_button("Guardar proveedor")

        if guardar:

            cursor.execute("""
            INSERT INTO proveedores(nombre)
            VALUES(?)
            """, (nombre,))

            conn.commit()

            st.success("Proveedor guardado correctamente")

    st.divider()

    proveedores = pd.read_sql(
        "SELECT * FROM proveedores",
        conn
    )

    st.dataframe(proveedores, use_container_width=True)

# ============================================================
# PRODUCTOS
# ============================================================

elif menu == "Productos":

    st.title("📦 Biblioteca de Productos")

    proveedores_df = pd.read_sql(
        "SELECT * FROM proveedores",
        conn
    )

    lista_proveedores = proveedores_df["nombre"].tolist()

    with st.form("form_producto"):

        col1, col2 = st.columns(2)

        with col1:

            producto = st.text_input("Producto")

            referencia = st.text_input("Referencia")

            proveedor = st.selectbox(
                "Proveedor",
                lista_proveedores
            )

            precio_compra = st.number_input(
                "Precio proveedor",
                min_value=0.0,
                step=1000.0
            )

        with col2:

            margen = st.slider(
                "Margen ganancia %",
                0,
                200,
                35
            )

            iva = st.selectbox(
                "IVA",
                ["Sí", "No"]
            )

            precio_venta = precio_compra * (1 + margen / 100)

            st.metric(
                "Precio Venta",
                f"${precio_venta:,.0f}"
            )

        guardar_producto = st.form_submit_button(
            "Guardar producto"
        )

        if guardar_producto:

            fecha = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
            INSERT INTO productos(
                producto,
                referencia,
                proveedor,
                precio_compra,
                margen,
                precio_venta,
                iva,
                fecha
            )
            VALUES(?,?,?,?,?,?,?,?)
            """, (
                producto,
                referencia,
                proveedor,
                precio_compra,
                margen,
                precio_venta,
                iva,
                fecha
            ))

            conn.commit()

            st.success("Producto guardado correctamente")

    st.divider()

    productos_df = pd.read_sql(
        "SELECT * FROM productos",
        conn
    )

    st.dataframe(productos_df, use_container_width=True)

# ============================================================
# COTIZADOR
# ============================================================

elif menu == "Cotizador":

    st.title("🧾 Cotizador")

    productos_df = pd.read_sql(
        "SELECT * FROM productos",
        conn
    )

    if productos_df.empty:

        st.warning("No hay productos registrados.")

    else:

        producto = st.selectbox(
            "Selecciona producto",
            productos_df["producto"]
        )

        producto_info = productos_df[
            productos_df["producto"] == producto
        ].iloc[0]

        cantidad = st.number_input(
            "Cantidad",
            min_value=1,
            value=1
        )

        precio = producto_info["precio_venta"]

        subtotal = cantidad * precio

        aplica_iva = st.selectbox(
            "Aplicar IVA",
            ["Sí", "No"]
        )

        if aplica_iva == "Sí":
            iva_total = subtotal * 0.19
        else:
            iva_total = 0

        total = subtotal + iva_total

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Subtotal",
                f"${subtotal:,.0f}"
            )

        with col2:
            st.metric(
                "IVA",
                f"${iva_total:,.0f}"
            )

        with col3:
            st.metric(
                "TOTAL",
                f"${total:,.0f}"
            )

        guardar_cotizacion = st.button(
            "Guardar cotización"
        )

        if guardar_cotizacion:

            fecha = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
            INSERT INTO cotizaciones(
                producto,
                cantidad,
                precio_unitario,
                iva,
                total,
                fecha
            )
            VALUES(?,?,?,?,?,?)
            """, (
                producto,
                cantidad,
                precio,
                aplica_iva,
                total,
                fecha
            ))

            conn.commit()

            st.success("Cotización guardada")

        st.divider()

        historial = pd.read_sql(
            "SELECT * FROM cotizaciones",
            conn
        )

        st.subheader("📑 Historial Cotizaciones")

        st.dataframe(historial, use_container_width=True)
