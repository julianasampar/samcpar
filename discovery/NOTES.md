# Make adjustments: 
- Collector: write file with the table_name
- Collector: Write the file under the domain/table_name folder
- Profiler: Create a function to orchestrate the calling of each function? or not necessary?
- Reader/Collector: Figure out how to read Snowflake tables + store in a storage
- Add orchestrator agent
- Switched the json ingested for the one the API returns (with more information)
- Add autofill suggestions to prompt ingestion
- Add quality guidelines in skills? Add XML tags?


### What Exactly Are We Compacting?
What eats up context?

Searching for files
Understanding code flow
Applying edits
Test/build logs
Huge JSON blobs from tools
All of these can flood the context window. Compaction is simply distilling them into structured artifacts.



Idea:
<img width="1440" height="862" alt="image" src="https://github.com/user-attachments/assets/00dd1f59-1f45-402d-8789-3d15784341d6" />

Minimum Requirement:
- Read/Select access to whole data warehouse

- Build Transformation Skills on top of dbt Agent Skills
- Two different things: How to Build it? How to Operate it?
- How can we deliver feedback for the agent as fast as possible?
- DAG of Skills
- Have "slim" Skills, the agent shouldn't be in doubt if they should trigger a skill or not

Refs to check again:
https://medium.com/@AnalyticsAtMeta/how-we-built-an-ai-second-brain-for-60k-knowledge-workers-78c507dd795b
PARA Method for Project Context Organization: https://fortelabs.com/blog/para/


"Write everything we did so far to progress.md, ensure to note the end goal, the approach we're taking, the steps we've done so far, and the current failure we're working on" https://www.humanlayer.dev/blog/advanced-context-engineering#:~:text=%23%23%23%20Slightly%20Smarter%3A%20Intentional%20Compaction

<img width="2640" height="470" alt="image" src="https://github.com/user-attachments/assets/b901695b-9803-4995-855f-2adda1ba92f8" />

Subagents are about context control.

The most common/straightforward use case for subagents is to let you use a fresh context window to do finding/searching/summarizing that enables the parent agent to get straight to work without clouding its context window with Glob / Grep / Read / etc calls.

Contains examples of md files for reasearch, plan and implementation: https://www.humanlayer.dev/blog/advanced-context-engineering

Include human interaction on Plan tasks
Include guardrails agents to spot anomalies and wrong information -> rank risks
"we introduced agent-specific metrics tailored to what each agent actually does"

connect to openspec? -> build transformation layer on top of approved/deployed openspec generated files

"The past has shown that the best way for us to stay in control of what we’re building are small, iterative steps, so I’m very skeptical that lots of up-front spec design is a good idea, especially when it’s overly verbose. "

** add instruction to find and flag PII information
