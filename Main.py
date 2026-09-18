"""
Main.py
-------
Ponto único de execução do pipeline ETL:

    1) Extract.py   -> extrai TODOS os dados, sem modificar nada
    2) Load.py      -> salva cada conjunto em .json e .csv
    3) Transform.py -> consolida tudo em arquivos únicos (xlsx, json, csv)
       (é esse arquivo que você usa depois para enviar ao banco de dados)

Uso:
    python Main.py
"""

from Extract import GerenciadorExtracao
from Load import Carregador
from Transform import PASTA_FINAL, ConsolidadorDados


def main() -> None:
    # 1) Extração (nada é modificado)
    dados_extraidos = GerenciadorExtracao().extrair_tudo()

    # 2) Carga individual em .json e .csv
    caminhos_gerados = Carregador().carregar_tudo(dados_extraidos)

    # 3) Arquivos finais com TODOS os dados juntos
    print("\n=== Gerando arquivos finais ===")
    consolidador = ConsolidadorDados()
    consolidador.gerar_excel(dados_extraidos, caminhos_gerados)
    consolidador.gerar_json_unico(dados_extraidos)
    consolidador.gerar_csv_empilhado(dados_extraidos)

    print(f"\nPipeline concluído. Os arquivos completos estão na pasta '{PASTA_FINAL}'.")


if __name__ == "__main__":
    main()
