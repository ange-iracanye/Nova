import os



DOCUMENT_FOLDER = "documents"



def load_documents():

    text = ""


    if not os.path.exists(DOCUMENT_FOLDER):

        os.makedirs(
            DOCUMENT_FOLDER
        )


    for file in os.listdir(
        DOCUMENT_FOLDER
    ):

        if file.endswith(".txt"):

            path = os.path.join(
                DOCUMENT_FOLDER,
                file
            )


            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                text += f.read()
                text += "\n"



    return text