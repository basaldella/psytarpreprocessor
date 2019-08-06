import os
import minerva as mine
import pandas as pd
import random
import re


def sentence_to_conll_string(
    sentence: mine.Sentence, entity_name: str, conflate: bool = False
) -> str:

    words = [t.text for t in sentence]
    annos = sentence.get_annotation(entity_name)
    labels = ["O"] * len(words)
    if annos:
        ner = isinstance(annos[0], mine.TokenSpan)

        if ner:
            for span in annos:
                entity_tag = span.value if not conflate else "Entity"
                labels[span.start_index] = "B-" + entity_tag
                for index in range(span.start_index + 1, span.end_index + 1):
                    labels[index] = "I-" + entity_tag
        else:
            raise NotImplementedError("Ouput for non-spans is not implemented yet.")

    return "\n".join(["\t".join(line) for line in zip(words, labels)]) + "\n"


XLSX_PATH = "data/PsyTAR_dataset.xlsx"
CSV_PATH = "data/PsyTAR_binary.csv"
BINARY_PATH = "data/binary/"
CONLL_ALL_PATH = "data/all/"
CONLL_CONFLATED_PATH = "data/conflated/"

sentence_df = pd.read_excel(
    XLSX_PATH, sheet_name="Sentence_Labeling", dtype={"drug_id": str, "sentences": str}
)

sentence_df = sentence_df[
    ["drug_id", "sentence_index", "sentences", "ADR", "WD", "EF", "INF", "SSI", "DI"]
]


sentence_df = sentence_df.dropna(subset=["sentences"])
sentence_df = sentence_df.loc[sentence_df.sentences.apply(lambda x: len(x.strip())) > 0]
sentence_df = sentence_df.fillna(0)


sentence_df[["ADR", "WD", "EF", "INF", "SSI", "DI"]] = (
    sentence_df[["ADR", "WD", "EF", "INF", "SSI", "DI"]]
    .replace(re.compile("[!* ]+"), 1)
    .astype(int)
)


print("Writing binary datasets...")

out_df = sentence_df[["sentences", "ADR", "WD", "EF", "INF", "SSI", "DI"]].iloc[:-1]
out_df.to_csv(
    BINARY_PATH + os.sep + "full.csv",
    header=True,
    index=False,
    sep="\t",
    encoding="utf8",
    decimal=".",
)

train_df = out_df.sample(frac=0.7, random_state=120307)
testdev_df = out_df.drop(train_df.index)
test_df = testdev_df.sample(frac=0.66, random_state=703021)
dev_df = testdev_df.drop(test_df.index)

train_df.to_csv(
    BINARY_PATH + os.sep + "train.csv",
    header=True,
    index=False,
    sep="\t",
    encoding="utf8",
    decimal=".",
)

test_df.to_csv(
    BINARY_PATH + os.sep + "test.csv",
    header=True,
    index=False,
    sep="\t",
    encoding="utf8",
    decimal=".",
)

dev_df.to_csv(
    BINARY_PATH + os.sep + "dev.csv",
    header=True,
    index=False,
    sep="\t",
    encoding="utf8",
    decimal=".",
)

print("Done.")

sentences_map = {}
for drug_name in sentence_df.drug_id.unique():
    sentences_map[drug_name] = {}

for _, row in sentence_df.iterrows():
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

    for key, row in labels_df.iterrows():

        try:
            sentence = sentences_map[row.drug_id][row.sentence_index]
        except:
            pass
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

sentences = []
for doc_id, doc in sentences_map.items():
    for sentence_id, sentence in doc.items():
        if (doc_id, sentence_id) not in invalid_sentences:
            sentences.append(sentence)

random.seed(120307)
random.shuffle(sentences)
train_cut = (len(sentences) // 100) * 70
dev_cut = train_cut + ((len(sentences) // 100) * 10)

train = sentences[:train_cut]
dev = sentences[train_cut:dev_cut]
test = sentences[dev_cut:]

assert len(sentences) == len(train) + len(dev) + len(test)

print(
    f"Out of          {len(sentences)} sentences,\n"
    f"I will generate {len(train)} training sentences,\n"
    f"                {len(dev)} dev sentences, and\n"
    f"                {len(test)} test sentences."
)

print("Saving...")

# Saving non-conflated
with open(CONLL_ALL_PATH + os.sep + "full.txt", "w", encoding="utf8") as f:
    for doc_id, doc in sentences_map.items():
        for sentence_id, sentence in doc.items():
            if (doc_id, sentence_id) not in invalid_sentences:
                f.write(sentence_to_conll_string(sentence, "PsyTAR"))
                f.write("\n")
with open(CONLL_ALL_PATH + os.sep + "train.txt", "w", encoding="utf8") as f:
    for sentence in train:
        f.write(sentence_to_conll_string(sentence, "PsyTAR"))
        f.write("\n")
with open(CONLL_ALL_PATH + os.sep + "dev.txt", "w", encoding="utf8") as f:
    for sentence in dev:
        f.write(sentence_to_conll_string(sentence, "PsyTAR"))
        f.write("\n")
with open(CONLL_ALL_PATH + os.sep + "test.txt", "w", encoding="utf8") as f:
    for sentence in test:
        f.write(sentence_to_conll_string(sentence, "PsyTAR"))
        f.write("\n")

# Saving conflated
with open(CONLL_CONFLATED_PATH + os.sep + "full.txt", "w", encoding="utf8") as f:
    for doc_id, doc in sentences_map.items():
        for sentence_id, sentence in doc.items():
            if (doc_id, sentence_id) not in invalid_sentences:
                f.write(sentence_to_conll_string(sentence, "PsyTAR", conflate=True))
                f.write("\n")
with open(CONLL_CONFLATED_PATH + os.sep + "train.txt", "w", encoding="utf8") as f:
    for sentence in train:
        f.write(sentence_to_conll_string(sentence, "PsyTAR", conflate=True))
        f.write("\n")
with open(CONLL_CONFLATED_PATH + os.sep + "dev.txt", "w", encoding="utf8") as f:
    for sentence in dev:
        f.write(sentence_to_conll_string(sentence, "PsyTAR", conflate=True))
        f.write("\n")
with open(CONLL_CONFLATED_PATH + os.sep + "test.txt", "w", encoding="utf8") as f:
    for sentence in test:
        f.write(sentence_to_conll_string(sentence, "PsyTAR", conflate=True))
        f.write("\n")

print("Done!")
