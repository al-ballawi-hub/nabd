# نبض (Nabd) — مشروع التخرج

منصة سحابية ذكية لتحليل السجلات الطبية ومراجعة الملفات الطبية.

## المتطلبات
- Python 3.12+
- Node.js 20+

## التشغيل (أول مرة)

### 1) تشغيل الـ API (الباك إند)
```bash
cd services/api
python -m venv .venv
# ويندوز: .venv\Scripts\activate
# ماك/لينكس: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
يشتغل على: http://localhost:8000
وثائق الـ API التفاعلية: http://localhost:8000/docs

### 2) تشغيل الواجهة (الفرونت إند)
في طرفية ثانية:
```bash
cd apps/web
npm install
npm run dev
```
يشتغل على: http://localhost:5173

### 3) توليد البيانات التجريبية
افتح الواجهة واضغط زر **"توليد بيانات تجريبية"**، أو نفّذ:
```bash
curl -X POST http://localhost:8000/api/v1/seed
```

## ملاحظات
- قاعدة البيانات الافتراضية SQLite (ملف nabd.db يتنشأ تلقائيًا) — بدون أي تنصيب إضافي.
- لاحقًا (مرحلة الـ OCR) نضيف مفتاح Gemini API في ملف `.env` — شوف `.env.example`.
- البيانات كلها وهمية ومولّدة للاختبار فقط.
