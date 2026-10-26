# PyMath 예시 만들기: 학생이 적은 문장(예: "2x + 3의 x=1에서의 극한")에서
# 식·점·구간을 뽑아, 함수별 틀에 채워 실행할 코드를 만든다.
import re
from sympy import (Symbol, symbols, sympify, oo, pi, E, I, S, Eq, Rational, Integer, sqrt, Pow,
                   roots as _roots, Poly, Abs)
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)

from sympy.printing.str import StrPrinter


class _P(StrPrinter):
    # 1/2를 파이썬 코드로 옮기면 0.5(소수)가 되므로 Rational(1, 2)로 적는다
    def _print_Rational(self, e):
        return str(e.p) if e.q == 1 else f"Rational({e.p}, {e.q})"


def pr(e):
    return e if isinstance(e, str) else _P().doprint(e)


_TR = standard_transformations + (implicit_multiplication_application, convert_xor)
_NAMES = "x y z t k n a b c h r m"
_LOC = {s: Symbol(s) for s in _NAMES.split()}
_LOC.update({"e": E, "E": E, "pi": pi, "oo": oo, "I": I, "i": I})
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋", "0123456789+-")
FUNS = "sin cos tan cot sec csc asin acos atan exp log ln sqrt Abs floor".split()


def _norm(s):
    s = s.replace("−", "-").replace("–", "-").replace("×", "*").replace("÷", "/").replace("·", "*").replace("⋅", "*")
    s = s.replace("π", "pi").replace("∞", "oo").replace("무한대", "oo").replace("θ", "t").replace("√", "sqrt")
    s = s.replace("≤", "<=").replace("≥", ">=").replace("＝", "=").replace("→", "->").replace("，", ",")
    s = re.sub(r"([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)", lambda m: "^(" + m.group(1).translate(_SUP) + ")", s)
    s = s.translate(_SUB)
    s = re.sub(r"\|([^|]+)\|", r"Abs(\1)", s)
    s = re.sub(r"\bln\b", "log", s)
    s = re.sub(r"sqrt\s*(\d+|[a-z])", r"sqrt(\1)", s)
    return s


def _parse(s):
    s = s.strip().strip(".,;:")
    if not s:
        return None
    try:
        return parse_expr(s, local_dict=dict(_LOC), transformations=_TR)
    except Exception:
        return None


_MATH = re.compile(r"[0-9A-Za-z_+\-*/^().,\[\]=<>! ]+")


def _chunks(s):
    # 한글이 나오는 곳에서 자르고, 수식처럼 보이는 조각만 남긴다
    out = []
    for m in _MATH.finditer(s):
        c = m.group(0).strip(" ,.")
        if not c or not re.search(r"[0-9a-z]", c):
            continue
        if re.fullmatch(r"[A-Za-z]{4,}", c) and c not in FUNS:
            continue
        out.append(c)
    return out


def _num(s):
    v = _parse(_norm(s))
    return v


def slots(text):
    """문장에서 쓸 재료를 뽑는다."""
    t = _norm(text)
    d = {"text": text}
    # 방향
    if re.search(r"좌극한|왼쪽|-\s*쪽", text):
        d["dir"] = "-"
    elif re.search(r"우극한|오른쪽", text):
        d["dir"] = "+"
    # 구간 [a, b] 또는 a부터 b까지, a ≤ x ≤ b
    m = re.search(r"\[\s*([^\],]+)\s*,\s*([^\]]+)\]", t) or re.search(r"(-?[0-9a-z.()/*]+(?:pi)?)\s*(?:부터|에서|~)\s*(-?[0-9a-z.()/*]+(?:pi)?|oo)\s*까지", t) \
        or re.search(r"(-?[0-9.()/*pi]+)\s*<=?\s*[a-z]\s*<=?\s*(-?[0-9.()/*pi]+)", t)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        if a is not None and b is not None:
            d["a"], d["b"] = a, b
            t = t[:m.start()] + " " + t[m.end():]
    # 점: x = 1, x -> 0, x가 2로
    m = re.search(r"\b([a-z])\s*(?:=|->|가|이)\s*(-?\s*[0-9.]+(?:/[0-9]+)?|-?oo|-?pi(?:/[0-9]+)?|0\+|0-)\s*(?:에서|일\s*때|로|으로|근처|부근|대입|을\s*넣|를\s*넣|에(?!\s*대))", t + " ") \
        or re.search(r"\b([a-z])\s*->\s*(-?\s*[0-9.]+(?:/[0-9]+)?|-?oo|-?pi(?:/[0-9]+)?)", t)
    if m:
        d["v"] = Symbol(m.group(1))
        d["p"] = _num(m.group(2).replace(" ", ""))
        t = t[:m.start()] + " " + t[m.end():]
    # 행렬 [[1, 2], [3, 4]]
    m = re.search(r"\[\s*\[.*?\]\s*\]", text)
    if m:
        try:
            M = sympify(m.group(0))
            d["M"] = [[sympify(v) for v in row] for row in M]
            t = t.replace(_norm(m.group(0)), " ")
        except Exception:
            pass
    # 몇 번 / 몇 자리
    m = re.search(r"(\d+)\s*자리", text)
    if m:
        d["digits"] = int(m.group(1))
        t = re.sub(r"\d+\s*자리", " ", t)
    if re.search(r"이계|두\s*번|2계", text):
        d["order"] = 2
    # 식 조각
    exprs, eqs, ineqs = [], [], []
    for c in _chunks(t):
        if re.search(r"<=|>=|<|>", c):
            ops = re.split(r"(<=|>=|<|>)", c)
            if len(ops) == 3:
                l, r = _parse(ops[0]), _parse(ops[2])
                if l is not None and r is not None:
                    from sympy import Le, Ge, Lt, Gt
                    ineqs.append({"<=": Le, ">=": Ge, "<": Lt, ">": Gt}[ops[1]](l, r))
            continue
        for part in re.split(r",|그리고", c):
            part = part.strip()
            if "=" in part and part.count("=") == 1:
                l, r = part.split("=")
                L, R = _parse(l), _parse(r)
                if L is not None and R is not None and not (L.is_Symbol and R.is_number and len(l.strip()) == 1 and "v" not in d):
                    eqs.append((L, R))
                elif L is not None and L.is_Symbol and R is not None:
                    d.setdefault("v", L); d.setdefault("p", R)
                continue
            e = _parse(part)
            if e is None:
                for sub in re.split(r"\.\.+|\s{2,}|\s(?=[(\[])", part):
                    se = _parse(sub)
                    if se is not None:
                        exprs.append(se)
                continue
            if e is not None and not (e.is_Symbol and len(part) == 1 and exprs):
                exprs.append(e)
    nonnum = [e for e in exprs if not e.is_number]
    exprs = nonnum or exprs[:1]
    d["exprs"], d["eqs"], d["ineqs"] = exprs, eqs, ineqs
    # 주 변수
    free = set()
    for e in exprs + [l - r for l, r in eqs] + ineqs:
        free |= e.free_symbols
    if "v" not in d:
        for cand in "x t n k y".split():
            if Symbol(cand) in free:
                d["v"] = Symbol(cand); break
        else:
            d["v"] = sorted(free, key=str)[0] if free else Symbol("x")
    d["free"] = sorted(free, key=str)
    return d


def _e(d):
    if d["exprs"]:
        return max(d["exprs"], key=lambda e: len(str(e)))
    if d["eqs"]:
        l, r = d["eqs"][0]
        return l - r
    return None


def _eq(d):
    if d["eqs"]:
        l, r = d["eqs"][0]
        return f"Eq({pr(l)}, {pr(r)})"
    e = _e(d)
    return None if e is None else f"Eq({pr(e)}, 0)"


def _surds(e, v):
    # 복소수·실수 범위 인수분해에 필요한 무리수(√n)를 근에서 찾는다
    out = set()
    try:
        for r in _roots(Poly(e, v)).keys():
            for p in r.atoms(Pow):
                if p.exp == S.Half and p.base.is_Integer and p.base > 0:
                    out.add(p)
    except Exception:
        pass
    return sorted(out, key=str)


def _ab(d, a=-5, b=5):
    return d.get("a", a), d.get("b", b)


def _need(msg):
    raise ValueError(msg)


def build(fn, text):
    d = slots(text)
    v, e = d["v"], _e(d)
    p, dr = d.get("p"), d.get("dir")
    T = d["text"]
    def need_e():
        if e is None:
            _need("식을 찾지 못했어요. 식을 x^2 - 4, sin(x)/x처럼 적어 주세요.")
    def need_p(what="점"):
        if p is None:
            _need(f"{what}을 찾지 못했어요. 'x=1에서'처럼 적어 주세요.")
    def mat():
        M = d.get("M")
        if not M:
            _need("행렬을 찾지 못했어요. [[1, 2], [3, 4]]처럼 적어 주세요.")
        return "[" + ", ".join("[" + ", ".join(map(pr, r)) + "]" for r in M) + "]"

    if fn in ("limit", "Limit"):
        need_e(); need_p("다가가는 값")
        if fn == "Limit":
            dd = f", '{dr}'" if dr else ("" if p in (oo, -oo) else ", '+-'")
            return f"L = Limit({pr(e)}, {v}, {pr(p)}{dd})\nprint(L)\nprint(L.doit())"
        if p in (oo, -oo):
            return f"limit({pr(e)}, {v}, {pr(p)})"
        if dr:
            return f"limit({pr(e)}, {v}, {pr(p)}, '{dr}')"
        return f"limit({pr(e)}, {v}, {pr(p)}, '+-')   # 양쪽 극한 (좌·우가 다르면 오류)"
    if fn in ("diff", "Derivative"):
        need_e(); o = d.get("order", 1); oo_ = f", {o}" if o > 1 else ""
        if fn == "Derivative":
            return f"D = Derivative({pr(e)}, {v}{oo_})\nprint(D)\nprint(D.doit())" + (f"\nprint(D.doit().subs({v}, {pr(p)}))" if p is not None else "")
        s = f"df = diff({pr(e)}, {v}{oo_})\nprint(df)"
        return s + (f"\nprint(df.subs({v}, {pr(p)}))   # {v} = {pr(p)}에서의 값" if p is not None else "")
    if fn in ("integrate", "Integral"):
        need_e()
        area = "넓이" in T
        body = f"Abs({pr(e)})" if area else str(e)
        rng = f"({v}, {pr(d['a'])}, {pr(d['b'])})" if "a" in d else str(v)
        if fn == "Integral":
            return f"I = Integral({body}, {rng})\nprint(I)\nprint(I.doit())"
        return f"integrate({body}, {rng})" + ("   # 부정적분: + C는 직접 붙인다" if "a" not in d else "")
    if fn in ("Sum", "summation", "is_convergent", "for", "sum", "SeqFormula"):
        need_e()
        k = next((s for s in (Symbol("k"), Symbol("n"), Symbol("i")) if s in e.free_symbols), v)
        a, b = d.get("a", 1), d.get("b", Symbol("n") if k != Symbol("n") else oo)
        if fn == "is_convergent":
            return f"Sum({pr(e)}, ({k}, {pr(a)}, oo)).is_convergent()"
        if fn == "SeqFormula":
            return f"s = SeqFormula({pr(e)}, ({k}, {pr(a)}, oo))\ns[:6]"
        if fn in ("for", "sum"):
            if not (getattr(a, "is_Integer", False) and getattr(b, "is_Integer", False)):
                b = Integer(10)
            pe = str(e)
            if fn == "for":
                return f"s = 0\nfor {k} in range({pr(a)}, {pr(b)} + 1):\n    s += {pe}\ns"
            return f"sum({pe} for {k} in range({pr(a)}, {pr(b)} + 1))"
        if fn == "summation":
            return f"summation({pr(e)}, ({k}, {pr(a)}, {pr(b)}))"
        return f"S_ = Sum({pr(e)}, ({k}, {pr(a)}, {pr(b)}))\nprint(S_)\nprint(factor(S_.doit()))"
    if fn == "rsolve":
        s = _norm(T)
        s = re.sub(r"a_?\{?\(?n\s*\+\s*1\)?\}?", "f(n+1)", s)
        s = re.sub(r"a_?\{?\(?n\)?\}?(?![+\w(])", "f(n)", s)
        m0 = re.search(r"a_?\(?([0-9])\)?\s*=\s*(-?[0-9]+)", s)
        s2 = re.sub(r"a_?\(?([0-9])\)?\s*=\s*(-?[0-9]+)", " ", s)
        m = re.search(r"f\(n\+1\)\s*=\s*([^,가-힣]+)", s2)
        if not m:
            _need("점화식을 찾지 못했어요. a(n+1) = 2a(n) + 3, a(1) = 1처럼 적어 주세요.")
        from sympy import Function as _F
        rhs = parse_expr(m.group(1).strip(), local_dict={"f": _F("f"), "n": Symbol("n")}, transformations=_TR)
        rhs = pr(rhs)
        init = f", {{f({m0.group(1)}): {m0.group(2)}}}" if m0 else ""
        return f"f = Function('f')\nrsolve(f(n+1) - ({rhs}), f(n){init})"
    if fn in ("solve", "solveset", "nsolve", "linsolve", "nonlinsolve", "roots", "real_roots", "nroots", "np.roots", "Poly", "Interval"):
        if fn == "solveset" and d["ineqs"]:
            return f"solveset({pr(d['ineqs'][0])}, {v}, S.Reals)"
        if fn in ("linsolve", "nonlinsolve") or (fn == "solve" and len(d["eqs"]) > 1):
            eqs = [f"Eq({pr(l)}, {pr(r)})" for l, r in d["eqs"]] or [pr(x) for x in d["exprs"]]
            if len(eqs) < 2:
                _need("방정식을 두 개 이상 쉼표로 나눠 적어 주세요. 예: x + y = 3, x - y = 1")
            vs = ", ".join(map(str, d["free"]))
            return f"{fn}([{', '.join(eqs)}], [{vs}])"
        need_e()
        q = _eq(d)
        if fn == "solve":
            return f"solve({q}, {v})"
        if fn == "solveset":
            dom = f"Interval({pr(d['a'])}, {pr(d['b'])})" if "a" in d else "S.Reals"
            return f"solveset({q}, {v}, {dom})"
        if fn == "Interval":
            a, b = _ab(d, 0, 1)
            return f"J = Interval({pr(a)}, {pr(b)})\nprint(J)\nprint(solveset({q}, {v}, J))"
        if fn == "nsolve":
            x0 = p if p is not None else (d["a"] + d["b"]) / 2 if "a" in d else 1
            lhs = e if not d["eqs"] else d["eqs"][0][0] - d["eqs"][0][1]
            return f"nsolve({pr(lhs)}, {v}, {pr(x0)})   # 마지막 수: 초기값"
        poly = e if not d["eqs"] else d["eqs"][0][0] - d["eqs"][0][1]
        if fn == "roots":
            return f"roots({pr(poly)}, {v})   # {{근: 중복도}}"
        if fn == "real_roots":
            return f"real_roots({pr(poly)})"
        if fn == "nroots":
            return f"nroots({pr(poly)})"
        if fn == "Poly":
            return f"P = Poly({pr(poly)}, {v})\nprint(P.degree(), P.all_coeffs())"
        try:
            cs = Poly(poly, v).all_coeffs()
        except Exception:
            _need("np.roots는 다항식만 됩니다.")
        return f"np.roots({[int(c) if c.is_Integer else float(c) for c in cs]})"
    if fn == "factor":
        need_e(); opt = ""
        if "복소" in T or "허수" in T:
            sr = _surds(e, v)
            opt = f", extension=[{', '.join(map(pr, sr))}, I]" if sr else ", gaussian=True"
        elif "실수" in T or "무리수" in T:
            sr = _surds(e, v)
            opt = f", extension=[{', '.join(map(pr, sr))}]" if sr else ""
        m = re.search(r"\b([a-z])\s*에\s*(?:대해|대하여|관해)", T)
        if m:
            opt += f", gens=[{m.group(1)}]"
        return f"factor({pr(e)}{opt})"
    simple = {"expand": "expand({e})", "expand_trig": "expand_trig({e})", "simplify": "simplify({e})", "trigsimp": "trigsimp({e})",
              "fu": "fu({e})", "together": "together({e})", "apart": "apart({e}, {v})", "nsimplify": "nsimplify({e})",
              "sqrt": "sqrt({e})", "log": "log({e})", "Abs": "Abs({e})", "floor": "floor({e})", "float": "float({e})",
              "decompogen": "decompogen({e}, {v})", "stationary_points": "stationary_points({e}, {v})",
              "continuous_domain": "from sympy.calculus.util import continuous_domain\ncontinuous_domain({e}, {v}, S.Reals)", "singularities": "singularities({e}, {v})",
              "sympify": "sympify('{e}')", "Rational": "nsimplify({e})", "doit": "D = Derivative({e}, {v})\nprint(D)\nprint(D.doit())"}
    if fn in simple:
        need_e()
        if fn == "expand" and re.search(r"sin|cos|tan", str(e)):
            return f"expand({pr(e)}, trig=True)"
        if fn == "N":
            pass
        return simple[fn].format(e=pr(e), v=v)
    if fn == "N":
        need_e(); dg = d.get("digits", 15)
        return f"N({pr(e)}, {dg})"
    if fn == "subs":
        need_e(); need_p("넣을 값")
        return f"f_ = {pr(e)}\nf_.subs({v}, {pr(p)})"
    if fn == "rewrite":
        need_e()
        tgt = next((w for w in ("sin", "cos", "tan", "exp") if re.search(w + r"\s*(으로|로)", T)), "cos")
        return f"({pr(e)}).rewrite({tgt})"
    if fn in ("equals", "Eq"):
        if not d["eqs"]:
            _need("두 식을 = 로 이어서 적어 주세요. 예: sin(2a) = 2sin(a)cos(a)")
        l, r = d["eqs"][0]
        if fn == "Eq":
            return f"eq = Eq({pr(l)}, {pr(r)})\nprint(eq)\nprint(simplify(eq.lhs - eq.rhs) == 0)   # 맞는 식인지"
        return f"({pr(l)}).equals({pr(r)})"
    if fn == "TR":
        need_e()
        return "from sympy.simplify.fu import TR2, TR8, TR9\n" + f"print(TR2({pr(e)}))   # tan → sin/cos\nprint(TR8({pr(e)}))   # 곱 → 합·차\nprint(TR9({pr(e)}))   # 합·차 → 곱"
    if fn in ("is_increasing",):
        need_e(); dom = f"Interval({pr(d['a'])}, {pr(d['b'])})" if "a" in d else "S.Reals"
        return f"print(is_increasing({pr(e)}, {dom}, {v}))\nprint(is_decreasing({pr(e)}, {dom}, {v}))"
    if fn == "minimum":
        need_e(); a, b = _ab(d, -3, 3)
        return f"J = Interval({pr(a)}, {pr(b)})\nprint(minimum({pr(e)}, {v}, J))\nprint(maximum({pr(e)}, {v}, J))"
    if fn == "minimize_scalar":
        need_e(); a, b = _ab(d, -3, 3)
        return f"fn = lambdify({v}, {pr(e)})\nr = minimize_scalar(fn, bounds=({pr(a)}, {pr(b)}), method='bounded')\nprint(r.x, r.fun)"
    if fn in ("quad", "simpson", "np.trapezoid"):
        need_e(); a, b = _ab(d, 0, 1)
        if fn == "quad":
            return f"quad(lambdify({v}, {pr(e)}), {pr(a)}, {pr(b)})   # (값, 오차)"
        xs = f"xs = np.linspace(float({pr(a)}), float({pr(b)}), 5)\nys = lambdify({v}, {pr(e)}, 'numpy')(xs)\n"
        return xs + ("simpson(ys, x=xs)" if fn == "simpson" else "np.trapezoid(ys, xs)")
    if fn == "lambdify":
        need_e()
        return f"f_ = lambdify({v}, {pr(e)})\nf_({p if p is not None else 1})"
    if fn in ("plot", "np.linspace", "plt.plot", "plt.fill_between"):
        need_e(); a, b = _ab(d)
        if fn == "plot":
            return f"plot({pr(e)}, ({v}, {pr(a)}, {pr(b)}))"
        s = f"xs = np.linspace(float({pr(a)}), float({pr(b)}), 400)\nys = lambdify({v}, {pr(e)}, 'numpy')(xs)\nplt.plot(xs, ys)\n"
        if fn == "plt.fill_between":
            s += "plt.fill_between(xs, ys, alpha=0.3)\n"
        return s + "plt.show()"
    if fn == "plot_implicit":
        q = _eq(d)
        if q is None:
            _need("식을 찾지 못했어요. x^2 + y^2 = 1처럼 적어 주세요.")
        return f"plot_implicit({q}, (x, -3, 3), (y, -3, 3), aspect_ratio=(1, 1))"
    if fn == "plot_parametric":
        ex = [r for l, r in d["eqs"] if str(l) in ("x", "y")] or d["exprs"][:2]
        if len(ex) < 2:
            _need("x = cos t, y = sin t처럼 두 식을 적어 주세요.")
        return f"plot_parametric({pr(ex[0])}, {pr(ex[1])}, (t, 0, 2*pi), aspect_ratio=(1, 1))"
    if fn == "polar":
        need_e()
        return f"th = np.linspace(0, 2*np.pi, 400)\nr_ = lambdify(t, {pr(e)}, 'numpy')(th)\nplt.subplot(projection='polar')\nplt.plot(th, r_ * np.ones_like(th)); plt.show()"
    if fn in ("Matrix", "det", "inv", "eigenvals", "np.array", "np.linalg", "LUsolve"):
        M = mat()
        if fn == "Matrix":
            return f"A = Matrix({M})\nprint(A * A)\nprint(A.det())"
        if fn == "det":
            return f"Matrix({M}).det()"
        if fn == "inv":
            return f"Matrix({M}).inv()"
        if fn == "eigenvals":
            return f"Matrix({M}).eigenvals()"
        if fn == "LUsolve":
            n = len(d["M"])
            return f"A = Matrix({M})\nb_ = Matrix({[1] * n})   # 오른쪽 값\nA.LUsolve(b_)"
        if fn == "np.array":
            return f"An = np.array({M})\nprint(An @ An)   # 행렬곱\nprint(An * An)   # 성분끼리 곱"
        return f"An = np.array({M}, dtype=float)\nprint(np.linalg.det(An))\nprint(np.linalg.inv(An))"
    if fn == "hilbert":
        m = re.search(r"(\d+)", T)
        n = int(m.group(1)) if m else 3
        return f"from scipy.linalg import hilbert\nhilbert({n})"
    if fn == "math.log":
        nums = re.findall(r"-?\d+(?:\.\d+)?", T)
        if not nums:
            _need("수를 적어 주세요. 예: 밑이 3인 9의 로그")
        return f"import math\nmath.log({', '.join(nums[:2])})"
    if fn == "symbols":
        need_e()
        a = "positive=True" if "양수" in T else "integer=True" if "정수" in T else "real=True"
        names = " ".join(map(str, d["free"])) or "x"
        lhs = ", ".join(map(str, d["free"])) or "x"
        return f"{pr(lhs)}{',' if len(d['free']) == 1 else ''} = symbols('{names}', {pr(a)})\nsimplify({pr(e)})"
    if fn == "Function":
        return build("rsolve", text)
    if fn == "Piecewise":
        _need("구간별 함수는 아직 문장으로 만들 수 없어요. 기본 코드의 식을 바꿔 보세요.")
    _need("이 함수는 아직 문장으로 예시를 만들 수 없어요.")


def make(fn, text):
    try:
        return {"code": build(fn, text)}
    except ValueError as ex:
        return {"fail": str(ex)}
    except Exception as ex:
        return {"fail": "문장을 이해하지 못했어요. 식을 x^2 - 4처럼 적어 주세요."}
