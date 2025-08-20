## FIAP - Faculdade de Informática e Administração Paulista

<p style="padding-top: 40px">
    <a href= "https://www.fiap.com.br/">
        <img src="../assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=30%>
    </a>
</p>

<br>

# Sprint 3 - Fase 5 - FarmTech na era da Cloud Computing


## Grupo TiãoTech

<p style="padding-top: 10px;">
    <img src="../assets/tiaotech-logo.png" alt="Grupo TiãoTech" border="0" width=10%>
</p>


## 👨‍🎓 Integrantes
- <a href="https://www.linkedin.com/in/edmilson-marciano-02648a33">RM565912 - Edmilson Marciano</a>
- <a href="https://www.linkedin.com/in/jayromazzi">RM565576 - Jayro Mazzi Junior</a>
- <a href="https://www.linkedin.com/in/lucas-a-5b7a70110">RM563353 - Lucas Arcanjo</a>
- <a href="https://www.linkedin.com/in/vinicius-andrade-01208822b">RM564544 - Marcus Vinicius de Andrades Silva Malaquias</a>

## 👩‍🏫 Professores

### Tutor
- <a href="https://www.linkedin.com/in/lucas-gomes-moreira-15a8452a">Lucas Gomes Moreira</a>

### Coordenador
- <a href="https://www.linkedin.com/in/andregodoichiovato">Andre Godoi Chiovato</a>



# Considerações iniciais e premissas

.

# Entrega 1

# Entrega 2

## Objetivo

Exercitar o uso da AWS Pricing Calculator, recurso que auxilia em estimativas prévias de custo mensal de uso das ferramentas de Cloud Computing da AWS.

## Configuração solicitada

- Função: hospedar API de coleta de dados de sensores agrícolas (entrega 1)
- Sistema operacional: Linux
- CPUs: 2
- Memória: 1 GiB
- Rede: até 5 Gb/s
- Armazenamento: 50 GB
- Região: a mais barata entre São Paulo (BR) e Virgínia do Norte (EUA)

**Outros requisitos e limitações**

    1 - Baixa latência no acesso aos dados.
    2 - Há restrições legais de acesso a dados no exterior.

**Importante**

- Dada a natureza do exercício, não foram consideradas necessidades outras que não as especificadas no enunciado.
- Assumimos que a anotação (HD) no enunciado não se refere necesariamente a um HD físico e sim apenas uma observação de que não se trata de um serviço de storage apartado.

### Visão conceitual da arquitetura

![Visão conceitual da arquitetura](assets/estimate_required_concept.png)
*<center><sub>Visão geral simplificada da arquitetura</sub></center>*


## Estimativas realizadas na AWS Pricing Calculator
https://calculator.aws/

### Critérios de seleção

Conforme solicitado, o critério principal é **preço**, ou seja, a configuração de menor custo, que atenda à especificação solicitada.

Foram feitas duas estimativas, uma para cada região solicitada.

### Configuração selecionada

## Instância Amazon EC2 - t4g.micro
Trata-se de uma arquitetura de uso geral, recomendada para aplicações que não exigem  desempenho extremo.

Utiliza armazenamento **AWS EBS** <sup>1</sup>

#### Características
- vCPUs: 2
- Memória: 1 GB
- Rede: até 5 Gb/s
- Armazenamento: **EBS** apenas <sup>1</sup>

#### Outras opções
- Data transfer de entrada (internet): 5 GB/mês
- Data transfer de saída (internet): 5 GB/mês
- **Shared instances** - Opção de custo benefício mais favorável para esta fase. Compartilha o mesmo servidor com outras instâncias.
- **EC2 Instance Savings Plans** <sup>2</sup>

### <sup>1</sup> Amazon EBS Volume 
Um volume EBS, ou Elastic Block Storage, é um recurso lógico que atua como um HD ou SSD, mas pode estar distribuído ao longo de diversos discos e servidores em um data center, o que confere alta durabilidade e disponibilidade aos volumes.
- O volume EBS está localizado necessariamente no mesmo data center (availability zone) da instância EC2. Isso garante uma conexão de alta velocidade e baixa latência entre a instância e o armazenamento, já que eles estão fisicamente próximos.
- A persistência dos dados em um volume EBS independe do funcionamento da instância.
- É uma solução flexível e escalável.
- Backup (snapshots) configurável conforme a necessidade.

#### Características
- Tamanho: 50 GB

#### Outras opções
- General purpose SSD
- Backup diferencial, diário.
- Poderíamos optar por uma frequência menor de backup, o que baixaria o custo, mas com a contrapartida de tornar a operação menos segura.

### Opções de contratação

<sup>2</sup> **EC2 Instance Savings Plans** - Esta opção está disponível para contratação de uma família única de instâncias EC2 em uma única região - o que se aplica ao nosso caso -  e pode render descontos de até 72% nos valores de uso, mantendo a característica **on-demand** da instância contratada. A contrapartida é o tempo mínimo de contratação. Para fins de exercício, consideramos uma opção razoável, com um retorno de investimento favorável.

### Estimativa 1 - t4g.micro - Região US East (North Virginia)

Veja a estimativa no arquivo [agro-machine-estimate_us_east_op_1.pdf](documents/estimates/agro-machine-estimate_us_east_op_1.pdf) ou na [página da AWS](https://calculator.aws/#/estimate?id=9844a4d02d605a1469e255effbb8b9a71f9932b4 "AWS Estimativa 1").

#### Resumo

| Serviço | Custo mensal (U$) |
| ----------- | -----------: |
| Amazon EC2 - t4g.micro - US East | 11,08 |

- O custo do armazenamento EBS já está incluso.
- Os custos não incluem impostos
- Veja **Opções de contratação - EC2 Instance Savings Plans**, acima².

### Estimativa 2 - t4g.micro - Região South America (São Paulo)

Veja a estimativa no arquivo [agro-machine-estimate_south_america_op_2.pdf](documents/estimates/agro-machine-estimate_south_america_op_2.pdf) ou na [página da AWS](https://calculator.aws/#/estimate?id=7ee46ca7a4a522cb20b35ee179a43053655211d0 "AWS Estimativa 2").

#### Resumo

| Serviço | Custo mensal (U$) |
| ----------- | -----------: |
| Amazon EC2 - t4g.micro - South America | 18,01 |

- Observações idem estimativa 1, acima.

## Configuração alternativa

Ainda que o enunciado do exercício tenha sido claro, propomos aqui simular a possibilidade da seguinte situação imprevista:

1. Segundo os arquitetos da solução, a capacidade de memória de 1 GB pode ser limitante para o desempenho da API.
2. Uma análise das características da EC2 t4g levantou que a arquitetura utilizada nos processadores AWS Graviton2 (arquitetura ARM64), pode apresentar incompatibilidades com algumas biliotecas de Machine Learning para o Linux, exigindo atapas adicionais de compilação.

Diante disso, voltamos à calculadora.

### Configuração selecionada

## Instância Amazon EC2 - t3a.medium
Trata-se igualmente de uma arquitetura de uso geral.

#### Características
- **Memória: 4 GB**
- Todas as demais características, opções e observações são idênticas às apresentadas para a ```t4g.micro```.


### Estimativa 3 - t3a.medium - Região US East (North Virginia)

Veja a estimativa no arquivo [agro-machine-estimate_us_east_op_3.pdf](documents/estimates/agro-machine-estimate_us_east_op_3.pdf) ou na [página da AWS](https://calculator.aws/#/estimate?id=da24ed25632959a1fabd8b6e2131716925183795 "AWS Estimativa 3").

#### Resumo

| Serviço | Custo mensal (U$) |
| ----------- | -----------: |
| Amazon EC2 - t3a.medium - US East | 20,28 |


### Estimativa 4 - t3a.medium - Região South America (São Paulo)

Veja a estimativa no arquivo [agro-machine-estimate_south_america_op_4.pdf](documents/estimates/agro-machine-estimate_south_america_op_4.pdf) ou na [página da AWS](https://calculator.aws/#/estimate?id=df5725f307041bf1342e99a276b8d57b463396d0 "AWS Estimativa 4").

#### Resumo

| Serviço | Custo mensal (U$) |
| ----------- | -----------: |
| Amazon EC2 - t3a.medium - South America | 32,83 |

### Tomada de decisões
Elaborar a melhor estimativa para um projeto de arquitetura implica jogar com inúmeras variáveis de forma estratégica, já que pequenos ajustes podem resultar em economia ou gastos desnecessários. Para fins de exercício, foram elaboradas 4 estimativas, comparadas na tabela a seguir. 

Num caso real, o fine-tuning de parâmetros de configuração poderia exigir estimativas adicionais, dependendo das necessidades do projeto, reunindo informações que permitiriam decidir de forma mais embasada pela melhor opção, por parte dos stakeholders do projeto em questão.

A tabela a seguir resume algumas considerações sobre as opções estimadas.

#### Tabela comparativa final

| Opção | Instância / Região | Custo (U$/mês) | Vantagens | Desvantagens |
| :-------: | ------- | -------: | ------- | ------- |
| 1 | t4g.micro - US East (North Virginia) | 11,08 | <ul><li>Menor preço</li></ul> | <ul><li>Pode ter restrição de acesso a dados</li><li>Processadores com arquitetura ARM</li><li>Maior latência</li><li>Memória limitada</li></ul>
| 2 | t4g.micro - South America (São Paulo) | 18,01 | <ul><li>Sem restrição de acesso a dados</li><li>Menor latência</li></ul> |<ul><li>Processadores com arquitetura ARM</li><li>Memória limitada</li></ul> 
| 3 | t3a.medium - US East (North Virginia) | 20,28 | <ul><li>Arquitetura x86_64</li><li>Folga de memória</li></ul> | <ul><li>Pode ter restrição de acesso a dados</li><li>Maior latência</li></ul>
| 4 | t3a.medium - South America (São Paulo) | 32,83 | <ul><li>Sem restrição de acesso a dados</li><li>Menor latência</li><li>Arquitetura x86_64</li><li>Folga de memória</li></ul> |  <ul><li>Maior preço</li></ul>

As informações da tabela acima suscitam diversas questões a partir do confronto entre vantagens e desvantagens dessa ou daquela opção. Questões como:
> Devemos pagar menos e arcar com o risco de sanções legais de acesso a dados em território estrangeiro e com uma maior latência no acesso aos dados?

> Devemos pagar mais e, em contrapartida, eliminar quaisquer riscos de incompatibilidade de bibliotecas de ML, além de menor latência de acesso aos dados?

Vários outros questionamentos podem ser propostos e esse é o desafio para a visão estratégica dos profissionais envolvidos nessas decisões.

### Fatores determinantes
O exercício permitiu observar, ainda que num nível ainda pouco aprofundado, como os valores estimados podem variar muito dependendo das opções configuradas. Dentre os principais fatores que influenciam o custo, podemos destacar:

#### Tipos de instância EC2 (tipo, geração e tamanho)
Este geralmente é o principal fator de custo. Exemplos: 
- Arquiteturas ``t3`` têm preço mais baixo que ```t4```. 
- Gerações mais recentes, como ```t3``` e ```t3```, tendem a ter um custo comparativamente menor e tecnologia superior.
- Uma arquitetura ```micro``` custa menos que uma ```medium```, mas oferece menos recursos (vCPUs e memória).  

#### Região
Como mostra o próprio exercício, a localização física tem um impacto importante. Os preços de todos os serviços (EC2, EBS, transferência de dados) podem ser significativamente mais altos em uma região (como São Paulo) devido a custos operacionais e impostos locais.

#### Armazenamento
A arquitetura de armazenamento, o tipo e a capacidade provisionada também tendem a mudar sensivelmente os valores de uso. Embora o tipo EBS ```gp3```, de uso geral, seja mais barato e flexível, soluções de altíssima performance, como ```io2```, costumam ser bem mais custosos.

#### Data transfer
A transferência de dados pode ser um custo estratégico e muitas vezes subestimado. Para economizar, seria ideal hospedar aplicações e bancos de dados na mesma região AWS. A transferência de dados entre serviços na mesma região geralmente é gratuita, enquanto a troca de dados com a Internet é cobrada. Essa diferença pode tornar os custos de transferência de dados significativamente mais altos se a arquitetura não for bem planejada.


## Conclusão

#### Sobre o uso da calculadora

Num primeiro momento, não proporciona uma experiência de uso agradável devido à complexidade da solução e do catálogo de serviços. Há interfaces diferentes, dependendo do ponto de acesso. Há sobrecarga de informações e de opções. A navegação não é facilitada. A curva de aprendizado não é favorável. Fica claro entender por que é necessário ser um profissional certificado para lidar com projetos de computação em nuvem. Requer familiaridade e experiência com a aplicação, assim como entendimento absoluto das necessidades do projeto para poder selecionar corretamente as opções mais adequadas e favoráveis.

Ainda assim, a calculadora conta com inúmeros recursos úteis, não só para o dimensionamento de estimativas, mas também para aprendizado do assunto e principalmente para tomada de decisões, como exemplos de cálculo, breakeven e memorial de cálculo detalhado das estimativas.











## 📁 Estrutura de pastas

- sprint_3/**assets**: imagens e outros artefatos.

- sprint_3/**documents**: .

- sprint_3/**scripts**: .

- sprint_3/**src**: .

- sprint_3/**README_sprint_2.md**: descrição geral da entrega (este documento que você está lendo agora).


## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/agodoi/template">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">Fiap</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>


