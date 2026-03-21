"""
PetroSafe Energia - Pipeline Silver (Transformação)
Sprint 3 - Governança e Medallion

Limpeza, padronização e validação dos dados Bronze → Silver.
Silver = dados limpos, padronizados e validados.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import structlog

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_settings
from src.utils.datalake import DataLakeClient
from src.utils.metadata import MetadataClient

logger = structlog.get_logger()


class SilverTransformPipeline:
    """
    Pipeline de transformação para a camada Silver.

    Responsabilidades:
    - Ler dados da camada Bronze
    - Limpar dados (remover duplicatas, tratar nulos, padronizar tipos)
    - Validar qualidade dos dados
    - Armazenar em formato Parquet no MinIO bucket 'silver'
    - Registrar metadados e linhagem
    """

    def __init__(self):
        self.datalake = DataLakeClient()
        self.metadata = MetadataClient()
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def transformar_csv(
        self,
        bronze_path: str,
        dataset_nome: str,
        versao: str = "1.0.0",
        regras_limpeza: Optional[dict] = None,
    ) -> dict:
        """Transforma dados CSV de Bronze para Silver."""
        logger.info("silver_inicio", bronze_path=bronze_path, dataset=dataset_nome)

        # Registrar execução
        exec_id = self.metadata.registrar_execucao_pipeline(
            pipeline_nome="transformacao_bronze_silver"
        )

        try:
            # Ler dados de Bronze
            raw_data = self.datalake.download("bronze", bronze_path)
            df = pd.read_csv(pd.io.common.BytesIO(raw_data))

            registros_originais = len(df)
            metricas = {"registros_originais": registros_originais}

            # ── Limpeza padrão ──────────────────────────────
            # 1. Remover duplicatas
            df = df.drop_duplicates()
            metricas["duplicatas_removidas"] = registros_originais - len(df)

            # 2. Padronizar nomes de colunas (snake_case, sem espaços)
            df.columns = (
                df.columns.str.strip()
                .str.lower()
                .str.replace(" ", "_")
                .str.replace("-", "_")
                .str.replace(r"[^\w]", "", regex=True)
            )

            # 3. Tratar valores nulos
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].str.strip()
                df[col] = df[col].replace({"": None, "N/A": None, "null": None, "NULL": None})

            # 4. Converter tipos quando possível
            for col in df.columns:
                # Tentar converter para numérico
                if df[col].dtype == "object":
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        pass

                # Tentar converter para datetime
                if df[col].dtype == "object":
                    try:
                        parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                        if parsed.notna().sum() / len(parsed) > 0.8:
                            df[col] = parsed
                    except (ValueError, TypeError):
                        pass

            # 5. Aplicar regras customizadas
            if regras_limpeza:
                df = self._aplicar_regras(df, regras_limpeza)

            # ── Validação de qualidade ──────────────────────
            qualidade = self._validar_qualidade(df)
            metricas["qualidade"] = qualidade

            registros_finais = len(df)
            metricas["registros_finais"] = registros_finais
            metricas["registros_rejeitados"] = registros_originais - registros_finais

            # ── Salvar em Silver (formato Parquet) ──────────
            parquet_buffer = df.to_parquet(index=False)
            nome_arquivo = Path(bronze_path).stem + ".parquet"
            silver_path = f"{dataset_nome}/{self.timestamp}/{nome_arquivo}"

            result = self.datalake.upload(
                camada="silver",
                path=silver_path,
                data=parquet_buffer,
                content_type="application/octet-stream",
                metadata={
                    "dataset": dataset_nome,
                    "versao": versao,
                    "formato": "parquet",
                    "bronze_origem": bronze_path,
                    "num_registros": str(registros_finais),
                    "colunas": ",".join(df.columns.tolist()),
                },
            )

            # Registrar versão Silver
            versao_id = self.metadata.registrar_versao_dataset(
                dataset_nome=dataset_nome,
                versao=versao,
                camada="silver",
                caminho_minio=f"silver/{silver_path}",
                minio_version_id=result.get("version_id"),
                tamanho_bytes=result["tamanho_bytes"],
                num_registros=registros_finais,
                checksum_md5=result["checksum_md5"],
                metadados_qualidade=metricas,
            )

            # Finalizar execução
            self.metadata.finalizar_execucao_pipeline(
                exec_id,
                status="sucesso",
                registros_processados=registros_finais,
                registros_rejeitados=metricas["registros_rejeitados"],
            )

            logger.info(
                "silver_concluido",
                dataset=dataset_nome,
                registros_in=registros_originais,
                registros_out=registros_finais,
            )

            return {
                "versao_id": versao_id,
                "silver_path": silver_path,
                "metricas": metricas,
                **result,
            }

        except Exception as e:
            self.metadata.finalizar_execucao_pipeline(
                exec_id, status="falha", erro_mensagem=str(e)
            )
            logger.error("silver_erro", erro=str(e))
            raise

    def _aplicar_regras(self, df: pd.DataFrame, regras: dict) -> pd.DataFrame:
        """Aplica regras de limpeza customizadas."""
        if "remover_colunas" in regras:
            df = df.drop(columns=regras["remover_colunas"], errors="ignore")

        if "renomear_colunas" in regras:
            df = df.rename(columns=regras["renomear_colunas"])

        if "filtros" in regras:
            for filtro in regras["filtros"]:
                col = filtro["coluna"]
                op = filtro["operador"]
                val = filtro["valor"]
                if op == "!=" and val is None:
                    df = df[df[col].notna()]
                elif op == ">":
                    df = df[df[col] > val]
                elif op == "<":
                    df = df[df[col] < val]

        return df

    def _validar_qualidade(self, df: pd.DataFrame) -> dict:
        """Calcula métricas de qualidade dos dados."""
        total = len(df)
        if total == 0:
            return {"total": 0, "score": 0}

        completude = 1 - (df.isnull().sum().sum() / (total * len(df.columns)))
        unicidade = df.nunique().sum() / (total * len(df.columns)) if len(df.columns) > 0 else 0

        return {
            "total_registros": total,
            "total_colunas": len(df.columns),
            "completude": round(completude * 100, 2),
            "nulos_por_coluna": df.isnull().sum().to_dict(),
            "score_qualidade": round(completude * 100, 1),
        }


# ── Execução direta ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Silver - Transformação")
    parser.add_argument("--bronze-path", required=True, help="Path no MinIO (camada bronze)")
    parser.add_argument("--dataset", required=True, help="Nome do dataset")
    parser.add_argument("--versao", default="1.0.0", help="Versão")
    args = parser.parse_args()

    pipeline = SilverTransformPipeline()
    result = pipeline.transformar_csv(args.bronze_path, args.dataset, args.versao)
    print(f"\n✓ Dados transformados para Silver")
    print(f"  Registros: {result['metricas']['registros_finais']}")
    print(f"  Qualidade: {result['metricas']['qualidade']['score_qualidade']}%")
