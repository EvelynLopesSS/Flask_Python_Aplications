from flask import Flask, render_template, request,  url_for, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
import locale
from babel.numbers import format_currency
import io
from bson.binary import Binary
import base64
import requests
import os
import uuid
from flask import send_file
import random



app = Flask(__name__)
client = MongoClient()
db = client['Imobiliaria']  # Nome do banco de dados no MongoDB
collection = db['propriedades']  # Nome da coleção no MongoDB
collection_acessos = db['acessos']  # Nome da coleção no MongoDB

app.config['UPLOAD_FOLDER'] = r'C:/Users/...'
RESULTS_PER_PAGE = 12  # Número de resultados por página


@app.route('/')
def index():


    return render_template('index.html')

@app.route('/area_corretor')
def area_corretor():
    return render_template('area_corretor.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obter dados do formulário
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        # Verificar se o email e senha estão corretos
        acesso_login = collection_acessos.find_one({'CPF_corretor': cpf, 'senha_corretor': senha})
        if acesso_login:
            # Credenciais corretas. Acesso permitido.
            return redirect(url_for('area_corretor'))
        else:
            # Credenciais incorretas. Acesso negado.
            return render_template('login.html', error_message='Credenciais incorretas.')

    return render_template('login.html')

@app.route('/cadastro_corretor', methods=['GET', 'POST'])
def cadastro():
    nome_corretor = None  # Definir um valor padrão para a variável
    endereco_corretor= None
    bairro_corretor= None
    cidade_corretor= None
    estado_corretor= None
    email_corretor= None
    senha_corretor= None
    CPF_corretor = None

    if request.method == 'POST':
        # Obter dados do formulário:
        nome_corretor = request.form.get('nome_corretor')
        endereco_corretor = request.form.get ('endereco_corretor')
        bairro_corretor = request.form.get ('bairro_corretor')
        cidade_corretor = request.form.get ('cidade_corretor')
        estado_corretor = request.form.get ('estado_corretor')
        email_corretor = request.form.get ('email_corretor')
        senha_corretor = request.form.get ('senha_corretor')
        CPF_corretor = request.form.get('CPF_corretor')


    acessos = {
            'nome_corretor': nome_corretor,
            'endereço_corretor': endereco_corretor,
            'bairro_corretor': bairro_corretor,
            'cidade_corretor':cidade_corretor,
            'estado_corretor':estado_corretor,
            'email_corretor': email_corretor,
            'senha_corretor':senha_corretor,
            'CPF_corretor': CPF_corretor
        }

    collection_acessos.insert_one(acessos)

    return render_template('cadastro_corretor.html')








@app.route('/propriedades')
def propriedades():
    page = int(request.args.get('page', 1))
    total_imoveis = collection.count_documents({})
    total_pages = (total_imoveis + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    if page < 1 or page > total_pages:
        page = 1
    start_index = (page - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE

    # Obter os valores mínimo e máximo do filtro
    valor_min = request.args.get('valor_min', '')
    valor_max = request.args.get('valor_max', '')

    # Verificar se os valores são vazios e definir como infinito ou zero, respectivamente
    valor_min = float(valor_min) if valor_min else 0
    valor_max = float(valor_max) if valor_max else float('inf')



    # Criar o filtro de valor
    filtro_valor = {'valor': {'$gte': valor_min, '$lte': valor_max}}

    # Obter o filtro de bairros
    bairro = request.args.get('bairro', '')
    # Criar o filtro de bairros
    filtro_bairro = {}
    if bairro:
        filtro_bairro = {'bairro': bairro}

    # Obter o filtro de tipo de imóvel
    tipo = request.args.get('tipo', '')
    # Criar o filtro de tipo de imóvel
    filtro_tipo = {}
    if tipo:
        filtro_tipo = {'tipo': tipo}

    # Obter a quantidade de quartos selecionada no filtro
    quartos = request.args.get('quartos', '')
    filtro_quartos = {}
    if quartos:
        filtro_quartos = {'quartos': quartos}

    # Obter o filtro de estado
    estado = request.args.get('estado', '')
    # Criar o filtro de estado
    filtro_estado = {}
    if estado:
        filtro_estado = {'estado': estado}

    # Obter o filtro de cidade
    cidade = request.args.get('cidade', '')
    # Criar o filtro de cidade
    filtro_cidade = {}
    if cidade:
        filtro_cidade = {'cidade': cidade}


    # Combinar os filtros de valor e bairros
    filtro = {**filtro_valor, **filtro_bairro, **filtro_tipo, **filtro_quartos, **filtro_cidade,**filtro_estado }

    # Buscar os bairros cadastrados
    bairros = collection.distinct('bairro')
    # Buscar os tipos de imóvel cadastrados
    tipos = collection.distinct('tipo')
    # Buscar os quartos cadastrados
    quartoss= collection.distinct('quartos')
    # Buscar os estados cadastrados
    estados = collection.distinct('estado')
    # Buscar as cidades cadastradas
    cidades = collection.distinct('cidade')

    # Aplicar o filtro na consulta ao banco de dados
    imoveis = collection.find(filtro).skip(start_index).limit(RESULTS_PER_PAGE)

    page_numbers = range(1, total_pages + 1)
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None

    ordenacao = request.args.get('ordenacao', 'valor')
    direcao = request.args.get('direcao', 'asc')

    imoveis = list(collection.find(filtro).sort(ordenacao, 1 if direcao == 'asc' else -1).limit(RESULTS_PER_PAGE).skip(start_index))
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    for imovel in imoveis:
        valor = imovel.get('valor')
        if valor is not None and valor != '':
            valor = float(valor)
            valor_formatado = locale.currency(valor, grouping=True, symbol='R$')
            imovel['valor_formatado'] = valor_formatado
        else:
            imovel['valor_formatado'] = None

    return render_template('propriedades.html', imoveis=imoveis, current_page=page, pages=page_numbers,
                           has_prev=has_prev, has_next=has_next, prev_page=prev_page, next_page=next_page,
                           valor_min=valor_min, valor_max=valor_max, bairro=bairro, bairros=bairros,tipo=tipo,
                           tipos=tipos,quartos= quartos,quartoss=quartoss,cidade=cidade,estado=estado, estados=estados,
                           cidades=cidades,ordenacao=ordenacao, direcao=direcao  )


@app.route('/propriedades/nova', methods=['GET', 'POST'])
def nova_propriedade():
    if request.method == 'POST':
        # Obter dados do formulário
        tipo = request.form.get('tipo')
        quartos = request.form.get('quartos')
        suites = request.form.get('suites')
        salas = request.form.get('salas')
        cozinhas = request.form.get('cozinhas')
        valor = float(request.form.get('valor'))  # Convert to float
        rua = request.form.get('rua')
        numero = request.form.get('numero')
        bairro = request.form.get('bairro')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        area = request.form.get('area')
        descricao = request.form.get('descricao')
        imagem = request.files['imagem']  # Obter o arquivo da imagem
        imagem_path = None  # Assign a default value

        #imagem_url = request.form.get('imagem')  # Obter a URL da imagem
        # Download da imagem da URL pública
        # if imagem_url:
        #     response = requests.get(imagem_url)
        #     if response.status_code == 200:
        #         # Gerar um nome de arquivo único
        #         temp_filename = str(uuid.uuid4()) + '.jpg'
        #
        #         # Salvar a imagem no sistema de arquivos
        #         imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        #         with open(imagem_path, 'wb') as file:
        #             file.write(response.content)
        #     else:
        #         imagem_path = None
        # else:
        #     imagem_path = None

        #imagem = request.files['imagem']  # Obter o arquivo da imagem
        # if imagem:
        #     imagem_binaria = imagem.read()  # Ler os dados binários da imagem
        #     imagem_codificada = base64.b64encode(imagem_binaria)  # Codificar a imagem em base64
        #     imagem_base64 = imagem_codificada.decode('utf-8')  # Converter para uma string legível


        piscina = 'piscina' in request.form
        praia = 'praia' in request.form
        lazer = 'lazer' in request.form
        quintal = 'quintal' in request.form
        jardim = 'jardim' in request.form
        varanda = 'varanda' in request.form
        solarium = 'solarium' in request.form
        quadra = 'quadra' in request.form
        elevador = 'elevador' in request.form

        # Insira os valores na coleção de propriedades no MongoDB
        propriedade = {
            'tipo': tipo,
            'quartos': quartos,
            'suites': suites,
            'salas': salas,
            'cozinhas': cozinhas,
            'valor': valor,
            'rua': rua,
            'numero': numero,
            'bairro': bairro,
            'cidade': cidade,
            'estado': estado,
            'area': area,
            'descricao': descricao,
            'imagem': temp_filename if imagem_path else None,
            #'imagem': imagem,
            # 'imagem': imagem_base64,  # Salvar a imagem codificada em base64 no campo 'imagem'

            'piscina': piscina,
            'praia': praia,
            'lazer': lazer,
            'quintal': quintal,
            'jardim': jardim,
            'varanda': varanda,
            'solarium': solarium,
            'quadra': quadra,
            'elevador': elevador
        }
        if imagem:
            # Gerar um nome de arquivo único
            temp_filename = str(uuid.uuid4()) + '.jpg'

            # Salvar a imagem no sistema de arquivos
            imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            imagem.save(imagem_path)

            # Atualizar o documento da propriedade com o nome do arquivo
            propriedade['imagem'] = temp_filename
        collection.insert_one(propriedade)

        return redirect('/propriedades/sucesso')
    else:
        return render_template('nova_propriedade.html')

@app.route('/propriedades/sucesso')
def sucesso_propriedade():
    return render_template('sucesso_propriedade.html')

from babel import numbers


@app.route('/propriedades/<id>')
def exibir_propriedade(id):
    exibir_imovel = collection.find_one({'_id': ObjectId(id)})
    if exibir_imovel:
        valor = exibir_imovel.get('valor')
        if valor is not None:
            locale = 'pt_BR'  # Set the appropriate locale for formatting currency
            valor_formatado = format_currency(valor, 'BRL', locale=locale)
        else:
            valor_formatado = None
        # Montar o caminho completo da imagem
        imagem_filename = exibir_imovel.get('imagem')
        if imagem_filename:
            imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], imagem_filename)
            return send_file(imagem_path, mimetype='image/jpeg')

        imagem_base64 = exibir_imovel.get('imagem_base64')
        if imagem_base64:
            imagem_decodificada = base64.b64decode(imagem_base64)
            return send_file(io.BytesIO(imagem_decodificada), mimetype='image/jpeg')
        else:
            imagem_path = None

        # imagem_base64 = None  # Inicialize a variável imagem_base64
        #
        # if 'imagem' in exibir_imovel:
        #     imagem_base64 = exibir_imovel['imagem']
        #
        # if imagem_base64:
        #     imagem_decodificada = base64.b64decode(imagem_base64)  # Decodificar a imagem em base64
        #     return send_file(io.BytesIO(imagem_decodificada), mimetype='image/jpeg')

        return render_template('exibir_propriedade.html', propriedade=exibir_imovel, valor_formatado=valor_formatado, imagem_path=imagem_path)
    else:
        return render_template('propriedade_nao_encontrada.html')






@app.route('/propriedades/<id>/editar', methods=['GET', 'POST'])
def editar_propriedade(id):
    if request.method == 'POST':
        # Obter dados do formulário
        tipo = request.form.get('tipo')
        quartos = request.form.get('quartos')
        suites = request.form.get('suites')
        salas = request.form.get('salas')
        cozinhas = request.form.get('cozinhas')
        valor = float(request.form.get('valor'))  # Convert to float
        rua = request.form.get('rua')
        numero = request.form.get('numero')
        bairro = request.form.get('bairro')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        area = request.form.get('area')
        descricao = request.form.get('descricao')
        #imagem = request.form.get('imagem')  # Obter a URL da imagem
        imagem = request.files['imagem']  # Obter o arquivo da imagem
        imagem_path = None  # Assign a default value

        piscina = 'piscina' in request.form
        praia = 'praia' in request.form
        lazer = 'lazer' in request.form
        quintal = 'quintal' in request.form
        jardim = 'jardim' in request.form
        varanda = 'varanda' in request.form
        solarium = 'solarium' in request.form
        quadra = 'quadra' in request.form
        elevador = 'elevador' in request.form

        if imagem:
            # Gerar um nome de arquivo único
            temp_filename = str(uuid.uuid4()) + '.jpg'

            # Salvar a imagem no sistema de arquivos
            imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            imagem.save(imagem_path)

            # Atualizar o documento da propriedade com o nome do arquivo
            propriedade['imagem'] = temp_filename


        # Atualizar os valores da propriedade no banco de dados
        collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'tipo': tipo,
                'quartos': quartos,
                'suites': suites,
                'salas': salas,
                'cozinhas': cozinhas,
                'valor': valor,
                'rua': rua,
                'numero': numero,
                'bairro': bairro,
                'cidade': cidade,
                'estado': estado,
                'area': area,
                'descricao': descricao,
                'imagem': imagem,
                'piscina': piscina,
                'praia': praia,
                'lazer': lazer,
                'quintal': quintal,
                'jardim': jardim,
                'varanda': varanda,
                'solarium': solarium,
                'quadra': quadra,
                'elevador': elevador
            }}
        )

        return redirect('/propriedades')
    else:
        editar_imovel = collection.find_one({'_id': ObjectId(id)})
        if editar_imovel:
            return render_template('editar_propriedade.html', editar_imovel=editar_imovel)
        else:
            return redirect('/propriedades')



@app.route('/propriedades/excluir', methods=['GET', 'POST'])
def excluir_propriedade():
    if request.method == 'POST':
        id_propriedade = request.form.get('id_propriedade')
        excluir_imovel = collection.find_one({'_id': ObjectId(id_propriedade)})
        if excluir_imovel:
            return redirect(f'/propriedades/excluir/{id_propriedade}')

    return render_template('excluir_propriedade.html', excluir_imovel=None)


@app.route('/propriedades/excluir/<id>', methods=['GET', 'POST'])
def confirmar_exclusao(id):
    excluir_imovel = collection.find_one({'_id': ObjectId(id)})
    if excluir_imovel:
        if request.method == 'POST':
            collection.delete_one({'_id': ObjectId(id)})
            return redirect('/propriedades')

        return render_template('excluir_propriedade.html', excluir_imovel=excluir_imovel)

    return redirect('/propriedades')






if __name__ == '__main__':
    app.run(debug=True)
