class VaultError(Exception):
    pass

class VaultNotInitializedError(VaultError):
    pass

class MasterPasswordError(VaultError):
    pass