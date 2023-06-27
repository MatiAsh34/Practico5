from flask import Flask,render_template, request,redirect,url_for,session
import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import hmac

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db
from models import Preceptor,Padre,Estudiante,Curso,Asistencia

@app.route('/',methods=['POST','GET'])
def inicio():
    
    
    
    if request.method== 'POST':
        rol=request.form.get('rol')
        
        if rol=='preceptor':
            preceptor_actual= Preceptor.query.filter_by(correo=request.form['correo']).first()
            if preceptor_actual is None:
                return render_template('error.html', error="El correo no está registrado")
            
            else:
                clave = request.form['password'].encode('utf-8')
                hashed_password = hashlib.md5(clave).hexdigest()
                verificacion = hmac.compare_digest(hashed_password, preceptor_actual.clave)
                if (verificacion):                    
                    session['idpreceptor']=preceptor_actual.id
                    return render_template('menu_preceptor.html', Preceptor = preceptor_actual)
                else:
                    return render_template('error.html', error="La contraseña no es válida")
                
        elif rol=='padre':
            padre_actual= Padre.query.filter_by(correo= request.form['correo']).first()
            if padre_actual is None:
                return render_template('error.html', error="El correo no está registrado")
            
            else:
                clave = request.form['password'].encode('utf-8')
                hashed_password = hashlib.md5(clave).hexdigest()
                verificacion = hmac.compare_digest(hashed_password, padre_actual.clave)
                if (verificacion):                    
                    return render_template('index.html', Padre = padre_actual)
                else:
                    return render_template('error.html', error="La contraseña no es válida")
                
    else:
        return render_template('index.html')
    
@app.route('/Registrar_Asistencia',methods=['POST','GET'])
def Registrar_Asistencia():
    if request.method== 'POST':
        if not request.form['curso']:
            cursos = Curso.query.filter_by(idpreceptor=session['idpreceptor']).all()
            return render_template('Registrar_Asistencia.html', cursos = cursos)
        else:
            fecha = request.form['fecha']
            codigo_clase = request.form['clase']
            curso_seleccionado = request.form['curso']
            return redirect(url_for('guardar_asistencia',fecha = fecha,codigo_clase = codigo_clase,curso_seleccionado = curso_seleccionado))            
    else:
        cursos = Curso.query.filter_by(idpreceptor=session['idpreceptor']).all()
        return render_template('Registrar_Asistencia.html', cursos = cursos)


@app.route('/Registrar_Asistencia/<fecha>/<codigo_clase>/<curso_seleccionado>',methods=['GET','POST'])
def guardar_asistencia(fecha,codigo_clase,curso_seleccionado):
    alumnos = Estudiante.query.filter_by(idcurso=curso_seleccionado).order_by(Estudiante.apellido.asc()).all()
    if request.method == 'POST':
        numeros_estudiantes = [estudiante.id for estudiante in alumnos]
        asistio = request.form.getlist('asistio[]')
        justificacion = request.form.getlist('justificacion[]')

        for i in range(len(numeros_estudiantes)):
            asistencia_estudiante = Asistencia()
            asistencia_estudiante.fecha=fecha
            asistencia_estudiante.codigoclase=codigo_clase
            asistencia_estudiante.asistio=asistio[i]
            asistencia_estudiante.justificacion=justificacion[i]
            asistencia_estudiante.idestudiante=numeros_estudiantes[i]
            db.session.add(asistencia_estudiante)
            db.session.commit()
        return render_template('menu_preceptor.html')
    else:
        return render_template('colocar_asistencia.html', alumnos=alumnos)

@app.route('/Informe',methods=['POST','GET'])
def Genera_Informe():
    if request.method== 'POST':
        curso_id = request.form.get('curso')
        alumnos = Estudiante.query.filter_by(idcurso=curso_id).order_by(Estudiante.apellido.asc()).all()

        informe = []

        for alumno in alumnos:
            asistencias = Asistencia.query.filter_by(idestudiante=alumno.id).all()

            clases_aula_presente = 0
            clases_aula_ausente_justificadas = 0
            clases_aula_ausente_injustificadas = 0
            clases_educacion_fisica_presente = 0
            clases_educacion_fisica_ausente_justificadas = 0
            clases_educacion_fisica_ausente_injustificadas = 0

            for asistencia in asistencias:
                if asistencia.codigoclase == 1: # AULA
                    if asistencia.asistio == 's': # asistio
                        clases_aula_presente += 1
                    elif asistencia.asistio == 'n':
                        if asistencia.justificacion == '':
                            clases_aula_ausente_injustificadas += 1
                        else:
                            clases_aula_ausente_justificadas += 1
                        
                elif asistencia.codigoclase == 2: # EDUCACION FISICA
                    if asistencia.asistio == 's':
                        clases_educacion_fisica_presente += 1
                    elif asistencia.asistio == 'n':
                        if asistencia.justificacion == '':
                            clases_educacion_fisica_ausente_injustificadas += 1
                        else:
                            clases_educacion_fisica_ausente_justificadas += 1
                        
            total_inasistencias = (clases_aula_ausente_injustificadas + (clases_educacion_fisica_ausente_injustificadas/2))
            
            informe_alumno = {
                'alumno': alumno,
                'clases_aula_presente': clases_aula_presente,
                'clases_aula_ausente_justificadas': clases_aula_ausente_justificadas,
                'clases_aula_ausente_injustificadas': clases_aula_ausente_injustificadas,
                'clases_educacion_fisica_presente': clases_educacion_fisica_presente,
                'clases_educacion_fisica_ausente_justificadas': clases_educacion_fisica_ausente_justificadas,
                'clases_educacion_fisica_ausente_injustificadas': clases_educacion_fisica_ausente_injustificadas,
                'total_inasistencias': total_inasistencias
            }

            informe.append(informe_alumno)
        
        return render_template('Informe_Detallado.html', informe=informe)
 
    cursos = Curso.query.filter_by(idpreceptor=session['idpreceptor']).all()
    return render_template('Selecciona_Curso.html', cursos = cursos)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug = True)
