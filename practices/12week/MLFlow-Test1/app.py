import sys
import torch
import torch.nn as nn
import torch.optim as optim
import mlflow
import mlflow.pytorch

# Windows 콘솔(cp949)에서 mlflow가 출력하는 이모지(예: 🏃)로 인한
# UnicodeEncodeError를 방지하기 위해 표준출력을 UTF-8로 재설정
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 1. Docker로 실행 중인 MLflow 서버 및 실험(Experiment) 설정
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("pytorch-linear-regression")

# 데이터 및 가상 모델 정의
X = torch.randn(100, 10)
y = torch.randn(100, 1)

model = nn.Linear(10, 1)
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

epochs = 20
batch_size = 100

# 2. MLflow 실행(Run) 시작
with mlflow.start_run(run_name="first_pytorch_run"):
    
    # [A] 하이퍼파라미터 기록 (log_params)
    mlflow.log_params({
        "learning_rate": 0.01,
        "epochs": epochs,
        "optimizer": "SGD",
        "batch_size": batch_size
    })

    # [B] 학습 루프 및 에폭별 Loss 기록
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()

        # 에폭마다 Loss 수치 기록 (UI에서 선 그래프로 시각화됨)
        mlflow.log_metric("train_loss", loss.item(), step=epoch)

    # [C] PyTorch 모델 저장 (Artifacts 탭에 저장됨)
    mlflow.pytorch.log_model(model, artifact_path="model", input_example=X.numpy())

print("학습 및 MLflow 로깅이 완료되었습니다!")