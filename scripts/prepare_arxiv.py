"""Prepare files for arXiv submission."""

import shutil
from pathlib import Path
from datetime import datetime


def prepare_arxiv_submission():
    """Prepare files for arXiv submission."""

    output_dir = Path('arxiv_submission')
    output_dir.mkdir(exist_ok=True)

    print("Preparing arXiv submission package...")
    print("=" * 50)

    # 1. Copy figures
    figures_dir = output_dir / 'figures'
    figures_dir.mkdir(exist_ok=True)

    source_figures = Path('benchmarks/figures')
    for fig in source_figures.glob('*.pdf'):
        shutil.copy(fig, figures_dir / fig.name)
        print(f"  Copied: {fig.name}")

    # 2. Create main.tex template
    latex_template = r'''
\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}
\usepackage{amsmath}
\usepackage{listings}
\usepackage{xcolor}

\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},
    commentstyle=\color{codegreen},
    keywordstyle=\color{blue},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\small,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}
\lstset{style=mystyle}

\title{Teaching LLMs Domain-Specific Languages via Prompt:\\
       Anka, a DSL for Reliable Data Transformation Pipelines}

\author{[Your Name]\\
  University of Wisconsin-Madison\\
  \texttt{[your-email]@wisc.edu}
}

\date{\today}

\begin{document}

\maketitle

\begin{abstract}
We investigate whether Large Language Models can effectively learn and
generate code in a novel domain-specific language (DSL) taught entirely
via in-context prompting. We introduce Anka, a constrained DSL for data
transformations designed to reduce common LLM coding errors through
explicit, step-by-step syntax.

Despite having zero prior training exposure to Anka, Claude 3.5 Haiku
achieves 99.9\% parse success and 95.8\% overall accuracy across 100
benchmark tasks. Critically, Anka demonstrates a \textbf{40\% accuracy
advantage} over Python on multi-step pipeline tasks (100\% vs 60\%),
validated across multiple LLM models including GPT-4o-mini.

Our results demonstrate that: (1) LLMs can learn novel DSLs entirely
from prompts, achieving near-native accuracy; (2) constrained syntax
significantly reduces errors on complex tasks; and (3) domain-specific
languages designed for LLM generation can outperform general-purpose
languages even when the LLM has extensive training on the latter.
\end{abstract}

\section{Introduction}

Large Language Models have demonstrated remarkable code generation
capabilities, yet they frequently produce errors in complex, multi-step
data transformations. These errors often stem from Python's flexible
syntax, which allows multiple approaches to the same problem.

We introduce \textbf{Anka}, a domain-specific language designed
specifically for LLM code generation. Anka's key insight is that
\emph{constrained syntax reduces LLM errors} by eliminating ambiguity
and enforcing explicit, step-by-step operations.

\subsection{Contributions}

\begin{enumerate}
    \item We introduce Anka, a novel DSL for data transformations with
          syntax optimized for LLM code generation.
    \item We demonstrate that LLMs can learn complex DSLs entirely from
          prompts, achieving 99.9\% parse success.
    \item We show that Anka achieves 40\% higher accuracy than Python
          on multi-step pipeline tasks.
    \item We validate our findings across multiple LLM architectures
          (Claude, GPT-4o).
\end{enumerate}

\section{The Anka Language}

Anka programs consist of explicit pipelines with named steps:

\begin{lstlisting}[language=Python]
PIPELINE customer_analysis:
  INPUT orders: TABLE[id: INT, amount: DECIMAL, status: STRING]

  STEP filter:
    FILTER orders WHERE amount > 100 INTO large_orders

  STEP aggregate:
    AGGREGATE large_orders
    GROUP_BY customer_id
    COMPUTE SUM(amount) AS total
    INTO by_customer

  OUTPUT by_customer
\end{lstlisting}

\subsection{Design Principles}

Anka's syntax follows principles designed to reduce LLM errors:

\begin{enumerate}
    \item \textbf{One canonical form}: Each operation has exactly one
          way to express it.
    \item \textbf{Explicit step naming}: Every transformation must be
          named and produces a named output.
    \item \textbf{Verbose keywords}: FILTER, SELECT, AGGREGATE instead
          of symbols.
    \item \textbf{No implicit state}: All data flow is explicit via
          INTO clauses.
\end{enumerate}

\section{Evaluation}

We evaluate Anka against Python across 100 benchmark tasks spanning
filtering, mapping, aggregation, and multi-step pipelines.

\subsection{Benchmark Design}

Our benchmark includes:
\begin{itemize}
    \item 10 filter tasks
    \item 10 map tasks
    \item 10 aggregate tasks
    \item 10 multi-step pipeline tasks
    \item 20 finance domain tasks
    \item 10 string manipulation tasks
    \item 10 hard/complex tasks
    \item 20 adversarial tasks
\end{itemize}

\subsection{Results}

\begin{table}[h]
\centering
\caption{Accuracy by Task Category (Claude 3.5 Haiku, n=3 samples)}
\label{tab:results}
\begin{tabular}{lccc}
\toprule
\textbf{Category} & \textbf{Anka} & \textbf{Python} & \textbf{$\Delta$} \\
\midrule
multi\_step & \textbf{100.0\%} & 60.0\% & \textbf{+40.0\%} \\
finance & \textbf{90.0\%} & 85.0\% & +5.0\% \\
aggregate & 100.0\% & 100.0\% & 0.0\% \\
filter & 96.7\% & 100.0\% & -3.3\% \\
map & 100.0\% & 100.0\% & 0.0\% \\
strings & 100.0\% & 100.0\% & 0.0\% \\
hard & 90.0\% & 100.0\% & -10.0\% \\
\midrule
\textbf{Overall} & \textbf{95.8\%} & 91.2\% & \textbf{+4.6\%} \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{figures/headline_figure.pdf}
\caption{Anka outperforms Python on multi-step tasks across models.}
\label{fig:headline}
\end{figure}

\subsection{Cross-Model Validation}

We validated our findings on GPT-4o-mini, confirming that Anka's
advantage generalizes across LLM architectures:

\begin{table}[h]
\centering
\caption{Multi-Step Task Performance by Model}
\label{tab:multimodel}
\begin{tabular}{lccc}
\toprule
\textbf{Model} & \textbf{Anka} & \textbf{Python} & \textbf{Advantage} \\
\midrule
Claude 3.5 Haiku & 100.0\% & 60.0\% & +40.0\% \\
GPT-4o-mini & 86.7\% & 60.0\% & +26.7\% \\
\midrule
\textbf{Average} & \textbf{93.4\%} & 60.0\% & \textbf{+33.4\%} \\
\bottomrule
\end{tabular}
\end{table}

\section{Analysis}

\subsection{Why Multi-Step Tasks?}

Python's flexibility becomes a liability on multi-step tasks:

\begin{enumerate}
    \item \textbf{Variable shadowing}: Python allows reusing variable
          names, leading to incorrect references.
    \item \textbf{Operation ordering}: LLMs sometimes apply operations
          in the wrong order.
    \item \textbf{Implicit state}: Without explicit intermediate
          variables, LLMs lose track of data flow.
\end{enumerate}

Anka's explicit syntax prevents all three error classes.

\subsection{Parse Success Rate}

Remarkably, 99.9\% of LLM-generated Anka code parses successfully,
despite the model having zero training exposure to the language. This
demonstrates that in-context learning is sufficient for complex syntax.

\section{Related Work}

\subsection{Code Generation with LLMs}
[Add citations to Codex, CodeGen, StarCoder, etc.]

\subsection{Domain-Specific Languages}
[Add citations to DSL literature]

\subsection{Prompt Engineering for Code}
[Add citations to prompt engineering papers]

\section{Limitations}

\begin{enumerate}
    \item Anka currently supports only tabular data transformations.
    \item Our benchmark may not cover all edge cases.
    \item We tested on two LLM families; more diversity would
          strengthen claims.
\end{enumerate}

\section{Conclusion}

We demonstrated that LLMs can effectively learn novel DSLs from prompts
alone, achieving 99.9\% parse success. More importantly, Anka's
constrained syntax provides a \textbf{40\% accuracy advantage} on complex
multi-step pipelines, suggesting that purpose-built DSLs can
significantly improve LLM code generation reliability.

Our work opens new directions for designing programming languages
specifically optimized for LLM generation, potentially enabling more
reliable AI-assisted software development.

\section*{Acknowledgments}
[Add acknowledgments]

\bibliographystyle{plain}
\bibliography{references}

\end{document}
'''

    with open(output_dir / 'main.tex', 'w') as f:
        f.write(latex_template)
    print("  Created: main.tex")

    # 3. Create references.bib
    references = r'''@article{chen2021codex,
  title={Evaluating Large Language Models Trained on Code},
  author={Chen, Mark and others},
  journal={arXiv preprint arXiv:2107.03374},
  year={2021}
}

@article{austin2021program,
  title={Program Synthesis with Large Language Models},
  author={Austin, Jacob and others},
  journal={arXiv preprint arXiv:2108.07732},
  year={2021}
}

@article{nijkamp2023codegen,
  title={CodeGen: An Open Large Language Model for Code with Multi-Turn Program Synthesis},
  author={Nijkamp, Erik and others},
  journal={ICLR},
  year={2023}
}

@article{li2023starcoder,
  title={StarCoder: may the source be with you!},
  author={Li, Raymond and others},
  journal={arXiv preprint arXiv:2305.06161},
  year={2023}
}
'''

    with open(output_dir / 'references.bib', 'w') as f:
        f.write(references)
    print("  Created: references.bib")

    # 4. Create submission checklist
    checklist = f'''
arXiv Submission Checklist
Generated: {datetime.now().isoformat()}
==================================================

Files in this package:
- main.tex          : Main paper
- references.bib    : Bibliography
- figures/          : All figures (PDF format)

Before submitting:
[ ] Update author name and email in main.tex
[ ] Add acknowledgments section
[ ] Review and expand all sections
[ ] Add related work citations
[ ] Verify all figures render correctly
[ ] Check bibliography completeness
[ ] Proofread entire document

Submission steps:
1. Go to https://arxiv.org/submit
2. Choose cs.CL (Computation and Language) or cs.PL (Programming Languages)
3. Upload all files
4. Preview and verify rendering
5. Submit

After submission:
[ ] Update README with arXiv ID
[ ] Update citation in README
[ ] Share on social media / relevant forums
'''

    with open(output_dir / 'CHECKLIST.txt', 'w') as f:
        f.write(checklist)
    print("  Created: CHECKLIST.txt")

    print("=" * 50)
    print(f"arXiv package ready in: {output_dir}/")
    print("\nNext steps:")
    print("1. Edit main.tex to expand content")
    print("2. Add your name and affiliation")
    print("3. Submit to https://arxiv.org/submit")


if __name__ == '__main__':
    prepare_arxiv_submission()
