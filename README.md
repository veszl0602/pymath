# PyMath 문제풀이 안내서

고등학교 수학(공통수학1·2, 대수, 미적분Ⅰ·Ⅱ) 문제를 파이썬으로 풀고 확인하는 방법을 안내하는 정적 웹사이트입니다. 2026 R&E 수학 C조.

- `index.html`: 사이트 전체 (서버 불필요)
- `fig/`: 예제 실행 결과 그래프
- `py/`: 브라우저에서 SymPy 1.14를 실행하는 Pyodide 파일과 실행기

## 올리는 법 (GitHub Pages)
저장소 Settings → Pages → Source를 `Deploy from a branch`, 브랜치 `main`, 폴더 `/ (root)`로 두면 `https://<아이디>.github.io/<저장소>/` 주소가 생깁니다.

NumPy·SciPy·Matplotlib 실행과 사진 글자 인식(Tesseract.js)은 jsDelivr CDN에서 불러옵니다.
