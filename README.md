# PsyTAR preprocessed files

This repository contains 
- the original PsyTAR dataset, as downloaded from [Ask a Patient](https://www.askapatient.com/research/pharmacovigilance/corpus-ades-psychiatric-medications.asp), on August 1st, 2019;
- a Python script to convert it to CSV and CoNLL format;
- the converted data.

The folder structure is the following:
- `data/binary` contains the annotations from the `Sentence_Labeling` sheet;
- `data/all` contains the annotations from the `{ADR, WD, SSI, DI}_Identified` sheets, in CoNLL format;
- `data/conflated` contains the same data as `data/all`, but all the entity types are conflated on a single type.

The corpus is avaiable as a whole in each `full.txt.` file. For the sake of reproducibility, 
I also provide training, development and test sets splits, with a 80-10-20 ratio. 
The code for generating the splits should be perfectly reproducible, i.e. if you run the 
Python scripts, you should obtain the exact same splits you see in this repository.

## License

The PsyTAR dataset is under the [CC BY 4.0 Data license](https://creativecommons.org/licenses/by/4.0/).

Please cite the [original paper](https://www.sciencedirect.com/science/article/pii/S2352340919301891#undtbl2) if you use
 the corpus. If you use the splits provided here, please also provide a pointer to this repository.