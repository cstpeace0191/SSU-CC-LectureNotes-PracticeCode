# todo-app-config
getting-started-todo-app-fastapi 의 배포 상태(원하는 상태)를 담는 GitOps Config 저장소.
- base/: 공통 Deployment · Service
- overlays/<env>/: 환경별 namespace · 이미지 태그(커밋 SHA)
- argocd/: AppProject · ApplicationSet · root Application
배포 = overlays/<env> 의 newTag 를 바꾸는 PR 을 병합하는 것.
