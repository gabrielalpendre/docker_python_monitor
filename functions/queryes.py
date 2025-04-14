import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from functions.alerts import load_alerts_state, save_alerts_state, check_send_alert
from functions.reports import save_incidents_to_file

load_dotenv(override=True)

DB_HOSTNAME = os.getenv('DB_HOSTNAME')

encoded_user = quote_plus(os.getenv('DB_USER'))
encoded_password = quote_plus(os.getenv('DB_PASSWORD'))
encoded_host = quote_plus(os.getenv('DB_HOST'))
encoded_db = quote_plus(os.getenv('DB_NAME'))

engine = create_engine(f"mysql+pymysql://{encoded_user}:{encoded_password}@{encoded_host}/{encoded_db}", pool_pre_ping=True)

def execute_count(query):
    with engine.connect() as conn:
        return conn.execute(text(query)).scalar()

def execute_query(query):
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return result.fetchall(), result.keys()

def get_query_counts():
    incidents_queryes = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    alerts_state = load_alerts_state("queryes")
    previous_state = alerts_state.get("previous_state", {})
    last_state = alerts_state.get("last_state", {})

    try:
        # ----------------- Query 1: Locks -----------------
        count_lock = execute_count("""
            SELECT COUNT(*) FROM information_schema.PROCESSLIST WHERE STATE LIKE '%lock%';
        """)
        status_lock = "🟢" if count_lock == 0 else "🔴"
        service_name = f"LockBanco"
        current_state = f"{status_lock} {count_lock}"
        prev_status_icon = previous_state.get(service_name, "").split(" ")[0]

        if prev_status_icon != status_lock:
            if status_lock == "🔴":
                details, columns = execute_query("""
                    SELECT
                    ID AS PROCESS_ID,
                    REGEXP_REPLACE(REPLACE(REPLACE(INFO, '\n', ' '), '\r', ''), ' +', ' ') AS QUERY,
                    DB, HOST, USER, STATE
                    FROM information_schema.PROCESSLIST
                    WHERE STATE LIKE '%lock%'
                """)

                if details:  # Só continua se houver retorno
                    for row in details:
                        for col, val in zip(columns, row):
                            current_state += f"\n{col}: {val}"
                        current_state += "\n"

                    incidents_queryes.append({
                        "service": service_name,
                        "timestamp": timestamp,
                        "reason": current_state
                    })
                    check_send_alert(service_name, current_state, previous_state, DB_HOSTNAME)

        last_state[service_name] = current_state

        # ----------------- Query 2: Mensagens com erro -----------------
        count_erro = execute_count("""
            SELECT SQL_NO_CACHE COUNT(*)
            FROM multaDetalhada md
            WHERE md.id IN (
                SELECT me.idmultaDetalhada
                FROM mensagensErro me
                WHERE md.id = me.idmultaDetalhada
            )
            AND (
                md.dataInfracao > md.apCondutorDataVencimento
                OR md.dataInfracao > md.dataVencimento
                OR md.dataInfracao > md.dataVencimentoBoleto
                OR md.cadastroDataHora < md.dataInfracao
                OR (md.cadastroNotificacao IS NOT NULL AND md.cadastroNotificacao != '0000-00-00' AND md.dataInfracao > md.cadastroNotificacao)
                OR (md.cadastroImposicao IS NOT NULL AND md.cadastroImposicao != '0000-00-00' AND md.dataInfracao > md.cadastroImposicao)
            );
        """)
        status_erro = "🟢" if count_erro == 0 else "🟡" if count_erro <= 50 else "🔴"
        service_name = "MensagensComErro"
        current_state = f"{status_erro} {count_erro}"
        prev_status_icon = previous_state.get(service_name, "").split(" ")[0]

        if ((prev_status_icon != "🔴" and status_erro == "🔴") or (prev_status_icon == "🔴" and status_erro == "🟢")):
            incidents_queryes.append({
                "service": service_name,
                "timestamp": timestamp,
                "reason": current_state
            })
            check_send_alert(service_name, current_state, previous_state, DB_HOSTNAME)

        last_state[service_name] = current_state

        # ----------------- Query 3: Multas OK -----------------
        count_correct = execute_count("""
            SELECT COUNT(mdo.id) FROM multaDetalhada mdo
            WHERE mdo.id IN (
                SELECT me.idmultaDetalhada FROM mensagensErro me WHERE mdo.id = me.idmultaDetalhada
            ) AND (
                (mdo.apCondutorDataVencimento IS NULL OR mdo.apCondutorDataVencimento = '0000-00-00' OR mdo.dataInfracao <= mdo.apCondutorDataVencimento)
                AND (mdo.dataVencimento IS NULL OR mdo.dataVencimento = '0000-00-00' OR mdo.dataInfracao <= mdo.dataVencimento)
                AND (mdo.dataVencimentoBoleto IS NULL OR mdo.dataVencimentoBoleto = '0000-00-00' OR mdo.dataInfracao <= mdo.dataVencimentoBoleto)
                AND (mdo.cadastroDataHora >= mdo.dataInfracao)
                AND (mdo.cadastroNotificacao IS NULL OR mdo.cadastroNotificacao = '0000-00-00' OR mdo.dataInfracao <= mdo.cadastroNotificacao)
                AND (mdo.cadastroImposicao IS NULL OR mdo.cadastroImposicao = '0000-00-00' OR mdo.dataInfracao <= mdo.cadastroImposicao)
            );
        """)
        status_correct = "🟢"
        service_name = "MultasValidas"
        current_state = f"{status_correct} {count_correct}"
        last_state[service_name] = current_state

        # ----------------- Finalização -----------------
        alerts_state["previous_state"] = last_state
        alerts_state["last_state"] = last_state
        save_alerts_state("queryes", alerts_state)

        if incidents_queryes:
            save_incidents_to_file(incidents_queryes)

        return {
            "id1": {"count": count_lock, "status_icon": status_lock},
            "id2": {"count": count_erro, "status_icon": status_erro},
            "id3": {"count": count_correct, "status_icon": status_correct},
        }

    except Exception as e:
        print(f"Erro ao executar query com SQLAlchemy: {e}")
        return None
