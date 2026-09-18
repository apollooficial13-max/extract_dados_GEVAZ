"""
Main.py
-------
Ponto único de execução do pipeline:

    1) Extrai TODOS os dados, sem modificar nada (Extract.py)
    2) Salva cada conjunto em .json e .csv (Load.py)
    3) Gera arquivos finais com todos os dados juntos, em Dados_Gevaz_Gerais/:
         - dados_completos.xlsx -> uma aba por conjunto + aba "resumo"
         - dados_completos.json -> tudo junto em um único JSON
         - dados_completos.csv  -> conjuntos empilhados (coluna "conjunto")
       (é esse arquivo que você usa depois para enviar ao banco de dados)

Uso:
    python Main.py
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from Extract import GerenciadorExtracao
from Load import Carregador, preparar_dataframe

PASTA_FINAL = "Dados_Gevaz_Gerais"
LIMITE_NOME_ABA = 31  # limite do Excel para nome de aba


class ConsolidadorDados:
    """
    Junta todos os conjuntos extraídos em arquivos únicos,
    sem alterar nenhum valor das colunas originais.
    """

    def __init__(self, pasta: str = PASTA_FINAL) -> None:
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _montar_resumo(
        dados_extraidos: dict[str, pd.DataFrame],
        caminhos_gerados: dict[str, dict[str, Path | None]],
    ) -> pd.DataFrame:
        data_extracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linhas = []
        for nome, dados in dados_extraidos.items():
            df = preparar_dataframe(dados)
            caminhos = caminhos_gerados.get(nome, {})
            linhas.append({
                "dado": nome,
                "linhas": len(df),
                "colunas": len(df.columns),
                "nomes_colunas": ", ".join(map(str, df.columns)),
                "arquivo_json": str(caminhos.get("json") or ""),
                "arquivo_csv": str(caminhos.get("csv") or ""),
                "data_extracao": data_extracao,
            })
        return pd.DataFrame(linhas)

    def gerar_excel(
        self,
        dados_extraidos: dict[str, pd.DataFrame],
        caminhos_gerados: dict[str, dict[str, Path | None]],
    ) -> Path:
        """Planilha única: uma aba por conjunto de dados + uma aba de resumo."""
        caminho = self.pasta / "dados_completos.xlsx"

        with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
            resumo = self._montar_resumo(dados_extraidos, caminhos_gerados)
            resumo.to_excel(writer, sheet_name="resumo", index=False)

            for nome, dados in dados_extraidos.items():
                df = preparar_dataframe(dados)
                if df.empty:
                    continue
                aba = str(nome)[:LIMITE_NOME_ABA]
                df.to_excel(writer, sheet_name=aba, index=False)
                print(f"[Excel] Aba '{aba}': {len(df)} linhas, {len(df.columns)} colunas")

        print(f"\n[Excel] Planilha completa salva em: {caminho}")
        return caminho

    def gerar_json_unico(self, dados_extraidos: dict[str, pd.DataFrame]) -> Path:
        """Um único JSON com todos os conjuntos, pronto para ir ao banco depois."""
        caminho = self.pasta / "dados_completos.json"

        # to_json + loads converte NaN em null antes de gravar o arquivo único
        conteudo = {
            nome: json.loads(
                preparar_dataframe(dados).to_json(orient="records", force_ascii=False)
            )
            for nome, dados in dados_extraidos.items()
        }

        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)

        print(f"[JSON]  Arquivo único salvo em: {caminho}")
        return caminho

    def gerar_csv_empilhado(self, dados_extraidos: dict[str, pd.DataFrame]) -> Path | None:
        """
        CSV único com todos os conjuntos empilhados, identificados
        pela coluna 'conjunto'. Nenhum valor é alterado.
        """
        caminho = self.pasta / "dados_completos.csv"

        partes = []
        for nome, dados in dados_extraidos.items():
            df = preparar_dataframe(dados)
            if df.empty:
                continue
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
