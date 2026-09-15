# 教材库 / Textbook Library

AP/IB 课程的原始教材 PDF，是 ingestion 管线的**数据来源**（不被应用直接读取）。
体积较大（合计 ~570MB），已在 `.gitignore` 中忽略，不入库。

## 清单 / Catalog

### `AP/` — AP 课程
| 文件 | 学科 | 原始文件名 |
|------|------|-----------|
| `AP_Statistics_The_Practice_of_Statistics.pdf` | AP Statistics | The Practice of Statistics |
| `AP_Physics_5_Steps_to_a_5_2023.pdf` | AP Physics（5 Steps to a 5, Greg Jacobs） | 2023新 5 Steps to a 5 - Greg Jacobs(1) |
| `AP_CS_Principles_Hare_4th.pdf` | AP CS Principles | Computer Science Principles, 4th Ed (Kevin P Hare) |

### `IB/` — IB 课程
| 文件 | 学科 | 原始文件名 |
|------|------|-----------|
| `IB_Math_AA_HL_Analysis_and_Approaches.pdf` | IB Math AA HL | Mathematics HL - Analysis and Approaches |
| `IB_Computer_Science_Hodder.pdf` | IB Computer Science | Hodder IBCS Textbook |
| `IB_Biology_Hodder.pdf` | IB Biology | Hodder IB Biology（原文件名未标科目，已据内容确认为 IB Biology DP） |

### `reference/` — 通用大学教材（AP/IB 通用参考）
| 文件 | 学科 | 原始文件名 |
|------|------|-----------|
| `Economics_Mankiw_Principles_of_Economics.pdf` | Economics | Principles of Economics, N. G. Mankiw |
| `Calculus_Adams_Essex_A_Complete_Course.pdf` | Calculus | Adams & Essex - Calculus: A Complete Course |

## 说明 / Notes

- 原 `IB_Hodder_UNKNOWN_SUBJECT_please_verify.pdf` 已据生成内容（A1.1 Water、IB Biology DP 探究技能等）确认为 **IB Biology**，已重命名为 `IB_Biology_Hodder.pdf`。
- 分类逻辑：`AP/` `IB/` 放课程专属教材；Mankiw、Adams 是通用大学教材，放 `reference/`。
  若你希望按学科（而非课程）组织，告诉我，我可以改成 `economics/ math/ cs/ ...` 的结构。
