import minerva as mine
import pandas as pd
import re
import warnings


def sentence_to_conll_string(sentence: mine.Sentence, entity_name: str) -> str:

    words = [t.text for t in sentence]
    annos = sentence.get_annotation(entity_name)
    labels = ["O"] * len(words)
    if annos:
        ner = isinstance(annos[0], mine.TokenSpan)

        if ner:
            for span in annos:
                labels[span.start_index] = "B-" + span.value
                for index in range(span.start_index + 1, span.end_index + 1):
                    labels[index] = "I-" + span.value
        else:
            raise NotImplementedError("Ouput for non-spans is not implemented yet.")

    return "\n".join(["\t".join(line) for line in zip(words, labels)]) + "\n"


XLSX_PATH = "data/PsyTAR_dataset.xlsx"
CSV_PATH = "data/PsyTAR_binary.csv"
CONLL_PATH = "data/PsyTAR_conll.csv"

sentence_df = pd.read_excel(XLSX_PATH, sheet_name="Sentence_Labeling")

sentence_df = sentence_df[
    ["drug_id", "sentence_index", "sentences", "ADR", "WD", "EF", "INF", "SSI", "DI"]
]
sentence_df = sentence_df.fillna(0)
sentence_df[["ADR", "WD", "EF", "INF", "SSI", "DI"]] = (
    sentence_df[["ADR", "WD", "EF", "INF", "SSI", "DI"]]
    .replace(re.compile("[!* ]+"), 1)
    .astype(int)
)

sentence_df[["sentences", "ADR", "WD", "EF", "INF", "SSI", "DI"]].to_csv(
    CSV_PATH, header=True, index=False, sep="\t", encoding="utf8", decimal="."
)

sentences_map = {}
for drug_name in sentence_df.drug_id.unique()[:-1]:
    sentences_map[drug_name] = {}

for _, row in sentence_df.iloc[:-1].iterrows():

    if isinstance(row.sentences, str):
        sentences_map[row.drug_id][row.sentence_index] = mine.Sentence(row.sentences)


sheet_names = ["ADR", "WD", "SSI", "DI"]
invalid_sentences = set()
total_annos = 0
total_warns = 0

for sheet in sheet_names:
    labels_df = pd.read_excel(XLSX_PATH, sheet_name=sheet + "_Identified")

    colnames = ["drug_id", "sentence_index", "sentences"]
    annotation_fields = []
    for i in range(30 if sheet == "ADR" else 10):
        annotation_fields.append(f"{sheet}{i + 1}")

    sentence_df = []

    for key, row in labels_df.iterrows():

        sentence = sentences_map[row.drug_id][row.sentence_index]
        for anno_name in annotation_fields:
            total_annos += 1
            anno = row[anno_name]

            if pd.isna(anno):
                continue

            try:
                anno = anno.strip()
                start_index = row.sentences.lower().index(anno.lower())
                end_index = start_index + len(anno) - 1
            except ValueError:
                # warnings.warn(f"Cannot find string '{anno}' in {sentence.text}")
                total_warns += 1
                invalid_sentences.add((row.drug_id, row.sentence_index))
                continue

            sentence.add_annotation(
                "PsyTAR",
                sheet,
                sentence.token_at_char(start_index).index,
                sentence.token_at_char(end_index).index + 1,
            )

print(f"I found {total_annos} annotations.")
print(
    f"There are {total_warns} invalid annotations in {len(invalid_sentences)} sentences."
)

with open(CONLL_PATH, "w", encoding="utf8") as f:
    for doc_id, doc in sentences_map.items():
        for sentence_id, sentence in doc.items():
            if (doc_id, sentence_id) not in invalid_sentences:
                f.write(sentence_to_conll_string(sentence, "PsyTAR"))
                f.write("\n")
