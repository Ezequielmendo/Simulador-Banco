from flask import session
import uuid
from sqlalchemy import text
from app import db


def crear_usuario_temporal():
    """
    Crea un ID al usuario y lo registra en la sesion.

    El usuario se genera con un saldo inicial predeterminado y se almacena en la tabla 'user'.

    Returns:
        str: El ID único generado para el usuario, si se creó correctamente.
        None: Si ocurre algún error durante el proceso de creación.
    """
    try:
        #Genera un usuario temporal con un ID único y lo guarda en la tabla user.
        usuario_id = str(uuid.uuid4())  #Genera el id del usuario.
        saldo = 1000000
        dolares = 0
        guardar_usuario = text('INSERT INTO user (user,saldo,dolares) VALUES (:usuario_id,:saldo,:dolares)') #Guarda el usuario en la tabla user.
        db.session.execute(guardar_usuario, {'usuario_id':usuario_id, 'saldo':saldo, 'dolares':dolares})
        db.session.commit()
        session['usuario_id'] = usuario_id
        return usuario_id
    except Exception:
        return None


def obtener_saldo(usuario):
    """
    Obtiene el saldo del usuario.

    Args:
        usuario(str): ID del usuario.
    Returns:
        int: El saldo del usuario.
        None: Si no existe saldo.
    """
    consulta = text('SELECT saldo FROM user WHERE user=:usuario')
    saldo_result = db.session.execute(consulta, {'usuario':usuario}).fetchone()
    saldo = saldo_result[0]
    return saldo if saldo else None
      

def obtener_dolares(usuario):
    """
    Obtiene los dólares del usuario.

    Args:
        usuario(str): ID del usuario.
    Returns:
        int: Los dólares del usuario.
        None: Si no existe dólares.
    """
    consulta = text('SELECT dolares FROM user WHERE user=:usuario')
    resultado = db.session.execute(consulta, {'usuario':usuario}).fetchone()
    return float(resultado[0])


def actualizar_saldo(usuario, saldo):
    """
    Actualiza el saldo del usuario.

    Args:
        usuario(str): ID del usuario.
        saldo(int): El nuevo saldo del usuario.
    Returns:
        Esta función no retorna valor.
    """
    consulta = text('UPDATE user SET saldo=:saldo WHERE user=:usuario')
    db.session.execute(consulta, {'saldo':saldo,'usuario':usuario})
    db.session.commit()


def actualizar_dolares(usuario, cantidad_dolares):
    """
    Actualiza los dólares del usuario, sumando a la cantidad actual.

    Args:
        usuario (str): ID del usuario.
        cantidad_dolares (float): Cantidad de dólares a agregar.
    Returns:
        None
    """
    consulta = text('UPDATE user SET dolares=:cantidad_dolares WHERE user=:usuario')
    db.session.execute(consulta, {'cantidad_dolares': cantidad_dolares, 'usuario': usuario})
    db.session.commit()


def obtener_transferencias_usuario(usuario):
    """
    Obtiene las transferencias enviadas y recibidas del usuario.

    Args:
        usuario(str): ID del usuario.
    Returns:
        str: El resultado de la consulta, que contiene las transferencias.
    """
    consulta = text('''
                SELECT u.user AS remitente, u_b.user AS beneficiario, t.transaccion
                FROM transferencias t 
                INNER JOIN user u ON t.id_usuario_remitente = u.id 
                INNER JOIN user u_b ON t.id_usuario_beneficiario = u_b.id 
                WHERE u.user = :usuario
                UNION ALL
                SELECT u_b.user AS remitente, u.user AS beneficiario, t.transaccion
                FROM transferencias t 
                INNER JOIN user u ON t.id_usuario_beneficiario = u.id 
                INNER JOIN user u_b ON t.id_usuario_remitente = u_b.id 
                WHERE u.user = :usuario
            ''')
    consulta_result = db.session.execute(consulta, {'usuario':usuario}).fetchall()

    return consulta_result


def realizar_transferencia(id_beneficiario, usuario, transferencia, saldo):
    """
    Realiza la transferencia asegurandose que haya saldo suficiente para la transacción.

    Args:
        id_beneficiario(str): ID del usuario al que se enviara el dinero.
        usuario(str): ID del usuario que enviara el dinero.
        transferencia(int): El monto de la transacción.
        saldo(int): El balance disponible del usuario que desea enviar el dinero. 

    Returns:
        Esta función no retorna valor.
    """
    checkusuariob = text('SELECT saldo,id FROM user WHERE user=:id_beneficiario')
    datausuariob = db.session.execute(checkusuariob, {'id_beneficiario':id_beneficiario}).fetchone()
    checkusuarior = text('SELECT id FROM user WHERE user=:usuario')
    datausuarior = db.session.execute(checkusuarior, {'usuario':usuario}).fetchone()
    if datausuariob:
        nuevosaldorecibe = datausuariob[0] + transferencia
        nuevosaldoenvia = saldo - transferencia
        acutualizar_saldos_usuarios = text('UPDATE user SET saldo=:nuevo_saldo WHERE user=:usuario')
        db.session.execute(acutualizar_saldos_usuarios, {'nuevo_saldo':nuevosaldorecibe,'usuario':id_beneficiario})
        db.session.execute(acutualizar_saldos_usuarios, {'nuevo_saldo':nuevosaldoenvia,'usuario':usuario})
        db.session.commit()
        #Registrar la transferencia en tabla transferencias.
         
        registrar_transferencia = text('''INSERT INTO transferencias (id_usuario_remitente,id_usuario_beneficiario,transaccion) 
                                       VALUES (:usuario_remitente,:usuario_beneficiario,:transferencia)''')
        db.session.execute(registrar_transferencia, {'usuario_remitente':datausuarior[0], 'usuario_beneficiario':datausuariob[1], 'transferencia':transferencia})
        db.session.commit()
    

def simular_prestamo(interesanual, montoprestamo, plazomeses):
    """
    Calcula las condiciones de un préstamo.

    Args:
        interesanual(int): Interés anual que va a tener el préstamo.
        montoprestamo(int): Monto del préstamo.
        plazomeses(int): Cantidad de meses que se va a tener que pagar el préstamo con sus intereses aplicados.
    Returns:
        int: Cantidad total de dinero que se va a pagar en interés.
        int: Cantidad total que se va a pagar sumando el monto inicial con los intereses.
        int: Cantidad que se va a pagar en cada cuota mensual.
    """
    interesmensual = interesanual / 12
    totalinteres = round(((montoprestamo * interesmensual * plazomeses) / 100), 2)
    totalpagar = round((montoprestamo + totalinteres), 2)
    cuotamensual = round((totalpagar / plazomeses), 2)

    return totalinteres, totalpagar, cuotamensual


def registrar_prestamo(usuario, montoprestamo, plazoprestamo, cuotamensual, tasaprestamo, total):
    """
    Registra el préstamo solicitado en la base de datos.

    Args:
        usuario(str): ID del usuario.
        montoprestamo(int): Monto del préstamo.
        plazoprestamo(int): Cantidad de meses que se va a tener que pagar el préstamo con sus intereses aplicados.
        cuotamensual(int): Cantidad que se va a pagar en cada cuota mensual.
        tasaprestamo(int): Interés anual que va a tener el préstamo.
        total(int): Monto total del préstamo sumado los interés, que se pagara concretado el pago de la totalidad de las cuotas.
    Returns:
        Esta función no retorna valor.
    """
    saldo = obtener_saldo(usuario)
    nuevobalance = saldo + montoprestamo

    # Obtener el ID del usuario
    consulta_id_usuario = text('SELECT id FROM user WHERE user=:usuario')
    consulta_id_usuario_result = db.session.execute(consulta_id_usuario, {'usuario':usuario}).fetchone()
    if not consulta_id_usuario_result:
        raise ValueError("Usuario no encontrado")
    usuarioid = consulta_id_usuario_result[0]

    # Insertar el préstamo en la base de datos
    consulta_registrar_prestamo = text('''INSERT INTO prestamos (id_usuario, cuotas, cuota_mensual, interes_anual, monto, monto_total) 
                                       VALUES (:usuario_id, :plazo, :cuota, :tasa, :monto, :total)''')
    db.session.execute(consulta_registrar_prestamo, {'usuario_id':usuarioid, 'plazo':plazoprestamo, 'cuota':cuotamensual, 'tasa':tasaprestamo, 'monto':montoprestamo, 'total':total})

    consulta_actualizar_balance = text('UPDATE user SET saldo=:saldo WHERE user=:usuario')
    db.session.execute(consulta_actualizar_balance, {'saldo':nuevobalance, 'usuario':usuario})
    db.session.commit()


def obtener_prestamos_usuario(usuario):
    """
    Obtiene todos los préstamos vigentes solicitados del usuario.

    Args:
        usuario(str): ID del usuario.
    Returns:
        str: Los préstamos que el usuario solicito y tiene vigentes.
    """
    checkusuarioid = text('SELECT id FROM user WHERE user=:usuario')
    datausuarioid = db.session.execute(checkusuarioid, {'usuario':usuario}).fetchone()
    usuarioid = datausuarioid[0]
    checkprestamos_consulta = text('SELECT * FROM prestamos WHERE id_usuario=:usuarioid AND cuotas > 0')
    checkprestamos = db.session.execute(checkprestamos_consulta, {'usuarioid':usuarioid}).fetchall()

    return checkprestamos


def obtener_detalle_prestamo(prestamo_id):
    """
    Obtiene los detalles de un préstamo específico.

    Args:
        prestamo_id(int): ID del préstamo.
    Returns:
        str: Los detalles del préstamo.
    """
    consulta = text('SELECT * FROM prestamos WHERE id=:prestamo_id')
    consulta_result = db.session.execute(consulta, {'prestamo_id':prestamo_id}).fetchone()

    return consulta_result


def pagar_cuota_prestamo(prestamo_id, usuario_id):
    """
    Paga las cuotas de un préstamo especifico, solo si hay balance suficiente.

    Args:
        prestamo_id(int): ID del préstamo.
        usuario_id(int): ID del usuario.
    Returns:
        Esta función no retorna valor.
    """
    try:

        # Obtener el préstamo y la cuota
        consulta_prestamo = text('SELECT cuotas, cuota_mensual, monto_total FROM prestamos WHERE id=:prestamo_id')
        prestamo = db.session.execute(consulta_prestamo, {'prestamo_id': prestamo_id}).fetchone()

        if not prestamo:
            raise ValueError("Préstamo no encontrado")

        cuotas_restantes, cuota_mensual, monto_total = prestamo

        # Verificar si hay cuotas restantes
        if cuotas_restantes <= 0:
            raise ValueError("El préstamo ya está completamente pagado")

        # Verificar el saldo del usuario
        saldo_actual = obtener_saldo(usuario_id)
        if saldo_actual < cuota_mensual:
            raise ValueError("Saldo insuficiente para pagar la cuota")

        # Actualizar saldo del usuario
        nuevo_saldo = saldo_actual - cuota_mensual
        actualizar_saldo = text('UPDATE user SET saldo=:nuevo_saldo WHERE id=:usuario_id')
        db.session.execute(actualizar_saldo, {'nuevo_saldo': nuevo_saldo, 'usuario_id': usuario_id})

        # Actualizar el préstamo
        nuevas_cuotas_restantes = cuotas_restantes - 1
        nuevo_monto_total = round(monto_total - cuota_mensual, 2)
        actualizar_prestamo = text('''
            UPDATE prestamos 
            SET cuotas=:nuevas_cuotas, monto_total=:nuevo_monto 
            WHERE id=:prestamo_id
        ''')
        db.session.execute(actualizar_prestamo, {
            'nuevas_cuotas': nuevas_cuotas_restantes,
            'nuevo_monto': nuevo_monto_total,
            'prestamo_id': prestamo_id
        })

        db.session.commit()
    except Exception:
        db.session.rollback()