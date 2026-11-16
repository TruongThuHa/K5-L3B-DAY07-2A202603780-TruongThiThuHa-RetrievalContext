# Chấm thử thách nâng cao · dev · text_only

## ad01 · table · ✅ ĐẠT

- Câu hỏi: According to Table 3, how many universities from the United Kingdom are in the QS top 1,000?
- Đáp án chuẩn: 76
- Tiêu chí: Phải là 76 (cột QS, hàng United Kingdom); 80 (Webometrics) hay 92 (THE) là sai
- Evidence gốc: tr. 43 · Table 3: Global University Rankings for Vietnam and Comparators · hàng United Kingdom × cột No. of Universities in the Top 1,000 QS
- Agent (answered, 1 lần search): According to Table 3, there are 76 universities from the United Kingdom in the QS top 1,000 [he2020-p043-B03].
- Trích `he2020-p043-B03` (trang 43): “No. of Universities in Top 1,000 Webometrics No. of Universities in the Top 1,000 QS No. of Universities in the Top 1,000 THE Denmark 6 5 7 Finland 10 10 8 France 40 35 32 Germany 60 45 47 Netherlands 13 13 13 Poland 11 14 5 Switzerland 11 9 10 United Kingdom …”
- Lý do: 76; text trang 43 có bảng dạng chữ

## ad02 · table · ✅ ĐẠT

- Câu hỏi: In Table 9, what was higher education spending as a percentage of GDP in 2011?
- Đáp án chuẩn: 0.24 percent of GDP
- Tiêu chí: 0,24 (hàng % HE/GDP, cột 2011); 0,34 là tertiary nên sai
- Evidence gốc: tr. 58 · Table 9: Spending on Tertiary and Higher Education as % of GDP · hàng % HE/GDP (khối Higher education) × cột 2011
- Agent (answered, 1 lần search): According to Table 9, higher education spending as a percentage of GDP (% HE/GDP) was 0.24 percent in 2011 [he2020-p058-B01, he2020-p058-B02]. [he2020-p058-B02] [he2020-p058-B01]
- Trích `he2020-p058-B02` (trang 58): “% Tertiary/GDP 0.45 0.34 0.33 % Tertiary/TGE 1.57 1.21 1.10 % Tertiary/TGEd 9.18 6.91 6.07 Higher education % HE/GDP 0.33 0.24 0.24 % HE/TGE 1.16 0.83 0.80 % HE/TGEd 6.80 4.76 4.41 Source: Authors’ estimates using MOF data for 2011 and 2015 and Education and S…”
- Trích `he2020-p058-B01` (trang 58): “In Vietnam, the concept has been emphasized several times in legal documents such as University Charters (2003 and 2014) and the Law on Higher Education 2012 under various terminologies such as ‘responsibility’ , ‘self-responsibility’ , or ‘social responsibili…”
- Lý do: 0,24; text trang 58

## ad03 · table · ❌ KHÔNG ĐẠT

- Câu hỏi: According to Table 13, how many researchers work in universities in Vietnam?
- Đáp án chuẩn: 65,628 researchers
- Tiêu chí: 65.628 (hàng Universities, cột Researchers, khối Human Resources)
- Evidence gốc: tr. 62 · Table 13: Disconnect between R&D Funding and R&D Human Resource · khối Human Resources, hàng Universities × cột Researchers
- Agent (abstain, 3 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối sau 3 lần tìm: không đưa được ô Universities × Researchers (Table 13) vào context

## ad04 · table · ❌ KHÔNG ĐẠT

- Câu hỏi: Which research funding modalities are only partially available in Vietnam according to Table 17?
- Đáp án chuẩn: Competitive research grants (Yes/partially) and centers of excellence/chairs of excellence (Partially)
- Tiêu chí: Đủ cả 2 modality; thiếu 1 là không đạt
- Evidence gốc: tr. 79 · Table 17: Allocation of Research Funding in Vietnam · cột Availability in Vietnam = Partially / Yes/partially
- Agent (answered, 3 lần search): According to Table 17, the research funding modality that is partially available ("Yes/partially") in Vietnam is competitive research grants [he2020-p079-B02].
- Trích `he2020-p079-B02` (trang 79): “Table 17, which analyzes how Vietnam compares internationally in terms of research allocation mechanisms, shows that it uses mainly competitive research grants. If the government is willing and able to substantially increase research funding, it could consider…”
- Lý do: Chỉ nêu 1/2 modality (thiếu Centers of excellence)

## ad05 · image · ✅ ĐẠT

- Câu hỏi: What are the three higher education outcomes shown in the report's analytical framework (Figure 2)?
- Đáp án chuẩn: Research and Innovation; Skills; Coverage and Equity
- Tiêu chí: Đủ 3 ô hàng 'HE Outcomes'
- Evidence gốc: tr. 34 · Figure 2: Higher Education Analytical/Conceptual Framework · hàng giữa có nhãn 'HE Outcomes'
- Agent (answered, 3 lần search): In the report's analytical framework (Figure 2), the three higher education outcomes (HE Outcomes) are Coverage and Equity, Skills, and Research and Innovation. [he2020-p034-B02]
- Trích `he2020-p034-B02` (trang 34): “Figure 2: Higher Education Analytical/Conceptual Framework Growth Shared Prosperity Coverage and EquitySkills Research and Innovation HE Outcomes Higher Level Goals Enhanced Governance Government as steward (sets vision and goals, coordinates, supervises, moni…”
- Lý do: Đủ 3 HE outcomes (chữ trong sơ đồ có trong text pypdf)

## ad06 · image · ❌ KHÔNG ĐẠT

- Câu hỏi: Which units of assessment are listed across the top of Figure 11 on the Vietnamese HE QA system?
- Đáp án chuẩn: Higher education institution, Program, Student, and External quality assurance agency
- Tiêu chí: Đủ 4 đơn vị
- Evidence gốc: tr. 56 · Figure 11: Functions and Units of Measure in the Vietnamese HE QA System · hàng tiêu đề 'UNITS OF ASSESSMENT'
- Agent (abstain, 3 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối sau 3 lần tìm: text pypdf của sơ đồ Figure 11 không đủ để agent xác định hàng tiêu đề

## ad07 · image · ✅ ĐẠT

- Câu hỏi: In Figure 14, what are the three technology functions shown as grey ovals?
- Đáp án chuẩn: Technology adoption, technology transfer, and technology generation
- Tiêu chí: Đủ 3 chức năng
- Evidence gốc: tr. 80 · Figure 14: Instruments for Building Firms' Technology Capabilities · 3 hình oval xám ở giữa
- Agent (answered, 3 lần search): In Figure 14, the three technology functions shown are "Technology generation," "Technology transfer," and "Technology adotion" (technology adoption) [he2020-p080-B00].
- Trích `he2020-p080-B00` (trang 80): “Improving the Performance of Higher Education in Vietnam 68 assist with innovation projects, (d) industrial training opportunities for master’s and doctoral students, and (e) mutual board membership opportunities whereby universities invite industry members an…”
- Lý do: Đủ 3 chức năng; text trang 80 có chữ trong sơ đồ

## ad08 · chart · ✅ ĐẠT

- Câu hỏi: In Figure ES.3, which two countries have public expenditure on tertiary education of exactly 1.00 percent of GDP?
- Đáp án chuẩn: Republic of Korea and Singapore
- Tiêu chí: Đủ 2 nước
- Evidence gốc: tr. 20 · Figure ES.3: Public Expenditure on Tertiary Education, as % of GDP (2016) · cột Rep. of Korea và Singapore, nhãn 1.00
- Agent (answered, 1 lần search): According to Figure ES.3, the two countries with public expenditure on tertiary education of exactly 1.00 percent of GDP are the Republic of Korea (Rep. of Korea) and Singapore [he2020-p020-B00].
- Trích `he2020-p020-B00` (trang 20): “Improving the Performance of Higher Education in Vietnam 8 except for the two national universities which receive it directly from MOF. Per student public funding also widely varies across ministries without any rational link to actual costs. Figure ES.3: Publ…”
- Lý do: Đúng 2 nước; nhãn số biểu đồ có trong text trang 20

## ad09 · chart · ✅ ĐẠT

- Câu hỏi: According to Figure 10, what was Switzerland's GERD as a percentage of GDP in 2015?
- Đáp án chuẩn: 3.4 percent
- Tiêu chí: 3,4
- Evidence gốc: tr. 51 · Figure 10: GERD as a Percentage of GDP in 2015 · cột Switzerland, nhãn 3.4
- Agent (answered, 3 lần search): According to Figure 10, Switzerland's gross expenditure for research and development (GERD) as a percentage of GDP in 2015 was 3.4 percent [he2020-p051-B04].
- Trích `he2020-p051-B04` (trang 51): “The limited resources in support of research and technology transfer in universities are spread too thin, do not always promote performance, and are not always aligned with national and local priorities. Figure 10: GERD as a Percentage of GDP in 2015 1.9 2.1 3…”
- Lý do: 3,4; nhãn số có trong text trang 51

## ad10 · chart · ❌ KHÔNG ĐẠT

- Câu hỏi: In Figure 7 (decomposition of access gaps, 2018), which group comparison shows the smallest access gap?
- Đáp án chuẩn: Female - Male (about 13 percentage points)
- Tiêu chí: Female - Male; giá trị ≈13 nếu có thì phải trong khoảng 12–14
- Evidence gốc: tr. 41 · Figure 7: Decomposition of Access Gaps in Tertiary Education, 2018 · cột Female - Male (thấp nhất)
- Agent (abstain, 3 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối: biểu đồ không nhãn số, text không có giá trị

## ad11 · chart · ❌ KHÔNG ĐẠT

- Câu hỏi: In Figure 3, which country's tertiary gross enrolment ratio rose above 100 percent?
- Đáp án chuẩn: Republic of Korea
- Tiêu chí: Republic of Korea (đường nét đứt xanh, ≈2007–2011)
- Evidence gốc: tr. 37 · Figure 3: Tertiary Education GER in Vietnam and Selected Countries, 2000–2016 · đường Republic of Korea, đỉnh ≈104
- Agent (abstain, 3 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối: biểu đồ đường không có nhãn số

## ad12 · multihop · ❌ KHÔNG ĐẠT

- Câu hỏi: What was Thailand's GERD as a percentage of GDP in 2015 (Figure 10), and how many patents per million population did Thailand have (Table 5)?
- Đáp án chuẩn: GERD 0.6 percent of GDP; 3.16 patents per million population
- Tiêu chí: Cả 2 giá trị đúng
- Evidence gốc: tr. 51 · Figure 10: GERD as a Percentage of GDP in 2015 · cột Thailand; tr. 50 · Table 5: Research and Innovation Capacity and Output · hàng Thailand × cột No. of Patents per Million Population
- Agent (answered, 3 lần search): ```json
{
 "thought": "Thailand's GERD as a percentage of GDP in 2015 was 0.6 percent (Figure 10), and Thailand had 3.16 patents per million population (Table 5).",
 "call": "default_api:final_answer",
 "args": {
  "answer": "In 2015, Thailand's GERD as a percentage of GDP was 0.6 percent [he2020-p051-B02, he2020-p051-B04]. According to Table 5, Thailand had 3.16 patents per million population [he2020-p051-B00].",
  "citations": [
   "he2020-p051-B00",
   "he2020-p051-B02",
   "he2020-p051-B04"
  ]
 }
}
``` [he2020-p051-B04] [he2020-p051-B02]
- Trích `he2020-p051-B04` (trang 51): “The limited resources in support of research and technology transfer in universities are spread too thin, do not always promote performance, and are not always aligned with national and local priorities. Figure 10: GERD as a Percentage of GDP in 2015 1.9 2.1 3…”
- Trích `he2020-p051-B02` (trang 51): “Vietnam’s research does not receive adequate funding. In terms of investment, as measured by gross expenditure for research and development (GERD) as a percentage of total GDP (Figure 9), Vietnam (0.4 percent of GDP) spends less than Thailand (0.6 percent) and…”
- Trích `he2020-p051-B00` (trang 51): “39 Diagnosis of the Vietnamese Higher Education System Measures of technology transfer capture the contribution of Vietnam’s universities to the national innovation system. Table 5 shows the patents per million inhabitants in Vietnam and comparator countries. …”
- Lý do: Nội dung đúng nhưng câu trả lời lộ JSON tool call (lỗi định dạng), không chấm đạt

## ad13 · multihop · ❌ KHÔNG ĐẠT

- Câu hỏi: By how many students would total tertiary enrolment in 2030 (Table 14) exceed total tertiary enrolment in 2016 (Table 1)?
- Đáp án chuẩn: About 1.28 million (3,584,647 in 2030 minus about 2,308 thousand in 2016)
- Tiêu chí: ≈1,28 triệu (chấp nhận 1,27–1,29 triệu) và nêu 2 số gốc
- Evidence gốc: tr. 68 · Table 14: Simulation on Additional Students by 2030 by Type of TEIs · hàng All × cột Total Enrolment in 2030; tr. 38 · Table 1: Enrolment in Tertiary Education, by Institution · hàng Total × cột Enrolment (thousands) 2016
- Agent (abstain, 3 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối sau 3 lần tìm: không có đủ cả hai tổng (Table 14 và Table 1) trong context

## ad14 · text · ❌ KHÔNG ĐẠT

- Câu hỏi: Roughly how many government research institutes (GRIs) are there in Vietnam?
- Đáp án chuẩn: More than 600
- Tiêu chí: More than 600
- Evidence gốc: tr. 51 · đoạn văn · đoạn 'The low level of R&D expenditure allocation...'
- Agent (answered, 3 lần search): There are several hundred government research institutes (GRIs) in Vietnam [he2020-p018-B03].
- Trích `he2020-p018-B03` (trang 18): “A further element of complication is the existence of several hundred GRIs, in most cases operating independently from the universities, resulting in ineffective and inefficient use of human and financial resources in both types of institutions.…”
- Lý do: Sai: 'several hundred' thay vì 'more than 600', trích trang 18 không có số này

## ad15 · text · ✅ ĐẠT

- Câu hỏi: What was the total revenue of the public universities in the 2017 MOET survey sample?
- Đáp án chuẩn: US$1,124 million
- Tiêu chí: US$1.124 triệu
- Evidence gốc: tr. 60 · chú thích 15 · chân trang
- Agent (answered, 1 lần search): In 2017, the total revenue for public universities in the MOET survey sample was US$1,124 million [he2020-p060-B02].
- Trích `he2020-p060-B02` (trang 60): “Figure 12: Evolution of Sources of Revenue of Public Universities, 2004 and 2017 68 26 6 22 55 23 0 10 20 30 40 50 60 70 80 State Subsidy Tuition RDI, services, others etc. 2004 2017 Source: Authors’ calculations using MOET University Surveys (2004 and 2017). …”
- Lý do: US$1.124 triệu

## ad16 · unanswerable · ✅ ĐẠT

- Câu hỏi: What was the student/lecturer ratio at VNU-Hanoi in 2015?
- Đáp án chuẩn: (không có trong tài liệu -> phải từ chối)
- Tiêu chí: từ chối, không bịa
- Evidence gốc: Table 7 (tr. 54) chỉ có tỷ lệ toàn hệ thống (23); không có số riêng của VNU-Hanoi. Tìm 'VNU-Hanoi', 'lecturer', 'ratio'.
- Agent (abstain, 3 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối đúng

## ad17 · unanswerable · ✅ ĐẠT

- Câu hỏi: What was Vietnam's rank in the 2023 Global Innovation Index?
- Đáp án chuẩn: (không có trong tài liệu -> phải từ chối)
- Tiêu chí: từ chối, không bịa
- Evidence gốc: Table 5 (tr. 50) và text tr. 51 chỉ có 2008 (64) và 2018 (45).
- Agent (abstain, 2 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối đúng

## ad18 · unanswerable · ✅ ĐẠT

- Câu hỏi: How much did MOET spend on IT infrastructure for e-learning in 2019?
- Đáp án chuẩn: (không có trong tài liệu -> phải từ chối)
- Tiêu chí: từ chối, không bịa
- Evidence gốc: Báo cáo chỉ khuyến nghị phát triển nền tảng e-learning (tr. 15, 21, 24), không có số chi.
- Agent (abstain, 3 lần search): Không đủ bằng chứng để trả lời.
- Lý do: Từ chối đúng


## Tổng hợp

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi hệ thống |
|---|---|---|---|
| table | 2/4 | 50% | 0 |
| image | 2/3 | 67% | 0 |
| chart | 2/4 | 50% | 0 |
| multihop | 0/2 | 0% | 0 |
| text | 1/2 | 50% | 0 |
| unanswerable | 3/3 | 100% | 0 |
| **Toàn bộ** | **10/18** | **55.6%** | 0 |
