from openai import OpenAI 
import json
from tqdm import tqdm
client = OpenAI(
    api_key="Yor API KEY",
    base_url=""
) 

TYPE1_TEMPLATE = """Act as a SPARQL expert. 
I need you to explain the meaning and function of a specific part of a SPARQL query.
You job is answer the Question for me. ONLY OUTPUT THE ANSWER, NOTING ELSE!!

### EXAMPLE1
Sparql:
?entity1 ns:location.country.currency_used ?entity2 .
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the currency used in the country ?entity1.

### EXAMPLE2
Sparql:
?entity2 ns:location.country.currency_used ?entity1 .
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the country that use ?entity1 as currency.

### EXAMPLE3
Sparql:
?entity2 ns:government.election_campaign.candidate ?entity1 .
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the election campaign which ?entity1 is the candidate.

### EXAMPLE4
Sparql:
?entity1 ns:government.election_campaign.candidate ?entity2 .
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the candidate in the election campaign ?entity1.

### EXAMPLE5
Sparql:
{{ ?entity2 ns:sports.sports_championship_event.runner_up ?entity1 }} UNION {{ ?entity2 ns:sports.sports_championship_event.champion ?entity1 }}
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is either the runner-up or the champion of a sports championship event ?entity1.

### EXAMPLE6
Sparql:
{{ ?entity1 ns:location.statistical_region.places_exported_to ?tmp0 . ?tmp0 ns:location.imports_and_exports.exported_to ?entity2 }} UNION {{ ?entity1 ns:location.statistical_region.places_exported_from ?tmp1 . ?tmp1 ns:location.imports_and_exports.exported_from ?entity2 }}
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the place that is either exported to or exported from the statistical region ?entity1.

### YOUR TURN
Sparql:
{sparql}
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: """

TYPE2_TEMPLATE = """Act as a SPARQL expert.
I need you to explain the meaning and function of a specific part of a SPARQL query.
You job is answer the Question for me. ONLY OUTPUT THE ANSWER, NOTING ELSE!!

### EXAMPLE1
Sparql:
?cvt ns:government.government_position_held.office_holder ?entity1 .
?entity2 ns:government.governmental_body.members ?cvt . 
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the governmental body that has an office holder ?entity1.

### EXAMPLE2 
Sparql:
?entity1 ns:film.actor.film ?cvt .
?cvt ns:film.performance.character ?entity2 .
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the character played by the actor ?entity1.

### EXAMPLE3 
Sparql:
?cvt ns:music.group_membership.member ?entity1 .
?entity2 ns:music.musical_group.member ?cvt .
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity2 is the musical group that has the member ?entity1.

### YOUR TURN
Sparql:
{sparql}
Question: How does ?entity2 related to ?entity1 ? Please answer the question with "?entity2 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer:  
"""

TYPE3_TEMPLATE = """Act as a SPARQL expert. 
I need you to explain the meaning and function of a specific part of a SPARQL query. 
You job is complete the answer for me. ONLY OUTPUT THE ANSWER, NOTING ELSE!! 

### EXAMPLE1 
Sparql: 
?cvt ns:sports.sports_team_coach_tenure.position ?entity1 . 
?cvt ns:sports.sports_team_coach_tenure.coach ?entity2 . 
?entity3 ns:sports.sports_team.coaches ?cvt . 
Question: How does ?entity3 related to ?entity1 and ?entity2 ? Please answer the question with "?entity3 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity3 is the sports team that has a coach ?entity2 who holds the position ?entity1 . 

### EXAMLPE2 
Sparql: 
?entity1 ns:film.actor.film ?cvt . 
?cvt ns:film.performance.character ?entity2 . 
?cvt ns:film.performance.film ?entity3 . 
Question: How does ?entity3 related to ?entity1 and ?entity2 ? Please answer the question with "?entity3 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity3 is the film in which the actor ?entity1 performs the character ?entity2. 

### EXAMLPE3 
Sparql: 
?entity1 ns:sports.pro_athlete.teams ?cvt . 
?cvt ns:sports.sports_team_roster.team ?entity2 . 
?cvt ns:sports.sports_team_roster.from ?entity3 
Question: How does ?entity3 related to ?entity1 and ?entity2 ? Please answer the question with "?entity3 is [noun phrase]" . Make sure ?cvt not in your answer.
Answer: ?entity3 is the starting date when the professional athlete ?entity1 was part of the team ?entity2. 

### YOUR TURN 
Sparql: 
{sparql} 
Question: How does ?entity3 related to ?entity1 and ?entity2 ? Please answer the question with "?entity3 is [noun phrase]" . Make sure ?cvt not in your answer. 
Answer: 
"""

def get_response(prompt):
    completion = client.chat.completions.create(
        model="glm-4-plus",  
        messages=[    
            {"role": "user", "content": prompt} 
        ],
        top_p=0.7,
        temperature=0.9
    ) 
    return completion.choices[0].message.content

with open("output/all_key.json", "r") as f:
    all_key = json.load(f)

key_explain = {}
for type in all_key:
    if type == "1":
        for key in tqdm(all_key[type]):
            prompt = TYPE1_TEMPLATE.format(sparql=key)
            key_explain[key] = get_response(prompt)
        with open("output/key_explain1.json", "w") as f:
            json.dump(key_explain, f)
    elif type == "2":
        for key in tqdm(all_key[type]):
            prompt = TYPE2_TEMPLATE.format(sparql=key)
            key_explain[key] = get_response(prompt)
        with open("output/key_explain2.json", "w") as f:
            json.dump(key_explain, f)
    elif type == "3":
        for key in tqdm(all_key[type]):
            prompt = TYPE3_TEMPLATE.format(sparql=key)
            key_explain[key] = get_response(prompt)
        with open("output/key_explain3.json", "w") as f:
            json.dump(key_explain, f)

with open("output/key_explain.json", "w") as f:
    json.dump(key_explain, f)
            