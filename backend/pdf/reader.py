from pypdf import PdfReader


class PDFReader:

    def read(

        self,

        path

    ):

        text=[]

        reader=PdfReader(path)

        for page in reader.pages:

            text.append(

                page.extract_text()

            )

        return "\n".join(text)