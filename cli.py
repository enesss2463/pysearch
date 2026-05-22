import typer
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from pysearch.engine import search_files
from pysearch.semantic import SemanticIndex
from pysearch.ai import explain_code, suggest_refactor

app = typer.Typer()
console = Console()

INDEX_DIR = Path.home() / ".pysearch_index"


def print_results(results, pattern: str, context_lines: int):
    if not results:
        console.print("[yellow]Hiç sonuç bulunamadı.[/yellow]")
        return

    total_matches = sum(r.match_count for r in results)

    for result in results:
        console.print(f"\n[bold cyan]{result.file}[/bold cyan]")

        for match in result.matches:
            for ctx in match.context_before:
                console.print(f"  [dim]{match.line_number - len(match.context_before)}  {ctx}[/dim]")

            line = match.line
            text = Text()
            text.append(f"  {match.line_number}  ")
            text.append(line[:match.match_start])
            text.append(line[match.match_start:match.match_end], style="bold red")
            text.append(line[match.match_end:])
            console.print(text)

            for ctx in match.context_after:
                console.print(f"  [dim]{match.line_number + 1}  {ctx}[/dim]")

    console.print(f"\n[bold green]{len(results)} dosyada {total_matches} eşleşme bulundu.[/bold green]")


@app.command()
def search(
    pattern: str = typer.Argument(..., help="Aranacak kelime veya pattern"),
    path: Path = typer.Argument(Path("."), help="Aranacak dizin"),
    regex: bool = typer.Option(False, "--regex", "-r", help="Regex kullan"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", "-c", help="Büyük/küçük harf duyarlı"),
    context: int = typer.Option(0, "--context", "-C", help="Context satır sayısı"),
    extensions: str = typer.Option(None, "--ext", "-e", help="Uzantı filtresi, örn: .py,.txt"),
    max_results: int = typer.Option(None, "--max", "-m", help="Maksimum sonuç sayısı"),
):
    ext_list = [e.strip() for e in extensions.split(",")] if extensions else None

    if not path.exists():
        console.print(f"[red]Hata: '{path}' bulunamadı.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]'{pattern}'[/bold] aranıyor → [cyan]{path}[/cyan]")

    results = search_files(
        root=path,
        pattern=pattern,
        use_regex=regex,
        case_sensitive=case_sensitive,
        context_lines=context,
        extensions=ext_list,
        max_results=max_results,
    )

    print_results(results, pattern, context)


@app.command()
def index(
    path: Path = typer.Argument(Path("."), help="Indexlenecek dizin"),
    extensions: str = typer.Option(None, "--ext", "-e", help="Uzantı filtresi, örn: .py,.txt"),
):
    """Dizini semantic search için indexler."""
    ext_list = [e.strip() for e in extensions.split(",")] if extensions else None

    if not path.exists():
        console.print(f"[red]Hata: '{path}' bulunamadı.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold cyan]{path}[/bold cyan] indexleniyor...")

    idx = SemanticIndex(INDEX_DIR)
    chunk_count, file_count = idx.index_directory(path, extensions=ext_list)
    if file_count == 0:
        console.print("[yellow]Değişen dosya yok, index güncel.[/yellow]")
    else:
        console.print(f"[bold green]{file_count} dosya, {chunk_count} chunk indexlendi![/bold green]")


@app.command()
def semantic(
    query: str = typer.Argument(..., help="Anlam bazlı arama sorgusu"),
    top_k: int = typer.Option(5, "--top", "-t", help="Kaç sonuç gösterilsin"),
):
    """Anlam bazlı (semantic) arama yapar."""
    if not INDEX_DIR.exists():
        console.print("[red]Henüz index yok. Önce 'index' komutunu çalıştır.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]'{query}'[/bold] için semantic arama yapılıyor...")

    idx = SemanticIndex(INDEX_DIR)
    results = idx.search(query, top_k=top_k)

    if not results:
        console.print("[yellow]Sonuç bulunamadı.[/yellow]")
        return

    for i, result in enumerate(results, 1):
        score_pct = f"{result['score'] * 100:.1f}%"
        console.print(Panel(
            f"[dim]{result['text'][:300]}...[/dim]",
            title=f"[bold cyan]{result['file']}[/bold cyan] · satır {result['start_line']}-{result['end_line']} · benzerlik: [green]{score_pct}[/green]",
            border_style="blue",
        ))

@app.command()
def explain(
    file: Path = typer.Argument(..., help="Açıklanacak dosya"),
    start: int = typer.Option(1, "--start", "-s", help="Başlangıç satırı"),
    end: int = typer.Option(50, "--end", "-e", help="Bitiş satırı"),
):
    """Seçilen kod bloğunu AI ile açıklar."""
    if not file.exists():
        console.print(f"[red]Hata: '{file}' bulunamadı.[/red]")
        raise typer.Exit(1)

    lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
    code = "\n".join(lines[start - 1: end])

    console.print(f"[bold cyan]{file}[/bold cyan] · satır {start}-{end} açıklanıyor...")
    result = explain_code(code)
    console.print(Panel(result, title="[bold green]AI Açıklama[/bold green]", border_style="green"))


@app.command()
def refactor(
    file: Path = typer.Argument(..., help="Refactor önerisi istenecek dosya"),
    start: int = typer.Option(1, "--start", "-s", help="Başlangıç satırı"),
    end: int = typer.Option(50, "--end", "-e", help="Bitiş satırı"),
):
    """Seçilen kod bloğu için AI refactor önerisi sunar."""
    if not file.exists():
        console.print(f"[red]Hata: '{file}' bulunamadı.[/red]")
        raise typer.Exit(1)

    lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
    code = "\n".join(lines[start - 1: end])

    console.print(f"[bold cyan]{file}[/bold cyan] · satır {start}-{end} için refactor önerisi alınıyor...")
    result = suggest_refactor(code)
    console.print(Panel(result, title="[bold yellow]AI Refactor Önerisi[/bold yellow]", border_style="yellow"))
if __name__ == "__main__":
    app()