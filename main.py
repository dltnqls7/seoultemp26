# ============================================================
#  서울 기온 순위 탐색기
#  - 두 날짜를 선택하면 그 기간의 기온이 역대 몇 위인지 알려줍니다.
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
# 1. 커스텀 스타일 (CSS) - 카드형 UI를 위한 최소한의 꾸밈
# ------------------------------------------------------------
st.markdown("""
<style>
/* 상단 여백 정리 */
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; }

/* 타이틀 배너 */
.hero {
    background: linear-gradient(135deg, #FF7E5F 0%, #FEB47B 50%, #86A8E7 100%);
    padding: 28px 32px;
    border-radius: 18px;
    color: white;
    margin-bottom: 22px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.hero h1 { margin: 0; font-size: 2.0rem; font-weight: 800; letter-spacing:-1px;}
.hero p  { margin: 8px 0 0 0; font-size: 0.98rem; opacity: 0.95; }

/* 순위 카드 */
.rank-card {
    border-radius: 16px;
    padding: 22px 20px;
    text-align: center;
    color: #fff;
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
    height: 100%;
}
.rank-card .label   { font-size: 0.92rem; opacity: 0.92; letter-spacing: 0.5px; }
.rank-card .rank    { font-size: 2.5rem; font-weight: 800; line-height: 1.15; margin: 6px 0 2px 0;}
.rank-card .total   { font-size: 0.85rem; opacity: 0.88; }
.rank-card .value   { font-size: 1.15rem; font-weight: 700; margin-top: 10px;
                      background: rgba(255,255,255,0.20); border-radius: 10px; padding: 6px 0;}

.c-hot  { background: linear-gradient(135deg,#F5515F 0%, #9F041B 100%); }
.c-cold { background: linear-gradient(135deg,#2193b0 0%, #6dd5ed 100%); }
.c-mean { background: linear-gradient(135deg,#7F00FF 0%, #E100FF 100%); }

/* 배지 */
.badge {
    display:inline-block; padding:5px 14px; border-radius:999px;
    background:#F1F3F5; color:#343A40; font-size:0.86rem; font-weight:600;
    margin-right:6px; margin-bottom:6px;
}
.small-note { color:#868E96; font-size:0.82rem; }
hr.soft { border:none; border-top:1px solid #E9ECEF; margin:18px 0; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# 2. 데이터 불러오기 (캐시로 속도 향상)
# ------------------------------------------------------------
@st.cache_data
def load_data():
    """seoul.csv를 읽어서 전처리한 DataFrame을 돌려준다."""
    # BOM(\ufeff) 제거를 위해 utf-8-sig 사용
    df = pd.read_csv("seoul.csv", encoding="utf-8-sig")

    # 컬럼명 앞뒤 공백 제거
    df.columns = [c.strip() for c in df.columns]

    # 날짜 앞 탭 문자/공백 제거 후 datetime 변환
    df["날짜"] = df["날짜"].astype(str).str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 기온 컬럼 숫자 변환
    for col in ["평균기온", "최저기온", "최고기온"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 날짜가 없는 행(마지막 빈 행 등) 제거
    df = df.dropna(subset=["날짜"]).copy()

    # 파생 컬럼
    df["연"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day
    df["월일"] = df["날짜"].dt.strftime("%m-%d")

    df = df.sort_values("날짜").reset_index(drop=True)
    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ 'seoul.csv' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 두세요.")
    st.stop()


# ------------------------------------------------------------
# 3. 헤더
# ------------------------------------------------------------
MIN_DATE = df["날짜"].min().date()
MAX_DATE = df["날짜"].max().date()

st.markdown(f"""
<div class="hero">
  <h1>🌡️ 서울 기온 순위 탐색기</h1>
  <p>기간을 고르면, 같은 기간(월·일 기준) 역대 기록 중 <b>몇 위</b>인지 알려드립니다.
     &nbsp;|&nbsp; 데이터 범위: <b>{MIN_DATE} ~ {MAX_DATE}</b> (총 {len(df):,}일)</p>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# 4. 사이드바 - 기간 선택
# ------------------------------------------------------------
with st.sidebar:
    st.header("📅 기간 선택")

    default_end = MAX_DATE
    default_start = default_end - datetime.timedelta(days=6)
    if default_start < MIN_DATE:
        default_start = MIN_DATE

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
        ["같은 월·일 기간끼리 (연도별 비교)", "역대 모든 같은 길이 구간"],
        index=0,
        help=(
            "① 예: 8/1~8/10을 골랐다면 1907년 8/1~8/10, 1908년 8/1~8/10 … 과 비교합니다.\n"
            "② 1년 중 아무 시점이나 같은 일수의 모든 구간과 비교합니다."
        ),
    )

    min_ratio = st.slider(
        "연도별 비교 시 최소 데이터 보유율(%)",
        0, 100, 80, step=5,
        help="해당 기간의 자료가 이 비율 미만인 연도는 순위 계산에서 제외합니다."
    )

    st.markdown("---")
    st.caption("📌 데이터: 기상청 기상자료개방포털 (지점 108, 서울)")


# 날짜 튜플 검증
if not isinstance(picked, (tuple, list)) or len(picked) != 2:
    st.info("👈 사이드바 달력에서 **종료일까지** 선택해 주세요.")
    st.stop()

start_date, end_date = picked
if start_date > end_date:
    start_date, end_date = end_date, start_date

n_days = (end_date - start_date).days + 1


# ------------------------------------------------------------
# 5. 선택 기간 요약
# ------------------------------------------------------------
sel = df[(df["날짜"].dt.date >= start_date) & (df["날짜"].dt.date <= end_date)]

if sel.empty:
    st.warning("선택한 기간에 데이터가 없습니다. 다른 기간을 선택해 주세요.")
    st.stop()

st.markdown(
    f'<span class="badge">🗓️ {start_date} ~ {end_date}</span>'
    f'<span class="badge">📏 {n_days}일</span>'
    f'<span class="badge">📊 실제 관측 {len(sel)}일</span>',
    unsafe_allow_html=True
)

sel_mean = sel["평균기온"].mean()
sel_max  = sel["최고기온"].max()
sel_min  = sel["최저기온"].min()


# ------------------------------------------------------------
# 6. 순위 계산 함수
# ------------------------------------------------------------
def rank_by_year(df, start_date, end_date, min_ratio):
    """같은 월·일 구간을 연도별로 묶어 통계를 낸다."""
    sm, sd = start_date.month, start_date.day
    em, ed = end_date.month, end_date.day
    cross_year = (sm, sd) > (em, ed)   # 연말~연초를 넘어가는 경우

    records = []
    years = sorted(df["연"].unique())
    for y in years:
        s = datetime.date(y, sm, sd) if not _valid(y, sm, sd) is False else None
        try:
            s = datetime.date(y, sm, sd)
            e = datetime.date(y + 1 if cross_year else y, em, ed)
        except ValueError:
            continue  # 2/29 같은 없는 날짜

        chunk = df[(df["날짜"].dt.date >= s) & (df["날짜"].dt.date <= e)]
        if chunk.empty:
            continue

        span = (e - s).days + 1
        ratio = len(chunk) / span * 100
        if ratio < min_ratio:
            continue

        records.append({
            "연도": y,
            "시작": s,
            "종료": e,
            "평균기온": round(chunk["평균기온"].mean(), 2),
            "최고기온": chunk["최고기온"].max(),
            "최저기온": chunk["최저기온"].min(),
            "관측일수": len(chunk),
        })
    return pd.DataFrame(records)


def _valid(y, m, d):
    try:
        datetime.date(y, m, d)
        return True
    except ValueError:
        return False


@st.cache_data
def rank_by_window(df, n_days):
    """역대 모든 n일 연속 구간의 이동 통계를 계산한다."""
    s = df.set_index("날짜")
    full = s.resample("D").asfreq()   # 빠진 날짜를 NaN으로 채워 연속성 확보

    res = pd.DataFrame(index=full.index)
    res["평균기온"] = full["평균기온"].rolling(n_days).mean().round(2)
    res["최고기온"] = full["최고기온"].rolling(n_days).max()
    res["최저기온"] = full["최저기온"].rolling(n_days).min()
    res["관측일수"] = full["평균기온"].rolling(n_days).count()

    res = res[res["관측일수"] >= n_days * 0.8]     # 결측 많은 구간 제외
    res = res.dropna(subset=["평균기온"])
    res["종료"] = res.index.date
    res["시작"] = (res.index - pd.Timedelta(days=n_days - 1)).date
    return res.reset_index(drop=True)


def ordinal_ko(rank, total, high_is_first=True):
    """순위를 사람이 읽기 좋은 문구로."""
    pct = rank / total * 100
    if rank == 1:
        return "🥇 역대 1위!", pct
    elif rank == 2:
        return "🥈 역대 2위", pct
    elif rank == 3:
        return "🥉 역대 3위", pct
    elif pct <= 5:
        return "🔥 상위 5% 이내", pct
    elif pct <= 10:
        return "✨ 상위 10% 이내", pct
    elif pct >= 95:
        return "🧊 하위 5% 이내", pct
    else:
        return "📊 평범한 편", pct


# ------------------------------------------------------------
# 7. 순위 산출
# ------------------------------------------------------------
if compare_mode.startswith("같은"):
    table = rank_by_year(df, start_date, end_date, min_ratio)
    unit_label = "개 연도"
    my_key = start_date.year
    key_col = "연도"
else:
    table = rank_by_window(df, n_days)
    unit_label = "개 구간"
    my_key = None
    key_col = None

if table.empty:
    st.warning("비교할 수 있는 과거 기록이 부족합니다. 조건을 완화해 보세요.")
    st.stop()

total_n = len(table)


def get_rank(series, value, descending=True):
    """value가 series 안에서 몇 번째로 크거나(작은) 값인지."""
    s = series.dropna()
    if descending:
        return int((s > value).sum()) + 1
    else:
        return int((s < value).sum()) + 1


rank_mean = get_rank(table["평균기온"], sel_mean, descending=True)
rank_max  = get_rank(table["최고기온"], sel_max,  descending=True)
rank_min  = get_rank(table["최저기온"], sel_min,  descending=False)

t_mean, p_mean = ordinal_ko(rank_mean, total_n)
t_max,  p_max  = ordinal_ko(rank_max,  total_n)
t_min,  p_min  = ordinal_ko(rank_min,  total_n)


# ------------------------------------------------------------
# 8. 결과 카드 3장
# ------------------------------------------------------------
st.markdown("### 🏆 이 기간의 역대 순위")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="rank-card c-mean">
      <div class="label">🌤️ 평균기온이 높은 순</div>
      <div class="rank">{rank_mean}위</div>
      <div class="total">전체 {total_n}{unit_label} 중 · 상위 {p_mean:.1f}%</div>
      <div class="value">{sel_mean:.2f} ℃</div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(t_mean)

with c2:
    st.markdown(f"""
    <div class="rank-card c-hot">
      <div class="label">🔥 기간 내 최고기온</div>
      <div class="rank">{rank_max}위</div>
      <div class="total">전체 {total_n}{unit_label} 중 · 상위 {p_max:.1f}%</div>
      <div class="value">{sel_max:.1f} ℃</div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(t_max)

with c3:
    st.markdown(f"""
    <div class="rank-card c-cold">
      <div class="label">🧊 기간 내 최저기온 (추운 순)</div>
      <div class="rank">{rank_min}위</div>
      <div class="total">전체 {total_n}{unit_label} 중 · 상위 {p_min:.1f}%</div>
      <div class="value">{sel_min:.1f} ℃</div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(t_min)

st.markdown('<hr class="soft">', unsafe_allow_html=True)


# ------------------------------------------------------------
# 9. 상세 탭
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📈 선택 기간 기온 변화", "🏅 역대 TOP 10", "📋 전체 순위표"])

# --- 탭1: 선택 기간 일별 그래프 ---
with tab1:
    st.markdown("#### 선택한 기간의 일별 기온")
    chart_df = sel.set_index("날짜")[["최고기온", "평균기온", "최저기온"]]
    st.line_chart(chart_df, height=340)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("기간 평균기온", f"{sel_mean:.2f} ℃")
    m2.metric("최고기온", f"{sel_max:.1f} ℃",
              help=str(sel.loc[sel['최고기온'].idxmax(), '날짜'].date()) if sel['최고기온'].notna().any() else None)
    m3.metric("최저기온", f"{sel_min:.1f} ℃",
              help=str(sel.loc[sel['최저기온'].idxmin(), '날짜'].date()) if sel['최저기온'].notna().any() else None)
    m4.metric("일교차 평균", f"{(sel['최고기온'] - sel['최저기온']).mean():.2f} ℃")

# --- 탭2: TOP 10 ---
with tab2:
    st.markdown("#### 평균기온이 가장 높았던 TOP 10")
    top = table.sort_values("평균기온", ascending=False).head(10).reset_index(drop=True)
    top.index = [f"{i+1}위" for i in range(len(top))]

    show_cols = [c for c in ["연도", "시작", "종료", "평균기온", "최고기온", "최저기온", "관측일수"]
                 if c in top.columns]
    st.dataframe(top[show_cols], use_container_width=True)

    st.markdown("#### 📊 TOP 10 평균기온 비교")
    if "연도" in top.columns:
        bar_df = top.set_index(top["연도"].astype(str))[["평균기온"]]
    else:
        bar_df = top.set_index(top["종료"].astype(str))[["평균기온"]]
    st.bar_chart(bar_df, height=300)

# --- 탭3: 전체 순위표 ---
with tab3:
    st.markdown("#### 전체 비교 대상 순위표 (평균기온 내림차순)")
    full_tbl = table.sort_values("평균기온", ascending=False).reset_index(drop=True)
    full_tbl.insert(0, "순위", range(1, len(full_tbl) + 1))

    # 내가 선택한 기간이 어디쯤인지 표시
    if key_col == "연도" and my_key in full_tbl["연도"].values:
        pos = full_tbl.index[full_tbl["연도"] == my_key][0] + 1
        st.info(f"👉 선택하신 **{my_key}년** 기록은 이 표에서 **{pos}위**입니다.")

    st.dataframe(full_tbl, use_container_width=True, height=420)

    csv = full_tbl.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ 순위표 CSV 내려받기", csv,
                       file_name="seoul_rank.csv", mime="text/csv")


# ------------------------------------------------------------
# 10. 푸터
# ------------------------------------------------------------
st.markdown('<hr class="soft">', unsafe_allow_html=True)
st.markdown(
    '<p class="small-note">'
    '※ 결측치가 많은 구간(6·25 전쟁기 등)은 순위 계산에서 자동 제외될 수 있습니다.<br>'
    '※ ‘같은 월·일 기간’ 비교는 윤년 2/29를 포함할 경우 일부 연도가 제외될 수 있습니다.'
    '</p>',
    unsafe_allow_html=True
)
