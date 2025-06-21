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

# Configura pandas para imprimir dataframe completo
# pd.set_option('display.max_rows', None)


# Lê arquivo de dados de leitura de sensores.
data_file = "input/computer_7.csv"
log_file = "input/computer_7.log"



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
    print("Erro: ", e) # Informa o erro
    conexao = False    # Não há conexão

else:
    conexao = True    # Há conexão

margem = ' ' * 4

# nova função para predição de irrigação
def prever_irrigacao(inst_consulta, conn, data_file):
    os.system('cls')
    print("----- Predição de Irrigação -----")

    try:
        # 1. carregar dados históricos do csv
        try:
            data_csv = pd.read_csv(data_file)
            print(f"Dados históricos carregados do CSV: {data_csv.shape[0]} registros.")
        except FileNotFoundError:
            print(f"Erro: Arquivo {data_file} não encontrado.")
            data_csv = pd.DataFrame()
        except Exception as e:
            print(f"Erro ao carregar dados do CSV: {e}.")
            data_csv = pd.DataFrame()

        # 2. Carregar dados históricos do banco de dados
        sql_select_all = 'SELECT * FROM T_READINGS'
        inst_consulta.execute(sql_select_all)
        data_db = inst_consulta.fetchall()
        colunas_db = [desc[0] for desc in inst_consulta.description]
        df_db = pd.DataFrame(data_db, columns=colunas_db)
        print(f"Dados históricos carregados do banco de dados: {df_db.shape[0]} registros.")

        # Unir dados do CSV e DB (se ambos existirem)
        if not data_csv.empty and not df_db.empty:
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

            colunas_relevantes = [
                'READING_TIME', 'READING_HUMIDITY_VALUE', 'READING_HUMIDITY_LEVEL',
                'READING_PUMP', 'READING_PHOSPHORUS', 'READING_POTASSIUM',
                'READING_PH_VALUE', 'READING_PH_LEVEL', 'READING_TEMPERATURE'
            ]

            # Tentar converter tipos de dados do CSV para serem compatíveis com o DB
            for col in ['READING_TIME', 'READING_HUMIDITY_VALUE', 'READING_PH_VALUE']:
                data_csv_renamed[col] = pd.to_numeric(data_csv_renamed[col], errors='coerce')
            for col in ['READING_TEMPERATURE', 'READING_POTASSIUM']:
                data_csv_renamed[col] = pd.to_numeric(data_csv_renamed[col], errors='coerce')

            # Converter para o mesmo tipo de string para colunas de nível/bomba
            data_csv_renamed['READING_HUMIDITY_LEVEL'] = data_csv_renamed['READING_HUMIDITY_LEVEL'].astype(str).str.lower()
            data_csv_renamed['READING_PUMP'] = data_csv_renamed['READING_PUMP'].astype(str).str.lower()
            data_csv_renamed['READING_PHOSPHORUS'] = data_csv_renamed['READING_PHOSPHORUS'].astype(str).str.lower()
            data_csv_renamed['READING_PH_LEVEL'] = data_csv_renamed['READING_PH_LEVEL'].astype(str).str.lower()

            df_db['READING_HUMIDITY_LEVEL'] = df_db['READING_HUMIDITY_LEVEL'].astype(str).str.lower()
            df_db['READING_PUMP'] = df_db['READING_PUMP'].astype(str).str.lower()
            df_db['READING_PHOSPHORUS'] = df_db['READING_PHOSPHORUS'].astype(str).str.lower()
            df_db['READING_PH_LEVEL'] = df_db['READING_PH_LEVEL'].astype(str).str.lower()

            data_csv_selected = data_csv_renamed[colunas_relevantes].copy()
            df_db_selected = df_db[colunas_relevantes].copy()

            dados_completos = pd.concat([data_csv_selected, df_db_selected], ignore_index=True)
            print(f"Total de dados para treinamento: {dados_completos.shape[0]} registros.")
        elif not data_csv.empty:
            dados_completos = data_csv.rename(columns={
                'time': 'READING_TIME',
                'valor_umidade': 'READING_HUMIDITY_VALUE',
                'nivel_umidade': 'READING_HUMIDITY_LEVEL',
                'bomba': 'READING_PUMP',
                'fosforo': 'READING_PHOSPHORUS',
                'potassio': 'READING_POTASSIUM',
                'valor_ph': 'READING_PH_VALUE',
                'nivel_ph': 'READING_PH_LEVEL',
                'temperatura': 'READING_TEMPERATURE'
            })[colunas_relevantes].copy()

            for col in ['REAING_TIME', 'READING_HUMIDITY_VALUE', 'READING_PH_VALUE']:
                dados_completos[col] = pd.to_numeric(dados_completos[col], errors='coerce')
            for col in ['REAING_TEMPERATURE', 'READING_POTASSIUM']:
                dados_completos[col] = pd.to_numeric(dados_completos[col], errors='coerce')

            dados_completos['READING_HUMIDITY_LEVEL'] = dados_completos['READING_HUMIDITY_LEVEL'].astype(str).str.lower()
            dados_completos['READING_PUMP'] = dados_completos['READING_PUMP'].astype(str).str.lower()
            dados_completos['READING_PHOSPHORUS'] = dados_completos['READING_PHOSPHORUS'].astype(str).str.lower()
            dados_completos['READING_PH_LEVEL'] = dados_completos['READING_PH_LEVEL'].astype(str).str.lower()

            print(f"Total de dados para treinamento: {dados_completos.shape[0]} registros (apenas CSV).")
        elif not df_db.empty:
            dados_completos = df_db[colunas_relevantes].copy()
            print(f"Total de dados para treinamento: {dados_completos.shape[0]} registros (apenas DB).")
        else:
            print("Não há dados suficientes para treinamento do modelo.")
            input("Pressione ENTER para continuar.")
            return

            dados_completos.dropna(inplace=True)
            if dados_completos.empty:
                print("Após o pré-processamento, não restaram dados válidos para o treinamento do modelo.")
                input("Pressione ENTER para continuar.")
                return
            
            # 3. Pré-processamento dos dados

            le_humidity_level = LabelEncoder()
            le_pump = LabelEncoder()
            le_phosphorus = LabelEncoder()
            le_ph_level = LabelEncoder()

            dados_completos['READING_HUMIDITY_LEVEL_ENCODED'] = le_humidity_level.fit_transform(dados_completos['READING_HUMIDITY_LEVEL'])
            dados_completos['READING_PUMP_ENCODED'] = le_pump.fit_transform(dados_completos['READING_PUMP']) #TARGET
            dados_completos['READING_PHOSPHORUS_ENCODED'] = le_phosphorus.fit_transform(dados_completos['READING_PHOSPHORUS'])
            dados_completos['READING_PH_LEVEL_ENCODED'] = le_ph_level.fit_transform(dados_completos['READING_PH_LEVEL'])

            # Selecionar features (X) e target (y)
            features = [
                'READING_TIME', 'READING_HUMIDITY_VALUE', 'READING_HUMIDITY_LEVEL_ENCODED',
                'READING_PHOSPHORUS_ENCODED', 'READING_POTASSIUM',
                'READING_PH_VALUE', 'READING_PH_LEVEL_ENCODED', 'READING_TEMPERATURE'
            ]
            target = 'READING_PUMP_ENCODED'

            # Verificar se todas as features existem no DataFrame
            missing_features = [f for f in features if f not in dados_completos.columns]
            if missing_features:
                print(f"Erro: As seguintes features estão faltando após o pré-processamento: {missing_features}")
                input("Pressione ENTER para continuar.")
                return
            X = dados_completos[features]
            y = dados_completos[target]

            # Verificar se há dados suficientes para treinar o modelo
            if X.shape[0] < 2:
                print("Dados insufucientes para treinar o modelo. Sãp necessários pelo menos 2 registros.")
                input("Pressione ENTER para continuar.")
                return
            
            # Verificar se a variável target possui mais de uma classe
            if len(y.unique()) <2:
                print(f"A variável 'bomba' (target) tem apenas uma classe: {le_pump.inverse_transform(y.unique())}. Não é possível treinar um modelo de classificação.")
                print("Certifique-se de que seus dados históricos contêm registros com a bomba ligada e desligada.")
                input("Pressione ENTER para continuar.")
                return
            
            # Dividir os dados em treino e teste
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


            # 4. Treinar o modelo de ML
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            # 5. Avaliar o modelo
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"Acurácia no modelo do conjunto de teste: {accuracy:.2f}")

            # 6. Realizar uma nova predição combase em novos dados ou atuais:
            print(f"\nPara a predição, informe os valores atuais:")

            # Captura de input do usuário para a predição
        try:
            pred_time = int(input("Horário de leitura (numérico): "))
            pred_humidity_value = int(input("Umidade do solo (numérico): "))
            pred_humidity_level = input("Nível de umidade (baixo ou OK): ").lower()
            pred_phosphorus = input("Teos de Fósforo no solo (alto ou baixo): ").lower()
            pred_potassium = float(input("Teor de potássio no solo (numérico): "))
            pred_ph_value = int(input("Valor do pH do solo (numérico): "))
            pred_ph_level = input("Nível do pH do solo (alto ou baixo): ").lower()
            pred_temperature = float(input("Temperatúra (numérico, duas casas decimais): "))

            # Codificar entrada do usuário, usar .transform() pois o modelo já foi 'fitado' com os dados de treino

            try:
                pred_humidity_level_encoded = le_humidity_level.transform([pred_humidity_level])[0]
            except ValueError:
                print(f"Valor {pred_humidity_level} inválido para o nível de umidade. Use 'baixo' ou 'OK'.")
                input("Pressione ENTER para continuar.")
                return
            
            try:
                pred_phosphorus_encoded = le_phosphorus.transform([pred_phosphorus])[0]
            except ValueError:
                print(f"Valor {pred_phosphorus} inválido para o teor de fósforo. Use 'alto' ou 'baixo'.")
                input("Pressione ENTER para continuar.")
                return
            
            try:
                pred_ph_level_encoded = le_ph_level.transform([pred_ph_level])[0]
            except ValueError:
                print(f"Valor {pred_ph_level} inválido para o nível de pH. Use 'alto' ou 'baixo'.")
                input("Pressione ENTER para continuar.")
                return
            
            new_data = pd.DataFrame([[
                pred_time,
                pred_humidity_value,
                pred_humidity_level_encoded,
                pred_phosphorus_encoded,
                pred_potassium,
                pred_ph_value,
                pred_ph_level_encoded,
                pred_temperature
            ]], columns=features)

            # Fazer a predição
            predicted_pump_status_encoded = model.predict(new_data)[0]
            predicted_pump_status = le.pump.inverse_transform([predicted_pump_status_encoded])[0]

            print(f"\nSugestão de Irrigação: A bomba deve ser '{predicted_pump_status.upper()}'.")
        except ValueError as ve:
            print(f"Erro de entrada: {ve}. Certifique-se de inserir os valores nos formatos corretos.")
        except Exception as e:
            print(f"Ocorreu um erro durante a predição: {e}.")
        
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a predição: {e}.")

    input ("Pressione ENTER para continuar.")

                        
# Executa a aplicação se e enquanto houver conexão com o banco de dados.
while conexao:
    os.system('cls')  

    # Exibe menu.
    print("---- Gerenciamento de dados de campo ----")
    print("""
    1 - Cadastrar leituras em lote
    2 - Adicionar leitura
    3 - Listar leituras
    4 - Alterar leituras
    5 - Excluir leituras
    6 - Limpar base de leituras
    7 - Predição de irrigação
    8 - Sair
    """)

    # Captura a escolha do usuário.
    escolha = int(input(margem + "Escolha -> "))   
    match escolha:

        # Cadastra leituras em lote.
        case 1:
            os.system('cls')  
            print("-----  Cadastrar leituras em lote  -----")

            try:
                # Importa dados de leitura de sensores.
                data_load = pd.read_csv(data_file)
                status_bomba = data_load.loc[0, 'bomba']
                print(f"\nStatus da bomba: {status_bomba}")

            except FileNotFoundError:
                print(f"Erro: Arquivo não encontrado em '{data_file}'")
            except KeyError as e:
                print(f"Erro: coluna não encontrada. Verifique a correspondência com o arquivo de dados: {e}")
            except Exception as e:
                print(f"Ocorreu um erro durante a importação: {e}")

            try:
                # Monta instruções SQL de inserção.
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

                # Itera sobre os registros do data frame de leituras.
                for index, row in data_load.iterrows():
                    try:
                        computer_id = 7
                        reading_time = int(row['time']) 
                        reading_humidity_value = int(row['valor_umidade'])
                        reading_humidity_level = row['nivel_umidade'] 
                        reading_pump = row['bomba']
                        reading_phosphorus = row['fosforo']
                        reading_potassium = row['potassio']
                        reading_ph_value = int(row['valor_ph'])
                        reading_ph_level = row['nivel_ph'] 
                        reading_temperature = float(row['temperatura'])

                        # Cria a tupla de um registro para inserção.
                        values = (
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

                        # Monta os valores nas instruções SQL e executa a inserção do registro no banco. Comita os dados.
                        inst_cadastro.execute(sql_insert, values)
                        conn.commit()

                        print(f"Inserindo registro: {values}")

                    except Exception as e:
                        print(f"Erro ao inserir registro {index}: {e}")


            except ValueError as ve:
                print("Erro: {ve}")

            except:
                print("Erro na cponexão com o DB.")

            else:
                print("Dados gravados.")

            input("Pressione ENTER.")


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

                computer_id = input("Código do computador de borda (numérico)*: ")
                reading_time = input("Horário de leitura (numérico)*: ")
                reading_humidity_value = input("Umidade do solo (numérico, duas casas decimais): ")
                reading_humidity_level = input("Nível de umidade (baixo ou OK): ")
                reading_pump = input("Status da bomba (ligada ou desligada): ")
                reading_phosphorus = input("Teor de fósforo no solo (alto ou baixo): ")
                reading_potassium = input("Teor de potássio no solo (numérico): ")
                reading_ph_value = input("Valor do pH do solo (numérico): ")
                reading_ph_level = input("Nível do pH do solo (alto ou baixo): ")
                reading_temperature = input("Temperatura (numérico, duas casas decimais): ")

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
                print("-----  Listar leituras  -----")

                # Consulta todos os registros da tabela
                inst_consulta.execute('SELECT * FROM T_READINGS')
                data = inst_consulta.fetchall()

                # Recupera os nomes das colunas da tabela
                colunas = [desc[0] for desc in inst_consulta.description]

                # Cria o DataFrame com os dados e as colunas corretas
                dados_df = pd.DataFrame(data, columns=colunas)

                # Exibe o DataFrame na tela
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
                print("-----  Alterar leituras por ID  -----")

                id_to_edit = input("Digite o código (id numérico) do registro que você deseja editar: ")

                # Verifica se o ID é um número inteiro
                if not id_to_edit.isdigit():
                    raise ValueError("O ID deve ser um número inteiro.")
                
                fields_to_edit = {}

                print("\nEdite os valores que desejar. Deixe em branco para pular.")

                reading_humidity_value = input("Umidade do solo (numérico, duas casas decimais): ")
                if reading_humidity_value:
                    fields_to_edit['reading_humidity_value'] = reading_humidity_value

                reading_humidity_level = input("Nível de umidade (baixo ou OK): ")
                if reading_humidity_level:
                    fields_to_edit['reading_humidity_level'] = reading_humidity_level

                reading_pump = input("Status da bomba (ligada ou desligada): ")
                if reading_pump:
                    fields_to_edit['reading_pump'] = reading_pump

                reading_phosphorus = input("Teor de fósforo no solo (alto ou baixo): ")
                if reading_phosphorus:
                    fields_to_edit['reading_phosphorus'] = reading_phosphorus

                reading_potassium = input("Teor de potássio no solo (numérico): ")
                if reading_potassium:
                    fields_to_edit['reading_potassium'] = reading_potassium

                reading_ph_value = input("Valor do pH do solo (numérico): ")
                if reading_ph_value:
                    fields_to_edit['reading_ph_value'] = reading_ph_value

                reading_ph_level = input("Nível do pH do solo (alto ou baixo): ")
                if reading_ph_level:
                    fields_to_edit['reading_ph_level'] = reading_ph_level

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
                conn.rollback()  # Desfaz qualquer alteração feita na transação
                print(f"Erro ao alterar registro: {e}")
            input("Pressione ENTER.")


        # Remove leituras cadastradas no banco de dados, a partir do ID.
        case 5:
            os.system('cls')

            try:
                print("-----  Remover leituras por ID  -----")

                id_to_delete = input("Digite o código (id numérico) do registro que você deseja remover: ")

                if not id_to_delete.isdigit():
                    raise ValueError("O código deve ser um número inteiro.")
                
                else:
                    flag_confirm = input(f'Confirme que deseja remover o registro de id={id_to_delete}, S/N: ')

                    if flag_confirm == 'S' or flag_confirm == 's':
                        sql_delete = "DELETE FROM T_READINGS WHERE reading_id = :id"
                        inst_exclusao.execute(sql_delete, {'id': id_to_delete})
                        conn.commit()

                        print("Registro removido com sucesso.")

            except ValueError as ve:
                print(f"Erro de entrada: {ve}.")
            except Exception as e:
                conn.rollback()  
                print(f"Erro ao alterar registro: {e}")
            input("Pressione ENTER.")


        # Remove todos os dados de leituras da base de dados.
        case 6:
            os.system('cls')

            try:
                print("-----  Remmover da base todas as leituras  -----")

                flag_confirm_all = input(f'Confirme que deseja remover todas as leituras, S/N: ')

                if flag_confirm_all == 'S' or flag_confirm_all == 's':
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


        # Fecha a conexão com o banco de dados e termina a execução do programa.
        case 7:
            prever_irrigacao(inst_consulta, conn, data_file)
        
        case 8:
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


        case _:
            print("Opção inválida. Por favor, escolha uma opção válida do menu.")
            input("Pressione ENTER para continuar.")