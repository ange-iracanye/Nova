from documents import load_documents



def find_information(question):

    documents = load_documents()


    sentences = documents.split(
        "."
    )


    question_words = question.lower().split()


    best_sentence = ""


    best_score = 0



    for sentence in sentences:

        score = 0


        words = sentence.lower().split()


        for word in question_words:

            if word in words:

                score += 1



        if score > best_score:

            best_score = score

            best_sentence = sentence



    if best_score == 0:

        return None



    return best_sentence.strip()