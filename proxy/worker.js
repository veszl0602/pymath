// PyMath AI 중계 (Cloudflare Worker)
// 사이트가 보낸 문장·사진을 Gemini에 넘기고, 실행할 파이썬 코드만 돌려준다.
// 키는 이 Worker의 비밀 값(GEMINI_KEY)에만 저장되고 사이트에는 드러나지 않는다.
//
// 설정할 값 (Cloudflare 대시보드 → Worker → Settings → Variables and Secrets)
//   GEMINI_KEY  (Secret)  Google AI Studio에서 만든 API 키
//   ALLOW       (Text)    허용할 사이트 주소. 예: https://veszl0602.github.io
//   MODEL       (Text)    선택. 비워 두면 gemini-2.5-flash

const SYSTEM = `너는 한국 고등학생용 수학 안내서 'PyMath'의 예시 코드 도우미다.
학생이 보고 싶은 예시(문장 또는 문제 사진)를 주면, 브라우저의 Pyodide에서 바로 실행할 파이썬 코드를 만든다.
규칙:
- 이미 실행된 준비 코드: from sympy import *; x, y, z, t, a, b, k, n, r, c, h = symbols('x y z t a b k n r c h'); import numpy as np; import matplotlib.pyplot as plt
- scipy가 필요하면 직접 import 한다. input()은 쓰지 않는다. 파일·인터넷 접근 금지.
- 지정된 함수(fn)를 중심으로 쓴다. 정확한 값은 SymPy, 분수는 Rational.
- 12줄 이하. 맨 바깥 줄의 식은 값이 자동으로 출력된다. 여러 값은 print.
- 주석은 짧은 한국어로, 꼭 필요한 곳만.
- 사진이면 사진 속 문제를 읽어 그 문제를 푸는 코드를 만든다. 읽은 식은 note에 적는다.
- 수학 예시와 관계없는 요청이면 code를 빈 문자열로 두고 note에 이유를 적는다.
반드시 JSON 하나만 답한다: {"code": "...", "note": "한 줄 설명"}`;

export default {
  async fetch(req, env) {
    const allow = env.ALLOW || "*";
    const origin = req.headers.get("origin") || "";
    const cors = { "access-control-allow-origin": allow === "*" ? "*" : (origin === allow ? origin : allow), "access-control-allow-methods": "POST, OPTIONS", "access-control-allow-headers": "content-type", "vary": "origin" };
    const reply = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: { ...cors, "content-type": "application/json; charset=utf-8" } });
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return reply({ error: "POST만 받습니다" }, 405);
    if (allow !== "*" && origin !== allow) return reply({ error: "허용되지 않은 사이트" }, 403);
    if (!env.GEMINI_KEY) return reply({ error: "GEMINI_KEY가 설정되지 않았습니다" }, 500);
    const body = await req.text();
    if (body.length > 4_000_000) return reply({ error: "사진이 너무 큽니다" }, 413);
    let q; try { q = JSON.parse(body); } catch { return reply({ error: "잘못된 요청" }, 400); }
    const parts = [{ text: `fn: ${String(q.fn || "").slice(0, 40)} (${String(q.name || "").slice(0, 60)})\n요청: ${String(q.text || "(사진 참고)").slice(0, 500)}` }];
    const m = /^data:(image\/[a-z+]+);base64,(.+)$/.exec(q.image || "");
    if (m) parts.push({ inline_data: { mime_type: m[1], data: m[2] } });
    const model = env.MODEL || "gemini-2.5-flash";
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-goog-api-key": env.GEMINI_KEY },
      body: JSON.stringify({ systemInstruction: { parts: [{ text: SYSTEM }] }, contents: [{ role: "user", parts }], generationConfig: { temperature: 0.2, responseMimeType: "application/json" } })
    });
    if (!r.ok) return reply({ error: r.status === 429 ? "오늘 무료 사용량을 다 썼습니다. 잠시 뒤 다시 해 보세요" : "AI 서버 오류 " + r.status }, 502);
    const j = await r.json();
    const text = j?.candidates?.[0]?.content?.parts?.map(p => p.text || "").join("") || "";
    let out; try { out = JSON.parse(text.replace(/^```(?:json)?|```$/g, "").trim()); } catch { return reply({ error: "AI 답을 읽지 못했습니다" }, 502); }
    return reply({ code: String(out.code || "").slice(0, 3000), note: String(out.note || "").slice(0, 300) });
  }
};
