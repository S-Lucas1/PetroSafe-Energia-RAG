"""
PetroSafe Energia - Pipeline de Treinamento de Modelos
Sprint 4 - Modelagem e Treinamento (ML + MLflow)

Classificação multiclasse de falhas em poços de petróleo (dataset 3W Petrobras).
Features: 7 sensores (P-PDG, P-TPT, T-TPT, P-MON-CKP, T-JUS-CKP, P-JUS-CKGL, QGL)
Target: 9 classes (0=Normal, 1-8=tipos de falha)
"""

import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "petrosafe"
os.environ["AWS_SECRET_ACCESS_KEY"] = "petrosafe123"
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import mlflow
import mlflow.sklearn
import mlflow.xgboost

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ── Configurações ──────────────────────────────────────────
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


def carregar_dados(path: Path) -> pd.DataFrame:
    """Carrega CSV e remove coluna timestamp."""
    print(f"📂 Carregando dados de {path}...")
    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        df = df.drop(columns=["timestamp"])
    print(f"   Shape: {df.shape}")
    print(f"   Colunas: {list(df.columns)}")
    return df


def preparar_dados(df: pd.DataFrame) -> tuple:
    """Trata nulos, separa features/target e faz split treino/teste."""
    print("\n🔧 Preparando dados...")

    nulos_antes = df.isnull().sum().sum()
    df = df.dropna()
    nulos_removidos = nulos_antes
    print(f"   Nulos removidos: {nulos_removidos}")
    print(f"   Registros após limpeza: {len(df)}")

    X = df.drop(columns=["class"])
    y = df["class"]

    print(f"\n📊 Distribuição das classes:")
    for cls, count in y.value_counts().sort_index().items():
        nome = CLASSES.get(cls, f"Classe {cls}")
        print(f"   {cls} ({nome}): {count} ({count/len(y)*100:.1f}%)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"\n   Treino: {X_train.shape[0]} amostras")
    print(f"   Teste:  {X_test.shape[0]} amostras")

    return X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, scaler


def salvar_matriz_confusao(y_true, y_pred, model_name: str, output_dir: Path) -> Path:
    """Gera e salva matriz de confusão como PNG."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred)
    labels = sorted(y_true.unique())

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
    )
    ax.set_xlabel("Predito")
    ax.set_ylabel("Real")
    ax.set_title(f"Matriz de Confusão - {model_name}")
    plt.tight_layout()

    filepath = output_dir / f"confusion_matrix_{model_name.lower().replace(' ', '_')}.png"
    fig.savefig(filepath, dpi=150)
    plt.close(fig)
    return filepath


def salvar_classification_report(y_true, y_pred, model_name: str, output_dir: Path) -> Path:
    """Salva classification report como TXT."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = classification_report(y_true, y_pred)
    filepath = output_dir / f"classification_report_{model_name.lower().replace(' ', '_')}.txt"
    filepath.write_text(f"Classification Report - {model_name}\n{'='*60}\n\n{report}")
    return filepath


def definir_modelos() -> dict:
    """Define os 3 modelos a serem comparados."""
    return {
        "Logistic Regression": {
            "model": LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                solver="lbfgs",
                random_state=42,
            ),
            "params": {
                "max_iter": 1000,
                "class_weight": "balanced",
                "solver": "lbfgs",
            },
            "usa_scaled": True,
            "log_fn": mlflow.sklearn.log_model,
        },
        "Random Forest": {
            "model": RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
            "params": {
                "n_estimators": 200,
                "max_depth": 15,
                "class_weight": "balanced",
            },
            "usa_scaled": False,
            "log_fn": mlflow.sklearn.log_model,
        },
        "XGBoost": {
            "model": xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                tree_method="hist",
                device="cpu",
                n_jobs=1,
                random_state=42,
                eval_metric="mlogloss",
            ),
            "params": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "tree_method": "hist",
            },
            "usa_scaled": False,
            "log_fn": mlflow.sklearn.log_model,
        },
    }


def treinar_e_avaliar(
    nome: str,
    config: dict,
    X_train, X_test, y_train, y_test,
    X_train_scaled, X_test_scaled,
    artifacts_dir: Path,
) -> dict:
    """Treina um modelo, calcula métricas e registra no MLflow."""
    print(f"\n{'='*60}")
    print(f"🚀 Treinando: {nome}")
    print(f"{'='*60}")

    model = config["model"]
    X_tr = X_train_scaled if config["usa_scaled"] else X_train
    X_te = X_test_scaled if config["usa_scaled"] else X_test

    with mlflow.start_run(run_name=nome) as run:
        # Logar parâmetros
        mlflow.log_params(config["params"])
        mlflow.set_tag("model_type", nome)

        # Treinar
        model.fit(X_tr, y_train)

        # Predições
        y_pred = model.predict(X_te)

        # Métricas
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
        prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_test, y_pred, average="macro", zero_division=0)

        print(f"   Accuracy:  {acc:.4f}")
        print(f"   F1 (macro): {f1:.4f}")
        print(f"   Precision:  {prec:.4f}")
        print(f"   Recall:     {rec:.4f}")

        # Logar métricas
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_macro", f1)
        mlflow.log_metric("precision_macro", prec)
        mlflow.log_metric("recall_macro", rec)

        # Gerar e logar artefatos
        cm_path = salvar_matriz_confusao(y_test, y_pred, nome, artifacts_dir)
        cr_path = salvar_classification_report(y_test, y_pred, nome, artifacts_dir)

        mlflow.log_artifact(str(cm_path))
        mlflow.log_artifact(str(cr_path))

        # Logar modelo
        artifact_name = nome.lower().replace(" ", "_") + "_model"
        config["log_fn"](model, artifact_path=artifact_name)

        return {
            "nome": nome,
            "run_id": run.info.run_id,
            "accuracy": acc,
            "f1_macro": f1,
            "precision_macro": prec,
            "recall_macro": rec,
        }


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║   PetroSafe Energia - Treinamento de Modelos    ║")
    print("║   Sprint 4 - Classificação de Falhas            ║")
    print("╚══════════════════════════════════════════════════╝")

    # Configurar MLflow
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    mlflow.set_experiment(EXPERIMENT_NAME)
    print(f"\n📡 MLflow Tracking: {os.environ['MLFLOW_TRACKING_URI']}")
    print(f"📋 Experimento: {EXPERIMENT_NAME}")

    # Carregar e preparar dados
    df = carregar_dados(DATA_PATH)
    X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, scaler = preparar_dados(df)

    # Definir modelos
    modelos = definir_modelos()
    artifacts_dir = ARTIFACTS_DIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Treinar e avaliar cada modelo
    resultados = []
    for nome, config in modelos.items():
        resultado = treinar_e_avaliar(
            nome, config,
            X_train, X_test, y_train, y_test,
            X_train_scaled, X_test_scaled,
            artifacts_dir,
        )
        resultados.append(resultado)

    # ── Comparação dos modelos ─────────────────────────────
    print(f"\n{'='*60}")
    print("📊 COMPARAÇÃO DOS MODELOS")
    print(f"{'='*60}")
    print(f"{'Modelo':<25} {'Accuracy':>10} {'F1 Macro':>10} {'Precision':>10} {'Recall':>10}")
    print("-" * 65)
    for r in resultados:
        print(f"{r['nome']:<25} {r['accuracy']:>10.4f} {r['f1_macro']:>10.4f} {r['precision_macro']:>10.4f} {r['recall_macro']:>10.4f}")

    # Melhor modelo por F1-Score macro
    melhor = max(resultados, key=lambda x: x["f1_macro"])
    print(f"\n🏆 Melhor modelo: {melhor['nome']} (F1 macro = {melhor['f1_macro']:.4f})")

    # Registrar comparação no MLflow
    with mlflow.start_run(run_name="Comparacao_Modelos"):
        for r in resultados:
            mlflow.log_metric(f"{r['nome']}_f1_macro", r["f1_macro"])
            mlflow.log_metric(f"{r['nome']}_accuracy", r["accuracy"])
        mlflow.set_tag("melhor_modelo", melhor["nome"])
        mlflow.log_metric("melhor_f1_macro", melhor["f1_macro"])

        # Salvar resumo
        resumo_path = artifacts_dir / "comparacao_modelos.json"
        resumo_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
        mlflow.log_artifact(str(resumo_path))

    print(f"\n✅ Treinamento concluído! Verifique os experimentos em http://localhost:5000")
    print(f"   Experimento: {EXPERIMENT_NAME}")


if __name__ == "__main__":
    main()
