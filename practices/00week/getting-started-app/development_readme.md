# Docker Getting Started App — 실행방법 

### ① 사전 준비 — VSCode 및 Node.js 설치
윈도우즈/리눅스  환경에서 동작 시키기 위해, VSCode 또는 다른 IDE 설치
 * VSCode 는 [VSCode-Download](https://code.visualstudio.com/download?_exp_download=fb315fc982) 에서 VSCode User 설치파일 또는 시스템 설치 파일을 다운로드하여 설치.  

 * Node.js 는 [Node.js-Download](https://nodejs.org/en/download) 에서 다운로드하여 설치
'node.js' 설치시에 ('npm' 은 자동 설치됨)

 
### ② 프로젝트 다운로드 (처음 한 번)
```bash
git clone https://github.com/docker/getting-started-app.git
cd getting-started-app
```

### ③  웹응용 실행
``` bash
npm install 
npm run dev 

```
#### npm run dev ---> nodemon -L src/index.js ; src/index.js 을 nodemon이 파일 변화를 감지할 때 '폴링(Polling)' 방식을 사용하도록 강제하는 옵션으로 수행.

### ④ 브라우저에서 접속
```
http://localhost:3000
```
→ Todo 앱 화면이 표시됩니다.

 
### ⑤ 할일 관리 사용
1. 입력창에 할일 텍스트 입력 → **Add Item** 버튼 클릭하여 추가
2. 항목 왼쪽 **체크박스** 클릭 → 완료/미완료 토글
3. 항목 오른쪽 **휴지통 아이콘** 클릭 → 삭제

