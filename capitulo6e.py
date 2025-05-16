#pyFarm Controle com sensor de umidade em plantações

import random

lista= [1,2,3,4,5]

print(lista)
# Capítulo 6 - Exemplo de controle de irrigação para plantação de milho



# Simulação de leitura de um sensor de umidade para plantação de milho
def ler_sensor_umidade():
    """
    Função que simula a leitura de um sensor de umidade.
    Retorna um valor de umidade entre 0 e 100.
    """
 
    return random.randint(0, 100)

def verificar_umidade(umidade):
    """
    Verifica o nível de umidade e retorna uma ação recomendada.
    """
    if umidade < 40:
        return "Umidade baixa! Ativar sistema de irrigação."
    elif 40 <= umidade <= 70:
        return "Umidade ideal. Nenhuma ação necessária."
    else:
        return "Umidade alta! Verificar drenagem do solo."

def main():
    """
    Função principal que gerencia a leitura do sensor e as ações na plantação.
    """
    print("Monitoramento da plantação de milho iniciado...")
    umidade = ler_sensor_umidade()
    print(f"Umidade atual do solo: {umidade}%")
    acao = verificar_umidade(umidade)
    print(f"Ação recomendada: {acao}")

    nova_leitura = input("Digite uma leitura de 0 a 100: ")

    print("umidade atual do solo: ", nova_leitura)
    acao = verificar_umidade(int(nova_leitura))
    print(f"Ação recomendada: {acao}")
   
    #print("Ação recomendada: ", verificar_umidade(int(nova_leitura)))

    print("Monitoramento da plantação de milho finalizado.")


# Executa o programa
if __name__ == "__main__":
    main()



print( __name__ + "teste"); print("Controla o programa executado inicial como main")



#parte do BD
import oracledb


#db_user="RM999999"
#db_pass="999999"
db_user = input("digite o RM exe ( RM123456 ) : ")
db_pass=input("digite a senha sua data nasc exe. ( 020399 ) : ")

db_host="oracle.fiap.com.br"
db_port=1521
db_srvc="ORCL"


def coneta():
    dsn=f"{db_host}:{db_port}/{db_srvc}"
    return oracledb.connect(user=db_user,password=db_pass,dsn=dsn)
    
# Conexão com o banco de dados no final do código

try:
    # Estabelece a conexão com o banco de dados
    conn = coneta()
    print("Conexão com o banco de dados estabelecida com sucesso!")
    print("Versão do banco de dados:", conn.version)

    # Cria um cursor para executar consultas
    cursor = conn.cursor()

    # Exemplo de consulta ao banco de dados
    cursor.execute("SELECT * FROM petshop")
    resultados = cursor.fetchall()

    # Exibe os resultados da consulta
    print("Dados da tabela 'petshop':")
    for linha in resultados:
        print(linha)

    # Fecha o cursor e a conexão
    cursor.close()
    conn.close()
    print("Conexão com o banco de dados encerrada.")

except Exception as erro:
    print("Erro ao conectar ao banco de dados:", erro)

else:
    print("Conexão com o banco de dados estabelecida com sucesso!")



# Em resumo, o grupo é livre para criar a solução que quiser, desde que atenda aos requisitos a seguir.
# 
# Uma vez definida a área do agronegócio a ser tratada, contemple nesta solução os conteúdos estudados nos capítulos 3, 4, 5 e 6 sobre Python. Lembrando:
# 
# Subalgoritmos: função e procedimento com passagem de parâmetros;
# Estruturas de dados: lista, tupla, dicionário, tabela de memória;
# Manipulação de arquivos: texto e JSON.
# Conexão com banco de dados: Oracle.
