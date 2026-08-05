# viparse

> Thư viện đọc tài liệu tiếng Việt cho RAG — xử lý bảng mã cũ TCVN3, VNI, VISCII, VPS.

[![PyPI](https://img.shields.io/pypi/v/viparse)](https://pypi.org/project/viparse/)
[![Python](https://img.shields.io/pypi/pyversions/viparse)](https://pypi.org/project/viparse/)
[![License](https://img.shields.io/pypi/l/viparse)](LICENSE)

**English:** [README.md](README.md) · **Trang chủ:** [viparse.trizenx.com](https://viparse.trizenx.com)

Một lệnh để biến tài liệu tiếng Việt bất kỳ — kể cả file dùng **phông chữ cũ** `.VnTime`,
`VNI-Times`, file `.doc` / `.xls` / `.ppt` đời cũ, PDF scan hay ảnh chụp — thành Unicode **dựng sẵn (NFC)**
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
pip install "viparse[ocr]"         # PDF scan và file ảnh (cần cài Tesseract)
pip install "viparse[langchain]"   # loader cho LangChain
pip install "viparse[llamaindex]"  # reader cho LlamaIndex
pip install "viparse[mcp]"         # MCP server, cho AI agent
pip install "viparse[all]"         # mọi engine và adapter
```

`mcp` cố ý **không** nằm trong `all`: `all` nói về khả năng đọc file, và việc cài đủ bộ đọc
không nên kéo theo một server runtime.

Hai phần tích hợp framework cũng được xuất bản dưới tên riêng, dành cho người đang tìm từ
phía bên kia chứ không phải từ phía này:

```bash
pip install viparse-langchain      # vẫn là VietnameseDocumentLoader
pip install viparse-llamaindex     # vẫn là ViparseReader
```

Chúng không chứa dòng code nào của riêng mình. Cả hai framework đều đã ngừng nhận tích hợp
của bên thứ ba vào repo của họ, nên một gói mà **cái tên** có chữ LangChain hoặc LlamaIndex
là cách duy nhất còn lại để xuất hiện ở chỗ những người đó tìm.

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
chunk không bao giờ vắt qua ranh giới mục, một dòng bảng không bao giờ bị cắt đôi, và
chunk nào tiếp nối một bảng thì được lặp lại dòng tiêu đề của bảng đó. Riêng PDF thì
không có mục nào để bám vào — xem [Những gì nó không làm](#những-gì-nó-không-làm).

### Cắm vào LangChain / LlamaIndex

```python
from viparse.integrations import VietnameseDocumentLoader, ViparseReader

docs = VietnameseDocumentLoader("bao_cao_cu.doc").load()
documents = ViparseReader().load_data("bao_cao_cu.doc")
```

Có sẵn trong `viparse[langchain]` / `viparse[llamaindex]`, hoặc cài riêng bằng
[`viparse-langchain`](https://pypi.org/project/viparse-langchain/) /
[`viparse-llamaindex`](https://pypi.org/project/viparse-llamaindex/) — cùng một lớp, dưới
cái tên mà người dùng framework tìm ra được.

Đây là loader hạng nhất theo đúng hình dạng mà pipeline của hai framework được viết
quanh, chứ không phải hàm chuyển đổi gọi sau. Khác biệt đó quan trọng hơn vẻ ngoài: một
hàm chuyển đổi chỉ tới tay người **đã đi tìm viparse**, còn một loader thì tới tay người
đang viết pipeline và cần đọc đúng một tài liệu tiếng Việt.

Cả hai nhận đúng các tuỳ chọn của `load()` và đều chạy theo luồng. Nếu đã có sẵn một
`Document` của viparse, hai hàm chuyển đổi bên dưới cũng là API công khai:

```python
from viparse.integrations import to_langchain_documents, to_llamaindex_documents
```

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

[viparse-corpus](https://github.com/TrizenX/viparse-corpus) công bố **0.986** độ chính xác
dấu thanh trên 96 văn bản nhà nước Việt Nam (2002–2009) được chép tay lại, thuộc năm định
dạng thật — `.doc`, `.xls`, `.rtf`, `.pdf`, `.ppt` — so với **0.019** của chính bộ đọc đó
khi tắt phần chuyển bảng mã. Hai hàng được chấm trên đúng cùng 96 tài liệu, bằng đúng một
câu lệnh đã công bố, khác nhau đúng một tham số.

Đó là một tuyên bố **về viparse, không phải một phép so sánh**: chưa có công cụ nào khác
được chạy trên corpus đó. Muốn so trực tiếp thì phải có kết quả của họ trên đúng những file
này, và chừng nào chưa có thì phần này không nói gì về bất kỳ ai khác. Corpus, cách đo và
toàn bộ kết quả thô đều công khai để có thể tranh luận lại — kèm cả một bản ghi những chỗ
mà con số này yếu hơn vẻ ngoài của nó.

## Những gì nó không làm

viparse cũng được đo trên tài liệu Unicode bình thường chứ không chỉ trên corpus mã cũ.
[Benchmark cấu trúc](https://github.com/TrizenX/viparse-corpus/tree/main/structure) cắm
các đoạn văn, tiêu đề và bảng có nhãn vào file `.docx` / `.xlsx` / `.pptx` / PDF rồi đếm
xem lấy lại được gì.

| tài liệu | thứ tự | đầy đủ | tiêu đề |
| --- | ---: | ---: | ---: |
| `.docx`, `.xlsx`, `.pptx` | **1.000** | 1.000 | **1.000** |
| PDF một cột | **1.000** | 1.000 | **0.000** |
| PDF hai cột | **0.600** | 1.000 | **0.000** |

Không bao giờ mất chữ — cột "đầy đủ" bằng 1.000 ở mọi nơi. Cả hai chỗ hỏng đều là hỏng
về **sắp xếp**, loại khó phát hiện hơn hẳn: chữ vẫn còn đủ, vẫn trôi chảy, và sai.

**PDF không có tiêu đề.** viparse không suy ra tiêu đề từ cỡ chữ, nên mọi tiêu đề trong
PDF ra thành đoạn văn thường và mọi chunk từ PDF đều có `section` rỗng. Chia chunk theo
mục là thật với `.docx`, `.xlsx`, `.pptx`; với PDF thì đó chỉ là cắt theo kích thước.

**PDF nhiều cột bị đọc ngang trang chứ không đọc dọc theo cột** — đoạn 1 rồi đến đoạn 19.
Muốn lấy lại đúng cột thì phải dò cột, tức là phân tích bố cục, và viparse cố ý không làm
phân tích bố cục. Với PDF nhiều cột, hãy dùng một bộ đọc hiểu bố cục — **Unstructured**,
**docling**, **LlamaParse** — rồi đưa kết quả của nó qua `viparse.fix()`. Đó mới là cách
ghép đúng ý đồ: họ biết chữ nằm ở đâu, viparse biết những byte đó nghĩa là gì.

**Hoàn toàn không đụng tới:** hình minh hoạ và biểu đồ nhúng, công thức, thứ tự đọc của
bố cục xoay hoặc tự do, và chữ viết tay.

**OCR đã được đo.** `viparse[ocr]` đọc được PDF scan và file ảnh (`.png` / `.jpg` / `.tif`,
kể cả TIFF nhiều trang). Đo trên
[corpus](https://github.com/TrizenX/viparse-corpus/tree/main/ocr):

| đối tượng | số tài liệu | **dấu thanh** |
| --- | ---: | ---: |
| **bản scan thật** | **3** | **0.973** |
| trang kết xuất | 96 | **0.990** |
| đường chuyển bảng mã, để so | 96 | **0.986** |

Ba bản scan là **mức sàn cho các con số kết xuất, không phải một benchmark** — cả ba đều là
một trang, được chép tay từ ảnh **trước khi** chạy OCR. Khoảng cách 0.973 so với 0.990 là
cái giá xấp xỉ của một trang thật. Hàng này sẽ đổi khi có thêm bản được chép; corpus giữ
con số hiện hành.

Lỗi còn lại gần như toàn bộ nằm ở dấu thanh, theo cả hai chiều — thêm dấu hỏi vào chữ `i`,
làm rơi dấu khỏi `ề`/`ầ`/`ồ` — tức đúng vào thứ sản phẩm này sinh ra để giữ.

Bản trước của mục này gọi OCR là phần yếu nhất và ghi 0.967 / 0.898. Những con số đó đến
từ một lỗi trong bộ chấm điểm của corpus, không phải từ viparse, và đã được rút lại.

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
