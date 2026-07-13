"""Concept-reacties genereren met Claude Haiku.

Twee modi:
- karma: geen productvermelding, puur behulpzaam.
- marketing: mag het project noemen, mét disclosure.

Concepten worden nooit automatisch gepost — de mens reviewt en plaatst zelf.
"""
import anthropic

from .scoring import MODEL

KARMA_RULES = (
    "Regels: noem het project of product NIET. Geen links naar het project. "
    "Schrijf een oprecht behulpzame reactie die de vraag of het probleem in de "
    "post adresseert. Doel is waarde toevoegen en karma opbouwen."
)

MARKETING_RULES = (
    "Regels: je mag het project noemen als het echt relevant is voor de post, "
    "maar wees er transparant over — vermeld expliciet dat je de maker/betrokkene "
    "bent (disclosure). Begin met daadwerkelijke hulp, noem het project pas daarna. "
    "Geen agressieve verkooppraat."
)

SYSTEM_PROMPT = (
    "Je schrijft een concept-Redditreactie namens de gebruiker. Schrijf in de taal "
    "van de originele post. Klink als een normale Redditor: informeel, concreet, "
    "geen marketingtaal, geen opsommingstekens tenzij het echt helpt, geen "
    "afsluitende slotzin als 'Hope this helps!'. Houd het beknopt. "
    "De gebruiker reviewt en post dit zelf handmatig."
)


def generate_draft(instruction: str, post: dict, mode: str) -> str:
    rules = MARKETING_RULES if mode == "marketing" else KARMA_RULES
    client = anthropic.Anthropic()
    user_msg = (
        f"Projectcontext:\n{instruction}\n\n"
        f"Modus: {mode}\n{rules}\n\n"
        f"Reddit-post in r/{post['subreddit']}:\n"
        f"Titel: {post['title']}\n\n"
        f"{post['body'][:3000]}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return next(b.text for b in response.content if b.type == "text")
