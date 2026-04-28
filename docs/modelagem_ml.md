# Modelagem de ML - PetroSafe Energia

## Sprint 4 - Classificação de Falhas em Poços de Petróleo

---

## 1. Definição do Problema

**Tipo:** Classificação multiclasse supervisionada

**Objetivo:** Classificar automaticamente o estado operacional de poços de petróleo a partir de dados de sensores, identificando o tipo de falha (se houver) em tempo real.

**Dataset:** 3W Petrobras (versão sintética) — 500 registros

---

## 2. Features (Variáveis de Entrada)

7 sensores industriais do poço:

| Feature      | Descrição                        | Unidade |
|-------------|----------------------------------|---------|
| P-PDG       | Pressão no PDG                   | kgf/cm² |
| P-TPT       | Pressão no TPT                   | kgf/cm² |
| T-TPT       | Temperatura no TPT               | °C      |
| P-MON-CKP   | Pressão a montante do choke      | kgf/cm² |
| T-JUS-CKP   | Temperatura a jusante do choke   | °C      |
| P-JUS-CKGL  | Pressão a jusante da choke GL    | kgf/cm² |
| QGL         | Vazão de gás lift                | m³/d    |

---

## 3. Target (Variável Alvo)

9 classes — operação normal + 8 tipos de falha:

| Classe | Descrição                |
|--------|--------------------------|
| 0      | Normal                   |
| 1      | Falha BSW                |
| 2      | Falha Incrustação        |
| 3      | Falha Corrosão           |
| 4      | Falha Hidratos           |
| 5      | Falha Perda de Circulação|
| 6      | Falha Produtividade      |
| 7      | Falha Interferência      |
| 8      | Falha Severa             |

---

## 4. Métricas de Avaliação

### Métrica Principal
- **F1-Score (macro):** média do F1 por classe, sem ponderar pelo número de amostras. Escolhida por tratar igualmente todas as classes, crucial em cenário desbalanceado onde falhas raras são tão importantes quanto eventos frequentes.

### Métrica Secundária
- **Recall por classe:** essencial para garantir que nenhum tipo de falha deixe de ser detectado (minimizar falsos negativos em cada classe).

### Métricas Complementares
- **Accuracy:** visão geral do desempenho
- **Precision (macro):** controle de falsos positivos

---

## 5. Modelos Selecionados

### 5.1 Regressão Logística
- **Justificativa:** Baseline linear robusto. Rápido de treinar, interpretável e oferece referência para comparação com modelos mais complexos.
- **Configuração:** `class_weight='balanced'`, `solver='lbfgs'`, `multi_class='multinomial'`, `max_iter=1000`
- **Pré-processamento:** StandardScaler (necessário para convergência do solver)

### 5.2 Random Forest
- **Justificativa:** Ensemble baseado em árvores que captura relações não-lineares entre sensores. Robusto a outliers e não requer normalização dos dados. `class_weight='balanced'` ajusta automaticamente os pesos das classes.
- **Configuração:** `n_estimators=200`, `max_depth=15`, `class_weight='balanced'`

### 5.3 XGBoost
- **Justificativa:** Gradient boosting state-of-the-art, excelente em dados tabulares. Captura interações complexas entre features e tende a ter desempenho superior em competições com dados estruturados.
- **Configuração:** `n_estimators=200`, `max_depth=6`, `learning_rate=0.1`, `objective='multi:softmax'`

---

## 6. Metodologia

1. **Carregamento:** CSV com 500 registros (7 features + 1 target)
2. **Pré-processamento:** Remoção de timestamp, tratamento de nulos (dropna)
3. **Split:** 80% treino / 20% teste (stratified para manter proporção das classes)
4. **Treinamento:** 3 modelos com `class_weight='balanced'` para lidar com desbalanceamento
5. **Avaliação:** Accuracy, F1 macro, Precision macro, Recall macro, Classification Report
6. **Tracking:** Todos os experimentos registrados no MLflow com parâmetros, métricas, artefatos e modelos

---

## 7. Integração com MLflow

- **Tracking URI:** http://localhost:5000
- **Experimento:** `petrosafe-classificacao-falhas`
- **Artefatos armazenados no MinIO** (S3-compatible)
- Cada run registra:
  - Parâmetros do modelo
  - Métricas (accuracy, f1_macro, precision_macro, recall_macro)
  - Matriz de confusão (PNG)
  - Classification report (TXT)
  - Modelo serializado (pickle/sklearn ou xgboost)
- Run de comparação final com tag do melhor modelo

---

## 8. Resultados

Os resultados detalhados estão registrados no MLflow (http://localhost:5000) no experimento `petrosafe-classificacao-falhas`.

Para reproduzir:
```bash
make train        # Treina os 3 modelos
make evaluate     # Avalia o melhor modelo
make train-all    # Pipeline completo
```

---

## 9. Conclusão

A comparação dos 3 modelos permite identificar a abordagem mais adequada para classificação de falhas em poços de petróleo. O melhor modelo (selecionado por F1 macro) é registrado no MLflow e pode ser carregado para predições em produção via `src/models/evaluate.py`.
