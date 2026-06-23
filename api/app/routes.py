import json
from pydantic import BaseModel
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Dict, Any
import secrets

from .security import verificar_token, TOKEN_MESTRE, tokens_ativos

router = APIRouter()
DB_FILE = Path("server_vault.json")

class LoginRequest(BaseModel):
    senha: str

@router.get("/vault", dependencies=[Depends(verificar_token)])
def buscar_cofre():
    """Retorna o estado atual do cofre criptografado."""
    if not DB_FILE.exists():
        raise HTTPException(status_code=404, detail="Cofre remoto nao inicializado")
    
    with open(DB_FILE, "r") as f:
        return json.load(f)

@router.put("/vault", dependencies=[Depends(verificar_token)])
def salvar_cofre(payload: Dict[str, Any]):
    """Recebe o dicionário criptografado da CLI e persiste."""
    with open(DB_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    return {"status": "sucesso", "mensagem": "Cofre atualizado"}

@router.head("/vault", dependencies=[Depends(verificar_token)])
def checar_existencia():
    """Rota apenas para verificar existencia sem baixar o JSON inteiro."""
    if not DB_FILE.exists():
        raise HTTPException(status_code=404)
    return Response(status_code=200)

class LoginRequest(BaseModel):
    senha: str

@router.post("/auth")
def login(req: LoginRequest):
    if req.senha == TOKEN_MESTRE:
        novo_token = secrets.token_hex(16)
        tokens_ativos.add(novo_token)
        return {"access_token": novo_token}
    
    raise HTTPException(status_code=401, detail="nao autorizado")