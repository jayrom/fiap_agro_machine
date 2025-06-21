#---------------------------------------------------
# TiãoTech Agro Machine
# Por favor, leia o README.md para mais informações.
#---------------------------------------------------


# Importa módulos.
import os
import oracledb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
import paho.mqtt.client as mqtt
import json
import time
from collections import deque
import traceback

# Configura pandas para imprimir dataframe completo
# pd.set_option('display.max_rows', None)


# Lê arquivo de dados de leitura de sensores.

# Caminho completo para o arquivo CSV
# Ajuste este caminho para a localização EXATA do seu computer_7.csv
# Ex: r'c:\Users\luarc\OneDrive\Área de Trabalho\fiap_agro_machine\sprint_1\input\computer_7.csv'
data_file = r'c:\Users\luarc\OneDrive\Área de Trabalho\fiap_agro_machine\sprint_1\input\computer_7.csv'
log_file = r'c:\Users\luarc\OneDrive\Área de Trabalho\fiap_agro_machine\sprint_1\log\computer_7.log'


# Conecta banco de dados.
try:
    # Efetua a conexão com o Usuário no servidor

    db_user = 'RM565576' # Insira a matrícula (ex.: RM123456)
    db_pass = 'Fiap#2025' # Insira a senha 
    conn = oracledb.connect(user=db_user, password=db_pass, dsn='oracle.fiap.com.br:1521/ORCL')
    # Cria as instruções para cada módulo
    inst_cadastro = conn.cursor()
    inst_consulta = conn.cursor()
    inst_alteracao = conn.cursor()
    inst_exclusao = conn.cursor()

except Exception as e:  
    print(f"Erro ao conectar ao banco de dados: {e}") # Mensagem mais descritiva
    conexao = False     # Não há conexão

else:
    conexao = True      # Há conexão

margem = ' ' * 4

# Configurações MQTT para o Python
mqtt_broker_py = "broker.hivemq.com"
mqtt_port_py = 1883
mqtt_topic_subscribe = "fe/field-3/plot-1/computer-7/data"
mqtt_client_id_py = "python-subscriber-agro-machine"

mqtt_message_buffer = deque(maxlen=100)
# Mover a inicialização da variável global para o topo do script, antes de QUALQUER FUNÇÃO.
add_to_mqtt_buffer = False 

# Esta variável global conterá o DataFrame das últimas leituras MQTT coletadas.
last_100_mqtt_dataframe = pd.DataFrame() 

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao broker MQTT com sucesso!")
        client.subscribe(mqtt_topic_subscribe)
        print(f"Inscrito no tópico: {mqtt_topic_subscribe}")
    else:
        print(f"Falha na conexão MQTT, código de retorno: {rc}")

def on_message(client, userdata, msg):
    global mqtt_message_buffer, add_to_mqtt_buffer 
    
    try:
        payload_str = msg.payload.decode('utf-8')
        json_data = json.loads(payload_str)
        
        if add_to_mqtt_buffer:
            mqtt_message_buffer.append(json_data) 
            print(f"\n[Coleta Ativa] Mensagem MQTT recebida no tópico {msg.topic}:")
            print(f"Conteúdo: {payload_str}")
            print("Dados do sensor:")
            for key, value in json_data.items():
                print(f"{key}: {value}")
            print("Mensagem adicionada ao buffer para cadastro em lote.")

    except json.JSONDecodeError:
        print("Payload não é um JSON válido.")
        print(f"Conteúdo bruto: {msg.payload.decode('utf-8')}")
    except Exception as e:
        print(f"Erro ao processar a mensagem MQTT (no on_message): {e}") 


# Cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, mqtt_client_id_py)
client.on_connect = on_connect
client.on_message = on_message

# Tenta conectar ao broker MQTT
try:
    client.connect(mqtt_broker_py, mqtt_port_py, 60)
    client.loop_start() # Inicia uma thread em background para processar mensagens
except Exception as e:
    print(f"Erro ao conectar ao broker MQTT: {e}")

# nova função para predição de irrigação
def prever_irrigacao(inst_consulta, conn, data_file):
    os.system('cls')
    print("----- Predição de Irrigação -----")

    try:
        colunas_relevantes = [
            'READING_TIME', 'READING_HUMIDITY_VALUE', 'READING_HUMIDITY_LEVEL',
            'READING_PUMP', 'READING_PHOSPHORUS', 'READING_POTASSIUM',
            'READING_PH_VALUE', 'READING_PH_LEVEL', 'READING_TEMPERATURE'
        ]
        
        # Para evitar o FutureWarning com concatenação de DataFrames vazios/NaNs
        dados_completos = pd.DataFrame(columns=colunas_relevantes)

        # 1. Carregar dados históricos do CSV
        try:
            data_csv = pd.read_csv(data_file)
            print(f"Dados históricos carregados do CSV: {data_csv.shape[0]} registros.")
        except FileNotFoundError:
            print(f"Erro: Arquivo '{data_file}' não encontrado. A predição usará apenas dados do banco de dados (se houver).")
            data_csv = pd.DataFrame() 
        except Exception as e:
            print(f"Erro ao carregar dados do CSV: {e}. A predição usará apenas dados do banco de dados (se houver).")
            data_csv = pd.DataFrame()
            
        # 2. Carregar dados históricos do banco de dados
        sql_select_all = 'SELECT * FROM T_READINGS'
        inst_consulta.execute(sql_select_all)
        data_db = inst_consulta.fetchall()
        colunas_db = [desc[0] for desc in inst_consulta.description]
        df_db = pd.DataFrame(data_db, columns=colunas_db)
        print(f"Dados históricos carregados do banco de dados: {df_db.shape[0]} registros.")

        # Unir dados do CSV
        if not data_csv.empty:
            data_csv_renamed = data_csv.rename(columns={
                'time': 'READING_TIME',
                'valor_umidade': 'READING_HUMIDITY_VALUE',
                'nivel_umidade': 'READING_HUMIDITY_LEVEL',
                'bomba': 'READING_PUMP',
                'fosforo': 'READING_PHOSPHORUS',
                'potassio': 'READING_POTASSIUM',
                'valor_ph': 'READING_PH_VALUE',
                'nivel_ph': 'READING_PH_LEVEL',
                'temperatura': 'READING_TEMPERATURE'
            })
            
            for col in ['READING_TIME', 'READING_HUMIDITY_VALUE', 'READING_PH_VALUE',
                        'READING_POTASSIUM', 'READING_TEMPERATURE']:
                data_csv_renamed[col] = pd.to_numeric(data_csv_renamed[col], errors='coerce')

            for col in ['READING_HUMIDITY_LEVEL', 'READING_PUMP',
                        'READING_PHOSPHORUS', 'READING_PH_LEVEL']:
                data_csv_renamed[col] = data_csv_renamed[col].astype(str).str.lower()

            data_csv_selected = data_csv_renamed[colunas_relevantes].copy()
            dados_completos = pd.concat([dados_completos, data_csv_selected], ignore_index=True) if not data_csv_selected.empty else dados_completos
            print(f"Total de dados do CSV adicionados: {data_csv_selected.shape[0]} registros.")


        # Unir dados do DB
        if not df_db.empty:
            for col in ['READING_TIME', 'READING_HUMIDITY_VALUE', 'READING_PH_VALUE',
                        'READING_POTASSIUM', 'READING_TEMPERATURE']:
                if col in df_db.columns: 
                    df_db[col] = pd.to_numeric(df_db[col], errors='coerce')
                else:
                    print(f"Aviso: Coluna numérica '{col}' esperada não encontrada no DataFrame do Banco de Dados.")


            for col in ['READING_HUMIDITY_LEVEL', 'READING_PUMP',
                        'READING_PHOSPHORUS', 'READING_PH_LEVEL']:
                if col in df_db.columns: 
                    df_db[col] = df_db[col].astype(str).str.lower()
                else:
                    print(f"Aviso: Coluna categórica '{col}' esperada não encontrada no DataFrame do Banco de Dados.")

            df_db_selected = df_db[colunas_relevantes].copy()
            dados_completos = pd.concat([dados_completos, df_db_selected], ignore_index=True) if not df_db_selected.empty else dados_completos
            print(f"Total de dados do DB adicionados: {df_db_selected.shape[0]} registros.")

        if dados_completos.empty: 
            print("Não há dados suficientes para treinamento do modelo. Certifique-se de que o CSV ou o banco de dados contêm registros.")
            input("Pressione ENTER para continuar.")
            return
        
        dados_completos.dropna(inplace=True)
        
        if dados_completos.empty: 
            print("Após o pré-processamento e remoção de valores inválidos, não restaram dados válidos para o treinamento do modelo.") # Mensagem melhorada
            input("Pressione ENTER para continuar.")
            return
            
        # 3. Pré-processamento dos dados (LabelEncoders)
        le_humidity_level = LabelEncoder()
        le_pump = LabelEncoder()
        le_phosphorus = LabelEncoder()
        le_ph_level = LabelEncoder()

        try:
            dados_completos['READING_HUMIDITY_LEVEL_ENCODED'] = le_humidity_level.fit_transform(dados_completos['READING_HUMIDITY_LEVEL'])
            dados_completos['READING_PUMP_ENCODED'] = le_pump.fit_transform(dados_completos['READING_PUMP']) #TARGET
            dados_completos['READING_PHOSPHORUS_ENCODED'] = le_phosphorus.fit_transform(dados_completos['READING_PHOSPHORUS'])
            
            # Garante que todos os valores para o encoder de pH são strings, tratando NaNs
            all_ph_levels_from_df = dados_completos['READING_PH_LEVEL'].dropna().astype(str).tolist()
            all_ph_levels = all_ph_levels_from_df + ['acid', 'alca', 'norm', 'unknown'] # Adiciona 'unknown' aqui também
            all_ph_levels = sorted(list(set(all_ph_levels))) # Remove duplicatas e ordena
            
            le_ph_level.fit(all_ph_levels)
            dados_completos['READING_PH_LEVEL_ENCODED'] = le_ph_level.transform(dados_completos['READING_PH_LEVEL'].fillna('unknown').astype(str)) # fillna para garantir que NaN seja tratado

        except Exception as e:
            print(f"Erro ao codificar variáveis categóricas: {e}. Verifique se as colunas categóricas têm valores válidos nos dados históricos ('baixo', 'OK', 'ligada', 'desligada', 'alto', 'acid', 'alca', 'norm').")
            traceback.print_exc() # Print do traceback para debug
            input("Pressione ENTER para continuar.")
            return

        le_potassium_feature = LabelEncoder()
        # Garante que todos os valores para o encoder de potássio são strings, tratando NaNs
        all_potassium_levels_from_df = dados_completos['READING_POTASSIUM'].dropna().astype(str).tolist()
        all_potassium_levels = all_potassium_levels_from_df + ['OK', 'Baixo', 'unknown']
        all_potassium_levels = sorted(list(set(all_potassium_levels))) # Remove duplicatas e ordena
        
        le_potassium_feature.fit(all_potassium_levels)
        
        # Usar .loc para evitar SettingWithCopyWarning
        # Garantir que NaN seja preenchido com 'unknown' antes da transformação
        dados_completos.loc[:, 'READING_POTASSIUM_ENCODED'] = le_potassium_feature.transform(dados_completos['READING_POTASSIUM'].fillna('unknown').astype(str))

        features_for_model = [ 
            'READING_TIME', 'READING_HUMIDITY_VALUE', 'READING_HUMIDITY_LEVEL_ENCODED',
            'READING_PHOSPHORUS_ENCODED', 'READING_POTASSIUM_ENCODED', 
            'READING_PH_VALUE', 'READING_PH_LEVEL_ENCODED', 'READING_TEMPERATURE'
        ]

        # Usar .copy() para evitar SettingWithCopyWarning
        X_for_model = dados_completos[features_for_model].copy()
        y = dados_completos[target].copy() 


        if X_for_model.shape[0] < 2:
            print("Dados insuficientes para treinar o modelo. São necessários pelo menos 2 registros.") 
            input("Pressione ENTER para continuar.")
            return
        
        if len(y.unique()) < 2: 
            print(f"A variável 'bomba' (target) tem apenas uma classe: {le_pump.inverse_transform(y.unique())}. Não é possível treinar um modelo de classificação.")
            print("Certifique-se de que seus dados históricos contêm registros com a bomba ligada e desligada.")
            input("Pressione ENTER para continuar.")
            return
        
        X_train, X_test, y_train, y_test = train_test_split(X_for_model, y, test_size=0.2, random_state=42)


        # 4. Treinar o modelo de ML
        model = RandomForestClassifier(n_estimators=100, random_state=42) 
        model.fit(X_train, y_train)

        # 5. Avaliar o modelo
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Acurácia do modelo no conjunto de teste: {accuracy:.2f}")

        print(f"\nRealizando predição com base nos dados do DataFrame em memória...")
        global last_100_mqtt_dataframe

        latest_sensor_data = None
        if not last_100_mqtt_dataframe.empty:
            latest_sensor_data = last_100_mqtt_dataframe.iloc[-1].to_dict()
            print(f"Usando a última leitura do DataFrame em memória para predição.")
        else:
            print(f"DataFrame MQTT em memória vazio. Nenhuma leitura recente coletada.")
            print("Por favor, colete os dados via MQTT primeiro (Opção 1).")
            input("Pressione ENTER para continuar.")
            return 
        
        if latest_sensor_data:
            try: 
                pred_time = latest_sensor_data.get('time', 0) 
                pred_humidity_value = latest_sensor_data.get('valor_umidade', 0)
                pred_humidity_level = latest_sensor_data.get('nivel_umidade', 'unknown').lower()
                pred_phosphorus =  latest_sensor_data.get('fosforo', 'unknown').lower()
                pred_potassium = latest_sensor_data.get('potassio', 'unknown').lower() 
                pred_ph_value = latest_sensor_data.get('valor_ph', 0.0) 
                pred_ph_level = latest_sensor_data.get('nivel_ph', 'unknown').lower() 
                pred_temperature = latest_sensor_data.get('temperatura', 0.0)

                try:
                    pred_humidity_level_encoded = le_humidity_level.transform([pred_humidity_level])[0]
                except ValueError:
                    print(f"AVISO: Valor '{pred_humidity_level}' da leitura não reconhecido para nível de umidade. Usando 0.")
                    pred_humidity_level_encoded = 0 
                
                try:
                    pred_phosphorus_encoded = le_phosphorus.transform([pred_phosphorus])[0]
                except ValueError:
                    print(f"AVISO: Valor '{pred_phosphorus}' da leitura não reconhecido para teor de fósforo. Usando 0.")
                    pred_phosphorus_encoded = 0 
                
                try:
                    pred_potassium_encoded = le_potassium_feature.transform([pred_potassium])[0] 
                except ValueError:
                    print(f"AVISO: Valor '{pred_potassium}' da leitura não reconhecido para teor de potássio. Usando 0.")
                    pred_potassium_encoded = 0

                try:
                    pred_ph_level_encoded = le_ph_level.transform([pred_ph_level])[0]
                except ValueError:
                    print(f"AVISO: Valor '{pred_ph_level}' da leitura não reconhecido para nível de pH. Use 'acid', 'alca' ou 'norm'. Usando 0.")
                    pred_ph_level_encoded = 0 
                
                new_data_for_prediction = pd.DataFrame([[
                    pred_time,
                    pred_humidity_value,
                    pred_humidity_level_encoded,
                    pred_phosphorus_encoded,
                    pred_potassium_encoded, 
                    pred_ph_value,
                    pred_ph_level_encoded,
                    pred_temperature
                ]], columns=features_for_model) 

                predicted_pump_status_encoded = model.predict(new_data_for_prediction)[0]
                predicted_pump_status = le_pump.inverse_transform([predicted_pump_status_encoded])[0]

                print(f"\nSugestão de Irrigação: A bomba deve ser '{predicted_pump_status.upper()}'.")
            except Exception as e:
                print(f"Erro ao processar dados para a predição: {e}.")
                traceback.print_exc() 
    except Exception as e:
            print(f"Ocorreu um erro inesperado durante a predição: {e}.")
            traceback.print_exc()

    input("Pressione ENTER para continuar.")

# =============== FUNÇÃO PARA CADASTRAS LEITURAS MQTT EM DATAFRAME ===============
def cadastrar_leitura_mqtt_em_dataframe(limit=100):
    os.system('cls')
    print(f"----- Coletar últimas {limit} Leituras MQTT para Análise (em memória) ------")
    global mqtt_message_buffer, add_to_mqtt_buffer, last_100_mqtt_dataframe

    mqtt_message_buffer.clear() # Limpa o buffer antes de iniciar uma nova coleta

    print("\nIniciando coleta de dados MQTT. Por favor, aguarde as mensagens chegarem.")
    print(f"Coletando até {limit} mensagens ou por até 105 segundos (aproximadamente).") 
    add_to_mqtt_buffer = True

    start_time = time.time()
    timeout = 105 
    while len(mqtt_message_buffer) < limit and (time.time() - start_time) < timeout:
        print(f"Aguardando mensagens MQTT... ({len(mqtt_message_buffer)} coletadas de {limit})  ", end='\r') 
        time.sleep(1)
    
    add_to_mqtt_buffer = False
    print("\nColeta de dados MQTT finalizada.                                        ") # Mais espaços para garantir que limpe a linha
    
    if not mqtt_message_buffer:
        print("Nenhuma leitura MQTT foi coletada. Verifique a conexão do sensor ou aumente o tempo de espera")
        last_100_mqtt_dataframe = pd.DataFrame() # Garante que o DataFrame esteja vazio
        input("Pressione ENTER para continuar.")
        return
    
    # Processa as mensagens coletadas para criar o DataFrame
    messages_to_process = list(mqtt_message_buffer)
    if len(messages_to_process) > limit:
        messages_to_process = messages_to_process[-limit:]

    print(f"Convertendo {len(messages_to_process)} Leituras para DataFrame...")

    # Lista para armazenar dicionários de cada linha para o DataFrame

    processed_data_list = []

    for i, message_data in enumerate(messages_to_process):
        try:
            processed_data = {
                'time': int(message_data.get('time', 0)),
                'temperatura': float(message_data.get('temperatura', 0.0)),
                'valor_umidade': float(message_data.get('valor_umidade', 0.0)),
                'nivel_umidade': message_data.get('nivel_umidade', 'unknown').lower(),
                'bomba': message_data.get('bomba', 'unknown').lower(),
                'fosforo': message_data.get('fosforo', 'unknown').lower(),
                'potassio': message_data.get('potassio', 'unknown').lower(),
                'valor_ph': float(message_data.get('valor_ph', 0.0)),
                'nivel_ph': message_data.get('nivel_ph', 'unknown').lower() 
            }
            processed_data_list.append(processed_data)
        except Exception as e:
            print(f"Erro ao processar leitura {i+1} para DataFrame: {e}. Esta leitura será ignorada")
            traceback.print_exc()

    if processed_data_list:
        last_100_mqtt_dataframe = pd.DataFrame(processed_data_list)
        print(f"\nDataFrame com {last_100_mqtt_dataframe.shape[0]} leituras MQTT criado em memória com sucesso!")
    else:
        last_100_mqtt_dataframe = pd.DataFrame()
        print("Nenhum dado válido para criar o Dataframe após o processamento.")

    mqtt_message_buffer.clear()

    input("Pressione ENTER para continuar.")

# =============================== FUNÇÃO ORIGINAL DE CADASTRO EM LOTE NO DB (AGORA OPCIONAL) ===============================
# Esta função foi separada para você poder decidir se quer manter ou remover.
# Você pode renomear ela, ou criar uma nova opção no menu para "Salvar dados do DataFrame no DB"

def salvar_dataframe_no_banco_de_dados():
    os.system('cls')
    print("----- Salvar Leituras do DataFrame em Memória no Banco de Dados -----")
    global last_100_mqtt_dataframe

    if last_100_mqtt_dataframe.empty:
        print("O DataFrame de leituras MQTT em memória está vazio. Colete os dados primeiro (Opção 1).")
        input("Pressione ENTER para continuar")
        return
    
    sql_columns_order = [
        'time', 'temperatura', 'valor_umidade', 'nivel_umidade', 'bomba',
        'fosforo', 'potassio', 'valor_ph', 'nivel_ph'
    ]

    # Prepara os dados do DataFrame para a inserção em lote no Oracle
    data_for_executemany = []
    
    for index, row in last_100_mqtt_dataframe.iterrows():
        try:
            computer_id = 7
            values = (
                computer_id,
                int(row['time']),
                float(row['valor_umidade']),
                str(row['nivel_umidade']).lower(),
                str(row['bomba']).lower(),
                str(row['fosforo']).lower(),
                str(row['potassio']).lower(), 
                float(row['valor_ph']),
                str(row['nivel_ph']).lower(),
                float(row['temperatura'])
            )
            data_for_executemany.append(values)
        except Exception as e:
            print(f"Erro ao preparar linha {index} do DataFrame para o DB: {e}. Linha ignorada.")
            traceback.print_exc()

    if data_for_executemany:
        sql_insert = """
        INSERT INTO T_READINGS (
            reading_id,
            computer_id,
            reading_time,
            reading_humidity_value,
            reading_humidity_level,
            reading_pump,
            reading_phosphorus,
            reading_potassium,
            reading_ph_value,
            reading_ph_level,
            reading_temperature
        ) VALUES (seq_readings.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
        """
        try:
            inst_cadastro.executemany(sql_insert, data_for_executemany)
            conn.commit()
            total_inserted = len(data_for_executemany)
            print(f"\nTotal de {total_inserted} leituras do DataFrame cadastradas no banco de dados com sucesso!")
        except Exception as e:
            conn.rollback()
            print(f"\nErro fatal ao cadastrar leituras no banco de dados: {e}. Todas as inserções desta operação foram desfeitas.")
            traceback.print_exc()
    else:
        print("Nenhum dado válido para inserção no banco de dados após o processamento do DataFrame.")

    input("Pressione ENTER para continuar.")
        
# Executa a aplicação se e enquanto houver conexão com o banco de dados.
while conexao:
    os.system('cls')    

    # Exibe menu.
    print("---- Gerenciamento de dados de campo ----")
    print("""
    1 - Coletar últimas leituras MQTT para análise (em memória)
    2 - Adicionar leitura (manual)
    3 - Listar leituras (do DB)
    4 - Alterar leituras (no DB)
    5 - Excluir leituras (no DB)
    6 - Limpar base de leituras (no DB)
    7 - Predição de irrigação (usando DataFrame em memória)
    8 - Monitorar leituras MQTT (ao vivo)     
    9 - Sair
    10 - Salvar leituras do DataFrame em memória no Banco de Dados
    """)

    escolha_str = input(margem + "Escolha -> ")   

    if not escolha_str.isdigit():
        print("Entrada inválida. Por favor, digite um número de 1 a 10.") 
        input("Pressione ENTER para continuar.") 
        continue

    escolha = int(escolha_str)

    match escolha:

        # Cadastra leituras em lote.
        case 1:
            cadastrar_leitura_mqtt_em_dataframe(limit=100)


        # Adiciona um registro à tabela de leituras
        case 2:
            os.system('cls')    

            try:
                sql_add = """
                INSERT INTO T_READINGS (
                    reading_id,
                    computer_id,
                    reading_time,
                    reading_humidity_value,
                    reading_humidity_level,
                    reading_pump,
                    reading_phosphorus,
                    reading_potassium,
                    reading_ph_value,
                    reading_ph_level,
                    reading_temperature
                ) VALUES (seq_readings.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
                """
                print("\nInforme os valores solicitados.")
                print("\nOs obrigatórios estão assinalados com *.")

                computer_id = int(input("Código do computador de borda (numérico)*: "))
                reading_time = int(input("Horário da leitura (numérico)*: "))
                reading_humidity_value = float(input("Umidade do solo (numérico)*: "))
                reading_humidity_level = input("Nível de umidade (baixo ou OK)*: ")
                reading_pump = input("Status da bomba (ligada ou desligada)*: ")
                reading_phosphorus = input("Teor de fósforo no solo (alto ou baixo)*: ")
                reading_potassium = input("Teor de potássio no solo (OK/Baixo)*: ") # Alterado para ser claro que é string
                reading_ph_value = float(input("Valor do pH do solo (numérico)*: "))
                reading_ph_level = input("Nível do pH do solo (acid/alca/norm)*: ") 
                reading_temperature = float(input("Temperatura (numérico, duas casas decimais)*: "))

                add_values = (
                    computer_id,
                    reading_time,
                    reading_humidity_value,
                    reading_humidity_level,
                    reading_pump,
                    reading_phosphorus,
                    reading_potassium,
                    reading_ph_value,
                    reading_ph_level,
                    reading_temperature
                )

                inst_cadastro.execute(sql_add, add_values)
                conn.commit()
                print("Registro inserido com sucesso!")

            except ValueError as ve:
                print(f"Erro de entrada: {ve}. Certifique-se de inserir os valores nos formatos corretos.")
            except Exception as e:
                conn.rollback()  # Desfaz qualquer alteração feita na transação
                print(f"Erro ao inserir registro: {e}")
            input("Pressione ENTER")


        # Lista leituras cadastradas no banco de dados
        case 3:
            os.system('cls')    

            try:
                print("-----   Listar leituras   -----")

                inst_consulta.execute('SELECT * FROM T_READINGS')
                data = inst_consulta.fetchall()

                colunas = [desc[0] for desc in inst_consulta.description]

                dados_df = pd.DataFrame(data, columns=colunas)

                if not dados_df.empty:
                    print(dados_df)
                else:
                    print("Nenhum registro encontrado na tabela de leituras.")

            except Exception as e:
                print(f"Erro ao buscar dados: {e}")

            print('Fim da lista')
            input('Pressione ENTER para continuar.')


        # Altera leituras cadastradas no banco de dados, a partir do ID.
        case 4:
            os.system('cls')

            try:
                print("-----   Alterar leituras por ID   -----")

                id_to_edit = input("Digite o código (id numérico) do registro que você deseja editar: ")

                if not id_to_edit.isdigit():
                    raise ValueError("O ID deve ser um número inteiro.")
                
                fields_to_edit = {}

                print("\nEdite os valores que desejar. Deixe em branco para pular.")

                reading_humidity_value = input("Umidade do solo (numérico): ")
                if reading_humidity_value:
                    fields_to_edit['reading_humidity_value'] = float(reading_humidity_value)

                reading_humidity_level = input("Nível de umidade (baixo ou OK): ")
                if reading_humidity_level:
                    fields_to_edit['reading_humidity_level'] = reading_humidity_level

                reading_pump = input("Status da bomba (ligada ou desligada): ")
                if reading_pump:
                    fields_to_edit['reading_pump'] = reading_pump

                reading_phosphorus = input("Teor de fósforo no solo (alto ou baixo): ")
                if reading_phosphorus:
                    fields_to_edit['reading_phosphorus'] = reading_phosphorus

                reading_potassium = input("Teor de potássio no solo (OK/Baixo): ") 
                if reading_potassium:
                    fields_to_edit['reading_potassium'] = reading_potassium

                reading_ph_value = input("Valor do pH do solo (numérico): ")
                if reading_ph_value:
                    fields_to_edit['reading_ph_value'] = float(reading_ph_value)

                reading_ph_level = input("Nível do pH do solo (acid/alca/norm): ") 
                if reading_ph_level:
                    fields_to_edit['reading_ph_level'] = reading_ph_level

                reading_temperature = input("Temperatura (numérico, duas casas decimais): ")
                if reading_temperature:
                    fields_to_edit['reading_temperature'] = float(reading_temperature)

                if not fields_to_edit:
                    print("Nenhuma alteração solicitada.")
                
                else:
                    updates = []
                    params = {}
                    for field, value in fields_to_edit.items():
                        updates.append(f"{field} = :{field}")
                        params[field] = value

                    sql_update = f"""
                        UPDATE T_READINGS
                        SET {', '.join(updates)}
                        WHERE reading_id = :id
                    """

                    params['id'] = int(id_to_edit)

                    inst_alteracao.execute(sql_update, params)
                    conn.commit()
                    print("Registro alterado com sucesso.")

            except ValueError as ve:
                print(f"Erro de entrada: {ve}. Certifique-se de inserir os valores nos formatos corretos.")
            except Exception as e:
                conn.rollback()  
                print(f"Erro ao alterar registro: {e}")
            input("Pressione ENTER.")


        # Remove leituras cadastradas no banco de dados, a partir do ID.
        case 5:
            os.system('cls')

            try:
                print("-----   Remover leituras por ID   -----")

                id_to_delete = input("Digite o código (id numérico) do registro que você deseja remover: ")

                if not id_to_delete.isdigit():
                    raise ValueError("O código deve ser um número inteiro.")
                
                else:
                    flag_confirm = input(f'Confirme que deseja remover o registro de id={id_to_delete}, S/N: ')

                    if flag_confirm.upper() == 'S': 
                        sql_delete = "DELETE FROM T_READINGS WHERE reading_id = :id"
                        inst_exclusao.execute(sql_delete, {'id': id_to_delete})
                        conn.commit()
                        print("Registro removido com sucesso.")
                    else:
                        print("Operação de remoção cancelada.")

            except ValueError as ve:
                print(f"Erro de entrada: {ve}.")
            except Exception as e:
                conn.rollback()  
                print(f"Erro ao remover registro: {e}")
            input("Pressione ENTER.")


        # Remove todos os dados de leituras da base de dados.
        case 6:
            os.system('cls')

            try:
                print("-----   Remover da base todas as leituras   -----")

                flag_confirm_all = input(f'Confirme que deseja remover todas as leituras, S/N: ')

                if flag_confirm_all.upper() == 'S':
                    sql_delete_all = "DELETE FROM T_READINGS"
                    inst_exclusao.execute(sql_delete_all)
                    conn.commit()
                    print("Todas as leituras removidas com sucesso.")
                else:
                    print("Operação de remoção de todas as leituras canceladas.")

            except Exception as e:
                conn.rollback()  
                print(f"Erro ao remover registro: {e}")
            input("Pressione ENTER.")


        # Fecha a conexão com o banco de dados e termina o programa.
        case 7:
            prever_irrigacao(inst_consulta, conn, data_file)


        case 8:
            os.system('cls')

            print("----- Monitoramento de leituras MQTT (ao vivo) -----")
            print("Aguardando mensagem do sensor... Pressione CTRL+C para voltar ao menu")
            print("--------------------------------------------------\n")
            # A variável 'add_to_mqtt_buffer' já é global e foi inicializada no topo do script.
            # Não é necessário 'global' aqui novamente se você apenas a acessa, não a reatribui.
            # No entanto, se ela for reatribuída aqui (como add_to_mqtt_buffer = False),
            # 'global' seria necessário. Como ela já está no topo do script e é acessada no on_message,
            # o erro 'UnboundLocalError' aqui é atípico. A solução mais robusta é declará-la global aqui
            # para garantir, caso o Python interprete de outra forma.
            global add_to_mqtt_buffer 
            add_to_mqtt_buffer = False 

            try:
                print("As mensagens MQTT estão sendo recebidas em segundo plano. Para ver os detalhes, selecione 'Coletar últimas leituras MQTT' (Opção 1).")
                print("Pressione CTRL+C a qualquer momento para voltar ao menu.")
                while True:
                    time.sleep(5) 
            except KeyboardInterrupt:
                print("\nMonitoramento encerrado.")
            except Exception as e:
                print(f"Ocorreu um erro durante o monitoramento: {e}")
            input("Pressione ENTER para continuar.")
        
        case 9:
            print("Encerrando o programa...")
            try:
                inst_cadastro.close()
                inst_consulta.close()
                inst_alteracao.close()
                inst_exclusao.close()
                conn.close()
                print("Conexão com o banco de dados encerrada com sucesso.")
            except Exception as e:
                print(f"Erro ao fechar a conexão: {e}")
            finally:
                conexao = False

                if client:
                    client.loop_stop()
                    client.disconnect()
                    print(f"Cliente MQTT desconectado.")


        case 10:
            salvar_dataframe_no_banco_de_dados()


        case _:
            print("Opção inválida. Por favor, escolha uma opção válida do menu.")
            input("Pressione ENTER para continuar.")