# Customer Success Hub — hệ điều hành cho CSM trên Lark Base

[English](README.md) · **Tiếng Việt**

Một mẫu Lark Base có thể nhân bản, biến công việc thường ngày của một Customer Success
Manager thành **một hệ thống liền mạch**: **quản lý danh mục khách → đo sức khỏe từ mức
dùng sản phẩm thật → quản lý tái ký → báo cáo doanh thu churn / downsell / upsell → và sở
hữu một con số thương mại.**

Toàn bộ được dựng bằng Lark CLI (`@larksuite/cli`), nên tái tạo lại từ code chỉ bằng vài
lệnh — chạy lại là có một bản sao mới đã seed đầy đủ.

> **Dữ liệu 100% hư cấu** (50 công ty & 5 CSM bịa) — an toàn để công khai. Không dùng bất
> kỳ dữ liệu doanh nghiệp, tenant hay cá nhân thật nào.

---

## 🎥 Video giới thiệu

https://github.com/user-attachments/assets/57e83780-ba4a-4f5e-a3f5-850f9d3e1412

---

## (1) Nhân bản Base này

> **▶️ [Nhân bản Base →](https://thinhle1.sg.larksuite.com/wiki/IS0AwYTdmiJIbxkOYsQlVwKbgLg?from=from_copylink)**
> Mở link rồi dùng **Save as / Make a copy** để có bản sao chỉnh sửa được của riêng bạn.

Hai cách để có bản của riêng bạn:

1. **Native (nhanh nhất):** mở link mẫu ở trên → **Save as / Make a copy**.
2. **Từ code (mới tinh + tái tạo được):**
   ```bash
   cd cs-hub
   python3 build_schema.py     # Base mới + 7 bảng + field + link + formula
   python3 seed_data.py        # dữ liệu hư cấu (dùng --reset để seed lại)
   python3 make_dashboard.py   # hai dashboard
   python3 workflows/setup_workflows.py   # bốn automation (disabled)
   ```
   `build_schema.py` idempotent và ghi mọi id vào `base_ids.json`.

---

## (2) Base này để làm gì

Đa số CSM đang làm việc rải rác ở năm nơi: CRM cho account, một sheet cho health, một sheet
khác cho tái ký, chat/email cho ghi chú churn, và một slide mỗi quý cho "con số". Sự phân
mảnh đó tạo ra năm nỗi đau lặp đi lặp lại — Base này được thiết kế để gỡ từng cái:

| Nỗi đau của CSM | Base này xử lý thế nào |
|---|---|
| Không có nguồn dữ liệu duy nhất | Một Base, **bảy bảng liên kết**, `Portfolio` là trung tâm |
| Health chỉ là cảm tính | `Health Score` được **tính** từ tín hiệu dùng thật, theo tháng |
| Tái ký bị động | Pipeline tái ký + automation "còn ~4 tuần" |
| Lý do churn không có cấu trúc | Bảng lý do tham chiếu, gắn vào từng đồng doanh thu mất đi |
| CS không gắn với con số | Bảng điểm thương mại theo từng CSM (GRR / NRR / attainment) |

**Dùng để:** chạy review danh mục hàng tuần, phát hiện account rủi ro *trước khi* churn,
làm tái ký theo timeline, và báo cáo retention/expansion cho lãnh đạo từ dữ liệu sống.

---

## (3) Cấu trúc & cách nhập dữ liệu

`Portfolio` là bảng trung tâm; mọi bảng khác đều liên kết về nó.

```
Portfolio (TRUNG TÂM) ── hồ sơ khách: plan, ARR, trạng thái, ngày tái ký, forecast, health
 ├─ Usage and Healthscore   mức dùng theo tháng → tự tính Health Score / Health Tier
 ├─ Renewals                pipeline tái ký: ngày, plan, giá, forecast, kết quả
 ├─ Revenue Movements       mọi biến động ARR (New / Upsell / Downsell / Churn)
 ├─ CSM Activities          nhật ký playbook: QBR, check-in, escalation, gọi tái ký
 └─ Commercial Targets      quota theo CSM × quý: renewal / expansion / GRR / NRR
Churn & Downsell Reasons ── bảng tham chiếu → liên kết từ Renewals & Revenue Movements
```

### 7 bảng — cái gì phải gõ, cái gì tự động

Chú thích: ⌨️ = bạn nhập · 🔗 = tự điền khi liên kết record · ⚙️ = tự tính (formula/rollup, **đừng gõ**)

**Portfolio** — mỗi khách một dòng (bắt đầu từ đây).
⌨️ Account Name, Segment, Industry, Region, CSM Owner, Plan, Seats, Price per Seat, Status,
Start Date, Next Renewal Date, Renewal Forecast · ⚙️ ARR (= Seats × Price), Current Health
Score, Avg Health 6mo, Last Snapshot · 🔗 Usage / Renewals / Revenue Movements / Activities.

**Usage and Healthscore** — mỗi account **mỗi tháng** một dòng (động cơ của mô hình).
🔗 Account · ⌨️ Month, Active Users, License Utilization %, Logins, Core & Advanced Feature
Adoption %, Stickiness (DAU/MAU) %, Sentiment 0–10, Support Tickets · ⚙️ **Health Score**,
**Health Tier**.

**Renewals** — mỗi lần tái ký một dòng.
🔗 Account, Reason (nếu mất/giảm) · ⌨️ Renewal Date, Current/Proposed Plan, Current/Proposed
ARR, Forecast, Probability %, Outcome, Owner · ⚙️ ARR Delta.

**Revenue Movements** — mỗi biến động ARR một dòng (nguồn sự thật về doanh thu).
🔗 Account, Linked Renewal, Reason · ⌨️ Event Type, Event Date, ARR Before, ARR After,
Plan From/To, Owner · ⚙️ ARR Delta.

**Churn & Downsell Reasons** — danh sách tham chiếu (điền một lần, dùng lại khắp nơi).
⌨️ Reason, Category, Applies To, Description, Mitigation Playbook.

**CSM Activities** — nhật ký playbook.
🔗 Account, Related Renewal · ⌨️ Type, Date, Owner, Status, Outcome / Next Steps.

**Commercial Targets** — bảng điểm theo CSM theo quý.
⌨️ CSM Owner, Quarter, Book of Business ARR, Renewal & Expansion Target/Actual, GRR & NRR
Target/Actual · ⚙️ Renewal & Expansion Attainment %, NRR vs Target, Status.

### Health Score — tính ra, không đoán

`Health Score` (0–100) là công thức có trọng số trên các tín hiệu dùng thật:

```
0.30 · License Utilization %      + 0.25 · Core Feature Adoption %
0.15 · Advanced Feature Adoption % + 0.10 · Stickiness (DAU/MAU)
0.10 · Sentiment (→0-100)         + 0.10 · (100 − Support Tickets·10)
```

`Health Tier` phân nhóm 🟢 ≥75 / 🟡 50–74 / 🔴 <50. Vì tính theo tháng, bạn thấy được **xu
hướng** — account rủi ro sẽ tụt dốc thấy rõ trước khi churn.

### Cắt gọn còn đúng thứ bạn cần

Không nhất thiết giữ cả bảy bảng. Các mức đề xuất:

- **Khởi đầu tinh gọn (5 bảng):** `Portfolio`, `Usage and Healthscore`, `Renewals`,
  `Revenue Movements`, `Churn & Downsell Reasons`. Bấy nhiêu đã đủ health + tái ký + báo cáo
  churn cho phần lớn CSM.
- **Thêm khi cần:** `CSM Activities` (chỉ khi muốn log QBR/check-in ngay trong Base thay vì
  calendar), và `Commercial Targets` (chỉ khi CS gánh quota — đây là phần nâng cao nhất; bỏ
  đi cũng không ảnh hưởng phần còn lại).
- **Cắt ở cấp field:** `Notes`, `Avg Health 6mo`, `Last Snapshot`, `Probability %` đều tùy
  chọn. Field nào không duy trì thì xóa hẳn thay vì để điền dở dang.

Để xóa bảng/field: làm trong giao diện Base, hoặc xóa khỏi `build_schema.py` trước khi nhân
bản để các bản sao mới không kèm nó.

---

## (4) Workflow — cài đặt & bảo trì

Bốn automation đóng gói dạng JSON recipe + trình cài chạy một lệnh. Chúng được tạo ở trạng
thái **tắt (disabled)**, để bạn kiểm tra người nhận và điều kiện trước khi có gì kích hoạt.

```bash
python3 workflows/setup_workflows.py            # tạo cả bốn (disabled)
python3 workflows/setup_workflows.py --enable   # tạo VÀ bật luôn
python3 workflows/setup_workflows.py --dry-run  # chỉ kiểm tra, không tạo gì
```

Trình cài tự lấy `open_id` Lark **của bạn** và mặc định gửi cảnh báo cho bạn.

| # | Flow | Kích hoạt khi |
|---|------|--------------|
| ① | **Health → Red alert** | một snapshot có `Health Score < 50` |
| ② | **Renewal approaching** | ~4 tuần trước `Renewal Date` mà vẫn `Pending` |
| ③ | **Churn / Downsell logged** | một Revenue Movement là `Churn` hoặc `Downsell` |
| ④ | **Activity due** | 1 ngày trước `Date` của một CSM Activity `Planned` |

**Chỉnh sửa flow** (ngưỡng, thời điểm, nội dung tin nhắn, đổi người nhận sang Person field để
DM đúng CSM, hay làm D-60 tái ký thật) được ghi trong
**[workflows/README.md](workflows/README.md)** — cả cách làm trên UI lẫn cách versioned bằng
code. Xem flow đang có bằng `lark-cli base +workflow-list`, cập nhật bằng `+workflow-update`.

### Dashboard (đã dựng sẵn, charts-as-code)
`make_dashboard.py` dựng hai dashboard theo hai nhịp báo cáo:
- **CSM Weekly Review** (vận hành, nhóm theo CSM): số account, health trung bình, book ARR
  theo CSM, status/health theo CSM, pipeline tái ký, activities.
- **Executive Monthly — BOD** (chiến lược): tổng ARR, NRR%/GRR% blended, ARR bridge theo loại
  event, ARR theo segment/ngành, churn ARR theo lý do, funnel tái ký, NRR% theo CSM.

---

## Các file

| File | Vai trò |
|---|---|
| `build_schema.py` | Tạo Base, bảng, field, link, formula |
| `gen_data.py` | Bộ sinh dữ liệu hư cấu tất định (`random.seed(42)`) |
| `seed_data.py` | Tạo record hàng loạt, phân giải link field thành record id |
| `make_dashboard.py` | Dựng hai dashboard báo cáo (charts-as-code) |
| `workflows/` | Bốn recipe automation + trình cài `setup_workflows.py` |
| `base_ids.example.json` | Mẫu cấu trúc file build; file thật `base_ids.json` (app_token + URL Base của bạn) sinh ra ở máy local và bị git bỏ qua |

## Ghi chú
- Tiền tệ là **USD** xuyên suốt. `CSM Owner` là field Select (không phải Person) để bộ dữ
  liệu hư cấu tự khép kín — xem workflows/README.md để đổi sang người thật.
- Token CLI dùng ở đây có scope **write** Bitable nhưng không có scope **read** record — không
  ảnh hưởng việc dùng Base; chỉ là số liệu được kiểm chứng trong giao diện Base.
