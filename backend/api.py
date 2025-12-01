from flask import Blueprint, jsonify, url_for, request
from dotenv import load_dotenv
import yaml
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

def create_api_blueprint(app):
    """
    Cria e configura o Blueprint da Backend, injetando a aplicação Flask
    para permitir a descoberta dinâmica de rotas.
    """
    bp_api = Blueprint('api', __name__)

    @bp_api.route(f'{FLASK_PREFIX}/backend', methods=['GET'])
    def api_index():
        """
        Provides a HATEOAS-style list of all available Backend endpoints following HAL specification.
        The links are grouped by resource and filtered to only include GET methods.
        ---
        tags:
          - Backend
        responses:
          200:
            description: A JSON object containing links to all other Backend resources.
        """
        base_url = request.url_root.rstrip('/')
        links = {}
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static' or not rule.endpoint.startswith(tuple(app.blueprints.keys())):
                continue
            view_function = app.view_functions[rule.endpoint]
            module_name = view_function.__module__
            if not module_name.startswith('backend.') or module_name == 'backend.docs' or module_name == 'backend.api':
                continue
            if 'GET' not in rule.methods:
                continue
            rel_module = module_name.split('.')[-1]
            rel_action = rule.endpoint.split('.')[-1]
            if rel_module not in links:
                links[rel_module] = []
            href = f"{base_url}{rule.rule.replace('<', '{').replace('>', '}')}"

            link_info = {"href": href, "rel": rel_action, "type": "GET"}
            links[rel_module].append(link_info)

        return jsonify({"_links": links})

    return bp_api