# AI 중계 설정 (무료)

사이트의 '예시 만들기'에서 규칙으로 못 만든 요청과 사진을 AI(Gemini)가 처리하게 합니다. 키는 중계(Worker)에만 저장되어 사이트 방문자에게 보이지 않습니다.

> Google의 Gemini API 약관은 이용자를 만 18세 이상으로 정합니다. 키와 Cloudflare 계정은 지도 선생님 계정으로 만드세요.

1. **Gemini 키**: https://aistudio.google.com/apikey 에서 `Create API key`. 결제(Billing)는 켜지 마세요. 켜지 않으면 무료 한도를 넘어도 요금이 나가지 않고 요청만 거절됩니다.
2. **Worker 만들기**: https://dash.cloudflare.com → Workers & Pages → Create → `Hello World` Worker 만들기 → `Edit code`에서 내용을 지우고 `worker.js`를 붙여 넣은 뒤 Deploy.
3. **값 넣기**: 그 Worker의 Settings → Variables and Secrets
   - `GEMINI_KEY` (Secret): 1번의 키
   - `ALLOW` (Text): `https://veszl0602.github.io`
4. **사이트에 연결**: Worker 주소(예: `https://pymath-ai.<이름>.workers.dev`)를 저장소의 `config.js`의 `aiUrl` 따옴표 안에 넣고 커밋합니다.

무료 한도(하루 요청 수)는 Google AI Studio의 Rate limits 화면에서 볼 수 있습니다. 모델 이름이 바뀌면 Worker 값 `MODEL`에 새 이름을 넣으면 됩니다.
