# ============================================================
#  서울 기온 순위 탐색기 (최저기온 강화판)
#  - 두 날짜를 고르면 그 기간이 역대 몇 위인지 알려줍니다.
#  - 최저기온은 '한파 순위'와 '열대야(더운 밤) 순위'를 함께 제공합니다.
#  - 사용 라이브러리: streamlit, pandas (Streamlit Cloud 기본 제공)
# ============================================================

import streamlit as st
import pandas as pd
import datetime

# ------------------------------------------------------------
# 0. 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="서울 기온 순위 탐색기",
    page_icon="🌡️",
    layout="wide",
)

# ------------------------------------------------------------
# 1. 커스텀 스타일 (CSS)
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; }

/* 상단 배너 */
.hero {
    background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 35%, #FEB47B 70%, #FF7E5F 100%);
    padding: 28px 32px;
    border-radius: 18px;
    color: white;
    margin-bottom: 22px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
.hero h1 { margin: 0; font-size: 2.0rem; font-weight: 800; letter-spacing:-1px; }
.hero p  { margin: 8px 0 0 0; font-size: 0.96rem; opacity: 0.96; }

/* 순위 카드 */
.rank-card {
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    color: #fff;
    box-shadow: 0 6px 18px rgba(0,0,0,0.12);
    margin-bottom: 10px;
}
.rank-card .label { font-size: 0.88rem; opacity: 0.93; letter-spacing: 0.3px; font-weight:600;}
.rank-card .rank  { font-size: 2.4rem; font-weight: 800; line-height: 1.15; margin: 4px 0 2px 0;}
.rank-card .total { font-size: 0.80rem; opacity: 0.88; }
.rank-card .value { font-size: 1.08rem; font-weight: 700; margin-top: 10px;
                    background: rgba(255,255,255,0.22); border-radius: 10px; padding: 6px 0;}
.rank-card .tag   { font-size: 0.82rem; margin-top: 8px; opacity: 0.95; }

/* 색상 팔레트 */
.c-mean    { background: linear-gradient(135deg,#7F00FF 0%, #E100FF 100%); }
.c-hot     { background: linear-gradient(135deg,#F5515F 0%, #9F041B 100%); }
.c-coldest { background: linear-gradient(135deg,#134E5E 0%, #71B280 100%); }
.c-night   { background: linear-gradient(135deg,#0F2027 0%, #2C5364 100%); }
.c-warmnight{background: linear-gradient(135deg,#FF512F 0%, #F09819 100%); }
.c-ice     { background: linear-gradient(135deg,#1c92d2 0%, #7bdcff 100%); }

/* 배지 */
.badge {
    display:inline-block; padding:5px 14px; border-radius:999px;
    background:#F1F3F5; color:#343A40; font-size:0.85rem; font-weight:600;
    margin-right:6px; margin-bottom:6px;
}
.section-title { font-size:1.15rem; font-weight:800; margin: 18px 0 10px 0; }
.small-note { color:#868E96; font-size:0.82rem; }
hr.soft { border:none; border-top:1px solid #E9ECEF; margin:18px 0; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# 2. 데이터 불러오기
# ------------------------------------------------------------
@st.cache_data
def load_data():
    """seoul.csv를 읽어서 전처리한 DataFrame을 반환한다."""
    # BOM(\ufeff) 제거를 위해 utf-8-sig 사용
    df = pd.read_csv("seoul.csv", encoding="utf-8-sig")

    # 컬럼명 공백 제거
    df.columns = [str(c).strip() for c in df.columns]

    # 날짜 앞 탭 문자/공백 제거 후 datetime 변환
    df["날짜"] = df["날짜"].astype(str).str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 기온 컬럼 숫자화
    for col in ["평균기온", "최저기온", "최고기온"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 날짜 없는 행(마지막 빈 행 등) 제거
    df = df.dropna(subset=["날짜"]).copy()

    # 파생 컬럼
    df["연"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일교차"] = df["최고기온"] - df["최저기온"]

    # 특성일 플래그
    df["열대야"] = (df["최저기온"] >= 25).astype("float")     # 밤에도 25℃ 이상
    df["한파일"] = (df["최저기온"] <= -12).astype("float")    # 최저 -12℃ 이하
    df["결빙일"] = (df["최고기온"] < 0).astype("float")       # 하루종일 영하
    df["영하일"] = (df["최저기온"] < 0).astype("float")       # 최저기온 영하
    df["폭염일"] = (df["최고기온"] >= 33).astype("float")

    # 기온이 NaN인 날은 플래그도 NaN 처리
    df.loc[df["최저기온"].isna(), ["열대야", "한파일", "영하일"]] = float("nan")
    df.loc[df["최고기온"].isna(), ["결빙일", "폭염일"]] = float("nan")

    return df.sort_values("날짜").reset_index(drop=True)


try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ 'seoul.csv' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 두세요.")
    st.stop()


MIN_DATE = df["날짜"].min().date()
MAX_DATE = df["날짜"].max().date()

st.markdown(f"""
<div class="hero">
  <h1>🌡️ 서울 기온 순위 탐색기</h1>
  <p>기간을 고르면 <b>평균 · 최고 · 최저기온</b>이 역대 몇 위인지 알려드립니다.
     최저기온은 <b>한파 순위 🧊</b> 와 <b>열대야 순위 🔥</b> 를 함께 확인할 수 있어요.<br>
     데이터 범위: <b>{MIN_DATE} ~ {MAX_DATE}</b> · 총 {len(df):,}일</p>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# 3. 사이드바
# ------------------------------------------------------------
with st.sidebar:
    st.header("📅 기간 선택")

    default_end = MAX_DATE
    default_start = max(MIN_DATE, default_end - datetime.timedelta(days=6))

    picked = st.date_input(
        "달력에서 시작일과 종료일을 선택하세요",
        value=(default_start, default_end),
        min_value=MIN_DATE,
        max_value=MAX_DATE,
        format="YYYY-MM-DD",
    )

    st.markdown("---")
    st.subheader("⚙️ 비교 방식")
    compare_mode = st.radio(
        "무엇과 비교할까요?",
        ["같은 월·일 기간끼리 (연도별)", "역대 모든 같은 길이 구간"],
        index=0,
        help=("① 8/1~8/10을 골랐다면 1907년 8/1~8/10, 1908년 8/1~8/10 … 과 비교\n"
              "② 1년 중 아무 시점이나 같은 일수의 모든 연속 구간과 비교"),
    )

    min_ratio = st.slider(
        "최소 데이터 보유율 (%)", 0, 100, 80, step=5,
        help="이 비율보다 관측 자료가 적은 연도/구간은 순위에서 제외합니다."
    )

    st.markdown("---")
    st.subheader("🌙 최저기온 기준")
    st.caption(
        "· **열대야**: 최저기온 25℃ 이상\n\n"
        "· **한파일**: 최저기온 -12℃ 이하\n\n"
        "· **영하일**: 최저기온 0℃ 미만"
    )
    st.markdown("---")
    st.caption("📌 데이터: 기상청 기상자료개방포털 (지점 108, 서울)")


# 날짜 검증
if not isinstance(picked, (tuple, list)) or len(picked) != 2:
    st.info("👈 사이드바 달력에서 **종료일까지** 선택해 주세요.")
    st.stop()

start_date, end_date = picked
if start_date > end_date:
    start_date, end_date = end_date, start_date
n_days = (end_date - start_date).days + 1


# ------------------------------------------------------------
# 4. 선택 기간 통계
# ------------------------------------------------------------
sel = df[(df["날짜"].dt.date >= start_date) & (df["날짜"].dt.date <= end_date)].copy()

if sel.empty or sel["최저기온"].isna().all():
    st.warning("선택한 기간에 사용할 수 있는 데이터가 없습니다. 다른 기간을 골라 주세요.")
    st.stop()

sel_stats = {
    "평균기온":     round(sel["평균기온"].mean(), 2),
    "최고기온":     sel["최고기온"].max(),
    "최저기온":     sel["최저기온"].min(),      # 기간 중 가장 추웠던 값
    "최저기온평균": round(sel["최저기온"].mean(), 2),
    "최저기온최댓값": sel["최저기온"].max(),    # 기간 중 가장 더웠던 밤
    "일교차평균":   round(sel["일교차"].mean(), 2),
    "열대야일수":   int(sel["열대야"].sum()),
    "한파일수":     int(sel["한파일"].sum()),
    "영하일수":     int(sel["영하일"].sum()),
    "폭염일수":     int(sel["폭염일"].sum()),
}

st.markdown(
    f'<span class="badge">🗓️ {start_date} ~ {end_date}</span>'
    f'<span class="badge">📏 {n_days}일</span>'
    f'<span class="badge">📊 실제 관측 {len(sel)}일</span>'
    f'<span class="badge">🌙 열대야 {sel_stats["열대야일수"]}일</span>'
    f'<span class="badge">❄️ 영하일 {sel_stats["영하일수"]}일</span>',
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# 5. 비교 대상 테이블 만들기
# ------------------------------------------------------------
def summarize(chunk):
    """구간 하나를 요약 통계 dict로."""
    return {
        "평균기온":     round(chunk["평균기온"].mean(), 2),
        "최고기온":     chunk["최고기온"].max(),
        "최저기온":     chunk["최저기온"].min(),
        "최저기온평균": round(chunk["최저기온"].mean(), 2),
        "최저기온최댓값": chunk["최저기온"].max(),
        "일교차평균":   round(chunk["일교차"].mean(), 2),
        "열대야일수":   int(chunk["열대야"].sum()),
        "한파일수":     int(chunk["한파일"].sum()),
        "영하일수":     int(chunk["영하일"].sum()),
        "폭염일수":     int(chunk["폭염일"].sum()),
        "관측일수":     int(chunk["최저기온"].notna().sum()),
    }


@st.cache_data
def build_year_table(df, sm, sd, em, ed, min_ratio):
    """같은 월·일 구간을 연도별로 묶어 통계 테이블 생성."""
    cross_year = (sm, sd) > (em, ed)          # 연말→연초로 넘어가는 경우
    rows = []
    for y in sorted(df["연"].unique()):
        try:
            s = datetime.date(y, sm, sd)
            e = datetime.date(y + 1 if cross_year else y, em, ed)
        except ValueError:
            continue                           # 윤년 2/29 등 없는 날짜
        chunk = df[(df["날짜"].dt.date >= s) & (df["날짜"].dt.date <= e)]
        if chunk.empty:
            continue
        span = (e - s).days + 1
        if chunk["최저기온"].notna().sum() / span * 100 < min_ratio:
            continue
        row = {"연도": y, "시작": s, "종료": e}
        row.update(summarize(chunk))
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data
def build_window_table(df, n_days, min_ratio):
    """역대 모든 n일 연속 구간의 이동 통계 생성."""
    s = df.set_index("날짜")
    full = s.resample("D").asfreq()            # 빠진 날짜를 NaN으로 채워 연속성 확보
    r = full.rolling(n_days)

    res = pd.DataFrame(index=full.index)
    res["평균기온"]       = r["평균기온"].mean().round(2)
    res["최고기온"]       = r["최고기온"].max()
    res["최저기온"]       = r["최저기온"].min()
    res["최저기온평균"]   = r["최저기온"].mean().round(2)
    res["최저기온최댓값"] = r["최저기온"].max()
    res["일교차평균"]     = r["일교차"].mean().round(2)
    res["열대야일수"]     = r["열대야"].sum()
    res["한파일수"]       = r["한파일"].sum()
    res["영하일수"]       = r["영하일"].sum()
    res["폭염일수"]       = r["폭염일"].sum()
    res["관측일수"]       = r["최저기온"].count()

    res = res[res["관측일수"] >= n_days * (min_ratio / 100)]
    res = res.dropna(subset=["평균기온", "최저기온"])
    res["종료"] = res.index.date
    res["시작"] = (res.index - pd.Timedelta(days=n_days - 1)).date
    return res.reset_index(drop=True)


if compare_mode.startswith("같은"):
    table = build_year_table(df, start_date.month, start_date.day,
                             end_date.month, end_date.day, min_ratio)
    unit_label, key_col, my_key = "개 연도", "연도", start_date.year
else:
    table = build_window_table(df, n_days, min_ratio)
    unit_label, key_col, my_key = "개 구간", None, None

if table.empty:
    st.warning("비교할 과거 기록이 부족합니다. 최소 데이터 보유율을 낮춰 보세요.")
    st.stop()

total_n = len(table)


# ------------------------------------------------------------
# 6. 순위 계산 함수
# ------------------------------------------------------------
def get_rank(series, value, descending=True):
    """value가 series 안에서 몇 번째로 큰(작은) 값인지 (공동순위는 최상위 부여)."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return 1
    if descending:
        return int((s > value).sum()) + 1
    return int((s < value).sum()) + 1


def comment(rank, total):
    """순위를 사람이 읽기 좋은 한 줄 평으로."""
    pct = rank / total * 100
    if rank == 1:   return "🥇 역대 1위!", pct
    if rank == 2:   return "🥈 역대 2위", pct
    if rank == 3:   return "🥉 역대 3위", pct
    if pct <= 5:    return "🔥 상위 5% 이내", pct
    if pct <= 10:   return "✨ 상위 10% 이내", pct
    if pct >= 95:   return "😌 하위 5% 수준", pct
    return "📊 평범한 편", pct


def card(css, label, rank, value_text, tag_text):
    t, pct = comment(rank, total_n)
    return f"""
    <div class="rank-card {css}">
      <div class="label">{label}</div>
      <div class="rank">{rank}위</div>
      <div class="total">{total_n}{unit_label} 중 · 상위 {pct:.1f}%</div>
      <div class="value">{value_text}</div>
      <div class="tag">{t} · {tag_text}</div>
    </div>
    """


# ------------------------------------------------------------
# 7. 결과 카드
# ------------------------------------------------------------
st.markdown('<div class="section-title">🏆 종합 기온 순위</div>', unsafe_allow_html=True)

r_mean = get_rank(table["평균기온"], sel_stats["평균기온"], True)
r_max  = get_rank(table["최고기온"], sel_stats["최고기온"], True)
r_gap  = get_rank(table["일교차평균"], sel_stats["일교차평균"], True)

c1, c2, c3 = st.columns(3)
c1.markdown(card("c-mean", "🌤️ 평균기온 (높은 순)", r_mean,
                 f'{sel_stats["평균기온"]:.2f} ℃', "더울수록 상위"), unsafe_allow_html=True)
c2.markdown(card("c-hot", "🔥 기간 내 최고기온", r_max,
                 f'{sel_stats["최고기온"]:.1f} ℃', f'폭염 {sel_stats["폭염일수"]}일'), unsafe_allow_html=True)
c3.markdown(card("c-ice", "🌗 평균 일교차 (큰 순)", r_gap,
                 f'{sel_stats["일교차평균"]:.2f} ℃', "클수록 상위"), unsafe_allow_html=True)


st.markdown('<div class="section-title">🌙 최저기온 집중 분석</div>', unsafe_allow_html=True)
st.caption("최저기온은 방향에 따라 의미가 달라집니다. **추운 순**과 **더운 순**을 모두 확인해 보세요.")

r_coldest   = get_rank(table["최저기온"], sel_stats["최저기온"], False)          # 낮을수록 1위
r_nightmean = get_rank(table["최저기온평균"], sel_stats["최저기온평균"], False)  # 낮을수록 1위
r_warmnight = get_rank(table["최저기온최댓값"], sel_stats["최저기온최댓값"], True)  # 높을수록 1위

d1, d2, d3 = st.columns(3)
d1.markdown(card("c-coldest", "🧊 최저기온 최솟값 (추운 순)", r_coldest,
                 f'{sel_stats["최저기온"]:.1f} ℃',
                 f'한파 {sel_stats["한파일수"]}일'), unsafe_allow_html=True)
d2.markdown(card("c-night", "🌚 최저기온 평균 (추운 순)", r_nightmean,
                 f'{sel_stats["최저기온평균"]:.2f} ℃',
                 f'영하 {sel_stats["영하일수"]}일'), unsafe_allow_html=True)
d3.markdown(card("c-warmnight", "🥵 가장 더운 밤 (높은 순)", r_warmnight,
                 f'{sel_stats["최저기온최댓값"]:.1f} ℃',
                 f'열대야 {sel_stats["열대야일수"]}일'), unsafe_allow_html=True)

# 최저기온 극값이 발생한 날짜 안내
try:
    cold_day = sel.loc[sel["최저기온"].idxmin(), "날짜"].date()
    warm_day = sel.loc[sel["최저기온"].idxmax(), "날짜"].date()
    st.info(f"❄️ 가장 추웠던 새벽: **{cold_day}** ({sel_stats['최저기온']:.1f} ℃) ｜ "
            f"🌡️ 가장 더웠던 밤: **{warm_day}** ({sel_stats['최저기온최댓값']:.1f} ℃)")
except Exception:
    pass

st.markdown('<hr class="soft">', unsafe_allow_html=True)


# ------------------------------------------------------------
# 8. 상세 탭
# ------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 기간 기온 변화", "🌙 최저기온 랭킹", "🏅 종합 TOP 10", "📋 전체 순위표"]
)

# --- 탭1 ---
with tab1:
    st.markdown("#### 선택 기간의 일별 기온")
    st.line_chart(sel.set_index("날짜")[["최고기온", "평균기온", "최저기온"]], height=340)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("기간 평균기온", f'{sel_stats["평균기온"]:.2f} ℃')
    m2.metric("최고기온", f'{sel_stats["최고기온"]:.1f} ℃')
    m3.metric("최저기온", f'{sel_stats["최저기온"]:.1f} ℃')
    m4.metric("최저기온 평균", f'{sel_stats["최저기온평균"]:.2f} ℃')

    n1, n2, n3, n4 = st.columns(4)
    n1.metric("🌙 열대야 일수", f'{sel_stats["열대야일수"]} 일')
    n2.metric("❄️ 영하 일수", f'{sel_stats["영하일수"]} 일')
    n3.metric("🥶 한파 일수", f'{sel_stats["한파일수"]} 일')
    n4.metric("🌗 평균 일교차", f'{sel_stats["일교차평균"]:.2f} ℃')

    st.markdown("#### 일별 최저기온만 보기")
    st.bar_chart(sel.set_index("날짜")[["최저기온"]], height=260)

# --- 탭2 : 최저기온 전용 랭킹 ---
with tab2:
    st.markdown("#### 🧊 가장 추웠던 기간 TOP 10 (최저기온 최솟값 기준)")
    cold_top = table.sort_values("최저기온", ascending=True).head(10).reset_index(drop=True)
    cold_top.index = [f"{i+1}위" for i in range(len(cold_top))]
    cols_show = [c for c in ["연도", "시작", "종료", "최저기온", "최저기온평균",
                             "영하일수", "한파일수", "관측일수"] if c in cold_top.columns]
    st.dataframe(cold_top[cols_show], use_container_width=True)

    st.markdown("#### 🥵 밤이 가장 더웠던 기간 TOP 10 (최저기온 최댓값 기준)")
    warm_top = table.sort_values("최저기온최댓값", ascending=False).head(10).reset_index(drop=True)
    warm_top.index = [f"{i+1}위" for i in range(len(warm_top))]
    cols_show2 = [c for c in ["연도", "시작", "종료", "최저기온최댓값", "최저기온평균",
                              "열대야일수", "관측일수"] if c in warm_top.columns]
    st.dataframe(warm_top[cols_show2], use_container_width=True)

    st.markdown("#### 📊 최저기온 평균 분포 비교")
    idx_col = "연도" if "연도" in table.columns else "종료"
    dist = table.sort_values("최저기온평균", ascending=False).head(15)
    st.bar_chart(dist.set_index(dist[idx_col].astype(str))[["최저기온평균"]], height=300)

# --- 탭3 ---
with tab3:
    st.markdown("#### 평균기온이 가장 높았던 TOP 10")
    top = table.sort_values("평균기온", ascending=False).head(10).reset_index(drop=True)
    top.index = [f"{i+1}위" for i in range(len(top))]
    cols3 = [c for c in ["연도", "시작", "종료", "평균기온", "최고기온",
                         "최저기온", "최저기온평균", "관측일수"] if c in top.columns]
    st.dataframe(top[cols3], use_container_width=True)

    idx_col = "연도" if "연도" in top.columns else "종료"
    st.bar_chart(top.set_index(top[idx_col].astype(str))[["평균기온"]], height=300)

# --- 탭4 ---
with tab4:
    sort_key = st.selectbox(
        "정렬 기준을 고르세요",
        ["평균기온", "최고기온", "최저기온", "최저기온평균",
         "최저기온최댓값", "일교차평균", "열대야일수", "영하일수"],
        index=0,
    )
    ascending = sort_key in ["최저기온", "최저기온평균", "영하일수"]
    full_tbl = table.sort_values(sort_key, ascending=ascending).reset_index(drop=True)
    full_tbl.insert(0, "순위", range(1, len(full_tbl) + 1))

    if key_col == "연도" and my_key in full_tbl["연도"].values:
        pos = int(full_tbl.index[full_tbl["연도"] == my_key][0]) + 1
        st.info(f"👉 선택하신 **{my_key}년** 기록은 '{sort_key}' 기준 **{pos}위**입니다.")

    st.dataframe(full_tbl, use_container_width=True, height=430)

    csv = full_tbl.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ 순위표 CSV 내려받기", csv,
                       file_name="seoul_rank.csv", mime="text/csv")


# ------------------------------------------------------------
# 9. 푸터
# ------------------------------------------------------------
st.markdown('<hr class="soft">', unsafe_allow_html=True)
st.markdown(
    '<p class="small-note">'
    '※ 결측이 많은 구간(6·25 전쟁기 등)은 순위 계산에서 자동 제외될 수 있습니다.<br>'
    '※ 공동 순위는 더 높은 순위로 표기합니다. (예: 값이 같으면 둘 다 3위)<br>'
    '※ 열대야·한파 기준은 기상청 정의를 참고한 값입니다.'
    '</p>',
    unsafe_allow_html=True
)
