query_expansion_prompt = """
<task>
You are a top-notch specialist in rephrasing user questions. Your task is to create a series of basic questions based on the user's question, the answers to which will help answer the original question.

You will be provided with:
- A user question mentioning one or more companies requesting information about a company (e.g., financial data, positions in the company, etc.).

Your task is to:
- Identify all the company names mentioned in the question.
- For each company mentioned in the question:
    - Write the company name.
    - Specify the name of the required metric.
    - Rephrase the user's original question specifically for this company.
    
Important details:
- If multiple companies are mentioned, you must include all mentioned companies in your answer.
- Adhere to the question format in the examples.

<example>
## User question:
Which company had a higher net income: \"TSX_ACQ\", \"QUIDELORTHO CORPORATION\" or \"PowerFleet, Inc.\", in the fiscal year 2022?

## Your rephrased questions:
What was the net income of \"TSX_ACQ\" in the fiscal year 2022?
What was the net income of \"QUIDELORTHO CORPORATION\" in the fiscal year 2022?
What was the net income of \"PowerFleet, Inc.\" in the fiscal year 2022?
</example>

</task>

<user_question>
{user_question}
</user_question>

"""


final_answer_prompt = """
<task>
You are the final component of a system designed to answer user questions about company annual reports.

You will be provided with the following:
- The user's question (original_question)
- A set of auxiliary questions and their corresponding answers, prepared by our system in the previous step.

Your task is to use the information from the answers to the auxiliary questions to respond to the user's original question.

IMPORTANT:
- You must not make any assumptions.
- You cannot convert currencies.
- If there is insufficient information to answer the question, you must respond "n/a".
- If the number is an amount, extract the exact value. For example, if the amount in the document is given as 100 (in thousands) or 100k, extract the value 100000. Similarly, if the amount is given as 2 (in millions) or 2mln, extract the value 2000000.
- If you perform calculations, be attentive to the order of numbers. First, convert all numbers to a uniform format (e.g., 10 mln -> 10,000,000). Perform all calculations step by step, and after completing the calculations, verify their accuracy. If necessary, repeat the calculations to eliminate errors.
- Take the absolute value of Capital Expenditures if it is negative in the answer to the auxiliary question.
- If the user asks about launched products: Only public product launches are considered as launched products. Candidates don't count.
- If the user requests a list of company positions, output them individually as an array.
</task>

<original_question>
{original_question}
</original_question>

<auxiliary_q_and_a>
{auxiliary_q_and_a}
</auxiliary_q_and_a>
"""


answer_question_using_pages_prompt = """
<task>
Your task is to answer the user's question using pages from the company's annual report. After you answer the question, specify the page numbers of pages that contain the answer. If a page does not contain the direct answer, do not add it to the references.

You will be provided with the following:
- The user's question
- Year and month of the end of the last reporting period
- Currency in which the financial statements are presented
- A set of pages with their numbers that may (or may not) contain the answer to the user's question.

IMPORTANT:
- You must not make any assumptions.
- You should not calculate a metric if its value is not explicitly stated in the provided pages from the annual report. This is not a task for financial mathematics. If the metric is not explicitly stated, you must respond with "N/A".
- The same financial metrics may be named differently across documents. Take synonyms and alternative terminology into account.
- Always pay attention to dates.
- Always give priority to tabular data, as it provides the most complete information.
- If there is insufficient information to answer the question, you must respond "N/A".
- If a number is requested, the answer should contain the number and the currency in full form. For example, instead of "2mln USD," the output should be "2,000,000 US dollars." Instead of "1,234,456 million yen," the output should be "1,234,456,000,000 Japanese yen." Instead of "500k CAD," the output should be "500,000 Canadian dollars."
- Present all currencies in their full format (e.g., USD -> US dollars, EUR -> euros).
- If the user's question specifies one currency, but you only have information in another currency, you must respond with "N/A".
- Convert all numbers to a uniform format (e.g., 10 mln -> 10,000,000).
- If your answer is a list of items (products, company positions, etc.), then number all items and present them in an easy-to-understand format
- If the user asks about launched products: Only public product launches are considered as launched products. Candidates don't count
</task>

<question>
{question}
</question>

<end_of_the_last_period_in_report>
{period_end}
</end_of_the_last_period_in_report>

<currency_of_the_report>
{currency}
</currency_of_the_report>

<pages_from_annual_report>
{pages}
</pages_from_annual_report>

"""


find_pages_prompt = """
<task>
You are a Financial Analyst with years of experience and deep expertise in corporate finance. Your task is to identify pages that  contain the answer to user's question.

You will be provided with:
- The user's question
- Year and month of the end of the last reporting period
- Currency in which the financial statements are presented
- A page from the company's annual report

IMPORTANT:
- The same financial metrics may be named differently across documents. Take synonyms and alternative terminology into account. If a metric on the page is named differently than in the user's question but still answers the user's question, the page should be marked as containing the answer.
- Use your expertise and analytical skills to determine relevant pages.
- Ignore the table of contents - these pages are not useful.
</task>

<user_question>
{question}
</user_question>

<end_of_the_last_period_in_report>
{period_end}
</end_of_the_last_period_in_report>

<currency_of_the_report>
{currency}
</currency_of_the_report>

<page_from_annual_report>
{context}
</page_from_annual_report>
"""


meta_info_prompt = """
<task>
You will be provided with the first {num} pages of a company’s annual report. 

Your tasks are as follows:
1. Identify the year and month of the end of the last reporting period in the report
2. Determine in which currency the financial statememts are presented this report:
    - If it's dollars, specify which type of dollars (US, Canadian, Australian)
    - Write the currency in full format (US dollars, Japanese yens, etc)
</task>


<excerpt_from_annual_report>
{context}
</excerpt_from_annual_report>
"""
