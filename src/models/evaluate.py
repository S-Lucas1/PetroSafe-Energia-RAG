"""
PetroSafe Energia - Avaliação do Melhor Modelo
Sprint 4 - Modelagem e Treinamento (ML + MLflow)

Carrega o melhor modelo registrado no MLflow e avalia em dados de teste.
"""

import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "petrosafe"
os.environ["AWS_SECRET_ACCESS_KEY"] = "petrosafe123"
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.pyfunc

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "poco_A1_sensores.csv"
EXPERIMENT_NAME = "petrosafe-classificacao-falhas"
ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "artifacts"

CLASSES = {
    0: "Normal",
    1: "Falha BSW",
    2: "Falha Incrust.",
    3: "Falha Corrosão",
    4: "Falha Hidratos",
    5: "Falha Perda Circ.",
    6: "Falha Produtiv.",
    7: "Falha Interfer.",
    8: "Falha Severa",
}


def buscar_melhor_run() -> dict:
    """Busca o melhor run do experimento no MLflow (por F1 macro)."""
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    client = mlflow.tracking.MlflowClient()

    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        raise ValueError(f"Experimento '{EXPERIMENT_NAME}' não encontrado no MLflow. Execute train.py primeiro.")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="tags.model_type != ''",
        order_by=["metrics.f1_macro DESC"],
        max_results=1,
    )

    if not runs:
        raise ValueError("Nenhum run encontrado. Execute train.py primeiro.")

    best_run = runs[0]
    model_type = best_run.data.tags.get("model_type", "unknown")
    artifact_name = model_type.lower().replace(" ", "_") + "_model"

    return {
        "run_id": best_run.info.run_id,
        "model_type": model_type,
        "artifact_uri": f"runs:/{best_run.info.run_id}/{artifact_name}",
        "metrics": best_run.data.metrics,
    }


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║   PetroSafe Energia - Avaliação do Modelo       ║")
    print("║   Sprint 4 - Classificação de Falhas            ║")
    print("╚══════════════════════════════════════════════════╝")

    # Buscar melhor modelo
    print("\n🔍 Buscando melhor modelo no MLflow...")
    best = buscar_melhor_run()
    print(f"   Modelo: {best['model_type']}")
    print(f"   Run ID: {best['run_id']}")
    print(f"   F1 Macro: {best['metrics'].get('f1_macro', 'N/A'):.4f}")
    print(f"   Accuracy: {best['metrics'].get('accuracy', 'N/A'):.4f}")

    # Carregar modelo
    print(f"\n📦 Carregando modelo: {best['artifact_uri']}...")
    model = mlflow.pyfunc.load_model(best["artifact_uri"])
    print("   ✓ Modelo carregado")

    # Preparar dados de teste
    print("\n📂 Carregando dados de teste...")
    df = pd.read_csv(DATA_PATH)
    if "timestamp" in df.columns:
        df = df.drop(columns=["timestamp"])
    df = df.dropna()

    X = df.drop(columns=["class"])
    y = df["class"]

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Escalar se for Logistic Regression
    if best["model_type"] == "Logistic Regression":
        X_train_full, _, _, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        scaler = StandardScaler()
        scaler.fit(X_train_full)
        X_test_input = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns, index=X_test.index)
    else:
        X_test_input = X_test

    # Predições
    print("\n🔮 Executando predições...")
    y_pred = model.predict(X_test_input)
    if hasattr(y_pred, 'values'):
        y_pred = y_pred.values.flatten()
    y_pred = np.array(y_pred).astype(int)

    # Classification Report
    print(f"\n{'='*60}")
    print("📋 CLASSIFICATION REPORT")
    print(f"{'='*60}")
    report = classification_report(y_test, y_pred, zero_division=0)
    print(report)

    # Matriz de Confusão
    cm = confusion_matrix(y_test, y_pred)
    labels = sorted(y_test.unique())

    print(f"\n{'='*60}")
    print("📊 MATRIZ DE CONFUSÃO")
    print(f"{'='*60}")
    print(pd.DataFrame(cm, index=labels, columns=labels))

    # Salvar visualização
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel("Predito")
    ax.set_ylabel("Real")
    ax.set_title(f"Avaliação - Melhor Modelo: {best['model_type']}")
    plt.tight_layout()

    eval_path = ARTIFACTS_DIR / "avaliacao_melhor_modelo.png"
    fig.savefig(eval_path, dpi=150)
    plt.close(fig)
    print(f"\n💾 Matriz de confusão salva em: {eval_path}")

    # Resumo
    print(f"\n{'='*60}")
    print("✅ AVALIAÇÃO CONCLUÍDA")
    print(f"{'='*60}")
    print(f"   Melhor Modelo: {best['model_type']}")
    print(f"   Run ID: {best['run_id']}")
    print(f"   Métricas do treino:")
    for k, v in best["metrics"].items():
        print(f"     {k}: {v:.4f}")


if __name__ == "__main__":
    main()
