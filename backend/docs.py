from flasgger import Swagger
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

def setup_swagger(app):
    """
    Configura o Swagger para a aplicação Flask.
    """
    template = {
        "swagger": "2.0",
        "info": {
            "title": "Docker Monitor Backend",
            "description": "Backend para monitoramento de serviços, queries, e alertas.",
            "version": os.getenv('VERSION', '1.0.0')
        },
        "basePath": FLASK_PREFIX,
        "schemes": [
            "http",
            "https"
        ]
    }

    swagger_config = {
        "headers": [],
        "specs_route": "/backend/docs/",
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "swagger_ui": True,
        "static_url_path": "/flasgger_static"
    }
    
    Swagger(app, template=template, config=swagger_config)