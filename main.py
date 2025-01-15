from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Optional
from scraping import fetch_table_data
from alias import alias_mapping

app = FastAPI()

@app.get("/dados/{ano}/{opcao}", response_model=List[Dict[str, str]])
async def get_dados(
    ano: int,
    opcao: str,
    subopcao: Optional[str] = Query(
        None, description="Subopção amigável, como 'uvas frescas' ou 'vinhos de mesa'"
    )
):
    # Validar se a opção existe no alias_mapping
    if opcao not in alias_mapping:
        raise HTTPException(status_code=400, detail=f"Opção inválida: {opcao}")
    
    # Validação para producao e comercializacao
    if opcao in ["producao", "comercializacao"]:
        if subopcao is not None:
            raise HTTPException(
                status_code=400,
                detail=f"A opção '{opcao}' não aceita subopções. Remova o campo 'subopcao'."
            )
        opt = alias_mapping[opcao]["opt"]
        subopt = alias_mapping[opcao]["subopt"]

    # Validação para demais opções
    else:
        if not subopcao:
            raise HTTPException(
                status_code=400,
                detail=f"A opção '{opcao}' exige uma subopção válida."
            )
        if subopcao not in alias_mapping[opcao]:
            raise HTTPException(
                status_code=400,
                detail=f"Subopção inválida para '{opcao}': {subopcao}"
            )
        opt = alias_mapping[opcao][subopcao]["opt"]
        subopt = alias_mapping[opcao][subopcao]["subopt"]

    try:
        # passa os valores para o fetch_table_data
        dados = await fetch_table_data(ano, opt, subopt=subopt)
        return dados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
