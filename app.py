from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Animal, Servico, Historico
from datetime import datetime 
from flask import flash
from dotenv import load_dotenv
from flask import jsonify
import os

load_dotenv() 

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinica.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ------ Funções Auxiliares ------

def formatar_telefone(telefone):
    """Remove caracteres não numéricos e formata como (00) 00000-0000"""
    numeros = ''.join(filter(str.isdigit, telefone))
    if len(numeros) == 11:
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    elif len(numeros) == 10:
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
    return None

def validar_telefone(telefone):
    """Verifica se tem 10 ou 11 dígitos (com ou sem formatação)"""
    numeros = ''.join(filter(str.isdigit, telefone))
    return len(numeros) in (10, 11)

# ----- Rotas Principais -----
@app.route('/')
def index():
    busca = request.args.get('q', '').strip()
    filtro_especie = request.args.get('especie', '')

    query = Animal.query
    
    if busca:
        query = query.filter(
            (Animal.nome.ilike(f'%{busca}%')) | 
            (Animal.proprietario_nome.ilike(f'%{busca}%'))
        )
    
    if filtro_especie:
        query = query.filter_by(especie=filtro_especie)
        
    animais = query.order_by(Animal.nome).all()
    especies = db.session.query(Animal.especie).distinct().all()
    
    return render_template('index.html', 
                         animais=animais,
                         especies=[e[0] for e in especies],
                         busca=busca,
                         filtro_especie=filtro_especie)


@app.route('/animal/novo', methods=['GET', 'POST'])
def novo_animal():
    if request.method == 'POST':
        try:
            # Validação do Peso
            peso = float(request.form['peso'])
            if peso <= 0:
                flash("❌ Peso deve ser maior que zero!", "danger")
                return redirect(url_for('novo_animal'))
            
            # Validação do Telefone
            telefone = request.form['proprietario_telefone'].strip()
            if not validar_telefone(telefone):
                flash("❌ Telefone inválido! Use o formato (99) 99999-9999", "danger")
                return redirect(url_for('novo_animal'))
            
            # Cria o animal se tudo estiver válido
            novo_animal = Animal(
                nome=request.form['nome'].strip(),
                especie=request.form['especie'].strip(),
                raca=request.form.get('raca', '').strip(),
                peso=peso,
                proprietario_nome=request.form['proprietario_nome'].strip(),
                proprietario_telefone=telefone
            )
            db.session.add(novo_animal)
            db.session.commit()
            flash("✅ Animal cadastrado com sucesso!", "success")
            return redirect(url_for('index'))
            
        except ValueError:
            flash("❌ Peso inválido! Use números (ex: 5.7)", "danger")
    return render_template('novo_animal.html')


@app.route('/animal/<int:id>')
def ver_animal(id):
    animal = Animal.query.get_or_404(id)
    servicos = Servico.query.order_by(Servico.tipo).all()
    historicos = Historico.query.filter_by(animal_id=id).order_by(Historico.data.desc()).all()
    return render_template('historico.html', animal=animal, servicos=servicos, historicos=historicos)

@app.route('/animal/excluir/<int:id>', methods=['POST'])
def excluir_animal(id):
    animal = Animal.query.get_or_404(id)
    
    # Primeiro exclui todos os históricos associados
    Historico.query.filter_by(animal_id=id).delete()
    
    db.session.delete(animal)
    db.session.commit()
    flash('Animal excluído com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/servico/excluir/<int:id>', methods=['POST'])
def excluir_servico(id):
    servico = Historico.query.get_or_404(id)
    animal_id = servico.animal_id
    db.session.delete(servico)
    db.session.commit()
    flash('Serviço excluído do histórico!', 'success')
    return redirect(url_for('ver_animal', id=animal_id))

# ----- Rota para Serviços -----
@app.route('/servico/novo/<int:animal_id>', methods=['POST'])
def novo_servico(animal_id):
    historico = Historico(
        animal_id=animal_id,
        servico_id=request.form['servico_id'],
        observacoes=request.form.get('observacoes', ''),
        data=datetime.now() 
    )
    db.session.add(historico)
    db.session.commit()
    return redirect(url_for('ver_animal', id=animal_id))

@app.route('/clear-flashes', methods=['POST'])
def clear_flashes():
    if '_flashes' in session:
        session.pop('_flashes', None)
    return jsonify({'status': 'success'}), 200

@app.route('/animal/editar/<int:id>', methods=['GET', 'POST'])
def editar_animal(id):
    animal = Animal.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            session.pop('_flashes', None) if '_flashes' in session else None
            # Validação do Peso
            peso = float(request.form['peso'])
            if peso <= 0:
                flash("❌ Peso deve ser maior que zero!", "danger")
                return redirect(url_for('editar_animal', id=id))
            session.pop('_flashes', None) if '_flashes' in session else None
            # Validação do Telefone
            telefone = request.form['proprietario_telefone'].strip()
            if not validar_telefone(telefone):
                if '_flashes' in session: 
                    session.pop('_flashes', None)
                flash("❌ Telefone deve conter 10 ou 11 dígitos", "danger")
                return render_template('editar_animal.html',
                                    animal=animal,
                                    form_data=request.form)
            
            # Atualização dos dados
            animal.nome = request.form['nome'].strip()
            animal.especie = request.form['especie'].strip()
            animal.raca = request.form.get('raca', '').strip()
            animal.peso = peso
            animal.proprietario_nome = request.form['proprietario_nome'].strip()
            animal.proprietario_telefone = formatar_telefone(telefone)
            
            db.session.commit()
            flash("✅ Animal atualizado com sucesso!", "success")
            return redirect(url_for('ver_animal', id=id))
            
        except ValueError:
            session.pop('_flashes', None)
            flash("❌ Valor inválido! Verifique os dados.", "danger")
            return render_template('editar_animal.html',
                                animal=animal,
                                form_data=request.form)
    return render_template('editar_animal.html', animal=animal)

# ----- Inicialização Automática -----
def criar_servicos_iniciais():
    if Servico.query.count() == 0:
        db.session.add_all([
            Servico(tipo="Consulta", preco=150.00),
            Servico(tipo="Vacina", preco=90.50),
            Servico(tipo="Cirurgia", preco=800.00)
        ])
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_servicos_iniciais()  # Cria os serviços automaticamente
    app.run(debug=True)