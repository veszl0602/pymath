# PyMath 브라우저 실행기: 준비 코드를 조용히 실행한 뒤, 학생 코드의 출력과 그래프를 돌려준다.
import sys, io, ast, base64, contextlib, builtins

def _fake_input(prompt=""):
    raise RuntimeError("이 페이지에서는 input()을 쓸 수 없습니다. 값을 직접 코드에 넣어 주세요.")

def _figs():
    out = []
    if "matplotlib.pyplot" in sys.modules:
        plt = sys.modules["matplotlib.pyplot"]
        for num in plt.get_fignums()[:4]:
            b = io.BytesIO(); plt.figure(num).savefig(b, format="png", dpi=80, bbox_inches="tight")
            out.append(base64.b64encode(b.getvalue()).decode())
        plt.close("all")
    return out

def _exec(src, g, echo):
    # echo=True: 맨 바깥의 식 한 줄마다 값을 보여 준다(None 제외)
    tree = ast.parse(src)
    for node in tree.body:
        if echo and isinstance(node, ast.Expr) and not (isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "print"):
            v = eval(compile(ast.Expression(node.value), "<code>", "eval"), g)
            if v is not None and not type(v).__name__.endswith("Plot"):
                print(repr(v) if isinstance(v, str) else v)
        else:
            exec(compile(ast.Module([node], []), "<code>", "exec"), g)

def _quiet(src, g):
    # 준비 코드: 한 문장씩 실행하고, 실패한 문장은 건너뛴다
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    for node in tree.body:
        try:
            exec(compile(ast.Module([node], []), "<pre>", "exec"), g)
        except Exception:
            pass

def run(pre, code):
    builtins.input = _fake_input
    if "matplotlib" in sys.modules or "plt" in code or "plot" in code:
        try:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt; plt.show = lambda *a, **k: None
        except Exception:
            pass
    g = {"__name__": "__main__"}
    for p in pre:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                _quiet(p, g)
        except Exception:
            pass
    _figs()
    buf = io.StringIO(); err = ""
    try:
        with contextlib.redirect_stdout(buf):
            _exec(code, g, True)
    except SyntaxError as e:
        err = f"문법 오류 (SyntaxError): {e.msg}, {e.lineno}번째 줄"
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    return {"out": buf.getvalue().rstrip("\n")[:20000], "err": err, "imgs": _figs()}
