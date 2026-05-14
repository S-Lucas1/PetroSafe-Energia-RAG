"""
PetroSafe Energia - Pipeline de Embeddings
Sprint 5 - Chunking, geração de embeddings e indexação no Milvus
"""

import json
import sys
from pathlib import Path

import structlog

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.config import get_settings
from src.utils.datalake import DataLakeClient
from src.utils.embedding import EmbeddingClient
from src.utils.metadata import MetadataClient
from src.utils.milvus_client import MilvusClient

logger = structlog.get_logger()


class EmbeddingPipeline:
    """
    Pipeline Sprint 5: Gold (JSON) → chunks → embeddings (Ollama) → Milvus.
    """

    def __init__(self):
        settings = get_settings()
        self.datalake  = DataLakeClient()
        self.metadata  = MetadataClient()
        self.embedder  = EmbeddingClient(host=settings.ollama_host, model=settings.ollama_embedding_model)
        self.milvus    = MilvusClient(host=settings.milvus_host, port=settings.milvus_port)
        self.splitter  = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    def _localizar_documentos_rag(self) -> str:
        """Retorna o path do documentos_rag.json mais recente no bucket gold."""
        objetos = self.datalake.listar("gold")
        rag_objs = [o for o in objetos if "documentos_rag.json" in o["nome"]]
        if not rag_objs:
            raise FileNotFoundError("Nenhum documentos_rag.json no bucket gold")
        return sorted(rag_objs, key=lambda x: x.get("modificado", ""))[-1]["nome"]

    def run(self) -> dict:
        print("╔══════════════════════════════════════════════════╗")
        print("║   PetroSafe - Pipeline de Embeddings (Sprint 5) ║")
        print("╚══════════════════════════════════════════════════╝")

        rag_path = self._localizar_documentos_rag()
        print(f"\n📂 Documentos RAG: gold/{rag_path}")

        exec_embed = self.metadata.registrar_execucao_pipeline("embedding_gold")
        exec_index = self.metadata.registrar_execucao_pipeline("indexacao_milvus")

        try:
            # ── 1. Carregar documentos ──────────────────────────────
            raw       = self.datalake.download("gold", rag_path)
            documentos = json.loads(raw)
            print(f"   {len(documentos)} documentos carregados")

            # ── 2. Chunking ─────────────────────────────────────────
            chunks = []
            for doc in documentos:
                partes = self.splitter.split_text(doc["texto"])
                for i, parte in enumerate(partes):
                    chunk_id = f"{doc['id']}_chunk_{i}"
                    chunks.append({
                        "id":        chunk_id[:100],
                        "texto":     parte[:8000],
                        "dataset":   str(doc["metadata"].get("dataset", ""))[:200],
                        "classe":    str(doc["metadata"].get("nome_classe", ""))[:100],
                        "titulo":    str(doc["titulo"])[:500],
                    })
            print(f"   {len(chunks)} chunks após split (chunk_size=500, overlap=50)")

            # ── 3. Embeddings ───────────────────────────────────────
            print(f"\n🔢 Gerando embeddings com nomic-embed-text...")
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = self.embedder.generate(chunk["texto"])
                if (i + 1) % 5 == 0 or (i + 1) == len(chunks):
                    print(f"   {i+1}/{len(chunks)} embeddings gerados")

            self.metadata.finalizar_execucao_pipeline(
                exec_embed, status="sucesso", registros_processados=len(chunks)
            )

            # ── 4. Indexação no Milvus ──────────────────────────────
            print(f"\n📥 Indexando no Milvus...")
            self.milvus.connect()
            self.milvus.create_collection()
            self.milvus.insert(chunks)
            self.milvus.load()
            total = self.milvus.count()
            print(f"   ✓ {total} documentos na collection '{MilvusClient.COLLECTION_NAME}'")

            self.metadata.finalizar_execucao_pipeline(
                exec_index, status="sucesso", registros_processados=total
            )

            # ── 5. Teste de busca ───────────────────────────────────
            print(f"\n🔍 Teste de busca por similaridade:")
            test_emb = self.embedder.generate("falha no sensor de pressão de fundo")
            results  = self.milvus.search(test_emb, top_k=3)
            for hits in results:
                for hit in hits:
                    titulo = hit.entity.get("titulo", "")[:55]
                    print(f"   {hit.score:.4f} | {titulo}")

            print(f"\n✅ Pipeline de embeddings concluído!\n")
            return {"chunks_gerados": len(chunks), "indexados_milvus": total}

        except Exception as e:
            self.metadata.finalizar_execucao_pipeline(exec_embed, status="falha", erro_mensagem=str(e))
            self.metadata.finalizar_execucao_pipeline(exec_index, status="falha", erro_mensagem=str(e))
            logger.error("embedding_pipeline_erro", erro=str(e))
            raise


if __name__ == "__main__":
    pipeline = EmbeddingPipeline()
    pipeline.run()
