# Chat file attachments

Nova's chat composer supports up to five attachments per message. Files are processed in memory; Nova does not persist the uploaded binary files.

## Supported formats

- Images: PNG, JPEG, WebP, GIF (first frame), BMP, TIFF.
- Documents: PDF, DOCX, PPTX, XLSX, legacy XLS, ODT, ODS.
- Text and source: TXT, Markdown, CSV, TSV, JSON, JSONL, XML, HTML, RTF, Python, JavaScript/TypeScript, CSS/SCSS, SQL, YAML, TOML, INI, logs, and common source files.

PDF text is extracted page by page. Image-only PDFs are rendered to a small number of page images and sent through Nova's vision-capable model route. Images are sent as multimodal image inputs. Word, Excel, and PowerPoint files are converted to bounded text, including tables and slide text.

## Limits and safety

- Maximum five files per message.
- Maximum 8 MB per file and 10 MB combined raw file data.
- Maximum 40 PDF pages; up to three scanned pages are sent for visual reading.
- Extracted document text is capped at 30,000 characters.
- Office archives are checked for excessive member counts and expanded size before parsing.
- Uploaded files are never written to disk by the attachment processor.
- Text found inside files and images is treated as untrusted source material, not as instructions to Nova.
- Image understanding uses the configured OpenRouter vision route (`NOVA_VISION_MODEL`, default `openrouter/free`) and requires a working `OPENROUTER_API_KEY` plus an available vision-capable free route.

Legacy binary Word `.doc` and PowerPoint `.ppt`, arbitrary executables, archives, audio, and video are not supported. Save legacy Office documents as DOCX/PPTX or export them to PDF before attaching.