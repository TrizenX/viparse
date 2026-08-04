# viparse

> Thư viện đọc tài liệu tiếng Việt cho RAG — xử lý bảng mã cũ TCVN3, VNI, VISCII, VPS.

[![PyPI](https://img.shields.io/pypi/v/viparse)](https://pypi.org/project/viparse/)
[![Python](https://img.shields.io/pypi/pyversions/viparse)](https://pypi.org/project/viparse/)
[![License](https://img.shields.io/pypi/l/viparse)](LICENSE)

**English:** [README.md](README.md) · **Trang chủ:** [viparse.trizenx.com](https://viparse.trizenx.com)

Một lệnh để biến tài liệu tiếng Việt bất kỳ — kể cả file dùng **phông chữ cũ** `.VnTime`,
`VNI-Times`, file `.doc` / `.xls` / `.ppt` đời cũ, hay PDF scan — thành Unicode **dựng sẵn (NFC)**
sạch, ở dạng Markdown hoặc JSON, sẵn sàng đẩy vào vector DB.

```python
import viparse

viparse.fix("B¸o c¸o tµi chÝnh quý II n¨m 2026")
# → 'Báo cáo tài chính quý II năm 2026'

docs = viparse.load("bao_cao_2003.doc")  # list[Document], đã NFC
```

## Vấn đề: file mở ra chữ bị lỗi

Nếu bạn từng mở một file Word đời cũ và thấy như thế này:

```
B¸o c¸o tµi chÝnh quý II n¨m 2026        ← phông .VnTime, bảng mã TCVN3 (ABC)
Coäng hoøa xaõ hoäi chuû nghóa Vieät Nam ← phông VNI-Times, bảng mã VNI
```

thì **file không hỏng**. Trước khi Unicode phổ biến ở Việt Nam, chữ có dấu được lưu bằng
các byte Latin thông thường, và chỉ hiện ra đúng khi máy có đúng bộ phông đó. Máy bạn
không có `.VnTime`, nên bạn thấy đúng những byte đang nằm trong file.

Đây chính là chỗ mọi thư viện đọc tài liệu thông thường **đọc đúng mà vẫn sai**: chúng lấy
byte ra một cách trung thực, và trung thực một cách vô dụng. Bạn không thể tìm kiếm,
không thể embedding, không thể đưa cho LLM đọc.

Về bản chất đây là việc mà chức năng **"Công cụ → Chuyển mã"** của Unikey vẫn làm — nhưng
làm được trên cả file, giữ nguyên bảng biểu, và gọi được từ trong code.

## Vị trí của viparse

viparse **không** phải thư viện đọc tài liệu đa năng và không cố thay thế cái nào cả.
**Unstructured**, **LlamaParse**, **docling** hỗ trợ nhiều định dạng hơn hẳn, phân tích bố
cục và dựng lại bảng tốt hơn hẳn. viparse lo đúng một tầng mà chúng không được thiết kế
xoay quanh: **tầng chữ tiếng Việt**.

Nên cách dùng hợp lý nhất thường là ghép chứ không thay:

```python
import viparse

docs = [viparse.fix(doc.page_content) for doc in some_other_loader.load()]
```

`fix()` nhận chuỗi chứ không nhận đường dẫn, nên nó ghép được với bất cứ thứ gì đã đọc file
trước đó. Văn bản đã là Unicode, và văn bản không phải tiếng Việt, sẽ được trả lại nguyên
vẹn.

## Cài đặt

Cần **Python 3.11+**. Bản lõi thuần stdlib — mọi bộ đọc file và OCR đều nằm sau `extras`,
cài thêm khi cần:

```bash
pip install viparse                # lõi — thuần stdlib
pip install "viparse[office]"      # .docx/.xlsx/.pptx và .doc/.xls/.ppt đời cũ
pip install "viparse[pdf]"         # PDF số hoá
pip install "viparse[rtf]"         # RTF
pip install "viparse[ocr]"         # PDF scan (cần cài Tesseract)
pip install "viparse[langchain]"   # adapter LangChain
pip install "viparse[llamaindex]"  # adapter LlamaIndex
pip install "viparse[mcp]"         # MCP server, cho AI agent
pip install "viparse[all]"         # mọi engine và adapter
```

`mcp` cố ý **không** nằm trong `all`: `all` nói về khả năng đọc file, và việc cài đủ bộ đọc
không nên kéo theo một server runtime.

Chạy `viparse doctor` để xem những engine nào đang bật với các extra bạn đã cài.

## Cách dùng

### Sửa chuỗi

```python
import viparse

viparse.fix("Coäng hoøa xaõ hoäi chuû nghóa")  # 'Cộng hòa xã hội chủ nghĩa'
viparse.fix("lËp", encoding="tcvn3")  # ép bảng mã, bỏ qua bước dò
viparse.detect_text_encoding("B¸o c¸o")  # 'tcvn3'  (hoặc None nếu không tìm ra)
```

### Đọc file

```python
docs = viparse.load("tai_lieu_cu.pdf")
docs = viparse.load("bang_luong.xls", output="markdown", encoding="auto")
```

`load()` nhận các tuỳ chọn theo từng lần gọi — `output` (`text` / `markdown` / `json`),
`encoding` (ép bảng mã thay vì để tự dò), `ocr`, `normalize` (mặc định NFC), `max_bytes`,
cùng `cache` và `chunk` tuỳ chọn.

`load_batch()` nhận thêm `workers` và trả về từng `list[Document]` một, nên corpus lớn
chạy theo luồng thay vì dựng hết vào bộ nhớ:

```python
from viparse import load_batch
from viparse.cache import DiskCache

for docs in load_batch(paths, output="markdown", workers=8, cache=DiskCache(".viparse-cache")):
    index(docs)
```

Việc chia chunk chạy trên cấu trúc khối của tài liệu chứ không trên văn bản phẳng, nên một
chunk không bao giờ vắt qua ranh giới mục, và một dòng bảng không bao giờ bị cắt đôi.

### Dòng lệnh

```bash
viparse ./docs/**/*.pdf -o md
viparse doctor        # liệt kê engine khả dụng theo extras đã cài
```

## Dùng từ AI agent

```bash
pip install "viparse[mcp]"
viparse-mcp                        # stdio; hoặc `python -m viparse.mcp`
```

Với Claude Desktop, Claude Code và mọi thứ nói được MCP:

```json
{ "mcpServers": { "viparse": { "command": "viparse-mcp" } } }
```

Bốn tool. `repair_garbled_vietnamese` nhận **chuỗi** chứ không nhận đường dẫn, vì phần lớn
trường hợp agent đã có sẵn đoạn chữ lỗi trong ngữ cảnh và không có file nào để trỏ tới.
`identify_vietnamese_encoding` chỉ gọi tên bảng mã mà không đổi gì, và trả kèm một đoạn xem
trước để câu trả lời của nó có thể được **kiểm chứng** thay vì phải tin.
`read_vietnamese_document` là `viparse.load` trên một đường dẫn. `viparse_version` để báo lỗi.

Nếu agent của bạn không chạy MCP, `skills/garbled-vietnamese-text/SKILL.md` là một skill
kiểu Claude bao phủ cùng nội dung: nhận diện từng bảng mã, cách chuyển, và các bẫy — đừng
bao giờ chuyển văn bản vốn đã là Unicode, tên phông không phải bằng chứng, một tài liệu có
thể chứa hai bảng mã, và việc dò cần cả một cụm từ chứ không phải bốn ký tự.

## Máy quyết định bảng mã như thế nào

Tín hiệu chính là **tên phông chữ** mà engine đọc được từ trong tài liệu: phông `.Vn*` ứng
với TCVN3, phông `VNI*` ứng với VNI. Tín hiệu này độ tin cậy cao nên bật sẵn.

Ngoài ra có một heuristic theo **tần suất ký tự** — thử chuyển rồi chấm điểm dựa trên mô
hình chữ cái tiếng Việt — nhưng nó **phải bật thủ công** (`encoding="auto"`). Một mô hình
tần suất không tách được tiếng Việt bảng mã cũ khỏi các thứ tiếng Latin nhiều dấu khác:
tiếng Tây Ban Nha và tiếng Đức đều *ăn điểm cao hơn* TCVN3 thật. Bật vô điều kiện là cách
làm hỏng những tài liệu nó không có việc gì phải đụng vào.

### Khi trả chữ về mà chưa chuyển, nó sẽ nói ra

Có hai trường hợp thật mà kết quả trả về là chữ lỗi và không gì khác báo cho bạn biết.
Bảng phông trong file RTF liệt kê những phông tài liệu **khai báo** chứ không phải phông
thực sự áp lên chữ; và một file PDF có thể nhúng phông đã cắt bớt, không lộ tên gốc. Cả
hai đều cho ra thứ trông như tiếng Việt vô nghĩa — không lỗi, không rỗng, độ dài vẫn đúng —
tức là kiểu hỏng khó phát hiện nhất.

Nên một tài liệu trả về mà chưa chuyển sẽ được chấm điểm đúng như khi bật `encoding="auto"`,
và nếu điểm đó đủ để gọi tên một bảng mã, bạn nhận được cảnh báo kèm cách sửa:

```
text looks like tcvn3 and was returned unconverted;
pass encoding="tcvn3" or encoding="auto" to convert it
```

Nó không tự chuyển gì cả, và dùng lại đúng các chốt chặn của `auto` — nên một tài liệu
tiếng Tây Ban Nha sẽ không nhận được lời khuyên làm hỏng chính nó.

## Về con số độ chính xác

[viparse-corpus](https://github.com/TrizenX/viparse-corpus) công bố **0.982** độ chính xác
dấu thanh trên 96 văn bản nhà nước Việt Nam (2002–2009) được chép tay lại, thuộc năm định
dạng thật — `.doc`, `.xls`, `.rtf`, `.pdf`, `.ppt` — so với **0.019** của chính bộ đọc đó
khi tắt phần chuyển bảng mã. Hai hàng được chấm trên đúng cùng 96 tài liệu, bằng đúng một
câu lệnh đã công bố, khác nhau đúng một tham số.

Đó là một tuyên bố **về viparse, không phải một phép so sánh**: chưa có công cụ nào khác
được chạy trên corpus đó. Muốn so trực tiếp thì phải có kết quả của họ trên đúng những file
này, và chừng nào chưa có thì phần này không nói gì về bất kỳ ai khác. Corpus, cách đo và
toàn bộ kết quả thô đều công khai để có thể tranh luận lại — kèm cả một bản ghi những chỗ
mà con số này yếu hơn vẻ ngoài của nó.

## Nguyên tắc thiết kế

**Không bao giờ tự viết parser.** Bọc các engine đang được bảo trì tốt sau những adapter
mỏng; nếu một engine dính CVE hoặc bị bỏ rơi thì thay adapter mà không đụng tới phần còn
lại. Các phụ thuộc nặng đều import lười qua extras.

Một pipeline, bốn tầng, mỗi tầng nằm sau một Protocol nên có thể thay thế và test bằng fake:

```
viparse.load("file")
    │
    ├─ route      nhận dạng định dạng từ magic bytes, chọn engine theo độ ưu tiên
    ├─ extract    Engine     → RawExtraction   (chữ thô + tín hiệu phông/bảng mã)
    ├─ normalize  Normalizer → NormalizedDoc   (bảng mã cũ → Unicode, NFC)
    └─ structure  Renderer   → Document        (text / markdown / json, + chunk)
```

Phần bảng mã nằm ở `normalize/` — đó là phần lõi giá trị của thư viện. Chi tiết kiến trúc
đầy đủ, bản đồ spec (SPEC-0 … SPEC-8) và hướng dẫn đóng góp nằm ở
[README tiếng Anh](README.md) và [`docs/specs/`](docs/specs/README.md).

## Giấy phép

[MIT](LICENSE) © 2026 Đinh Minh Trí (Kayden)
