#---------------------------------------------------
# TiãoTech Agro Machine
# Por favor, leia o README.md para mais informações.
#---------------------------------------------------


# Importa módulos.
import os
import oracledb
import pandas as pd


# Lê arquivo de dados de leitura de sensores.
data_file = "input/computer_7.csv"
log_file = "input/computer_7.log"


# Importa dados de leitura de sensores.
try:
    data_load = pd.read_csv(data_file)
    status_bomba = data_load.loc[0, 'bomba']
    print(f"\nStatus da bomba: {status_bomba}")

except FileNotFoundError:
    print(f"Erro: Arquivo não encontrado em '{data_file}'")
except KeyError as e:
    print(f"Erro: coluna não encontrada. Verifique a correspondência com o arquivo de dados: {e}")
except Exception as e:
    print(f"Ocorreu um erro durante a importação: {e}")


# Conecta banco de dados.
try:
    # Efetua a conexão com o Usuário no servidor

    db_user = 'RM000000' # Insira a matrícula (ex.: RM123456)
    db_pass = '1234' # Insira a senha 
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

# Executa a aplicação se e enquanto houver conexão com o banco de dados.
while conexao:
    os.system('cls')  

    # Exibe menu.
    print("---- Gerenciamento de dados de campo ----")
    print("""
    1 - Cadastrar leituras em lote
    2 - Listar leituras
    3 - Alterar leituras
    4 - Excluir leituras
    5 - Limpar base de leituras
    6 - Sair
    """)

    # Captura a escolha do usuário.
    escolha = int(input(margem + "Escolha -> "))   
    match escolha:

        # Cadastra leituras em lote.
        case 1:
            os.system('cls')  

            try:
                print("-----  Cadastrar leituras em lote  -----")

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
                ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)
                """

                # Itera sobre os registros do data frame de leituras.
                for index, row in data_load.iterrows():
                    try:
                        reading_id = index + 1 
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
                        )

                        # Monta os valores nas instruções SQL e executa a inserção do registro no banco. Comita os dados.
                        inst_cadastro.execute(sql_insert, values)
                        conn.commit()

                        print(f"Inserindo registro: {values}")

                    except Exception as e:
                        print(f"Erro ao inserir registro {index}: {e}")

# @@@ Falta tratar exceção e opção default.


            except ValueError as ve:
                print("Erro: {ve}")

            except:
                print("Erro na cponexão com o DB.")

            else:
                print("Dados gravados.")

            input("Pressione ENTER.")

        # Lista leituras cadastradas no banco de dados
        case 2:
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
                print(dados_df)

            except Exception as e:
                print(f"Erro ao buscar dados: {e}")

            print('Fim da lista')
            input('Pressione ENTER para continuar.')

        # Altera leituras cadastradas no banco de dados, a partir do ID.
        case 3:
            os.system('cls')

            try:
                print("-----  Alterar leituras por ID  -----")

                id_to_edit = input("Digite o código (id numérico) do registro que você deseja editar.")

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

            except Exception as e:
                conn.rollback()  # Desfaz qualquer alteração feita na transação
                print(f"Erro ao alterar registro: {e}")

        # Remove leituras cadastradas no banco de dados, a partir do ID.
        case 4:
            os.system('cls')

            try:
                print("-----  Remover leituras por ID  -----")

                id_to_delete = input("Digite o código (id numérico) do registro que você deseja remover.")

                if not id_to_delete.isdigit():
                    raise ValueError("O código deve ser um número inteiro.")
                
                else:
                    flag_confirm = input(f'Confirme que deseja remover o registro de id={id_to_delete}, S/N')

                    if flag_confirm == 'S' or flag_confirm == 's':
                        sql_delete = "DELETE FROM T_READINGS WHERE reading_id = :id"
                        inst_exclusao.execute(sql_delete, {'id': id_to_delete})
                        conn.commit()

                        print("Registro removido com sucesso.")

            except Exception as e:
                conn.rollback()  
                print(f"Erro ao alterar registro: {e}")

        # Remove todos os dados de leituras da base de dados.
        case 5:
            os.system('cls')

            try:
                print("-----  Remmover da base todas as leituras  -----")

                flag_confirm_all = input(f'Confirme que deseja remover todas as leituras, S/N')

                if flag_confirm_all == 'S' or flag_confirm_all == 's':
                    sql_delete_all = "DELETE FROM T_READINGS"
                    inst_exclusao.execute(sql_delete_all)
                    conn.commit()

            except Exception as e:
                conn.rollback()  
                print(f"Erro ao remover registro: {e}")

        # Fecha a conexão com o banco de dados e termina a execução do programa.
        case 6:
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