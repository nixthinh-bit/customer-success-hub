# Automation (workflow)

[English](README.md) · **Tiếng Việt**

Bốn automation sẵn-sàng-chạy cho Customer Success Hub, đóng gói dạng JSON recipe kèm trình
cài chạy một lệnh. Chúng được tạo ở trạng thái **tắt (disabled)** để bạn kiểm tra và đặt
người nhận trước khi có gì kích hoạt.

## Cài đặt

```bash
# chạy từ thư mục gốc của repo
python3 workflows/setup_workflows.py            # tạo cả bốn (disabled)
python3 workflows/setup_workflows.py --enable   # tạo VÀ bật luôn
python3 workflows/setup_workflows.py --dry-run  # chỉ kiểm tra — không tạo gì
```

Trình cài đọc Base token từ `../base_ids.json`, tự phân giải `open_id` Lark **của bạn** (để
cảnh báo về đúng Lark của bạn), chèn `client_token` duy nhất cho từng workflow, rồi gọi
`lark-cli base +workflow-create`. Muốn gửi cho người/nơi khác thì thêm `--receiver ou_xxxxx`.

## Bốn flow

| # | File | Kích hoạt | Nội dung | Gửi cho |
|---|------|-----------|----------|---------|
| ① | `01-health-red-alert.json` | Một dòng **Usage & Healthscore** có `Health Score < 50` được thêm/sửa | "Account health dropped to Red" | bạn (chủ Base) |
| ② | `02-renewal-approaching.json` | **4 tuần trước** một `Renewal Date`, nếu `Outcome = Pending` | "Renewal approaching" | bạn |
| ③ | `03-churn-downsell-logged.json` | Một **Revenue Movement** có `Event Type = Churn hoặc Downsell` | "Churn/Downsell logged — gắn lý do" | bạn |
| ④ | `04-activity-due.json` | **1 ngày trước** `Date` của một **CSM Activity**, nếu `Status = Planned` | "Activity due tomorrow" | bạn |

> **Vì sao là "bạn" chứ không phải CSM của account?** `CSM Owner` trong mẫu này là field
> *Select* với tên hư cấu, mà bước gửi tin nhắn không thể nhắm tới. Xem "Định tuyến tới CSM
> thật" bên dưới để chuyển sang DM thật.

## Cách mỗi recipe được dựng

Mỗi file là một workflow body đầy đủ: `{ client_token, title, steps[] }`.
Một step là `{ id, type, title, next, data }`; `next` nối các step, `null` là kết thúc flow.

- **Trigger** — `ChangeRecordTrigger` (dòng được thêm/sửa, lọc bằng `condition_list`),
  `ReminderTrigger` (N ngày/tuần trước một field ngày), `TimerTrigger` (theo lịch).
- **Action** — `LarkMessageAction` với `receiver`, `title`, `content[]`, `btn_list[]`.
- **Ref** — nội dung tin nhắn lấy giá trị sống bằng `{ "value_type": "ref", "value": "$.t1.<fieldId>" }`.
  `$.t1.recordLink` là URL của record (nút "Open record" dùng cái này).

`condition_list` là mảng OR của các nhóm AND:

```json
"condition_list": [
  { "conjunction": "and", "conditions": [
    { "field_name": "Health Score", "operator": "isLess", "value": [{ "value_type": "number", "value": 50 }] }
  ]}
]
```

Toán tử: `is` / `isNot` / `containsAny` / `doesNotContainAny` / `containsAll` /
`isEmpty` / `isNotEmpty` / `isGreater` / `isGreaterEqual` / `isLess` / `isLessEqual`.
Với field Select dùng `value_type: "option"` và `{ "name": "..." }`.

## Cách chỉnh sửa một flow

**Trên giao diện Base (dễ nhất).** Mở Base → **Automation** → chọn flow → sửa điều kiện
trigger, nội dung tin nhắn, hoặc người nhận → lưu. Hợp cho chỉnh nhanh.

**Bằng code (versioned, lặp lại được).** Sửa JSON rồi áp lại:

- Đổi **ngưỡng** → sửa `condition_list[].conditions[].value` (vd `50` → `60`).
- Đổi **thời điểm** → trong `ReminderTrigger`, sửa `unit` (`DAY`/`WEEK`/`MONTH`) + `offset`
  (DAY ∈ −7…7, WEEK ∈ 1…7). Muốn nhắc ở mốc 60 ngày, xem recipe Timer+Find bên dưới.
- Đổi **tin nhắn** → sửa mảng `content[]` (trộn các item `text` và `ref`).
- Áp lại một file:
  ```bash
  lark-cli base +workflow-create --base-token <token> --json @workflows/01-health-red-alert.json
  ```
  (Đặt `client_token` một giá trị mới trước, hoặc để `setup_workflows.py` lo.)
- **Cập nhật** một flow đang có thay vì tạo mới:
  `lark-cli base +workflow-list` → lấy id → `+workflow-update --workflow-id <id> --json @file`.
- Bật / tắt: `+workflow-enable` / `+workflow-disable --workflow-id <id>`.

### Định tuyến tới CSM thật (tùy chọn)
1. Trong **Portfolio**, thêm field `CSM (person)` kiểu **Person** và điền CSM thật.
2. Trong recipe, đổi `receiver` của action từ `open_id` cố định sang một ref đi qua link tới
   người đó, vd `{ "value_type": "ref", "value": "$.t1.<accountLinkFieldId>.<personFieldId>" }`.
3. Áp lại file.

### Nâng cao: "D-60" tái ký thật
`ReminderTrigger` tối đa khoảng 7 tuần. Để có đúng mốc 60 ngày, dùng `TimerTrigger` (hàng
ngày) → `FindRecordAction` trên **Renewals** lọc theo `Renewal Date` trong vòng 60 ngày và
`Outcome = Pending` → `Loop` → `LarkMessageAction`. Lấy mẫu từ ví dụ "定时+查找+循环" trong
`lark-cli skills read lark-base references/lark-base-workflow-guide.md`.
