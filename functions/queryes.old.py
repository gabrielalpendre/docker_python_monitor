import os
import mysql.connector
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv(override=True)

# Configuracao do banco de dados
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_query_counts():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()

        # Executar primeira query
        query1 = """
        SELECT COUNT(*) FROM usuarioANTT usr
        INNER JOIN cliente c ON usr.id_cliente = c.id
        WHERE usr.idOrgao = '17'
        AND usr.status = 2
        AND c.id IN (
            SELECT DISTINCT v.id_cliente FROM veiculos v WHERE v.status IN (0,5)
        )
        AND c.id NOT IN (
            SELECT DISTINCT usra.id_cliente FROM usuarioANTT usra WHERE usra.status = 0 AND usra.idOrgao=17
        );
        """
        cursor.execute(query1)
        count1 = cursor.fetchone()[0]

        # Executar segunda query
        query2 = """
        SELECT COUNT(*) AS total_inconsistencias
        FROM multaDetalhada md
        WHERE md.id IN (SELECT me.idmultaDetalhada FROM mensagensErro me WHERE md.id = me.idmultaDetalhada)
        AND (
            md.dataInfracao > md.apCondutorDataVencimento
            OR md.dataInfracao > md.dataVencimento
            OR md.dataInfracao > md.dataVencimentoBoleto
        );
        """
        cursor.execute(query2)
        count2 = cursor.fetchone()[0]

        # Executar segunda query
        query3 = """
        SELECT 
            COUNT(*) AS totalMultasOK
        FROM multaDetalhada md
        WHERE md.id IN (SELECT me.idmultaDetalhada FROM mensagensErro me WHERE md.id = me.idmultaDetalhada)
        AND (
            CASE
                WHEN md.dataInfracao <= md.apCondutorDataVencimento THEN 'OK'
                ELSE 'dataInfracao nao pode ser maior que apCondutorDataVencimento'
            END = 'OK'
            AND
            CASE
                WHEN md.dataInfracao <= md.dataVencimento THEN 'OK'
                ELSE 'dataInfracao nao pode ser maior que dataVencimento'
            END = 'OK'
            AND
            CASE
                WHEN md.dataInfracao <= md.dataVencimentoBoleto THEN 'OK'
                ELSE 'dataInfracao nao pode ser maior que dataVencimentoBoleto'
            END = 'OK'
        );
        """

        cursor.execute(query3)
        count3 = cursor.fetchone()[0]

        # Montar status
        status_icon1 = "🟢" if count1 == 0 else "🔴"
        status_icon2 = "🟢" if count2 == 0 else "🟡" if count2 <= 100 else "🔴"
        status_icon3 = "🟢"

        return {
            "id1": {"count": count1, "status_icon": status_icon1},
            "id2": {"count": count2, "status_icon": status_icon2},
            "id3": {"count": count3, "status_icon": status_icon3},
        }

    except Exception as e:
        print(f"Erro ao executar query: {e}")
        return None

    finally:
        if connection:
            connection.close()
