"""
main.py
-------
Ponto único de execução do pipeline:

    1) Extrai TODOS os dados, sem modificar nada (extract.py)
    2) Salva cada conjunto em .json e .csv (load.py)
    3) Gera UM arquivo final com todos os dados:
         - Dados_finais/dados_completos.xlsx  -> uma aba por conjunto + aba "resumo"
         - Dados_finais/dados_completos.json  -> tudo junto em um único JSON
       (é esse arquivo que você usa depois para enviar ao banco de dados)

Uso:
    python main.py
"""

import os
import json
from datetime import datetime

import pandas as pd

from Extract import GerenciadorExtracao
from Load import Carregador


PASTA_FINAL = "Dados_Gevaz_Gerais"


class ConsolidadorDados:
    """
    Junta todos os conjuntos extraídos em um único arquivo,
    sem alterar nenhum valor das colunas originais.
    """

    def __init__(self, pasta=PASTA_FINAL):
        self.pasta = pasta
        os.makedirs(self.pasta, exist_ok=True)

    @staticmethod
    def _para_dataframe(dados):
        """Garante DataFrame comum do pandas (nunca GeoDataFrame)."""
        if dados is None:
            return pd.DataFrame()
        df = pd.DataFrame(dados).copy()
        if "geometry" in df.columns:
            df["geometry"] = df["geometry"].astype(str)
        return df

    def _montar_resumo(self, dados_extraidos, caminhos_gerados):
        linhas = []
        for nome, dados in dados_extraidos.items():
            df = self._para_dataframe(dados)
            caminhos = caminhos_gerados.get(nome, {})
            linhas.append({
                "dado": nome,
                "linhas": len(df),
                "colunas": len(df.columns),
                "nomes_colunas": ", ".join(map(str, df.columns)),
                "arquivo_json": caminhos.get("json"),
                "arquivo_csv": caminhos.get("csv"),
                "data_extracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        return pd.DataFrame(linhas)

    def gerar_excel(self, dados_extraidos, caminhos_gerados):
        """Planilha única: uma aba por conjunto de dados + uma aba de resumo."""
        caminho = os.path.join(self.pasta, "dados_completos.xlsx")

        with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
            resumo = self._montar_resumo(dados_extraidos, caminhos_gerados)
            resumo.to_excel(writer, sheet_name="resumo", index=False)

            for nome, dados in dados_extraidos.items():
                df = self._para_dataframe(dados)
                if df.empty:
                    continue
                # nome de aba no Excel: máximo 31 caracteres
                aba = str(nome)[:31]
                df.to_excel(writer, sheet_name=aba, index=False)
                print(f"[Excel] Aba '{aba}': {len(df)} linhas, {len(df.columns)} colunas")

        print(f"\n[Excel] Planilha completa salva em: {caminho}")
        return caminho

    def gerar_json_unico(self, dados_extraidos):
        """Um único JSON com todos os conjuntos, pronto para ir ao banco depois."""
        caminho = os.path.join(self.pasta, "dados_completos.json")

        conteudo = {}
        for nome, dados in dados_extraidos.items():
            df = self._para_dataframe(dados)
            # default=str garante que datas e tipos especiais virem texto
            conteudo[nome] = json.loads(df.to_json(orient="records", force_ascii=False))

        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(conteudo, arquivo, ensure_ascii=False, indent=2, default=str)

        print(f"[JSON]  Arquivo único salvo em: {caminho}")
        return caminho

    def gerar_csv_empilhado(self, dados_extraidos):
        """
        CSV único com todos os conjuntos empilhados, identificados
        pela coluna 'conjunto'. Nenhum valor é alterado.
        """
        caminho = os.path.join(self.pasta, "dados_completos.csv")

        partes = []
        for nome, dados in dados_extraidos.items():
            df = self._para_dataframe(dados)
            if df.empty:
                continue
            df = df.copy()
            df.insert(0, "conjunto", nome)
            partes.append(df)

        if not partes:
            print("[CSV]   Nenhum dado para empilhar.")
            return None

        completo = pd.concat(partes, ignore_index=True, sort=False)
        completo.to_csv(caminho, index=False, encoding="utf-8-sig")
        print(f"[CSV]   Arquivo único salvo em: {caminho} "
              f"({len(completo)} linhas, {len(completo.columns)} colunas)")
        return caminho


def main():
    # 1) Extração (nada é modificado)
    dados_extraidos = GerenciadorExtracao().extrair_tudo()

    # 2) Carga individual em .json e .csv
    caminhos_gerados = Carregador().carregar_tudo(dados_extraidos)

    # 3) Arquivo final com TODOS os dados juntos
    print("\n=== Gerando arquivos finais ===")
    consolidador = ConsolidadorDados()
    consolidador.gerar_excel(dados_extraidos, caminhos_gerados)
    consolidador.gerar_json_unico(dados_extraidos)
    consolidador.gerar_csv_empilhado(dados_extraidos)

    print("\nPipeline concluído. Os arquivos completos estão na pasta "
          f"'{PASTA_FINAL}'.")


if __name__ == "__main__":
    main()