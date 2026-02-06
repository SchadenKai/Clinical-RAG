# 🧪 Test Case: test_case_0

**Status:** ❌ **FAILED**

**Input Query:**
> *"How does WHO define infertility, and what duration of unprotected intercourse does it specify?"*

---

## 📊 Metrics Summary

| Metric Name | Score | Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Answer Relevancy** | 1.000 | 0.700 | ✅ Pass |
| **Faithfulness** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Relevancy** | 0.214 | 0.700 | ❌ Fail |
| **Contextual Recall** | 1.000 | 0.700 | ✅ Pass |
| **Contextual Precision** | 1.000 | 0.700 | ✅ Pass |

---

## 🔍 Detailed Analysis

### ✅ Answer Relevancy
- **Score:** 1.000
- **Reason:** The score is 1.00 because the response directly answered the WHO definition of infertility and the specified duration of unprotected intercourse with no irrelevant material.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Statements:
[
    "The World Health Organization defines infertility as a disease of the male and female reproductive system.",
    "Infertility is the failure to achieve a pregnancy after 12 months (or more) of regular unprotected sexual intercourse."
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

### ✅ Faithfulness
- **Score:** 1.000
- **Reason:** The score is 1.00 because there are no contradictions, indicating the actual output fully aligns with the retrieval context. Great job!

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Truths (limit=None):
[
    "Infertility is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse.",
    "Infertility can be classified as primary or secondary.",
    "Primary infertility is when a pregnancy has never been achieved.",
    "Secondary infertility is when at least one prior pregnancy has been achieved.",
    "Individuals and couples have the right to decide the number, timing, and spacing of their children.",
    "Persons of full age, without limitation due to race, nationality, or religion, have the right to marry and found a family.",
    "There is a gap between desired and actual fertility in many settings.",
    "Addressing infertility is an important part of enabling individuals and couples to achieve their fertility preferences.",
    "Evaluation of both the female and male partners is initiated simultaneously to provide prompt diagnosis of infertility before commencing treatment.",
    "A diagnosis of infertility is arrived at if there is failure to achieve a pregnancy after 12 months of unprotected intercourse.",
    "The World Health Organization defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse.",
    "The basic evaluation and management of infertility includes several components outlined in guidelines.",
    "The guideline covers prevention, diagnosis, and treatment of infertility."
] 
 
Claims:
[
    "The World Health Organization defines infertility as a disease of the male and female reproductive system that is the failure to achieve a pregnancy after 12 months (or more) of regular unprotected sexual intercourse."
] 
 
Verdicts:
[
    {
        "verdict": "idk",
        "reason": "The retrieval context defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse, but it does not state that infertility is a disease of the male and female reproductive system, so the claim is not directly supported by the provided context."
    }
]
```
</details>

### ❌ Contextual Relevancy
- **Score:** 0.214
- **Reason:** The score is 0.21 because most of the retrieved context is unrelated—e.g., "Infertility can be primary or secondary" and "The focus on marriage rights is irrelevant to the WHO definition"—while only a few statements actually address the WHO definition, such as "Infertility is a disease of the male and female reproductive system, which is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse" and "WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse." The predominance of irrelevant content drives the low relevancy score.

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
                "reason": "The statement \"Infertility can be primary or secondary\" does not address how WHO defines infertility or the specified duration of unprotected intercourse."
            },
            {
                "statement": "Primary infertility is when a pregnancy has never been achieved, and secondary infertility is when at least one prior pregnancy has been achieved.",
                "verdict": "no",
                "reason": "The details about primary and secondary infertility are unrelated to the WHO definition or the 12\u2011month duration requirement."
            },
            {
                "statement": "Individuals and couples have the right to decide the number, timing and spacing of their children.",
                "verdict": "no",
                "reason": "This statement concerns reproductive rights, not the WHO definition of infertility or the duration of unprotected intercourse."
            },
            {
                "statement": "Persons of full age, without any limitation due to race, nationality or religion, have the right to marry and founded a family.",
                "verdict": "no",
                "reason": "The focus on marriage rights is irrelevant to the WHO definition of infertility and its time frame."
            },
            {
                "statement": "There is a gap between desired and actual fertility in many settings, implying constraints to people's ability to realize their reproductive goals because of several reasons that may include infertility.",
                "verdict": "no",
                "reason": "This observation about fertility gaps does not provide the WHO definition or the specified 12\u2011month period."
            },
            {
                "statement": "Addressing infertility is an important part of enabling individuals and couples to achieve their fertility preferences.",
                "verdict": "no",
                "reason": "While related to infertility, this statement does not specify the WHO definition or the duration of unprotected intercourse."
            },
            {
                "statement": "Addressing infertility will enable individuals and couples",
                "verdict": "no",
                "reason": "The incomplete statement about addressing infertility does not contain the WHO definition or duration information."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "Evaluation of both the female and male partners is initiated simultaneously to provide prompt diagnosis of infertility before commencing treatment.",
                "verdict": "no",
                "reason": "The statement focuses on the evaluation process ('Evaluation of both the female and male partners is initiated simultaneously...') and does not address WHO's definition of infertility or the specified duration of unprotected intercourse."
            },
            {
                "statement": "A diagnosis of infertility is arrived at if there is failure to achieve a pregnancy after 12 months of unprotected intercourse.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse.",
                "verdict": "yes",
                "reason": null
            },
            {
                "statement": "The basic evaluation and management of infertility includes the following components:",
                "verdict": "no",
                "reason": "This statement describes components of evaluation and management ('The basic evaluation and management of infertility includes the following components') and does not provide WHO's definition or the duration requirement."
            },
            {
                "statement": "Initial consultation",
                "verdict": "no",
                "reason": "The phrase 'Initial consultation' is merely a heading and contains no information about WHO's definition or the duration of unprotected intercourse."
            }
        ]
    },
    {
        "verdicts": [
            {
                "statement": "Guideline for the prevention, diagnosis and treatment of infertility",
                "verdict": "no",
                "reason": "No statements found in provided context."
            }
        ]
    }
]
```
</details>

### ✅ Contextual Recall
- **Score:** 1.000
- **Reason:** The score is 1.00 because sentence 1 is directly supported by node 1 and node 2 in the retrieval context, perfectly matching the expected definition.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "Matches 1st node ('Infertility is a disease of the male and female reproductive system, which is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse...') and 2nd node ('WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse...')",
        "expected_output": "The WHO defines infertility as a disease of the male and female reproductive system that is \u201cthe failure to achieve a pregnancy after\u202f12\u202fmonths of regular unprotected sexual intercourse.\u201d\u3010Context\u3011"
    }
]
```
</details>

### ✅ Contextual Precision
- **Score:** 1.000
- **Reason:** The score is 1.00 because the two relevant nodes (rank 1 and rank 2) contain the WHO definition and the 12‑month duration—"Infertility is a disease... failure to achieve a pregnancy after 12 months..." and "WHO defines infertility as failure to achieve a pregnancy after 12 months or more..."—and they are ranked before the irrelevant node (rank 3), which only mentions a guideline without any definition. This perfect ordering yields a contextual precision of 1.

<details>
<summary><strong>View Verbose Logs & Verdicts</strong></summary>

```text
Verdicts:
[
    {
        "verdict": "yes",
        "reason": "The text states: \"Infertility is a disease of the male and female reproductive system, which is defined as the failure to achieve a pregnancy after 12 months of regular unprotected sexual intercourse\" \u2013 directly providing the WHO definition and the 12\u2011month duration."
    },
    {
        "verdict": "yes",
        "reason": "It includes the sentence: \"WHO defines infertility as failure to achieve a pregnancy after 12 months or more of regular unprotected sexual intercourse,\" which matches the required definition and timeframe."
    },
    {
        "verdict": "no",
        "reason": "The entry only says \"Guideline for the prevention, diagnosis and treatment of infertility\" and does not contain any definition or duration information, so it is not useful for answering the question."
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

> The World Health Organization defines infertility as a disease of the male and female reproductive system that is **the failure to achieve a pregnancy after 12 months (or more) of regular unprotected sexual intercourse**【0](9789240115774-eng.pdf)】【1](9789240115774-eng.pdf).

---

