"""
PetroSafe Energia - CLI para consultas RAG
Sprint 6 - Interface de linha de comando

Uso:
  python3 -m src.pipelines.rag_query "Quais falhas BSW foram detectadas?"
  python3 -m src.pipelines.rag_query          # modo interativo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipelines.rag_pipeline import RAGPipeline


def responder(pipeline: RAGPipeline, pergunta: str):
    print(f"\n{'='*60}")
    print(f"❓ PERGUNTA: {pergunta}")
    print(f"{'='*60}")
    print("⏳ Consultando RAG...")

    result = pipeline.query(pergunta)

    print(f"\n📝 RESPOSTA:")
    print(result["resposta"])

    print(f"\n📚 FONTES ({len(result['fontes'])}):")
    for f in result["fontes"]:
        print(f"   [{f['score']:.4f}] {f['titulo'][:70]}")

    print(
        f"\n⏱  retrieval={result['tempo_retrieval_ms']}ms | "
        f"geração={result['tempo_geracao_ms']}ms | "
        f"total={result['total_ms']}ms"
    )


if __name__ == "__main__":
    pipeline = RAGPipeline()

    if len(sys.argv) > 1:
        # Modo argumento: python3 -m src.pipelines.rag_query "pergunta"
        responder(pipeline, " ".join(sys.argv[1:]))
    else:
        # Modo interativo
        print("╔══════════════════════════════════════════════════╗")
        print("║   PetroSafe Energia — RAG Query (Sprint 6)      ║")
        print("║   Digite 'sair' para encerrar                   ║")
        print("╚══════════════════════════════════════════════════╝")
        while True:
            try:
                pergunta = input("\n❓ Pergunta: ").strip()
                if pergunta.lower() in ("sair", "exit", "quit", ""):
                    break
                responder(pipeline, pergunta)
            except (KeyboardInterrupt, EOFError):
                break
        print("\n👋 Até logo!")
