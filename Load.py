"""
load.py
-------
Camada de CARGA (LOAD): recebe os DataFrames já extraídos (extract.py)
e salva cada um em dois formatos: .json e .csv.
"""

import os
import pandas as pd

PASTA_JSON_PADRAO = "Dados_json"
PASTA_CSV_PADRAO = "Dados_csv"


class Carregador:
    """
    Salva um DataFrame (ou GeoDataFrame) em .json e .csv.
    Lida com a coluna 'geometry' (não serializável) convertendo-a para WKT.
    """

    def __init__(self, pasta_json=PASTA_JSON_PADRAO, pasta_csv=PASTA_CSV_PADRAO):
        self.pasta_json = pasta_json
        self.pasta_csv = pasta_csv
        os.makedirs(self.pasta_json, exist_ok=True)
        os.makedirs(self.pasta_csv, exist_ok=True)

    @staticmethod
    def _preparar(dados):
        """Converte geometria (se existir) para WKT e devolve um DataFrame comum do pandas."""
        df = dados.copy()

        if "geometry" in df.columns:
            # converte enquanto ainda é coluna de geometria (evita o UserWarning)
            try:
                df["geometry"] = df["geometry"].to_wkt()
            except AttributeError:
                df["geometry"] = df["geometry"].apply(
                    lambda g: g.wkt if g is not None else None
                )
          # deixa de ser GeoDataFrame -> passa a usar o to_json/to_csv do pandas
        return pd.DataFrame(df)
       

    def salvar_json(self, nome, dados):
        if dados is None or dados.empty:
            print(f"[{nome}] Nenhum dado para salvar em JSON.")
            return None
        df = self._preparar(dados)
        caminho = os.path.join(self.pasta_json, f"{nome}.json")
        df.to_json(caminho, orient="records", force_ascii=False, indent=2)
        print(f"[{nome}] JSON salvo em: {caminho}")
        return caminho

    def salvar_csv(self, nome, dados):
        if dados is None or dados.empty:
            print(f"[{nome}] Nenhum dado para salvar em CSV.")
            return None
        df = self._preparar(dados)
        caminho = os.path.join(self.pasta_csv, f"{nome}.csv")
        df.to_csv(caminho, index=False, encoding="utf-8-sig")
        print(f"[{nome}] CSV salvo em: {caminho}")
        return caminho

    def carregar(self, nome, dados):
        """Salva um único conjunto de dados nos dois formatos."""
        caminho_json = self.salvar_json(nome, dados)
        caminho_csv = self.salvar_csv(nome, dados)
        return {"json": caminho_json, "csv": caminho_csv}

    def carregar_tudo(self, dicionario_dados):
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
    # Permite testar a carga isoladamente, usando o extract.py
    from Extract import GerenciadorExtracao

    dados_extraidos = GerenciadorExtracao().extrair_tudo()
    Carregador().carregar_tudo(dados_extraidos)