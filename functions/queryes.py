import os
import re
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from functions.alerts import load_alerts_state, save_alerts_state, check_send_alert
from functions.reports import save_incidents_to_file

load_dotenv(override=True)

DB_NAME1 = os.getenv('DB_NAME1')
DB_NAME2 = os.getenv('DB_NAME2')

encoded_host = quote_plus(os.getenv('DB_HOST1'))
encoded_user = quote_plus(os.getenv('DB_USER1'))
encoded_password = quote_plus(os.getenv('DB_PASSWORD1'))
encoded_db = quote_plus(os.getenv('DB_NAME1'))
engine = create_engine(f"mysql+pymysql://{encoded_user}:{encoded_password}@{encoded_host}/{encoded_db}", pool_pre_ping=True)

encoded_d_user = quote_plus(os.getenv('DB_USER2'))
encoded_d_password = quote_plus(os.getenv('DB_PASSWORD2'))
encoded_d_host = quote_plus(os.getenv('DB_HOST2'))
encoded_d_db = quote_plus(os.getenv('DB_NAME2'))
engine_d = create_engine(f"mysql+pymysql://{encoded_d_user}:{encoded_d_password}@{encoded_d_host}/{encoded_d_db}", pool_pre_ping=True)

def execute_count(engine, query):
    with engine.connect() as conn:
        return conn.execute(text(query)).scalar()

def execute_query(engine, query):
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
        # ----------------- Query 2: -----------------
        try:
            count_erro = execute_count(engine, """
                SELECT SQL_NO_CACHE COUNT(*)
                FROM 
                WHERE;
            """)
            curr_error_icon = "🟢" if count_erro == 0 else "🟡" if count_erro <= 50 else "🔴"
            service_name = "Query2"
            current_state = f"{curr_error_icon} {count_erro}"
            prev_status_icon = previous_state.get(service_name, "").split(" ")[0]

            if prev_status_icon != curr_error_icon and "🟡" not in (prev_status_icon, curr_error_icon):
                incidents_queryes.append({
                    "service": service_name,
                    "type": "Banco",
                    "timestamp": timestamp,
                    "reason": current_state
                })
                check_send_alert(service_name, current_state, previous_state, DB_NAME1, "telegram_infra", 'function')
            last_state[service_name] = current_state
        except Exception as e:
            print(f"Erro na query {service_name}: {e}")
            last_state[service_name] = "🔴 erro"

        # ----------------- Query 3: -----------------
        try:
            service_name = "Query3"
            count_correct = execute_count(engine, """
                SELECT COUNT
                FROM 
                JOIN 
                WHERE NOT;
            """)
            status_correct = "🟢"
            last_state[service_name] = f"{status_correct} {count_correct}"
        except Exception as e:
            print(f"Erro na query {service_name}: {e}")
            last_state[service_name] = "🔴 erro"

        # ----------------- Query 4: -----------------
        try:
            multas_result, columns = execute_query(engine, "SELECT * FROM VW4;")
            columns = list(columns)
            count = int(multas_result[0][columns.index('Quantidade')])
            percentual = float(multas_result[0][columns.index('percentual_da_meta')])
            curr_r_icon = "🟢" if percentual <= 70 else "🟡" if percentual <= 100 else "🔴"
            service_name = "Query4"
            current_state = f"{curr_r_icon} {count} ({percentual:.2f}%)"
            prev_state = previous_state.get(service_name, "")
            match = re.search(r"\(([\d.]+)%\)", prev_state)
            percentual_anterior = float(match.group(1)) if match else None
            if int(percentual) % 10 == 0 and int(percentual) != int(percentual_anterior or 0):
                incidents_queryes.append({
                    "service": service_name,
                    "type": "Banco",
                    "timestamp": timestamp,
                    "reason": current_state
                })
                check_send_alert(service_name, current_state, previous_state, DB_NAME1, "telegram_miner", 'function')
                last_state[service_name] = current_state
        except Exception as e:
            print(f"Erro na query {service_name}: {e}")
            last_state[service_name] = "🔴 erro"

        # ----------------- Query 5: -----------------
        try:
            debitos_result, columns = execute_query(engine_d, "SELECT * FROM VW5;")
            columns = list(columns)
            count_d = debitos_result[0][columns.index('Quantidade')]
            percentual_d = float(debitos_result[0][columns.index('percentual_da_meta')])
            curr_r_d_icon = "🟢" if percentual_d <= 70 else "🟡" if percentual_d <= 100 else "🔴"
            service_name = "Query5"
            current_state = f"{curr_r_d_icon} {count_d} ({percentual_d:.2f}%)"
            prev_state = previous_state.get(service_name, "")
            match = re.search(r"\(([\d.]+)%\)", prev_state)
            percentual_d_anterior = float(match.group(1)) if match else None
            if int(percentual_d) % 10 == 0 and int(percentual_d) != int(percentual_d_anterior or 0):
                incidents_queryes.append({
                    "service": service_name,
                    "type": "Banco",
                    "timestamp": timestamp,
                    "reason": current_state
                })
                check_send_alert(service_name, current_state, previous_state, DB_NAME2, "telegram_miner", 'function')
                last_state[service_name] = current_state
        except Exception as e:
            print(f"Erro na query {service_name}: {e}")
            last_state[service_name] = "🔴 erro"

        # ----------------- Query 6 e 7: -----------------
        def processar_s(tipo_consulta, threshold_1, threshold_2, previous_state, last_state, timestamp, incidents_queryes):
            try:
                result, columns = execute_query(engine, f"""
                    SELECT * FROM VW6 WHERE tipo_consulta = '{tipo_consulta}';
                """)
                if result:
                    columns = list(columns)
                    count = result[0][columns.index('quantidade_atual')]
                    perc = float(result[0][columns.index('percentual')])
                else:
                    count = 0
                    perc = 0.0
                if perc <= threshold_1:
                    icon = "🟢"
                elif perc <= threshold_2:
                    icon = "🟡"
                else:
                    icon = "🔴"

                service_name = f"Query6{tipo_consulta}"
                current_state = f"{icon} {count} ({perc:.2f}%)"
                prev_icon = previous_state.get(service_name, "").split(" ")[0]

                if prev_icon != icon and "🟡" not in (icon, prev_icon):
                    incidents_queryes.append({
                        "service": service_name,
                        "type": "Banco",
                        "timestamp": timestamp,
                        "reason": current_state
                    })
                    check_send_alert(service_name, current_state, previous_state, DB_NAME1, "telegram_miner", 'function')

                last_state[service_name] = current_state
                return count, perc, icon

            except Exception as e:
                print(f"Erro na query Query6{tipo_consulta}: {e}")
                last_state[f"Query6{tipo_consulta}"] = "🔴 erro"
                return "erro", "erro", "🔴"

        count_cpf, perc_cpf, curr_cpf_icon = processar_s(
            tipo_consulta="CPF", threshold_1=10, threshold_2=30,
            previous_state=previous_state, last_state=last_state,
            timestamp=timestamp, incidents_queryes=incidents_queryes
        )

        count_cnpj, perc_cnpj, curr_cnpj_icon = processar_s(
            tipo_consulta="CNPJ", threshold_1=20, threshold_2=50,
            previous_state=previous_state, last_state=last_state,
            timestamp=timestamp, incidents_queryes=incidents_queryes
        )
            
        # ----------------- Query 8: -----------------
        try:
            count_curr_m = execute_count(engine, """
                SELECT COUNT;
            """)
            curr_m_icon = "🟢" if count_curr_m > 0 else "🔴"
            current_state = f"{curr_m_icon} {count_curr_m}"
            service_name = "Query8"
            prev_m_icon = previous_state.get(service_name, "").split(" ")[0]
            
            if prev_m_icon != curr_m_icon:
                incidents_queryes.append({
                    "service": service_name,
                    "type": "Banco",
                    "timestamp": timestamp,
                    "reason": current_state
                })
                check_send_alert(service_name, current_state, previous_state, DB_NAME1, "telegram_miner", 'function')
            
            last_state[service_name] = current_state

        except Exception as e:
            print(f"Erro na query {service_name}: {e}")
            last_state[service_name] = "🔴 erro"

        # ----------------- Finalização -----------------
        alerts_state["previous_state"] = last_state
        alerts_state["last_state"] = last_state
        alerts_state["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_alerts_state("queryes", alerts_state)

        if incidents_queryes:
            save_incidents_to_file(incidents_queryes)

        return {
            "id2": {"count": count_erro, "percentage": "", "status_icon": curr_error_icon},
            "id3": {"count": count_correct, "percentage": "", "status_icon": status_correct},
            "id4": {"count": count, "percentage": f"{percentual:.2f}%" if count != "erro" else "", "status_icon": curr_r_icon},
            "id5": {"count": count_d, "percentage": f"{percentual_d:.2f}%" if count_d != "erro" else "", "status_icon": curr_r_d_icon},
            "id6": {"count": count_cpf, "percentage": f"{perc_cpf:.2f}%" if count_cpf != "erro" else "", "status_icon": curr_cpf_icon},
            "id7": {"count": count_cnpj, "percentage": f"{perc_cnpj:.2f}%" if count_cnpj != "erro" else "", "status_icon": curr_cnpj_icon},
            "id8": {"count": count_curr_m, "percentage": "", "status_icon": curr_m_icon}
        }

    except Exception as e:
        print(f"Ocorreu algum erro ao executar alguma das queryes")
        return None
