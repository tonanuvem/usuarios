from flask import Flask, current_app, render_template
from flask import request, Blueprint

from flask_cors import CORS
from flask_restful.reqparse import RequestParser

# https://pypi.org/project/flask-restful-swagger-3/
from flask_restful_swagger_3 import swagger, get_swagger_blueprint
from flask_restful_swagger_3 import Api, swagger, Resource, abort
from flask_restful_swagger_3 import Schema

from datetime import datetime

app = Flask(__name__)
CORS(app, resources={"/api/*": {"origins": "*"}})


######
# Modelo de Entidade com suas propriedades

class UsuarioModel(Schema):
    properties = {
        'login': {
            'type': 'string'
        },
        'password': {
            'type': 'string'
        },
    }
    required = ['login']

class ErrorModel(Schema):
    type = 'object'
    properties = {
        'message': {
            'type': 'string'
        }
    }

#####
# Rotas e Endpoints

def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

PEOPLE = {
    "maria": {
        "login": "maria",
        "password": "123",
        "timestamp": get_timestamp(),
    },
    "ana": {
        "login": "ana",
        "password": "123",
        "timestamp": get_timestamp(),
    },
    "joao": {
        "login": "joao",
        "password": "123",
        "timestamp": get_timestamp(),
    },
}

class Usuarios(Resource):
    
    # Get:
    @swagger.tags('usuarios')
    @swagger.response(response_code=200, summary='Retornar todos os usuários')
    def get(self):
        """
        Retorna todos os usuários.
        """
        return [PEOPLE[key] for key in sorted(PEOPLE.keys())], 200
         
    
    # Post:    
    @swagger.tags('usuarios')
    @swagger.reorder_with(UsuarioModel, response_code=200, summary="Adicionar Usuário")
    @swagger.parameter(_in='query', name='usuarios', schema=UsuarioModel, required=True, description='campos')
    def post(self, _parser):
        """
        Adicionar um novo Usuário
        """
        # Valida o request body através do schema model:
        try:
            data = UsuarioModel(**_parser.parse_args())
        except ValueError as e:
            return ErrorModel(**{'message': e.args[0]}), 400
        
        # Insere o item:
        login = data.get("login", None)
        password = data.get("password", None)
        if login not in PEOPLE and login is not None:
            PEOPLE[login] = {
                "login": login,
                "password": password,
                "timestamp": get_timestamp(),
            }
            return "{login} criado com sucesso".format(login=login), 201
        else:
            abort(406, message="Login "+login+" ja existe")


class Usuario(Resource):
    # Get:
    @swagger.tags('usuarios')
    @swagger.response(response_code=200, summary='Retornar informações de um usuário específico')
    def get(self, login):
        """
        Retorna informações de um usuário específico.
        :param login: Identificador do login
        """
        if login in PEOPLE:
            person = PEOPLE.get(login)
        else:
            abort(404, message="Login "+login+ " nao encontrado")
        return person, 200
    
    # Put:
    @swagger.tags('usuarios')
    @swagger.reorder_with(UsuarioModel, response_code=200, summary="Atualizar informações de um usuário específico")
    @swagger.parameter(_in='query', name='usuarios', schema=UsuarioModel, required=True, description='campos') 
    def put(self, login, _parser):
        """
        Atualiza as informações de um usuário específico.
        :param login: Identificador do login
        """
        if login in PEOPLE:
            # Valida o request body através do schema model:
            # Se um recurso tiver decorator com swagger.parameters, a documentação será automaticamente atribuída ao argumento _parser.
            try:
                data = UsuarioModel(**_parser.parse_args())
            except ValueError as e:
                return ErrorModel(**{'message': e.args[0]}), 400
            
            # Atualiza o item:
            password = data.get("password", None)

            PEOPLE[login]["password"] = password
            PEOPLE[login]["timestamp"] = get_timestamp()
            return PEOPLE[login], 200
        else:
            abort(404, message="Login "+login+ " nao encontrado")
        
    # Delete:
    @swagger.tags('usuarios')
    @swagger.response(response_code=200, summary='Deletar um usuário específico')
    def delete(self, login):
        """
        Deleta um usuário específico.
        :param login: Identificador do login
        """
        if login in PEOPLE:
            del PEOPLE[login]
            return "{login} deletado com sucesso".format(login=login), 204
        else:
            abort(404, message="Login "+login+ " nao encontrado")


class Autenticacao(Resource):

    # Post:    
    @swagger.tags('autenticacao')
    @swagger.reorder_with(UsuarioModel, response_code=200, summary="Autenticar um Usuário")
    @swagger.parameter(_in='query', name='usuarios', schema=UsuarioModel, required=True, description='campos')
    def post(self, _parser):
        """
        Autenticar um  Usuário
        """
        # Valida o request body através do schema model:
        try:
            data = UsuarioModel(**_parser.parse_args())
        except ValueError as e:
            return ErrorModel(**{'message': e.args[0]}), 400
        
        # Insere o item:
        login = data.get("login", None)
        password = data.get("password", None)
        if login in PEOPLE:
            if password == PEOPLE[login]["password"]:
                return "{login} autenticado com sucesso".format(login=login), 202
            else:
                abort(401, message="Password do login "+login+" invalido")
        else:
            abort(401, message="Login "+login+" nao existe")



#####

# Instead of coding your application from scratch, you may consider searching for an existing Flask Blueprint or Extension that you can reuse.

def get_resources():
    """
    Retorna os endpoints e recursos fornecidos pela API.
    :param app: Flask instance
    :return: API resources
    """
    
    blueprint = Blueprint('api', __name__)
    api = Api(blueprint)

    api.add_resource(Usuarios, '/api/usuarios')
    api.add_resource(Usuario, '/api/usuarios/<string:login>')
    api.add_resource(Autenticacao, '/api/auth')

    return api

# Verificar os recursos da API
api_resources = get_resources()

# Registra um blueprint para os recursos da API
# Em vez de codificar seu aplicativo do zero, você pode considerar o uso de um Flask Blueprint (injeta código no projeto).
# https://realpython.com/flask-blueprint/
app.register_blueprint(api_resources.blueprint)

# Prepara o blueprint do Swagger/OpenAPI
SWAGGER_URL = '/api/doc'  # URL for exposing Swagger UI (without trailing '/')
API_URL = 'swagger.json'  # Our API url (can of course be a local resource)
app.config.setdefault('SWAGGER_BLUEPRINT_URL_PREFIX', '/swagger')
with app.app_context():
    swagger_blueprint = get_swagger_blueprint(
        api_resources.open_api_object,
        swagger_prefix_url=SWAGGER_URL,
        swagger_url=API_URL,
        title='Usuários Microservice', version='1')#, servers=servers)

app.register_blueprint(swagger_blueprint, url_prefix='/swagger')

@app.route('/')
def home(): 
    return render_template('index.html')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
