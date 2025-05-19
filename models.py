from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50), nullable=False)
    raca = db.Column(db.String(50))
    peso = db.Column(db.Float, nullable=False)
    proprietario_nome = db.Column(db.String(100), nullable=False)
    proprietario_telefone = db.Column(db.String(20), nullable=False)

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)

class Historico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'))
    data = db.Column(db.DateTime, default=db.func.now())
    observacoes = db.Column(db.Text)
    
    animal = db.relationship('Animal', backref='historicos')
    servico = db.relationship('Servico')