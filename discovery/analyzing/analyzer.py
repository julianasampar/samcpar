"""
analyzer.py

Creates an agent to summarize all findings (in JSON) and create a final report in .md.
"""

import json
from discovery.utils.reader import get_datasource
from discovery.utils.writer import get_storage
from discovery.utils import assistant, manager, executor

from pathlib import Path

# Assigning the SKILL as the system prompt
def load_skill(skill_name) -> str:
    skill_path = Path(__file__).parent / f"{skill_name}.md"
    print(f" Skill {skill_name}.md loaded.")
    return skill_path.read_text(encoding="utf-8")

def analyze_results(
    domain_name:     str,
    storage_type:    str,
    **kwargs
):
    """
        Receives the profiling JSON from the previous steps and spins up agents to
         create a summarized analysis of all findings.
    """
    reading_kwargs, writting_kwargs = manager.manage_input_output_paths(
        storage_type,
        io_type='inspector-analyzer',
        input_path=kwargs.get('input_path'),
        output_path=kwargs.get('output_path'),
        input_bucket=kwargs.get('input_bucket'),
        output_bucket=kwargs.get('output_bucket'),
    )

    storage = get_storage(storage_type=storage_type, **reading_kwargs)
    inspector_json = storage.read_json_from_storage(f"{reading_kwargs["folder_path"]}/{domain_name}")

    system_prompt = load_skill(skill_name="ANALYSIS")

    for datasource, inspection in inspector_json.items():
        analysis_messages = [
                 {
                     "role": "user",
                     "content": f"""
                         Analyze the data of {datasource}, with the provided JSON and create a summarized and comprehensive text: 
                             {inspection}
                         """
                 }
             ]
        
        print(f"Summarizing content of Datasource: {datasource}.")
    
        response = assistant.chat(
            stream_text=False,
            messages=analysis_messages,
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt
            )
        results = response.content[0].text

        storage = get_storage(storage_type, **writting_kwargs)
        storage.write_json_to_storage(content={datasource: {"analysis": results}}, domain_folder=domain_name, analysis_type="summary")

        print(f"{datasource} analyzed. File in storage. Length of analysis: {len(results)} caracteres.")

    return print(f"Analysis finished.")