from .storage import StorageProvider
from .cipher import Cipher
from .exceptions import VaultError, VaultNotInitializedError

class Registry:
    """Orquestra a regra de negócio utilizando Storage agnóstico e o motor de cifra."""
    
    def __init__(self, storage: StorageProvider):
        self.storage = storage

    def init(self, senha: str):
        if self.storage.exists():
            raise VaultError("o cofre ja foi inicializado antes.")
            
        dados = {"__verify__": Cipher.encrypt(senha, "ok")}
        self.storage.save(dados)

    def set(self, senha: str, chave: str, valor: str):
        if chave.startswith("__"):
            raise ValueError("chaves com '__' sao reservadas pelo sistema.")
        if not self.storage.exists():
            raise VaultNotInitializedError("cofre nao inicializado. rode 'init' primeiro.")

        dados = self.storage.load()
        
        Cipher.decrypt(senha, dados["__verify__"]) # valida senha
        
        dados[chave] = Cipher.encrypt(senha, valor)
        self.storage.save(dados)

    def get(self, senha: str, chave: str) -> str:
        if chave.startswith("__"):
            raise ValueError("acesso negado a chaves internas.")
        if not self.storage.exists():
            raise VaultNotInitializedError("cofre nao inicializado. rode 'init' primeiro.")

        dados = self.storage.load()
        
        Cipher.decrypt(senha, dados["__verify__"]) # valida senha
        
        if chave not in dados:
            raise KeyError(f"chave '{chave}' nao existe no cofre.")
            
        return Cipher.decrypt(senha, dados[chave])