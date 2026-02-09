# 🧪 Test Case: test_case_2

**Status:** ❌ **FAILED**

**Input Query:**
> *"What objectives does the WHO infertility guideline aim to achieve regarding recommendations, adaptation, and national adoption?"*

---

## 📊 Metrics Summary

| Metric Name | Score | Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Answer Relevancy** | 1.000 | 0.700 | ✅ Pass |
| **Faithfulness** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Relevancy** | 0.667 | 0.700 | ❌ Fail |
| **Contextual Recall** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Precision** | 1.000 | 0.700 | ✅ Pass |

---

## 🔍 Detailed Analysis

### ✅ Answer Relevancy
- **Score:** 1.000
- **Reason:** The score is 1.00 because the output is perfectly relevant, directly and fully addressing all aspects of the input question about the WHO guideline's objectives. There are no irrelevant statements to lower the score. Excellent job!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Statements:
[
    "Based on the WHO infertility guideline's stated objectives, it aims to achieve three main goals regarding recommendations, adaptation, and national adoption.",
    "It aims to provide evidence-based recommendations for the entire spectrum of infertility care, including its prevention, diagnosis, and treatment.",
    "It aims to maximize adaptation and implementation in different settings by providing explicit explanations of all the relevant factors that guided the development of these recommendations.",
    "It aims to serve as a resource for countries.",
    "It aims to provide them with a source to adopt, adapt, or update their own national guidelines for infertility."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "idk",
        "reason": "Statement is too vague and generic ('serve as a resource for countries') without specifying how it relates to recommendations, adaptation, or national adoption objectives."
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ✅ Faithfulness
- **Score:** 1.000
- **Reason:** The score is 1.00 because there are no contradictions between the actual output and the retrieval context, indicating perfect faithfulness. Excellent work!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Truths (limit=None):
[
    "This is the first WHO Guideline for the prevention, diagnosis and treatment of infertility.",
    "The guideline aims to improve the implementation of evidence-based interventions related to infertility.",
    "One objective of the guideline is to provide evidence-based recommendations for the prevention, diagnosis and treatment of infertility.",
    "One objective of the guideline is to provide explicit explanations of the factors that guided the development of the recommendations.",
    "One objective of the guideline is to provide a source for countries to adopt, adapt or update their national guidelines.",
    "The guideline includes a chapter on research gaps, future scope and updating the guideline.",
    "A document titled 'Infertility prevalence estimates: 1990-2021' was published by the World Health Organization in Geneva in 2023.",
    "A document titled 'The selection and use of essential medicines 2023: web annex A: World Health Organization model list of essential medicines: 23rd list (2023)' was published by the World Health Organization in Geneva in 2023.",
    "A document titled 'The selection and use of essential in vitro diagnostics: report of the fourth meeting of the WHO Strategic Advisory Group of Experts on In Vitro Diagnostics, 2022' was published by the World Health Organization in Geneva in 2023.",
    "An article titled 'Towards a nuanced view and response to global fertility trends' by Mburu G, Kiarie J, Allotey P was published in The Lancet in 2024."
] 
 
Claims:
[
    "The WHO infertility guideline aims to achieve three main goals regarding recommendations, adaptation, and national adoption.",
    "The first goal is to provide evidence-based recommendations for the entire spectrum of infertility care, including its prevention, diagnosis, and treatment.",
    "The second goal is to maximize adaptation and implementation in different settings by providing explicit explanations of all the relevant factors that guided the development of these recommendations.",
    "The third goal is to serve as a resource for countries, providing them with a source to adopt, adapt, or update their own national guidelines for infertility."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ❌ Contextual Relevancy
- **Score:** 0.667
- **Reason:** The score is 0.67 because while three relevant statements directly address the input's objectives regarding recommendations ('evidence-based recommendations'), adaptation ('maximize adaptation in different settings'), and national adoption ('source for countries to adopt, adapt or update national guidelines'), the retrieval context also contained irrelevant bibliographic references and a general title that did not specifically answer the query about objectives.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdicts": [
            {
                "statement": "This is the first WHO Guideline for the prevention, diagnosis and treatment of infertility, which aims to improve the implementation of evidence-based interventions related to infertility.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "The objectives of this guideline are: to provide evidence-based recommendations for the prevention, diagnosis and treatment of infertility.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "The objectives of this guideline are: to provide explicit explanations of all the relevant factors that guided the development of the recommendations in order to maximize the adaptation and implementation of the guideline in different settings.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "The objectives of this guideline are: to provide a source for countries to adopt, adapt or update their national guidelines for the prevention, diagnosis and treatment of infertility.",
                "verdict": "yes",
                "reason": null
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "Guideline for the prevention, diagnosis and treatment of infertility",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'Guideline for the prevention, diagnosis and treatment of infertility' which is only a title/scope description and does not address the specific input about objectives regarding recommendations, adaptation, and national adoption."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "The provided context consists of bibliographic references and a chapter heading, but contains no actual statements describing the WHO infertility guideline's objectives regarding recommendations, adaptation, and national adoption.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'The provided context consists of bibliographic references and a chapter heading, but contains no actual statements describing the WHO infertility guideline's objectives regarding recommendations, adaptation, and national adoption.' when it has nothing to do with the specific objectives of the WHO infertility guideline as asked in the input."
            }
        ]
    }
]
```
</details>

### ✅ Contextual Recall
- **Score:** 1.000
- **Reason:** The score is 1.00 because every sentence in the expected output (sentences 1, 2, and 3) is fully supported by the 1st node in the retrieval context, which explicitly lists all three objectives.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The 1st node in the retrieval context states the guideline's objectives: 'to provide evidence-based recommendations for the prevention, diagnosis and treatment of infertility'.",
        "expected_output": "The WHO infertility guideline has three main objectives:\n\n1. **Evidence\u2011based recommendations** \u2013 to issue clear, evidence\u2011based guidance on the prevention, diagnosis and treatment of infertility.  \n2. **Facilitate adaptation and implementation** \u2013 to explain all relevant factors (e.g., resources, feasibility, equity) so that the recommendations can be readily adapted to different contexts and health\u2011system settings.  \n3. **Support national guideline development** \u2013 to serve as a source that countries can adopt, adapt, or update for their own national infertility policies and clinical guidelines."
    },
    {
        "verdict": "yes",
        "reason": "The 1st node in the retrieval context states: 'to provide explicit explanations of all the relevant factors... to maximize the adaptation and implementation of the guideline in different settings'.",
        "expected_output": "The WHO infertility guideline has three main objectives:\n\n1. **Evidence\u2011based recommendations** \u2013 to issue clear, evidence\u2011based guidance on the prevention, diagnosis and treatment of infertility.  \n2. **Facilitate adaptation and implementation** \u2013 to explain all relevant factors (e.g., resources, feasibility, equity) so that the recommendations can be readily adapted to different contexts and health\u2011system settings.  \n3. **Support national guideline development** \u2013 to serve as a source that countries can adopt, adapt, or update for their own national infertility policies and clinical guidelines."
    },
    {
        "verdict": "yes",
        "reason": "The 1st node in the retrieval context states: 'to provide a source for countries to adopt, adapt or update their national guidelines...'.",
        "expected_output": "The WHO infertility guideline has three main objectives:\n\n1. **Evidence\u2011based recommendations** \u2013 to issue clear, evidence\u2011based guidance on the prevention, diagnosis and treatment of infertility.  \n2. **Facilitate adaptation and implementation** \u2013 to explain all relevant factors (e.g., resources, feasibility, equity) so that the recommendations can be readily adapted to different contexts and health\u2011system settings.  \n3. **Support national guideline development** \u2013 to serve as a source that countries can adopt, adapt, or update for their own national infertility policies and clinical guidelines."
    }
]
```
</details>

### ✅ Contextual Precision
- **Score:** 1.000
- **Reason:** The score is 1.00 because the single relevant node is correctly ranked first, while both irrelevant nodes are ranked lower. The first node directly answers the input by quoting the three WHO guideline objectives. The second node (rank 2) is irrelevant because it only repeats the guideline title without addressing objectives. The third node (rank 3) is irrelevant because it discusses research gaps and references instead of the requested objectives.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The text directly states the three objectives of the WHO infertility guideline: 'to provide evidence-based recommendations...', 'to provide explicit explanations... to maximize the adaptation and implementation...', and 'to provide a source for countries to adopt, adapt or update their national guidelines...'. This perfectly matches the three objectives outlined in the expected output."
    },
    {
        "verdict": "no",
        "reason": "The text 'Guideline for the prevention, diagnosis and treatment of infertility' only repeats the title of the guideline. It does not provide any information about the specific objectives regarding recommendations, adaptation, or national adoption requested in the input."
    },
    {
        "verdict": "no",
        "reason": "The text lists references and a chapter title ('Research gaps, future scope and updating the guideline'). It contains no information about the guideline's objectives concerning recommendations, adaptation, or national adoption."
    }
]
```
</details>

## 📚 Retrieval Data

<details>
<summary><strong>Retrieval Context (Chunks)</strong></summary>

**Chunk 1:**
> This is the first WHO Guideline for the prevention, diagnosis and treatment of infertility , which aims to improve the implementation of evidence-based interventions related to infertility. ## The objectives of this guideline are: - to provide evidence-based recommendations for the prevention, diagnosis and treatment of infertility; - to provide explicit explanations of all the relevant factors that guided the development of the recommendations in order to maximize the adaptation and implementation of the guideline in different settings; - to provide a source for countries to adopt, adapt or update their national guidelines for the prevention, diagnosis and treatment of infertility.

**Chunk 2:**
> Guideline for the prevention, diagnosis and treatment of infertility

**Chunk 3:**
> 1. Infertility prevalence estimates: 1990-2021. Geneva: World Health Organization; 2023 (https://apps.who.int/iris/handle/10665/366700). 2. The selection and use of essential medicines 2023: web annex A: World Health Organization model list of essential medicines: 23rd list (2023). Geneva: World Health Organization; 2023 (https://iris.who.int/handle/10665/371090). 3. The selection and use of essential in vitro diagnostics: report of the fourth meeting of the WHO Strategic Advisory Group of Experts on In Vitro Diagnostics, 2022 (including the fourth WHO model list of essential in vitro diagnostics). Geneva: World Health Organization; 2023 (https://iris.who.int/handle/10665/373322). 4. Mburu G, Kiarie J, Allotey P. Towards a nuanced view and response to global fertility trends. Lancet. 2024;403(10440):1953-56 ( https://doi. org/10.1016/s0140-6736(24)00490-2). <!-- image --> ## Chapter ## 12 Research gaps, future scope and updating the guideline

</details>

**Actual LLM Output:**

> Based on the WHO infertility guideline's stated objectives, it aims to achieve three main goals regarding recommendations, adaptation, and national adoption [0](9789240115774-eng.pdf):

1.  **To provide evidence-based recommendations** for the entire spectrum of infertility care, including its prevention, diagnosis, and treatment [0](9789240115774-eng.pdf).
2.  **To maximize adaptation and implementation in different settings** by providing explicit explanations of all the relevant factors that guided the development of these recommendations [0](9789240115774-eng.pdf).
3.  **To serve as a resource for countries**, providing them with a source to adopt, adapt, or update their own **national guidelines** for infertility [0](9789240115774-eng.pdf).

---

# 🧪 Test Case: test_case_4

**Status:** ❌ **FAILED**

**Input Query:**
> *"How do good practice statements for infertility management differ between diagnostic testing and treatment decisions?"*

---

## 📊 Metrics Summary

| Metric Name | Score | Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Answer Relevancy** | 1.000 | 0.700 | ✅ Pass |
| **Faithfulness** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Relevancy** | 0.000 | 0.700 | ❌ Fail |
| **Contextual Recall** | 0.000 | 0.700 | ❌ Fail |
| **Contextual Precision** | 0.000 | 0.700 | ❌ Fail |

---

## 🔍 Detailed Analysis

### ✅ Answer Relevancy
- **Score:** 1.000
- **Reason:** The score is 1.00 because the output is perfectly relevant, directly addressing the requested comparison between diagnostic and treatment guidelines in infertility management. There are no irrelevant statements, and the response stays sharply focused on the input's specific question. Great job!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Statements:
[
    "Based solely on the provided documents, I cannot answer your question about how good practice statements for infertility management differ between diagnostic testing and treatment decisions.",
    "The retrieved documents contain a general guideline title and several reference lists pertaining to economic impact, obstetric outcomes, and lifestyle factors in infertility.",
    "None of the text excerpts address the specific differences in practice statements, diagnostic testing protocols, or treatment decision-making criteria that your query requires.",
    "Therefore, the necessary information to compare these aspects is not present in the provided context."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ✅ Faithfulness
- **Score:** 1.000
- **Reason:** The score is 1.00 because there are no contradictions listed, indicating the actual output is fully faithful to the retrieval context. Excellent work!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Truths (limit=None):
[
    "The text is a guideline for the prevention, diagnosis and treatment of infertility.",
    "The text includes a reference to a 1983 Nature article by Trounson and Mohr about a human pregnancy following cryopreservation, thawing and transfer of an eight-cell embryo.",
    "The text includes a reference to a 2002 Hum Reprod Update article by Collins on an international survey of the health economics of IVF and ICSI.",
    "The text includes a reference to a 2009 Fertil Steril article by Chambers et al. on the economic impact of assisted reproductive technology in selected developed countries.",
    "The text includes a reference to a 2012 Hum Reprod Update article by Pandey et al. on obstetric and perinatal outcomes in singleton pregnancies from IVF/ICSI.",
    "The text includes a section titled 'Research gaps and future guideline update'.",
    "The text includes a reference to a 2013 Reprod Biol Endocrinol article by Sharma et al. on lifestyle factors and reproductive health.",
    "The text includes a reference to a 2007 Hum Reprod Update article by Homan et al. on the impact of lifestyle factors on reproductive performance.",
    "The text includes a reference to a 2021 Cochrane Database Syst Rev article by Boedt et al. on preconception lifestyle advice for people with infertility."
] 
 
Claims:
[
    "The AI cannot answer the question about how good practice statements for infertility management differ between diagnostic testing and treatment decisions based solely on the provided documents.",
    "The retrieved documents contain a general guideline title.",
    "The retrieved documents contain several reference lists pertaining to economic impact in infertility.",
    "The retrieved documents contain several reference lists pertaining to obstetric outcomes in infertility.",
    "The retrieved documents contain several reference lists pertaining to lifestyle factors in infertility.",
    "None of the text excerpts address the specific differences in practice statements for infertility management.",
    "None of the text excerpts address diagnostic testing protocols for infertility management.",
    "None of the text excerpts address treatment decision-making criteria for infertility management.",
    "The necessary information to compare these aspects is not present in the provided context."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "idk",
        "reason": "The context mentions the text is a guideline for prevention, diagnosis and treatment, but no specific diagnostic testing protocols are described in the provided excerpts."
    },
    {
        "verdict": "idk",
        "reason": "The context mentions the text is a guideline for treatment, but no specific treatment decision-making criteria are described in the provided excerpts."
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ❌ Contextual Relevancy
- **Score:** 0.000
- **Reason:** The score is 0.00 because the retrieval context contained only a guideline title, reference citations, and mentions of lifestyle factors and future research, none of which address the specific comparison requested between good practice statements for diagnostic testing versus treatment decisions in infertility management. As noted, the context had 'no actual content about how good practice statements differ' and the references were 'about lifestyle factors...not about comparing guidelines for diagnosis versus treatment.'

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdicts": [
            {
                "statement": "Guideline for the prevention, diagnosis and treatment of infertility",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'Guideline for the prevention, diagnosis and treatment of infertility' which is only a title/header with no actual content about how good practice statements differ between diagnostic testing and treatment decisions."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "The context consists only of reference citations and a section heading without substantive content about good practice statements for infertility management.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'The context consists only of reference citations and a section heading without substantive content about good practice statements for infertility management' when it has nothing to do with how good practice statements differ between diagnostic testing and treatment decisions in infertility management."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "The context lists three references about lifestyle factors and reproductive health/infertility.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'The context lists three references about lifestyle factors and reproductive health/infertility' when the input specifically asks about how good practice statements differ between diagnostic testing and treatment decisions. The listed references are about lifestyle factors and preconception advice, not about comparing guidelines for diagnosis versus treatment."
            },
            {
                "statement": "The context mentions a section titled 'Research gaps and future guideline update'.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'The context mentions a section titled \"Research gaps and future guideline update\"' when the input asks for a comparison of good practice statements between diagnostic testing and treatment decisions. The mention of future guidelines does not address the requested comparison."
            }
        ]
    }
]
```
</details>

### ❌ Contextual Recall
- **Score:** 0.000
- **Reason:** The score is 0.00 because none of the content in the expected output can be attributed to the nodes in retrieval context. The expected output describes detailed clinical guidance (sentences 1-4), but the retrieval context nodes (1 and 2) contain only guideline titles and reference lists for research gaps, with no actual clinical recommendations.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "no",
        "reason": "The retrieval context contains only a guideline title and reference lists for research gaps/future updates. No content describes separating diagnostic testing and treatment decisions into two steps or provides the specific good-practice statements quoted in the sentence.",
        "expected_output": "The good\u2011practice statements separate the two steps:\n\n* **Diagnostic testing** \u2013\u202fThe guideline says clinicians should *choose tests* that are driven by the patient\u2019s history and physical exam, making the work\u2011up **systematic and cost\u2011effective**.\n\n* **Treatment decisions** \u2013\u202fWhen moving to therapy, clinicians should **base choices on the balance of benefits and harms, the couple\u2019s values and preferences, feasibility, and resource availability**. They should also prioritize the **least\u2011expensive yet effective options**, plan follow\u2011up, manage risks, and record pregnancy outcomes.\n\nIn short, diagnostics are guided by clinical findings and efficiency, while treatment is guided by outcomes, patient preferences, and overall cost\u2011effectiveness."
    },
    {
        "verdict": "no",
        "reason": "The retrieval context does not contain any guideline content about diagnostic testing being driven by history/exam to be systematic and cost-effective. The nodes only list references for research gaps (1st node) and lifestyle advice (2nd node), with no such recommendations.",
        "expected_output": "The good\u2011practice statements separate the two steps:\n\n* **Diagnostic testing** \u2013\u202fThe guideline says clinicians should *choose tests* that are driven by the patient\u2019s history and physical exam, making the work\u2011up **systematic and cost\u2011effective**.\n\n* **Treatment decisions** \u2013\u202fWhen moving to therapy, clinicians should **base choices on the balance of benefits and harms, the couple\u2019s values and preferences, feasibility, and resource availability**. They should also prioritize the **least\u2011expensive yet effective options**, plan follow\u2011up, manage risks, and record pregnancy outcomes.\n\nIn short, diagnostics are guided by clinical findings and efficiency, while treatment is guided by outcomes, patient preferences, and overall cost\u2011effectiveness."
    },
    {
        "verdict": "no",
        "reason": "The retrieval context provides no guideline recommendations on treatment decisions balancing benefits/harms, patient values, feasibility, or prioritizing least-expensive effective options. The nodes contain only reference lists for economic reviews and research gaps, not clinical guidance.",
        "expected_output": "The good\u2011practice statements separate the two steps:\n\n* **Diagnostic testing** \u2013\u202fThe guideline says clinicians should *choose tests* that are driven by the patient\u2019s history and physical exam, making the work\u2011up **systematic and cost\u2011effective**.\n\n* **Treatment decisions** \u2013\u202fWhen moving to therapy, clinicians should **base choices on the balance of benefits and harms, the couple\u2019s values and preferences, feasibility, and resource availability**. They should also prioritize the **least\u2011expensive yet effective options**, plan follow\u2011up, manage risks, and record pregnancy outcomes.\n\nIn short, diagnostics are guided by clinical findings and efficiency, while treatment is guided by outcomes, patient preferences, and overall cost\u2011effectiveness."
    },
    {
        "verdict": "no",
        "reason": "The summary statement comparing diagnostics and treatment is not present in the retrieval context. The nodes contain only a guideline title and reference lists, with no synthesized guidance on clinical findings, efficiency, outcomes, or patient preferences.",
        "expected_output": "The good\u2011practice statements separate the two steps:\n\n* **Diagnostic testing** \u2013\u202fThe guideline says clinicians should *choose tests* that are driven by the patient\u2019s history and physical exam, making the work\u2011up **systematic and cost\u2011effective**.\n\n* **Treatment decisions** \u2013\u202fWhen moving to therapy, clinicians should **base choices on the balance of benefits and harms, the couple\u2019s values and preferences, feasibility, and resource availability**. They should also prioritize the **least\u2011expensive yet effective options**, plan follow\u2011up, manage risks, and record pregnancy outcomes.\n\nIn short, diagnostics are guided by clinical findings and efficiency, while treatment is guided by outcomes, patient preferences, and overall cost\u2011effectiveness."
    }
]
```
</details>

### ❌ Contextual Precision
- **Score:** 0.000
- **Reason:** The score is 0.00 because all retrieved nodes are irrelevant and none address the input. The first node (rank 1) is irrelevant because it is 'a general title and does not provide any specific content about how good-practice statements differ'. The second node (rank 2) is irrelevant because its 'quoted references... address... none of these... differences in good-practice statements'. The third node (rank 3) is irrelevant because its 'quoted references provide information on... none of these... distinct principles for diagnostic testing versus treatment decisions'. Since no relevant nodes were retrieved, no relevant information could be ranked highly.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "no",
        "reason": "The context 'Guideline for the prevention, diagnosis and treatment of infertility' is a general title and does not provide any specific content about how good-practice statements differ between diagnostic testing and treatment decisions. No details are quoted to support the expected output."
    },
    {
        "verdict": "no",
        "reason": "The context lists references about cryopreservation, economic impact of IVF/ICSI, and obstetric outcomes, but none of these quoted references ('Human pregnancy following cryopreservation...', 'An international survey of the health economics of IVF...', 'The economic impact of assisted reproductive technology...', 'Obstetric and perinatal outcomes in singleton pregnancies resulting from IVF/ICSI...') address the specific differences in good-practice statements between diagnostic testing and treatment decisions as outlined in the expected output."
    },
    {
        "verdict": "no",
        "reason": "The context lists references about lifestyle factors and preconception advice ('Lifestyle factors and reproductive health...', 'The impact of lifestyle factors on reproductive performance...', 'Preconception lifestyle advice for people with infertility...'), but none of these quoted references provide information on the distinct principles for diagnostic testing (systematic, cost-effective, driven by history/exam) versus treatment decisions (balance of benefits/harms, patient preferences, cost-effectiveness) as detailed in the expected output."
    }
]
```
</details>

## 📚 Retrieval Data

<details>
<summary><strong>Retrieval Context (Chunks)</strong></summary>

**Chunk 1:**
> Guideline for the prevention, diagnosis and treatment of infertility

**Chunk 2:**
> 1. Trounson A, Mohr L. Human pregnancy following cryopreservation, thawing and transfer of an eight-cell embryo. Nature. 1983;305(5936):707-9 (https://doi.org/10.1038/305707a0). 2. Collins JA. An international survey of the health economics of IVF and ICSI. Hum Reprod Update. 2002;8(3):265-77 (https://doi.org/10.1093/ humupd/8.3.265). 3. Chambers GM, Sullivan EA, Ishihara O, Chapman MG, Adamson GD. The economic impact of assisted reproductive technology: a review of selected developed countries. Fertil Steril. 2009;91(6):2281-94 (https://doi. org/10.1016/j.fertnstert.2009.04.029). 4. Pandey S, Shetty A, Hamilton M, Bhattacharya S, Maheshwari A. Obstetric and perinatal outcomes in singleton pregnancies resulting from IVF/ICSI: a systematic review and meta-analysis. Hum Reprod Update. 2012;18(5):485-503 (https://doi. org/10.1093/humupd/dms018). ## Research gaps and future guideline update

**Chunk 3:**
> 1. Sharma R, Biedenharn KR, Fedor JM, Agarwal A. Lifestyle factors and reproductive health: taking control of your fertility. Reprod Biol Endocrinol. 2013;11:66 (https://doi.org/10.1186/1477-782711-66). 2. Homan GF, Davies M, Norman R. The impact of lifestyle factors on reproductive performance in the general population and those undergoing infertility treatment: a review. Hum Reprod Update. 2007;13(3):209-23 (https://doi. org/10.1093/humupd/dml056). 3. Boedt T, Vanhove AC, Vercoe MA, Matthys C, Dancet E, Lie Fong S. Preconception lifestyle advice for people with infertility. Cochrane Database Syst Rev. 2021;(4):CD008189 (https:// doi.org/10.1002/14651858.CD008189.pub3). according to prevalent lifestyle risks and audience preferences in different settings. ## Research gaps and future guideline update

</details>

**Actual LLM Output:**

> Based solely on the provided documents, I cannot answer your question about how good practice statements for infertility management differ between diagnostic testing and treatment decisions.

The retrieved documents contain a general guideline title and several reference lists pertaining to economic impact, obstetric outcomes, and lifestyle factors in infertility. None of the text excerpts address the specific differences in practice statements, diagnostic testing protocols, or treatment decision-making criteria that your query requires.

**Therefore, the necessary information to compare these aspects is not present in the provided context.**

---

# 🧪 Test Case: test_case_0

**Status:** ❌ **FAILED**

**Input Query:**
> *"How does WHO define infertility, and what duration of unprotected intercourse does it specify?"*

---

## 📊 Metrics Summary

| Metric Name | Score | Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Answer Relevancy** | 1.000 | 0.700 | ✅ Pass |
| **Faithfulness** | 0.500 | 0.700 | ❌ Fail |
| **Contextual Relevancy** | 0.231 | 0.700 | ❌ Fail |
| **Contextual Recall** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Precision** | 1.000 | 0.700 | ✅ Pass |

---

## 🔍 Detailed Analysis

### ✅ Answer Relevancy
- **Score:** 1.000
- **Reason:** The score is 1.00 because the output perfectly and directly addresses both parts of the input question—providing WHO's definition of infertility and the specific duration of unprotected intercourse—with no irrelevant or extraneous information. Excellent work!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Statements:
[
    "According to WHO, infertility is defined as a disease of the male and female reproductive system characterized by the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse.",
    "Another document states the definition as the failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ❌ Faithfulness
- **Score:** 0.500
- **Reason:** The score is 0.50 because the actual output incorrectly merges two separate statements from the retrieval context into WHO's definition. While the context states WHO defines infertility specifically as 'failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse,' the actual output incorrectly presents the definition as 'a disease of the male and female reproductive system characterized by...', which is a separate fact from the context, not part of WHO's official definition.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Truths (limit=None):
[
    "Infertility is a disease of the male and female reproductive system.",
    "Infertility is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse.",
    "Infertility can be primary or secondary.",
    "Primary infertility is when a pregnancy has never been achieved.",
    "Secondary infertility is when at least one prior pregnancy has been achieved.",
    "Individuals and couples have the right to decide the number, timing and spacing of their children.",
    "Persons of full age, without any limitation due to race, nationality or religion, have the right to marry and found a family.",
    "There is a gap between desired and actual fertility in many settings.",
    "Addressing infertility is an important part of enabling individuals and couples to achieve their fertility preferences.",
    "Evaluation of both the female and male partners is initiated simultaneously to provide prompt diagnosis of infertility before commencing treatment.",
    "A diagnosis of infertility is arrived at if there is failure to achieve a pregnancy after 12 months of unprotected intercourse.",
    "WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse.",
    "The basic evaluation and management of infertility includes several components.",
    "The text references a guideline for the prevention, diagnosis and treatment of infertility."
] 
 
Claims:
[
    "According to WHO, infertility is defined as a disease of the male and female reproductive system characterized by the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse.",
    "Another document states the definition of infertility as the failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse."
] 
 
Verdicts:
[
    {
        "verdict": "no",
        "reason": "The claim incorrectly states WHO defines infertility as 'a disease of the male and female reproductive system characterized by...' The retrieval context states WHO defines infertility as 'failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse.' While the context does mention infertility is a disease of the reproductive system, this is presented as a separate fact, not as part of WHO's specific definition. The claim merges two separate statements from the context."
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ❌ Contextual Relevancy
- **Score:** 0.231
- **Reason:** The score is 0.23 because, while the retrieval context contained the exact relevant statements, such as 'WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse', the vast majority of the retrieved information was irrelevant. The reasons for irrelevancy list numerous off-topic points, including discussions of 'primary or secondary' classifications, 'rights', 'evaluation processes', and 'management components', which do not address the specific query asking for the definition and duration.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdicts": [
            {
                "statement": "Infertility is a disease of the male and female reproductive system, which is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "Infertility can be primary or secondary.",
                "verdict": "no",
                "reason": "The input specifically asks for WHO's definition and the duration specified, not for classifications like 'primary or secondary'."
            },
            {
                "statement": "Primary infertility is when a pregnancy has never been achieved, and secondary infertility is when at least one prior pregnancy has been achieved.",
                "verdict": "no",
                "reason": "The input asks for the definition and duration, not the distinction between 'primary' and 'secondary' infertility."
            },
            {
                "statement": "Individuals and couples have the right to decide the number, timing and spacing of their children.",
                "verdict": "no",
                "reason": "The input asks for the definition and duration, not about 'rights' related to family planning."
            },
            {
                "statement": "Persons of full age, without any limitation due to race, nationality or religion, have the right to marry and found a family.",
                "verdict": "no",
                "reason": "The input asks for the definition and duration, not about 'rights to marry and found a family'."
            },
            {
                "statement": "There is a gap between desired and actual fertility in many settings, implying constraints to people's ability to realize their reproductive goals because of several reasons that may include infertility.",
                "verdict": "no",
                "reason": "The input asks for the definition and duration, not about 'gaps between desired and actual fertility' or 'constraints to reproductive goals'."
            },
            {
                "statement": "Addressing infertility is an important part of enabling individuals and couples to achieve their fertility preferences.",
                "verdict": "no",
                "reason": "The input asks for the definition and duration, not about the 'importance of addressing infertility'."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "Evaluation of both the female and male partners is initiated simultaneously to provide prompt diagnosis of infertility before commencing treatment.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'Evaluation of both the female and male partners is initiated simultaneously to provide prompt diagnosis of infertility before commencing treatment' when the input specifically asks for WHO's definition and the specified duration, not the evaluation process."
            },
            {
                "statement": "A diagnosis of infertility is arrived at if there is failure to achieve a pregnancy after 12 months of unprotected intercourse.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "Factors in order to enhance the chances of achieving a pregnancy.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'factors in order to enhance the chances of achieving a pregnancy' when the input asks for the definition and duration, not factors for enhancing pregnancy chances."
            },
            {
                "statement": "The basic evaluation and management of infertility includes the following components.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'The basic evaluation and management of infertility includes the following components' when the input asks for the definition and duration, not the components of evaluation and management."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "Guideline for the prevention, diagnosis and treatment of infertility",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'Guideline for the prevention, diagnosis and treatment of infertility' when it has no actual content or statements about WHO's definition of infertility or the specified duration of unprotected intercourse."
            }
        ]
    }
]
```
</details>

### ✅ Contextual Recall
- **Score:** 1.000
- **Reason:** The score is 1.00 because every part of the expected output is fully supported by the retrieval context. Specifically, the definition and criteria in the output sentence are directly reflected in node 1 and node 2 in retrieval context.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The sentence can be attributed to the 1st node ('Infertility is a disease of the male and female reproductive system...failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse') and the 2nd node ('WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse').",
        "expected_output": "The WHO defines infertility as a disease of the male and female reproductive system that is \u201cthe failure to achieve a pregnancy after\u202f12\u202fmonths of regular unprotected sexual intercourse.\u201d\u3010Context\u3011"
    }
]
```
</details>

### ✅ Contextual Precision
- **Score:** 1.000
- **Reason:** The score is 1.00 because all relevant nodes are perfectly ranked above the irrelevant node. The first node directly provides the WHO definition and 12-month duration, and the second node confirms it. The irrelevant third node, which lacks the specific definition and duration, is correctly ranked last.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The first document directly provides the WHO definition: 'Infertility is a disease of the male and female reproductive system, which is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse.' This matches the expected output exactly."
    },
    {
        "verdict": "yes",
        "reason": "The second document states: 'A diagnosis of infertility is arrived at if there is failure to achieve a pregnancy after 12 months of unprotected intercourse' and 'WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse.' This confirms both the definition and the 12-month duration."
    },
    {
        "verdict": "no",
        "reason": "The third document only mentions 'Guideline for the prevention, diagnosis and treatment of infertility' without providing the specific WHO definition or the 12-month duration requested in the input. It is too general and lacks the precise information needed."
    }
]
```
</details>

## 📚 Retrieval Data

<details>
<summary><strong>Retrieval Context (Chunks)</strong></summary>

**Chunk 1:**
> Infertility is a disease of the male and female reproductive system, which is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse (1, 2) . Infertility can be primary or secondary. Primary infertility is when a pregnancy has never been achieved, and secondary infertility is when at least one prior pregnancy has been achieved. Individuals and couples have the right to decide the number, timing and spacing of their children (3) . Persons of full age, without any limitation due to race, nationality or religion, have the right to marry and found a family (4) . However, there is a gap between desired and actual fertility in many settings (5) , implying constraints to people's ability to realize their reproductive goals because of several reasons that may include infertility. Therefore, addressing infertility is an important part of enabling individuals and couples to achieve their fertility preferences. Addressing infertility will enable individuals and couples

**Chunk 2:**
> Evaluation of both the female and male partners is initiated simultaneously to provide prompt diagnosis of infertility before commencing treatment. A diagnosis of infertility is arrived at if there is failure to achieve a pregnancy after 12 months of unprotected intercourse (1) . factors in order to enhance the chances of achieving a pregnancy. <!-- image --> WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse. ## 3.3 Elements of evaluation and management ## Fig. 3.1. Elements of evaluation and management The basic evaluation and management of infertility includes the following components: <!-- image --> <!-- image --> ## Initial consultation

**Chunk 3:**
> Guideline for the prevention, diagnosis and treatment of infertility

</details>

**Actual LLM Output:**

> According to WHO, infertility is defined as a disease of the male and female reproductive system characterized by the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse [0](9789240115774-eng.pdf). Another document states the definition as the failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse [1](9789240115774-eng.pdf).

---

# 🧪 Test Case: test_case_3

**Status:** ❌ **FAILED**

**Input Query:**
> *"Which clinicians, policymakers, and NGOs are primary users of the WHO infertility guideline?"*

---

## 📊 Metrics Summary

| Metric Name | Score | Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Answer Relevancy** | 1.000 | 0.700 | ✅ Pass |
| **Faithfulness** | 0.500 | 0.700 | ❌ Fail |
| **Contextual Relevancy** | 0.429 | 0.700 | ❌ Fail |
| **Contextual Recall** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Precision** | 0.333 | 0.700 | ❌ Fail |

---

## 🔍 Detailed Analysis

### ✅ Answer Relevancy
- **Score:** 1.000
- **Reason:** The score is 1.00 because the output directly and comprehensively addresses the specific question by listing the primary user groups (clinicians, policymakers, NGOs) as requested, with no irrelevant or off-topic information.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Statements:
[
    "The primary users of the WHO infertility guideline include several groups.",
    "Health care professionals involved in fertility care are primary users.",
    "Physicians are primary users.",
    "Embryologists are primary users.",
    "Nurses are primary users.",
    "Midwives are primary users.",
    "Laboratory specialists are primary users.",
    "Policy-makers responsible for developing national health policies, services, and financing are primary users.",
    "Various non-governmental organizations are primary users.",
    "Professional patient support and advocacy organizations are primary users.",
    "Funding and philanthropic agencies are primary users.",
    "Civil society and professional societies are primary users.",
    "Other NGOs that provide social, financial, and technical support to reproductive health programmes are primary users.",
    "The guideline is intended for these users.",
    "The guideline can also serve as an advocacy tool for evidence-based fertility care."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "idk",
        "reason": "The input specifically asks about clinicians, policymakers, and NGOs. Funding/philanthropic agencies are not explicitly mentioned in the input categories."
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "idk",
        "reason": "This statement is about the guideline's intended purpose rather than directly identifying specific user groups."
    },
    {
        "verdict": "idk",
        "reason": "This statement describes a potential use of the guideline rather than directly identifying specific user groups."
    }
]
```
</details>

### ❌ Faithfulness
- **Score:** 0.500
- **Reason:** The score is 0.50 because the actual output incorrectly states that certain organizations are 'primary users' of the guideline, while the retrieval context repeatedly clarifies that the guideline 'may be used to inform the work of' those organizations, which is a less definitive and more permissive relationship.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Truths (limit=None):
[
    "The text references a WHO report titled 'Infertility prevalence estimates: 1990-2021' published in 2023.",
    "The text references a WHO document titled 'The selection and use of essential medicines 2023: web annex A: World Health Organization model list of essential medicines: 23rd list (2023)'.",
    "The text references a WHO report titled 'The selection and use of essential in vitro diagnostics: report of the fourth meeting of the WHO Strategic Advisory Group of Experts on In Vitro Diagnostics, 2022' published in 2023.",
    "The text references a Lancet article by Mburu G, Kiarie J, Allotey P titled 'Towards a nuanced view and response to global fertility trends' published in 2024.",
    "The text includes a chapter titled 'Research gaps, future scope and updating the guideline'.",
    "The text presents a document titled 'Guideline for the prevention, diagnosis and treatment of infertility'.",
    "The guideline is primarily intended for use by health care professionals involved in the provision of fertility care.",
    "The listed health care professionals include physicians, embryologists, nurses, midwives, laboratory specialists and other health care providers.",
    "The guideline is of interest to policy-makers responsible for developing national health policies, services, and financing.",
    "The guideline's recommendations use a population perspective that considers resource considerations, acceptability, feasibility, and impact on equity.",
    "The guideline may be used to inform the work of professional patient support and advocacy organizations.",
    "The guideline may be used to inform funding and philanthropic agencies, civil society, professional societies, and other nongovernmental organizations.",
    "These organizations provide social, financial, and technical support to reproductive health programmes.",
    "The guideline can be used as an advocacy tool for evidence-based fertility care for everyone."
] 
 
Claims:
[
    "The primary users of the WHO infertility guideline include health care professionals involved in fertility care, such as physicians, embryologists, nurses, midwives, and laboratory specialists.",
    "The primary users of the WHO infertility guideline include policy-makers responsible for developing national health policies, services, and financing.",
    "The primary users of the WHO infertility guideline include various non-governmental organizations, including professional patient support and advocacy organizations.",
    "The primary users of the WHO infertility guideline include various non-governmental organizations, including funding and philanthropic agencies.",
    "The primary users of the WHO infertility guideline include various non-governmental organizations, including civil society and professional societies.",
    "The primary users of the WHO infertility guideline include various non-governmental organizations, including other NGOs that provide social, financial, and technical support to reproductive health programmes.",
    "The WHO infertility guideline is intended for these users.",
    "The WHO infertility guideline can also serve as an advocacy tool for evidence-based fertility care."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "no",
        "reason": "The context states the guideline 'may be used to inform the work of' these organizations, not that they are 'primary users'."
    },
    {
        "verdict": "no",
        "reason": "The context states the guideline 'may be used to inform' these agencies, not that they are 'primary users'."
    },
    {
        "verdict": "no",
        "reason": "The context states the guideline 'may be used to inform' these groups, not that they are 'primary users'."
    },
    {
        "verdict": "no",
        "reason": "The context states the guideline 'may be used to inform' these NGOs, not that they are 'primary users'."
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ❌ Contextual Relevancy
- **Score:** 0.429
- **Reason:** The score is 0.43 because while the relevant statements identify policymakers and NGOs as interested parties, they do not explicitly list them as 'primary users' alongside clinicians. The irrelevancy reasons correctly note that the context contains only a chapter heading and a title, and that the mention of 'health care professionals' as primary intended users doesn't fully match the input's request for a specific list of all three categories equally.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdicts": [
            {
                "statement": "The context consists of four bibliographic citations and a chapter heading.",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'The context consists of four bibliographic citations and a chapter heading' when it has nothing to do with identifying primary users of the WHO infertility guideline."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "Guideline for the prevention, diagnosis and treatment of infertility",
                "verdict": "no",
                "reason": "The retrieval context contained the information 'Guideline for the prevention, diagnosis and treatment of infertility' which is only the title of the guideline and does not identify any specific clinicians, policymakers, or NGOs as primary users."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "This guideline is primarily intended for use by health care professionals (including physicians, embryologists, nurses, midwives, laboratory specialists and other health care providers) involved in the provision of fertility care.",
                "verdict": "no",
                "reason": "The input specifically asks about 'clinicians, policymakers, and NGOs' as primary users. While this statement mentions 'health care professionals' (clinicians), it describes them as the guideline's primary intended users, whereas the input asks for a list of primary user groups including all three categories equally. The statement's focus on 'primarily intended for use by health care professionals' does not fully match the input's request for which clinicians, policymakers, and NGOs are primary users."
            },
            {
                "statement": "This guideline is of interest to policy-makers responsible for the development of national health (and other) policies, services and financing because its recommendations use a population perspective that considers resource considerations, acceptability, feasibility and impact on equity.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "This guideline may be used to inform the work of professional patient support, as well as advocacy organizations, funding and philanthropic agencies, civil society, professional societies and other nongovernmental organizations that provide social, financial and technical support to reproductive health programmes.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "The guideline can also be used as an advocacy tool for evidence-based fertility care for everyone.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "Guideline for the prevention, diagnosis and treatment of infertility",
                "verdict": "no",
                "reason": "The phrase 'Guideline for the prevention, diagnosis and treatment of infertility' is a title or descriptor of the document and does not provide information about which specific user groups (clinicians, policymakers, NGOs) are primary users."
            }
        ]
    }
]
```
</details>

### ✅ Contextual Recall
- **Score:** 1.000
- **Reason:** The score is 1.00 because every target audience listed in the expected output is fully supported by node 2 in the retrieval context: clinicians (sentence 1), policymakers (sentence 2), and NGOs/civil-society groups (sentence 3). Perfect match!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The 2nd node states: 'This guideline is primarily intended for use by health care professionals (including physicians, embryologists, nurses, midwives, laboratory specialists and other health care providers) involved in the provision of fertility care.' This directly matches the target audience of clinicians.",
        "expected_output": "The WHO infertility guideline is aimed at:\n\n* **Clinicians** \u2013 physicians, embryologists, nurses, midwives, laboratory specialists and other health\u2011care providers who deliver fertility care.  \n* **Policymakers** \u2013 officials and decision\u2011makers who design, fund and regulate national health (and related) policies, services and financing for reproductive health.  \n* **NGOs and civil\u2011society groups** \u2013 patient\u2011support organisations, advocacy bodies, professional societies, funding and philanthropic agencies, and other nongovernmental organisations that provide social, financial or technical support to reproductive\u2011health programmes."
    },
    {
        "verdict": "yes",
        "reason": "The 2nd node states: 'This guideline is of interest to policy-makers responsible for the development of national health (and other) policies, services and financing...' This directly matches the target audience of policymakers.",
        "expected_output": "The WHO infertility guideline is aimed at:\n\n* **Clinicians** \u2013 physicians, embryologists, nurses, midwives, laboratory specialists and other health\u2011care providers who deliver fertility care.  \n* **Policymakers** \u2013 officials and decision\u2011makers who design, fund and regulate national health (and related) policies, services and financing for reproductive health.  \n* **NGOs and civil\u2011society groups** \u2013 patient\u2011support organisations, advocacy bodies, professional societies, funding and philanthropic agencies, and other nongovernmental organisations that provide social, financial or technical support to reproductive\u2011health programmes."
    },
    {
        "verdict": "yes",
        "reason": "The 2nd node states: 'This guideline may be used to inform the work of professional patient support, as well as advocacy organizations, funding and philanthropic agencies, civil society, professional societies and other nongovernmental organizations...' This directly matches the target audience of NGOs and civil-society groups.",
        "expected_output": "The WHO infertility guideline is aimed at:\n\n* **Clinicians** \u2013 physicians, embryologists, nurses, midwives, laboratory specialists and other health\u2011care providers who deliver fertility care.  \n* **Policymakers** \u2013 officials and decision\u2011makers who design, fund and regulate national health (and related) policies, services and financing for reproductive health.  \n* **NGOs and civil\u2011society groups** \u2013 patient\u2011support organisations, advocacy bodies, professional societies, funding and philanthropic agencies, and other nongovernmental organisations that provide social, financial or technical support to reproductive\u2011health programmes."
    }
]
```
</details>

### ❌ Contextual Precision
- **Score:** 0.333
- **Reason:** The score is 0.33 because only one relevant node (rank 3) directly answers the question by listing clinicians, policymakers, and NGOs as primary users. However, two irrelevant nodes are ranked higher (ranks 1 and 2). The first node is irrelevant as it 'lists several WHO reports... but none directly address the primary users', and the second node is irrelevant as it 'identifies the document but provides no information about its intended users'. Since relevant information should be prioritized, the relevant node should be ranked above these two irrelevant ones.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "no",
        "reason": "The context lists several WHO reports and a Lancet article, but none directly address the primary users of the WHO infertility guideline. It mentions 'Chapter 12 Research gaps' but provides no specific information about clinicians, policymakers, or NGOs as users."
    },
    {
        "verdict": "no",
        "reason": "The title 'Guideline for the prevention, diagnosis and treatment of infertility' identifies the document but provides no information about its intended users."
    },
    {
        "verdict": "yes",
        "reason": "This context directly answers the question. It states the guideline is 'primarily intended for use by health care professionals (including physicians, embryologists, nurses, midwives, laboratory specialists and other health care providers)' (clinicians), is 'of interest to policy-makers responsible for the development of national health... policies', and 'may be used to inform the work of professional patient support, as well as advocacy organizations... and other nongovernmental organizations' (NGOs/civil society)."
    }
]
```
</details>

## 📚 Retrieval Data

<details>
<summary><strong>Retrieval Context (Chunks)</strong></summary>

**Chunk 1:**
> 1. Infertility prevalence estimates: 1990-2021. Geneva: World Health Organization; 2023 (https://apps.who.int/iris/handle/10665/366700). 2. The selection and use of essential medicines 2023: web annex A: World Health Organization model list of essential medicines: 23rd list (2023). Geneva: World Health Organization; 2023 (https://iris.who.int/handle/10665/371090). 3. The selection and use of essential in vitro diagnostics: report of the fourth meeting of the WHO Strategic Advisory Group of Experts on In Vitro Diagnostics, 2022 (including the fourth WHO model list of essential in vitro diagnostics). Geneva: World Health Organization; 2023 (https://iris.who.int/handle/10665/373322). 4. Mburu G, Kiarie J, Allotey P. Towards a nuanced view and response to global fertility trends. Lancet. 2024;403(10440):1953-56 ( https://doi. org/10.1016/s0140-6736(24)00490-2). <!-- image --> ## Chapter ## 12 Research gaps, future scope and updating the guideline

**Chunk 2:**
> Guideline for the prevention, diagnosis and treatment of infertility

**Chunk 3:**
> This guideline is primarily intended for use by health care professionals (including physicians, embryologists, nurses, midwives, laboratory specialists and other health care providers) involved in the provision of fertility care. This guideline is of interest to policy-makers responsible for the development of national health (and other) policies, services and financing because its recommendations use a population perspective that considers resource considerations, acceptability, feasibility and impact on equity. This guideline may be used to inform the work of professional patient support, as well as advocacy organizations, funding and philanthropic agencies, civil society, professional societies and other nongovernmental organizations that provide social, financial and technical support to reproductive health programmes. The guideline can also be used as an advocacy tool for evidence-based fertility care for everyone. Guideline for the prevention, diagnosis and treatment of infertility

</details>

**Actual LLM Output:**

> The primary users of the WHO infertility guideline include several groups:

1.  **Health care professionals** involved in fertility care, such as **physicians, embryologists, nurses, midwives, and laboratory specialists** [\[2\]](9789240115774-eng.pdf).
2.  **Policy-makers** responsible for developing national health policies, services, and financing [\[2\]](9789240115774-eng.pdf).
3.  Various **non-governmental organizations**, including:
    *   Professional patient support and advocacy organizations.
    *   Funding and philanthropic agencies.
    *   Civil society and professional societies.
    *   Other NGOs that provide social, financial, and technical support to reproductive health programmes [\[2\]](9789240115774-eng.pdf).

The guideline is intended for these users and can also serve as an advocacy tool for evidence-based fertility care [\[2\]](9789240115774-eng.pdf).

---

# 🧪 Test Case: test_case_1

**Status:** ❌ **FAILED**

**Input Query:**
> *"If reproductive‑age population doubled, how many additional infertile individuals arise from the 1‑in‑6 rate?"*

---

## 📊 Metrics Summary

| Metric Name | Score | Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Answer Relevancy** | 1.000 | 0.700 | ✅ Pass |
| **Faithfulness** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Relevancy** | 0.143 | 0.700 | ❌ Fail |
| **Contextual Recall** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Precision** | 1.000 | 0.700 | ✅ Pass |

---

## 🔍 Detailed Analysis

### ✅ Answer Relevancy
- **Score:** 1.000
- **Reason:** The score is 1.00 because the output directly and completely addresses the precise calculation requested in the input, with no irrelevant statements or off-topic information.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Statements:
[
    "If the reproductive‑age population doubled, and a 1‑in‑6 (approximately 17 %) infertility rate continues to apply, the number of additional infertile individuals would be equal to the size of the original population multiplied by that rate.",
    "Specifically, if we denote the original reproductive‑age population as *P*, the initial number of infertile individuals is about *P* × (1/6).",
    "After doubling, the new population is 2*P*.",
    "The new number of infertile individuals would be 2*P* × (1/6) = *P* × (1/3).",
    "The **additional** infertile individuals are therefore: (*P* × 1/3) – (*P* × 1/6) = *P* × (1/6).",
    "Thus, doubling the population would produce an **extra infertile cohort equal to the original number of infertile individuals**.",
    "The extra infertile cohort is one‑sixth of the original reproductive‑age population.",
    "This calculation assumes the infertility rate remains unchanged.",
    "This calculation assumes that “reproductive‑age population” is defined consistently.",
    "The 1‑in‑6 infertility rate among people of reproductive age is reported in the retrieved document [0](9789240115774-eng.pdf)."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "idk",
        "reason": "The statement clarifies an assumption behind the calculation, which is indirectly relevant as supporting information but not a direct step in answering the core question."
    },
    {
        "verdict": "idk",
        "reason": "The statement clarifies an assumption about definitions, which is indirectly relevant as supporting information but not a direct step in answering the core question."
    },
    {
        "verdict": "idk",
        "reason": "The statement provides a source citation for the infertility rate, which is supporting information but not a direct part of the mathematical answer to the question."
    }
]
```
</details>

### ✅ Faithfulness
- **Score:** 1.000
- **Reason:** The score is 1.00 because there are no contradictions listed, indicating the actual output is fully aligned with and faithfully reflects the information in the retrieval context. Great job!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Truths (limit=None):
[
    "Globally, approximately one in six people of reproductive age experience infertility at some stage in their lives.",
    "The lifetime prevalence of infertility is 17.5%.",
    "The period prevalence of infertility is 12.6%.",
    "Infertility prevalence does not differ significantly between high-income and low- and middle-income countries (LMICs).",
    "Infertility prevalence does not differ significantly according to world regions.",
    "Infertility is a global public health issue affecting people in all regions and countries.",
    "The overall period and lifetime prevalence of infertility is similar across regions.",
    "The distribution of the underlying risks of infertility can vary across countries and regions.",
    "Examples of underlying risks of infertility include postpartum infections, unsafe abortions, and some sexually transmitted infections (STIs).",
    "The variation in underlying risks can potentially cause differences in the patterns of primary versus secondary infertility.",
    "Different definitions and methodological approaches are used to estimate the number of people affected by infertility.",
    "The number of people affected by infertility was estimated to be 186 million individuals in 2004.",
    "The number of people affected by infertility was estimated to be 48.5 million individuals (in an unspecified year)."
] 
 
Claims:
[
    "If the reproductive-age population doubled, and a 1-in-6 (approximately 17%) infertility rate continues to apply, the number of additional infertile individuals would be equal to the size of the original population multiplied by that rate.",
    "If we denote the original reproductive-age population as P, the initial number of infertile individuals is about P × (1/6).",
    "After doubling, the new population is 2P, so the new number of infertile individuals would be 2P × (1/6) = P × (1/3).",
    "The additional infertile individuals are therefore: (P × 1/3) – (P × 1/6) = P × (1/6).",
    "Doubling the population would produce an extra infertile cohort equal to the original number of infertile individuals, i.e., one-sixth of the original reproductive-age population.",
    "This calculation assumes the infertility rate remains unchanged and that 'reproductive-age population' is defined consistently.",
    "The 1-in-6 infertility rate among people of reproductive age is reported in the retrieved document [0](9789240115774-eng.pdf)."
] 
 
Verdicts:
[
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    },
    {
        "verdict": "yes",
        "reason": null
    }
]
```
</details>

### ❌ Contextual Relevancy
- **Score:** 0.143
- **Reason:** The score is 0.14 because only one statement ('Globally, approximately one in six people of reproductive age experience infertility at some stage in their lives.') provides the necessary '1-in-6' rate for the calculation, while the rest of the context is filled with irrelevant details such as geographic comparisons, historical estimates, risk factor distributions, and citation information that do not help answer the quantitative, hypothetical question.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdicts": [
            {
                "statement": "Globally, approximately one in six people of reproductive age experience infertility at some stage in their lives.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "Lifetime prevalence of infertility is 17.5%, while period prevalence is 12.6%.",
                "verdict": "no",
                "reason": "The input asks specifically about the '1-in-6 rate' and its implications if population doubles, but the statement 'Lifetime prevalence of infertility is 17.5%, while period prevalence is 12.6%' provides additional prevalence statistics that are not directly needed to answer the calculation-based question."
            },
            {
                "statement": "Infertility prevalence does not differ significantly between high-income and low- and middle-income countries (LMICs), or according to world regions, indicating that infertility is a global public health issue affecting people in all regions and countries.",
                "verdict": "no",
                "reason": "The input is a quantitative question about population doubling and the '1-in-6 rate', but the statement 'Infertility prevalence does not differ significantly between high-income and low- and middle-income countries (LMICs), or according to world regions' discusses geographic and economic comparisons irrelevant to the calculation."
            },
            {
                "statement": "Although the overall period and lifetime prevalence is similar across regions, the distribution of the underlying risks of infertility (such as postpartum infections, unsafe abortions and some sexually transmitted infections [STIs]) can vary across countries and regions and potentially cause differences in the patterns of primary versus secondary infertility.",
                "verdict": "no",
                "reason": "The input asks for a simple calculation based on a fixed rate, but the statement 'the distribution of the underlying risks of infertility (such as postpartum infections, unsafe abortions and some sexually transmitted infections [STIs]) can vary across countries and regions' introduces epidemiological details about risk factors and infertility patterns that are not relevant to the population-doubling scenario."
            },
            {
                "statement": "Using different definitions and methodological approaches, the numbers of people affected by infertility were estimated to be 186 million individuals in 2004 and 48.5 million.",
                "verdict": "no",
                "reason": "The input is a hypothetical question about a doubled reproductive-age population, but the statement 'the numbers of people affected by infertility were estimated to be 186 million individuals in 2004 and 48.5 million' provides specific historical estimates that do not help answer the forward-looking, rate-based calculation."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "The provided context consists only of a list of academic references (citations) without any actual statements, data, or explanatory content.",
                "verdict": "no",
                "reason": "No statements found in provided context."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "The context consists of four bibliographic citations (references 67-70) to academic articles on topics related to fertility, assisted reproductive technology, and gender differences in infertility.",
                "verdict": "no",
                "reason": "The retrieval context contains only citation information such as 'Lazzari E, Gray E, Chambers GM. The contribution of assisted reproductive technology to fertility rates...' and 'Mburu G, Kamuyango A, Kidula N... Fulfilment of fertility desires...'. These are references to articles, not actual statements containing the '1-in-6 rate' of infertility or data needed to calculate the effect of a doubled reproductive-age population."
            }
        ]
    }
]
```
</details>

### ✅ Contextual Recall
- **Score:** 1.000
- **Reason:** The score is 1.00 because every calculation and statement in the expected output is perfectly derived from the proportion provided in node 1 of the retrieval context. The initial proportion (P ÷ 6), the doubled scenario (2P ÷ 6), and the final additional count (P ÷ 6) all logically follow from the 'one in six' fact. Excellent work!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The 1st node states 'approximately one in six people of reproductive age experience infertility', which directly supports the claim that infertile individuals \u2248 P \u00f7 6.",
        "expected_output": "If the reproductive\u2011age population doubles, the number of people who will be infertile also doubles.  \n\n- Original population\u202f=\u202fP \u2192 infertile\u202f\u2248\u202fP\u202f\u00f7\u202f6.  \n- Doubled population\u202f=\u202f2P \u2192 infertile\u202f\u2248\u202f2P\u202f\u00f7\u202f6\u202f=\u202fP\u202f\u00f7\u202f3.  \n\nThus the **additional infertile individuals** equal the original count, i.e., **another\u202fP\u202f\u00f7\u202f6** (an extra 1\u2011in\u20116 of the original reproductive\u2011age population)."
    },
    {
        "verdict": "yes",
        "reason": "The 1st node provides the infertility proportion (one in six), allowing the logical extrapolation that if population doubles to 2P, infertile individuals \u2248 2P \u00f7 6.",
        "expected_output": "If the reproductive\u2011age population doubles, the number of people who will be infertile also doubles.  \n\n- Original population\u202f=\u202fP \u2192 infertile\u202f\u2248\u202fP\u202f\u00f7\u202f6.  \n- Doubled population\u202f=\u202f2P \u2192 infertile\u202f\u2248\u202f2P\u202f\u00f7\u202f6\u202f=\u202fP\u202f\u00f7\u202f3.  \n\nThus the **additional infertile individuals** equal the original count, i.e., **another\u202fP\u202f\u00f7\u202f6** (an extra 1\u2011in\u20116 of the original reproductive\u2011age population)."
    },
    {
        "verdict": "yes",
        "reason": "This is a mathematical conclusion derived from the proportion in the 1st node ('one in six...experience infertility'). The additional infertile = (2P \u00f7 6) - (P \u00f7 6) = P \u00f7 6.",
        "expected_output": "If the reproductive\u2011age population doubles, the number of people who will be infertile also doubles.  \n\n- Original population\u202f=\u202fP \u2192 infertile\u202f\u2248\u202fP\u202f\u00f7\u202f6.  \n- Doubled population\u202f=\u202f2P \u2192 infertile\u202f\u2248\u202f2P\u202f\u00f7\u202f6\u202f=\u202fP\u202f\u00f7\u202f3.  \n\nThus the **additional infertile individuals** equal the original count, i.e., **another\u202fP\u202f\u00f7\u202f6** (an extra 1\u2011in\u20116 of the original reproductive\u2011age population)."
    }
]
```
</details>

### ✅ Contextual Precision
- **Score:** 1.000
- **Reason:** The score is 1.00 because the single relevant node is perfectly ranked first. The relevant node (rank 1) contains the essential '1-in-6' infertility rate needed for the calculation, while both irrelevant nodes (ranks 2 and 3) are correctly ranked lower as they are 'lists of citation references' providing 'no data useful for answering the question'.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The first sentence directly provides the key rate: 'approximately one in six people of reproductive age experience infertility.' This is the essential '1-in-6 rate' referenced in the input question, which is the foundational data point needed to perform the calculation about population doubling."
    },
    {
        "verdict": "no",
        "reason": "This context is a list of citation references (e.g., '7. Kersten FA...', '8. Evers JL...') and does not contain any factual information about infertility rates, population sizes, or calculations. It is purely a reference list and provides no data useful for answering the question."
    },
    {
        "verdict": "no",
        "reason": "This context is another list of citation references (e.g., '67. Lazzari E...', '68. Mburu G...') discussing topics like assisted reproductive technology and fertility desires. It contains no information about the '1-in-6' infertility rate or any population data necessary for the mathematical reasoning required by the input."
    }
]
```
</details>

## 📚 Retrieval Data

<details>
<summary><strong>Retrieval Context (Chunks)</strong></summary>

**Chunk 1:**
> Globally, approximately one in six people of reproductive age experience infertility at some stage in their lives (6) . Lifetime prevalence of infertility is 17.5%, while period prevalence is 12.6%. In addition, infertility prevalence does not differ significantly between high-income and low- and middle-income countries (LMICs), or according to world regions, indicating that infertility is a global public health issue affecting people in all regions and countries (6) . Although the overall period and lifetime prevalence is similar across regions, the distribution of the underlying risks of infertility (such as postpartum infections, unsafe abortions and some sexually transmitted infections [STIs]) can vary across countries and regions and potentially cause differences in the patterns of primary versus secondary infertility (6-8) . Using different definitions and methodological approaches, the numbers of people affected by infertility were estimated to be 186 million individuals in 2004 (9) and 48.5 million

**Chunk 2:**
> 7. Kersten FA, Hermens RP, Braat DD, Hoek A, Mol BW, Goddijn M et al. Overtreatment in couples with unexplained infertility. Hum Reprod. 2015;30(1):71-80 (https://doi.org/10.1093/ humrep/deu262). 8. Evers JL, de Haas HW, Land JA, Dumoulin JC, Dunselman GA. Treatment-independent pregnancy rate in patients with severe reproductive disorders. Hum Reprod. 1998;13(5):1206-9 (https://doi.org/10.1093/ humrep/13.5.1206). 9. Dunson DB, Baird DD, Colombo B. Increased infertility with age in men and women. Obstet Gynecol. 2004;103(1):51-6 (https://doi. org/10.1097/01.AOG.0000100153.24061.45). 10. van der Steeg JW, Steures P, Eijkemans MJ, Habbema JD, Hompes PG, Broekmans FJ et al. Pregnancy is predictable: a large-scale prospective external validation of the prediction of spontaneous pregnancy in subfertile couples. Hum Reprod. 2007;22(2):536-42 (https://doi. org/10.1093/humrep/del378).

**Chunk 3:**
> 67. Lazzari E, Gray E, Chambers GM. The contribution of assisted reproductive technology to fertility rates and parity transition. Demogr Res. 2021;45:1081-96 (https://doi.org/10.4054/ DemRes.2021.45.35). 68. Mburu G, Kamuyango A, Kidula N, Kabra R, Thatte N, Kiarie J et al. Fulfilment of fertility desires for the attainment of Global Sustainable Development Goals. BMJ Glob Health. 2023;8(4):e012322 (https://doi.org/10.1136/ bmjgh-2023-012322). 69. Mburu G, Kiarie J, Allotey P. Towards a nuanced view and response to global fertility trends. Lancet. 2024;403(10440):1953-6 ( https://doi. org/10.1016/s0140-6736(24)00490-2). 70. Ying LY, Wu LH, Loke AY. Gender differences in experiences with and adjustments to infertility: a literature review. Int J Nurs Stud. 2015;52(10):1640-52 (https://doi.org/10.1016/j. ijnurstu.2015.05.004).

</details>

**Actual LLM Output:**

> If the reproductive‑age population doubled, and a 1‑in‑6 (approximately 17 %) infertility rate continues to apply, the number of additional infertile individuals would be equal to the size of the original population multiplied by that rate.  

Specifically, if we denote the original reproductive‑age population as *P*, the initial number of infertile individuals is about *P* × (1/6). After doubling, the new population is 2*P*, so the new number of infertile individuals would be 2*P* × (1/6) = *P* × (1/3). The **additional** infertile individuals are therefore:  

*(P* × 1/3) – (*P* × 1/6) = *P* × (1/6).

Thus, doubling the population would produce an **extra infertile cohort equal to the original number of infertile individuals**, i.e., one‑sixth of the original reproductive‑age population.  

*Note: This calculation assumes the infertility rate remains unchanged and that “reproductive‑age population” is defined consistently.*  

**Citation:** The 1‑in‑6 infertility rate among people of reproductive age is reported in the retrieved document [0](9789240115774-eng.pdf).

---

