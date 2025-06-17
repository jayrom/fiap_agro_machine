## FIAP - Faculdade de Informática e Administração Paulista

<p style="padding-top: 40px">
    <a href= "https://www.fiap.com.br/">
        <img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=30%>
    </a>
</p>

<br>

# Fase 4 / Cap 1 - Automação e inteligência na FarmTech Solutions


## Grupo TiãoTech

## 👨‍🎓 Integrantes
- <a href="https://www.linkedin.com/in/edmilson-marciano-02648a33">Edmilson Marciano</a>
- <a href="https://www.linkedin.com/in/jayromazzi">Jayro Mazzi Junior</a>
- <a href="https://www.linkedin.com/in/lucas-a-5b7a70110">Lucas Arcanjo</a> 

## 👩‍🏫 Professores

### Tutor
- <a href="https://www.linkedin.com/in/lucas-gomes-moreira-15a8452a">Lucas Gomes Moreira</a>
### Coordenador
- <a href="https://www.linkedin.com/in/andregodoichiovato">Andre Godoi Chiovato</a>



# Considerações iniciais

A FE optou por iniciar o processo de automatização de sua lavouras, realizando uma prova de conceito (POC) em um pequeno lote de 5 hectares (200m x 250m), valendo-se de um conjunto inicial de sensores e um microcontrolador (descritos em detalhe mais adiante), cujo objetivo é extrair dados importantes de propriedades do solo, como humidade, pH, teor de nutrientes e, a partir deles, realizar predições quanto às necessidades de irrigação e correção do solo.
Neste estágio do projeto, estamos simulando a implantação dos sensores, coleta, agregação e armazenamento dos dados coletados pelos sensores em banco de dados.

# Entrega 1

## Circuito de sensores

A figura a seguir (arquivo fe_computer_7.png) mostra a configuração da unidade de edge computing utilizada para simular a coleta de sinais no lote.<br>.

![Circuito do computador de borda.](assets/fe_computer_7_circuit.png)

O circuito de simulação foi montado em https://wokwi.com/.

Os arquivos gerados pelo wokwi encontram-se em [/document/computer_7_diagram](/document/computer_7_diagram).

Conforme especificado, estamos recolhendo os seguintes sinais:

- Umidade do solo - A partir de um sensor DHT-22, que recolhe leituras analógicas.
- pH - Simulado por um sensor foto-resistor (LDR), de leituras analógicas.
- Potássio (K) - Vale-se de um pushbutton associado a um led e simula dois estados: alto (botão acionado) e baixo (botão livre). Usamos resistores para adequação de tensão e proteção.
- Fósforo (P) - Idem potássio.

O circuito conta ainda com os seguintes componentes:

- ESP32 - Microcontrolador central, nosso edge computer.
- Relê - Para acionamento de uma bomba d'água para irrigiação.


## Lógica de controle

O elemento principal da simulação é controlar o acionamento de uma bomba d'água para irrigação a partir dos valores obtidos de umidade do solo. Esses valores são medidos de forma analógica pelo sensor de umidade (DHT-22) e confrontados com um valor configurado em código (humThreshold) como limite para acionamento da bomba, ou seja, abaixo dessa valor, aciona-se o relê para ligar a bomba de irrigação e aumentar a umidade do solo; acima do limiar, desliga-se a bomba.

O sensor de pH oferece igualmente leituras analógicas, que são comparadas pelo programa com um valor configurado em código (pHThreshold). Acima do limiar, o pH é considerado baixo (ácido) e acima, alto (alcalino). Tanto o valor medido, quanto o nível calculado (alto ou baixo) são registrados para impressão.

Os sensores de potássio e de fósforo, simulam manualmente dois estados: alto para teor de potássio adequado/fósforo (OK, led aceso) e baixo para teor baixo (baixo, led apagado).

Na simulação, o circuito está configurado para recolher uma leitura dos sensores a cada segundo e serializá-las para impressão, num formato amigável (no caso, CSV) para processamento posterior.

Em linhas gerais, a lógica é exibida na figura abaixo:

![Fluxograma do computador de borda.](assets/fe_computer_7_logic.png)

# Entrega 2

## Dados importados

As leituras exibidas na saída serial do simulador estão registradas no arquivo input/coputer_7.csv (veja amostra abaixo)

![Visão da saída serial do simulador.](assets/fe_computer_7_serial.png)

Os dados de configuração para a aplicação principal estão em input/coputer_7.log (veja amostra abaixo)

![figura](assets/fe_computer_7_setup.png)

## Banco de dados

A figura a seguir traz o diagrama entidade relacionamento (DER), ou seja,  a estrutura adotada para armazenamento inicial dos dados.

![figura](assets/fe_der.png)

Embora tenhamos procurado seguir ao máximo a modelagem inicial descrita na fase 2, a decisão de utilizarmos edge computers para a agregação inicial dos dados de leitura e múltiplos sensores e a necessidade de informações adicionais exigiram a adaptação da estrutura original proposta, de forma a atender às necessidades demandadas para esta entrega.
A título ilustrativo, veja abaixo o DER original da fase 2.

![figura](assets/fe_der_fase_2.png)

Os scripts SQL para construção e população inicial da base de dados estão em [/scripts](/scripts).

## Script Python

Conta com as seguintes funcionalidades:

- Cadastrar leituras em lote - Importação de dados a partir de um arquivo CSV.
- Adicionar leitura - Inserir registro de leitura na base de dados.
- Listar leituras - Lista em tela os registros da tabela de leituras.
- Alterar leituras - Permite editar o conteúdo dos principais campos de um registro de leitura, a partir do seu ID.
- Excluir leituras - Permite excluir um registro, a partir do seu ID. 
- Limpar base de leituras - Excluir todos os registros da tabela de leituras.


# Considerações adicionais

- Não houve nenhuma transformação de tempo/data nos dados de simulação. Se considerarmos uma frequência de 3 leituras/dia, os dados considerados são equivalentes às leituras de aproximadamente 30 dias, compiladas na data anotada no arquivo computer_7.log.
    
- Os dados adicionais relativos à identificação de campo, lote, cultura etc., não relevantes para o teor da entrega,  foram inseridos na base de dados por meio do script SQL.

- Devido ao prazo exíguo, nem todas as consistências foram implementadas, como exemplo, tipo e dados inseridos pelo usuário durante a execução do programa, importação duplicada de dados etc.

- Não foram trabalhados os valores simulados no sentido de transformá-los ao que seriam valores adequados às grandezas que eles simulam (ex.: valores de um sinal de LDR (intensidade de luz) para valores de pH).

- A base de dados foi montada no banco Oracle da FIAP. Está populada, mas, caso seja necessário, os dados de leitura podem ser removidos e novamente importados por meio da própria aplicação aqui apresentada.

- Alguns dados de setup são necessários para rodar a aplicação:
    - Usuário e senha da base de dados - Inserir nas constantes db_ser e db_pass ([src/main.py](src/main.py), linhas 25 e 26)


## 📁 Estrutura de pastas

- <b>assets</b>: imagens e outros artefatos.

- <b>document</b>: artefatos de simulação (/computer_7_diagram).

- <b>scripts</b>: scripts SQL para construção e população inicial do banco de dados.

- <b>src</b>: Todo o código fonte criado para o desenvolvimento do projeto ao longo das 7 fases.

- <b>README.md</b>: descrição geral do projeto (este documento que você está lendo agora).


## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/agodoi/template">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">Fiap</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>


