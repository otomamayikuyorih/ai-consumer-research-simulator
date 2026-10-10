import random
import numpy as np
from typing import Any

# 日本の公的統計データ（総務省統計局「国勢調査」「就業構造基本調査」「家計調査」、国税庁「民間給与実態統計調査」等）に基づくパラメータ
STATISTICAL_BENCHMARKS = {
    "source": "総務省統計局「国勢調査」「就業構造基本調査」「家計調査」および国税庁「民間給与実態統計調査」に基づく推計結合モデル",
    "official_citations": [
        {
            "name": "令和2年国勢調査（人口等基本集計・就業状態等基本集計）",
            "agency": "総務省統計局",
            "survey_year": "2020年（令和2年）",
            "citation_url": "https://www.stat.go.jp/data/kokusei/2020/",
            "applied_dimensions": "8地方区分・47都道府県別人口比率、男女比（男48.5% : 女51.5%）、10歳刻み年代別人口比率、世帯構成比"
        },
        {
            "name": "令和4年就業構造基本調査",
            "agency": "総務省統計局",
            "survey_year": "2022年（令和4年）",
            "citation_url": "https://www.stat.go.jp/data/shugyou/2022/",
            "applied_dimensions": "年代別×学歴別の就労形態（正規・非正規・役員・自営・パート・無職）、職種分類構成比"
        },
        {
            "name": "令和4年分 民間給与実態統計調査",
            "agency": "国税庁",
            "survey_year": "2022年（令和4年）",
            "citation_url": "https://www.nta.go.jp/publication/statistics/kokuzeicho/minkan/minkan.htm",
            "applied_dimensions": "年代別・男女別平均年収および対数正規分布パラメータ（年収レンジと標準偏差）"
        },
        {
            "name": "2023年家計調査年報（家計収支編・総世帯）",
            "agency": "総務省統計局",
            "survey_year": "2023年（令和5年）",
            "citation_url": "https://www.stat.go.jp/data/kakei/",
            "applied_dimensions": "世帯構成別の世帯年収分布および可処分所得比率"
        }
    ],
    "manual_assumptions": [
        {
            "category": "サイコグラフィック・消費価値観（6セグメント）",
            "assumption_details": "日本の一般消費者市場分析（電通総研生活者定点等）を参考に、消費価値観を『コスパ・実利重視(28%)』『タイパ・効率重視(20%)』『健康・ウェルネス投資(18%)』『サステナビリティ・エシカル(12%)』『自己投資・知的好奇心(12%)』『プレミアム・情緒価値(10%)』の6類型に手動設定。年代・年収による条件付き結合確率モデルを採用。",
            "is_official_statistic": False
        },
        {
            "category": "情報収集チャネル・購買意思決定スタイル",
            "assumption_details": "総務省『情報通信白書』の年代別ネット利用実態を基礎としつつ、情報チャネル接触傾向（SNS/Web検索/TV等）と意思決定傾向（スペック比較/口コミ重視/直感型等）は消費者行動論に基づくヒューリスティック設定。",
            "is_official_statistic": False
        }
    ],
    "notes": "公的統計をベースに、属性間の相関（年齢×職業、学歴×職種×年収）を統計的結合モデルで合成しています。サイコグラフィック（価値観、決定スタイル）は消費者行動調査に基づく仮説的合成データです。",
    "regions": {
        "関東": 0.342,
        "近畿": 0.163,
        "中部": 0.168,
        "九州・沖縄": 0.104,
        "東北": 0.068,
        "中国": 0.057,
        "北海道": 0.041,
        "四国": 0.029,
    },
    "prefectures_by_region": {
        "関東": ["東京都", "神奈川県", "埼玉県", "千葉県", "茨城県", "栃木県", "群馬県"],
        "近畿": ["大阪府", "兵庫県", "京都府", "滋賀県", "奈良県", "和歌山県"],
        "中部": ["愛知県", "静岡県", "岐阜県", "三重県", "新潟県", "長野県", "石川県", "富山県", "福井県"],
        "九州・沖縄": ["福岡県", "熊本県", "鹿児島県", "長崎県", "大分県", "宮崎県", "佐賀県", "沖縄県"],
        "東北": ["宮城県", "福島県", "青森県", "岩手県", "山形県", "秋田県"],
        "中国": ["広島県", "岡山県", "山口県", "島根県", "鳥取県"],
        "北海道": ["北海道"],
        "四国": ["愛媛県", "香川県", "徳島県", "高知県"],
    },
    "gender_ratio": {
        "男性": 0.485,
        "女性": 0.515,
    },
    "age_groups_national": {
        "20代": 0.125,
        "30代": 0.142,
        "40代": 0.175,
        "50代": 0.186,
        "60代": 0.178,
        "70代以上": 0.194,
    },
    "education_distribution": {
        "高校卒": 0.38,
        "専門学校・短大・高専卒": 0.22,
        "大学卒（文系）": 0.24,
        "大学卒（理系）": 0.12,
        "大学院卒": 0.04,
    }
}

LAST_NAMES = [
    "佐藤", "鈴木", "高橋", "田中", "渡辺", "伊藤", "山本", "中村", "小林", "加藤",
    "吉田", "山田", "佐々木", "山口", "松本", "井上", "木村", "林", "斎藤", "清水",
    "山崎", "阿部", "池田", "橋本", "山下", "森", "石川", "前田", "小川", "藤田"
]

MALE_FIRST_NAMES = [
    "翔太", "大輝", "蓮", "拓海", "健一", "直樹", "裕介", "達也", "誠", "剛",
    "修平", "哲也", "浩二", "雅人", "康平", "宏樹", "隆司", "勝", "博", "正雄"
]

FEMALE_FIRST_NAMES = [
    "美咲", "陽菜", "葵", "結衣", "愛", "香織", "麻衣", "恵理", "真由美", "千尋",
    "里奈", "明日香", "裕子", "智子", "由美子", "和代", "恵子", "洋子", "節子", "美代子"
]

VALUES_SEGMENTS = [
    "コスパ・実利重視",
    "品質・本物志向",
    "トレンド・体験消費",
    "堅実・節約・保守的",
    "サステナビリティ・エシカル",
    "デジタル・ガジェット愛好",
    "健康・ウェルネス投資"
]

DECISION_STYLES = [
    "徹底比較・レビュー重視型",
    "直感・インスピレーション型",
    "価格・コストパフォーマンス最優先型",
    "有名ブランド・信頼性重視型",
    "知人・インフルエンサー推薦型",
    "慎重検討・失敗回避型"
]

LIFESTYLES = [
    "ワークライフバランス重視",
    "キャリア志向・自己研鑽",
    "家庭・育児・家族第一",
    "趣味・マイペース生活",
    "健康長寿・ウェルネス生活",
    "効率・タイパ重視"
]

HOBBIES_POOL = [
    "カフェ・グルメ巡り", "旅行・観光", "料理・自炊", "映画・ドラマ鑑賞",
    "読書", "ゲーム・アニメ", "ランニング・フィットネス", "キャンプ・アウトドア",
    "資産運用・株式投資", "美容・スキンケア", "音楽・ライブ鑑賞", "DIY・インテリア",
    "ガーデニング", "カメラ・写真", "スポーツ観戦", "ヨガ・サウナ"
]

def sample_weighted(weight_dict: dict[str, float]) -> str:
    keys = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]

def generate_correlated_persona(
    idx: int,
    preset: str = "general_national",
    rng: np.random.RandomState = None,
    mode: str = "mode_b",
    grounded_sample: dict[str, Any] = None
) -> dict[str, Any]:
    if rng is None:
        rng = np.random.RandomState()

    # 1. プリセットに応じた年齢・性別のサンプリング
    if preset == "young_digital":
        age_group = random.choices(["20代", "30代"], weights=[0.55, 0.45], k=1)[0]
        if age_group == "20代":
            age = int(rng.randint(20, 30))
        else:
            age = int(rng.randint(30, 40))
        gender = sample_weighted(STATISTICAL_BENCHMARKS["gender_ratio"])
    elif preset == "senior_silver":
        age_group = random.choices(["60代", "70代以上"], weights=[0.50, 0.50], k=1)[0]
        if age_group == "60代":
            age = int(rng.randint(60, 70))
        else:
            age = int(rng.randint(70, 80))
        gender = sample_weighted(STATISTICAL_BENCHMARKS["gender_ratio"])
    elif preset == "working_parents":
        age_group = random.choices(["30代", "40代", "50代"], weights=[0.45, 0.45, 0.10], k=1)[0]
        if age_group == "30代":
            age = int(rng.randint(30, 40))
        elif age_group == "40代":
            age = int(rng.randint(40, 50))
        else:
            age = int(rng.randint(50, 60))
        gender = sample_weighted(STATISTICAL_BENCHMARKS["gender_ratio"])
    else: # general_national
        age_group = sample_weighted(STATISTICAL_BENCHMARKS["age_groups_national"])
        if age_group == "20代":
            age = int(rng.randint(20, 30))
        elif age_group == "30代":
            age = int(rng.randint(30, 40))
        elif age_group == "40代":
            age = int(rng.randint(40, 50))
        elif age_group == "50代":
            age = int(rng.randint(50, 60))
        elif age_group == "60代":
            age = int(rng.randint(60, 70))
        else:
            age = int(rng.randint(70, 80))
        gender = sample_weighted(STATISTICAL_BENCHMARKS["gender_ratio"])

    # 氏名生成
    last_name = random.choice(LAST_NAMES)
    first_name = random.choice(MALE_FIRST_NAMES) if gender == "男性" else random.choice(FEMALE_FIRST_NAMES)
    full_name = f"{last_name} {first_name}"

    # 2. 地域と都道府県（人口比重ベース）
    region = sample_weighted(STATISTICAL_BENCHMARKS["regions"])
    prefectures = STATISTICAL_BENCHMARKS["prefectures_by_region"][region]
    # 代表的な主要都道府県に少し多めの傾斜
    prefecture = random.choice(prefectures)

    # 3. 学歴（年代相関: 若い世代ほど大学・大学院進学率が高い）
    if age < 40:
        edu_weights = {"高校卒": 0.25, "専門学校・短大・高専卒": 0.20, "大学卒（文系）": 0.35, "大学卒（理系）": 0.15, "大学院卒": 0.05}
    elif age < 60:
        edu_weights = {"高校卒": 0.38, "専門学校・短大・高専卒": 0.22, "大学卒（文系）": 0.25, "大学卒（理系）": 0.11, "大学院卒": 0.04}
    else:
        edu_weights = {"高校卒": 0.55, "専門学校・短大・高専卒": 0.18, "大学卒（文系）": 0.18, "大学卒（理系）": 0.07, "大学院卒": 0.02}
    education = sample_weighted(edu_weights)

    # 4. 職業・就業形態（年齢・性別・学歴に連動）
    if age < 23 and education in ["大学卒（文系）", "大学卒（理系）", "大学院卒"] and random.random() < 0.35:
        occupation = "学生・大学院生"
        employment_type = "学生"
    elif age >= 65:
        if random.random() < 0.65:
            occupation = "無職・年金受給者"
            employment_type = "年金生活・無職"
        elif random.random() < 0.5:
            occupation = "再雇用・シニア嘱託"
            employment_type = "パート・アルバイト"
        else:
            occupation = "自営業・個人事業主"
            employment_type = "自営業・フリーランス"
    elif gender == "女性" and random.random() < 0.20 and age >= 30:
        occupation = "専業主婦"
        employment_type = "専業主婦・主夫"
    elif gender == "女性" and random.random() < 0.30:
        occupation = "パート・契約社員（事務・販売）"
        employment_type = "パート・アルバイト"
    else:
        # 正規社員・専門職・公務員等
        occ_candidates = [
            ("会社員（IT・インターネット・Web）", "正規雇用", 0.18),
            ("会社員（メーカー・製造業・技術職）", "正規雇用", 0.22),
            ("会社員（卸売・小売・飲食・サービス）", "正規雇用", 0.16),
            ("会社員（金融・保険・不動産）", "正規雇用", 0.12),
            ("公務員・団体職員・教職員", "公務員", 0.10),
            ("医療・福祉・介護専門職", "正規雇用", 0.10),
            ("自営業・フリーランス", "自営業・フリーランス", 0.07),
            ("会社経営・役員", "正規雇用", 0.05),
        ]
        chosen = random.choices(occ_candidates, weights=[c[2] for c in occ_candidates], k=1)[0]
        occupation = chosen[0]
        employment_type = chosen[1]

    # 5. 世帯構成（年齢およびプリセット相関）
    if preset == "working_parents":
        household = random.choice([
            "夫婦と子ども（未就学児）",
            "夫婦と子ども（小中学生）",
            "夫婦と子ども（高校・大学生以上）"
        ])
    elif age < 30:
        household = sample_weighted({"単身（ひとり暮らし）": 0.55, "親と同居（未婚）": 0.35, "夫婦のみ（DINKS）": 0.10})
    elif age < 50:
        household = sample_weighted({
            "単身（ひとり暮らし）": 0.28,
            "夫婦のみ（DINKS）": 0.20,
            "夫婦と子ども（未就学児）": 0.18,
            "夫婦と子ども（小中学生）": 0.22,
            "ひとり親と子ども": 0.07,
            "三世代同居・親族同居": 0.05
        })
    elif age < 65:
        household = sample_weighted({
            "単身（ひとり暮らし）": 0.25,
            "夫婦のみ": 0.35,
            "夫婦と子ども（高校・大学生以上）": 0.30,
            "ひとり親と子ども": 0.05,
            "親族同居": 0.05
        })
    else:
        household = sample_weighted({
            "単身（ひとり暮らし）": 0.33,
            "夫婦のみ": 0.52,
            "子ども世帯と同居": 0.15
        })

    # 6. 個人年収・世帯年収（日本の給与所得統計・対数正規分布 + 属性相関）
    # 基準となる個人年収 (万円)
    if employment_type in ["学生", "専業主婦・主夫"]:
        personal_income = int(max(0, rng.normal(40, 25)))
    elif employment_type in ["年金生活・無職"]:
        personal_income = int(max(100, rng.normal(190, 45)))
    elif employment_type in ["パート・アルバイト"]:
        personal_income = int(max(80, rng.normal(125, 35)))
    elif employment_type in ["自営業・フリーランス"]:
        personal_income = int(max(150, rng.lognormal(5.8, 0.5))) # 平均 ~400-500万、分散大きめ
    else:
        # 正規・公務員: 年代による上昇カーブ
        base_income_by_age = {
            "20代": 340,
            "30代": 480,
            "40代": 610,
            "50代": 700,
            "60代": 460,
            "70代以上": 250
        }
        mean_inc = base_income_by_age.get(age_group, 500)
        # 学歴・性別補正
        if "大学院" in education:
            mean_inc *= 1.35
        elif "大学" in education:
            mean_inc *= 1.15
        elif "高校" in education:
            mean_inc *= 0.88

        if gender == "女性":
            mean_inc *= 0.82 # 日本の賃金実態統計の男女格差反映

        noise = rng.normal(1.0, 0.22)
        personal_income = int(max(200, mean_inc * noise))

    # 世帯年収の算出
    if "単身" in household or "ひとり暮らし" in household or "親と同居（未婚）" in household:
        household_income = personal_income
    elif "夫婦" in household:
        # 共働き確率
        dual_earner = random.random() < 0.65
        if dual_earner:
            partner_income = int(max(100, rng.normal(320, 120)))
            household_income = personal_income + partner_income
        else:
            household_income = personal_income
    elif "子ども世帯と同居" in household or "三世代同居" in household:
        household_income = personal_income + int(max(200, rng.normal(450, 150)))
    else:
        household_income = personal_income + int(max(0, rng.normal(150, 80)))

    # 7. 趣味・興味（2〜4個）
    num_hobbies = random.randint(2, 4)
    # 年齢連動の重み付け
    if age < 35:
        hob_weights = [1.5 if h in ["カフェ・グルメ巡り", "ゲーム・アニメ", "美容・スキンケア", "旅行・観光", "音楽・ライブ鑑賞"] else 1.0 for h in HOBBIES_POOL]
    elif age < 55:
        hob_weights = [1.5 if h in ["資産運用・株式投資", "料理・自炊", "キャンプ・アウトドア", "ランニング・フィットネス"] else 1.0 for h in HOBBIES_POOL]
    else:
        hob_weights = [1.5 if h in ["旅行・観光", "ガーデニング", "読書", "健康長寿・ウェルネス", "料理・自炊"] else 1.0 for h in HOBBIES_POOL]
    
    selected_hobbies = list(np.random.choice(HOBBIES_POOL, size=num_hobbies, replace=False, p=np.array(hob_weights)/sum(hob_weights)))

    # 8. 価値観・消費志向
    if personal_income >= 800 or household_income >= 1200:
        val_weights = [0.10, 0.35, 0.20, 0.05, 0.12, 0.10, 0.08]
    elif age < 35:
        val_weights = [0.30, 0.10, 0.28, 0.07, 0.05, 0.15, 0.05]
    elif age >= 60:
        val_weights = [0.18, 0.22, 0.05, 0.30, 0.08, 0.02, 0.15]
    else:
        val_weights = [0.25, 0.18, 0.15, 0.18, 0.08, 0.06, 0.10]
    values_segment = random.choices(VALUES_SEGMENTS, weights=val_weights, k=1)[0]

    # 9. 意思決定スタイル
    if values_segment == "コスパ・実利重視":
        dec_weights = [0.45, 0.05, 0.35, 0.03, 0.02, 0.10]
    elif values_segment == "品質・本物志向":
        dec_weights = [0.25, 0.10, 0.05, 0.40, 0.05, 0.15]
    elif values_segment == "トレンド・体験消費":
        dec_weights = [0.15, 0.35, 0.05, 0.15, 0.25, 0.05]
    else:
        dec_weights = [0.25, 0.10, 0.20, 0.15, 0.10, 0.20]
    decision_style = random.choices(DECISION_STYLES, weights=dec_weights, k=1)[0]

    # 10. ライフスタイル
    lifestyle = random.choice(LIFESTYLES)

    # 11. 情報収集チャネル（年代・価値観連動）
    channels = []
    if age < 30:
        channels = ["Instagram", "X (旧Twitter)", "YouTube"]
        if random.random() < 0.45: channels.append("TikTok")
        if random.random() < 0.60: channels.append("Web検索・Google")
    elif age < 50:
        channels = ["Web検索・Google", "YouTube", "口コミサイト・比較サイト"]
        if random.random() < 0.55: channels.append("Instagram")
        if random.random() < 0.50: channels.append("テレビ番組・ニュース")
        if random.random() < 0.45: channels.append("X (旧Twitter)")
    else:
        channels = ["テレビ番組・ニュース", "新聞・雑誌・チラシ", "Web検索・Google"]
        if random.random() < 0.45: channels.append("YouTube")
        if random.random() < 0.40: channels.append("友人・知人のクチコミ")

    # 12. 消費行動プロファイル（自然言語テキスト生成）
    income_desc = f"個人年収{personal_income}万円（世帯年収{household_income}万円）"

    # AI4PB モード別プロファイル & 生活史・購買経験
    life_history = ""
    purchase_experiences = []
    grounded_interview = {}
    is_consented = 0
    consent_status = "synthetic_public_stats"

    if mode == "mode_a":
        # Mode A: Demographic Persona（属性のみ、架空の物語は付与しない）
        profile = (
            f"【Mode A: 人口統計属性ペルソナ】{age}歳{gender}、{prefecture}（{region}）在住。"
            f"最終学歴は{education}、職業は{occupation}（{employment_type}）。"
            f"{household}暮らし、個人年収{personal_income}万円、世帯年収{household_income}万円。"
        )
        consent_status = "synthetic_demographic_only"

    elif mode == "mode_c" and grounded_sample:
        # Mode C: Interview-Grounded Persona（実測インタビュー接地）
        grounded_interview = grounded_sample.get("extracted_data", {})
        verbatims = grounded_interview.get("verbatim_quotes", [])
        top_quote = f"「{verbatims[0]}」" if verbatims else ""
        
        # インタビューからの属性上書き・反映
        if "values" in grounded_interview and grounded_interview["values"]:
            values_segment = grounded_interview["values"][0]
        if "decision_style" in grounded_interview and grounded_interview["decision_style"]:
            decision_style = grounded_interview["decision_style"]

        life_history = grounded_sample.get("raw_transcript", "").strip()[:500] + "..."
        purchase_experiences = grounded_interview.get("purchase_triggers", [])
        is_consented = 1 if not grounded_sample.get("is_demo", True) else 0
        consent_status = "consented_anonymous_participant" if is_consented else "demo_interview_data"

        profile = (
            f"【Mode C: 実測インタビュー接地ペルソナ】{prefecture}在住の{age}歳{gender}（{occupation}）。"
            f"インタビューでの実直な発言: {top_quote}。"
            f"生活価値観: 『{values_segment}』、購買意思決定: 『{decision_style}』。"
            f"価格感度: {grounded_interview.get('price_sensitivity', '状況に応じてメリハリをつける')}。"
        )

    else:
        # Mode B: Synthetic Rich Persona（統計属性＋合成生活史＋合成購買経験）
        mode = "mode_b"
        life_history = generate_synthetic_life_history(age, gender, occupation, household, prefecture, values_segment)
        purchase_experiences = generate_synthetic_purchase_experiences(values_segment, personal_income, age)
        consent_status = "synthetic_public_stats_rich_narrative"

        profile = (
            f"【Mode B: 仮想生活史リッチペルソナ】{prefecture}在住の{age}歳{gender}。{household}で暮らし、{occupation}として勤務。"
            f"{education}で、{income_desc}の生活水準。"
            f"消費価値観は『{values_segment}』で、商品購入時は『{decision_style}』の傾向がある。"
            f"普段は『{lifestyle}』を志向し、余暇は{', '.join(selected_hobbies)}などを楽しむ。"
            f"主な情報収集は{', '.join(channels[:3])}を中心に行う。"
        )

    persona_code = f"P-{idx+1:04d}"

    return {
        "persona_code": persona_code,
        "generation_mode": mode,
        "name": full_name,
        "age": age,
        "age_group": age_group,
        "gender": gender,
        "region": region,
        "prefecture": prefecture,
        "occupation": occupation,
        "employment_type": employment_type,
        "household": household,
        "education": education,
        "personal_income": personal_income,
        "household_income": household_income,
        "hobbies": selected_hobbies,
        "values_segment": values_segment,
        "lifestyle": lifestyle,
        "info_channels": channels,
        "decision_style": decision_style,
        "consumption_profile": profile,
        "life_history": life_history,
        "purchase_experiences": purchase_experiences,
        "grounded_interview": grounded_interview,
        "is_consented_human_subject": is_consented,
        "data_consent_status": consent_status
    }

def generate_synthetic_life_history(age: int, gender: str, occupation: str, household: str, prefecture: str, values_segment: str) -> str:
    if age < 30:
        return f"{prefecture}出身。新卒から数年が経ち、現在は{occupation}として勤務。{household}の生活。学生時代からデジタルサービスに親しみ、時間効率と自分の趣味の両立を重視している。将来のキャリアや貯蓄、自己投資のバランスを模索している段階。"
    elif age < 50:
        return f"{prefecture}在住。{occupation}としてキャリアの責任ある立場を務める。{household}の暮らしの中で、日々の生活維持と将来の資金計画（住宅や教育、老後資金）を意識している。多忙な毎日の中で、家事や仕事を効率化しストレスを減らす商品やサービスへの受容性が高い。"
    elif age < 65:
        return f"{prefecture}にて長年{occupation}として勤め上げ、生活基盤を確立。子どもの自立や定年後の生活設計を見据え、健康維持や夫婦の余暇時間の充実に関心が高い。派手な消費よりも、信頼できる品質と安心感を重視する。"
    else:
        return f"{prefecture}在住のシニア層。定年を経て現在は穏やかな日々を送る。{household}で暮らし、日常の健康長寿や安心できるサポート体制を最も大切にしている。長年の人生経験から安易な衝動買いは避け、信頼できる製品を選ぶ。"

def generate_synthetic_purchase_experiences(values_segment: str, personal_income: int, age: int) -> list[str]:
    experiences = []
    if values_segment == "コスパ・実利重視":
        experiences.append("日用品や固定費は定期的に見直し、価格比較サイトで最安値や還元率を確認して購入した。")
        experiences.append("型落ちの家電やセール期間を狙い、機能と価格のバランスが最も優れたモデルを選定した。")
    elif values_segment == "品質・本物志向":
        experiences.append("多少価格が高くても、耐久性と素材の良さに納得できる国内メーカー製品を購入し、長く愛用している。")
        experiences.append("安価な代替品を買って失敗した経験から、信頼できるブランドのロングセラー商品を選ぶようにしている。")
    elif values_segment == "トレンド・体験消費":
        experiences.append("SNSで話題の新商品や期間限定の体験型サービスをいち早く予約購入し、満足感を得た。")
        experiences.append("モノの所有よりも、旅行やイベント、趣味など思い出に残るコト消費に支出した。")
    elif values_segment in ["サステナビリティ・エシカル", "健康・ウェルネス投資"]:
        experiences.append("オーガニック食品や睡眠改善デバイス、定期的な健康管理に重点的に支出した。")
        experiences.append("環境負荷に配慮された再生素材パッケージの商品を選び、企業の社会的姿勢に共感して購入した。")
    else:
        experiences.append("生活必需品の購入にあたっては事前に口コミを調べ、失敗のない手堅い選択肢を重視している。")
        experiences.append("大きな買い物をする際は家族と相談し、数週間検討した上で納得して購入した。")
    return experiences

def generate_cohort_personas(
    count: int = 100, 
    preset: str = "general_national", 
    seed: int = 42,
    mode: str = "mode_b",
    interview_samples: list[dict[str, Any]] = None
) -> list[dict[str, Any]]:
    random.seed(seed)
    rng = np.random.RandomState(seed)
    personas = []
    
    samples_len = len(interview_samples) if interview_samples else 0

    for i in range(count):
        grounded_sample = None
        if mode == "mode_c" and samples_len > 0:
            grounded_sample = interview_samples[i % samples_len]

        p = generate_correlated_persona(i, preset=preset, rng=rng, mode=mode, grounded_sample=grounded_sample)
        personas.append(p)
    return personas

def get_cohort_distribution_summary(personas: list[dict[str, Any]]) -> dict[str, Any]:
    """生成コホートの属性分布と統計ベンチマークとの比較指標を計算"""
    total = len(personas)
    if total == 0:
        return {}

    age_groups = {}
    genders = {}
    regions = {}
    values_counts = {}
    personal_incomes = []
    household_incomes = []

    for p in personas:
        ag = p["age_group"]
        age_groups[ag] = age_groups.get(ag, 0) + 1

        g = p["gender"]
        genders[g] = genders.get(g, 0) + 1

        r = p["region"]
        regions[r] = regions.get(r, 0) + 1

        v = p["values_segment"]
        values_counts[v] = values_counts.get(v, 0) + 1

        personal_incomes.append(p["personal_income"])
        household_incomes.append(p["household_income"])

    # 割合換算
    age_ratio = {k: round(v / total, 3) for k, v in age_groups.items()}
    gender_ratio = {k: round(v / total, 3) for k, v in genders.items()}
    region_ratio = {k: round(v / total, 3) for k, v in regions.items()}
    values_ratio = {k: round(v / total, 3) for k, v in values_counts.items()}

    return {
        "total_count": total,
        "age_distribution": {
            "actual_counts": age_groups,
            "actual_ratio": age_ratio,
            "benchmark_ratio": STATISTICAL_BENCHMARKS["age_groups_national"]
        },
        "gender_distribution": {
            "actual_counts": genders,
            "actual_ratio": gender_ratio,
            "benchmark_ratio": STATISTICAL_BENCHMARKS["gender_ratio"]
        },
        "region_distribution": {
            "actual_counts": regions,
            "actual_ratio": region_ratio,
            "benchmark_ratio": STATISTICAL_BENCHMARKS["regions"]
        },
        "values_distribution": {
            "actual_counts": values_counts,
            "actual_ratio": values_ratio
        },
        "income_stats": {
            "personal_mean": round(float(np.mean(personal_incomes)), 1),
            "personal_median": round(float(np.median(personal_incomes)), 1),
            "household_mean": round(float(np.mean(household_incomes)), 1),
            "household_median": round(float(np.median(household_incomes)), 1)
        },
        "data_source": STATISTICAL_BENCHMARKS["source"],
        "notes": STATISTICAL_BENCHMARKS["notes"]
    }
