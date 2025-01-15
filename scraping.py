import os
import csv
from typing import List, Dict, Optional
import httpx
import chardet
from bs4 import BeautifulSoup


async def fetch_table_data(ano: int, opcao: str, subopt: Optional[str] = None) -> List[Dict[str, str]]:
    """
    primeira tentativa busca online
    segunda tentativa busca csv 
    """
    url = "http://vitibrasil.cnpuv.embrapa.br/index.php"
    params = {
        "ano": ano,
        "opcao": opcao
    }

    # add subopt aos parametros
    if subopt:
        params["subopcao"] = subopt
    
    try:
        # tenta acessar o site
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return extract_table_data(soup)
            else:
                print(f"Falha ao buscar do site: {response.status_code}")
    except (httpx.RequestError, httpx.ConnectError) as e:
        print(f"O site está offline ou inacessível {e}")

    # Site offline: buscar nos arquivos CSV
    print("Recorrendo aos arquivos CSV locais")
    return fetch_from_csv(opcao, subopt, ano)

def fetch_from_csv(opcao: str, subopt: Optional[str], ano: int) -> List[Dict[str, str]]:
    """
    busca no csv caso o site esteja indisponivel
    filtra pelo ano e retorna os dados padronizados pelo tipo 'opt'
    """
    # construção do nome do arquivo
    if subopt:
        filename = f"subopt_{subopt.split('_')[1]}_{opcao}.csv"
    else:
        filename = f"{opcao}.csv"

    filepath = os.path.join("src", "csv", filename)

    if not os.path.exists(filepath):
        print(f"CSV file not found: {filepath}")
        return []

    data = []
    try:
        # identifica o encoding
        with open(filepath, 'rb') as f:
            detected_encoding = chardet.detect(f.read())['encoding']

        # leitura do csv com o encoding encontrado
        with open(filepath, mode="r", encoding=detected_encoding) as file:
            reader = csv.DictReader(file, delimiter=';')
            headers = reader.fieldnames  

            # verifica se o ano buscado esta no arquivo
            year_col = str(ano)
            if year_col not in headers:
                print(f"Ano {ano} não encontrado nos cabeçalhos do arquivo {filename}. Anos disponíveis: {headers}")
                return []

            # processo dos arquivos baseado no opt
            if opcao == "opt_02":
                for row in reader:
                    data.append({
                        "Produto": row.get("produto", ""),
                        "Quantidade (L.)": row.get(year_col, "")
                    })
            elif opcao.startswith("opt_03"):
                for row in reader:
                    data.append({
                        "Cultivar": row.get("cultivar", ""),
                        "Quantidade (Kg)": row.get(year_col, "")
                    })
            elif opcao.startswith("opt_04"):
                for row in reader:
                    data.append({
                        "Produto": row.get("Produto", ""),
                        "Quantidade (L.)": row.get(year_col, "")
                    })
            elif opcao.startswith("opt_05") or opcao.startswith("opt_06"):
                for row in reader:
                    data.append({
                        "Países": row.get("País", ""),
                        "Quantidade (Kg)": row.get(year_col, ""),
                        "Valor (US$)": row.get(f"valor_{year_col}", "")
                    })

    except Exception as e:
        print(f"Erro ao ler o arquivo CSV {filename}: {e}")
        return []

    if not data:
        print(f"Nenhum dado encontrado para o ano {ano} no arquivo {filename}.")
        return []

    print(f"Dados carregados do arquivo CSV: {filename} (codificação: {detected_encoding})")
    return data

def extract_table_data(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    função auxiliar para extração de dados da tabela em um objeto BeaultifulSoup
    """
    table = soup.find('table', {'class': 'tb_base tb_dados'})
    if not table:
        print("Nenhuma tabela encontrada com a classe 'tb_base tb_dados'.")
        return []
    
    headers = [th.text.strip() for th in table.find('thead').find_all('th')]
    rows = table.find('tbody').find_all('tr')
    
    data = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == len(headers):
            data.append({headers[i]: cells[i].text.strip() for i in range(len(cells))})
    return data
