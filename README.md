# Regina da Saúde 20123 em 2026

Para onde foram os votos de Regina da Saúde (Maria Regina da Cunha, Podemos, número 20123) para deputada estadual em Pernambuco, no 1º turno de 04/10/2026. Foi a primeira eleição dela para deputada estadual.

**Site:** https://leonardoanselmo.github.io/regina-da-saude-2026/
**PDF:** [relatorio/Regina_da_Saude_20123_2026.pdf](relatorio/Regina_da_Saude_20123_2026.pdf)

O relatório tem:
- mapa de Pernambuco com os votos por município;
- os 167 municípios onde ela teve voto, com a posição dela em cada um;
- força nas cidades: onde ela ficou entre os primeiros e quem liderou;
- Itaíba, a base eleitoral, por bairro/distrito e por local de votação;
- Itaíba 2022 × 2026: de quem eram, em 2022, os votos que ela conquistou, com mapa dos locais de votação;
- votos em cada seção eleitoral de PE, sem misturar as seções agregadas;
- resultado oficial: a lista do Podemos e quantos votos faltaram para a vaga.

Resultado proclamado pelo TSE: Regina ficou como **1ª suplente do Podemos**, a 385 votos do último eleito do partido.

## Estrutura

| Pasta / arquivo | Conteúdo |
|---|---|
| `index.html` | O site publicado no GitHub Pages (gerado pelo passo 6) |
| `scripts/` | Coleta e análise, numeradas na ordem em que rodam |
| `scripts/comum.py` | Parâmetros da candidata (número, cargo, cidade-base) e funções compartilhadas |
| `scripts/template.html` | Modelo da página. Os dados são inseridos no passo 6 |
| `dados/` | Resultados pequenos que alimentam o site e o PDF |
| `relatorio/` | Versão em PDF (gerada pelo passo 7) |
| `brutos/` | Downloads grandes do TSE (fora do Git, criados pelos scripts) |

## Como atualizar

Requer Python 3.10 ou mais novo. Os passos 1 a 6 usam só a biblioteca padrão.

```bash
cd scripts
python 1_coleta_municipios.py   # API do TSE: votos, % e posição da 20123 nos 185 municípios
python 2_resultado_oficial.py   # vagas por partido e lista do Podemos (resultado proclamado)
python 3_base_secoes.py         # Itaíba por local de votação e bairro (~280 MB na 1ª vez)
python 3b_votos_por_secao.py    # votos da 20123 em cada seção de PE (mesmos downloads do passo 3)
python 3c_base_2022.py          # Itaíba 2022 x 2026 (~150 MB de 2022)
python 5_mapa.py                # contornos dos municípios e votos por código IBGE
python 6_monta_site.py          # gera dados/relatorio.json e index.html
```

Para gerar o PDF:

```bash
pip install -r requirements.txt
python scripts/7_gera_pdf.py
```

Os arquivos grandes ficam em `brutos/` e só são baixados se ainda não existirem.

## Seções agregadas e consolidadas

Quando uma seção é agregada a outra, os eleitores dela votam na urna da seção principal, e o TSE publica o resultado só na principal. O arquivo de votos por seção não tem linhas para as agregadas: em PE são 673 agregadas, somadas em 626 seções principais.

Por isso, o passo 3b:
- não cria linha para seção agregada (e confere que nenhuma agregada tem voto próprio);
- marca a principal como consolidada e lista as agregadas que ela recebe;
- soma o eleitorado da principal com o das agregadas, para o percentual não misturar bases.

O arquivo de locais de votação repete cada seção para o 1º e o 2º turno. Os scripts usam só as linhas do 1º turno e ligam cada seção ao local pela própria seção.

## Itaíba 2022 × 2026

Em 2022, os votos de Itaíba para deputado estadual se concentraram em Rodrigo Novaes (40555), que não concorreu em 2026, e em Claudiano Filho (11555), que disputou as duas eleições. O passo 3c compara a fatia de cada um nos votos válidos para deputado estadual, por bairro/distrito e por local de votação (só locais com o mesmo código nos dois anos).

## Fontes

- [API de resultados do TSE](https://resultados.tse.jus.br/oficial/ele2026/6259/dados/pe/pe-c0007-e006259-u.json): votos por município e resultado oficial (eleição 6259, cargo 7).
- [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/): `votacao_secao_2026_PE`, `votacao_secao_2022_PE`, `eleitorado_local_votacao_2026` e `eleitorado_local_votacao_2022`.
- Contornos dos municípios: [geodata-br](https://github.com/tbrugz/geodata-br), a partir da malha do IBGE.

## Sobre o PDF

As dicas ao passar o mouse no PDF aparecem no Adobe Acrobat Reader e no Firefox. O leitor de PDF do Chrome e do Edge não as mostra. Para a versão interativa em qualquer navegador, use o site.

---

## Quem desenvolveu?

<img src="img/leo.jpg" alt="Foto de Léo Ansélmo" width="96" align="left">

**Léo Ansélmo** — Bacharelado em Administração e Desenvolvimento de Sistemas, com mais de 20 anos de experiência na área.

Procurei desenvolver um relatório baseado nos dados do TSE, mostrando o panorama político do candidato para o mesmo entender os dados consolidados e gerar conhecimento agregado da campanha atual.

Com ajuda da inteligência artificial (AI) nos mapas e gráficos, obtendo uma compreensão visual mais detalhada.

Instagram: [@leonardoanselmo79](https://www.instagram.com/leonardoanselmo79/)
