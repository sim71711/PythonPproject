import yfinance as yf
import pygame
import time
import datetime
import sys
import json
import os
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

SAVE_DIR = "saves"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):

    os.makedirs(CACHE_DIR)

# ----- 1. 데이터 준비: 여러 종목 데이터 다운로드 -----
TICKERS = {
    # 미국
    'AAPL': 'Apple',
    'GOOG': 'Google',
    'TSLA': 'Tesla',
    'MSFT': 'Microsoft',
    'AMZN': 'Amazon',
    'META': 'Meta',
    'NFLX': 'Netflix',
    'NVDA': 'Nvidia',
    'INTC': 'Intel',
    # 'AMD': 'AMD',
    # 'DIS': 'Disney',
    # 'IBM': 'IBM',
    # 'ORCL': 'Oracle',
    # 'PYPL': 'PayPal',
    # 'ADBE': 'Adobe',
    # 'QCOM': 'Qualcomm',
    # 'KO': 'CocaCola',
    # 'PEP': 'PepsiCo',
    # 'WMT': 'Walmart',
    # 'JNJ': 'Johnson & Johnson',
    # 'V': 'Visa',
    # 'MA': 'Mastercard',

    # 한국
    '005930.KS': '삼성전자',
    '000660.KS': 'SK하이닉스',
    '066570.KS': 'LG전자',
    '005380.KS': '현대차',
    '035420.KS': 'NAVER',
    '035720.KS': '카카오',

    # 대만
    # '2330.TW': 'TSMC',

    # 중국 (홍콩 상장)
    '9988.HK': 'Alibaba',
    '0700.HK': 'Tencent',
    # '3690.HK': 'Meituan',
    '1810.HK': 'Xiaomi',

    # 일본
    '6758.T': 'Sony',
    '9984.T': 'SoftBank',
    '7203.T': 'Toyota',

    # 유럽
    'AIR.PA': 'Airbus',
    'OR.PA': 'L’Oreal',
    'SIE.DE': 'Siemens',
    'BMW.DE': 'BMW',
    'SAP.DE': 'SAP',
    'AZN.L': 'AstraZeneca',

    # 남미 (브라질)
    'VALE': 'Vale (Brazil)',
    'PBR': 'Petrobras (Brazil)',

    # 캐나다
    'SHOP': 'Shopify',
    'RY': 'Royal Bank of Canada',

    # 인도
    'RELIANCE.NS': 'Reliance'
}


LAYOUT = {
    "screen": {"width": 1366, "height": 768},
    "chart": {"x": 478, "y": 50, "width": 751, "height": 268},
    "buttons": {
        "buy": {"width": 136, "height": 45, "offset_x": -341},
        "sell": {"width": 136, "height": 45, "offset_x": -163},
        "offset_y": 15
    },
    "stock_list": {
        "x": 30, "y_start": 100, "button_height": 35, "visible_height": 300,
        "title_x": 30, "title_y": 60
    },
    "grid": {
        "x": 30, "y_offset_from_bottom": 10,
        "cols": 5, "rows": 10,
        "cell_width": 273, "cell_height": 35
    },
    "portfolio": {
        "x": -273, "y_start": 100, "visible_height": 400, "line_height": 25
    },
    "alerts": {"x": 614, "y_base": 668, "line_height": 20, "max": 3},
    "profit_summary": {"x": -273, "y": 10},
    "rank_chart": {
        "x_from_grid": True,
        "offset_from_grid_x": 40,
        "offset_y": -15,
        "width": 683,
        "extra_height": 20
    },
    "cash": {"x": 30, "y": 30}
}


COMPANY_COLORS = {
    'AAPL': (255, 99, 132),
    'GOOG': (54, 162, 235),
    'TSLA': (255, 206, 86),
    'MSFT': (75, 192, 192),
    'AMZN': (153, 102, 255),
    'META': (255, 159, 64),
    'NFLX': (199, 199, 199),
    'NVDA': (83, 102, 255),
    'INTC': (255, 99, 255),
    'AMD': (99, 255, 132),
    'DIS': (100, 100, 100),
    'IBM': (255, 70, 70),
    'ORCL': (0, 230, 115),
    'PYPL': (204, 204, 0),
    'ADBE': (0, 153, 153),
    'QCOM': (102, 0, 204),
    'KO': (255, 51, 0)
}
mouse_x = 0
mouse_y = 0

buy_quantity = 1
quantity_input_mode = False
quantity_input_text = ""


comparison_scroll_offset_index = 0
comparison_tickers = []
comparison_tickers.clear()
comparison_mode = False  # 선택 모드 on/off
show_comparison_charts = False
start_comparison_button_rect = None

menu_new_game_rect = None
menu_continue_rect = None
menu_clear_cache_rect = None


default_save_file = "autosave.json"

input_mode = None  # "save" or "load"
input_text = ""  # 현재 입력 중인 텍스트
load_file_buttons = []  # load 모드일 때 파일 선택 버튼 저장

back_to_menu_rect = pygame.Rect(20, 20, 100, 30)
load_back_button_rect = pygame.Rect(20, 20, 100, 30)

chart_zoom_mode = False
chart_scroll_offset_index = 0
comparison_zoom_mode = False  # ✅ 비교 차트 줌 모드
chart_zoom_scale = 1.0
chart_zoom_center_ratio = 0.5


all_company_buttons = []
portfolio_scroll_offset = 0
PORTFOLIO_SCROLL_STEP = 20
PORTFOLIO_MAX_SCROLL = 0
PORTFOLIO_SUMMARY_HEIGHT = 100  # 투자 총합, 현재 가치, 수익률 텍스트 높이


stock_scroll_offset = 0
STOCK_SCROLL_STEP = 20
STOCK_MAX_SCROLL = 0

volumes_by_ticker = {}
prices_by_ticker = {}
dates_by_ticker = {}
first_available_date = {}  # 전역으로 선언해야 모든 함수에서 접근 가능
rank_history = {ticker: {} for ticker in TICKERS}  # 모든 티커에 대해 날짜별 순위 기록


start_date = "2000-01-01"  # 예: 2000년 1월 1일 부터
end_date = datetime.datetime.now().strftime("%Y-%m-%d")


current_day_index = 0  # 현재 시뮬레이션 날짜 인덱스
# 전역 변수 초기화
current_ticker_index = 0
current_ticker = list(TICKERS.keys())[0]
time_indices = {ticker: 0 for ticker in TICKERS}

scroll_offset = 0
MAX_SCROLL = 0  # 이후 버튼 길이에 따라 계산

# ----- 2. 게임 상태 초기화 -----
simulation_date_list = []
game_state = "menu"  # "menu", "playing"


portfolio = {
    'cash': 100000,
    'stocks': {ticker: {'quantity': 0, 'buy_price': 0} for ticker in TICKERS}
}
alerts = []



# ----- 3. Pygame 초기화 및 화면 설정 -----
pygame.init()

# 화면 해상도 정보 가져오기
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h

# 💡 세로 모드일 경우에도 강제로 가로로 세팅
if screen_height > screen_width:
    screen_width, screen_height = 1400, 700

# 작업표시줄과 타이틀바가 보이도록 화면에서 살짝 작게 설정 (예: -50 픽셀씩 줄임)
margin_x, margin_y = 50, 50
window_width = screen_width - margin_x
window_height = screen_height - margin_y



# 윈도우 타이틀과 닫기 버튼이 보이게 유지하기 위해 RESIZABLE 플래그 사용
screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)

# LAYOUT에도 반영하여 나머지 UI가 자동으로 조정됨
LAYOUT["screen"]["width"], LAYOUT["screen"]["height"] = window_width, window_height


pygame.display.set_caption("Stock Trading Simulator")
font = pygame.font.SysFont(None, 24)
clock = pygame.time.Clock()


# 주식 목록 버튼 정의
# ✅ 대체할 새로운 버튼 생성 코드
button_height = 40  # 버튼 높이 설정
stock_buttons = []
# 주식 목록 버튼 정의
stock_buttons = []
for i, ticker in enumerate(TICKERS):
    rect = pygame.Rect(50, 100 + i * button_height, 150, button_height)
    # 기본 rank=0, price=0으로 초기화
    stock_buttons.append((ticker, rect, 0, 0))


# ✅ 스크롤 최대 거리 계산 (아래 공간이 500 픽셀 기준일 때)
MAX_SCROLL = max(0, len(TICKERS) * button_height - 500)


# ----- 4. 함수 정의 -----
def get_stock_data(ticker):
    cache_file = os.path.join(CACHE_DIR, f"{ticker}.csv")
    should_update = True

    if os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file, index_col=0, nrows=5, encoding="utf-8-sig")
            if not set(required_cols).issubset(df.columns):
                raise ValueError("필수 컬럼 누락")

            required_cols = ["open", "high", "low", "close", "volume"]


            missing_cols = [col for col in required_cols if col not in df.columns]

            if df.empty or missing_cols:
                print(f"❌ {ticker} 캐시 오류 → 컬럼 없음 또는 데이터 비어있음 → 삭제함 (없음: {missing_cols})")
                os.remove(cache_file)
                should_update = True
            else:
                should_update = False
                return df
        except Exception as e:
            print(f"⚠ 캐시 파일 읽기 오류: {e}")
            os.remove(cache_file)

    if should_update:
        print(f"📡 캐시 갱신: {ticker}")
        try:
            time.sleep(1)  # ← 요거 추가!
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start_date, end=end_date, interval="1d", auto_adjust=False)
        except Exception as e:
            print(f"❌ {ticker} 다운로드 실패: {e}")
            return pd.DataFrame()

        # 컬럼 이름을 소문자로 변환
        df.columns = [col.lower() for col in df.columns]

        required_cols = ["open", "high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_cols):
            print(f"❌ {ticker} → 필요한 컬럼 없음 (컬럼들: {df.columns})")
            return pd.DataFrame()

        try:
            df_clean = pd.DataFrame({
                "open": pd.to_numeric(df["open"], errors="coerce"),
                "high": pd.to_numeric(df["high"], errors="coerce"),
                "low": pd.to_numeric(df["low"], errors="coerce"),
                "close": pd.to_numeric(df["close"], errors="coerce"),
                "volume": pd.to_numeric(df["volume"], errors="coerce"),
            }, index=df.index).dropna()

            df_clean.to_csv(cache_file, index=True, encoding="utf-8-sig")
            return df_clean

        except Exception as e:
            print(f"❌ {ticker} 데이터 정리 실패: {e}")
            return pd.DataFrame()


    
from concurrent.futures import ThreadPoolExecutor

def download_one(ticker):
    df = get_stock_data(ticker)
    if df.empty:
        return

    try:
        df = df.dropna(subset=["open", "high", "low", "close", "volume"])
        df = df.astype({
            "open": float, "high": float, "low": float, "close": float, "volume": int
        })
    except Exception as e:
        print(f"⚠️ {ticker} 변환 실패: {e}")
        return

    # 데이터 저장
    prices_by_ticker.update({
        f"{ticker}_Open": df["open"].tolist(),
        f"{ticker}_High": df["high"].tolist(),
        f"{ticker}_Low": df["low"].tolist(),
        f"{ticker}_Close": df["close"].tolist()
    })
    volumes_by_ticker[ticker] = df["volume"].tolist()
    dates_by_ticker[ticker] = [d.date() for d in df.index]
    first_available_date[ticker] = df.index[0].date()

def download_all_stock_data():
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(download_one, TICKERS)

    print("✅ 다운로드 완료된 종목들:", list(prices_by_ticker.keys()))
    print("✅ 정상 처리된 종목 수:", len(prices_by_ticker) // 4)
    if not prices_by_ticker:
        print("❌ 모든 종목 데이터 수집 실패. 캐시를 지우고 다시 시도하세요.")

def init_game():
    global simulation_date_list
    global game_state
    global current_ticker
    global comparison_tickers, comparison_mode, comparison_zoom_mode, show_comparison_charts, comparison_scroll_offset_index

    # ✅ 먼저 로딩 메시지를 보여주고
    screen.fill((0, 0, 0))
    loading_font = pygame.font.SysFont(None, 36)
    loading_text = loading_font.render("Downloading stock data...", True, (255, 255, 0))
    screen.blit(loading_text, (LAYOUT["screen"]["width"] // 2 - 150, LAYOUT["screen"]["height"] // 2))
    pygame.display.flip()

    # ✅ 그 다음 데이터를 다운로드함
    download_all_stock_data()
    
    print("📊 다운로드된 티커 확인:")
    for ticker in TICKERS:
        if f"{ticker}_Close" in prices_by_ticker:
            print(f"✅ {ticker} 차트 있음")
        else:
            print(f"❌ {ticker} 차트 없음 (prices_by_ticker에 없음)")


    all_dates = []
    for ticker_dates in dates_by_ticker.values():
        all_dates.extend(ticker_dates)

    if not all_dates:
        print("❗ 데이터가 부족해서 시뮬레이션 날짜 리스트를 만들 수 없습니다.")
        print("📌 캐시 폴더 내용을 지우고 다시 시도해보세요.")
        alerts.append(("❗ 데이터가 부족합니다. 캐시 삭제 후 다시 시도하세요.", time.time()))
        return

    # 여기 추가 로그!
    print("📅 날짜 예시:", all_dates[:5])
    print(f"[디버그] prices_by_ticker 키 목록: {list(prices_by_ticker.keys())[:5]}")

    simulation_date_list = sorted(set(all_dates))  # 만약 all_dates가 date 객체면 이대로 OK
    if isinstance(simulation_date_list[0], str):
        simulation_date_list = [datetime.datetime.strptime(d, "%y.%m.%d").date() for d in simulation_date_list]

    simulation_date_list.sort()

    print(f"[디버그] simulation_date_list 길이: {len(simulation_date_list)}")
    # ✅ 여기서 출력하는 것이 맞음
    print(f"[디버그] 최종 simulation_date_list 길이: {len(simulation_date_list)}")

    print(f"✅ prices_by_ticker 수: {len(prices_by_ticker)}")
    print(f"✅ dates_by_ticker 수: {len(dates_by_ticker)}")
    print(f"✅ simulation_date_list 수: {len(simulation_date_list)}")

    if not simulation_date_list:
        print("❌ 시뮬레이션 날짜 리스트 없음. 게임을 종료합니다.")
        sys.exit()
    # ✅ 마지막에 게임 상태 전환 추가
    game_state = "menu"
    # simulation_date_list가 생성된 후에 이걸로 설정
    if prices_by_ticker:
        for key in prices_by_ticker.keys():
            if key.endswith("_Open"):
                ticker = key.replace("_Open", "")
                # 날짜 타입이 datetime.date인지 확인 후 비교
                if (ticker in first_available_date and 
                    isinstance(first_available_date[ticker], datetime.date) and 
                    first_available_date[ticker] <= simulation_date_list[0]):
                    current_ticker = ticker
                    print(f"✅ 초기 종목 설정: {ticker}, 상장일: {first_available_date[ticker]}")
                    break
        # 🔧 비교 모드 상태 초기화
    comparison_tickers.clear()
    comparison_mode = False
    comparison_zoom_mode = False
    show_comparison_charts = False
    comparison_scroll_offset_index = 0




def clear_cache():
    deleted = 0
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith(".csv"):
            os.remove(os.path.join(CACHE_DIR, fname))
            deleted += 1
    alerts.append((f"🗑️ 캐시 {deleted}개 삭제됨", time.time()))


def save_game(filename=None):
    try:
        if filename is None:
            filename = default_save_file
            if not filename.endswith(".json"):
                filename += ".json"

        # ✅ 저장 경로 구성
        filepath = os.path.join(SAVE_DIR, filename)
        temp_filename = filepath + ".tmp"

        recent_days = simulation_date_list[max(0, current_day_index - 100): current_day_index + 1]
        rank_history_trimmed = {
            t: {str(day): rank for day, rank in ranks.items() if day in recent_days}
            for t, ranks in rank_history.items()
        }

        save_data = {
            "portfolio": portfolio,
            "current_day_index": current_day_index,
            "time_indices": time_indices,
            "current_ticker": current_ticker,
            "rank_history": rank_history_trimmed
        }

        with open(temp_filename, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2)
        os.replace(temp_filename, filepath)

        alerts.append((f"{filename} 저장 완료", time.time()))
        print(f"[Saved] {filepath}")
    except Exception as e:
        alerts.append((f"저장 오류: {str(e)}", time.time()))
        print("저장 중 오류 발생:", e)


def load_game(filename=None):
    global portfolio, current_day_index, time_indices, current_ticker, rank_history, game_state

    try:
        if filename is None:
            save_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
            if not save_files:
                alerts.append(("⚠ 저장된 파일이 없습니다.", time.time()))
                return
            
            print("📂 저장된 파일 목록:")
            for i, f in enumerate(save_files):
                print(f"{i+1}. {f}")
            choice = int(input("불러올 번호 선택: ")) - 1
            filename = save_files[choice]

        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            portfolio = data["portfolio"]
            current_day_index = data["current_day_index"]
            time_indices = data["time_indices"]
            current_ticker = data["current_ticker"]

            raw_rank_history = data["rank_history"]
            rank_history = {}
            for ticker, ranks in raw_rank_history.items():
                rank_history[ticker] = {
                    datetime.datetime.strptime(date_str, "%Y-%m-%d").date(): rank
                    for date_str, rank in ranks.items()
                }

        alerts.append((f"{filename} 불러오기 완료", time.time()))
        game_state = "playing"  # <-- 게임 화면으로 전환


    except Exception as e:
        print("게임 불러오기 오류:", e)



def draw_load_file_buttons():
    global load_file_buttons
    load_file_buttons = []

    # 🔙 뒤로가기 버튼
    pygame.draw.rect(screen, (150, 150, 150), load_back_button_rect)
    draw_text("Menu", load_back_button_rect.x + 10, load_back_button_rect.y + 5)

    save_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    start_y = 160
    for i, fname in enumerate(save_files):
        btn_rect = pygame.Rect(LAYOUT["screen"]["width"] // 2 - 150, start_y + i * 45, 300, 40)
        pygame.draw.rect(screen, (70, 70, 70), btn_rect)
        pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2)
        draw_text(fname, btn_rect.x + 10, btn_rect.y + 10)
        
        delete_rect = pygame.Rect(btn_rect.right + 10, btn_rect.y, 80, btn_rect.height)
        pygame.draw.rect(screen, (200, 50, 50), delete_rect)
        draw_text("Delete", delete_rect.x + 5, delete_rect.y + 10)

        load_file_buttons.append((fname, btn_rect, delete_rect))


def get_layout_x(key):
    x = LAYOUT[key]["x"]
    if x < 0:
        x = LAYOUT["screen"]["width"] + x
    return x


def adjust_layout_for_orientation():
    return  # <- 아무것도 안 하게 만들기


def draw_buttons(prev_y):
    button_layout = LAYOUT["buttons"]
    screen_width = LAYOUT["screen"]["width"]

    # offset_x가 음수일 경우 오른쪽 정렬
    buy_x = screen_width + button_layout["buy"]["offset_x"]
    sell_x = screen_width + button_layout["sell"]["offset_x"]
    button_y = prev_y + 10

    buy_rect = pygame.Rect(buy_x, button_y, button_layout["buy"]["width"], button_layout["buy"]["height"])
    sell_rect = pygame.Rect(sell_x, button_y, button_layout["sell"]["width"], button_layout["sell"]["height"])

    pygame.draw.rect(screen, (70, 130, 180), buy_rect)
    pygame.draw.rect(screen, (180, 70, 70), sell_rect)

    screen.blit(font.render("Buy", True, (255, 255, 255)), (buy_rect.x + 50, buy_rect.y + 15))
    screen.blit(font.render("Sell", True, (255, 255, 255)), (sell_rect.x + 50, sell_rect.y + 15))

    return buy_rect, sell_rect


def draw_chart(prices, dates):
    print(f"[디버그] draw_chart 호출됨 ✅")
    print(f"  └─ prices 길이: {len(prices)}")
    print(f"  └─ dates 길이: {len(dates)}")

    current_index = min(time_indices[current_ticker], len(prices_by_ticker[f"{current_ticker}_Close"]) - 1)
    
    # 차트 위치와 크기
    chart_layout = LAYOUT["chart"]
    offset_x = chart_layout["x"]
    offset_y = chart_layout["y"]
    width = chart_layout["width"]
    height = chart_layout["height"]

    if len(prices) < 2:
        draw_text("No price variation", offset_x, offset_y + height // 2, (200, 100, 100))
        return

    draw_text(f"Stock Chart: {TICKERS[current_ticker]} ({current_ticker})", offset_x, offset_y - 30, (255, 255, 0))
    
    # 보여줄 범위
    start_index = max(0, current_index - int(width))
    dates_view = dates[start_index:current_index + 1]

    opens = prices_by_ticker[current_ticker + "_Open"][start_index:current_index + 1]
    highs = prices_by_ticker[current_ticker + "_High"][start_index:current_index + 1]
    lows = prices_by_ticker[current_ticker + "_Low"][start_index:current_index + 1]
    closes = prices_by_ticker[current_ticker + "_Close"][start_index:current_index + 1]

    if not (opens and closes and highs and lows):
        return
    
    vols = volumes_by_ticker.get(current_ticker, [])[start_index:current_index + 1]
    max_volume = max(vols) if vols else 1


    # 가격 범위 계산은 딱 1번만!
    max_price = max(highs)
    min_price = min(lows)

    if max_price == min_price:
        draw_text("⚠ 가격 변화 없음", offset_x, offset_y + height // 2, (200, 100, 100))
        return

    scale = height / (max_price - min_price)
    bar_width = width / len(closes)
    # bar_width = min(bar_width, 10)  # ✅ 이 줄 추가

    # 캔들 차트 그리기
    for i in range(len(closes)):
        o = opens[i]
        h = highs[i]
        l = lows[i]
        c = closes[i]

        color = (255, 0, 0) if c > o else (0, 128, 255)

        x = offset_x + i * bar_width
        y_open = offset_y + height - (o - min_price) * scale
        y_close = offset_y + height - (c - min_price) * scale
        y_high = offset_y + height - (h - min_price) * scale
        y_low = offset_y + height - (l - min_price) * scale

        # 십자선 (위꼬리 + 아래꼬리)
        pygame.draw.line(screen, color, (x + bar_width / 2, y_high), (x + bar_width / 2, y_low), 1)

        # 몸통
        top = min(y_open, y_close)
        body_height = max(abs(y_open - y_close), 1)
        pygame.draw.rect(screen, color, (x, top, bar_width * 0.8, body_height))

    # Y축 눈금
    price_range = max_price - min_price
    num_horizontal = min(max(int(price_range // 10), 4), 10)
    price_step = price_range / num_horizontal

    for i in range(num_horizontal + 1):
        y_line = offset_y + i * (height / num_horizontal)
        pygame.draw.line(screen, (80, 80, 80), (offset_x, y_line), (offset_x + width, y_line), 1)
        price_tick = max_price - i * price_step
        draw_text(f"${price_tick:.2f}", offset_x - 60, y_line - 10, (200, 200, 200))

    # X축 눈금
    num_vertical = 6
    for j in range(num_vertical + 1):
        x_line = offset_x + j * (width / num_vertical)
        pygame.draw.line(screen, (80, 80, 80), (x_line, offset_y), (x_line, offset_y + height), 1)
        index = int(j * (len(dates_view) - 1) / num_vertical)
        date_label = dates_view[index]

        # 날짜 문자열이 아닌 경우도 다루기
        if isinstance(date_label, (datetime.datetime, datetime.date)):
            label = date_label.strftime("%y.%m.%d")
        elif isinstance(date_label, str):
            try:
                parsed = datetime.datetime.strptime(date_label, "%Y-%m-%d")
                label = parsed.strftime("%y.%m.%d")
            except:
                try:
                    parsed = datetime.datetime.strptime(date_label, "%y.%m.%d")
                    label = parsed.strftime("%y.%m.%d")
                except:
                    label = date_label  # 최악의 경우 그냥 출력
        else:
            label = str(date_label)



        draw_text(label, x_line - 25, offset_y + height + 5, (200, 200, 200))

        # ✅ 선 그래프 덧그리기 (초록색 선)
    points = []
    for i, price in enumerate(closes):
        x_point = offset_x + i * bar_width
        y_point = offset_y + height - (price - min_price) * scale
        points.append((float(x_point), float(y_point)))

    if len(points) >= 2:
        pygame.draw.lines(screen, (0, 255, 0), False, points, 2)  # 초록색 선


    # 🔵 거래량 그리기
    volume_height = 100
    volume_offset_y = offset_y + height + 20

    if vols and max(vols) > 0:
        for j, v in enumerate(vols):
            vol_height = max(3, (v / max_volume) * volume_height)
            x = offset_x + j * bar_width
            pygame.draw.rect(screen, (100, 200, 255),
                             (x, volume_offset_y + volume_height - vol_height, bar_width * 0.8, vol_height))
        draw_text("Volume", offset_x, volume_offset_y - 20, (100, 200, 255))


def draw_comparison_charts_candlestick():
    offset_x = 80
    offset_y = 80
    chart_width = LAYOUT["screen"]["width"] - 160
    chart_height = 140  # 🔽 줄임
    volume_height = 50  # 🔽 줄임

    spacing_y = 30

    if not comparison_tickers:
        return

    for idx, ticker in enumerate(comparison_tickers):
        start_y = offset_y + idx * (chart_height + volume_height + spacing_y) - comparison_scroll_offset_index
        close_key = f"{ticker}_Close"
        open_key = f"{ticker}_Open"
        high_key = f"{ticker}_High"
        low_key = f"{ticker}_Low"
        vols = volumes_by_ticker.get(ticker, [])

        if close_key not in prices_by_ticker:
            continue

        # 🔄 날짜 기준으로 슬라이싱 범위 조정
        today = simulation_date_list[current_day_index]
        date_list = dates_by_ticker[ticker]
        index = 0
        for i, d in enumerate(date_list):
            d_obj = d if isinstance(d, datetime.date) else datetime.datetime.strptime(str(d), "%Y-%m-%d").date().strptime(str(d), "%Y-%m-%d").date()
            if d_obj > today:
                break
            index = i

        closes = prices_by_ticker[close_key][:index + 1]
        opens = prices_by_ticker[open_key][:index + 1]
        highs = prices_by_ticker[high_key][:index + 1]
        lows = prices_by_ticker[low_key][:index + 1]
        vols = volumes_by_ticker[ticker][:index + 1]


        if len(closes) < 2:
            continue

        max_price = max(highs)
        min_price = min(lows)
        price_scale = chart_height / (max_price - min_price + 1)
        bar_width = chart_width / len(closes)
        max_volume = max(vols) if vols else 1

        # 📊 캔들 차트 그리기
        for i in range(len(closes)):
            o = opens[i]
            h = highs[i]
            l = lows[i]
            c = closes[i]
            color = (255, 0, 0) if c >= o else (0, 128, 255)

            x = offset_x + i * bar_width
            y_open = start_y + chart_height - (o - min_price) * price_scale
            y_close = start_y + chart_height - (c - min_price) * price_scale
            y_high = start_y + chart_height - (h - min_price) * price_scale
            y_low = start_y + chart_height - (l - min_price) * price_scale

            pygame.draw.line(screen, color, (x + bar_width / 2, y_high), (x + bar_width / 2, y_low), 1)
            top = min(y_open, y_close)
            height = max(abs(y_open - y_close), 1)
            pygame.draw.rect(screen, color, (x, top, bar_width * 0.8, height))

        # 🔵 거래량 (캔들 루프 밖에서!)
                # 🔵 거래량 (캔들 루프 밖에서!)
        if vols and max(vols) > 0:
            for j, v in enumerate(vols):
                vol_height = (v / max_volume) * volume_height
                x = offset_x + j * bar_width
                pygame.draw.rect(screen, (100, 200, 255),
                                 (x, start_y + chart_height + volume_height - vol_height, bar_width * 0.8, vol_height))

            draw_text("Volume", offset_x, start_y + chart_height + volume_height + 5, (100, 200, 255))


        # 선 그래프
        points = []
        for i, price in enumerate(closes):
            x_point = offset_x + i * bar_width
            y_point = start_y + chart_height - (price - min_price) * price_scale
            points.append((float(x_point), float(y_point)))

        if len(points) >= 2:
            pygame.draw.lines(screen, (0, 255, 0), False, points, 2)

        # 텍스트
        draw_text("Volume", offset_x, start_y + chart_height + volume_height + 5, (100, 200, 255))
        draw_text(f"{TICKERS[ticker]} ({ticker})", offset_x, start_y - 20, (255, 255, 0))




def draw_volume_bars(volumes, offset_x, offset_y, width, height):
    if len(volumes) < 2:
        return

    max_volume = max(volumes)
    if max_volume == 0:
        return

    bar_width = width / len(volumes)
    for i, volume in enumerate(volumes):
        x = offset_x + i * bar_width
        bar_height = max(3, (volume / max_volume) * height)
        y = offset_y + height - bar_height
        pygame.draw.rect(screen, (100, 200, 255), (x, y, bar_width * 0.9, bar_height))
    
    if not volumes or max(volumes) == 0:
        print("⚠️ 거래량이 비어있거나 0입니다.")
        return




def draw_portfolio_summary():
    portfolio_layout = LAYOUT["portfolio"]
    screen_height = LAYOUT["screen"]["height"]
    button_height = LAYOUT["buttons"]["buy"]["height"]
    button_offset_y = LAYOUT["buttons"]["offset_y"]

    # 버튼이 있는 위치보다 위에서만 보여지도록 제한
    max_visible_bottom = screen_height - button_height - button_offset_y - 20
    visible_height = max_visible_bottom - portfolio_layout["y_start"]

    x = portfolio_layout["x"]
    if x < 0:
        x = LAYOUT["screen"]["width"] + x

    y_start = portfolio_layout["y_start"]
    y = y_start - portfolio_scroll_offset
    line_height = portfolio_layout["line_height"]
    total_items = 0

    draw_text("Portfolio", x, y - 40, (255, 255, 0))

    total_invested = 0.0
    total_current_value = 0.0

    for ticker, data in portfolio["stocks"].items():
        quantity = data["quantity"]
        if quantity == 0:
            continue

        if y > max_visible_bottom:
            break  # 화면 아래로 넘어가면 출력 중단

        index = min(time_indices[ticker], len(prices_by_ticker[f"{ticker}_Close"]) - 1)
        current_price = float(prices_by_ticker[f"{ticker}_Close"][index])

        avg_price = data["buy_price"]
        profit_percent = ((current_price - avg_price) / avg_price) * 100
        color = (255, 0, 0) if profit_percent >= 0 else (0, 128, 255)
        company_name = TICKERS[ticker]

        draw_text(f"{company_name} ({ticker})", x, y, (255, 255, 255))
        draw_text(f"{quantity}주 @ {avg_price:.2f}", x, y + 15, (200, 200, 200))
        draw_text(f"{profit_percent:+.2f}%", x + 150, y + 15, color)

        y += line_height + 10
        total_items += 1

        total_invested += quantity * avg_price
        total_current_value += quantity * current_price

    # 수익 계산
    if total_invested > 0:
        total_profit = total_current_value - total_invested
        profit_percent = (total_profit / total_invested) * 100
    else:
        total_profit = 0
        profit_percent = 0

    color = (255, 0, 0) if profit_percent >= 0 else (0, 128, 255)

    y += 20
    if y <= max_visible_bottom:
        draw_text(f"Total Invested: ${total_invested:.2f}", x, y, (255, 255, 255))
        draw_text(f"Current Value: ${total_current_value:.2f}", x, y + 20, (255, 255, 255))
        draw_text(f"Total Profit: ${total_profit:+.2f} ({profit_percent:+.2f}%)", x, y + 40, color)

    # 스크롤 계산
    content_height = (total_items * (line_height + 10)) + 100
    global PORTFOLIO_MAX_SCROLL
    PORTFOLIO_MAX_SCROLL = max(0, content_height - visible_height)

    return y + 70


def cash():
    x = LAYOUT["cash"]["x"]
    y = LAYOUT["cash"]["y"]
    draw_text(f"Cash: ${float(portfolio['cash']):.2f}", x, y)


def draw_all_companies_grid():
    global start_comparison_button_rect
    global mode_button_rect
    global start_comparison_button_rect
    # 비교 모드 진입/종료 버튼 (항상 표시)
    mode_button_text = " end select mode" if comparison_mode else " start select mode"
    mode_button_color = (200, 100, 100) if comparison_mode else (100, 200, 100)
    mode_button_rect = pygame.Rect(LAYOUT["screen"]["width"] - 250, 20, 220, 30)
    pygame.draw.rect(screen, mode_button_color, mode_button_rect)
    draw_text(mode_button_text, mode_button_rect.x + 10, mode_button_rect.y + 5)

    today = simulation_date_list[current_day_index]
    visible_companies = [
        ticker for ticker in TICKERS
        if ticker in first_available_date and first_available_date[ticker] <= today
    ]

    visible_companies.sort(key=lambda t: first_available_date[t])
    
    grid_x = LAYOUT["grid"]["x"]
    cell_width = LAYOUT["grid"]["cell_width"]
    cell_height = LAYOUT["grid"]["cell_height"]
    cols = LAYOUT["grid"]["cols"]
    rows = LAYOUT["grid"]["rows"]

    grid_height = cell_height * rows
    grid_y = LAYOUT["screen"]["height"] - grid_height - LAYOUT["grid"]["y_offset_from_bottom"]

    all_company_buttons.clear()

    total_cells = cols * rows

    for idx in range(total_cells):
        col = idx % cols
        row = idx // cols
        x = grid_x + col * cell_width
        y = grid_y + row * cell_height - comparison_scroll_offset_index  # ✅ 수정된 줄

        rect = pygame.Rect(x, y, cell_width, cell_height)


        if idx < len(visible_companies):
            ticker = visible_companies[idx]
            pygame.draw.rect(screen, (80, 80, 80), rect, 2)
            draw_text(f"{TICKERS[ticker]} ({ticker})", x + 5, y + 5)

            if comparison_mode:
                # 선택/해제 버튼 추가
                button_rect = pygame.Rect(x + cell_width - 70, y + 5, 60, 20)
                if ticker in comparison_tickers:
                    pygame.draw.rect(screen, (200, 70, 70), button_rect)
                    draw_text("Deselect", button_rect.x + 10, button_rect.y + 2)
                else:
                    pygame.draw.rect(screen, (70, 180, 70), button_rect)
                    draw_text("Select", button_rect.x + 10, button_rect.y + 2)

                all_company_buttons.append((ticker, rect, button_rect))  # 버튼 좌표도 추가
            else:
                all_company_buttons.append((ticker, rect, None))  # 버튼은 없음

    global start_comparison_button_rect
    button_width = 200
    button_height = 30
    start_button_x = LAYOUT["screen"]["width"] - button_width - 30
    start_button_y = grid_y - button_height - 10  # 그리드 내부에 위치
    
    start_comparison_button_rect = pygame.Rect(start_button_x, start_button_y, button_width, button_height)
    
    # 비교 실행 버튼 항상 표시되도록 수정
    pygame.draw.rect(screen, (80, 80, 80), start_comparison_button_rect)  # 기본 회색 배경

    if comparison_mode:
        if len(comparison_tickers) >= 1:
            pygame.draw.rect(screen, (100, 200, 100), start_comparison_button_rect)
        else:
            pygame.draw.rect(screen, (120, 120, 120), start_comparison_button_rect)
        draw_text("선택한 차트 비교 실행", start_button_x + 20, start_button_y + 5)
    else:
        draw_text("(비교모드에서만 사용 가능)", start_button_x + 10, start_button_y + 5, (160, 160, 160))


def draw_stock_list(visible_companies):
    draw_text("Current Stock Rankings", LAYOUT["stock_list"]["title_x"], LAYOUT["stock_list"]["title_y"], (255, 255, 0))
    today = simulation_date_list[current_day_index]

    current_prices = []
    for ticker in visible_companies:
        index = min(time_indices[ticker], len(prices_by_ticker[f"{ticker}_Close"]) - 1)
        current_price = prices_by_ticker[f"{ticker}_Close"][index]

        current_prices.append((ticker, current_price))
    
    current_prices.sort(key=lambda x: x[1], reverse=True)

    stock_buttons.clear()
    top_10 = current_prices[:10]  # ✅ 10개만 잘라서 보여줌

    for rank, (ticker, price) in enumerate(top_10, start=1):
        rect = pygame.Rect(50, 100 + len(stock_buttons) * button_height, 250, button_height)
        stock_buttons.append((ticker, rect, rank, price))

    # ✅ 여기를 아래로 이동
    rank_today = {ticker: rank for rank, (ticker, _) in enumerate(current_prices, start=1)}
    for ticker in rank_today:
        rank_history[ticker][today] = rank_today[ticker]

    for ticker, rect, rank, price in stock_buttons:
        shifted_rect = pygame.Rect(rect.x, rect.y - stock_scroll_offset, rect.width, rect.height)
        pygame.draw.rect(screen, (100, 100, 100), shifted_rect)
        text = font.render(f"{rank}. {TICKERS[ticker]} ({ticker}) - ${price:.2f}", True, (255, 255, 255))
        screen.blit(text, (shifted_rect.x + 10, shifted_rect.y + 5))

    # 스크롤 최대 거리 계산
    global STOCK_MAX_SCROLL
    STOCK_MAX_SCROLL = max(0, len(top_10) * button_height - 400)


def draw_text(text, x, y, color=(255, 255, 255)):
    render = font.render(text, True, color)
    screen.blit(render, (x, y))

def draw_input_box():
    global input_text
    box_rect = pygame.Rect(LAYOUT["screen"]["width"] // 2 - 150, 100, 300, 40)
    pygame.draw.rect(screen, (255, 255, 255), box_rect)
    pygame.draw.rect(screen, (0, 0, 0), box_rect, 2)
    draw_text(input_text, box_rect.x + 10, box_rect.y + 10, (0, 0, 0))

    # 🔙 뒤로가기 버튼
    pygame.draw.rect(screen, (150, 150, 150), load_back_button_rect)
    draw_text("Menu", load_back_button_rect.x + 10, load_back_button_rect.y + 5)



def update_intraday_data():
    # 최신 1일치 인트라데이 데이터를 가져오는 예제
    global prices_by_ticker, dates_by_ticker

def sell_stock(ticker):
    global alerts, buy_quantity
    info = portfolio['stocks'][ticker]
    quantity = info['quantity']
    if quantity == 0:
        alerts.append((f"No {ticker} to sell", time.time()))
        return

    index = min(time_indices[ticker], len(prices_by_ticker[f"{ticker}_Close"]) - 1)
    price = float(prices_by_ticker[f"{ticker}_Close"][index])
    sell_qty = min(buy_quantity, quantity)

    portfolio['cash'] += price * sell_qty
    info['quantity'] -= sell_qty
    if info['quantity'] == 0:
        info['buy_price'] = 0
    alerts.append((f"Sold {sell_qty} {ticker}", time.time()))
    buy_quantity = 1



def buy_stock(ticker):
    global alerts, buy_quantity
    index = min(time_indices[ticker], len(prices_by_ticker[f"{ticker}_Close"]) - 1)
    price = float(prices_by_ticker[f"{ticker}_Close"][index])
    total_cost = price * buy_quantity

    if portfolio['cash'] >= total_cost:
        portfolio['cash'] -= total_cost
        info = portfolio['stocks'][ticker]
        total_qty = info['quantity']
        avg_price = info['buy_price']
        new_total_cost = total_qty * avg_price + total_cost
        new_total_qty = total_qty + buy_quantity
        info['quantity'] = new_total_qty
        info['buy_price'] = new_total_cost / new_total_qty
        alerts.append((f"Bought {buy_quantity} {ticker}", time.time()))


    else:
        # 가능한 최대 수량만큼이라도 구매 시도
        max_qty = int(portfolio['cash'] // price)
        if max_qty >= 1:
            portfolio['cash'] -= price * max_qty
            info = portfolio['stocks'][ticker]
            total_qty = info['quantity']
            avg_price = info['buy_price']
            new_total_cost = total_qty * avg_price + price * max_qty
            new_total_qty = total_qty + max_qty
            info['quantity'] = new_total_qty
            info['buy_price'] = new_total_cost / new_total_qty
            alerts.append((f"Partially bought {max_qty} {ticker}", time.time()))
        else:
            alerts.append((f"Not enough cash to buy {buy_quantity} {ticker}", time.time()))

    buy_quantity = 1



def draw_alerts():
    now = time.time()
    duration = 1.5  # 초단위, 몇 초 동안 보여줄지

    # 오래된 메시지 제거
    alerts[:] = [entry for entry in alerts if now - entry[1] <= duration]

    # 최근 메시지 3개만 보여줌
    for i, (msg, _) in enumerate(alerts[-3:]):
        x = LAYOUT["alerts"]["x"]
        y_base = LAYOUT["alerts"]["y_base"]
        line_height = LAYOUT["alerts"]["line_height"]
        draw_text(msg, x, y_base + i * line_height, (255, 255, 0))


def draw_total_profit():
    total_invested = 0.0
    total_current_value = 0.0

    for ticker, data in portfolio["stocks"].items():
        quantity = data["quantity"]
        if quantity > 0:
            invested = quantity * data["buy_price"]
            current_price = float(prices_by_ticker[f"{ticker}_Close"][time_indices[ticker]])
            current_value = quantity * current_price
            total_invested += invested
            total_current_value += current_value

    if total_invested > 0:
        total_profit = total_current_value - total_invested
        profit_percent = (total_profit / total_invested) * 100
    else:
        total_profit = 0
        profit_percent = 0

    color = (255, 0, 0) if profit_percent >= 0 else (0, 128, 255)

    x = LAYOUT["profit_summary"]["x"]
    if x < 0:
        x = LAYOUT["screen"]["width"] + x
    y = LAYOUT["profit_summary"]["y"]

    draw_text(f"Total Invested: ${total_invested:.2f}", x, y, (255, 255, 255))
    draw_text(f"Current Value: ${total_current_value:.2f}", x, y + 20, (255, 255, 255))
    draw_text(f"Total Profit: ${total_profit:+.2f} ({profit_percent:+.2f}%)", x, y + 40, color)


def get_sorted_visible_stocks():
    today = simulation_date_list[current_day_index]
    visible = []

    for ticker in TICKERS:
        if ticker in first_available_date and first_available_date[ticker] <= today:
            quantity = portfolio["stocks"][ticker]["quantity"]
            price_index = min(time_indices[ticker], len(prices_by_ticker[ticker]) - 1)
            current_price = prices_by_ticker[ticker][price_index]
            total_value = quantity * current_price
            visible.append((ticker, total_value))

    # 가치 기준 정렬 (내림차순)
    visible.sort(key=lambda x: -x[1])
    return visible
def draw_zoomed_chart_like_chart():
    close_key = f"{current_ticker}_Close"
    if close_key not in prices_by_ticker:
        return

    prices = prices_by_ticker[close_key]
    opens = prices_by_ticker[f"{current_ticker}_Open"]
    highs = prices_by_ticker[f"{current_ticker}_High"]
    lows = prices_by_ticker[f"{current_ticker}_Low"]
    closes = prices_by_ticker[f"{current_ticker}_Close"]
    dates = dates_by_ticker[current_ticker]

    chart_layout = {"x": 80, "y": 80, "width": LAYOUT["screen"]["width"] - 160, "height": 450}
    offset_x = chart_layout["x"]
    offset_y = chart_layout["y"]
    width = chart_layout["width"]
    height = chart_layout["height"]

    screen.fill((0, 0, 0))
    global chart_scroll_offset_index
    current_index = min(time_indices[current_ticker], len(closes) - 1)
    total_len = current_index + 1
    view_len = int(total_len * chart_zoom_scale)
    
    # ✅ 스크롤 인덱스 범위 제한
    chart_scroll_offset_index = max(0, min(chart_scroll_offset_index, total_len - view_len))
    
    # ✅ start, end를 스크롤 인덱스로 계산
    start_index = chart_scroll_offset_index
    end_index = min(total_len, start_index + view_len)


    # 슬라이싱
    dates = dates[start_index:end_index]
    opens = opens[start_index:end_index]
    highs = highs[start_index:end_index]
    lows = lows[start_index:end_index]
    closes = closes[start_index:end_index]
    volumes = volumes_by_ticker.get(current_ticker, [])[start_index:end_index]

    dates = dates[:current_index + 1]
    opens = opens[:current_index + 1]
    highs = highs[:current_index + 1]
    lows = lows[:current_index + 1]
    closes = closes[:current_index + 1]

    if not highs or not lows:
        draw_text("⚠ 확대할 데이터가 부족합니다.", offset_x, offset_y + height // 2, (255, 100, 100))
        return

    max_price = max(highs)
    min_price = min(lows)
    
    if max_price == min_price:
        draw_text("⚠ 가격 변화 없음", offset_x, offset_y + height // 2, (200, 100, 100))
        return

    scale = height / (max_price - min_price)
    bar_width = width / len(closes)

    for i in range(len(closes)):
        o = opens[i]
        h = highs[i]
        l = lows[i]
        c = closes[i]

        color = (255, 0, 0) if c > o else (0, 128, 255)

        x = offset_x + i * bar_width
        y_open = offset_y + height - (o - min_price) * scale
        y_close = offset_y + height - (c - min_price) * scale
        y_high = offset_y + height - (h - min_price) * scale
        y_low = offset_y + height - (l - min_price) * scale

        pygame.draw.line(screen, color, (x + bar_width / 2, y_high), (x + bar_width / 2, y_low), 1)
        top = min(y_open, y_close)
        body_height = max(abs(y_open - y_close), 1)
        pygame.draw.rect(screen, color, (x, top, bar_width * 0.8, body_height))

    points = []
    for i, price in enumerate(closes):
        x_point = offset_x + i * bar_width
        y_point = offset_y + height - (price - min_price) * scale
        points.append((float(x_point), float(y_point)))

    if len(points) >= 2:
        pygame.draw.lines(screen, (0, 255, 0), False, points, 2)
    # 거래량
    volume_height = 150
    volume_offset_y = offset_y + height + 40
    volumes = volumes_by_ticker.get(current_ticker, [])[:current_index + 1]
    draw_volume_bars(volumes, offset_x, volume_offset_y, width, volume_height)


    draw_text("ESC to exit zoom", offset_x, volume_offset_y + volume_height + 10, (255, 255, 255))
    draw_text("Volume", offset_x, volume_offset_y - 20, (100, 200, 255))

    # 마우스 위치가 거래량 바 위에 있을 경우 거래량 텍스트 출력
    bar_width = width / len(volumes)
    max_volume = max(volumes) if volumes else 1
    if max_volume == 0:
        max_volume = 1  # <- 0으로 나누는 것 방지

    for i, volume in enumerate(volumes):
        x = offset_x + i * bar_width
        bar_height = max(3, (volume / max_volume) * volume_height)
        y = volume_offset_y + volume_height - bar_height
        bar_rect = pygame.Rect(x, y, bar_width * 0.9, bar_height)

        if bar_rect.collidepoint(mouse_x, mouse_y):
            draw_text(f"{volume:,}", x, y - 20, (255, 255, 255))
            break


    # Y축 눈금 추가
    price_range = max_price - min_price
    num_y_ticks = 5
    for i in range(num_y_ticks + 1):
        y = offset_y + i * height / num_y_ticks
        price_val = max_price - i * (price_range / num_y_ticks)
        pygame.draw.line(screen, (60, 60, 60), (offset_x, y), (offset_x + width, y), 1)
        draw_text(f"${price_val:.2f}", offset_x - 60, y - 10, (200, 200, 200))

        num_x_ticks = 6
    for i in range(num_x_ticks):
        x = offset_x + i * width / (num_x_ticks - 1)
        idx = int(i * (len(dates) - 1) / (num_x_ticks - 1))
        if isinstance(dates[idx], datetime.date):
            label = dates[idx].strftime("%y.%m.%d")
        elif isinstance(dates[idx], str):
            label = dates[idx][:10]
        else:
            label = str(dates[idx])
        pygame.draw.line(screen, (60, 60, 60), (x, offset_y), (x, offset_y + height), 1)
        draw_text(label, x - 25, offset_y + height + 5, (200, 200, 200))

        # 🔄 확대 차트 위에 UI 요소도 함께 그리기
    draw_alerts()
    cash()
    draw_total_profit()

    if show_comparison_charts:
        draw_comparison_charts_candlestick()

    # 뒤로가기 버튼도 표시
    pygame.draw.rect(screen, (150, 150, 150), back_to_menu_rect)
    draw_text("← Menu", back_to_menu_rect.x + 10, back_to_menu_rect.y + 5)

    if comparison_mode:
        pygame.draw.rect(screen, (200, 100, 100), mode_button_rect)
        draw_text(" end select mode", mode_button_rect.x + 10, mode_button_rect.y + 5)
    else:
        pygame.draw.rect(screen, (100, 200, 100), mode_button_rect)
        draw_text(" start select mode", mode_button_rect.x + 10, mode_button_rect.y + 5)

    if comparison_mode and not chart_zoom_mode:
        draw_all_companies_grid()


def draw_zoomed_chart(opens, highs, lows, closes, dates):
    screen.fill((0, 0, 0))

    offset_x, offset_y = 80, 80
    width = LAYOUT["screen"]["width"] - 160
    height = 400

    total_len = time_indices[current_ticker] + 1
    view_len = int(total_len * chart_zoom_scale)
    center_index = time_indices[current_ticker]
    start = max(0, center_index - view_len // 2)
    end = min(total_len, start + view_len)

    opens_view = opens[start:end]
    highs_view = highs[start:end]
    lows_view = lows[start:end]
    closes_view = closes[start:end]
    dates_view = dates[start:end]

    if len(closes_view) < 2:
        return

    max_price = max(highs_view)
    min_price = min(lows_view)
    scale = height / (max_price - min_price)
    bar_width = width / len(closes_view)

    # 🔴 캔들 차트
    for i in range(len(closes_view)):
        o, h, l, c = opens_view[i], highs_view[i], lows_view[i], closes_view[i]
        color = (255, 0, 0) if c > o else (0, 128, 255)
        x = offset_x + i * bar_width
        y_open = offset_y + height - (o - min_price) * scale
        y_close = offset_y + height - (c - min_price) * scale
        y_high = offset_y + height - (h - min_price) * scale
        y_low = offset_y + height - (l - min_price) * scale

        pygame.draw.line(screen, color, (x + bar_width / 2, y_high), (x + bar_width / 2, y_low), 1)
        top = min(y_open, y_close)
        body_height = max(abs(y_open - y_close), 1)
        pygame.draw.rect(screen, color, (x, top, bar_width * 0.8, body_height))

    # 🟢 선 그래프
    points = []
    for i, price in enumerate(closes_view):
        x = offset_x + i * bar_width
        y = offset_y + height - (price - min_price) * scale
        points.append((x, y))
    if len(points) >= 2:
        pygame.draw.lines(screen, (0, 255, 0), False, points, 2)

    # 🔵 거래량
    volume_offset_y = offset_y + height + 60
    volume_height = 120
    volumes = volumes_by_ticker.get(current_ticker, [])
    if len(volumes) < end:
        volumes += [0] * (end - len(volumes))
    volumes_view = volumes[start:end]
    draw_volume_bars(volumes_view, offset_x, volume_offset_y, width, volume_height)
    draw_text("Volume", offset_x, volume_offset_y - 20, (100, 200, 255))

    # 🔡 X축
    for i in range(6):
        x_tick = offset_x + i * width / 5
        idx = int(i * (len(dates_view) - 1) / 5)
        label_date = dates_view[idx]
        if isinstance(label_date, str):
            label = label_date[:7]
        else:
            label = label_date.strftime("%y.%m.%d")[:7]
        pygame.draw.line(screen, (60, 60, 60), (x_tick, offset_y), (x_tick, offset_y + height))
        draw_text(label, x_tick - 25, offset_y + height + 5, (200, 200, 200))

    # 🔢 Y축
    for i in range(5):
        y = offset_y + i * height / 4
        val = max_price - i * (max_price - min_price) / 4
        pygame.draw.line(screen, (60, 60, 60), (offset_x, y), (offset_x + width, y))
        draw_text(f"${val:.2f}", offset_x - 60, y - 10, (200, 200, 200))

    draw_text("ESC to exit zoom", offset_x, volume_offset_y + volume_height + 10, (255, 255, 255))


def draw_ui():
    global start_comparison_button_rect  # ✅ 이 줄 추가
    start_comparison_button_rect = None  # 매 프레임마다 초기화

    today = simulation_date_list[current_day_index]
    visible_companies = [
        ticker for ticker in TICKERS
        if ticker in first_available_date and first_available_date[ticker] <= today
    ]

    draw_stock_list(visible_companies)
    cash()
    draw_alerts()
    y_after_profit = draw_portfolio_summary()
    global buy_button_rect, sell_button_rect
    buy_button_rect, sell_button_rect = draw_buttons(y_after_profit)
    draw_text(f"Quantity: {buy_quantity}", buy_button_rect.x, buy_button_rect.y - 25, (255, 255, 0))

    close_key = f"{current_ticker}_Close"
    if close_key in prices_by_ticker:
        current_index = min(time_indices[current_ticker], len(prices_by_ticker[close_key]) - 1)
        prices = prices_by_ticker[close_key][:max(2, current_index + 1)]
        dates = dates_by_ticker[current_ticker][:max(2, current_index + 1)]

        if show_comparison_charts:
            draw_comparison_charts_candlestick()

        draw_chart(prices, dates)

        # 🔧 확대 모드일 때 그리드는 안 보이게
        if not chart_zoom_mode:
            draw_all_companies_grid()


    
        print(f"current_ticker: {current_ticker}, prices 길이: {len(prices)}, dates 길이: {len(dates)}")

    
    # 🟡 뒤로가기 버튼
    pygame.draw.rect(screen, (150, 150, 150), back_to_menu_rect)
    draw_text("← Menu", back_to_menu_rect.x + 10, back_to_menu_rect.y + 5)
    # draw_ui() 함수 내 draw_comparison_charts() 호출 부분을 아래처럼 수정



def draw_comparison_charts():
    offset_x = 80
    offset_y = 80  # 기존 차트 아래 영역
    width = LAYOUT["screen"]["width"] - 160
    height = 250  # 높이 크게

    if len(comparison_tickers) == 0:
        return

    pygame.draw.rect(screen, (20, 20, 20), (offset_x, offset_y, width, height))  # 배경

    # 공통 스케일 구하기
    all_prices = []
    for ticker in comparison_tickers:
        closes = prices_by_ticker.get(f"{ticker}_Close", [])
        index = min(time_indices[ticker], len(closes) - 1)
        all_prices.extend(closes[:index+1])

    if not all_prices:
        return

    max_price = max(all_prices)
    min_price = min(all_prices)
    scale = height / (max_price - min_price + 1)

    for i, ticker in enumerate(comparison_tickers):
        closes = prices_by_ticker[f"{ticker}_Close"]
        index = min(time_indices[ticker], len(closes) - 1)
        prices = closes[:index+1]

        if len(prices) < 2:
            continue

        company_colors = {ticker: COMPANY_COLORS.get(ticker, (255, 255, 255)) for ticker in TICKERS}
        points = []

        for j, p in enumerate(prices):
            x = offset_x + j * (width / len(prices))
            y = offset_y + height - (p - min_price) * scale
            points.append((x, y))

        if len(points) >= 2:
            color = COMPANY_COLORS.get(ticker, (255, 255, 255))
            pygame.draw.lines(screen, color, False, points, 2)
            draw_text(ticker, int(points[-1][0]), int(points[-1][1]) - 15, color)


def draw_main_menu():
    global menu_new_game_rect, menu_continue_rect, menu_clear_cache_rect

    screen.fill((20, 20, 20))  # ✅ 먼저 화면을 지워주고 나머지 요소 그리기 시작ㅍㅍ

    title = font.render(" stock simulator", True, (255, 255, 0))
    screen.blit(title, (LAYOUT["screen"]["width"] // 2 - 100, 100))

    menu_new_game_rect = pygame.Rect(LAYOUT["screen"]["width"] // 2 - 100, 200, 200, 50)
    menu_continue_rect = pygame.Rect(LAYOUT["screen"]["width"] // 2 - 100, 270, 200, 50)
    menu_clear_cache_rect = pygame.Rect(LAYOUT["screen"]["width"] // 2 - 100, 340, 200, 50)

    pygame.draw.rect(screen, (70, 130, 180), menu_new_game_rect)
    pygame.draw.rect(screen, (100, 100, 100), menu_continue_rect)
    pygame.draw.rect(screen, (180, 70, 70), menu_clear_cache_rect)

    screen.blit(font.render("new game start", True, (255, 255, 255)), (menu_new_game_rect.x + 30, menu_new_game_rect.y + 15))
    screen.blit(font.render("load game", True, (255, 255, 255)), (menu_continue_rect.x + 50, menu_continue_rect.y + 15))
    screen.blit(font.render("Clear Cache", True, (255, 255, 255)), (menu_clear_cache_rect.x + 40, menu_clear_cache_rect.y + 15))

    if input_mode == "load":
        draw_load_file_buttons()

def draw_comparison_zoom_screen():
    screen.fill((0, 0, 0))  # 배경 초기화

    count = len(comparison_tickers)
    if count == 0:
        return

    if count == 1:
        rows, cols = 1, 1
        width = LAYOUT["screen"]["width"] - 80
        height = LAYOUT["screen"]["height"] - 150  # 전체 공간 사용
    else:
        if count == 2:
            rows, cols = 2, 1
        else:
            rows, cols = 2, 2

        width = LAYOUT["screen"]["width"] // cols
        height = (LAYOUT["screen"]["height"] - 150) // rows


    for i, ticker in enumerate(comparison_tickers):
        row = i // cols
        col = i % cols
        offset_x = col * width + 20
        offset_y = row * height + 80

        # 보여줄 데이터 범위 설정
        view_len = 100
        start = comparison_scroll_offset_index

        # ✅ 진행된 날짜까지만 보여주도록 인덱스 제한
        time_index = time_indices.get(ticker, 0)
        end = min(start + view_len, time_index + 1)


        # 데이터 추출
        opens = prices_by_ticker.get(f"{ticker}_Open", [])[start:end]
        highs = prices_by_ticker.get(f"{ticker}_High", [])[start:end]
        lows = prices_by_ticker.get(f"{ticker}_Low", [])[start:end]
        closes = prices_by_ticker.get(f"{ticker}_Close", [])[start:end]
        volumes = volumes_by_ticker.get(ticker, [])[start:end]
        dates = dates_by_ticker.get(ticker, [])[start:end]


        if not closes or not highs or not lows:
            continue

        # 가격 스케일링
        max_price = max(highs)
        min_price = min(lows)
        price_scale = height / (max_price - min_price + 1)
        bar_width = width / max(1, len(closes))

        # 🔵 거래량
        volume_height = 50
        volume_offset_y = offset_y + height + 10
        max_volume = max(volumes) if volumes else 1
        # 🔵 거래량
        for j, v in enumerate(volumes):
            vol_height = (v / max_volume) * volume_height
            x = offset_x + j * bar_width
            y = volume_offset_y + volume_height - vol_height
            volume_rect = pygame.Rect(x, y, bar_width * 0.8, vol_height)
            pygame.draw.rect(screen, (100, 200, 255), volume_rect)

            # 🔍 마우스 올렸을 때 거래량 텍스트 표시
            if volume_rect.collidepoint(mouse_x, mouse_y):
                draw_text(f"{v:,}", int(x), int(y) - 20, (255, 255, 255))


        # 📈 캔들 차트
        for j in range(len(closes)):
            o = opens[j]
            h = highs[j]
            l = lows[j]
            c = closes[j]
            color = (255, 0, 0) if c >= o else (0, 128, 255)

            x = offset_x + j * bar_width
            y_open = offset_y + height - (o - min_price) * price_scale
            y_close = offset_y + height - (c - min_price) * price_scale
            y_high = offset_y + height - (h - min_price) * price_scale
            y_low = offset_y + height - (l - min_price) * price_scale

            pygame.draw.line(screen, color, (x + bar_width / 2, y_high), (x + bar_width / 2, y_low), 1)
            top = min(y_open, y_close)
            body_height = max(abs(y_open - y_close), 1)
            pygame.draw.rect(screen, color, (x, top, bar_width * 0.8, body_height))

        # 🔢 Y축 눈금
        for k in range(4):
            y = offset_y + k * height / 3
            val = max_price - k * (max_price - min_price) / 3
            pygame.draw.line(screen, (60, 60, 60), (offset_x, y), (offset_x + width, y))
            draw_text(f"${val:.2f}", offset_x - 60, y - 10, (200, 200, 200))

        # 📅 X축 날짜
        for k in range(4):
            x_tick = offset_x + k * width / 3
            if len(dates) > 0:
                idx = int(k * (len(dates) - 1) / 3)
                d = dates[idx]
                if isinstance(d, datetime.date):
                    label = d.strftime("%y.%m.%d")
                else:
                    label = str(d)
                pygame.draw.line(screen, (60, 60, 60), (x_tick, offset_y), (x_tick, offset_y + height))
                draw_text(label, x_tick - 25, offset_y + height + 5, (200, 200, 200))

        draw_text(f"{TICKERS[ticker]} ({ticker})", offset_x, offset_y - 25, (255, 255, 0))

    # 🔙 ESC 안내
    draw_text("ESC to exit comparison mode", 80, 20, (255, 255, 255))

def draw_quantity_input_box():
    global quantity_input_text
    box_rect = pygame.Rect(LAYOUT["screen"]["width"] // 2 - 150, 100, 300, 40)
    pygame.draw.rect(screen, (255, 255, 255), box_rect)
    pygame.draw.rect(screen, (0, 0, 0), box_rect, 2)
    draw_text("Enter quantity:", box_rect.x + 10, box_rect.y - 30, (255, 255, 0))
    draw_text(quantity_input_text, box_rect.x + 10, box_rect.y + 10, (0, 0, 0))

    # 🔙 뒤로가기 버튼
    pygame.draw.rect(screen, (150, 150, 150), back_to_menu_rect)
    draw_text("Menu", back_to_menu_rect.x + 10, back_to_menu_rect.y + 5)



def main_loop():
    if not simulation_date_list:
        print("❌ simulation_date_list가 비어있습니다. 게임을 시작할 수 없습니다.")
        return

    global comparison_scroll_offset_index
    global chart_scroll_offset_index
    global comparison_mode, show_comparison_charts
    global quantity_input_mode, quantity_input_text, buy_quantity

    global current_day_index, current_ticker
    global chart_zoom_mode, chart_zoom_scale, chart_zoom_center_ratio
    global input_mode, input_text, load_file_buttons
    global game_state
    global comparison_zoom_mode
    last_day_update_time = time.time()

    running = True
    while running:
        screen.fill((30, 30, 30))

        global mouse_x, mouse_y
        mouse_x, mouse_y = pygame.mouse.get_pos()

        today = simulation_date_list[current_day_index]
        if isinstance(today, str):
            today = datetime.datetime.strptime(today, "%y.%m.%d").date()

        visible_companies = [
            ticker for ticker in TICKERS
            if ticker in first_available_date and first_available_date[ticker] <= today
        ]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
                        # 🔽🔽🔽 여기에 추가하면 됨! 🔽🔽🔽
            if quantity_input_mode:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        try:
                            buy_quantity = max(1, int(quantity_input_text))
                            alerts.append((f"수량 설정됨: {buy_quantity}", time.time()))
                        except:
                            alerts.append(("⚠ 숫자만 입력해주세요.", time.time()))
                        quantity_input_mode = False
                        quantity_input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        quantity_input_text = quantity_input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        quantity_input_mode = False
                        quantity_input_text = ""
                    elif event.unicode.isdigit():
                        quantity_input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if back_to_menu_rect.collidepoint(event.pos):
                        quantity_input_mode = False
                        quantity_input_text = ""
                continue  # 수량 입력 모드일 때는 다른 이벤트 무시

            # 확대 차트 모드
            if chart_zoom_mode:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("🔙 ESC 입력 → chart_zoom_mode 종료")
                        chart_zoom_mode = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        chart_scroll_offset_index = max(0, chart_scroll_offset_index - 10)
                    elif event.button == 5:
                        chart_scroll_offset_index += 10
                continue

            # 비교 차트 줌 모드
            if comparison_zoom_mode:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        comparison_scroll_offset_index = max(0, comparison_scroll_offset_index - 10)
                    elif event.key == pygame.K_RIGHT:
                        comparison_scroll_offset_index += 10
                    elif event.key == pygame.K_ESCAPE:
                        print("🔙 ESC 입력 → comparison_zoom_mode 종료")
                        comparison_zoom_mode = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        comparison_scroll_offset_index = max(0, comparison_scroll_offset_index - 10)
                    elif event.button == 5:
                        comparison_scroll_offset_index += 10
                continue

            # 저장 입력 모드
            if input_mode == "save":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        save_game(input_text.strip() + ".json")
                        input_mode = None
                        input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if load_back_button_rect.collidepoint(event.pos):
                        input_mode = None
                        input_text = ""
                continue

            # 불러오기 모드
            if input_mode == "load":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if load_back_button_rect.collidepoint(event.pos):
                        input_mode = None
                        continue
                    for fname, load_rect, del_rect in load_file_buttons:
                        if load_rect.collidepoint(event.pos):
                            load_game(fname)
                            input_mode = None
                            break
                        elif del_rect.collidepoint(event.pos):
                            os.remove(os.path.join(SAVE_DIR, fname))
                            draw_load_file_buttons()
                            alerts.append((f"{fname} 삭제됨", time.time()))
                            break
                continue

            # 메뉴 화면
            if game_state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_new_game_rect and menu_new_game_rect.collidepoint(event.pos):
                        global portfolio
                        game_state = "playing"
                        current_day_index = 0
                        portfolio = {
                            'cash': 100000,
                            'stocks': {ticker: {'quantity': 0, 'buy_price': 0} for ticker in TICKERS}
                        }
                    elif menu_continue_rect and menu_continue_rect.collidepoint(event.pos):
                        input_mode = "load"
                    elif menu_clear_cache_rect and menu_clear_cache_rect.collidepoint(event.pos):
                        clear_cache()
                continue

            # 게임 플레이 화면
            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q and (event.mod & pygame.KMOD_SHIFT):
                        quantity_input_mode = True
                        quantity_input_text = ""
                        continue

                    if event.key == pygame.K_s and (event.mod & pygame.KMOD_SHIFT):
                        input_mode = "save"
                        input_text = ""
                        continue
                    elif event.key == pygame.K_s:
                        save_game()
                        continue
                    elif event.key == pygame.K_l:
                        input_mode = "load"
                        continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # 휠 업                        
                        buy_quantity += 1
                    elif event.button == 5:  # 휠 다운
                        buy_quantity = max(1, buy_quantity - 1)    
                    
                    if 'mode_button_rect' in globals() and mode_button_rect.collidepoint(event.pos):
                        comparison_mode = not comparison_mode
                        if not comparison_mode:
                            comparison_tickers.clear()
                            show_comparison_charts = False
                        continue

                    if start_comparison_button_rect and start_comparison_button_rect.collidepoint(event.pos):
                        print("🖱️ 실행 버튼 클릭됨")  # ✅ 디버깅 출력
                        print("📊 선택된 종목:", comparison_tickers)
                        if comparison_mode:
                            if len(comparison_tickers) == 1:
                                current_ticker = comparison_tickers[0]
                                chart_zoom_mode = True
                                chart_scroll_offset_index = 0
                                print(f"✅ 단독 차트 확대 모드 진입: {current_ticker}")
                            elif len(comparison_tickers) >= 2:
                                comparison_zoom_mode = True
                                print("✅ 비교 차트 줌 모드 진입!")
                            else:
                                alerts.append(("⚠ 최소 1개 이상 선택해야 합니다.", time.time()))
                        continue

                    if comparison_tickers:
                        exit_rect = pygame.Rect(LAYOUT["screen"]["width"] - 150, 20, 120, 30)
                        if exit_rect.collidepoint(event.pos):
                            comparison_tickers.clear()
                            continue

                    if back_to_menu_rect.collidepoint(event.pos):
                        game_state = "menu"
                        continue

                    if buy_button_rect.collidepoint(event.pos):
                        buy_stock(current_ticker)
                        continue

                    if sell_button_rect.collidepoint(event.pos):
                        sell_stock(current_ticker)
                        continue

                    chart_rect = pygame.Rect(LAYOUT["chart"]["x"], LAYOUT["chart"]["y"], LAYOUT["chart"]["width"], LAYOUT["chart"]["height"])
                    if chart_rect.collidepoint(event.pos):
                        chart_zoom_mode = True
                        chart_zoom_center_ratio = (event.pos[0] - chart_rect.x) / chart_rect.width
                        continue

                    for ticker, main_rect, select_rect in all_company_buttons:
                        if comparison_mode:
                            if select_rect and select_rect.collidepoint(event.pos):
                                if ticker in comparison_tickers:
                                    comparison_tickers.remove(ticker)
                                elif len(comparison_tickers) < 4:
                                    comparison_tickers.append(ticker)
                                print(f"✅ 선택 상태 변경됨: {ticker}, 현재 비교 리스트: {comparison_tickers}")
                                break
                        if main_rect.collidepoint(event.pos):
                            current_ticker = ticker
                            print(f"📈 현재 종목 변경됨: {ticker}")
                            break

        # 날짜 및 데이터 업데이트
        if time.time() - last_day_update_time > 2:
            if current_day_index + 1 < len(simulation_date_list):
                current_day_index += 1
                last_day_update_time = time.time()
                today = simulation_date_list[current_day_index]

                # 모든 티커에 대해 유효한 인덱스를 갱신
                for ticker in TICKERS:
                    dates = dates_by_ticker.get(ticker, [])
                    for i, d in enumerate(dates):
                        if isinstance(d, str):
                            d = datetime.datetime.strptime(d, "%Y-%m-%d").date()
                        if d > today:
                            break
                        time_indices[ticker] = i


        if chart_zoom_mode:
            draw_zoomed_chart_like_chart()
        elif comparison_zoom_mode:
            draw_comparison_zoom_screen()
        elif input_mode == "save":
            draw_input_box()
        elif input_mode == "load":
            draw_load_file_buttons()
        elif game_state == "menu":
            draw_main_menu()
        elif quantity_input_mode:
            draw_quantity_input_box()
        else:
            draw_ui()

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    init_game()

    print(f"🎯 최종 날짜 리스트 길이 확인: {len(simulation_date_list)}")  # <-- 디버깅용

    if not simulation_date_list:
        print("❌ 날짜 리스트 없음 → 게임 시작 불가. 캐시를 삭제하거나 인터넷 연결을 확인하세요.")
        sys.exit()

    print("🟢 main_loop 시작")  # <- 여기도 디버깅 추가
    main_loop()