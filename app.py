from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'inventario'

def get_db_connection():
    """Crea y retorna una conexión a la base de datos."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",          
            password="",        
            database="inventario_pyme" 
        )
        return conn
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def registrar_modificacion(cursor, modificacion, descripcion, autor, id_producto):
    """Registra una acción en la tabla de registros."""
    sql = """
    INSERT INTO registros (modificacion, descripcion, autor, id_producto)
    VALUES (%s, %s, %s, %s)
    """
    datos = (modificacion, descripcion, autor, id_producto)
    cursor.execute(sql, datos)


@app.route('/')
def index():
    """Página principal que muestra todos los productos."""
    conn = get_db_connection()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos ORDER BY nombre ASC")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('index.html', productos=productos)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar_producto_route():
    """Ruta para mostrar el formulario y para agregar un nuevo producto."""
    if request.method == 'POST':
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        precio_compra = request.form['precio_compra']
        precio_venta = request.form['precio_venta']
        proveedor = request.form['proveedor']
        #Excepciones
        if not all([nombre, cantidad, precio_compra, precio_venta]):
            flash("Error: Todos los campos son obligatorios.", "error")
            return redirect(url_for('agregar_producto_route'))

        conn = get_db_connection()
        if not conn:
            flash("Error de conexión a la base de datos.", "error")
            return redirect(url_for('agregar_producto_route'))

        cursor = conn.cursor()
        
        # Insertar
        sql_prod = "INSERT INTO productos (nombre, cantidad, precio_compra, precio_venta, proveedor) VALUES (%s, %s, %s, %s, %s)"
        datos_prod = (nombre, cantidad, precio_compra, precio_venta, proveedor)
        cursor.execute(sql_prod, datos_prod)
        id_nuevo = cursor.lastrowid
        
        # Registrar
        registrar_modificacion(cursor, "Ingreso", f"Se agregó el producto: {nombre}", "Admin", id_nuevo)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Producto agregado con éxito.", "success")
        return redirect(url_for('index'))

    return render_template('agregar.html')

@app.route('/modificar/<int:id>', methods=['GET', 'POST'])
def modificar_producto_route(id):
    """Ruta para editar un producto existente."""
    conn = get_db_connection()
    if not conn:
        return "Error de conexión."

    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        precio_compra = request.form['precio_compra']
        precio_venta = request.form['precio_venta']
        proveedor = request.form['proveedor']

        sql_update = """
        UPDATE productos SET
            nombre = %s, cantidad = %s, precio_compra = %s, precio_venta = %s, proveedor = %s
        WHERE id_producto = %s
        """
        datos_update = (nombre, cantidad, precio_compra, precio_venta, proveedor, id)
        cursor.execute(sql_update, datos_update)
        
        registrar_modificacion(conn.cursor(), "Modificación", f"Se actualizó el producto: {nombre}", "Admin", id)

        conn.commit()
        cursor.close()
        conn.close()

        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for('index'))
    
    # Formulario modificacion
    cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id,))
    producto = cursor.fetchone()
    cursor.close()
    conn.close()

    if not producto:
        return "Producto no encontrado", 404
        
    return render_template('modificar.html', producto=producto)


@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_producto_route(id):
    """Ruta para eliminar un producto."""
    conn = get_db_connection()
    if not conn:
        flash("Error de conexión.", "error")
        return redirect(url_for('index'))
    
    cursor = conn.cursor(dictionary=True)

    # Obtener nombre para el registro antes de borrar
    cursor.execute("SELECT nombre FROM productos WHERE id_producto = %s", (id,))
    producto = cursor.fetchone()
    
    if producto:
        # Registrar eliminación
        reg_cursor = conn.cursor()
        registrar_modificacion(reg_cursor, "Eliminación", f"Se eliminó el producto: {producto['nombre']}", "Admin", id)
        reg_cursor.close()

        # Eliminar el producto
        cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
        conn.commit()
        flash(f"Producto '{producto['nombre']}' eliminado.", "success")
    else:
        flash("El producto no existe.", "error")

    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)