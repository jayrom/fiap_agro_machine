#---------------------------------------------------
# TiãoTech Agro Machine
# Por favor, leia o README.md para mais informações.
#---------------------------------------------------

# Importa módulos.
import os
import oracledb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
import paho.mqtt.client as mqtt
import json
import time
from collections import deque
import traceback
import sys

# Configura pandas para imprimir dataframe completo
# pd.set_option('display.max_rows', None)

# Caminho para o arquivo CSV de dados de leitura de sensores (para operações de CRUD no DB)
data_file_computer_7 = r'c:\Users\luarc\OneDrive\Área de Trabalho\fiap_agro_machine\sprint_1\input\computer_7.csv'

# Caminho completo para o arquivo CSV de dados climáticos (para predição de irrigação)
weather_data_file = r'C:\Users\luarc\OneDrive\Área de Trabalho\fiap_agro_machine\sprint_2\input\weather_data.csv'

# Variáveis globais para o DataFrame de clima e LabelEncoder (para predição ML)
df_clima_global = pd.DataFrame()
le_sugestao_irrigacao = LabelEncoder()

# Definindo os limiares como variáveis globais para a lógica da predição de irrigação
limiar_ura_baixa = 60.0
limiar_chuva_recente = 1.0 # mm de chuva para considerar que "choveu" e não precisa irrigar
limiar_umidade_solo_ok = 50.0 # Exemplo: Limiar para considerar umidade do solo "OK" (ajuste conforme sensor)

# NOVO: Número de últimas leituras a considerar para o histórico (para Clima e MQTT)
N_LEITURAS_HISTORICO = 6 

# --- MQTT CONFIGURAÇÕES E VARIÁVEIS GLOBAIS ---
mqtt_broker_py = "broker.hivemq.com"
mqtt_port_py = 1883
mqtt_topic_subscribe = "fe/field-3/plot-1/computer-7/data"
mqtt_client_id_py = "python-subscriber-agro-machine"

# Maxlen ajustado para N_LEITURAS_HISTORICO
mqtt_message_buffer = deque(maxlen=N_LEITURAS_HISTORICO)
add_to_mqtt_buffer = False
mqtt_print_live_messages = False
last_100_mqtt_dataframe = pd.DataFrame() 

# Conecta banco de dados.
conn = None
try:
    db_user = 'RM565576'
    db_pass = 'Fiap#2025'
    conn = oracledb.connect(user=db_user, password=db_pass, dsn='oracle.fiap.com.br:1521/ORCL')
    inst_cadastro = conn.cursor()
    inst_consulta = conn.cursor()
    inst_alteracao = conn.cursor()
    inst_exclusao = conn.cursor()
    conexao_db_ativa = True
    print("Conexão com o banco de dados Oracle estabelecida com sucesso.")

except Exception as e: 
    print(f"Erro ao conectar ao banco de dados: {e}")
    conexao_db_ativa = False
    print("Funcionalidades que dependem do banco de dados não estarão disponíveis.")

margem = ' ' * 4


# --- FUNÇÕES MQTT ---

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao broker MQTT com sucesso!")
        client.subscribe(mqtt_topic_subscribe)
        print(f"Inscrito no tópico: {mqtt_topic_subscribe}")
    else:
        print(f"Falha na conexão MQTT, código de retorno: {rc}")

def on_message(client, userdata, msg):
    global mqtt_message_buffer, add_to_mqtt_buffer, mqtt_print_live_messages
    try:
        payload_str = msg.payload.decode('utf-8')
        json_data = json.loads(payload_str)

        if add_to_mqtt_buffer:
            mqtt_message_buffer.append(json_data)
            print(f"\n[Coleta Ativa] Mensagem MQTT recebida no tópico {msg.topic}:")
            print(f"Conteúdo: {payload_str}")
            print("Mensagem adicionada ao buffer para cadastro em lote.")
        elif mqtt_print_live_messages:
            print(f"\nMensagem MQTT ao vivo no tópico {msg.topic}:")
            print(f"Conteúdo: {payload_str}")
            print(f"Dados do sensor:")
            for key, value in json_data.items():
                print(f"  {key}: {value}")

    except json.JSONDecodeError:
        print("Payload não é um JSON válido.")
        print(f"Conteúdo bruto: {msg.payload.decode('utf-8')}")
    except Exception as e:
        print(f"Erro ao processar a mensagem MQTT: {e}")

# Cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, mqtt_client_id_py)
client.on_connect = on_connect
client.on_message = on_message

# Tenta conectar ao broker MQTT ao iniciar o programa
try:
    client.connect(mqtt_broker_py, mqtt_port_py, 60)
    client.loop_start() # Inicia uma thread em background para processar mensagens
    print("Iniciando cliente MQTT em background.")
except Exception as e:
    print(f"Erro ao conectar ao broker MQTT: {e}")


# =============== FUNÇÃO PARA COLETAR LEITURAS MQTT EM DATAFRAME ===============
def coletar_leituras_mqtt_em_dataframe(limit=N_LEITURAS_HISTORICO): # Limitando a coleta ao N_LEITURAS_HISTORICO
    os.system('cls')
    print(f"----- Coletar últimas {limit} Leituras MQTT para Análise (em memória) ------")
    global mqtt_message_buffer, add_to_mqtt_buffer, last_100_mqtt_dataframe, mqtt_print_live_messages

    mqtt_message_buffer.clear() 

    print("\nIniciando coleta de dados MQTT. Por favor, aguarde as mensagens chegarem.")
    print(f"Coletando até {limit} mensagens ou até 200 segundos.")
    add_to_mqtt_buffer = True 
    mqtt_print_live_messages = False 

    start_time = time.time()
    timeout = 200
    while len(mqtt_message_buffer) < limit and (time.time() - start_time) < timeout:
        print (f"Aguardando mensagem MQTT... ({len(mqtt_message_buffer)} coletadas de {limit}) ", end='\r')
        time.sleep(1)
    
    add_to_mqtt_buffer = False
    print("\nColeta de dados MQTT finalizada.")

    if not mqtt_message_buffer:
        print("Nenhuma leitura MQTT foi coletada. Verifique a conexão do sensor ou aumente o tempo de espera.")
        last_100_mqtt_dataframe = pd.DataFrame()
        input("Pressione ENTER para continuar.")
        return
    
    messages_to_process = list(mqtt_message_buffer)
    # Com maxlen definido para N_LEITURAS_HISTORICO, esta linha é redundante
    # pois o deque já limita. Mas mantida por segurança.
    if len(messages_to_process) > limit: 
        messages_to_process = messages_to_process[-limit:]

    print(f"Convertendo {len(messages_to_process)} Leituras para DataFrame...")

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
                'potassio': str(message_data.get('potassio', 'unknown')).lower(),
                'valor_ph': float(message_data.get('valor_ph', 0.0)),
                'nivel_ph': message_data.get('nivel_ph', 'unknown').lower()
            }
            processed_data_list.append(processed_data)
        except Exception as e:
            print(f"Erro ao processar leitura {i+1} para DataFrame: {e}. Esta leitura será ignorada.")
            traceback.print_exc()

    if processed_data_list:
        last_100_mqtt_dataframe = pd.DataFrame(processed_data_list)
        print(f"\nDataFrame com {last_100_mqtt_dataframe.shape[0]} leituras MQTT criado em memória com sucesso!")
    else:
        last_100_mqtt_dataframe = pd.DataFrame()
        print("Nenhum dado válido para criar o Dataframe após o processamento.")

    mqtt_message_buffer.clear()

    input("Pressione ENTER para continuar.")

# =============== FUNÇÃO PARA SALVAR DATAFRAME MQTT NO DB ===============
def salvar_dataframe_no_banco_de_dados():
    os.system('cls')
    print("----- Salvar Leituras do DataFrame em Memória no Banco de Dados -----")
    global last_100_mqtt_dataframe

    if not conexao_db_ativa:
        print("Operação não disponível: Conexão com o banco de dados não estabelecida.")
        input("Pressione ENTER")
        return

    if last_100_mqtt_dataframe.empty:
        print(f"O DataFrame de leituras MQTT em memória está vazio. Colete {N_LEITURAS_HISTORICO} dados primeiro (Opção 8).")
        input("Pressione ENTER para continuar")
        return
    
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

# =============== FUNÇÃO PARA MONITORAR LEITURAS MQTT AO VIVO ===============
def monitorar_leituras_mqtt_ao_vivo():
    os.system('cls')
    global add_to_mqtt_buffer, mqtt_print_live_messages
    
    add_to_mqtt_buffer = False 
    mqtt_print_live_messages = True 

    print("----- Monitoramento de leituras MQTT (ao vivo) -----")
    print("Aguardando mensagem do sensor... Pressione CTRL+C para voltar ao menu")
    print("--------------------------------------------------\n")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado.")
    except Exception as e:
        print(f"Ocorreu um erro durante o monitoramento: {e}")
    finally:
        mqtt_print_live_messages = False 
    input("Pressione ENTER para continuar.")


# --- FUNÇÕES DE GERENCIAMENTO DE DADOS (DB) ---

def adicionar_leitura_manual():
    if not conexao_db_ativa:
        print("Operação não disponível: Conexão com o banco de dados não estabelecida.")
        input("Pressione ENTER")
        return

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
        reading_humidity_value = int(input("Umidade do solo (numérico)*: "))
        reading_humidity_level = input("Nível de umidade (baixo ou OK)*: ").lower()
        reading_pump = input("Status da bomba (ligada ou desligada)*: ").lower()
        reading_phosphorus = input("Teor de fósforo no solo (alto ou baixo)*: ").lower()
        reading_potassium = str(float(input("Teor de potássio no solo (numérico): "))).lower()
        reading_ph_value = int(input("Valor do pH do solo (numérico): "))
        reading_ph_level = input("Nível do pH do solo (acid, alca ou norm): ").lower()
        reading_temperature = float(input("Temperatura (numérico, duas casas decimais): "))

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
        if conn: conn.rollback()
        print(f"Erro ao inserir registro: {e}")
    input("Pressione ENTER")

def listar_leituras():
    if not conexao_db_ativa:
        print("Operação não disponível: Conexão com o banco de dados não estabelecida.")
        input("Pressione ENTER")
        return

    os.system('cls') 
    try:
        print("-----    Listar leituras    -----")

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

def alterar_leituras():
    if not conexao_db_ativa:
        print("Operação não disponível: Conexão com o banco de dados não estabelecida.")
        input("Pressione ENTER")
        return

    os.system('cls')
    try:
        print("-----    Alterar leituras por ID    -----")

        id_to_edit = input("Digite o código (id numérico) do registro que você deseja editar: ")

        if not id_to_edit.isdigit():
            raise ValueError("O ID deve ser um número inteiro.")
        
        fields_to_edit = {}

        print("\nEdite os valores que desejar. Deixe em branco para pular.")

        reading_humidity_value = input("Umidade do solo (numérico): ")
        if reading_humidity_value:
            fields_to_edit['reading_humidity_value'] = int(reading_humidity_value)

        reading_humidity_level = input("Nível de umidade (baixo ou OK): ")
        if reading_humidity_level:
            fields_to_edit['reading_humidity_level'] = reading_humidity_level.lower()

        reading_pump = input("Status da bomba (ligada ou desligada): ")
        if reading_pump:
            fields_to_edit['reading_pump'] = reading_pump.lower()

        reading_phosphorus = input("Teor de fósforo no solo (alto ou baixo): ")
        if reading_phosphorus:
            fields_to_edit['reading_phosphorus'] = reading_phosphorus.lower()

        reading_potassium = input("Teor de potássio no solo (numérico): ")
        if reading_potassium:
            fields_to_edit['reading_potassium'] = str(float(reading_potassium)).lower()

        reading_ph_value = input("Valor do pH do solo (numérico): ")
        if reading_ph_value:
            fields_to_edit['reading_ph_value'] = int(reading_ph_value)

        reading_ph_level = input("Nível do pH do solo (acid, alca ou norm): ")
        if reading_ph_level:
            fields_to_edit['reading_ph_level'] = reading_ph_level.lower()

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
        if conn: conn.rollback()
        print(f"Erro ao alterar registro: {e}")
    input("Pressione ENTER.")

def excluir_leituras():
    if not conexao_db_ativa:
        print("Operação não disponível: Conexão com o banco de dados não estabelecida.")
        input("Pressione ENTER")
        return

    os.system('cls')
    try:
        print("-----    Remover leituras por ID    -----")

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
        if conn: conn.rollback()
        print(f"Erro ao remover registro: {e}")
    input("Pressione ENTER.")

def limpar_base_leituras():
    if not conexao_db_ativa:
        print("Operação não disponível: Conexão com o banco de dados não estabelecida.")
        input("Pressione ENTER")
        return

    os.system('cls')
    try:
        print("-----    Remover da base todas as leituras    -----")

        flag_confirm_all = input(f'Confirme que deseja remover todas as leituras, S/N: ')

        if flag_confirm_all.upper() == 'S':
            sql_delete_all = "DELETE FROM T_READINGS"
            inst_exclusao.execute(sql_delete_all)
            conn.commit()
            print("Todas as leituras removidas com sucesso.")
        else:
            print("Operação de remoção de todas as leituras cancelada.")

    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao remover registro: {e}")
    input("Pressione ENTER.")

# --- FUNÇÕES DE PREDIÇÃO (ML) ---

# Função para carregar e pré-processar o CSV de clima
def carregar_e_processar_dados_climaticos():
    global df_clima_global, le_sugestao_irrigacao

    os.system('cls')
    print("----- Carregando e Processando Dados Climáticos -----")

    try:
        df_clima = pd.read_csv(
            weather_data_file,
            sep=',', # Usando vírgula como delimitador
            header=0 # A primeira linha é o cabeçalho
        )
        print(f"Dados climáticos carregados do CSV: {df_clima.shape[0]} registros.")
        
        # Renomear as colunas para nomes mais fáceis de usar no código.
        df_clima.columns = ['Time', 'Temp_Max_C', 'URA_Perc', 'Chuva_mm']

        # Converter 'Time' para datetime. O formato agora é "%d/%m/%Y %H:%M" (sem segundos)
        df_clima['Time'] = pd.to_datetime(df_clima['Time'], format='%d/%m/%Y %H:%M', errors='coerce')
        
        # Extrair features de data/hora
        df_clima['Hora_do_Dia'] = df_clima['Time'].dt.hour
        df_clima['Dia_do_Ano'] = df_clima['Time'].dt.dayofyear

        # Converter tipos numéricos
        df_clima['Temp_Max_C'] = pd.to_numeric(df_clima['Temp_Max_C'], errors='coerce')
        df_clima['URA_Perc'] = pd.to_numeric(df_clima['URA_Perc'], errors='coerce')
        df_clima['Chuva_mm'] = pd.to_numeric(df_clima['Chuva_mm'], errors='coerce')

        # Remover linhas com valores NaN (resultantes de erros de conversão ou dados faltantes)
        df_clima.dropna(inplace=True)

        if df_clima.empty:
            print("Após o pré-processamento e remoção de valores inválidos, não restaram dados climáticos válidos.")
            df_clima_global = pd.DataFrame()
            input("Pressione ENTER para continuar.")
            return

        # Criação da variável target 'Necessidade_Irrigacao' baseada em heurísticas
        df_clima['Necessidade_Irrigacao'] = 'nao'
        df_clima.loc[(df_clima['URA_Perc'] < limiar_ura_baixa) & 
                     (df_clima['Chuva_mm'] < limiar_chuva_recente), 
                     'Necessidade_Irrigacao'] = 'sim'
        df_clima.loc[df_clima['URA_Perc'] > 85.0, 'Necessidade_Irrigacao'] = 'nao'

        # Treinar o LabelEncoder com todas as classes possíveis para a variável target
        all_possible_targets = df_clima['Necessidade_Irrigacao'].unique().tolist()
        if 'sim' not in all_possible_targets: all_possible_targets.append('sim')
        if 'nao' not in all_possible_targets: all_possible_targets.append('nao')
        le_sugestao_irrigacao.fit(all_possible_targets)

        # Armazenar o DataFrame processado globalmente
        df_clima_global = df_clima.copy()
        print("\nDados climáticos processados e prontos para a predição!")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{weather_data_file}' não foi encontrado. Por favor, verifique o caminho.")
        df_clima_global = pd.DataFrame()
    except Exception as e:
        print(f"Ocorreu um erro ao carregar/processar os dados climáticos: {e}")
        traceback.print_exc()
        df_clima_global = pd.DataFrame()
    
    input("Pressione ENTER para continuar.")


# FUNÇÃO RENOMEADA: Agora faz predição combinada (Clima ML + Sensor regras)
def prever_irrigacao_combinada_ml():
    global df_clima_global, le_sugestao_irrigacao, last_100_mqtt_dataframe

    os.system('cls')
    print("----- Predição de Necessidade de Irrigação (Clima ML + Dados Sensor) -----")

    if df_clima_global.empty:
        print("Nenhum dado climático carregado. Por favor, carregue os dados na Opção 1 primeiro.")
        input("Pressione ENTER para continuar.")
        return
    
    if last_100_mqtt_dataframe.empty:
        print(f"Nenhum dado recente do sensor MQTT disponível. Por favor, colete {N_LEITURAS_HISTORICO} dados na Opção 7 primeiro.")
        input("Pressione ENTER para continuar.")
        return
    
    # Verificar se há leituras suficientes no DataFrame MQTT para o histórico
    if len(last_100_mqtt_dataframe) < N_LEITURAS_HISTORICO:
        print(f"Dados insuficientes do sensor MQTT para análise de histórico. São necessárias pelo menos {N_LEITURAS_HISTORICO} leituras.")
        print(f"Atualmente há {len(last_100_mqtt_dataframe)} leituras coletadas. Colete mais mensagens na Opção 7.")
        input("Pressione ENTER para continuar.")
        return

    try:
        # --- 1. Predição baseada em dados climáticos (como antes) ---
        features_clima = ['Temp_Max_C', 'URA_Perc', 'Chuva_mm', 'Hora_do_Dia', 'Dia_do_Ano']
        target_clima = 'Necessidade_Irrigacao'

        # Garante que o df_clima_global tem dados suficientes para o split
        if df_clima_global.shape[0] < 2:
            print("Dados climáticos insuficientes para treinar o modelo. Necessário no mínimo 2 registros.")
            input("Pressione ENTER para continuar.")
            return

        X_clima = df_clima_global[features_clima]
        y_clima = df_clima_global[target_clima]
        y_clima_encoded = le_sugestao_irrigacao.transform(y_clima)

        if len(np.unique(y_clima_encoded)) < 2:
            print(f"A variável 'Necessidade_Irrigacao' tem apenas uma classe. Não é possível treinar o modelo de clima.")
            print("Verifique a lógica de criação da target ou os dados climáticos.")
            input("Pressione ENTER para continuar.")
            return

        X_train_clima, X_test_clima, y_train_clima, y_test_clima = train_test_split(
            X_clima, y_clima_encoded, test_size=0.2, random_state=42, stratify=y_clima_encoded
        )

        model_clima = DecisionTreeClassifier(random_state=42)
        model_clima.fit(X_train_clima, y_train_clima)

        # --- ANÁLISE DAS ÚLTIMAS N LEITURAS DO CSV DE CLIMA PARA A DECISÃO ---
        # Se houver menos leituras do que o histórico desejado, pegue todas que tiver.
        num_clima_leituras_para_historico = min(N_LEITURAS_HISTORICO, len(df_clima_global))
        recent_clima_data_df = df_clima_global.iloc[-num_clima_leituras_para_historico:]

        # Calcular a média da temperatura e URA nas últimas N leituras climáticas
        mean_temp_clima_hist = recent_clima_data_df['Temp_Max_C'].mean()
        mean_ura_clima_hist = recent_clima_data_df['URA_Perc'].mean()
        sum_chuva_clima_hist = recent_clima_data_df['Chuva_mm'].sum() # Total de chuva no período

        # Tendência de temperatura e URA do clima (última vs. primeira das N leituras)
        clima_temp_tendencia = "estável"
        if len(recent_clima_data_df) > 1:
            first_temp_clima = recent_clima_data_df['Temp_Max_C'].iloc[0]
            last_temp_clima = recent_clima_data_df['Temp_Max_C'].iloc[-1]
            if last_temp_clima > first_temp_clima:
                clima_temp_tendencia = "aumentando"
            elif last_temp_clima < first_temp_clima:
                clima_temp_tendencia = "diminuindo"
        
        clima_ura_tendencia = "estável"
        if len(recent_clima_data_df) > 1:
            first_ura_clima = recent_clima_data_df['URA_Perc'].iloc[0]
            last_ura_clima = recent_clima_data_df['URA_Perc'].iloc[-1]
            if last_ura_clima > first_ura_clima:
                clima_ura_tendencia = "aumentando"
            elif last_ura_clima < first_ura_clima:
                clima_ura_tendencia = "diminuindo"

        # A predição do modelo de ML ainda é baseada na última leitura para manter a "instantaneidade" do ML
        latest_clima_data = df_clima_global.iloc[-1]
        new_data_for_clima_prediction = pd.DataFrame([latest_clima_data[features_clima].values], columns=features_clima)
        predicted_necessidade_clima_encoded = model_clima.predict(new_data_for_clima_prediction)[0]
        predicted_necessidade_clima = le_sugestao_irrigacao.inverse_transform([predicted_necessidade_clima_encoded])[0]

        print(f"\nPredição (Baseada Apenas no Clima Mais Recente): {predicted_necessidade_clima.upper()}")
        print(f"Dados climáticos utilizados (última leitura): {new_data_for_clima_prediction.iloc[0].to_dict()}")
        print(f"Histórico Climático (últimas {num_clima_leituras_para_historico} leituras):")
        print(f"- Média da Temperatura: {mean_temp_clima_hist:.2f}C (Tendência: {clima_temp_tendencia})")
        print(f"- Média da URA: {mean_ura_clima_hist:.2f}% (Tendência: {clima_ura_tendencia})")
        print(f"- Chuva Total no Período: {sum_chuva_clima_hist:.2f}mm")

        # --- 2. Incorporar dados do sensor MQTT: Análise das últimas N leituras ---
        # Garantido que len(last_100_mqtt_dataframe) >= N_LEITURAS_HISTORICO pelo check inicial
        recent_sensor_data_df = last_100_mqtt_dataframe.iloc[-N_LEITURAS_HISTORICO:]
        
        mean_valor_umidade_solo = recent_sensor_data_df['valor_umidade'].mean()
        mode_nivel_umidade_solo = recent_sensor_data_df['nivel_umidade'].mode()[0]

        first_umidade = recent_sensor_data_df['valor_umidade'].iloc[0]
        last_umidade = recent_sensor_data_df['valor_umidade'].iloc[-1]
        umidade_tendencia_solo = "estável" # Renomeado para evitar conflito com 'umidade_tendencia' do clima
        if last_umidade > first_umidade:
            umidade_tendencia_solo = "aumentando"
        elif last_umidade < first_umidade:
            umidade_tendencia_solo = "diminuindo"

        print(f"\nDados recentes do sensor de solo (MQTT - últimas {N_LEITURAS_HISTORICO} leituras):")
        print(f"- Média da Umidade do Solo: {mean_valor_umidade_solo:.2f}")
        print(f"- Nível de Umidade Mais Frequente: {mode_nivel_umidade_solo.upper()}")
        print(f"- Tendência da Umidade do Solo: {umidade_tendencia_solo.upper()}")
        
        # --- 3. Lógica de Decisão Combinada (ML + Regras de Sensor e Clima Histórico) ---
        final_necessidade_irrigacao = predicted_necessidade_clima
        sugestao_final_msg = ""

        # Regra 1: Se o clima sugere irrigar, mas o solo (média/tendência) está OK, talvez não precise
        if predicted_necessidade_clima == 'sim':
            if (mode_nivel_umidade_solo == 'ok' or mean_valor_umidade_solo >= limiar_umidade_solo_ok) and umidade_tendencia_solo != 'diminuindo':
                final_necessidade_irrigacao = 'nao'
                sugestao_final_msg = "SOBRESCRITA: O clima sugere irrigar, mas a umidade do solo (sensor) está OK e/ou estável/aumentando."
                # Adiciona condição para não sobrescrever se o clima também está secando muito rápido
                if clima_ura_tendencia == 'diminuindo' and clima_temp_tendencia == 'aumentando':
                    final_necessidade_irrigacao = 'sim' # Reverte a sobrescrita se o clima está piorando rapidamente
                    sugestao_final_msg = "AVISO: Clima indica piora rápida, reverter sugestão: Necessita irrigação."

            elif (mode_nivel_umidade_solo == 'baixa' or mean_valor_umidade_solo < limiar_umidade_solo_ok) or umidade_tendencia_solo == 'diminuindo':
                 sugestao_final_msg = "CONFIRMADA: O clima e a umidade do solo (sensor) indicam necessidade de irrigação."
            else:
                sugestao_final_msg = "AVALIAR: Clima sugere irrigação, mas umidade do solo está no limite ou incerta."
        
        # Regra 2: Se o clima NÃO sugere irrigar, mas o solo (média/tendência) está baixo, PRECISA irrigar
        elif predicted_necessidade_clima == 'nao':
            if (mode_nivel_umidade_solo == 'baixa' or mean_valor_umidade_solo < limiar_umidade_solo_ok) or umidade_tendencia_solo == 'diminuindo':
                final_necessidade_irrigacao = 'sim'
                sugestao_final_msg = "SOBRESCRITA: O clima não sugere irrigar, mas a umidade do solo (sensor) está BAIXA e/ou diminuindo."
                # Adiciona condição para não sobrescrever se choveu o suficiente no histórico
                if sum_chuva_clima_hist >= limiar_chuva_recente: # Se choveu bastante no histórico recente
                    final_necessidade_irrigacao = 'nao' # Reverte a sobrescrita se a chuva no histórico foi suficiente
                    sugestao_final_msg = "AVISO: Solo baixo, mas chuva recente significativa. Reverter sugestão: NÃO necessita irrigação."

            elif (mode_nivel_umidade_solo == 'ok' or mean_valor_umidade_solo >= limiar_umidade_solo_ok) and umidade_tendencia_solo != 'diminuindo':
                sugestao_final_msg = "CONFIRMADA: O clima e a umidade do solo (sensor) indicam que NÃO há necessidade de irrigação."
            else:
                sugestao_final_msg = "AVALIAR: Clima não sugere, mas umidade do solo está no limite ou incerta."


        print(f"\n--- SUGESTÃO FINAL DE IRRIGAÇÃO: {final_necessidade_irrigacao.upper()} ---")
        print(f"Motivo: {sugestao_final_msg}")


        # --- Sugestão de Horário e Duração (Pós-Decisão Aprimorada com Histórico) ---
        if final_necessidade_irrigacao == 'sim':
            print("\n--- Detalhes da Sugestão ---")
            
            current_temp = latest_clima_data['Temp_Max_C']
            current_ura_clima = latest_clima_data['URA_Perc']
            current_chuva = latest_clima_data['Chuva_mm']
            current_hour = latest_clima_data['Hora_do_Dia']
            
            sugestao_horario = ""
            
            # Prioridade 1: Necessidade Crítica ou Pós-Chuva
            if umidade_tendencia_solo == 'diminuindo' and mean_valor_umidade_solo < (limiar_umidade_solo_ok - 10): 
                sugestao_horario = "IMEDIATAMENTE (umidade do solo crítica e em queda!)"
            elif sum_chuva_clima_hist > 0 and sum_chuva_clima_hist < limiar_chuva_recente * N_LEITURAS_HISTORICO / 2: # Choveu pouco no período histórico
                sugestao_horario = "imediatamente após chuva cessar, para complementar."
            elif sum_chuva_clima_hist >= limiar_chuva_recente * N_LEITURAS_HISTORICO: # Choveu o suficiente no período histórico
                sugestao_horario = "Reavaliar (a chuva histórica pode ter sido suficiente, monitore o solo)."
            # Prioridade 2: Horários ideais de clima se não for crítico, considerando a tendência do clima
            elif (current_hour >= 6 and current_hour < 10) or (current_hour >= 18 and current_hour < 22):
                if current_temp < 30 and current_ura_clima > 70 and clima_temp_tendencia != 'aumentando' and clima_ura_tendencia != 'diminuindo':
                    sugestao_horario = "entre 06:00-10:00 ou 18:00-22:00 (condições ótimas, clima estável/melhorando)."
                else:
                    sugestao_horario = "horário ideal de clima (06:00-10:00 ou 18:00-22:00) com atenção ao clima atual."
            # Prioridade 3: Agora, se as condições atuais não forem péssimas (fora dos picos) e umidade solo não for crítica
            elif current_temp < 30 and current_ura_clima > 60:
                sugestao_horario = "Agora, se não puder esperar pelos horários ideais."
            else: # Pior cenário, se for muito quente/seco fora dos horários ideais
                sugestao_horario = "aguardar horários de menor temperatura e maior umidade do ar (ex: madrugada/noite)."
            

            sugestao_duracao_min = "5-10 minutos"
            if mean_valor_umidade_solo < 30: 
                sugestao_duracao_min = "20-30 minutos (umidade do solo crítica)"
            elif mean_valor_umidade_solo < limiar_umidade_solo_ok:
                sugestao_duracao_min = "15-20 minutos (para compensar baixa umidade do solo)"
            elif sum_chuva_clima_hist > 0 and sum_chuva_clima_hist < limiar_chuva_recente * N_LEITURAS_HISTORICO: # Ajuste o limiar aqui para histórico de chuva
                sugestao_duracao_min = "5 minutos (para complementar a chuva)."

            print(f"É recomendado irrigar. Melhor Horário: {sugestao_horario}")
            print(f"Duração Sugerida: Aproximadamente {sugestao_duracao_min}.")
            print("Ajuste a duração observando a resposta do solo.")
        else:
            print("\n--- Detalhes da Sugestão ---")
            print("Não há necessidade de irrigação no momento. Continue monitorando.")

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a predição combinada: {e}.")
        traceback.print_exc()

    input("Pressione ENTER para continuar.")


def sair_do_programa():
    print("Encerrando o programa...")
    try:
        if conexao_db_ativa and conn:
            inst_cadastro.close()
            inst_consulta.close()
            inst_alteracao.close()
            inst_exclusao.close()
            conn.close()
            print("Conexão com o banco de dados encerrada com sucesso.")
    except Exception as e:
        print(f"Erro ao fechar a conexão com o banco de dados: {e}")
    finally:
        if client:
            client.loop_stop()
            client.disconnect()
            print("Cliente MQTT desconectado.")
        sys.exit()


# --- LOOP PRINCIPAL DO PROGRAMA ---
while True:
    os.system('cls')    

    print("---- Gerenciamento de dados de campo ----")
    print("""
    1 - Carregar e Processar Dados Climáticos (weather_data.csv)
    2 - Predição de Necessidade de Irrigação (Modelo ML + Sensor MQTT)
    3 - Adicionar leitura (manual - DB)
    4 - Listar leituras (DB)
    5 - Excluir leituras (DB)
    6 - Limpar base de leituras (DB)
    7 - Coletar últimas leituras MQTT para análise (em memória)
    8 - Salvar leituras MQTT do DataFrame no Banco de Dados
    9 - Monitorar leituras MQTT (ao vivo)
    10 - Sair
    """)

    escolha_str = input(margem + "Escolha -> ")    

    if not escolha_str.isdigit():
        print("Entrada inválida. Por favor, digite um número válido.") 
        input("Pressione ENTER para continuar.") 
        continue

    escolha = int(escolha_str)

    match escolha:

        case 1:
            carregar_e_processar_dados_climaticos()

        case 2:
            prever_irrigacao_combinada_ml()

        case 3:
            adicionar_leitura_manual()

        case 4:
            listar_leituras()

        case 5:
            alterar_leituras()

        case 6:
            limpar_base_leituras()

        case 7:
            coletar_leituras_mqtt_em_dataframe()

        case 8:
            salvar_dataframe_no_banco_de_dados()

        case 9:
            monitorar_leituras_mqtt_ao_vivo()

        case 10:
            sair_do_programa()

        case _:
            print("Opção inválida. Por favor, escolha uma opção válida do menu.")
            input("Pressione ENTER para continuar.")