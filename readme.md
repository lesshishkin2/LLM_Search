# LLM_Search

This document describes my approach to the Enterprize Rag Challenge 2 competition, which secured me second place overall and a shared first prize in the speed category. The approach is notable for not utilizing traditional search tools, neither full-text nor vector-based, yet it achieved high retrieval accuracy (86.3 in the R column of the results table).

# Initial Document Processing

## File: pdf_convert_and_cleanup.py

1. To convert PDF to Markdown, I used the marker-pdf API (https://www.datalab.to/marker).
2. Minor cleanup was performed using regular expressions.

## File: get_meta_info.py

Next, we need to extract the primary currency, year, and month of the last reporting period from the documents. My approach here is straightforward—I simply send the first 100 pages of the report to o3-mini and obtain the necessary information using Structured Output.

# Answering Questions

## File: main.py

Let's illustrate the script's workflow using a fictional question: "Which company is more fun: X or Y?"

1. **Query Expansion & Company Identification**  
   Using gpt4o with Structured Output, we derive auxiliary questions from the original question as follows:
   ```
   [
       {"company": "X", "auxiliary_question": "How fun is company X?"},
       {"company": "Y", "auxiliary_question": "How fun is company Y?"}
   ]
   ```
   If the question involves only one company, the process remains unchanged, resulting in a single auxiliary question.

2. **Page Identification**  
   The most interesting part of my approach is next. For each auxiliary question, I classify each page of the relevant report using gpt4o-mini, asking whether the page contains an answer to the question "How fun is company X?"

   This employs Structured Output (SO), providing not only classification results but also the model’s reasoning chain, useful for analysis.

   The process ran using 100 parallel threads (I have Tier 3 access in OpenAI; lower tiers may struggle with this scale).

3. **Answering Auxiliary Questions**  
   This step is straightforward. We pass the auxiliary question text and the pages classified as relevant to o3-mini.

4. **Finalizing the Answer**  
   The model receives the original question along with auxiliary questions and their answers, formatted as follows:

   ```
   Original question:
   Which company is more fun: X or Y?

   Auxiliary questions and answers:
   Question: How fun is company X?
   Answer: Company X is 30% fun.

   Question: How fun is company Y?
   Answer: Company Y is 50% fun.
   ```

   This yields the final response using the required answer schema.

# Costs

- PDF to Markdown conversion: ~$43
- Meta-info extraction: ~$10
- Question answering: ~$8.50 (most expenses were from o3-mini, not from searching with gpt4o-mini)
---
Total: ~$61.50

# Run time
The script executed in approximately 40 minutes. The duration was largely due to handling a 1000-page file (trimmed to 750 pages) with at least five related questions. For 100 dry-run questions generated from the PDF, the script completed in 20 minutes.

# Analysis Tool

## File: report_creator.py

This tool generates a convenient report summarizing the entire run, allowing review of page classifications and model reasoning. To execute, point it to runs/20250227_153643/questions_with_final_answers.pkl.

