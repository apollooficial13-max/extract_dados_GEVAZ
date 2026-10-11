"""
Extract.py
----------
Camada de EXTRAÇÃO.

Regra deste módulo: NADA é modificado, filtrado, renomeado ou convertido.
Todas as colunas originais dos arquivos (nomes, ruas, quantidades, códigos,
coordenadas, etc.) são mantidas exatamente como vieram.

Erros de leitura NÃO são engolidos: se um arquivo falhar, o pipeline para
com a exceção original, em vez de terminar "com sucesso" com dados faltando.

A única coisa que o módulo FAZ é ACRESCENTAR colunas auxiliares, sem apagar
nada do que já existia:
    - arquivo_origem  : de qual pasta/arquivo aquela linha veio
    - caminho_origem  : caminho completo lido
    - crs_origem      : sistema de coordenadas original do shapefile
    - geometry_wkt    : a geometria em texto (WKT), para poder ser salva
    - tipo_geometria  : Point, Polygon, MultiPolygon, etc.
    - latitude/longitude : extraídas da geometria (ponto ou ponto interno)
"""

import glob
import os
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod

import geopandas as gpd
import pandas as pd


BASE_PADRAO = "Dados_extraidos"
DISTRITOS_SANITARIOS = range(1, 9)  # DS 1 a DS 8


def pastas_por_distrito(base: str, subpasta: str) -> list[str]:
    """Monta os caminhos '<base>/<subpasta>/DS N' para cada distrito sanitário."""
    return [f"{base}/{subpasta}/DS {i}" for i in DISTRITOS_SANITARIOS]


# ---------------------------------------------------------------------------
# Classe abstrata base
# ---------------------------------------------------------------------------
class ExtratorBase(ABC):
    """Toda fonte de dados extraída deve herdar daqui."""

    def __init__(self, nome: str) -> None:
        self.nome = nome                        # identificador único da fonte
        self.dados: pd.DataFrame | None = None  # DataFrame resultante

    @abstractmethod
    def extrair(self) -> pd.DataFrame:
        """Lê os dados brutos e preenche self.dados. Deve retornar self.dados."""
        raise NotImplementedError

    def __repr__(self) -> str:
        linhas = 0 if self.dados is None else len(self.dados)
        return f"<{self.__class__.__name__} nome='{self.nome}' linhas={linhas}>"


# ---------------------------------------------------------------------------
# Listagem de arquivos (equivalente a Explorar.py)
# ---------------------------------------------------------------------------
class ExtratorArquivos(ExtratorBase):
    """Lista, recursivamente, todos os arquivos de uma pasta."""

    def __init__(self, pasta: str = BASE_PADRAO, nome: str = "explorar") -> None:
        super().__init__(nome)
        self.pasta = pasta

    def extrair(self) -> pd.DataFrame:
        registros = []
        for pasta_atual, _subpastas, arquivos in os.walk(self.pasta):
            for nome_arquivo in arquivos:
                caminho = os.path.join(pasta_atual, nome_arquivo)
                registros.append({
                    "caminho": caminho,
                    "pasta": pasta_atual,
                    "arquivo": nome_arquivo,
                    "extensao": os.path.splitext(nome_arquivo)[1].lower(),
                })

        self.dados = pd.DataFrame(registros)
        print(f"[{self.nome}] {len(self.dados)} arquivo(s) encontrado(s)")
        return self.dados


# ---------------------------------------------------------------------------
# Shapefiles (BDS, Estações, Ovitrampas)
# ---------------------------------------------------------------------------
class ExtratorShapefile(ExtratorBase):
    """
    Lê um ou vários shapefiles e mantém TODAS as colunas originais.
    Acrescenta apenas colunas auxiliares de origem e de coordenadas.
    """

    # usado só para gerar latitude/longitude em graus;
    # as colunas originais não são alteradas
    CRS_SAIDA = "EPSG:4326"

    def __init__(self, nome: str, caminhos: str | list[str]) -> None:
        super().__init__(nome)
        self.caminhos = [caminhos] if isinstance(caminhos, str) else list(caminhos)

    def _acrescentar_coordenadas(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Cria geometry_wkt, tipo_geometria, latitude e longitude sem alterar nada."""
        gdf["geometry_wkt"] = gdf.geometry.to_wkt()
        gdf["tipo_geometria"] = gdf.geometry.geom_type

        gdf_geo = gdf.to_crs(self.CRS_SAIDA) if gdf.crs is not None else gdf

        # ponto representativo: para Point é o próprio ponto;
        # para polígonos, um ponto garantidamente dentro da área
        pontos = gdf_geo.geometry.representative_point()
        gdf["longitude"] = pontos.x
        gdf["latitude"] = pontos.y

        return gdf

    def extrair(self) -> pd.DataFrame:
        partes = []
        for caminho in self.caminhos:
            gdf = gpd.read_file(caminho)
            gdf["arquivo_origem"] = os.path.basename(caminho.rstrip("/\\"))
            gdf["caminho_origem"] = caminho
            gdf["crs_origem"] = str(gdf.crs)

            gdf = self._acrescentar_coordenadas(gdf)

            # vira DataFrame comum; a geometria fica preservada em geometry_wkt
            df = pd.DataFrame(gdf.drop(columns="geometry"))
            partes.append(df)

            print(f"[{self.nome}] Lido: {caminho} "
                  f"({len(df)} linhas, {len(df.columns)} colunas)")
            print(f"           colunas: {list(df.columns)}")

        # sort=False preserva a ordem; colunas que existem só em alguns
        # arquivos são todas mantidas (ficam vazias onde não existiam)
        self.dados = (
            pd.concat(partes, ignore_index=True, sort=False) if partes else pd.DataFrame()
        )
        return self.dados


# ---------------------------------------------------------------------------
# XML (metadados dos Distritos Sanitários)
# ---------------------------------------------------------------------------
class ExtratorXML(ExtratorBase):
    """Lê vários XMLs elemento a elemento, preservando tag, texto e atributos."""

    def __init__(self, nome: str, padrao_glob: str) -> None:
        super().__init__(nome)
        self.padrao_glob = padrao_glob

    def extrair(self) -> pd.DataFrame:
        registros = []
        for arquivo in glob.glob(self.padrao_glob):
            raiz = ET.parse(arquivo).getroot()
            for elem in raiz.iter():
                registros.append({
                    "arquivo": os.path.basename(arquivo),
                    "caminho_origem": arquivo,
                    "tag": elem.tag,
                    "texto": elem.text if elem.text is not None else "",
                    "atributos": str(elem.attrib),
                })
            print(f"[{self.nome}] Lido: {arquivo}")

        self.dados = pd.DataFrame(registros)
        return self.dados


# ---------------------------------------------------------------------------
# Extratores específicos de cada fonte
# ---------------------------------------------------------------------------
class ExtratorBDS(ExtratorShapefile):
    """Base de Distritos Sanitários."""

    def __init__(self, base: str = BASE_PADRAO) -> None:
        super().__init__(
            nome="bds",
            caminhos=f"{base}/BASE Distritos sanitários shapefile/",
        )


class ExtratorEstacoesDisseminadoras(ExtratorShapefile):
    """Estações Disseminadoras (DS 1 a DS 8)."""

    def __init__(self, base: str = BASE_PADRAO) -> None:
        super().__init__(
            nome="estacoes_disseminadoras",
            caminhos=pastas_por_distrito(base, "ESTAÇÕES DISSEMINADORAS shapefile"),
        )


class ExtratorOvitrampas2026(ExtratorShapefile):
    """Atualização total das Ovitrampas 2026 (DS 1 a DS 8)."""

    def __init__(self, base: str = BASE_PADRAO) -> None:
        super().__init__(
            nome="ovitrampas_2026",
            caminhos=pastas_por_distrito(
                base, "ATUALIZAÇÃO TOTAL DAS OVITRAMPAS 2026 shapefile"
            ),
        )


class ExtratorDistritosSanitariosXML(ExtratorXML):
    """XMLs de metadado dos Distritos Sanitários (*.shp.xml)."""

    def __init__(self, base: str = BASE_PADRAO) -> None:
        super().__init__(
            nome="distritos_sanitarios_xml",
            padrao_glob=f"{base}/BASE Distritos sanitários shapefile/*.shp.xml",
        )


# ---------------------------------------------------------------------------
# Gerenciador
# ---------------------------------------------------------------------------
class GerenciadorExtracao:
    """Executa todos os extratores e devolve {nome: DataFrame}."""

    def __init__(self, base: str = BASE_PADRAO) -> None:
        self.base = base
        self.extratores = [
            ExtratorArquivos(pasta=base),
            ExtratorBDS(base=base),
            ExtratorEstacoesDisseminadoras(base=base),
            ExtratorOvitrampas2026(base=base),
            ExtratorDistritosSanitariosXML(base=base),
        ]

    def adicionar(self, extrator: ExtratorBase) -> "GerenciadorExtracao":
        self.extratores.append(extrator)
        return self

    def extrair_tudo(self) -> dict[str, pd.DataFrame]:
        resultado = {}
        for extrator in self.extratores:
            print(f"\n=== Extraindo: {extrator.nome} ===")
            resultado[extrator.nome] = extrator.extrair()
        return resultado


if __name__ == "__main__":
    dados = GerenciadorExtracao().extrair_tudo()
    for nome, df in dados.items():
        print(f"\n{nome}: {len(df)} linhas | colunas: {list(df.columns)}")