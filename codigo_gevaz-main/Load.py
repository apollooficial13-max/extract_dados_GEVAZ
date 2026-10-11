"""
Load.py
-------
Camada de CARGA (LOAD): recebe os DataFrames já extraídos (Extract.py)
e salva cada um em dois formatos: .json e .csv.
"""

from pathlib import Path

import pandas as pd

from Transform import preparar_dataframe

PASTA_JSON_PADRAO = "Dados_json"
PASTA_CSV_PADRAO = "Dados_csv"


class Carregador:
    """Salva cada conjunto de dados em .json e .csv, uma pasta por formato."""

    def __init__(
        self,
        pasta_json: str = PASTA_JSON_PADRAO,
        pasta_csv: str = PASTA_CSV_PADRAO,
    ) -> None:
        self.pasta_json = Path(pasta_json)
        self.pasta_csv = Path(pasta_csv)
        self.pasta_json.mkdir(parents=True, exist_ok=True)
        self.pasta_csv.mkdir(parents=True, exist_ok=True)

    def salvar_json(self, nome: str, dados: pd.DataFrame | None) -> Path | None:
        if dados is None or dados.empty:
            print(f"[{nome}] Nenhum dado para salvar em JSON.")
            return None
        caminho = self.pasta_json / f"{nome}.json"
        preparar_dataframe(dados).to_json(
            caminho, orient="records", force_ascii=False, indent=2
        )
        print(f"[{nome}] JSON salvo em: {caminho}")
        return caminho

    def salvar_csv(self, nome: str, dados: pd.DataFrame | None) -> Path | None:
        if dados is None or dados.empty:
            print(f"[{nome}] Nenhum dado para salvar em CSV.")
            return None
        caminho = self.pasta_csv / f"{nome}.csv"
        preparar_dataframe(dados).to_csv(caminho, index=False, encoding="utf-8-sig")
        print(f"[{nome}] CSV salvo em: {caminho}")
        return caminho

    def carregar(
        self, nome: str, dados: pd.DataFrame | None
    ) -> dict[str, Path | None]:
        """Salva um único conjunto de dados nos dois formatos."""
        return {
            "json": self.salvar_json(nome, dados),
            "csv": self.salvar_csv(nome, dados),
        }

    def carregar_tudo(
        self, dicionario_dados: dict[str, pd.DataFrame]
    ) -> dict[str, dict[str, Path | None]]:
        """
        Recebe {nome: DataFrame} (saída de GerenciadorExtracao.extrair_tudo())
        e salva cada um em JSON e CSV.
        Retorna {nome: {"json": caminho, "csv": caminho}}.
        """
        resultado = {}
        for nome, dados in dicionario_dados.items():
            print(f"\n=== Carregando: {nome} ===")
            resultado[nome] = self.carregar(nome, dados)
        return resultado


if __name__ == "__main__":
    # Permite testar a carga isoladamente, usando o Extract.py
    from Extract import GerenciadorExtracao

    dados_extraidos = GerenciadorExtracao().extrair_tudo()
    Carregador().carregar_tudo(dados_extraidos)
