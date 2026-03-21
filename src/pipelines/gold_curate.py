"""
PetroSafe Energia - Pipeline Gold (Curadoria)
Sprint 3 - Governança e Medallion

Enriquecimento e preparação dos dados Silver → Gold.
Gold = dados prontos para consumo, enriquecidos e otimizados para o RAG.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import structlog

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_settings
from src.utils.datalake import DataLakeClient
from src.utils.metadata import MetadataClient

logger = structlog.get_logger()


class GoldCuratePipeline:
    """
    Pipeline de curadoria para a camada Gold.

    Responsabilidades:
    - Ler dados da camada Silver
    - Enriquecer com campos calculados e agregações
    - Preparar documentos para o pipeline RAG (chunking-ready)
    - Armazenar no MinIO bucket 'gold' em formato otimizado
    - Registrar metadados e linhagem
    """

    def __init__(self):
        self.datalake = DataLakeClient()
        self.metadata = MetadataClient()
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def curar_dados_sensores(
        self,
        silver_path: str,
        dataset_nome: str,
        versao: str = "1.0.0",
    ) -> dict:
        """Cura dados de sensores para análise e RAG."""
        logger.info("gold_sensores_inicio", silver_path=silver_path)

        exec_id = self.metadata.registrar_execucao_pipeline(
            pipeline_nome="curadoria_silver_gold"
        )

        try:
            # Ler dados Silver
            raw_data = self.datalake.download("silver", silver_path)
            df = pd.read_parquet(pd.io.common.BytesIO(raw_data))

            # ── Enriquecimento ──────────────────────────────
            # Identificar colunas de sensores (numéricas)
            sensor_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
            if "class" in sensor_cols:
                sensor_cols.remove("class")

            # Estatísticas agregadas por evento/classe
            if "class" in df.columns:
                stats = df.groupby("class")[sensor_cols].agg(["mean", "std", "min", "max"])
                stats.columns = ["_".join(col) for col in stats.columns]

                # Salvar estatísticas como Gold
                stats_json = stats.reset_index().to_json(orient="records", force_ascii=False)
                stats_path = f"{dataset_nome}/{self.timestamp}/estatisticas_por_classe.json"
                self.datalake.upload(
                    camada="gold",
                    path=stats_path,
                    data=stats_json.encode("utf-8"),
                    content_type="application/json",
                )

            # ── Preparar documentos para RAG ────────────────
            documentos = self._gerar_documentos_rag(df, dataset_nome, sensor_cols)

            docs_path = f"{dataset_nome}/{self.timestamp}/documentos_rag.json"
            docs_json = json.dumps(documentos, ensure_ascii=False, indent=2)

            result = self.datalake.upload(
                camada="gold",
                path=docs_path,
                data=docs_json.encode("utf-8"),
                content_type="application/json",
                metadata={
                    "dataset": dataset_nome,
                    "versao": versao,
                    "tipo": "documentos_rag",
                    "num_documentos": str(len(documentos)),
                },
            )

            versao_id = self.metadata.registrar_versao_dataset(
                dataset_nome=dataset_nome,
                versao=versao,
                camada="gold",
                caminho_minio=f"gold/{docs_path}",
                minio_version_id=result.get("version_id"),
                tamanho_bytes=result["tamanho_bytes"],
                num_registros=len(documentos),
                checksum_md5=result["checksum_md5"],
            )

            self.metadata.finalizar_execucao_pipeline(
                exec_id,
                status="sucesso",
                registros_processados=len(documentos),
            )

            logger.info(
                "gold_concluido",
                dataset=dataset_nome,
                documentos_gerados=len(documentos),
            )

            return {
                "versao_id": versao_id,
                "gold_path": docs_path,
                "num_documentos": len(documentos),
                **result,
            }

        except Exception as e:
            self.metadata.finalizar_execucao_pipeline(
                exec_id, status="falha", erro_mensagem=str(e)
            )
            raise

    def _gerar_documentos_rag(
        self, df: pd.DataFrame, dataset_nome: str, sensor_cols: list
    ) -> list[dict]:
        """
        Gera documentos textuais estruturados para o pipeline RAG.
        Cada documento representa um evento ou grupo de dados.
        """
        documentos = []

        if "class" in df.columns:
            # Mapeamento de classes do dataset 3W
            classes_3w = {
                0: "Normal",
                1: "Falha Abrupta na BSW",
                2: "Falha Incipiente na BSW",
                3: "Falha por Instabilidade Severa",
                4: "Falha por Perda de Produção",
                5: "Rápido Aumento de Produtividade",
                6: "Rápido Decréscimo de Produtividade",
                7: "Falha no Sensor de Pressão de Fundo (P-PDG)",
                8: "Falha no Sensor de Pressão (P-TPT)",
            }

            for classe, grupo in df.groupby("class"):
                nome_classe = classes_3w.get(int(classe), f"Classe {classe}")

                # Calcular estatísticas do grupo
                stats = {}
                for col in sensor_cols:
                    if col in grupo.columns:
                        stats[col] = {
                            "media": round(grupo[col].mean(), 4),
                            "desvio": round(grupo[col].std(), 4),
                            "min": round(grupo[col].min(), 4),
                            "max": round(grupo[col].max(), 4),
                        }

                # Gerar texto descritivo para embedding
                texto = self._gerar_texto_evento(nome_classe, stats, len(grupo))

                documentos.append({
                    "id": f"{dataset_nome}_classe_{int(classe)}",
                    "titulo": f"Análise de Evento: {nome_classe}",
                    "texto": texto,
                    "metadata": {
                        "dataset": dataset_nome,
                        "classe": int(classe),
                        "nome_classe": nome_classe,
                        "num_amostras": len(grupo),
                        "sensores": sensor_cols,
                    },
                })
        else:
            # Para dados sem classificação, criar documento resumo
            texto = f"Dataset {dataset_nome} com {len(df)} registros e {len(df.columns)} colunas."
            documentos.append({
                "id": f"{dataset_nome}_resumo",
                "titulo": f"Resumo do Dataset: {dataset_nome}",
                "texto": texto,
                "metadata": {"dataset": dataset_nome, "num_registros": len(df)},
            })

        return documentos

    def _gerar_texto_evento(self, nome_classe: str, stats: dict, num_amostras: int) -> str:
        """Gera texto descritivo de um evento para embedding."""
        linhas = [
            f"Tipo de Evento: {nome_classe}",
            f"Total de amostras analisadas: {num_amostras}",
            "",
            "Análise dos Sensores:",
        ]

        sensores_nomes = {
            "p_pdg": "Pressão de Fundo (P-PDG)",
            "p_tpt": "Pressão do Tubing (P-TPT)",
            "t_tpt": "Temperatura do Tubing (T-TPT)",
            "p_mon_ckp": "Pressão Montante Choke (P-MON-CKP)",
            "t_jus_ckp": "Temperatura Jusante Choke (T-JUS-CKP)",
            "p_jus_ckgl": "Pressão Jusante Choke GL (P-JUS-CKGL)",
            "qgl": "Vazão de Gas Lift (QGL)",
        }

        for sensor, vals in stats.items():
            nome = sensores_nomes.get(sensor, sensor)
            linhas.append(
                f"  - {nome}: média={vals['media']}, "
                f"desvio={vals['desvio']}, "
                f"faixa=[{vals['min']}, {vals['max']}]"
            )

        if "falha" in nome_classe.lower():
            linhas.extend([
                "",
                "Recomendação: Este tipo de evento requer atenção imediata da equipe de manutenção.",
                "Verificar procedimentos operacionais padrão (SOP) correspondentes.",
            ])

        return "\n".join(linhas)


# ── Execução direta ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Gold - Curadoria")
    parser.add_argument("--silver-path", required=True, help="Path no MinIO (camada silver)")
    parser.add_argument("--dataset", required=True, help="Nome do dataset")
    parser.add_argument("--versao", default="1.0.0", help="Versão")
    args = parser.parse_args()

    pipeline = GoldCuratePipeline()
    result = pipeline.curar_dados_sensores(args.silver_path, args.dataset, args.versao)
    print(f"\n✓ Dados curados para Gold")
    print(f"  Documentos RAG gerados: {result['num_documentos']}")
