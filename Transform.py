"""
Transform.py
------------
Camada de TRANSFORMAÇÃO: prepara os DataFrames extraídos (Extract.py) para
serialização e os consolida em arquivos únicos, em Dados_Gevaz_Gerais/:

    - dados_completos.xlsx -> uma aba por conjunto + aba "resumo"
    - dados_completos.json -> tudo junto em um único JSON
    - dados_completos.csv  -> conjuntos empilhados (coluna "conjunto")

Nenhum valor das colunas originais é alterado.
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def preparar_dataframe(dados: pd.DataFrame | None) -> pd.DataFrame:
    """
    Devolve um DataFrame comum do pandas, seguro para serializar.

    - None vira DataFrame vazio.
    - Se existir a coluna 'geometry' (GeoDataFrame), ela é convertida para WKT,
      pois objetos de geometria não são serializáveis em JSON/CSV.

    Função única usada pelo Consolidador e pelo Carregador (Load.py).
    """
    if dados is None:
        return pd.DataFrame()

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
