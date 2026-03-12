import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"
HOST = "127.0.0.1"
PORT = "8010"
BASE_URL = f"http://{HOST}:{PORT}"

DB_URL = "sqlite:///demo_linkedin.sqlite3"
SECRET_KEY = "dev-screenshot-key"
USERNAME = "linkedin_demo"
PASSWORD = "SynexDemo123!"


def wait_for_server(url: str, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"Servidor nao respondeu em {url}. erro={last_error}")


def prepare_env() -> dict[str, str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = DB_URL
    env["DEBUG"] = "True"
    env["SECRET_KEY"] = SECRET_KEY
    env["PYTHONUNBUFFERED"] = "1"
    return env


def seed_data(env: dict[str, str]) -> None:
    cmd = [str(PYTHON), "manage.py", "shell", "-c", "exec(open('scripts/seed_linkedin_demo.py', encoding='utf-8').read())"]
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def disable_onboarding(page) -> None:
    try:
        user_id = page.evaluate(
            "() => window.SYNEX_CONFIG && window.SYNEX_CONFIG.user ? String(window.SYNEX_CONFIG.user.id || '') : ''"
        )
    except Exception:  # noqa: BLE001
        user_id = ""
    if not user_id:
        return
    page.evaluate(
        """(uid) => {
            localStorage.setItem('synex_onboarding_done_' + uid, '1');
            localStorage.removeItem('synex_onboarding_step_' + uid);
            localStorage.removeItem('synex_onboarding_active_' + uid);
            localStorage.removeItem('synex_onboarding_pause_' + uid);
            localStorage.removeItem('synex_onboarding_pending_materia_' + uid);
        }""",
        user_id,
    )


def login(page) -> None:
    page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    page.fill("input[name='username']", USERNAME)
    page.fill("input[name='password']", PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_url(f"{BASE_URL}/board/", timeout=15000)
    disable_onboarding(page)


def capture_pages() -> list[Path]:
    output_dir = ROOT / "assets" / "linkedin" / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    captures = [
        ("/dashboard/", "01-dashboard.png"),
        ("/cronograma/", "02-cronograma.png"),
        ("/board/", "03-kanban.png"),
        ("/foco/", "04-modo-foco.png"),
        ("/anotacoes/", "05-anotacoes.png"),
    ]

    saved: list[Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 900})
        page = context.new_page()
        login(page)

        for path, filename in captures:
            page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
            page.wait_for_timeout(1200)
            disable_onboarding(page)
            page.wait_for_timeout(400)
            output_path = output_dir / filename
            page.screenshot(path=str(output_path), full_page=False)
            saved.append(output_path)

        context.close()
        browser.close()
    return saved


def run() -> int:
    env = prepare_env()
    seed_data(env)

    server_cmd = [str(PYTHON), "manage.py", "runserver", f"{HOST}:{PORT}", "--noreload"]
    server = subprocess.Popen(server_cmd, cwd=ROOT, env=env)
    try:
        wait_for_server(f"{BASE_URL}/login/")
        files = capture_pages()
        print("screenshots-ok")
        for f in files:
            print(f)
        return 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    sys.exit(run())
