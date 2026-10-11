"""Coleta diaria (GitHub Actions e local.ps1): python coleta/coletar.py
Importar este arquivo roda os autotestes (assert) de todas as camadas."""
from naplanta.app.coleta_diaria import executar

if __name__ == '__main__':
    executar()
