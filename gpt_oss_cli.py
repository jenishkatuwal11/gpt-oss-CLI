import os
import httpx
import typer
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# ----------------------------
# Settings
# ----------------------------
class ClientSettings(BaseSettings):
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "meta-llama/llama-3.1-8b-instruct:free"

    class Config:
        env_file = ".env"


# ----------------------------
# HTTP Client
# ----------------------------
class RouterClient:
    def __init__(self, settings: ClientSettings):
        self.settings = settings

        headers = {"Content-Type": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"

        # ✅ Add OpenRouter attribution headers (some gateways require these)
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
        headers["X-Title"] = os.getenv("OPENROUTER_APP_NAME", "gpt-oss-cli-demo")

        self.client = httpx.Client(
            base_url=self.settings.base_url.rstrip("/"),
            headers=headers,
            timeout=30.0,
        )

    def list_models(self) -> List[str]:
        response = self.client.get("/models")
        response.raise_for_status()
        data = response.json()
        models = data.get("data", data)
        out: List[str] = []
        for m in models:
            if isinstance(m, dict) and "id" in m:
                out.append(m["id"])
            else:
                out.append(str(m))
        return out

    def chat(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        body: Dict[str, Any] = {
            "model": model or self.settings.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 300),
        }
        response = self.client.post("/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "choices" in data:
            try:
                return data["choices"][0]["message"]["content"]
            except Exception:
                pass
        return data.get("content") if isinstance(data, dict) else str(data)

    def get_faq_answer(self, question: str, *, model: str | None = None) -> str:
        body: Dict[str, Any] = {
            "model": model or self.settings.default_model,
            "messages": [
                {"role": "system", "content": (
                    "You are a concise FAQ assistant. Answer clearly in 1–3 short paragraphs. "
                    "If information is missing, ask one brief clarifying question. Avoid invented links."
                )},
                {"role": "user", "content": question},
            ],
            "temperature": 0.3,
            "max_tokens": 400,
        }
        response = self.client.post("/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        return data.get("content", "").strip()

    def close(self):
        self.client.close()


# ----------------------------
# FAQ data (exactly 10)
# ----------------------------
@dataclass(frozen=True)
class FAQ:
    q: str
    a: str

def get_faqs() -> List[FAQ]:
    return [
        FAQ("What programs does Islington College offer?",
            "Undergraduate and postgraduate programs in Computing, IT, Business and related disciplines with UK university partnerships."),
        FAQ("Where is the campus located?",
            "Kamalpokhari, Kathmandu—well connected to public transportation and amenities."),
        FAQ("What are the bachelor’s admission requirements?",
            "Typically +2/A-Levels (or equivalent), minimum grades, English proficiency, and a completed application with documents (varies by program)."),
        FAQ("When are the intakes?",
            "Usually two main intakes (e.g., Spring/Fall). Exact dates are announced by the college."),
        FAQ("Are scholarships available?",
            "Yes—merit and need-based options. Requirements may include transcripts, SOP, and an interview."),
        FAQ("How do I apply?",
            "Submit the application form, academic documents, ID photos, required scores; admissions will guide evaluation and offer steps."),
        FAQ("Is instruction in English?",
            "Yes. Courses follow partner university standards and are delivered in English."),
        FAQ("What campus facilities are available?",
            "Modern computer labs, libraries, student support services, seminar halls, and collaboration spaces."),
        FAQ("Are there internships or industry links?",
            "Yes—industry ties for internships, guest lectures, projects, and placement support."),
        FAQ("How can I contact admissions?",
            "Use the official website’s contact page or call admissions during office hours for current details."),
    ]

WELCOME = "Welcome to Islington College!"
PROMPT = (
    "\nType a number (1-10) to view an FAQ answer,\n"
    "or type your own question to ask the chatbot.\n"
    "Type 'help' for commands or 'exit' to quit."
)
HELP = (
    "\nCommands:\n"
    "  1-10   Show the answer for that FAQ\n"
    "  list   Reprint the FAQ list\n"
    "  exit   Quit the chatbot\n"
    "  help   Show this help\n"
)

def print_faqs():
    faqs = get_faqs()
    typer.echo("\nFrequently Asked Questions:")
    for i, f in enumerate(faqs, start=1):
        typer.echo(f"  {i}. {f.q}")

def show_answer(index: int):
    faqs = get_faqs()
    if 1 <= index <= len(faqs):
        f = faqs[index - 1]
        typer.echo(f"\nQ: {f.q}\nA: {f.a}\n")
    else:
        typer.echo("Invalid FAQ number. Please choose 1-10.")


# ----------------------------
# CLI
# ----------------------------
app = typer.Typer(add_completion=False)

@app.command()
def models():
    settings = ClientSettings()
    client = RouterClient(settings)
    try:
        for m in client.list_models():
            typer.echo(m)
    finally:
        client.close()

@app.command()
def chat(
    prompt: str = typer.Option(None, "--prompt", "-p", help="Single prompt (non-interactive)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Run chatbot mode"),
    model: str = typer.Option(None, "--model", "-m", help="Override default model"),
):
    settings = ClientSettings()
    client = RouterClient(settings)

    try:
        if interactive:
            typer.echo("=" * 60)
            typer.secho(WELCOME, bold=True)
            typer.echo("=" * 60)
            print_faqs()
            typer.echo(PROMPT)

            while True:
                try:
                    user = input("\nYou: ").strip()
                except (EOFError, KeyboardInterrupt):
                    typer.echo("\nGoodbye!")
                    break

                if not user:
                    continue
                low = user.lower()

                if low in {"exit", "quit", "q"}:
                    typer.echo("Goodbye!")
                    break
                if low in {"help", "/help"}:
                    typer.echo(HELP)
                    continue
                if low in {"list", "faq", "faqs"}:
                    print_faqs()
                    continue
                if low.isdigit():
                    show_answer(int(low))
                    continue

                typer.echo("Asking the assistant...")
                try:
                    reply = client.chat(user, model=model)
                    typer.secho("\nAssistant:", bold=True)
                    typer.echo(reply)
                except Exception as e:
                    typer.secho("Error talking to the model:", fg=typer.colors.RED, bold=True)
                    typer.echo(str(e))

        else:
            if not prompt:
                typer.echo("Error: --prompt is required unless you use --interactive")
                raise typer.Exit(1)
            reply = client.chat(prompt, model=model)
            typer.echo(reply)
    finally:
        client.close()


if __name__ == "__main__":
    app()
