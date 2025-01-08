from flask import render_template, request, redirect, flash, session, url_for
from app import app
from app.funciones import actualizar_dolares, actualizar_saldo, crear_usuario_temporal, obtener_detalle_prestamo, obtener_dolares, obtener_prestamos_usuario, obtener_saldo, obtener_transferencias_usuario, pagar_cuota_prestamo, realizar_transferencia, registrar_prestamo, simular_prestamo
import csv
import requests

@app.route('/')
def auth():
    if 'usuario_id' in session:
        return redirect(url_for('home'))
    
    usuario_id = crear_usuario_temporal()
    if usuario_id:
        session['usuario_id'] = usuario_id
        return redirect(url_for('home'))
    else:
        flash('Hubo un problema al crear el usuario temporal.', 'error')


@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'usuario_id' not in session:
        return redirect(url_for('auth'))
    
    usuario = session['usuario_id']
    saldo = obtener_saldo(usuario)
    dolares = obtener_dolares(usuario)

    if saldo is None:
        flash('Error al obtener el saldo del usuario.')
        return redirect(url_for('home'))

    try:
        # Consulta para obtener transferencias enviadas y recibidas
        data = obtener_transferencias_usuario(usuario)
    except Exception:
        flash('Error al cargar historial de transferencias del usuario.', 'error')
        data = []

    return render_template('home.html', data=data, saldo=saldo, dolares=dolares)


@app.route('/transferencia', methods=['GET','POST'])
def transferencia():
    if request.method == 'POST':

        #Conseguir los datos del formulario.
        try:
            transferencia = int(request.form['montotransferencia'])
            id_beneficiario = request.form['ID']
        except Exception:
            flash('Error al procesar datos de la transferencia', 'error')
            return redirect(url_for('transferencia'))
        
        usuario = session.get('usuario_id')
        
        #Se realiza la transferencia.
        try:
            saldo = obtener_saldo(usuario)
            if saldo is not None and saldo >= transferencia:
                realizar_transferencia(id_beneficiario, usuario, transferencia, saldo)
                flash('Transferencia Realizada con exito.', 'success')
                return redirect(url_for('transferencia'))
            else:
                flash('No hay suficiente saldo para realizar la transferencia.', 'error')    
                return redirect(url_for('transferencia'))
        except Exception:
            flash('Error al realizar la transferencia.', 'error') 
            return redirect(url_for('transferencia'))
                   
    elif request.method == 'GET':
        return render_template('transferencia.html')


@app.route('/interescompuesto', methods=['GET','POST'])
def interescompuesto():
    if request.method == 'POST':

        try:    
            capital = int(request.form['capital'])
            tasainteres = float(request.form['tasainteres'])
            tiempo = int(request.form['tiempo'])
            aportemensual = int(request.form['aportemensual'])
        except Exception:
            flash('Error al conseguir los datos del formulario.', 'error')
            return redirect(url_for('interescompuesto'))

        try:
            tasamensual = tasainteres / 100 / 12
            tiempo_meses = tiempo * 12

            capitalfinal = round(capital * (1 + tasamensual) ** tiempo_meses + aportemensual 
                                * (((1 + tasamensual) ** tiempo_meses - 1) / tasamensual), 2)
            
            return render_template('interescompuesto.html',capitalfinal=capitalfinal,tiempo=tiempo)
        
        except ValueError as e:
            flash(f'Error al realizar los calculos, Porfavor intente nuevamente.{e}')
            return redirect(url_for('interescompuesto'))
        
    elif request.method == 'GET':
        return render_template('interescompuesto.html', capitalfinal=None)


@app.route('/prestamo', methods=['GET','POST'])
def prestamo():
    if request.method == 'POST':
        try:
            montoprestamo = int(request.form['montoprestamo'])
            interesanual = int(request.form['tasaprestamo'])
            plazomeses = int(request.form['plazoprestamo'])

            # Cálculo del préstamo
            totalinteres, totalpagar, cuotamensual = simular_prestamo(interesanual, montoprestamo, plazomeses) 
            
            return render_template(
                'prestamo.html',
                cuotamensual=cuotamensual,
                totalinteres=totalinteres,
                totalpagar=totalpagar,
                plazomeses=plazomeses,
                montoprestamo=montoprestamo,
                tasaprestamo=interesanual,
                plazoprestamo=plazomeses
            )
        except ValueError:
            flash('Error al simular prestamo.', 'error')
            return render_template('prestamo.html', totalpagar=None)
        
    elif request.method == 'GET':
        return render_template('prestamo.html', totalpagar=None)
    

@app.route('/solicitar_prestamo', methods=['POST'])
def solicitar_prestamo():
    montoprestamo = int(request.form['monto'])
    tasaprestamo = int(request.form['tasa'])
    plazoprestamo = int(request.form['plazo'])
    cuotamensual = float(request.form['cuotamensual'])
    total = float(request.form['total'])

    usuario = session.get('usuario_id')
    
    try:
        registrar_prestamo(usuario, montoprestamo, plazoprestamo, cuotamensual, tasaprestamo, total)
        flash('Prestamo solicitado correctamente.', 'success')
        return redirect(url_for('home'))
    except ValueError:
        flash('Ocurrió un error al solicitar el préstamo.', 'error')
        return redirect(url_for('prestamo'))
    
    
@app.route('/misprestamos')
def misprestamos():
    try:
        usuario = session.get('usuario_id')
        dataprestamos = obtener_prestamos_usuario(usuario)
        if dataprestamos:
            return render_template('misprestamos.html',dataprestamos=dataprestamos)
        else:
            return render_template('misprestamos.html', dataprestamos=None)
    except ValueError:
        flash('Hubo un error al cargar sus prestamos.', 'error')


@app.route('/misprestamos/prestamo_detalle')
def prestamo_detalle():
    prestamo_id = request.args.get('prestamo_id')
    usuario_id = session.get('usuario_id')

    prestamo = obtener_detalle_prestamo(prestamo_id)
    saldo_usuario = obtener_saldo(usuario_id)

    return render_template('prestamo_detalle.html', prestamo=prestamo, usuario_saldo=saldo_usuario)


@app.route('/misprestamos/pagar_cuota', methods=['POST'])
def pagar_cuota():
    try:
        prestamo_id = request.form.get('prestamo_id')
        usuario_id = session.get('usuario_id')

        pagar_cuota_prestamo(prestamo_id, usuario_id)

        flash("Cuota pagada exitosamente", "success")
        return redirect(url_for('prestamo_detalle', prestamo_id=prestamo_id))
    except ValueError as e:
        flash(f"Error: {e}", "error")
        return redirect(url_for('prestamo_detalle', prestamo_id=prestamo_id))
    

@app.route('/comprardolares')
def comprar_dolares():
    try:
        # Llamada a una API para obtener el precio del dólar
        url = 'https://api.exchangerate-api.com/v4/latest/USD'
        response = requests.get(url)
        data = response.json()

        # Toma el valor del dólar frente al peso argentino (ARS)
        dollar_price = data['rates']['ARS']
        return render_template('comprar_dolares.html', dollar_price=dollar_price)
    except Exception:
        flash('No se pudo obtener el precio del dólar. Inténtelo más tarde.', 'error')
        return render_template('comprar_dolares.html', dollar_price='Error')


@app.route('/comprar_dolares', methods=['GET', 'POST'])
def compra_dolares():
    # Llamada a la API para obtener el precio del dólar
    url = 'https://api.exchangerate-api.com/v4/latest/USD'
    response = requests.get(url)
    data = response.json()
    dollar_price = data['rates']['ARS']

    usuario = session.get('usuario_id')  # Obtenemos el usuario desde la sesión
    if not usuario:
        flash('Usuario no identificado. Por favor, inicia sesión.', 'error')
        return redirect('/login')

    if request.method == 'POST':
        try:
            cantidad_dolares = float(request.form['cantidad_dolares'])
            if cantidad_dolares <= 0:
                flash('La cantidad de dólares debe ser válida.', 'error')
                return render_template('comprar_dolares.html', dollar_price=dollar_price)

            costo_total = cantidad_dolares * dollar_price
            saldo = obtener_saldo(usuario)
            dolares = obtener_dolares(usuario)
            # Verificar si el usuario tiene saldo suficiente
            if saldo is None or saldo < costo_total:
                flash('No tienes saldo suficiente para realizar esta compra.', 'error')
            else:
                # Realizar la compra
                actualizar_saldo(usuario, saldo - costo_total)
                actualizar_dolares(usuario, cantidad_dolares + dolares)
                flash(f'Compra realizada con éxito. Compraste {cantidad_dolares} USD por ${costo_total:.2f} ARS.', 'success')
        except ValueError:
            flash('Error al procesar la compra. Inténtelo más tarde.', 'error')

    return render_template('comprar_dolares.html', dollar_price=dollar_price)


@app.route('/vender_dolares', methods=['GET','POST'])
def vender_dolares():
    # Llamada a la API para obtener el precio del dólar
    url = 'https://api.exchangerate-api.com/v4/latest/USD'
    response = requests.get(url)
    data = response.json()
    dollar_price = data['rates']['ARS']
    usuario = session.get('usuario_id')
    saldo = obtener_saldo(usuario)
    dolares = obtener_dolares(usuario)

    if request.method == 'POST':
        try:
            cantidad_dolares = float(request.form['cantidad_dolares'])
            if cantidad_dolares <= 0:
                flash('La cantidad de dólares debe ser válida.', 'error')
                return render_template('vender_dolares.html', dollar_price=dollar_price)

            costo_total = cantidad_dolares * dollar_price
            
            # Verificar si el usuario tiene saldo suficiente
            if dolares is None or dolares < cantidad_dolares:
                flash('No tienes dólares suficiente para realizar esta venta.', 'error')
            else:
                # Realizar la compra
                actualizar_saldo(usuario, saldo + costo_total)
                actualizar_dolares(usuario,  dolares - cantidad_dolares)
                flash(f'Venta realizada con éxito. Vendiste {cantidad_dolares} USD por ${costo_total:.2f} ARS.', 'success')
        except ValueError:
            flash('Error al procesar la venta. Inténtelo más tarde.', 'error')
    return render_template('vender_dolares.html', dollar_price=dollar_price, saldo=saldo, dolares=dolares)