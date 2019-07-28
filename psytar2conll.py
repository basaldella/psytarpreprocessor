import minerva as mine
import pandas as pd
import re

XLSX_PATH = "data/PsyTAR_dataset.xlsx"
CSV_PATH = "data/PsyTAR_binary.csv"

sentences = pd.read_excel(XLSX_PATH, sheet_name="Sentence_Labeling")

sentences = sentences[["drug_id", "sentences", "ADR", "WD", "EF", "INF", "SSI", "DI"]]
sentences = sentences.fillna(0)
sentences[["ADR", "WD", "EF", "INF", "SSI", "DI"]] = (
    sentences[["ADR", "WD", "EF", "INF", "SSI", "DI"]]
    .replace(re.compile("[!* ]+"), 1)
    .astype(int)
)

sentences[["sentences", "ADR", "WD", "EF", "INF", "SSI", "DI"]].to_csv(
    CSV_PATH, header=True, index=False, sep="\t", encoding="utf8", decimal="."
)

sheet = "ADR"
labels = pd.read_excel(XLSX_PATH, sheet_name=sheet + "_Identified")

colnames = ["drug_id", "sentence_index", "sentences"]
annotation_fields = []
for i in range(30):
    annotation_fields.append(f"{sheet}{i+1}")

print(colnames)
for key, row in labels.iterrows():

    sentence = mine.Sentence(row.sentences)
    anno = row["ADR1"]
    start_index = row.sentences.index(anno)
    end_index = start_index + len(anno) - 1
