# 本机改动说明

- 上游：https://github.com/AIExcel1949/excel1949-cn-legal-skills ，提交 f8f8240a58876a434609a1426bcdde2c7dba1d91，许可 GPL-3.0（见 LICENSE），2026-10-13 引入。
- 改动：`skills/cn-legal-core/scripts/docx_brand.py` 的 `brand_docx()` 默认不再插入上游作者的 Logo / 公众号二维码页眉，也不改写 Word 作者元数据；设置 `CN_LEGAL_BRAND=1` 可恢复。
- 未改动：部分脚本与 schema 仍把输出 JSON 的 author 写成 “AIOffice职场通关-excel1949”（如 cn-data-privacy、cn-contract-review/render_docx.py 的打印信息）。对外交付 Word 前，核对文件属性里的作者。
- 只在 ai-skills 顶层为合同、合规、研究相关的 14 个 skill 建了软链接；诉讼类 skill 仍在本目录，需要时再链接。
- 部分脚本要求 `.venv/bin/python`，首次运行前按上游 README 建虚拟环境。
