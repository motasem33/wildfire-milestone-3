from pathlib import Path
import json
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'presentation' / 'Final_Demo_Day_Code_Guide_Arabic.docx'
OUT.parent.mkdir(parents=True, exist_ok=True)

metrics = json.loads((ROOT / 'reports/final_model_metrics.json').read_text(encoding='utf-8'))
cv = pd.read_csv(ROOT / 'reports/model_comparison_cv.csv').sort_values('cv_average_precision_mean', ascending=False)
audit = json.loads((ROOT / 'reports/preprocessing_audit.json').read_text(encoding='utf-8'))

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.7)
sec.bottom_margin = Inches(0.65)
sec.left_margin = Inches(0.72)
sec.right_margin = Inches(0.72)

NAVY = '0B192C'
RUST = 'B94E35'
MUTED = '4F5E70'
PALE = 'F1EEE6'

# Use a consistent Arabic-capable body font and readable heading hierarchy.
for style_name, size, color, bold in [('Normal', 11, MUTED, False), ('Title', 24, NAVY, True), ('Heading 1', 17, NAVY, True), ('Heading 2', 13, RUST, True), ('Heading 3', 11, NAVY, True)]:
    style = doc.styles[style_name]
    style.font.name = 'Arial'
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor.from_string(color)
    style._element.rPr.rFonts.set(qn('w:ascii'), 'Arial')
    style._element.rPr.rFonts.set(qn('w:hAnsi'), 'Arial')
    style._element.rPr.rFonts.set(qn('w:cs'), 'Arial')


def rtl_paragraph(p):
    pPr = p._p.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), '1')
    pPr.append(bidi)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def add_text(text, style=None, bold=False, color=None, size=None, align=WD_ALIGN_PARAGRAPH.RIGHT, rtl=True, after=5):
    p = doc.add_paragraph(style=style)
    p.alignment = align
    if rtl:
        rtl_paragraph(p)
    p.paragraph_format.space_after = Pt(after)
    r = p.add_run(text)
    r.bold = bold
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    r.font.name = 'Arial'
    r._element.get_or_add_rPr().rFonts.set(qn('w:cs'), 'Arial')
    return p


def add_code(code):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Inches(0.18)
    p.paragraph_format.right_indent = Inches(0.18)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), PALE)
    pPr.append(shd)
    r = p.add_run(code)
    r.font.name = 'Consolas'
    r._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), 'Consolas')
    r._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), 'Consolas')
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor.from_string(NAVY)
    return p


def add_labeled(label, text):
    p = doc.add_paragraph()
    rtl_paragraph(p)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(label + ': ')
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(RUST)
    r.font.name = 'Arial'
    r._element.get_or_add_rPr().rFonts.set(qn('w:cs'), 'Arial')
    rr = p.add_run(text)
    rr.font.name = 'Arial'
    rr._element.get_or_add_rPr().rFonts.set(qn('w:cs'), 'Arial')
    return p


def add_image(path, caption, width=6.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Inches(width))
    c = doc.add_paragraph()
    rtl_paragraph(c)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(8)
    rr = c.add_run(caption)
    rr.italic = True
    rr.font.size = Pt(9)
    rr.font.color.rgb = RGBColor.from_string(MUTED)
    rr.font.name = 'Arial'
    rr._element.get_or_add_rPr().rFonts.set(qn('w:cs'), 'Arial')


def add_section(title, time, explanation, code, output, image=None, caption=None, transition=None):
    doc.add_heading(title, level=1)
    add_labeled('الوقت المقترح', time)
    add_labeled('الشرح الذي تقوله', explanation)
    add_labeled('الكود الفعلي من المشروع', 'المقطع التالي مأخوذ من ملفات المشروع، ويمكنك الإشارة إليه دون قراءة كل سطر.')
    add_code(code)
    add_labeled('المخرج ومعناه', output)
    if image:
        add_image(ROOT / image, caption or image)
    if transition:
        add_labeled('جملة انتقال', transition)


# Header and footer
header = sec.header.paragraphs[0]
header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
rtl_paragraph(header)
rr = header.add_run('مشروع حرائق الغابات | دليل Demo Day')
rr.font.name = 'Arial'; rr.font.size = Pt(9); rr.font.color.rgb = RGBColor.from_string(MUTED)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
rr = footer.add_run('صفحة ')
rr.font.name = 'Arial'; rr.font.size = Pt(9)
fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE'); footer._p.append(fld)

# Cover
p = doc.add_paragraph(style='Title'); rtl_paragraph(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run('دليل شرح الكود ومناقشة المشروع')
add_text('مشروع تصنيف بدايات حرائق الغابات — العرض النهائي Demo Day', size=15, bold=True, color=RUST, align=WD_ALIGN_PARAGRAPH.CENTER)
add_text('دليل عملي: شرح ثم كود ثم مخرج ورسم، مع خطة زمنية لعرض 20 دقيقة وأسئلة متوقعة من اللجنة.', size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
add_text('المجموعة: California Weather and Fire Prediction Dataset | فترة التحليل: 1984–2023', size=11, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
add_text('تنبيه مهم: المشروع تصنيف تاريخي لليوم نفسه، وليس نظام إنذار مبكر تشغيليًا مثبتًا.', size=11, bold=True, color=RUST, align=WD_ALIGN_PARAGRAPH.CENTER)
add_text('ملخص سريع للجنة', style='Heading 2')
cover_table = doc.add_table(rows=2, cols=3)
cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
cover_table.style = 'Table Grid'
cover_values = [
    ('14,610', 'يوم للتحليل'), ('4', 'نماذج مقارنة'), ('5', 'طيات تحقق زمني'),
    ('87.0%', 'استدعاء الحرائق'), ('653', 'إنذارًا خاطئًا'), ('2016–2023', 'فترة الاختبار')
]
for cell, (value, label) in zip([cell for row in cover_table.rows for cell in row.cells], cover_values):
    cell.text = value
    label_para = cell.add_paragraph(label)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for para in cell.paragraphs:
        rtl_paragraph(para)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in para.runs:
            run.font.name = 'Arial'
            run.font.size = Pt(12 if para == cell.paragraphs[0] else 9)
            run.font.color.rgb = RGBColor.from_string(NAVY)
add_text('رسالتك الأساسية: لدينا خط أساس بحثي واعد، لكن لا يجوز وصفه بإنذار مبكر أو استخدامه تشغيليًا قبل اختبار بيانات سابقة للحدث والتحقق المكاني والزمني المستقل.', size=11, bold=True, color=RUST)
doc.add_page_break()

# Brief contents
add_text('خريطة الدليل', style='Heading 1')
for item in [
    '1. خطة عرض 20 دقيقة', '2. المشكلة والبيانات وجودة الوسوم', '3. التحليل الاستكشافي والرسوم',
    '4. تجهيز البيانات والميزات ومنع التسرب', '5. مقارنة النماذج والتحقق الزمني',
    '6. الاختبار النهائي وتفسير النتائج', '7. القيود والخطوات المستقبلية', '8. أسئلة اللجنة وإجابات مقترحة',
    '9. تشغيل المشروع والملفات المهمة'
]:
    add_text(item, size=11, after=2)

# Timing plan table
add_text('1. خطة عرض 20 دقيقة', style='Heading 1')
plan = [
    ('0:00–2:00', 'المشكلة وسياق حرائق الغابات'),
    ('2:00–4:00', 'مصدر البيانات وحجمها وقرار التغطية'),
    ('4:00–7:00', 'تنظيف البيانات والتحليل الاستكشافي'),
    ('7:00–10:00', 'هندسة الميزات والتقسيم الزمني ومنع التسرب'),
    ('10:00–13:00', 'النماذج والتحقق المتقاطع واختيار النموذج'),
    ('13:00–16:00', 'أداء الاختبار النهائي ومصفوفة الالتباس'),
    ('16:00–18:00', 'التفسير والقيود والعمل المستقبلي'),
    ('18:00–20:00', 'خلاصة موجزة وتسليم الكلام للأسئلة'),
]
tbl = doc.add_table(rows=1, cols=2)
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl.style = 'Table Grid'
for c, txt in zip(tbl.rows[0].cells, ['الوقت', 'المحور']):
    c.text = txt
for time, topic in plan:
    cells = tbl.add_row().cells
    cells[0].text = time
    cells[1].text = topic
for row in tbl.rows:
    for cell in row.cells:
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for p in cell.paragraphs:
            rtl_paragraph(p)
            for run in p.runs:
                run.font.name = 'Arial'; run.font.size = Pt(10)

add_text('افتتاحية جاهزة', style='Heading 2')
add_text('«مشروعنا يدرس ما إذا كان بالإمكان تصنيف اليوم الذي سُجلت فيه بداية حريق باستخدام مؤشرات الطقس اليومية. بدأنا ببيانات صغيرة من 244 سجلًا، ثم انتقلنا إلى مجموعة بيانات حقيقية أكبر بكثير بدل إنشاء بيانات اصطناعية. سنعرض كيف فحصنا التغطية، جهزنا الميزات، قارنّا النماذج زمنيًا، ثم اختبرنا النموذج على فترة لاحقة لم يرها أثناء التدريب.»')
add_text('ملاحظة للعرض: لا تبدأ بقراءة الكود. اشرح سؤال المشروع أولًا، ثم اعرض مقطع الكود المحدد عند كل مرحلة.', bold=True, color=RUST)

doc.add_page_break()

# Section 1
add_section(
    '2. المشكلة والبيانات وقرار التغطية', '2 دقيقة',
    'المتغير الذي نحاول تصنيفه هو FIRE_START_DAY: هل سُجلت بداية حريق في اليوم أم لا؟ مصدر البيانات يجمع طقسًا يوميًا من NOAA وسجلات حوادث من CAL FIRE حسب وصف مجموعة البيانات. حجم المصدر 14,988 صفًا، لكننا استبعدنا 378 صفًا من 2024 وحتى أول 12 يومًا من 2025 لأن جميع وسومها كانت سلبية، وهو نمط قد يدل على نقص في التغطية لا على انعدام الحرائق. لذلك التحليل الأساسي 14,610 يومًا بين 1984 و2023.',
    'raw = pd.read_csv(RAW_PATH, parse_dates=["DATE"])\nraw = raw.sort_values("DATE").reset_index(drop=True)\ndf = raw.loc[raw["YEAR"] <= 2023].copy().reset_index(drop=True)\ndf.to_csv(PROCESSED_DIR / "california_wildfire_1984_2023.csv", index=False)',
    '14,988 صفًا بالمصدر؛ 14,610 صفًا للتحليل؛ 378 صفًا مستبعدًا؛ الفترة النهائية من 1984-01-01 إلى 2023-12-31. ثلاثة قيَم مفقودة في متوسط سرعة الرياح وبعض المشتقات المرتبطة بها، وستُعالج داخل خط المعالجة الملائم للتدريب.',
    'visuals/missing_values.png', 'الشكل 1. القيم المفقودة في نافذة التحليل (مصدره run_milestone3.py).',
    '«بعد تحديد فترة موثوقة للوسوم، انتقلنا إلى وصف الأنماط قبل بناء أي نموذج.»'
)

# EDA
add_section(
    '3. التحليل الاستكشافي: الموسم والحرارة', '3 دقائق',
    'استخدمنا التجميع حسب الموسم، ثم حسبنا معدل الأيام الموسومة ببداية حريق. ولتحليل الحرارة قسمنا MAX_TEMP إلى أربعة أرباع متساوية تقريبًا باستخدام qcut. الوصف في الرسوم ارتباط داخل هذه البيانات، ولا يثبت أن الموسم أو الحرارة يسببان الحريق.',
    'season = df.groupby("SEASON")["FIRE_START_DAY"].agg(["mean", "sum", "count"])\n\ntemp = df.dropna(subset=["MAX_TEMP"]).copy()\ntemp["MAX_TEMP_QUARTILE"] = pd.qcut(temp["MAX_TEMP"], 4, duplicates="drop")\ntemp_rate = temp.groupby("MAX_TEMP_QUARTILE", observed=True)["FIRE_START_DAY"].mean() * 100',
    'معدل الوسم حسب الموسم: الصيف 70.30%، الخريف 35.63%، الربيع 22.15%، الشتاء 7.53%. حسب أرباع الحرارة: 7.20%، 28.62%، 48.06%، 53.79% من الأقل إلى الأعلى. تذكر للجنة أن هذه النسب من عينة البيانات نفسها، وليست احتمالات عامة أو أثرًا سببيًا.',
    'visuals/season_and_year.png', 'الشكل 2. عدد أيام بدايات الحرائق المسجلة حسب الموسم والسنة.',
    '«بعد فهم الأنماط، جهزنا البيانات بطريقة تحافظ على الترتيب الزمني.»'
)
add_image(ROOT / 'visuals/fire_rate_by_temperature.png', 'الشكل 3. معدل وسم بداية الحريق عبر أرباع درجة الحرارة القصوى.')

# Feature engineering and split
add_section(
    '4. الميزات الزمنية والتقسيم ومنع تسرب البيانات', '3 دقائق',
    'رتبنا الصفوف حسب التاريخ وقسمناها زمنيًا: أول 80% للتدريب وآخر 20% للاختبار. لم نستخدم تقسيمًا عشوائيًا لأن ذلك قد يخلط الأيام المستقبلية بالماضية. كذلك أظهر تدقيقنا أن بعض حقول “lagged” الجاهزة تحتوي اليوم الحالي، لذلك أعدنا حساب ملخص السبعة أيام السابقة باستخدام shift(1) قبل rolling. DATE بقي للترتيب والتقسيم ولم يدخل كميزة مباشرة.',
    'df = df.sort_values("DATE").reset_index(drop=True)\ndf["PREVIOUS_7D_PRECIPITATION"] = df["PRECIPITATION"].shift(1).rolling(7, min_periods=1).sum()\ndf["PREVIOUS_7D_AVG_WIND_SPEED"] = df["AVG_WIND_SPEED"].shift(1).rolling(7, min_periods=1).mean()\ncut = int(len(df) * 0.80)\ntrain, test = df.iloc[:cut].copy(), df.iloc[cut:].copy()',
    'التدريب: 11,688 يومًا (1984–2015)، والاختبار: 2,922 يومًا (2016–2023). نسبة الوسوم الإيجابية ارتفعت من 31.0% في التدريب إلى 46.0% في الاختبار؛ وهذا تغير زمني مهم يحد من التعميم. ميزات السبعة أيام السابقة لا تستخدم معلومات اليوم الحالي.',
    'visuals/chronological_split.png', 'الشكل 4. التقسيم الزمني الفعلي: 80% للتدريب و20% للاختبار.',
    '«كل خطوة تعلم من البيانات، مثل التعويض والتقييس، تُلائم داخل بيانات التدريب فقط.»'
)

# preprocessing pipeline
add_section(
    '5. المعالجة المسبقة ومقارنة النماذج', '3 دقائق',
    'أنشأنا خط معالجة واحدًا للميزات الرقمية: تعويض الوسيط ثم StandardScaler. أما الموسم فهو فئوي، لذلك نعوض الأكثر تكرارًا ثم نستخدم One-Hot Encoding. وضع المعالجة والمصنف داخل Pipeline يمنع ملاءمة التحويلات على الطية التي يجري تقييمها. قارنا خط أساس للأغلبية وثلاثة مصنفات.',
    'numeric = Pipeline([\n    ("imputer", SimpleImputer(strategy="median")),\n    ("scaler", StandardScaler()),\n])\ncategorical = Pipeline([\n    ("imputer", SimpleImputer(strategy="most_frequent")),\n    ("onehot", OneHotEncoder(handle_unknown="ignore")),\n])\npreprocessor = ColumnTransformer([\n    ("numeric", numeric, NUMERIC_FEATURES),\n    ("categorical", categorical, CATEGORICAL_FEATURES),\n])',
    'المقارنة شملت Majority baseline وLogistic Regression وRandom Forest وHistogram Gradient Boosting. متوسط Average Precision عبر خمس طيات زمنية كان: 0.652 للانحدار اللوجستي، 0.648 للغابة العشوائية، 0.623 للتعزيز، و0.321 لخط الأساس. الفرق بين أول نموذجين صغير والانحراف عبر الطيات ملحوظ.',
    'visuals/model_comparison_cv.png', 'الشكل 5. مقارنة متوسط Average Precision والانحراف عبر خمس طيات زمنية.',
    '«اختير النموذج صاحب أعلى متوسط Average Precision وفق قاعدة مسجلة مسبقًا، ثم استخدمنا الاختبار النهائي مرة واحدة للتقرير.»'
)

# Final results
add_section(
    '6. التقييم النهائي ومصفوفة الالتباس', '3 دقائق',
    'بعد اختيار Logistic Regression، أعدنا تدريبه على كامل فترة التدريب ثم قيّمناه على 2016–2023. حد القرار 0.5 محدد مسبقًا ولم نضبطه على الاختبار. الاستدعاء العالي يعني أن النموذج التقط معظم الأيام الموسومة بحريق، لكن الدقة الأقل تعني وجود إنذارات خاطئة كثيرة. لذلك لا نعرض رقمًا واحدًا دون تفسير نوع الأخطاء.',
    'final_model.fit(X_train, y_train)\ny_probability = final_model.predict_proba(X_test)[:, 1]\ny_prediction = (y_probability >= 0.5).astype(int)\nmatrix = confusion_matrix(y_test, y_prediction, labels=[0, 1])',
    'على الاختبار: Accuracy 71.7%، Balanced Accuracy 72.8%، Precision للحريق 64.2%، Recall 87.0%، F1 73.8%، ROC AUC 0.839، وAverage Precision 0.797. مصفوفة الالتباس: 925 سالبًا صحيحًا، 653 إنذارًا خاطئًا، 175 حريقًا فائتًا، و1,169 إيجابيًا صحيحًا. النتائج تعتمد على حد 0.5 وعلى اختلاف التوزيع بين الفترتين.',
    'visuals/final_model_confusion_matrix.png', 'الشكل 6. مصفوفة الالتباس على فترة الاختبار المحجوزة.',
    '«هذه نتيجة تصنيف تاريخي على اليوم نفسه؛ نحتاج ميزات سابقة فقط وتجارب مستقلة قبل أي حديث عن الإنذار المبكر.»'
)

# Interpretation
add_section(
    '7. تفسير النموذج والقيود', '2 دقائق',
    'استخدمنا Permutation Importance كتشخيص: نقيس انخفاض Average Precision عند خلط قيم ميزة في عينة الاختبار. كانت SEASON ثم AVG_WIND_SPEED ثم WIND_TEMP_RATIO أعلى الميزات في هذا الفحص. هذا يصف اعتماد النموذج في هذه العينة ولا يثبت أثرًا سببيًا. كما أن درجات المصنف ليست احتمالات مخاطر معايرة.',
    'permutation = permutation_importance(\n    final_model, X_test, y_test,\n    scoring="average_precision", n_repeats=5,\n    random_state=42, n_jobs=-1\n)',
    'ترتيب أعلى الميزات: SEASON (0.113)، AVG_WIND_SPEED (0.094)، WIND_TEMP_RATIO (0.067)، ثم PREVIOUS_7D_PRECIPITATION (0.025) وMIN_TEMP (0.019). من القيود: فجوة محتملة في وسوم 2024–2025، تغير معدل الإيجابيات بين التدريب والاختبار، ووجود طقس اليوم نفسه في المدخلات.',
    'visuals/selected_model_feature_importance.png', 'الشكل 7. أهمية تبديل الميزات للنموذج المختار؛ تشخيص وليست علاقة سببية.',
    '«الخطوة التالية هي تحويل المسألة إلى توقع قبل الحدث، مع بيانات مكانية ومقاييس تكلفة للإنذار الخاطئ.»'
)

# Q&A
add_text('8. أسئلة اللجنة وإجابات مقترحة', style='Heading 1')
qa = [
('لماذا لم نُكبّر البيانات اصطناعيًا؟', 'لأن نسخ الصفوف أو توليد قياسات غير حقيقية قد يضخم الأداء دون إضافة أحداث مستقلة. استخدمنا مجموعة حقيقية موثقة أكبر بدل ذلك.'),
('لماذا استبعدتم 2024–2025؟', 'كل الأيام المتاحة في هذه الفترة موسومة False، وهو تغير مفاجئ قد يعني فجوة في تغطية الوسوم؛ لم نفسره كدليل على عدم حدوث حرائق.'),
('لماذا تقسيم زمني وليس عشوائيًا؟', 'لأن الهدف الزمني يجب أن يُختبر على مستقبل لاحق. التقسيم العشوائي يسمح بانتقال أنماط قريبة زمنيًا بين التدريب والاختبار.'),
('ما معنى shift(1) قبل rolling؟', 'shift(1) يؤخر السلسلة يومًا حتى تبدأ نافذة السبعة أيام السابقة من الأمس، فلا تدخل بيانات اليوم الجاري في ميزة الماضي.'),
('لماذا اخترتم Average Precision؟', 'لأنه يلخص أداء ترتيب الحالات عبر عتبات متعددة ويركز على precision–recall، بينما الدقة وحدها قد تخفي المقايضة بين الإنذارات والحرائق الفائتة. لدينا أيضًا تغير بمعدل الإيجابيات زمنيًا.'),
('لماذا اختير Logistic Regression مع أن Random Forest أفضل ببعض المقاييس؟', 'قاعدة الاختيار المسجلة كانت أعلى متوسط AP عبر CV؛ كان 0.6517 مقابل 0.6476 للغابة العشوائية. الفرق طفيف والانحرافات كبيرة ومتداخلة، لذلك لا ندعي تفوقًا حاسمًا.'),
('هل 87% Recall يعني أن النظام جاهز؟', 'لا. يعني أن النموذج التقط 87% من إيجابيات فترة الاختبار عند عتبة 0.5، لكنه أنتج 653 إنذارًا خاطئًا ولم يُختبر تشغيليًا أو زمنيًا على خصائص قبل الحدث فقط.'),
('هل هذا نموذج إنذار مبكر؟', 'لا. ميزات الطقس تتضمن قياسات اليوم نفسه الذي سُجلت فيه بداية الحريق؛ إنه تصنيف تاريخي متزامن، وليس توقعًا استباقيًا مثبتًا.'),
('ما معنى 653 إنذارًا خاطئًا؟', 'هي أيام تنبأ فيها المصنف ببداية حريق بينما كان الوسم الفعلي سلبيًا. الأثر التشغيلي يتوقف على تكلفة الاستجابة وحدود الموارد، لذلك يلزم ضبط العتبة على مجموعة تحقق وبمشاركة أصحاب القرار.'),
('هل أهمية المتغير تثبت أن الرياح تسبب الحرائق؟', 'لا. هي تقيس اعتماد تنبؤ النموذج على المتغير في هذه العينة؛ لا تستنتج السببية من هذا التحليل.'),
('ما أول خطوة مستقبلية؟', 'إعادة صياغة الهدف إلى توقع قبل الحدث بزمن محدد، واستخدام ميزات متاحة قبل الموعد فقط، ثم تحقق زمني ومكاني مستقل ومعايرة العتبة وفق تكاليف الإنذار.'),
('كيف أعيد تشغيل المشروع؟', 'من مجلد المشروع: python run_milestone3.py لإعادة توليد التحضير والرسوم، ثم python run_milestone4.py للمقارنة والتقييم، أو تشغيل الدفاتر بالترتيب. تُثبت المكتبات في requirements.txt.'),
]
for question, answer in qa:
    add_text(question, style='Heading 2')
    add_text(answer)

add_text('9. الملفات التي تفتحها أثناء العرض', style='Heading 1')
for item in [
    'الكود الكامل للتجربة: run_milestone3.py و run_milestone4.py',
    'دفتر التحليل: notebooks/01_eda_wildfire.ipynb',
    'دفتر المعالجة: notebooks/02_preprocessing_wildfire.ipynb',
    'دفتر التدريب والتقييم: notebooks/03_model_training_and_evaluation.ipynb',
    'نتائج النموذج النهائي: reports/final_model_metrics.json',
    'مقارنة النماذج: reports/model_comparison_cv.csv',
    'الرسوم المناسبة للشرح: visuals/season_and_year.png, fire_rate_by_temperature.png, model_comparison_cv.png, final_model_confusion_matrix.png, selected_model_feature_importance.png'
]:
    add_text(item, size=10, after=3)

add_text('جملة ختامية جاهزة', style='Heading 2')
add_text('«قدمنا مسارًا كاملًا من مشكلة واقعية إلى بيانات موثقة وتحليل ونماذج وتقييم زمني. النتيجة مفيدة كخط أساس بحثي، لكننا نلتزم بحدودها: إنها لا تثبت السببية ولا تمثل إنذارًا مبكرًا، وتحتاج إلى بيانات مستقبلية مناسبة وتحقق مستقل قبل أي تطبيق عملي.»')

# Set metadata and save
props = doc.core_properties
props.title = 'دليل شرح الكود ومناقشة مشروع حرائق الغابات — Demo Day'
props.subject = 'عرض 20 دقيقة، شرح كود، مخرجات، رسوم، وأسئلة لجنة'
props.author = 'Wildfire Project Team'
doc.save(OUT)
print(OUT)
