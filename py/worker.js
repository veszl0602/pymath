// PyMath: 브라우저에서 파이썬(Pyodide)과 SymPy 1.14를 실행하는 웹 워커
const BASE = new URL("./", self.location).href;
const CDN = "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/";
let py = null;
const say = text => self.postMessage({ type: "progress", text });
async function boot() {
  importScripts(BASE + "pyodide.js");
  say("파이썬을 불러오는 중… (처음 한 번만 10~30초)");
  py = await loadPyodide({ indexURL: BASE, lockFileURL: BASE + "pyodide-lock.json", packageBaseUrl: CDN });
  say("SymPy를 설치하는 중…");
  for (const w of ["mpmath-1.3.0-py3-none-any.whl", "sympy-1.14.0-py3-none-any.whl"]) {
    const buf = await (await fetch(BASE + w)).arrayBuffer();
    py.unpackArchive(new Uint8Array(buf), "wheel");
  }
  const src = await (await fetch(BASE + "runner.py")).text();
  py.runPython(src);
  const ver = py.runPython("import sympy; sympy.__version__");
  self.postMessage({ type: "ready", ver });
  return ver;
}
const booting = boot().catch(e => { self.postMessage({ type: "ready", error: String(e) }); throw e; });
self.onmessage = async e => {
  const { id, code, pre } = e.data;
  let ver;
  try { ver = await booting; } catch (err) { self.postMessage({ id, err: "파이썬을 불러오지 못했습니다. 인터넷 연결을 확인해 주세요." }); return; }
  const all = (pre || []).join("\n") + "\n" + code;
  const need = [];
  if (/numpy|np\./.test(all) || /scipy/.test(all) || /lambdify/.test(all)) need.push("numpy");
  if (/scipy/.test(all)) need.push("scipy");
  if (/matplotlib|plt\.|plot\(|plot_implicit|plot_parametric/.test(all)) need.push("matplotlib");
  try {
    if (need.length) { say(need.join(", ") + " 불러오는 중…"); await py.loadPackage(need); }
    const run = py.globals.get("run");
    const r = run(py.toPy(pre || []), code).toJs({ dict_converter: Object.fromEntries });
    self.postMessage({ id, out: r.out, err: r.err, imgs: r.imgs, ver });
  } catch (err) {
    self.postMessage({ id, err: String(err).split("\n").slice(-2).join("\n"), ver });
  }
};
