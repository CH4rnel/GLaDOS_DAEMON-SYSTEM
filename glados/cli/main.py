# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
CLI interface for GLaDOS_DAEMON-SYSTEM.
Provides command-line access to the daemon's functionality.
"""

import typer
from typing import Optional
from pathlib import Path

from glados.core.agent import GLaDOSAgent
from glados.brain.models import TaskInput
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Create Typer app
app = typer.Typer(
    name="glados",
    help="GLaDOS Daemon System - Personal Autonomous AI Assistant",
    add_completion=False
)

console = Console()


@app.command()
def status():
    """
    Display system status and loaded components.
    """
    try:
        agent = GLaDOSAgent()
        
        console.print(Panel.fit(
            f"[bold cyan]{agent.identity.name}[/bold cyan]\n"
            f"Codename: {agent.identity.codename}\n"
            f"Version: {agent.identity.version}\n"
            f"Owner: {agent.identity.owner.get('username', 'Unknown')}\n"
            f"Environment: {agent.identity.owner.get('environment', 'Unknown')}\n"
            f"\n[bold green]Status: ONLINE[/bold green]",
            title="System Status",
            border_style="cyan"
        ))
        
        # Display loaded components
        table = Table(title="Loaded Components")
        table.add_column("Component", style="cyan")
        table.add_column("Count", style="green", justify="right")
        
        skills_count = len(agent.skills.list_all()) if agent.skills else 0
        tools_count = len(agent.tools.list_all()) if agent.tools else 0
        agents_count = len(agent.llm_agents.list_all()) if agent.llm_agents else 0
        active_agents = len(agent.llm_agents.get_active()) if agent.llm_agents else 0
        
        table.add_row("Skills", str(skills_count))
        table.add_row("Tools", str(tools_count))
        table.add_row("LLM Agents", f"{agents_count} ({active_agents} active)")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def agents():
    """
    List all registered LLM agents.
    """
    try:
        agent = GLaDOSAgent()
        
        if not agent.llm_agents:
            console.print("[yellow]No LLM agents registered.[/yellow]")
            return
        
        all_agents = agent.llm_agents.list_all()
        
        if not all_agents:
            console.print("[yellow]No agents found in registry.[/yellow]")
            return
        
        table = Table(title="Registered LLM Agents")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Provider", style="magenta")
        table.add_column("Model", style="blue")
        table.add_column("Tags", style="yellow")
        table.add_column("Status", style="red")
        
        for profile in all_agents:
            status = "[green]Active[/green]" if profile.is_active else "[red]Inactive[/red]"
            tags = ", ".join(profile.tags) if profile.tags else "-"
            
            table.add_row(
                profile.agent_id,
                profile.display_name,
                profile.provider.value,
                profile.model,
                tags,
                status
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def task(
    description: str = typer.Argument(..., help="Task description"),
    priority: int = typer.Option(3, min=1, max=5, help="Task priority (1-5)"),
    agent_id: Optional[str] = typer.Option(None, help="Preferred agent ID"),
    tag: Optional[str] = typer.Option(None, help="Preferred agent tag")
):
    """
    Send a task to the agent for processing.
    """
    import asyncio
    
    try:
        agent = GLaDOSAgent()
        
        # Build metadata
        metadata = {}
        if agent_id:
            metadata["preferred_agent"] = agent_id
        if tag:
            metadata["preferred_tag"] = tag
        
        # Create task
        task_input = TaskInput(
            description=description,
            priority=priority,
            metadata=metadata
        )
        
        console.print(f"[cyan]Processing task:[/cyan] {description}")
        console.print(f"[cyan]Priority:[/cyan] {priority}")
        
        if metadata:
            console.print(f"[cyan]Metadata:[/cyan] {metadata}")
        
        # Process task asynchronously
        result = asyncio.run(agent.brain.process_task(task_input))
        
        if result.success:
            console.print(Panel.fit(
                f"[bold green]Success[/bold green]\n\n{result.message}",
                title="Task Result",
                border_style="green"
            ))
            
            # Display additional data
            if result.data:
                console.print("\n[bold]Additional Data:[/bold]")
                for key, value in result.data.items():
                    console.print(f"  {key}: {value}")
        else:
            console.print(Panel.fit(
                f"[bold red]Failed[/bold red]\n\n{result.message}",
                title="Task Result",
                border_style="red"
            ))
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def memory(
    search: Optional[str] = typer.Option(None, help="Search term for long-term memory")
):
    """
    Display memory information.
    """
    try:
        agent = GLaDOSAgent()
        
        if not agent.ctx.memory:
            console.print("[yellow]Memory subsystem not initialized.[/yellow]")
            return
        
        # Display short-term memory
        stm_context = agent.ctx.memory.get_short_term_context()
        
        console.print(Panel.fit(
            f"[bold cyan]Short-Term Memory[/bold cyan]\n"
            f"Records: {len(stm_context)}",
            border_style="cyan"
        ))
        
        if stm_context:
            for i, record in enumerate(stm_context[-5:], 1):  # Last 5 records
                console.print(f"  {i}. [{record.role}] {record.content[:100]}...")
        
        # Display long-term memory search results
        if search:
            console.print(f"\n[bold cyan]Long-Term Memory Search:[/bold cyan] '{search}'")
            
            ltm_results = agent.ctx.memory.search_long_term(search)
            
            if ltm_results:
                console.print(f"Found {len(ltm_results)} matching records:")
                for i, record in enumerate(ltm_results[:10], 1):  # First 10 results
                    console.print(f"  {i}. [{record.role}] {record.content[:100]}...")
            else:
                console.print("[yellow]No matching records found.[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def logs(
    lines: int = typer.Option(50, help="Number of recent log lines to display")
):
    """
    Display recent system logs.
    """
    try:
        log_file = Path("logs/glados.log")
        
        if not log_file.exists():
            console.print("[yellow]Log file not found. System may not have been run yet.[/yellow]")
            return
        
        # Read last N lines
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        console.print(Panel.fit(
            f"[bold cyan]Recent Logs (last {len(recent_lines)} lines)[/bold cyan]",
            border_style="cyan"
        ))
        
        for line in recent_lines:
            # Color-code log levels
            if "ERROR" in line:
                console.print(f"[red]{line.strip()}[/red]")
            elif "WARNING" in line:
                console.print(f"[yellow]{line.strip()}[/yellow]")
            elif "INFO" in line:
                console.print(f"[green]{line.strip()}[/green]")
            else:
                console.print(line.strip())
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()