# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Trần Ngọc Sơn]
**Nhóm:** [E5]
**Ngày:** [10/04/2026]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai đoạn văn bản có cosine similarity cao nghĩa là vector embedding của chúng gần nhau trong không gian nhiều chiều. Ví dụ, hai câu nói về cùng một chủ đề hoặc diễn đạt cùng một ý tưởng sẽ có cosine similarity gần 1.

**Ví dụ HIGH similarity:**
- Sentence A: "The cat sat on the mat."
- Sentence B: "A cat was sitting on a mat."
- Tại sao tương đồng: Hai câu mô tả cùng một sự kiện (con mèo ngồi trên thảm), dùng từ vựng và cấu trúc rất giống nhau nên embedding của chúng sẽ gần nhau về hướng.

**Ví dụ LOW similarity:**
- Sentence A: "The cat sat on the mat."
- Sentence B: "WORLD WAR III IS COMINGGG"
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau (động vật vs. chiến tranh), không chia sẻ bất kỳ khái niệm hay từ ngữ nào liên quan nên embedding của chúng sẽ trỏ theo hướng hoàn toàn khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector, bỏ qua độ lớn (magnitude), nên nó không bị ảnh hưởng bởi độ dài văn bản — một đoạn văn dài và đoạn tóm tắt ngắn cùng chủ đề vẫn có similarity cao. Ngược lại, Euclidean distance phụ thuộc vào độ lớn của vector, khiến các văn bản dài tự nhiên có khoảng cách xa hơn dù nghĩa gần nhau.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Áp dụng công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
>
> `num_chunks = ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.11) = **23 chunks**`

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Với overlap=100: `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = ceil(24.75) = **25 chunks**` — tức tăng thêm 2 chunks. Overlap nhiều hơn giúp đảm bảo các câu hoặc ý tưởng nằm ở ranh giới giữa hai chunk không bị mất ngữ cảnh, cải thiện chất lượng retrieval cho các truy vấn liên quan đến nội dung ở vùng chuyển tiếp giữa các chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [Tài liệu bói toán]

**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:* Domain lạ, tìm được tài liệu đạt yêu cầu, xác định được câu hỏi và trả lời làm ground truth

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 |Tử vi đẩu số tân biên |https://drive.google.com/file/d/1DTBH6jhq0ia_RenD3my6LDQdv0Bk_HQO/edit?fbclid=IwY2xjawRFgxBleHRuA2FlbQIxMABicmlkETF2Rkt4UlVBZjFGWW5tOWFxc3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHlzYdm64HUDC9ciLL_NPBp-u0xjvLPJBIn2RTxi2hPQ2KH0Em0bwvZHSOhY6_aem__0NJhHXdZdtRnGFPlVHYBw |36904 |? |




## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu `data/data.md` với `chunk_size=200`:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| data.md | FixedSizeChunker (`fixed_size`) | 14 | 199.81 | Yes |
| data.md | SentenceChunker (`by_sentences`) | 10 | 283.48 | Yes |



### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> RecursiveChunker tách văn bản theo thứ tự ưu tiên separator: đoạn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), và cuối cùng là tách cứng theo ký tự nếu cần. Thuật toán đệ quy để tiếp tục tách khi một đoạn vẫn lớn hơn `chunk_size`, nhờ đó chunk cuối cùng ít vượt ngưỡng hơn. Với dữ liệu dài và nhiều tiêu đề/mục như `data.md`, cách này giữ cấu trúc tự nhiên tốt hơn cắt cứng theo vị trí ký tự. Kết quả chunk thường có tính mạch lạc cao và vẫn đủ gọn để embedding.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain bói toán có nhiều phần mục, tiêu đề, đoạn giải nghĩa dài-ngắn không đều, nên tách theo cấu trúc văn bản sẽ hợp lý hơn tách cố định. RecursiveChunker tận dụng đúng pattern này: ưu tiên ngắt ở ranh giới ngữ nghĩa trước khi ngắt kỹ thuật. Nhờ vậy, chunk trả về khi retrieval thường dễ đọc và sát ý hơn khi trả lời câu hỏi nghiệp vụ.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| data.md | best baseline: FixedSizeChunker | 14 | 199.81 | Medium |
| data.md | **của tôi: RecursiveChunker** | 25 | 133.89 | High |



### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | RecursiveChunker | 9 | Giữ ngữ cảnh theo cấu trúc tài liệu, chunk mạch lạc | Cần tuning `chunk_size` cho từng bộ dữ liệu |
| Dũng |SentenceChunker |7.0 |Giữ ngữ cảnh tốt, xử lý văn bản phức tạp | |
| Huy | FixedSizeChunker | 7.5 | Đơn giản, ổn định, dễ kiểm soát kích thước chunk | Dễ cắt ngang ý, mất ngữ cảnh ở đoạn dài |
| Đăng | SentenceChunker | 7.0 | Tạo chunk tự nhiên, dễ đọc | Chunk có thể quá dài hoặc quá ngắn tùy câu |
| Tuấn |  RecursiveChunker | 8.0 | Tối ưu theo domain, cân bằng giữa context và size | Cần tinh chỉnh nhiều, khó triển khai hơn baseline |
| Đạt |RecursiveChunker |7.5 |Giữ ngữ cảnh tốt, chunk rõ nghĩa | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Với bộ tài liệu hiện tại, RecursiveChunker là lựa chọn tốt nhất vì dữ liệu có nhiều đoạn dài, tiêu đề và cấu trúc phân mục rõ ràng. Strategy này giúp cắt theo ranh giới ngữ nghĩa thay vì cắt cơ học, nên chất lượng chunk ổn định hơn cho retrieval. Trong các thử nghiệm baseline, nó giữ được cân bằng tốt giữa độ dài chunk và tính liên kết nội dung.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Em dùng regex để tách câu dựa trên dấu chấm, chấm hỏi, chấm than và trường hợp dấu chấm xuống dòng. Sau khi split, em loại bỏ các phần rỗng và `strip()` từng câu để tránh lỗi do khoảng trắng thừa ở đầu hoặc cuối. Cuối cùng, các câu được gom lại thành từng chunk theo `max_sentences_per_chunk` bằng cách nối các câu liền nhau.

**`RecursiveChunker.chunk` / `_split`** — approach:
> `RecursiveChunker` thử tách văn bản theo thứ tự separator ưu tiên: đoạn, dòng, câu, từ, rồi mới đến ký tự. Nếu một phần vẫn còn dài hơn `chunk_size`, hàm `_split` sẽ đệ quy với separator tiếp theo để tạo ra các mảnh nhỏ hơn nhưng vẫn cố giữ cấu trúc tự nhiên của văn bản. Base case là khi đoạn hiện tại đã ngắn hơn hoặc bằng `chunk_size`, hoặc không còn separator nào để thử nữa; lúc đó hàm trả về trực tiếp chunk đã được `strip()`.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Khi thêm tài liệu, em tạo embedding cho `content` của từng `Document` rồi lưu lại dưới dạng record gồm `id`, `content`, `embedding` và `metadata`. Với chế độ in-memory, hàm `search` tạo embedding cho query rồi tính độ tương đồng bằng dot product giữa vector query và vector của từng record. Sau đó, kết quả được sắp xếp giảm dần theo `score` và cắt theo `top_k`.

**`search_with_filter` + `delete_document`** — approach:
> Với `search_with_filter`, em lọc record theo `metadata_filter` trước, sau đó mới chạy similarity search trên tập ứng viên đã được thu hẹp. Cách này giúp đảm bảo kết quả đúng điều kiện metadata ngay từ đầu thay vì lọc sau khi đã xếp hạng. Với `delete_document`, em xóa tất cả record có `id` trùng với `doc_id`, rồi trả về `True` nếu số lượng phần tử giảm xuống và `False` nếu không có gì bị xóa.

### KnowledgeBaseAgent

**`answer`** — approach:
> Hàm `answer` trước hết gọi `store.search()` để lấy ra các chunk liên quan nhất đến câu hỏi. Sau đó em ghép nội dung các chunk này thành một phần `Context`, ngăn cách nhau bằng `---`, rồi tạo prompt theo cấu trúc: context trước, question sau, cuối cùng là `Answer:` để LLM hoàn tất. Cách inject context này giúp mô hình luôn nhìn thấy bằng chứng retrieval trước khi sinh câu trả lời.

### Test Results

```

============================= 42 passed in 0.17s 
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 |Reading books is fun | i love reading novel| high |0.95 | True |
| 2 |My favorite color is blue |I prefer red over blue | high |0.7 |True |
| 3 |My sister is very generous. | My brother is very kind. | high  |0.5 |True |
| 4 | I study programming languages.   | I am learning Python.   | high  |0.85 | True|
| 5 |Wie heist du | what is your name | high |0.04| False|

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
Case cuối bất ngờ nhất vì đó là 2 câu chung nghĩa nhưng ở 2 ngôn ngữ khác nhau, tuy vậy theo hash text thì nó sẽ không liên quan.
---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Trong lý giải về Ngũ hành, quy luật Tương sinh diễn ra như thế nào|Quy luật Tương sinh giữa các hành bao gồm: *Kim sinh Thủy, Thủy sinh Mộc, Mộc sinh Hỏa, Hỏa sinh Thổ, và Thổ sinh Kim*. Ngược lại, quy luật Tương khắc là: Kim khắc Mộc, Mộc khắc Thổ, Thổ khắc Thủy, Thủy khắc Hỏa, và Hỏa khắc Kim |
| 2 |Làm thế nào để tìm được Bản Mệnh thuộc hành nào trong Ngũ hành? |Để tìm Bản Mệnh, người xem số cần rõ tuổi của mình ở hai hàng *Can và Chi*, sau đó tra bảng để xác định mình thuộc hành nào trong Ngũ hành (Kim, Mộc, Thủy, Hỏa, Thổ). Có tất cả *Thập Thiên Can* (Giáp, Ất, Bính, Đinh, Mậu, Kỷ, Canh, Tân, Nhâm, Qúy) phối hợp với các Địa chi. |
| 3 |Quy tắc đổi giờ đồng hồ sang giờ hàng Chi trong Tử Vi là gì? |Một ngày có 24 giờ đồng hồ và cứ *hai giờ đồng hồ tương ứng với một giờ hàng Chi*. Ví dụ: giờ Tý bắt đầu từ 23 giờ đến 1 giờ sáng, giờ Sửu từ 1 giờ đến 3 giờ sáng, và tiếp tục như vậy cho đến hết 12 ch |
| 4 |Chùm sao thuộc Tử Vi tinh hệ bao gồm những sao nào? |Chùm sao này gồm có 5 sao: *Tử Vi, Liêm Trinh, Thiên Đồng, Vũ Khúc và Thiên Cơ*. Việc an các sao này dựa trên Cục và ngày sinh của mỗi ngườ |
| 5 |Một lá số Tử Vi được chia làm bao nhiêu ô và tên gọi của các ô này dựa trên quy tắc nào? |Lá số được chia làm *12 ô*, mỗi ô gọi là một cung. Tên riêng của mỗi cung được gọi theo *Thập Nhị Địa Chi*, bao gồm: Tý, Sửu, Dần, Mão, Thìn, Tỵ, Ngọ, Mùi, Thân, Dậu, Tuất, Hợi. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Trong lý giải về Ngũ hành, quy luật Tương sinh diễn ra như thế nào |**Kim sinh Thủy**: Kim loại (như vàng, bạc) khi được nung chảy sẽ tạo thành chất lỏng, tượng trưng cho nước (Thủy). **Hỏa sinh Thổ**: Lửa (Hỏa) khi đốt cháy chất hữu cơ sẽ tạo ra tro, là phần đất (Thổ). **Thủy sinh Mộc**: Nước (Thủy) giúp cho cây cối (Mộc) phát triển và sinh trưởng.**Thổ sinh Kim**: Đất (Thổ) chứa khoáng sản, từ đó hình thành các kim loại (Kim). **Mộc sinh Hỏa**: Cây cối (Mộc) khi bị đốt sẽ cháy tạo thành lửa (Hỏa). | 0.48 | Có | Agent trả lời đúng 5 cặp Tương sinh và bổ sung 5 cặp Tương khắc theo đúng nội dung tài liệu |
| 2 | Làm thế nào để tìm được Bản Mệnh thuộc hành nào trong Ngũ hành? | Chunk trả ra tra cứu Ngũ Hành của Thiên Can, tra cứu Ngũ Hành của Địa Chỉ | 0.46 | Có | Agent trả lời đúng quy trình xác định Bản Mệnh: xác định Can-Chi, tra bảng, suy ra hành tương ứng |
| 3 | Quy tắc đổi giờ đồng hồ sang giờ hàng Chi trong Tử Vi là gì? | Một ngày có 24 giờ đồng hồ, và mỗi giờ hàng Chi tương ứng với 2 giờ đồng hồ. Sau đó có bảng tra cứu | 0.50 | Có | Agent trả lời đúng nguyên tắc đổi giờ |
| 4 | Chùm sao thuộc Tử Vi tinh hệ bao gồm những sao nào? | Chùm sao thuộc Tử Vi tinh hệ bao gồm các sao: Tử Vi, Liêm Trinh, Thiên Đồng, Vũ Khúc và Thiên Cơ. | 0.57 | Có | Agent liệt kê đúng 5 sao trong chùm Tử Vi tinh hệ |
| 5 | Một lá số Tử Vi được chia làm bao nhiêu ô và tên gọi của các ô này dựa trên quy tắc nào? | Một lá số Tử Vi được chia làm 12 ô, tương ứng với 12 cung. Tên gọi của các ô này dựa trên quy tắc của Thập Nhị Địa Chi, bao gồm các cung: Tý, Sửu, Dần, Mão, Thìn, Tỵ, Ngọ, Mùi, Thân, Dậu, Tuất, Hợi. Các cung được sắp xếp theo chiều thuận kim đồng hồ bắt đầu từ cung Tý. Vị trí và tên của mỗi cung không bao giờ thay đổi. | 0.55 | Có | Agent trả lời đúng số lượng 12 cung và quy tắc đặt tên theo Thập Nhị Địa Chi |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5/ 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Chủ yếu là bọn em hỗ trợ nhau trong việc tìm embedding, còn lại thì các strategy của thành viên trong nhóm đều khá cơ bản*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *?*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> * "Thay đổi" thì em chưa nghĩ ra, nhưng em nghĩ có thể sẽ tìm hiểu sâu hơn về việc có thể đưa ra kích thước chunk phù hợp tùy vào văn bản đầu vào*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5/ 5 |
| Document selection | Nhóm | 10/ 10 |
| Chunking strategy | Nhóm |13 / 15 |
| My approach | Cá nhân | 10/ 10 |
| Similarity predictions | Cá nhân | 5/ 5 |
| Results | Cá nhân |10 / 10 |
| Core implementation (tests) | Cá nhân | 30/ 30 |
| Demo | Nhóm | 4/ 5 |
| **Tổng** | | **87/ 90** |
